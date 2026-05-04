import logging
import numpy as np
from time import time
from psychopy.visual.rift import Rift

class VR(Rift):
    """
    Extended VR class for HMDs, providing built-in methods for
    stereoscopic rendering math, precise hardware clock synchronization,
    and per-trial compositor telemetry buffering.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.libovr_to_wallclock_offset = None

    def compute_optical_axis_offsets(self):
        """
        NDC x offsets placing content on each lens's optical axis:
        ndc_x = (LeftTan - RightTan) / (LeftTan + RightTan).
        """
        try:
            import psychxr.drivers.libovr as libovr
            # fov = [UpTan, DownTan, LeftTan, RightTan]
            left_fov, _, _ = libovr.getEyeRenderFov(libovr.EYE_LEFT)
            right_fov, _, _ = libovr.getEyeRenderFov(libovr.EYE_RIGHT)
            left_L, left_R = float(left_fov[2]), float(left_fov[3])
            right_L, right_R = float(right_fov[2]), float(right_fov[3])
            return ((left_L - left_R) / (left_L + left_R),
                    (right_L - right_R) / (right_L + right_R))
        except Exception as e:
            logging.warning(f"[VR] Failed to compute optical axis offsets: {e}")
            return (0.0, 0.0)

    def sync_vr_clock(self):
        """
        Calculates Wall-clock <-> LibOVR clock offset. LibOVR timestamps are on a QPC-based
        clock with arbitrary zero; time.time() is Unix epoch. Sample paired calls in a 
        tight bracket and keep the tightest, so analysis can convert LibOVR times to wall-clock.
        """
        if self.libovr_to_wallclock_offset is not None:
            return self.libovr_to_wallclock_offset

        try:
            from psychxr.drivers.libovr import timeInSeconds
            best_bracket = None
            best_offset = None
            for _ in range(21):
                t0 = time()
                lovr = timeInSeconds()
                t1 = time()
                bracket = t1 - t0
                offset = 0.5 * (t0 + t1) - lovr
                if best_bracket is None or bracket < best_bracket:
                    best_bracket = bracket
                    best_offset = offset
            
            logging.info(
                f"[VR] clock offset (wall - libovr) = "
                f"{best_offset:.6f}s  (tightest bracket = {best_bracket*1e3:.3f}ms)"
            )
            
            self.libovr_to_wallclock_offset = best_offset
            return best_offset
        except Exception as e:
            logging.warning(f"[VR] LibOVR clock sync failed: {e}")
            return None

    def log_display_info(self):
        """
        Reads IPD, PPD, and display resolution from the LibOVR session and logs
        them to the telemetry sidecar as header comment rows.
        Returns (ppd, ipd_mm) for use in stimulus sizing.
        """
        try:
            ppta = self.pixelsPerTanAngleAtCenter
            ppd_h = np.mean([p[0] for p in ppta]) * (np.pi / 180.0)
            ppd_v = np.mean([p[1] for p in ppta]) * (np.pi / 180.0)
            ppd = int(round(min(ppd_h, ppd_v)))

            eye_to_nose = self.eyeToNoseDistance
            ipd_mm = (eye_to_nose[0] + eye_to_nose[1]) * 1000.0

            logging.info(
                f"[VR] IPD={ipd_mm:.1f}mm  ppd={ppd} (h={ppd_h:.1f} v={ppd_v:.1f})  "
                f"res={self.displayResolution}  eye_buf={self.size}"
            )

            if not hasattr(self, 'timing_data'):
                self.timing_data = []
            self.timing_data.insert(0, ['# ipd_mm', ipd_mm, 'ppd', ppd, f'ppd_h={ppd_h:.1f} ppd_v={ppd_v:.1f}'])

            return ppd, ipd_mm
        except Exception as e:
            logging.warning(f"[VR] Failed to read display info: {e}")
            return None, None

    def log_telemetry(self, trial_idx, software_time):
        """Extracts native LibOVR performance stats and buffers them in memory."""
        submitted_frame_index = None
        app_frame_index = None
        app_m2p_s = None
        comp_latency_s = None
        time_to_vsync_s = None
        
        try:
            submitted_frame_index = self._frameIndex - 1
            perf = getattr(self, '_perfStats', None)
            if perf is not None and perf.frameStatsCount > 0:
                stat = perf.frameStats[0]
                app_frame_index = stat.appFrameIndex
                app_m2p_s = stat.appMotionToPhotonLatency
                comp_latency_s = stat.compositorLatency
                time_to_vsync_s = stat.timeToVsync
        except Exception:
            pass
        
        if not hasattr(self, 'timing_data'):
            self.timing_data = []
            
        self.timing_data.append([
            trial_idx, software_time,
            submitted_frame_index, app_frame_index,
            app_m2p_s, comp_latency_s, time_to_vsync_s
        ])

    def save_telemetry(self, save_fn):
        """Saves memory-buffered VR timing telemetry to a CSV sidecar."""
        timing_data = getattr(self, 'timing_data', [])
        if not timing_data:
            return
            
        import csv
        timing_path = save_fn.with_name(save_fn.stem + '_timing.csv') if save_fn else 'vr_timing.csv'
        with open(timing_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'trial_idx', 'software_time',
                'submitted_frame_index', 'app_frame_index',
                'app_motion_to_photon_latency_s', 'compositor_latency_s',
                'time_to_vsync_s'
            ])
            
            # Log the clock offset if calculated
            if self.libovr_to_wallclock_offset is not None:
                 writer.writerow(['# libovr_to_wallclock_offset_s', self.libovr_to_wallclock_offset, 'bracket_ms', 0])
                 
            writer.writerows(timing_data)
        print(f"  Saved VR timing telemetry to {timing_path}")
