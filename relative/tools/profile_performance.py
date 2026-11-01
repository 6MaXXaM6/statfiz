"""Профиль кадра: расчёт, подготовка графиков и Qt-отрисовка, без ожидания таймера."""
import argparse
import cProfile
import json
import os
import pstats
import sys
import time
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
from PyQt5 import QtCore, QtWidgets  # noqa: E402
from main import MainWindow  # noqa: E402
from ui import style  # noqa: E402


def run(frames=120, particles=150, factor=1., fast=False, history=0):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    style.init_style(app, QtCore.QSize(1366, 768))
    win = MainWindow()
    win.resize(1366, 768)
    win.show()
    win.show_demo()
    page = win.demo
    page.run.pause()
    page.exp.n_total = particles
    page.exp.rebuild()
    page.exp.ensemble = fast
    page.configure_plots()
    if history:
        for series in page.exp.series.values():
            for k in range(history):
                series.add(k * .01, float(k % 100))
        page.exp.gas.time = history * .01
    times = []
    profile = cProfile.Profile()
    profile.enable()
    for _ in range(frames):
        start = time.perf_counter()
        if fast:
            page.exp.advance_for_seconds(.020)
        else:
            page.exp.advance_by(factor)
        calculated = time.perf_counter()
        page.refresh()
        refreshed = time.perf_counter()
        app.processEvents()
        rendered = time.perf_counter()
        times.append([(calculated-start)*1000, (refreshed-calculated)*1000,
                      (rendered-refreshed)*1000, (rendered-start)*1000])
    profile.disable()
    stats = pstats.Stats(profile).strip_dirs().sort_stats('cumtime')
    stats.print_stats(22)
    data = np.asarray(times)
    result = dict(particles=particles, factor=factor, fast=fast, frames=frames,
                  mean_ms=dict(zip(('physics', 'refresh', 'qt', 'total'), data.mean(axis=0).tolist())),
                  p95_ms=float(np.percentile(data[:, 3], 95)), max_ms=float(data[:, 3].max()),
                  steps=page.exp.steps_since_reset)
    print(json.dumps(result, ensure_ascii=False))
    win.close()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, default=120)
    parser.add_argument('--particles', type=int, default=150)
    parser.add_argument('--factor', type=float, default=1.)
    parser.add_argument('--fast', action='store_true')
    parser.add_argument('--history', type=int, default=0)
    args = parser.parse_args()
    run(**vars(args))
