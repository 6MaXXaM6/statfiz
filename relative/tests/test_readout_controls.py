"""Отображение чисел/проекции не вмешивается в опыт; пауза, размеры и поворот."""
import copy
import os
import pickle
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtTest import QTest

import settings
from main import MainWindow
from model.experiment import Experiment
from pages.demo.graph_panel import QUANTITIES, stats_text
from pages.demo.readouts import significant, stats_ready
from ui import style
from tools.layout_check import problems, plot_areas


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def win(app):
    style.init_style(app, QtCore.QSize(1024, 768))
    window = MainWindow()
    window.resize(1024, 768)
    window.show()
    window.show_demo()
    window.demo.pause()
    app.processEvents()
    yield window
    window.close()
    app.processEvents()


@pytest.mark.parametrize('value,expected', [
    (529, '530'), (76.5, '76'), (1.414, '1.4'), (1.001, '1.0'),
    (.0999, '0.10'), (9.99, '10'), (-1.234, '−1.2'),
    (12345, '1.2·10⁴'), (.00012345, '1.2·10⁻⁴'),
    (0, '0'), (float('nan'), '—'), (float('inf'), '—'),
])
def test_two_significant_digits(value, expected):
    assert significant(value) == expected


def test_first_numbers_wait_for_samples_and_resets(win):
    d = win.demo
    d.exp = Experiment(seed=67)
    d.on_experiment_changed()
    assert not stats_ready(d.exp)
    assert all('Набор статистики' in p.stats.text() for p in d.panels)
    assert '<b>—</b>' in d.ratio.text()
    d.exp.advance(settings.STATS_MIN_STEPS - 1)
    d.refresh()
    assert all('Набор статистики' in p.stats.text() for p in d.panels)
    d.exp.advance(1)
    d.refresh()
    assert all('Набор статистики' not in p.stats.text() for p in d.panels)
    for p in d.panels:
        assert p.stats.text() == stats_text(d.exp, *p.quantity)
    # Темп обнуляет только историю; накопленная статистика остаётся видимой.
    d.run.mode.buttons['fast'].click()
    assert stats_ready(d.exp)
    assert all('Набор статистики' not in p.stats.text() for p in d.panels)
    # Новый выбранный объект / новый опыт действительно начинают набор заново.
    d._changed(d.exp.select, 10, 1)
    assert all('Набор статистики' in p.stats.text() for p in d.panels)
    d.exp.advance(settings.STATS_MIN_STEPS)
    d.on_start()
    assert not stats_ready(d.exp)


def test_statistics_throttle_pause_and_parameter_changes(win, monkeypatch):
    from pages.demo import page as page_module
    d = win.demo
    d.exp.advance(settings.STATS_MIN_STEPS)
    now = [100.]
    monkeypatch.setattr(page_module.time, 'perf_counter', lambda: now[0])
    calls = []
    for panel in d.panels:
        original = panel.refresh_stats
        monkeypatch.setattr(panel, 'refresh_stats', lambda exp, p=panel, f=original: (calls.append(p), f(exp)))
    d.refresh()
    old_stats = [p.stats.text() for p in d.panels]
    old_ratio = d.ratio.text()
    d.run.toggle_pause()
    d.run.timer.stop()
    d.exp.advance(20)
    now[0] += .49
    d.refresh(force_stats=False)
    assert len(calls) == 2
    assert [p.stats.text() for p in d.panels] == old_stats
    assert d.ratio.text() == old_ratio
    for panel in d.panels:
        assert panel.hist_plot.current.value() == pytest.approx(d.exp.current_value(*panel.quantity))
    now[0] += .02
    d.refresh(force_stats=False)
    assert len(calls) == 4
    d.exp.advance(10)
    d.run.pause()
    assert len(calls) == 6
    for panel in d.panels:
        assert panel.stats.text() == stats_text(d.exp, *panel.quantity)
    total = d.exp.hist[d.panels[0].quantity].total
    # Реальный обработчик поля температуры; не ждём очередные полсекунды.
    d.gas.temperature.spin.setValue(1200)
    QTest.qWait(80)
    assert d.exp.temperature == 1200
    assert len(calls) == 8
    assert d.exp.hist[d.panels[0].quantity].total == total
    assert d.panels[0].stats.text() == stats_text(d.exp, *d.panels[0].quantity)
    d.panels[1].show_quantity('single', 'energy')
    assert d.panels[1].stats.text() == stats_text(d.exp, 'single', 'energy')
    assert '10⁻²¹ Дж' in d.panels[1].stats.toolTip()


