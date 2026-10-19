"""Language-neutral learning figures for array traces and public announcements."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("diagram_canvas", HERE / "draw_batch_042_043.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Canvas = MODULE.Canvas
SCALE = MODULE.SCALE


def panel(c, box, fill="#f6f7fb", outline="#566599"):
    c.draw.rounded_rectangle(tuple(v * SCALE for v in box), radius=15 * SCALE,
                             fill=fill, outline=outline, width=3 * SCALE)


def pair_trace():
    c = Canvas(1180, 850)
    c.text(590, 58, "A = [4, 1, 6]     x = 10", 39)
    c.box(270, 110, 640, 100, "complement = x - A[i]")
    c.line([(590, 210), (590, 260)], arrow=True)
    edges = [70, 160, 310, 565, 920, 1110]
    labels = ["i", "A[i]", "x - A[i]", "seen", "in seen?"]
    for index, label in enumerate(labels):
        panel(c, (edges[index], 280, edges[index + 1], 355), "#e9edf7")
        c.text((edges[index] + edges[index + 1]) / 2, 318, label, 30)
    rows = [("0", "4", "6", "{}", "False"),
            ("1", "1", "9", "{4}", "False"),
            ("2", "6", "4", "{1, 4}", "True")]
    for row, values in enumerate(rows):
        top = 355 + row * 102
        for index, value in enumerate(values):
            panel(c, (edges[index], top, edges[index + 1], top + 102),
                  "#e6f2ec" if row == 2 else "white")
            c.text((edges[index] + edges[index + 1]) / 2, top + 51, value, 35,
                   "#2b7d70" if row == 2 else "#28354c")
    c.line([(590, 661), (590, 705)], arrow=True, color="#2b7d70")
    panel(c, (250, 710, 930, 800), "#e6f2ec", "#2b7d70")
    c.text(590, 755, "A[0] + A[2] = 4 + 6 = 10", 36, "#2b7d70")
    c.save("prep-040-complement-trace.png")


def presence_flags():
    c = Canvas(1180, 970)
    c.text(590, 55, "n = 7     remaining = [6, 1, 4, 7, 3]", 36)
    c.box(260, 110, 660, 105, "seen = [False] * (n + 1)")
    c.line([(590, 215), (590, 265)], arrow=True)
    c.box(260, 270, 660, 105, "seen[value] = True")
    c.line([(590, 375), (590, 435)], arrow=True)
    x0, width, y = 90, 125, 470
    values = [False, True, False, True, True, False, True, True]
    for index, value in enumerate(values):
        left = x0 + index * width
        color = "#eef0f4" if index == 0 else "#e6f2ec" if value else "#fff0d9"
        c.text(left + width / 2, y - 34, str(index), 33)
        panel(c, (left, y, left + width, y + 105), color)
        c.text(left + width / 2, y + 52, "T" if value else "F", 40)
        if index == 0:
            c.line([(left + 12, y + 90), (left + width - 12, y + 15)], color="#9ba2af", width=4)
    c.text(590, 630, "T = True     F = False", 32)
    c.text(590, 688, "range(1, n + 1)", 32)
    c.line([(590, 723), (590, 770)], arrow=True, color="#b0752c")
    panel(c, (315, 785, 865, 890), "#fff0d9", "#b0752c")
    c.text(590, 837, "missing = [2, 5]", 42, "#8a571d")
    c.save("prep-041-presence-flags.png")


def birthday():
    c = Canvas(1360, 1020)
    c.text(680, 55, "DD / MM", 39)
    boxes = [(70, 130, 590, 480), (770, 130, 1290, 480),
             (770, 620, 1290, 950), (70, 620, 590, 950)]
    rows = [("C0", ("15/05,16/05,19/05", "17/06,18/06", "14/07,16/07", "14/08,15/08,17/08")),
            ("C1", ("14/07,16/07", "14/08,15/08,17/08")),
            ("C2", ("16/07", "15/08,17/08")),
            ("C3", ("16 / 07",))]
    for index, (box, (label, dates)) in enumerate(zip(boxes, rows)):
        panel(c, box, "#e6f2ec" if index == 3 else "#f6f7fb",
              "#2b7d70" if index == 3 else "#566599")
        left, top, right, _bottom = box
        c.text((left + right) / 2, top + 43, label, 36)
        for row, value in enumerate(dates):
            position = top + 110 + row * 57 if len(dates) > 2 else top + 152 + row * 70
            c.text((left + right) / 2, position, value, 42 if index == 3 else 35)
    c.line([(590, 305), (770, 305)], arrow=True)
    c.label(680, 265, "1")
    c.line([(1030, 480), (1030, 620)], arrow=True)
    c.label(1080, 550, "2")
    c.line([(770, 785), (590, 785)], arrow=True, color="#2b7d70")
    c.label(680, 745, "3", "#2b7d70")
    c.save("prep-046-public-announcement-stages.png")


if __name__ == "__main__":
    pair_trace()
    presence_flags()
    birthday()
