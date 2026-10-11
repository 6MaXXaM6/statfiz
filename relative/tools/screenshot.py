"""Снимок окна без показа на экране: python tools/screenshot.py WxH страница кадров файл.png [настройки]"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
w, h = map(int, sys.argv[1].split("x"))
os.environ["RELATIVE_SCREEN"] = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PyQt5 import QtWidgets  # noqa: E402

import main  # noqa: E402
from ui import style  # noqa: E402

page, frames, out = sys.argv[2], int(sys.argv[3]), sys.argv[4]
extra = sys.argv[5:]
app = QtWidgets.QApplication(sys.argv[:1])
style.init_style(app)
win = main.MainWindow()
win.resize(w, h)
win.show()
getattr(win, "show_" + page)()
d = win.demo
QUANT = {"vrel": ("pair", "modulus"), "vrelx": ("pair", "projection"),
         "v1": ("single", "modulus"), "v1x": ("single", "projection"),
         "v2": ("second", "modulus"), "v2x": ("second", "projection"),
         "e1": ("single", "energy"), "e2": ("second", "energy")}
for opt in extra:
    key, _, val = opt.partition("=")
    if key == "fast":
        d.run.mode.set_value("fast")
        d.on_mode_changed(True)
    elif key == "add":            # add=v1 — второй график
        d.add_panel(*QUANT[val])
    elif key == "first":          # first=vrelx — что в первом графике
        d.panels[0].show_quantity(*QUANT[val])
    elif key == "rotate":
        d.panels[0].rotate()
    elif key == "mix":
        d.gas.gas_mode.set_value("mix")
        d.on_gas_changed()
    elif key == "pair":
        d.gas.pair.set_value(val)
        d._changed(d.exp.choose_pair, val)
if page == "demo":
    d.run.start()
    d.run.timer.stop()
    import time
    t = time.perf_counter()
    for _ in range(frames):
        d.run._on_timer()
        d.run.timer.stop()  # кадры считаем вручную
        app.processEvents()
    print("ms/frame: %.1f" % ((time.perf_counter() - t) / max(frames, 1) * 1000))
app.processEvents()
win.grab().save(out)
print("saved", out)
