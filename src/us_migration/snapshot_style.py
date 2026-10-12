"""Shared light presentation for data snapshot exports."""
PAPER = '#ffffff'
INK = '#293d36'
HEADER = '#eee7d7'
STRIPE = '#f8f3e8'
LINE = '#ded4bf'


def style_cell(cell, row):
    cell.set_edgecolor(LINE)
    cell.set_facecolor(HEADER if row == 0 else (STRIPE if row % 2 else PAPER))
    cell.set_text_props(color=INK, weight='bold' if row == 0 else 'normal')
