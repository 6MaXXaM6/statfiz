"""Сосуд с молекулами."""

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from model.experiment import PAIR
from ui import style
from ui.plots.base import Arrow, StaticPlot

ARROW_LENGTH = 12.0  # длина стрелки (нм) для скорости, равной масштабной
ARROW_HEAD = 3.0     # наконечник стрелки, нм


class BoxView(StaticPlot):
    """Молекулы газов A и B; выбранные молекулы выделены цветом и стрелками скоростей.

    Щелчок левой кнопкой мыши — сигнал clicked(x, y, 1), правой — clicked(x, y, 2).
    """

    HINT = "Щелчок по молекуле: левая кнопка — молекула 1, правая — молекула 2"

    clicked = QtCore.pyqtSignal(float, float, int)

    def __init__(self):
        super().__init__(canvas=True)
        self.frame = QtWidgets.QGraphicsRectItem()
        frame_pen = QtGui.QPen(QtGui.QColor("black"))
        frame_pen.setWidth(3)
        frame_pen.setCosmetic(True)
        self.frame.setPen(frame_pen)

        # Размер кружков задаётся в пикселях (pxMode) — так pyqtgraph рисует их из готовых
        # картинок, это в разы быстрее. Пиксели пересчитываются из масштаба в update_view.
        self.gas_a = pg.ScatterPlotItem(pen=None, brush=style.GAS_A)
        self.gas_b = pg.ScatterPlotItem(pen=None, brush=style.GAS_B)
        self.chosen = pg.ScatterPlotItem()
        self.arrows = [Arrow(style.MOL1), Arrow(style.MOL2)]
        self.add_all(self.frame, self.gas_a, self.gas_b, self.chosen, *self.arrows)
        self.speed_scale = 1.0
        self.scene().sigMouseClicked.connect(self._on_click)
        self.setToolTip(self.HINT)

    def configure(self, box_size, speed_scale):
        """speed_scale — характерная скорость (м/с), которой соответствует стрелка ARROW_LENGTH нм."""
        self.frame.setRect(0, 0, box_size, box_size)
        self.setRange(xRange=(0, box_size), yRange=(0, box_size), padding=0.01)
        self.speed_scale = speed_scale

    def _on_click(self, event):
        p = self.getViewBox().mapSceneToView(event.scenePos())
        which = 2 if event.button() == QtCore.Qt.RightButton else 1
        self.clicked.emit(p.x(), p.y(), which)

    def update_view(self, exp, obj):
        gas = exp.gas
        is_a = gas.species == 0
        px_per_nm = 1.0 / max(self.getViewBox().viewPixelSize()[0], 1e-9)
        # Радиус зависит от массы; внутри одного сорта он одинаковый.
        for item, mask in ((self.gas_a, is_a), (self.gas_b, ~is_a)):
            size = 2 * gas.radius[mask][0] * px_per_nm if mask.any() else 0
            item.setData(pos=gas.pos[mask], size=size)

        chosen = [exp.i, exp.j] if obj == PAIR else [exp.i]
        colors = [style.MOL1, style.MOL2][:len(chosen)]
        self.chosen.setData(
            pos=gas.pos[chosen],
            size=[(2 * gas.radius[k] + 0.6) * px_per_nm for k in chosen],
            brush=[pg.mkBrush(c) for c in colors],
            pen=[pg.mkPen("w", width=2)] * len(chosen),
        )
        scale = ARROW_LENGTH / self.speed_scale
        for n, arrow in enumerate(self.arrows):
            if n < len(chosen):
                k = chosen[n]
                arrow.set(gas.pos[k], gas.vel[k] * scale, ARROW_HEAD)
            else:
                arrow.clear()
