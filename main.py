import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

import cv2
from pynput.keyboard import Controller, Key

CHECK_INTERVAL_S = 0.5
TRIGGER_COOLDOWN_S = 3.0


@dataclass
class DetectionResult:
    faces: int
    triggered: bool


class FaceMonitor:
    def __init__(self, camera_index: int, key_name: str, status_callback):
        self.camera_index = camera_index
        self.key_name = key_name
        self.status_callback = status_callback
        self.stop_event = threading.Event()
        self.thread = None
        self.keyboard = Controller()
        self.last_trigger = 0.0
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.status_callback("无法打开摄像头，请检查索引或权限。")
            return
        self.status_callback("监控中：每 0.5 秒检测一次。")
        while not self.stop_event.is_set():
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                self.status_callback("摄像头读取失败，正在重试……")
                time.sleep(CHECK_INTERVAL_S)
                continue
            result = self._detect_and_trigger(frame)
            if result.faces >= 0:
                message = f"检测到 {result.faces} 张人脸"
                if result.triggered:
                    message += "，已触发按键。"
                self.status_callback(message)
            elapsed = time.time() - start_time
            if elapsed < CHECK_INTERVAL_S:
                time.sleep(CHECK_INTERVAL_S - elapsed)
        cap.release()
        self.status_callback("已停止监控。")

    def _detect_and_trigger(self, frame) -> DetectionResult:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
        triggered = False
        if len(faces) >= 2 and self._cooldown_ready():
            triggered = self._trigger_key()
            if triggered:
                self.last_trigger = time.time()
        return DetectionResult(faces=len(faces), triggered=triggered)

    def _cooldown_ready(self) -> bool:
        return (time.time() - self.last_trigger) >= TRIGGER_COOLDOWN_S

    def _trigger_key(self) -> bool:
        key = parse_key(self.key_name)
        if key is None:
            self.status_callback("按键无效：请设置为单个字符或常用按键名。")
            return False
        self.keyboard.press(key)
        self.keyboard.release(key)
        return True


KEY_MAPPING = {
    "space": Key.space,
    "enter": Key.enter,
    "return": Key.enter,
    "tab": Key.tab,
    "esc": Key.esc,
    "escape": Key.esc,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "control": Key.ctrl,
    "alt": Key.alt,
    "cmd": Key.cmd,
    "win": Key.cmd,
    "capslock": Key.caps_lock,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "home": Key.home,
    "end": Key.end,
    "pageup": Key.page_up,
    "pagedown": Key.page_down,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
}


def parse_key(key_text: str):
    if not key_text:
        return None
    key_text = key_text.strip().lower()
    if key_text in KEY_MAPPING:
        return KEY_MAPPING[key_text]
    if len(key_text) == 1:
        return key_text
    return None


class AppUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Notice When It In Danger")
        self.root.geometry("420x240")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="等待启动…")
        self.key_var = tk.StringVar(value="space")
        self.camera_var = tk.StringVar(value="0")
        self.monitor = None

        self._build_layout()

    def _build_layout(self):
        padding = {"padx": 12, "pady": 6}
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        title = ttk.Label(main_frame, text="双人检测触发器", font=("Arial", 14, "bold"))
        title.pack(pady=12)

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", **padding)

        ttk.Label(form_frame, text="触发按键：").grid(row=0, column=0, sticky="w")
        key_entry = ttk.Entry(form_frame, textvariable=self.key_var, width=20)
        key_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(form_frame, text="摄像头索引：").grid(row=1, column=0, sticky="w", pady=8)
        camera_entry = ttk.Entry(form_frame, textvariable=self.camera_var, width=20)
        camera_entry.grid(row=1, column=1, sticky="w", pady=8)

        hint = ttk.Label(
            form_frame,
            text="支持按键名：space、enter、esc、f1~f12 或单个字符",
            foreground="#555",
        )
        hint.grid(row=2, column=0, columnspan=2, sticky="w")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", **padding)

        start_button = ttk.Button(button_frame, text="开始", command=self.start)
        start_button.pack(side="left", padx=5)
        stop_button = ttk.Button(button_frame, text="停止", command=self.stop)
        stop_button.pack(side="left", padx=5)

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", **padding)
        ttk.Label(status_frame, text="状态：").pack(side="left")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left")

    def start(self):
        camera_index = self._parse_camera_index()
        if camera_index is None:
            self.status_var.set("摄像头索引无效，请输入数字。")
            return
        key_name = self.key_var.get().strip()
        if parse_key(key_name) is None:
            self.status_var.set("按键无效，请重新设置。")
            return
        if self.monitor:
            self.monitor.stop()
        self.monitor = FaceMonitor(camera_index, key_name, self._set_status)
        self.monitor.start()

    def stop(self):
        if self.monitor:
            self.monitor.stop()

    def _parse_camera_index(self):
        try:
            return int(self.camera_var.get().strip())
        except ValueError:
            return None

    def _set_status(self, message: str):
        self.root.after(0, lambda: self.status_var.set(message))


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    AppUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
