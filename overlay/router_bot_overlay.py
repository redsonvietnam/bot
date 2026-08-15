"""
9router Status Bot — desktop overlay mascot
=============================================
Cửa sổ nhỏ, trong suốt, luôn nổi trên cùng, hiển thị trạng thái kết nối/quota
của 9router (đọc từ endpoint /api/status của Flask app hiện có).

Tính năng:
- Kéo thả để đặt vị trí bất kỳ trên màn hình, vị trí được lưu lại giữa các lần chạy
- Ẩn/hiện qua system tray icon (click phải > Show/Hide), và double-click vào bot cũng ẩn tạm thời
- Click chuột trái vào bot -> mở dashboard 9router trên trình duyệt
- Animation khác nhau theo từng trạng thái: idle / active / warning / blocked / offline
- Poll trạng thái định kỳ từ API, tự chuyển sang "offline" (xám) nếu không gọi được

Cài đặt:
    pip install PyQt6 requests

Chạy:
    python router_bot_overlay.py

Cấu hình:
    Sửa các hằng số ở phần CONFIG bên dưới cho khớp với 9router của bạn.
"""

import sys
import os
import json
import math
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QIcon, QPixmap, QAction, QFont
)

try:
    import requests
except ImportError:
    requests = None


# ───────────────────────── CONFIG ─────────────────────────
STATUS_API_URL = "http://127.0.0.1:5000/api/status"   # sửa lại đúng endpoint 9router
DASHBOARD_URL = "http://127.0.0.1:5000/"               # mở khi click vào bot
POLL_INTERVAL_MS = 4000                                  # tần suất hỏi trạng thái
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".9router_bot", "config.json")
BOT_SIZE = 72                                             # kích thước widget (px)
VALID_STATES = {"idle", "active", "warning", "blocked", "offline"}

# Trạng thái mong đợi từ API: {"state": "idle|active|warning|blocked|offline", "detail": "..."}
STATE_COLORS = {
    "idle":    QColor(70, 110, 220),    # xanh dương dịu
    "active":  QColor(60, 190, 110),    # xanh lá
    "warning": QColor(230, 175, 40),    # vàng
    "blocked": QColor(220, 60, 60),     # đỏ
    "offline": QColor(120, 120, 120),   # xám
}


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def _parse_status_payload(data):
    if not isinstance(data, dict):
        raise ValueError("status response must be an object")

    state = data.get("state")
    if state not in VALID_STATES:
        raise ValueError("status response contains an unknown state")

    detail = data.get("detail", "")
    if not isinstance(detail, str):
        raise ValueError("status response contains an invalid detail")

    return state, detail


def _fetch_status():
    if requests is None:
        raise RuntimeError("requests is not installed")

    response = requests.get(STATUS_API_URL, timeout=2)
    response.raise_for_status()
    return _parse_status_payload(response.json())