@pytest.mark.parametrize('mode,ensemble', [('pure', False), ('pure', True), ('mix', False), ('mix', True)])
def test_display_switches_preserve_all_experiment_data_and_rng(win, app, mode, ensemble):
    d = win.demo
    d.exp = Experiment(seed=103)
    d.exp.configure_gas(mode, 28, 4, 30, 10)
    d.exp.ensemble = ensemble
    d.on_experiment_changed()
    d.panels[0].show_quantity('pair', 'projection')
    d.panels[1].show_quantity('single', 'projection')
    reference = copy.deepcopy(d.exp)
    assert pickle.dumps(d.exp) == pickle.dumps(reference)
    # Полное состояние: позиции/скорости/время, все гистограммы и истории, RNG.
    # Чередуем переключения и одинаковые физические шаги; проверяем и дальнейшую траекторию.
    for index in range(8):
        before = pickle.dumps(d.exp)
        d._frame_remaining = .123  # имитация незавершённого кадра: флажок не должен отменять его
        d.instant_action.setChecked(index % 2 == 0)
        d.projection_action.setChecked(index % 3 != 0)
        d.vector_toggle.setChecked(index % 4 != 0)
        assert d._frame_remaining == .123
        d._frame_remaining = None
        assert pickle.dumps(d.exp) == before
        assert all(p.value.isVisible() == d.instant_action.isChecked() for p in d.panels)
        for p in d.panels:
            assert p.value.text().startswith('= <b>')
        d.exp.advance(17)
        reference.advance(17)
        d.refresh()
        assert pickle.dumps(d.exp) == pickle.dumps(reference)
    # Добавленная заново панель наследует текущую настройку чисел.
    d.instant_action.setChecked(True)
    d.remove_panel(d.panels[1])
    d.add_next_panel()
    app.processEvents()
    assert d.panels[1].value.isVisible()
    assert pickle.dumps(d.exp) == pickle.dumps(reference)


def test_projection_optional_and_available_for_either_panel(win):
    d = win.demo
    assert not d.instant_action.isChecked()
    assert not d.projection_action.isChecked()
    assert not d.projection_action.isEnabled()
    for panel, obj in zip(d.panels, ['pair', 'single']):
        panel.show_quantity(obj, 'projection')
        assert d.projection_action.isEnabled()
        assert d.vectors.proj.path().isEmpty()
        d.projection_action.setChecked(True)
        assert d.projection_of == obj
        assert not d.vectors.proj.path().isEmpty()
        assert d.vectors._projection
        assert 'x' in d.legend.text()
        d.projection_action.setChecked(False)
        assert d.vectors.proj.path().isEmpty()
        assert panel.quantity == (obj, 'projection')
        panel.show_quantity(obj, 'modulus')
    # Два графика проекции: приоритет первого, при его смене — второго.
    d.panels[0].show_quantity('pair', 'projection')
    d.panels[1].show_quantity('single', 'projection')
    d.projection_action.setChecked(True)
    assert d.projection_of == 'pair'
    d.panels[0].show_quantity('pair', 'modulus')
    assert d.projection_of == 'single'
    d.vector_toggle.setChecked(False)
    assert not d.projection_action.isEnabled()
    assert d.projection_of is None
    d.vector_toggle.setChecked(True)
    assert d.projection_of == 'single'


