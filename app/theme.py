"""
UI theme and style constants for Laptop Inspector.
"""

# Color Palette
COLOR_BG_DARK = "#0f1923"         # sidebar / dark background
COLOR_BG_MAIN = "#f0f4f8"         # main content background
COLOR_BG_CARD = "#ffffff"          # card backgrounds
COLOR_BG_HEADER = "#1a3a5c"        # header bar
COLOR_ACCENT = "#2563eb"           # primary accent (blue)
COLOR_ACCENT_HOVER = "#1d4ed8"
COLOR_SUCCESS = "#16a34a"
COLOR_DANGER = "#dc2626"
COLOR_WARNING = "#d97706"
COLOR_TEXT_PRIMARY = "#0f172a"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_BORDER = "#e2e8f0"
COLOR_SIDEBAR_ITEM_HOVER = "#1e2d3d"
COLOR_SIDEBAR_ITEM_ACTIVE = "#2563eb"
COLOR_INPUT_BG = "#f8fafc"
COLOR_ROW_ALT = "#f8fafc"

# Fonts
FONT_FAMILY = "Segoe UI"
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_MEDIUM = 12
FONT_SIZE_LARGE = 14
FONT_SIZE_XLARGE = 18
FONT_SIZE_TITLE = 24

# Dimensions
SIDEBAR_WIDTH = 220
HEADER_HEIGHT = 56
CARD_RADIUS = 8

STATUS_COLORS = {
    "PASS": COLOR_SUCCESS,
    "FAIL": COLOR_DANGER,
    "WARNING": COLOR_WARNING,
    "SKIP": COLOR_TEXT_SECONDARY,
}

STATUS_BG_COLORS = {
    "PASS": "#dcfce7",
    "FAIL": "#fee2e2",
    "WARNING": "#fef3c7",
}

QSS_GLOBAL = f"""
QWidget {{
    font-family: "{FONT_FAMILY}", "Arial", sans-serif;
    font-size: {FONT_SIZE_NORMAL}pt;
    color: {COLOR_TEXT_PRIMARY};
}}
QScrollBar:vertical {{
    background: {COLOR_BG_MAIN};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {COLOR_BG_MAIN};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QToolTip {{
    background-color: {COLOR_BG_HEADER};
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: {FONT_SIZE_SMALL}pt;
}}
"""