class RouterBot(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "offline"
        self.detail = "Chưa kết nối"
        self._drag_offset = None
        self._dragged = False  # phân biệt kéo vs click
        self._t = 0.0  # thời gian nội bộ cho animation (giây, cộng dồn)

        self._setup_window()
        self._restore_position()

        # Timer animation (~30 fps)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick_animation)
        self.anim_timer.start(33)

        # Timer poll trạng thái
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_status)
        self.poll_timer.start(POLL_INTERVAL_MS)
        self.poll_status()  # gọi ngay lần đầu

    def closeEvent(self, event):
        """Stop owned timers before the overlay is closed."""
        self.poll_timer.stop()
        self.anim_timer.stop()
        super().closeEvent(event)

    # ── window setup ──
    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # không hiện trên taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(BOT_SIZE + 60, BOT_SIZE + 35)  # chừa chỗ cho state + detail bên dưới

    def _restore_position(self):
        cfg = load_config()
        x = cfg.get("x")
        y = cfg.get("y")
        if x is not None and y is not None:
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.width() - BOT_SIZE - 40, screen.height() - BOT_SIZE - 100)

    def _save_position(self):
        save_config({"x": self.x(), "y": self.y()})

    # ── polling trạng thái ──
    def poll_status(self):
        if requests is None:
            self.state, self.detail = "offline", "Thiếu thư viện requests"
            self.update()
            return
        try:
            self.state, self.detail = _fetch_status()
        except requests.RequestException:
            self.state, self.detail = "offline", "Không kết nối được 9router"
        except (ValueError, RuntimeError):
            self.state, self.detail = "offline", "Phản hồi status không hợp lệ"
        self.setToolTip(f"{self.state.upper()} — {self.detail}")
        self.update()

    # ── animation ──
    def _tick_animation(self):
        self._t += 0.033
        self.update()

    def _offset_for_state(self):
        """Trả về (dx, dy, scale, shake) tuỳ trạng thái để paintEvent dùng."""
        if self.state == "idle":
            # nhấp nhô nhẹ nhàng
            dy = math.sin(self._t * 1.5) * 3
            return 0, dy, 1.0, 0
        if self.state == "active":
            # nảy nhanh hơn, hơi phóng to thu nhỏ (đang làm việc)
            dy = math.sin(self._t * 5) * 4
            scale = 1.0 + 0.03 * math.sin(self._t * 5)
            return 0, dy, scale, 0
        if self.state == "warning":
            # nhấp nháy chậm
            return 0, 0, 1.0, 0
        if self.state == "blocked":
            # rung lắc
            dx = math.sin(self._t * 25) * 2.5
            return dx, 0, 1.0, 1
        return 0, math.sin(self._t * 0.6) * 1, 0.95, 0  # offline: gần như đứng im, hơi mờ

    # ── vẽ bot ──
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        dx, dy, scale, _ = self._offset_for_state()
        color = STATE_COLORS.get(self.state, STATE_COLORS["offline"])

        # độ mờ nhấp nháy cho warning
        opacity = 1.0
        if self.state == "warning":
            opacity = 0.6 + 0.4 * abs(math.sin(self._t * 4))
        elif self.state == "offline":
            opacity = 0.55

        painter.setOpacity(opacity)

        cx, cy = BOT_SIZE / 2 + dx, BOT_SIZE / 2 + dy
        r = (BOT_SIZE / 2 - 6) * scale

        # thân bot (hình tròn bo góc kiểu pixel-art đơn giản)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(130), 2))
        painter.drawRoundedRect(
            QRectF(cx - r, cy - r, r * 2, r * 2), r * 0.35, r * 0.35
        )

        # "mặt" hiển thị icon trạng thái đơn giản (ký hiệu >_ giống ảnh mẫu, hoặc !)
        painter.setPen(QPen(QColor(230, 240, 255), 3))
        face_rect = QRectF(cx - r * 0.55, cy - r * 0.35, r * 1.1, r * 0.7)
        painter.setBrush(QBrush(QColor(20, 25, 45)))
        painter.drawRoundedRect(face_rect, 6, 6)

        painter.setPen(QPen(QColor(120, 220, 255), 2))
        if self.state == "blocked":
            painter.setPen(QPen(QColor(255, 90, 90), 3))
            painter.drawText(face_rect, Qt.AlignmentFlag.AlignCenter, "!")
        elif self.state == "offline":
            painter.drawText(face_rect, Qt.AlignmentFlag.AlignCenter, "×")
        else:
            painter.drawText(face_rect, Qt.AlignmentFlag.AlignCenter, ">_")

        # nhãn trạng thái nhỏ phía dưới (state + detail, không phụ thuộc vào tooltip)
        painter.setOpacity(1.0)
        painter.setPen(QColor(230, 230, 230))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, BOT_SIZE + 2, BOT_SIZE + 60, 14),
            Qt.AlignmentFlag.AlignCenter,
            self.state.upper(),
        )
        painter.setPen(QColor(180, 200, 230))
        painter.setFont(QFont("Segoe UI", 7))
        detail = self.detail or ""
        if len(detail) > 35:
            detail = detail[:35] + "…"
        painter.drawText(
            QRectF(0, BOT_SIZE + 17, BOT_SIZE + 60, 12),
            Qt.AlignmentFlag.AlignCenter,
            detail,
        )

    # ── kéo thả ──
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self._dragged = False

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            if (new_pos - self.pos()).manhattanLength() > 3:
                self._dragged = True
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragged:
                self._save_position()
            else:
                # click thường (không kéo) -> mở dashboard
                webbrowser.open(DASHBOARD_URL)
            self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        self.hide()


class TrayController:
    """Quản lý system tray icon để ẩn/hiện bot và thoát chương trình."""

    def __init__(self, app: QApplication, bot: RouterBot):
        self.app = app
        self.bot = bot

        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(70, 110, 220))
        self.tray = QSystemTrayIcon(QIcon(pixmap), app)
        self.tray.setToolTip("9router Status Bot")

        menu = QMenu()
        self.toggle_action = QAction("Ẩn bot")
        self.toggle_action.triggered.connect(self.toggle_visibility)
        menu.addAction(self.toggle_action)

        quit_action = QAction("Thoát")
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.bot.isVisible():
            self.bot.hide()
            self.toggle_action.setText("Hiện bot")
        else:
            self.bot.show()
            self.toggle_action.setText("Ẩn bot")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # để đóng cửa sổ không tắt luôn tray

    bot = RouterBot()
    bot.show()

    tray = TrayController(app, bot)  # noqa: F841 (giữ tham chiếu để không bị GC)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
