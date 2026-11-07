"""PsychoPy window presented through an OpenXR runtime (``pyopenxr``).

PsychoPy owns the window and the stimuli; OpenXR owns pacing and
presentation. Each ``flip()`` submits the eye textures, swaps the desktop
mirror, then blocks in ``xrWaitFrame`` for the next frame. Head-locked,
monoscopic or per-eye stereoscopic.

``runtime=`` names the OpenXR runtime (a manifest path, or a name such as
``'oculus'``, ``'steamvr'`` or ``'virtualdesktop'``); ``None`` uses the
system's active one. The runtime used and each frame's predicted display time
(``predicted_display_time_s``, on the ``time.perf_counter`` clock) are written
to the ``_timing.csv`` sidecar.

The Oculus runtime paces an OpenGL application at ~85 Hz unless the window is
visible with its event queue pumped every frame and the desktop window is
swapped every frame with vsync off. Both are handled here; keep the window in
front.
"""

import csv
import ctypes
import glob
import json
import logging
import math
import os
import re
import sys
import time
from time import time as wall_time

import numpy as np
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL import GL
from psychopy import monitors, visual
from psychopy import logging as psy_logging

SESSION_READY_TIMEOUT_S = 15.0
EYE_INDEX = {'left': 0, 'right': 1}
TRIGGER_DEADZONE = 0.2746
HAND_PATHS = {'left': '/user/hand/left', 'right': '/user/hand/right',
              'gamepad': '/user/gamepad'}
TOUCH_PROFILE = '/interaction_profiles/oculus/touch_controller'
XBOX_PROFILE = '/interaction_profiles/microsoft/xbox_controller'
BUTTON_HANDS = {'A': 'right', 'B': 'right', 'X': 'left', 'Y': 'left'}
TOUCH_CONTROLLER_HANDS = {'LeftTouch': ('left',), 'RightTouch': ('right',),
                          'Touch': ('left', 'right')}
INERT_CONTROLLERS = ('Remote', 'Object0', 'Object1', 'Object2', 'Object3')
INERT_BUTTONS = ('RThumb', 'RShoulder', 'LThumb', 'LShoulder', 'Up', 'Down',
                 'Left', 'Right', 'Enter', 'Back', 'VolUp', 'VolDown', 'Home')
TEST_STATES = {'continuous': 'continuous', 'rising': 'pressed', 'pressed': 'pressed',
               'falling': 'released', 'released': 'released'}
WINDOWS_RUNTIMES_KEY = r'SOFTWARE\Khronos\OpenXR\1\AvailableRuntimes'
LINUX_RUNTIME_DIRS = ('/usr/share/openxr/1', '/usr/local/share/openxr/1',
                      '/etc/xdg/openxr/1', '/etc/openxr/1', '~/.config/openxr/1')


def _placeholder_monitor():
    prev_level = psy_logging.console.level
    psy_logging.console.setLevel(psy_logging.ERROR)
    try:
        mon = monitors.Monitor('eegnb_openxr_placeholder', autoLog=False)
        mon.setDistance(60)
        mon.setSizePix([1920, 1080])
    finally:
        psy_logging.console.setLevel(prev_level)
    return mon


def _manifest_name(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)['runtime']['name']
    except (OSError, ValueError, KeyError, TypeError):
        return os.path.splitext(os.path.basename(path))[0]


def registered_runtimes():
    """Installed OpenXR runtimes as ``{manifest path: runtime name}``."""
    paths = []
    if sys.platform == 'win32':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WINDOWS_RUNTIMES_KEY) as key:
                index = 0
                while True:
                    try:
                        paths.append(winreg.EnumValue(key, index)[0])
                    except OSError:
                        break
                    index += 1
        except OSError:
            pass
    else:
        for folder in LINUX_RUNTIME_DIRS:
            for path in sorted(glob.glob(os.path.join(os.path.expanduser(folder), '*.json'))):
                if not os.path.basename(path).startswith('active_runtime'):
                    paths.append(path)
    return {path: _manifest_name(path) for path in paths if os.path.isfile(path)}


def resolve_runtime(runtime):
    """Manifest path for ``runtime``: a manifest path, or a name such as
    ``'oculus'``, ``'steamvr'``, ``'virtualdesktop'`` or ``'monado'`` matched
    against the registered runtimes' names and manifest file names."""
    if os.path.isfile(runtime):
        return os.path.abspath(runtime)

    def normalise(text):
        return re.sub(r'[^a-z0-9]', '', text.lower())

    key = normalise(runtime)
    runtimes = registered_runtimes()
    matches = [path for path, name in runtimes.items()
               if key and (key in normalise(name)
                           or key in normalise(os.path.splitext(os.path.basename(path))[0]))]
    if len(matches) == 1:
        return matches[0]
    found = '; '.join(f"{name} ({path})" for path, name in runtimes.items()) or 'none'
    raise ValueError(f"OpenXR runtime {runtime!r} matched {len(matches)} of the registered "
                     f"runtimes, need exactly one. Registered: {found}")


class _PygletContext:
    """``GraphicsContextProvider`` over PsychoPy's pyglet window."""

    def __init__(self, win):
        self.win = win

    def make_current(self):
        self.win.winHandle.switch_to()

    def done_current(self):
        pass

    def pump(self):
        self.win.winHandle.dispatch_events()

    def present(self):
        self.win.winHandle.flip()

    def destroy(self):
        pass


