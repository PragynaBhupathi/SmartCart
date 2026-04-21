"""
SmartCart — Camera Scanner Module
Background thread: webcam capture + OpenCV barcode/QR detection.
No tkinter imports here — pure CV logic.
"""

import cv2
import threading
import time
import numpy as np
from config import SCAN_COOLDOWN, CAM_WIDTH, CAM_HEIGHT


class ScannerThread(threading.Thread):
    """
    Runs in background. Continuously reads webcam frames,
    detects barcodes (EAN, UPC, Code128, QR …),
    draws overlays, and fires on_scan(barcode_str) callback.

    Thread-safe: latest_frame protected by frame_lock.
    """

    def __init__(self, on_scan, camera_index=0):
        super().__init__(daemon=True, name="ScannerThread")
        self.on_scan      = on_scan
        self.camera_index = camera_index
        self.running      = False
        self.paused       = False

        self.frame_lock   = threading.Lock()
        self.latest_frame = None           # BGR numpy array
        self.last_scanned: dict[str, float] = {}

        # OpenCV detectors (built-in, no extra library)
        self._bd  = cv2.barcode.BarcodeDetector()
        self._qrd = cv2.QRCodeDetector()

        # Status
        self.cam_ok   = False
        self.fps      = 0.0
        self._fps_buf = []

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start_scanning(self, camera_index=None):
        if camera_index is not None:
            self.camera_index = camera_index
        self.running = True
        self.paused  = False
        if not self.is_alive():
            self.start()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        cap = self._open_camera()
        if cap is None:
            self.cam_ok = False
            return

        self.cam_ok = True
        t_prev = time.time()

        while self.running:
            if self.paused:
                time.sleep(0.05)
                continue

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # FPS calculation
            now   = time.time()
            dt    = now - t_prev
            t_prev = now
            self._fps_buf.append(1.0 / dt if dt > 0 else 0)
            if len(self._fps_buf) > 20:
                self._fps_buf.pop(0)
            self.fps = sum(self._fps_buf) / len(self._fps_buf)

            # Detect
            codes = self._detect(frame)

            # Draw overlays + fire callbacks
            self._draw_and_fire(frame, codes, now)

            # Store frame for GUI
            with self.frame_lock:
                self.latest_frame = frame

        cap.release()
        self.cam_ok = False

    # ── Camera open ───────────────────────────────────────────────────────────
    def _open_camera(self):
        for idx in [self.camera_index] + [i for i in range(5) if i != self.camera_index]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # minimal latency
                self.camera_index = idx
                return cap
        return None

    # ── Detection ─────────────────────────────────────────────────────────────
    def _detect(self, frame):
        """Returns list of (barcode_str, points_array_or_None)."""
        found = []

        # 1. Barcode detector (EAN-8/13, UPC, Code128, Code39 …)
        try:
            ok, decoded_list, _, points = self._bd.detectAndDecodeWithType(frame)
            if ok and decoded_list:
                for i, code in enumerate(decoded_list):
                    if code:
                        pts = points[i] if points is not None else None
                        found.append((code.strip(), pts))
        except Exception:
            pass

        # 2. QR code
        try:
            data, pts, _ = self._qrd.detectAndDecode(frame)
            if data:
                found.append((data.strip(), pts))
        except Exception:
            pass

        return found

    # ── Overlay + callback ────────────────────────────────────────────────────
    def _draw_and_fire(self, frame, codes, now):
        for code, pts in codes:
            if not code:
                continue

            # Draw bounding box
            if pts is not None:
                try:
                    pts_int = np.array(pts, dtype=int).reshape((-1, 1, 2))
                    # Glow effect: thick dim + thin bright
                    cv2.polylines(frame, [pts_int], True, (108, 99, 255), 6)
                    cv2.polylines(frame, [pts_int], True, (180, 175, 255), 2)

                    # Label badge
                    x = int(pts_int[:, 0, 0].min())
                    y = int(pts_int[:, 0, 1].min()) - 12
                    label = code[:28]
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                    cv2.rectangle(frame, (x - 2, y - th - 4),
                                  (x + tw + 4, y + 2), (108, 99, 255), -1)
                    cv2.putText(frame, label, (x, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
                except Exception:
                    pass

            # Cooldown guard → fire callback
            if now - self.last_scanned.get(code, 0) >= SCAN_COOLDOWN:
                self.last_scanned[code] = now
                try:
                    self.on_scan(code)
                except Exception:
                    pass

    # ── Utility ───────────────────────────────────────────────────────────────
    def get_frame(self):
        """Thread-safe frame grab. Returns BGR numpy array or None."""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def reset_cooldown(self, barcode=None):
        """Allow immediate re-scan of barcode (or all if None)."""
        if barcode:
            self.last_scanned.pop(barcode, None)
        else:
            self.last_scanned.clear()
