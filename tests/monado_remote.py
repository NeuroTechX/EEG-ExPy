import ctypes as C
import socket
import time

PORT = 4242
HEADER = int.from_bytes(b"mndrmt3\0", "little")


class Quat(C.Structure):
    _fields_ = [("x", C.c_float), ("y", C.c_float), ("z", C.c_float), ("w", C.c_float)]


class Vec3(C.Structure):
    _fields_ = [("x", C.c_float), ("y", C.c_float), ("z", C.c_float)]


class Pose(C.Structure):
    _fields_ = [("orientation", Quat), ("position", Vec3)]


class Fov(C.Structure):
    _fields_ = [("left", C.c_float), ("right", C.c_float), ("up", C.c_float), ("down", C.c_float)]


class View(C.Structure):
    _fields_ = [("fov", Fov), ("pose", Pose), ("_pad", C.c_uint32)]


class Head(C.Structure):
    _fields_ = [("views", View * 2), ("center", Pose), ("per_view_data_valid", C.c_bool),
                ("_pad", C.c_bool * 3)]


class Controller(C.Structure):
    _fields_ = [("pose", Pose), ("linear_velocity", Vec3), ("angular_velocity", Vec3),
                ("hand_curl", C.c_float * 5),
                ("trigger_value", C.c_float), ("squeeze_value", C.c_float),
                ("squeeze_force", C.c_float), ("thumbstick", C.c_float * 2),
                ("trackpad_force", C.c_float), ("trackpad", C.c_float * 2),
                ("hand_tracking_active", C.c_bool), ("active", C.c_bool),
                ("system_click", C.c_bool), ("system_touch", C.c_bool),
                ("a_click", C.c_bool), ("a_touch", C.c_bool),
                ("b_click", C.c_bool), ("b_touch", C.c_bool),
                ("trigger_click", C.c_bool), ("trigger_touch", C.c_bool),
                ("thumbstick_click", C.c_bool), ("thumbstick_touch", C.c_bool),
                ("trackpad_touch", C.c_bool), ("_pad", C.c_bool * 3)]


class RemoteData(C.Structure):
    _fields_ = [("header", C.c_uint64), ("head", Head), ("left", Controller), ("right", Controller)]


assert C.sizeof(Head) == 128 and C.sizeof(Controller) == 120 and C.sizeof(RemoteData) == 376


def _connect(host, port, timeout):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return socket.create_connection((host, port), timeout=timeout)
        except ConnectionRefusedError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.05)


class MonadoRemote:
    def __init__(self, host="127.0.0.1", port=PORT, timeout=5.0):
        self.sock = _connect(host, port, timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.reset = self._read()
        self.state = self._read()
        q = self.reset.head.center.orientation
        norm = (q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w) ** 0.5
        if abs(norm - 1.0) > 1e-3:
            raise RuntimeError(f"remote driver reset pose is not a unit quaternion ({norm}): "
                               "wire format differs from Monado 25")

    def _read(self):
        buf = bytearray()
        size = C.sizeof(RemoteData)
        while len(buf) < size:
            chunk = self.sock.recv(size - len(buf))
            if not chunk:
                raise ConnectionError("remote driver closed the connection")
            buf += chunk
        return RemoteData.from_buffer_copy(bytes(buf))

    def send(self):
        self.state.header = HEADER
        self.sock.sendall(bytes(self.state))

    def clear(self):
        self.state = RemoteData.from_buffer_copy(bytes(self.reset))
        self.state.left.active = self.state.right.active = True
        self.send()

    def close(self):
        self.sock.close()
