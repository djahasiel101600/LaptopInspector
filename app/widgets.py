"""
Reusable UI widgets for Laptop Inspector.
"""

from PyQt6.QtWidgets import (
    QLabel, QPushButton, QFrame, QHBoxLayout, QVBoxLayout,
    QWidget, QLineEdit, QTextEdit, QComboBox, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor

from app.theme import (
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BG_CARD, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_LIGHT,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_INPUT_BG,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    STATUS_COLORS, STATUS_BG_COLORS,
)


def drop_shadow(widget: QWidget, blur: int = 16, offset_y: int = 2) -> None:
    """Apply a subtle drop shadow to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(0, 0, 0, 30))
    widget.setGraphicsEffect(shadow)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        label = f"{icon_text}  {text}" if icon_text else text
        self.setText(label)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(36)
        self.setMinimumWidth(100)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-weight: 600;
                font-family: "{FONT_FAMILY}";
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
            QPushButton:disabled {{
                background-color: #93c5fd;
                color: #e0e7ff;
            }}
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        label = f"{icon_text}  {text}" if icon_text else text
        self.setText(label)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(36)
        self.setMinimumWidth(100)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_ACCENT};
                border: 1.5px solid {COLOR_ACCENT};
                border-radius: 6px;
                padding: 0 18px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-weight: 600;
                font-family: "{FONT_FAMILY}";
            }}
            QPushButton:hover {{
                background-color: #eff6ff;
            }}
            QPushButton:pressed {{
                background-color: #dbeafe;
            }}
        """)


class DangerButton(QPushButton):
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        label = f"{icon_text}  {text}" if icon_text else text
        self.setText(label)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(36)
        self.setMinimumWidth(80)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_DANGER};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-weight: 600;
                font-family: "{FONT_FAMILY}";
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
            QPushButton:pressed {{
                background-color: #991b1b;
            }}
        """)


class StatusBadge(QLabel):
    """Colored badge for PASS / FAIL / WARNING status."""

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        text = status or "N/A"
        fg = STATUS_COLORS.get(text, COLOR_TEXT_SECONDARY)
        bg = STATUS_BG_COLORS.get(text, "#f1f5f9")
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.setMinimumWidth(70)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1.5px solid {fg};
                border-radius: 12px;
                padding: 0 10px;
                font-size: {FONT_SIZE_SMALL}pt;
                font-weight: 700;
                font-family: "{FONT_FAMILY}";
            }}
        """)


class Card(QFrame):
    """A white rounded card widget with optional shadow."""

    def __init__(self, parent=None, shadow: bool = True):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {COLOR_BG_CARD};
                border-radius: 10px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        if shadow:
            drop_shadow(self)


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        font = QFont(FONT_FAMILY, FONT_SIZE_MEDIUM)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)
        self.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")


class FieldLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        font = QFont(FONT_FAMILY, FONT_SIZE_SMALL)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        self.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")


class StyledLineEdit(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
                color: {COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLOR_ACCENT};
                background-color: white;
            }}
            QLineEdit:disabled {{
                background-color: #f1f5f9;
                color: {COLOR_TEXT_SECONDARY};
            }}
        """)


class StyledTextEdit(QTextEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
                color: {COLOR_TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border: 1.5px solid {COLOR_ACCENT};
                background-color: white;
            }}
        """)


class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_INPUT_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
                color: {COLOR_TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border: 1.5px solid {COLOR_ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid {COLOR_BORDER};
                selection-background-color: #eff6ff;
                selection-color: {COLOR_ACCENT};
                outline: none;
            }}
        """)


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none;")


class StatCard(QFrame):
    """Small stat card for dashboard summaries."""

    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedHeight(90)
        self.setMinimumWidth(130)
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: white;
                border-radius: 10px;
                border-left: 4px solid {color};
                border-top: 1px solid {COLOR_BORDER};
                border-right: 1px solid {COLOR_BORDER};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)
        drop_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(2)

        self.value_label = QLabel(value)
        font = QFont(FONT_FAMILY, 22)
        font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet(f"color: {color}; border: none;")

        self.title_label = QLabel(title)
        font2 = QFont(FONT_FAMILY, FONT_SIZE_SMALL)
        self.title_label.setFont(font2)
        self.title_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; border: none;")

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def update_value(self, value: str) -> None:
        self.value_label.setText(value)


class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_char: str = "", parent=None):
        super().__init__(parent)
        label = f"  {icon_char}   {text}" if icon_char else f"   {text}"
        self.setText(label)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                background-color: transparent;
                color: #94a3b8;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #1e2d3d;
                color: white;
            }}
            QPushButton:checked {{
                background-color: {COLOR_ACCENT};
                color: white;
                font-weight: 700;
            }}
        """)
