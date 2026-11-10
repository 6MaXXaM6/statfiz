"""Регрессия сосуда после полноэкранного перехода и точность нижнего отношения."""
import os
import pickle
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtTest import QTest, QSignalSpy

from main import MainWindow
from model.experiment import Experiment
from pages.demo.readouts import ratio_text
from tools.layout_check import problems
from ui import style


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def win(app):
    style.init_style(app, QtCore.QSize(944, 630))
    w = MainWindow()
    w.resize(944, 630)
    w.show()
    w.show_demo()
    w.demo.pause()
    QTest.qWait(180)
    yield w
    w.close()
    app.processEvents()


def assert_box_fills_available_space(w):
    d = w.demo
    free = d.body.height() - d.run_card.sizeHint().height() - d.left.layout().spacing()
    expected = min(d.left.width(), free)
    assert abs(d.box_card.maximumHeight() - expected) <= 1
    assert abs(d.box_card.height() - expected) <= 2
    vessel = d.box.frame.mapRectToScene(d.box.frame.rect())
    assert vessel.width() > .8 * min(d.box.width(), d.box.height())
    assert not problems(w)


@pytest.mark.parametrize('small', [(944, 630), (1024, 768), (1093, 614)])
def test_large_small_round_trips_restore_vessel_size(win, small):
    d = win.demo
    before = pickle.dumps(d.exp)
    for size in (small, (1920, 1080), small, (2560, 1440), small, (1920, 1080), small):
        win.resize(*size)
        win.font_scale.apply()
        QTest.qWait(180)
        assert win.size() == QtCore.QSize(*size)
        assert_box_fills_available_space(win)
    assert pickle.dumps(d.exp) == before
    # Обновление не должно вызывать бесконечную цепочку LayoutRequest.
    assert not d._box_fit_timer.isActive()
    spy = QSignalSpy(d._box_fit_timer.timeout)
    QTest.qWait(100)
    assert len(spy) == 0


def test_child_layout_resize_after_parent_resize_is_handled(win):
    d = win.demo
    # Во время смены масштаба дочерняя область временно мала. После
    # завершения layout размер страницы уже тот же, нового resizeEvent нет.
    d.body.resize(d.body.width(), 200)
    d.rescale_layout()
    d.layout().invalidate()
    d.layout().activate()
    QTest.qWait(180)
    assert_box_fills_available_space(win)


def test_zoom_page_navigation_and_fullscreen_restore_vessel(win, app):
    d = win.demo
    before = pickle.dumps(d.exp)
    for large, small in [((1920, 1080), (944, 630)), ((1366, 768), (1093, 614))]:
        d.zoom_button.click()
        win.resize(*large)
        win.font_scale.apply()
        QTest.qWait(100)
        win.resize(*small)
        win.font_scale.apply()
        QTest.qWait(100)
        d.zoom_button.click()
        QTest.qWait(180)
        assert_box_fills_available_space(win)
        win.show_title()
        win.resize(*large)
        win.font_scale.apply()
        QTest.qWait(100)
        win.show_demo()
        QTest.qWait(180)
        assert_box_fills_available_space(win)
    # При ×2 у offscreen виртуальный fullscreen 400×300: проверяем размеры выше.
    if app.primaryScreen().geometry().width() >= 800:
        QTest.keyClick(win, QtCore.Qt.Key_F11)
        QTest.qWait(180)
        assert win.isFullScreen()
        # Отложенные resize/layout/font события могут занять больше 180 мс.
        # Ждём готовую геометрию, не вызывая подгонку вручную из теста.
        for _ in range(50):
            free = d.body.height() - d.run_card.sizeHint().height() - d.left.layout().spacing()
            expected = min(d.left.width(), free)
            if (not d._box_fit_timer.isActive()
                    and abs(d.box_card.maximumHeight() - expected) <= 1
                    and abs(d.box_card.height() - expected) <= 2):
                break
            QTest.qWait(20)
        assert_box_fills_available_space(win)
        QTest.keyClick(win, QtCore.Qt.Key_Escape)
        QTest.qWait(180)
        assert not win.isFullScreen()
        assert_box_fills_available_space(win)
    assert pickle.dumps(d.exp) == before


@pytest.mark.parametrize('mean,expected', [(565.6, '1.41'), (560., '1.40'), (600., '1.50')])
def test_ratio_has_exactly_two_decimal_places(mean, expected):
    exp = Experiment(seed=16)
    exp.advance(100)
    for obj, value in [('single', 400.), ('pair', mean)]:
        hist = exp.hist[obj, 'modulus']
        hist.reset()
        hist.add([value, value])
    text = ratio_text(exp, 'single', 'modulus')
    assert '<b>%s</b>' % expected in text
    assert '√2 ≈ 1.41' in text


def test_mixture_ratio_theory_has_two_decimal_places():
    exp = Experiment(seed=16)
    exp.configure_gas('mix', 28, 4, 30, 10)
    exp.choose_pair('AB')
    exp.advance(100)
    text = ratio_text(exp, 'single', 'modulus')
    assert '√(m/μ) ≈ 2.83' in text
