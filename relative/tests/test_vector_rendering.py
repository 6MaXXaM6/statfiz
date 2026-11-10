"""Стрелки в одной сцене: края, перерисовка, масштаб температуры и resize."""
import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from PyQt5 import QtCore, QtTest, QtWidgets
from main import MainWindow
from ui import style


@pytest.fixture(scope='module')
def app():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    style.init_style(app)
    return app


@pytest.fixture
def window(app):
    win = MainWindow()
    win.resize(1093, 700)
    win.show()
    win.show_demo()
    win.demo.pause()
    win.demo.exp.configure_gas('pure', 28, 28, 2, 1, collisions=False)
    win.demo.exp.gas.pos[:] = [[25., 25.], [75., 75.]]
    win.demo.on_experiment_changed()
    app.processEvents()
    yield win
    win.close()


def scene_path(arrow):
    return arrow.mapToScene(arrow.path()).boundingRect()


@pytest.mark.parametrize('size', [(1024, 640), (1093, 700), (1366, 768), (1920, 1080)])
@pytest.mark.parametrize('velocities', [
    [[500, 0], [-500, 0]], [[0, 500], [0, -500]],
    [[-900, -900], [900, 900]], [[900, -900], [-900, 900]],
    [[0, 0], [0, 0]], [[300, 400], [300, 400]],
])
def test_complete_construction_fits_and_preserves_vector_difference(window, app, size, velocities):
    d = window.demo
    window.resize(*size)
    window.font_scale.apply()
    app.processEvents()
    d.exp.gas.vel[:] = velocities
    for projection in (None, 'pair', 'single', 'second'):
        d.projection_of = projection
        d.refresh()
        app.processEvents()
        v = d.vectors
        assert v.scene() is d.box.scene()
        assert v.fits
        for arrow in v.arrows:
            if arrow.isVisible() and not arrow.path().isEmpty():
                assert v._area.contains(scene_path(arrow))
        v1, v2 = np.array(velocities)
        if np.any(v1 != v2):
            start = v.rel.path().elementAt(0)
            np.testing.assert_allclose([start.x, start.y], v2)
            tip = v.mapToScene(QtCore.QPointF(*v1.astype(float)))
            assert scene_path(v.rel).adjusted(-.001, -.001, .001, .001).contains(tip)
        assert d.box.vector_caption.geometry().bottom() <= d.box.height()


def test_extreme_vectors_hide_whole_and_reappear_without_changing_scale(window, app):
    d = window.demo
    scale = d.box.vector_pixel_scale()
    d.exp.gas.vel[:] = [[1e7, -1e7], [-1e7, 1e7]]
    d.refresh()
    assert not d.vectors.fits
    assert not any(a.isVisible() for a in d.vectors.arrows)
    assert not any(a.isVisible() for a in d.box.arrows)
    d.vector_toggle.setChecked(False)
    d.exp.gas.vel[:] = [[300, 400], [-100, 200]]
    d.refresh()
    assert d.vectors.fits and not d.vectors.isVisible()
    d.vector_toggle.setChecked(True)
    assert d.vectors.v1.isVisible() and d.box.arrows[0].isVisible()
    assert d.box.vector_pixel_scale() == pytest.approx(scale)


def test_arrows_can_cross_vessel_wall_without_hidden_inset_clipping(window, app):
    d = window.demo
    # В широком поле за квадратным сосудом достаточно места для целой стрелки.
    window.resize(1920, 800)
    window.font_scale.apply()
    QtTest.QTest.qWait(180)
    app.processEvents()
    d.exp.gas.pos[:] = [[1., 50.], [99., 50.]]
    d.exp.gas.vel[:] = [[-100., 0.], [100., 0.]]
    d.refresh()
    frame = d.box.frame.mapRectToScene(d.box.frame.rect())
    for arrow in d.box.arrows:
        assert arrow.isVisible()
        assert not frame.contains(scene_path(arrow))
    # Поворот к границе самого viewport не оставляет обрезанный наконечник.
    d.exp.gas.vel[:] = [[-1e5, 0.], [1e5, 0.]]
    d.refresh()
    assert not any(a.isVisible() for a in d.box.arrows)


def test_temperature_still_doubles_drawn_lengths(window, app):
    d = window.demo
    d.exp.gas.vel[:] = [[120., 160.], [-40., 80.]]
    lengths = []
    for temperature in (300, 1200):
        d._changed(d.exp.set_temperature, temperature)
        v = d.vectors
        assert v.fits
        origin = v.mapToScene(QtCore.QPointF())
        tip = v.mapToScene(QtCore.QPointF(*d.exp.gas.vel[d.exp.i]))
        lengths.append(np.hypot(tip.x() - origin.x(), tip.y() - origin.y()))
    assert lengths[1] == pytest.approx(2 * lengths[0])


class PaintRegions(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.rectangles = []

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Paint:
            self.rectangles.append((event.region().boundingRect(), obj.rect()))
        return False


def test_every_changed_frame_repaints_whole_canvas_and_keeps_no_old_paths(window, app):
    d = window.demo
    observer = PaintRegions()
    viewport = d.box.viewport()
    viewport.installEventFilter(observer)
    d.exp.gas.vel[:] = [[500., 400.], [-600., 300.]]
    d.refresh()
    QtTest.QTest.qWait(30)
    QtTest.QTest.qWait(120)  # Завершить отложенное масштабирование шрифта окна.
    d.refresh()
    QtTest.QTest.qWait(30)
    d.box.grab()  # Создать растровый кеш молекул для текущего devicePixelRatio.
    d.refresh()
    QtTest.QTest.qWait(30)
    initial = d.box.grab().toImage()
    count = len(d.box.scene().items())
    observer.rectangles.clear()
    for angle in np.linspace(0, 2 * np.pi, 24):
        observer.rectangles.clear()
        d.exp.gas.vel[:] = [[1000 * np.cos(angle), 1000 * np.sin(angle)], [-200, -500]]
        d.refresh(plots=False)
        QtTest.QTest.qWait(15)
        assert len(d.box.scene().items()) == count
        # Дополнительные события от QLabel допустимы; каждый новый кадр
        # обязан вызвать перерисовку всего viewport, включая левое поле.
        assert any(region == full for region, full in observer.rectangles)
    d.exp.gas.vel[:] = [[500., 400.], [-600., 300.]]
    d.refresh()
    QtTest.QTest.qWait(30)
    final = d.box.grab().toImage()
    assert final == initial
    viewport.removeEventFilter(observer)