@pytest.mark.parametrize('size', [(1024, 768), (1093, 614), (1366, 768), (1920, 1080)])
def test_layout_both_panels_rotation_zoom_and_numbers(win, app, size):
    d = win.demo
    win.resize(*size)
    win.font_scale.apply()
    d.exp.advance(120)
    d.refresh()
    QTest.qWait(80)
    for instant in (False, True):
        d.instant_action.setChecked(instant)
        for zoom in (False, True):
            d.zoom_button.setChecked(zoom)
            d.toggle_graphs_zoom()
            # Все величины в обеих панелях, поочерёдный поворот каждой.
            for index, quantity in enumerate(QUANTITIES):
                d.panels[0].show_quantity(*quantity)
                d.panels[1].show_quantity(*QUANTITIES[-index-1])
                panel = d.panels[index % 2]
                panel.rotate()
                app.processEvents()
                assert not problems(win)
                assert d.display_button.isVisible()
                for p in d.panels:
                    assert p.header.isAncestorOf(p.stats)
                    assert p.stats.width() >= p.stats.sizeHint().width()
                    assert p.stats.height() >= p.stats.sizeHint().height()
                    assert p.hist_plot.height() > 80
                    if p.time_plot.isVisible():
                        assert p.time_plot.height() > 80
                    if instant:
                        assert p.value.width() >= p.value.sizeHint().width()
                panel.rotate()
                app.processEvents()
    # Значения меняются, геометрия графиков — нет.
    d.instant_action.setChecked(False)
    app.processEvents()
    before = plot_areas(d)
    for _ in range(5):
        d.exp.advance(5)
        d.refresh()
        app.processEvents()
        assert plot_areas(d) == before


def test_real_fullscreen_flag_and_return_keep_data(win, app):
    # Offscreen даёт виртуальный экран 800×600 физических пикселей. При ×2
    # это лишь 400×300 логических: меньше поддерживаемого окна всего приложения.
    # Retina-компоновку отдельно проверяет матрица логических размеров выше.
    screen = app.primaryScreen().geometry()
    if app.platformName() == 'offscreen' and (screen.width() < 800 or screen.height() < 600):
        pytest.skip('Виртуальный fullscreen меньше 800×600; размеры Retina проверены отдельно')
    d = win.demo
    d.exp.advance(120)
    d.refresh()
    state = pickle.dumps(d.exp)
    for zoom in (False, True):
        d.zoom_button.setChecked(zoom)
        d.toggle_graphs_zoom()
        QTest.keyClick(win, QtCore.Qt.Key_F11)
        QTest.qWait(150)
        assert win.isFullScreen()
        assert not problems(win)
        for p in d.panels:
            assert p.stats.width() >= p.stats.sizeHint().width()
            p.rotate()
        QTest.keyClick(win, QtCore.Qt.Key_Escape)
        QTest.qWait(150)
        assert not win.isFullScreen()
        assert not problems(win)
        assert pickle.dumps(d.exp) == state


@pytest.mark.parametrize('mode,n,mass_a,mass_b,temperature,start,memory', [
    ('pure', 2, 1, 1, 1500, 'maxwell', 1),
    ('pure', 300, 200, 200, 50, 'maxwell', 5000),
    ('mix', 30, 200, 1, 1500, 'maxwell', 3),
    ('mix', 30, 1, 200, 50, 'beam', 1),
])
def test_readouts_at_parameter_extremes(win, app, mode, n, mass_a, mass_b, temperature, start, memory):
    d = win.demo
    d.exp = Experiment(seed=110)
    d.exp.configure_gas(mode, mass_a, mass_b, n, 1, start=start)
    d.exp.set_temperature(temperature)
    d.exp.set_memory(memory)
    d.exp.advance(settings.STATS_MIN_STEPS)
    d.on_experiment_changed()
    d.instant_action.setChecked(True)
    for quantity in QUANTITIES:
        for panel in d.panels:
            panel.show_quantity(*quantity)
            panel.rotate()
            app.processEvents()
            assert panel.stats.text() == stats_text(d.exp, *quantity)
            assert 'Набор статистики' not in panel.stats.text()
            assert panel.stats.width() >= panel.stats.sizeHint().width()
            assert panel.value.width() >= panel.value.sizeHint().width()
            assert not problems(win)
            panel.rotate()
