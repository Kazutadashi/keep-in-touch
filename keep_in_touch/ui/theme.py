"""Small shared UI styling helpers."""

SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background: palette(base);
    width: 14px;
    margin: 2px;
    border: none;
}
QScrollBar::handle:vertical {
    background: palette(highlight);
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: palette(base);
    height: 14px;
    margin: 2px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: palette(highlight);
    min-width: 28px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}
"""