class VR(visual.Window):

    _DERIVED_TIMING_FIELDS = (
        'marker',
        'predicted_display_time_s',
        'runtime_time_s',
        'display_period_ms',
        'frame_step_ms',
        'missed_vsyncs',
        'session_state',
    )

    def __init__(self, monoscopic=True, headLocked=True, size=None,
                 app_name='eegnb', runtime=None, **kwargs):
        self._closed = True
        if not headLocked:
            raise NotImplementedError(
                "VR renders head-locked only; pass headLocked=True")
        if runtime is not None:
            os.environ['XR_RUNTIME_JSON'] = resolve_runtime(runtime)
        self.runtime_manifest = os.environ.get('XR_RUNTIME_JSON')
        logging.info("[openxr] runtime manifest: %s",
                     self.runtime_manifest or 'system default')
        try:
            import xr
        except ImportError as e:
            raise ImportError(
                "the OpenXR backend needs pyopenxr: pip install pyopenxr") from e
        self._xr = xr
        self._monoscopic = monoscopic
        self.buffer = None
        self.timing_data = []
        self.mirror_swap_every = 1
        self._mirror_swap_counter = 0
        self.runtime_to_wallclock_offset = None
        self.runtime_to_wallclock_bracket = None
        self.app_dropped_max = 0
        self._missed_vsyncs = 0
        self._missed_events = 0
        self._longest_step_ms = 0.0
        self._zero_steps = 0
        self._frame_index = 0
        self._last_pdt = None
        self.last_predicted_display_time_s = None
        self.last_runtime_time_s = None
        self.last_display_period_ms = None
        self.last_frame_step_ms = None
        self._frame_step_ns = None
        self._frame_state = None
        self._views = None
        self._layer = None
        self._layer_views = None
        self._acquired = {}
        self._bound = None
        self._bound_size = None
        self._session_state = xr.SessionState.IDLE
        self._session_running = False
        self._session_lost = False
        self.resume_after_stop = False
        self._xr_ready = False
        self._input_enabled = False
        self._actions = {}
        self._input_paths = {}
        self._buttons = {}
        self._prev_buttons = {}
        self._triggers = {}
        self._input_poll_time_s = 0.0

        available = {e.extension_name.decode()
                     for e in xr.enumerate_instance_extension_properties()}
        wanted = [xr.KHR_OPENGL_ENABLE_EXTENSION_NAME]
        if xr.KHR_OPENGL_ENABLE_EXTENSION_NAME not in available:
            raise RuntimeError("the OpenXR runtime does not support OpenGL")
        optional = [xr.FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME, xr.FB_PASSTHROUGH_EXTENSION_NAME]
        if sys.platform == 'win32':
            optional.append(xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME)
        else:
            optional.append(xr.KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME)
        self._extensions = set(wanted + [e for e in optional if e in available])

        self.instance = xr.create_instance(create_info=xr.InstanceCreateInfo(
            application_info=xr.ApplicationInfo(
                application_name=app_name, application_version=1,
                engine_name='psychopy', engine_version=1),
            enabled_extension_names=sorted(self._extensions)))
        self.system_id = xr.get_system(
            instance=self.instance,
            get_info=xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY))
        props = xr.get_instance_properties(self.instance)
        self.runtime_name = f"{props.runtime_name.decode()} {xr.Version(props.runtime_version)}"
        self.system_name = xr.get_system_properties(
            self.instance, self.system_id).system_name.decode()
        self._view_config = xr.ViewConfigurationType.PRIMARY_STEREO
        config_views = xr.enumerate_view_configuration_views(
            instance=self.instance, system_id=self.system_id,
            view_configuration_type=self._view_config)
        recommended = (config_views[0].recommended_image_rect_width,
                       config_views[0].recommended_image_rect_height)
        self.recommended_eye_size = recommended
        size = tuple(int(v) for v in (size or recommended))

        kwargs.setdefault('monitor', _placeholder_monitor())
        kwargs.setdefault('units', 'norm')
        kwargs.setdefault('color', [0, 0, 0])
        kwargs.setdefault('checkTiming', False)
        kwargs.setdefault('autoLog', False)
        super().__init__(size=size, fullscr=False, winType='pyglet', useFBO=False,
                         waitBlanking=False, allowGUI=True, **kwargs)
        self.winHandle.switch_to()
        self.winHandle.set_vsync(False)
        self.winHandle.activate()
        self._eye_size = tuple(int(v) for v in self.clientSize)

        from xr.utils.gl import OpenGLGraphics
        self._context = _PygletContext(self)
        self._graphics = OpenGLGraphics(self.instance, self.system_id, self._context)
        self.session = xr.create_session(
            instance=self.instance,
            create_info=xr.SessionCreateInfo(
                system_id=self.system_id,
                next=self._graphics.graphics_binding.pointer))
        self.space = xr.create_reference_space(
            session=self.session,
            create_info=xr.ReferenceSpaceCreateInfo(
                reference_space_type=xr.ReferenceSpaceType.VIEW))
        self._draw_fbo = GL.glGenFramebuffers(1)
        self._copy_fbo = GL.glGenFramebuffers(1)

        formats = list(xr.enumerate_swapchain_formats(self.session))
        preferred = [GL.GL_SRGB8_ALPHA8, GL.GL_RGBA8, GL.GL_RGB10_A2, GL.GL_RGBA16F]
        self.swapchain_format = next((f for f in preferred if f in formats), formats[0])
        self._swapchains = []
        self._swapchain_images = []
        w, h = self._eye_size
        for _ in config_views:
            info = xr.SwapchainCreateInfo(
                array_size=1, format=self.swapchain_format, width=w, height=h,
                mip_count=1, face_count=1, sample_count=1,
                usage_flags=(xr.SwapchainUsageFlags.SAMPLED_BIT
                             | xr.SwapchainUsageFlags.COLOR_ATTACHMENT_BIT))
            handle = xr.create_swapchain(session=self.session, create_info=info)
            self._swapchains.append(handle)
            self._swapchain_images.append(xr.enumerate_swapchain_images(
                swapchain=handle, element_type=xr.SwapchainImageOpenGLKHR))

        self._passthrough = None
        self._passthrough_layer = None
        self._passthrough_composition = None
        self._passthrough_on = False
        self._refresh_rate_hz = None
        if xr.FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME in self._extensions:
            try:
                rate = xr.get_display_refresh_rate_fb(self.session)
                self._refresh_rate_hz = float(getattr(rate, 'value', rate))
            except Exception as e:
                logging.warning("[openxr] display refresh rate unavailable: %s", e)
        self._qpc_freq = None
        if sys.platform == 'win32':
            freq = ctypes.c_longlong()
            ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
            self._qpc_freq = float(freq.value)

        self._action_set = xr.create_action_set(
            instance=self.instance,
            create_info=xr.ActionSetCreateInfo(
                action_set_name='eegnb', localized_action_set_name='eegnb', priority=0))
        self._setup_input()
        xr.attach_session_action_sets(
            session=self.session,
            attach_info=xr.SessionActionSetsAttachInfo(
                count_action_sets=1, action_sets=(xr.ActionSet * 1)(self._action_set)))
        self._wait_until_running()
        self._xr_ready = True
        self._begin_frame()
        logging.info("[openxr] %s on %s, %dx%d per eye, %s Hz, format 0x%x",
                     self.runtime_name, self.system_name, w, h,
                     self._refresh_rate_hz, self.swapchain_format)

    def _poll_events(self):
        xr = self._xr
        while True:
            try:
                event = xr.poll_event(self.instance)
            except xr.EventUnavailable:
                return
            kind = xr.StructureType(event.type)
            if kind == xr.StructureType.EVENT_DATA_SESSION_STATE_CHANGED:
                changed = ctypes.cast(ctypes.byref(event),
                                      ctypes.POINTER(xr.EventDataSessionStateChanged)).contents
                self._session_state = xr.SessionState(changed.state)
                if self._session_state == xr.SessionState.READY:
                    xr.begin_session(self.session, xr.SessionBeginInfo(self._view_config))
                    self._session_running = True
                elif self._session_state == xr.SessionState.STOPPING:
                    self._session_running = False
                    xr.end_session(self.session)
                elif self._session_state in (xr.SessionState.EXITING,
                                             xr.SessionState.LOSS_PENDING):
                    self._session_running = False
                    self._session_lost = True
            elif kind == xr.StructureType.EVENT_DATA_INSTANCE_LOSS_PENDING:
                self._session_running = False
                self._session_lost = True

    def _wait_until_running(self, timeout_s=SESSION_READY_TIMEOUT_S):
        deadline = time.perf_counter() + timeout_s
        while not self._session_running:
            self._poll_events()
            self._context.pump()
            if self._session_lost:
                raise RuntimeError("OpenXR session lost before it started")
            if time.perf_counter() > deadline:
                raise RuntimeError(
                    f"OpenXR session did not reach READY within {timeout_s:.0f}s "
                    f"(state {self._session_state.name}); is the headset awake "
                    "and Link connected?")
            time.sleep(0.005)

    def _wait_for_resume(self):
        """Block until a stopped session runs again, e.g. the headset was taken off and put back on.

        Only reached while ``resume_after_stop`` is set. Passthrough is
        restarted if it was on.
        """
        logging.warning("[openxr] session %s; waiting for the headset to resume",
                        self._session_state.name)
        started = time.perf_counter()
        while not self._session_running:
            if self._session_lost:
                raise RuntimeError("OpenXR session lost while waiting for the headset to resume")
            time.sleep(0.01)
            self._poll_events()
            self._context.pump()
        self._last_pdt = None
        logging.info("[openxr] session resumed after %.1f s", time.perf_counter() - started)
        if self._passthrough_on:
            self._passthrough_on = False
            self.set_passthrough(True)

    def _xr_time_to_s(self, xr_time):
        xr = self._xr
        if self._qpc_freq is not None:
            ticks = xr.convert_time_to_win32_performance_counter_khr(self.instance, xr_time)
            return getattr(ticks, 'value', ticks) / self._qpc_freq
        if xr.KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME in self._extensions:
            ts = xr.convert_time_to_timespec_time_khr(self.instance, xr_time)
            return ts.tv_sec + ts.tv_nsec * 1e-9
        return None

    def _begin_frame(self):
        xr = self._xr
        self._poll_events()
        self._context.pump()
        self._frame_state = None
        self._views = None
        self._layer = None
        self._acquired = {}
        self._bound = None
        if not self._session_running:
            if not (self.resume_after_stop and not self._session_lost):
                raise RuntimeError(
                    f"OpenXR session stopped mid-run (state {self._session_state.name}): "
                    "frames are no longer reaching the headset. Was Link disconnected, "
                    "the headset put to sleep, or the app closed from the headset menu?")
            self._wait_for_resume()
        fs = xr.wait_frame(self.session)
        xr.begin_frame(self.session)
        self._poll_input()
        self._frame_state = fs
        self._frame_index += 1
        period = fs.predicted_display_period
        self._frame_step_ns = None
        displayed = self._session_state in (xr.SessionState.VISIBLE, xr.SessionState.FOCUSED)
        if displayed and self._last_pdt is not None and period > 0:
            step = fs.predicted_display_time - self._last_pdt
            self._frame_step_ns = step
            if step > 1.5 * period:
                self._missed_vsyncs += int(round(step / period)) - 1
                self._missed_events += 1
                self._longest_step_ms = max(self._longest_step_ms, step / 1e6)
                self.app_dropped_max = self._missed_vsyncs
            elif step < 0.5 * period:
                self._zero_steps += 1
        self._last_pdt = fs.predicted_display_time if displayed else None
        self._locate_views(fs.predicted_display_time)
        if fs.should_render:
            self._bind_view(0, clear=True)
        else:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def _locate_views(self, display_time):
        xr = self._xr
        _, views = xr.locate_views(
            session=self.session,
            view_locate_info=xr.ViewLocateInfo(
                view_configuration_type=self._view_config,
                display_time=display_time,
                space=self.space))
        self._views = list(views)
        w, h = self._eye_size
        layer_views = tuple(xr.CompositionLayerProjectionView() for _ in views)
        for i, view in enumerate(views):
            lv = layer_views[i]
            lv.pose = view.pose
            lv.fov = view.fov
            lv.sub_image.swapchain = self._swapchains[i]
            lv.sub_image.image_rect.offset[:] = [0, 0]
            lv.sub_image.image_rect.extent[:] = [w, h]
        self._layer_views = layer_views
        self._layer = xr.CompositionLayerProjection(space=self.space)
        self._layer.views = layer_views

    def _attach_draw_target(self, texture):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._draw_fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                                  GL.GL_TEXTURE_2D, texture, 0)

    def _acquire_view(self, index):
        xr = self._xr
        if index in self._acquired:
            return self._acquired[index]
        handle = self._swapchains[index]
        image_index = xr.acquire_swapchain_image(
            swapchain=handle, acquire_info=xr.SwapchainImageAcquireInfo())
        xr.wait_swapchain_image(
            swapchain=handle,
            wait_info=xr.SwapchainImageWaitInfo(timeout=xr.INFINITE_DURATION))
        texture = self._swapchain_images[index][image_index].image
        self._acquired[index] = texture
        return texture

    def _bind_view(self, index, clear):
        texture = self._acquire_view(index)
        self._attach_draw_target(texture)
        self._bound = index
        w, h = self._eye_size
        if self._bound_size != (w, h):
            self.viewport = self.scissor = (0, 0, w, h)
            self._bound_size = (w, h)
        GL.glEnable(GL.GL_SCISSOR_TEST)
        if clear:
            if self._passthrough_on:
                GL.glClearColor(0.0, 0.0, 0.0, 0.0)
            else:
                r, g, b, _ = self._color.rgba1
                GL.glClearColor(r, g, b, 1.0)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glDisable(GL.GL_TEXTURE_2D)

    def _blit(self, src_texture, dst_fbo, dst_size):
        w, h = self._eye_size
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self._copy_fbo)
        GL.glFramebufferTexture2D(GL.GL_READ_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                                  GL.GL_TEXTURE_2D, src_texture, 0)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dst_fbo)
        GL.glDisable(GL.GL_SCISSOR_TEST)
        GL.glBlitFramebuffer(0, 0, w, h, 0, 0, dst_size[0], dst_size[1],
                             GL.GL_COLOR_BUFFER_BIT, GL.GL_LINEAR)

    def _submit_frame(self):
        xr = self._xr
        fs = self._frame_state
        if fs is None:
            return
        layers = []
        if fs.should_render and self._views is not None:
            if self._monoscopic or 1 not in self._acquired:
                source = self._acquire_view(0)
                target = self._acquire_view(1)
                self._attach_draw_target(target)
                self._blit(source, self._draw_fbo, self._eye_size)
            mirror = self._acquired.get(0)
            n = self.mirror_swap_every
            if mirror is not None and n and (self._mirror_swap_counter + 1) % n == 0:
                self._blit(mirror, 0, tuple(int(v) for v in self.clientSize))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            for index in list(self._acquired):
                xr.release_swapchain_image(
                    swapchain=self._swapchains[index],
                    release_info=xr.SwapchainImageReleaseInfo())
            if self._passthrough_on:
                self._layer.layer_flags = xr.CompositionLayerFlags.BLEND_TEXTURE_SOURCE_ALPHA_BIT
                layers = [ctypes.byref(self._passthrough_composition), ctypes.byref(self._layer)]
            else:
                layers = [ctypes.byref(self._layer)]
        xr.end_frame(self.session, frame_end_info=xr.FrameEndInfo(
            display_time=fs.predicted_display_time,
            environment_blend_mode=xr.EnvironmentBlendMode.OPAQUE,
            layers=layers))
        self.last_predicted_display_time_s = self._xr_time_to_s(fs.predicted_display_time)
        self.last_runtime_time_s = time.perf_counter()
        self.last_display_period_ms = fs.predicted_display_period / 1e6
        self.last_frame_step_ms = (None if self._frame_step_ns is None
                                   else self._frame_step_ns / 1e6)
        self._acquired = {}
        self._bound = None
        self._frame_state = None

    def _setup_input(self):
        xr = self._xr
        self._input_enabled = False
        try:
            paths = {name: xr.string_to_path(self.instance, text)
                     for name, text in HAND_PATHS.items()}
            self._input_paths = paths
            subs = [paths['left'], paths['right'], paths['gamepad']]

            def make(name, kind, subaction_paths):
                return xr.create_action(
                    action_set=self._action_set,
                    create_info=xr.ActionCreateInfo(
                        action_name=name, action_type=kind,
                        subaction_paths=subaction_paths,
                        localized_action_name=name))

            actions = {'trigger': make('trigger', xr.ActionType.FLOAT_INPUT,
                                       [paths['left'], paths['right']]),
                       'xbox_trigger_left': make('xbox_trigger_left',
                                                 xr.ActionType.FLOAT_INPUT, None),
                       'xbox_trigger_right': make('xbox_trigger_right',
                                                  xr.ActionType.FLOAT_INPUT, None)}
            for button in BUTTON_HANDS:
                actions[button] = make('button_' + button.lower(),
                                       xr.ActionType.BOOLEAN_INPUT, subs)
            self._actions = actions
        except Exception as e:
            logging.warning("[openxr] controller actions unavailable, keyboard only: %s", e)
            return

        def bind(action, text):
            return xr.ActionSuggestedBinding(action, xr.string_to_path(self.instance, text))

        touch = [bind(actions['trigger'], HAND_PATHS[hand] + '/input/trigger/value')
                 for hand in ('left', 'right')]
        touch += [bind(actions[button], HAND_PATHS[hand] + f'/input/{button.lower()}/click')
                  for button, hand in BUTTON_HANDS.items()]
        xbox = [bind(actions['xbox_trigger_left'],
                     HAND_PATHS['gamepad'] + '/input/trigger_left/value'),
                bind(actions['xbox_trigger_right'],
                     HAND_PATHS['gamepad'] + '/input/trigger_right/value')]
        xbox += [bind(actions[button], HAND_PATHS['gamepad'] + f'/input/{button.lower()}/click')
                 for button in BUTTON_HANDS]
        for profile, bindings in ((TOUCH_PROFILE, touch), (XBOX_PROFILE, xbox)):
            try:
                xr.suggest_interaction_profile_bindings(
                    instance=self.instance,
                    suggested_bindings=xr.InteractionProfileSuggestedBinding(
                        interaction_profile=xr.string_to_path(self.instance, profile),
                        suggested_bindings=bindings))
                self._input_enabled = True
            except Exception as e:
                logging.warning("[openxr] could not bind %s: %s", profile, e)
        if not self._input_enabled:
            logging.warning("[openxr] no controller bindings accepted, keyboard only")

    def _read_boolean(self, action, subaction_path):
        xr = self._xr
        state = xr.get_action_state_boolean(
            self.session, xr.ActionStateGetInfo(action, subaction_path))
        return bool(state.is_active and state.current_state)

    def _read_float(self, action, subaction_path):
        xr = self._xr
        state = xr.get_action_state_float(
            self.session, xr.ActionStateGetInfo(action, subaction_path))
        return float(state.current_state) if state.is_active else 0.0

    def _clear_input(self):
        self._prev_buttons = {}
        self._buttons = {}
        self._triggers = {}

    def _poll_input(self):
        if not self._input_enabled or not self._session_running:
            return
        xr = self._xr
        if self._session_state != xr.SessionState.FOCUSED:
            self._clear_input()
            return
        paths = self._input_paths
        actions = self._actions
        try:
            xr.sync_actions(self.session, xr.ActionsSyncInfo(
                active_action_sets=[xr.ActiveActionSet(self._action_set, 0)]))
            triggers = {
                'left': self._read_float(actions['trigger'], paths['left']),
                'right': self._read_float(actions['trigger'], paths['right']),
                'xbox_left': self._read_float(actions['xbox_trigger_left'], 0),
                'xbox_right': self._read_float(actions['xbox_trigger_right'], 0)}
            buttons = {}
            for button, hand in BUTTON_HANDS.items():
                for source in (hand, 'gamepad'):
                    buttons[(button, source)] = self._read_boolean(
                        actions[button], paths[source])
        except xr.SessionNotFocused:
            self._clear_input()
            return
        except Exception as e:
            logging.warning("[openxr] controller poll failed, keyboard only: %s", e)
            self._input_enabled = False
            return
        self._prev_buttons = self._buttons
        self._buttons = buttons
        self._triggers = triggers
        self._input_poll_time_s = time.perf_counter()

    @staticmethod
    def _check_controller(controller):
        if (controller != 'Xbox' and controller not in TOUCH_CONTROLLER_HANDS
                and controller not in INERT_CONTROLLERS):
            raise KeyError(controller)

    @staticmethod
    def _button_source(controller, button):
        if controller == 'Xbox':
            return 'gamepad' if button in BUTTON_HANDS else None
        hand = BUTTON_HANDS.get(button)
        if hand is not None and hand in TOUCH_CONTROLLER_HANDS.get(controller, ()):
            return hand
        return None

    def updateInputState(self, controllers=None):
        if controllers is not None:
            if not isinstance(controllers, (list, tuple)):
                raise TypeError("Argument 'controllers' must be iterable type.")
            for name in controllers:
                self._check_controller(name)
        self._poll_input()

    def getIndexTriggerValues(self, controller='Xbox', deadzone=False):
        self._check_controller(controller)
        triggers = self._triggers
        if controller == 'Xbox':
            values = (triggers.get('xbox_left', 0.0), triggers.get('xbox_right', 0.0))
        else:
            hands = TOUCH_CONTROLLER_HANDS.get(controller, ())
            values = tuple(triggers.get(hand, 0.0) if hand in hands else 0.0
                           for hand in ('left', 'right'))
        if deadzone:
            values = tuple(v if v > TRIGGER_DEADZONE else 0.0 for v in values)
        return values

    def getButtons(self, buttons, controller='Xbox', testState='continuous'):
        self._check_controller(controller)
        if isinstance(buttons, str):
            names = [buttons]
        elif isinstance(buttons, (list, tuple)):
            names = list(buttons)
        else:
            raise ValueError("Invalid 'buttons' specified.")
        for name in names:
            if name not in BUTTON_HANDS and name not in INERT_BUTTONS:
                raise KeyError(name)
        if testState not in TEST_STATES:
            raise ValueError(f"Invalid testState '{testState}'.")
        mode = TEST_STATES[testState]
        result = bool(names)
        for name in names:
            source = self._button_source(controller, name)
            if source is None:
                result = False
                continue
            now = self._buttons.get((name, source), False)
            before = self._prev_buttons.get((name, source), False)
            if mode == 'continuous':
                hit = now
            elif mode == 'pressed':
                hit = now and not before
            else:
                hit = before and not now
            result = result and hit
        return result, self._input_poll_time_s

    def setBuffer(self, buffer, clear=True):
        if buffer not in EYE_INDEX:
            raise RuntimeError("Invalid buffer name specified.")
        self.buffer = buffer
        if self._monoscopic or self._frame_state is None or not self._frame_state.should_render:
            return
        self._bind_view(EYE_INDEX[buffer], clear=clear)

    def flip(self, clearBuffer=True):
        if not self._xr_ready:
            return super().flip(clearBuffer)
        self._submit_frame()
        self._mirror_swap_counter += 1
        self._context.present()
        self._begin_frame()
        if clearBuffer and self._bound is None:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        now = psy_logging.defaultClock.getTime()
        self._frameTime = now
        n_items = len(self._toCall)
        for i in range(n_items):
            self._toCall[i]['function'](*self._toCall[i]['args'],
                                        **self._toCall[i]['kwargs'])
        del self._toCall[:n_items]
        if self.recordFrameIntervals:
            self.frames += 1
            deltaT = now - self.lastFrameT
            self.lastFrameT = now
            if self.recordFrameIntervalsJustTurnedOn:
                self.recordFrameIntervalsJustTurnedOn = False
            else:
                self.frameIntervals.append(deltaT)
                if deltaT > self.refreshThreshold:
                    self.nDroppedFrames += 1
        for entry in self._toLog:
            psy_logging.log(msg=entry['msg'], level=entry['level'], t=now,
                            obj=entry['obj'])
        del self._toLog[:]
        return now

    def close(self):
        xr = self._xr
        try:
            if self._frame_state is not None:
                self._submit_frame()
        except Exception:
            pass
        for handle in getattr(self, '_swapchains', None) or []:
            try:
                xr.destroy_swapchain(handle)
            except Exception:
                pass
        self._swapchains = []
        for attr, destroy in (('_passthrough_layer', xr.destroy_passthrough_layer_fb),
                              ('_passthrough', xr.destroy_passthrough_fb),
                              ('_action_set', xr.destroy_action_set),
                              ('space', xr.destroy_space),
                              ('session', xr.destroy_session),
                              ('instance', xr.destroy_instance)):
            handle = getattr(self, attr, None)
            if handle is not None:
                try:
                    destroy(handle)
                except Exception:
                    pass
                setattr(self, attr, None)
        super().close()

    @property
    def passthrough_available(self):
        return self._xr.FB_PASSTHROUGH_EXTENSION_NAME in self._extensions

    @property
    def passthrough_on(self):
        return self._passthrough_on

    def set_passthrough(self, enabled):
        """Show the headset cameras wherever the submitted frame is transparent.

        While on, eye buffers clear to transparent rather than to the window
        colour and the projection layer is alpha-blended over a passthrough
        layer, so only what is drawn hides the room. Needs the runtime's
        ``XR_FB_passthrough``; over Link the Meta app may also need passthrough
        over Link enabled. Returns whether passthrough is now on.
        """
        xr = self._xr
        enabled = bool(enabled)
        if enabled == self._passthrough_on:
            return enabled
        if enabled and not self.passthrough_available:
            logging.warning("[openxr] the runtime offers no passthrough; the frame stays opaque")
            return False
        try:
            if enabled:
                if self._passthrough is None:
                    self._passthrough = xr.create_passthrough_fb(
                        self.session, xr.PassthroughCreateInfoFB(flags=xr.PassthroughFlagsFB.NONE))
                    self._passthrough_layer = xr.create_passthrough_layer_fb(
                        self.session, xr.PassthroughLayerCreateInfoFB(
                            passthrough=self._passthrough, flags=xr.PassthroughFlagsFB.NONE,
                            purpose=xr.PassthroughLayerPurposeFB.RECONSTRUCTION))
                    self._passthrough_composition = xr.CompositionLayerPassthroughFB(
                        layer_handle=self._passthrough_layer)
                xr.passthrough_start_fb(self._passthrough)
                xr.passthrough_layer_resume_fb(self._passthrough_layer)
            else:
                xr.passthrough_layer_pause_fb(self._passthrough_layer)
                xr.passthrough_pause_fb(self._passthrough)
        except Exception as e:
            logging.warning("[openxr] passthrough %s failed: %s",
                            'start' if enabled else 'pause', e)
            if enabled:
                return False
        self._passthrough_on = enabled
        logging.info("[openxr] passthrough %s", 'on' if enabled else 'off')
        return enabled

    def setDefaultView(self, clearDepth=True):
        if self.USE_LEGACY_GL:
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glOrtho(-1, 1, -1, 1, -1, 1)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
        if clearDepth:
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    @property
    def displayRefreshRate(self):
        if self._refresh_rate_hz:
            return self._refresh_rate_hz
        if self.last_display_period_ms:
            return 1000.0 / self.last_display_period_ms
        fs = self._frame_state
        if fs is not None and fs.predicted_display_period > 0:
            return 1e9 / fs.predicted_display_period
        return 0.0

    @property
    def eye_fov(self):
        """Per-view field of view ``(left, right, up, down)`` in radians."""
        if not self._views:
            return None
        return [(v.fov.angle_left, v.fov.angle_right, v.fov.angle_up, v.fov.angle_down)
                for v in self._views]

    def compute_optical_axis_offsets(self):
        """Normalized-device x offset of each eye's optical axis.

        The lenses are asymmetric — the view extends further to the outside of
        the eye than the inside — so NDC (0, 0) is not the optical axis. Same
        formula the LibOVR backend used, from the view fov tangents.
        """
        fov = self.eye_fov
        if not fov:
            logging.warning("[openxr] no views yet; optical axis offsets unknown")
            return (0.0, 0.0)
        out = []
        for left, right, _, _ in fov[:2]:
            tan_l, tan_r = -math.tan(left), math.tan(right)
            out.append((tan_l - tan_r) / (tan_l + tan_r))
        return tuple(out)

    def eye_separation_mm(self):
        """Distance between the two view poses in millimetres, or ``None`` before they are located."""
        views = self._views
        if not views or len(views) < 2:
            return None
        return abs(views[1].pose.position.x - views[0].pose.position.x) * 1000.0

    def _nasal_tangent(self, view, centre, distance_m):
        return (centre - view.pose.position.x) / distance_m

    def offsets_at_distance(self, distance_m, strict=False):
        """Normalized-device x, per eye, of a point ``distance_m`` straight ahead.

        ``compute_optical_axis_offsets`` is the same at infinite distance. A
        nearer point sits nasally of each eye's optical axis by the eye's half of
        the interpupillary distance, taken from the view poses, so text drawn at
        these offsets converges at ``distance_m`` instead of at infinity.

        Poses exist only once a frame has been begun. Without them this falls
        back to the infinite-distance offsets, unless ``strict`` is set, which
        raises instead: a stimulus placed from the fallback would sit at
        infinity while the caller believes it is at ``distance_m``.
        """
        fov = self.eye_fov
        views = self._views
        if not fov or not views or len(views) < 2:
            if strict:
                raise RuntimeError(
                    f"view poses are not located yet; cannot place a stimulus at {distance_m} m")
            return self.compute_optical_axis_offsets()
        centre = (views[0].pose.position.x + views[1].pose.position.x) / 2
        out = []
        for view, (left, right, _, _) in zip(views[:2], fov[:2]):
            tan_l, tan_r = -math.tan(left), math.tan(right)
            tan_point = self._nasal_tangent(view, centre, distance_m)
            out.append((2 * tan_point + tan_l - tan_r) / (tan_l + tan_r))
        return tuple(out)

    def nasal_shift_deg(self, distance_m):
        """Signed angle, per eye, from its optical axis to a point ``distance_m`` ahead.

        Positive is rightwards, so the left eye is positive and the right eye
        negative for any finite distance. Needs located poses.
        """
        views = self._views
        if not views or len(views) < 2:
            raise RuntimeError("view poses are not located yet")
        centre = (views[0].pose.position.x + views[1].pose.position.x) / 2
        return tuple(math.degrees(math.atan(self._nasal_tangent(v, centre, distance_m)))
                     for v in views[:2])

    def pixels_per_degree(self):
        """(ppd_horizontal, ppd_vertical) at the view centre, from view 0."""
        fov = self.eye_fov
        if not fov:
            return None, None
        left, right, up, down = fov[0]
        w, h = self._eye_size
        ppta_h = w / (math.tan(right) - math.tan(left))
        ppta_v = h / (math.tan(up) - math.tan(down))
        return ppta_h * math.pi / 180.0, ppta_v * math.pi / 180.0

    def log_display_info(self):
        """Log IPD and pixels-per-degree; returns ``(ppd, ipd_mm)``."""
        ppd_h, ppd_v = self.pixels_per_degree()
        if ppd_h is None:
            logging.warning("[openxr] no views yet; display info unknown")
            return None, None
        ppd = int(round(min(ppd_h, ppd_v)))
        ipd_mm = None
        if self._views and len(self._views) >= 2:
            ipd_mm = abs(self._views[1].pose.position.x
                         - self._views[0].pose.position.x) * 1000.0
        logging.info("[openxr] IPD=%s mm  ppd=%d (h=%.1f v=%.1f)  eye_buf=%s",
                     f"{ipd_mm:.1f}" if ipd_mm is not None else "?",
                     ppd, ppd_h, ppd_v, self._eye_size)
        self.timing_data.insert(0, ['# ipd_mm', ipd_mm, 'ppd', ppd,
                                    f'ppd_h={ppd_h:.1f} ppd_v={ppd_v:.1f}'])
        return ppd, ipd_mm

    def sync_vr_clock(self):
        """Wall-clock minus runtime-clock offset, from the tightest bracket.

        The predicted display times are on ``time.perf_counter``'s clock;
        markers carry ``time.time()``. Analysis adds this offset to convert.
        """
        if self.runtime_to_wallclock_offset is not None:
            return self.runtime_to_wallclock_offset
        best_bracket = best_offset = None
        for _ in range(21):
            t0 = wall_time()
            pc = time.perf_counter()
            t1 = wall_time()
            bracket = t1 - t0
            if best_bracket is None or bracket < best_bracket:
                best_bracket, best_offset = bracket, 0.5 * (t0 + t1) - pc
        logging.info("[openxr] clock offset (wall - runtime) = %.6fs "
                     "(tightest bracket = %.3fms)", best_offset, best_bracket * 1e3)
        self.runtime_to_wallclock_offset = best_offset
        self.runtime_to_wallclock_bracket = best_bracket
        return best_offset

    def get_session_status(self):
        xr = self._xr
        state = self._session_state
        return {
            'is_visible': state in (xr.SessionState.VISIBLE, xr.SessionState.FOCUSED),
            'hmd_mounted': None,
            'has_input_focus': state == xr.SessionState.FOCUSED,
            'session_state': state.name,
        }

    def get_session_summary(self):
        summary = {
            'app_dropped': int(self.app_dropped_max),
            'missed_vsyncs': int(self._missed_vsyncs),
            'missed_vsync_events': int(self._missed_events),
            'longest_step_ms': round(self._longest_step_ms, 1),
            'repeated_predictions': int(self._zero_steps),
            'mirror_swap_every': int(self.mirror_swap_every),
            'runtime': self.runtime_name,
            'system': self.system_name,
            'eye_size_px': list(self._eye_size),
            'swapchain_format': int(self.swapchain_format),
        }
        summary['session_status'] = self.get_session_status()
        return summary

    def log_telemetry(self, trial_idx, software_time, marker=None):
        stat = {
            'marker': marker,
            'predicted_display_time_s': self.last_predicted_display_time_s,
            'runtime_time_s': self.last_runtime_time_s,
            'display_period_ms': self.last_display_period_ms,
            'frame_step_ms': self.last_frame_step_ms,
            'missed_vsyncs': self._missed_vsyncs,
            'session_state': self._session_state.name,
        }
        submitted_frame_index = self._frame_index - 1
        self.timing_data.append(
            [trial_idx, software_time, submitted_frame_index]
            + [stat[f] for f in self._DERIVED_TIMING_FIELDS])

    def save_telemetry(self, save_fn):
        if save_fn is None:
            return
        timing_path = save_fn.with_name(save_fn.stem + '_timing.csv')
        with open(timing_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trial_idx', 'software_time', 'submitted_frame_index']
                            + list(self._DERIVED_TIMING_FIELDS))
            writer.writerow(['# backend', 'openxr', 'runtime', self.runtime_name,
                             'system', self.system_name])
            if self.runtime_to_wallclock_offset is not None:
                writer.writerow(['# runtime_to_wallclock_offset_s',
                                 self.runtime_to_wallclock_offset,
                                 'bracket_ms', self.runtime_to_wallclock_bracket * 1000])
            writer.writerow(['# missed_vsyncs', self._missed_vsyncs,
                             'missed_vsync_events', self._missed_events,
                             'longest_step_ms', round(self._longest_step_ms, 1),
                             'repeated_predictions', self._zero_steps])
            writer.writerows(self.timing_data)
        print(f"  Saved VR timing telemetry to {timing_path}")
        print(f"  [openxr] {self._missed_events} late frames lost {self._missed_vsyncs} "
              f"vsyncs (longest gap {self._longest_step_ms:.0f} ms); a stall counts "
              f"every vsync it spans, so compare the event count against the frame "
              f"count for the rate")
