"""Векторная диаграмма в общей графической сцене сосуда."""
# Текст цветной формулы под построением находится в pages/demo/readouts.py, сами обозначения — в ui/labels.py.

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style
from ui.plots.base import Arrow

HEAD = 0.12  # наконечник стрелки в долях характерной скорости


# Дополнительная диаграмма v1, v2 и vотн; рисуется на общем холсте без отдельного маленького окна.
class VectorView(QtWidgets.QGraphicsObject):
    """Общий масштаб v1, v2 и v1 − v2; отдельного обрезающего viewport нет."""

    # Здесь задаются толщины отдельных стрелок, серые оси и надпись x; цвета скоростей — в settings.py.
    def __init__(self):
        super().__init__()
        self.setZValue(20)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.radius = 1.0
        self.fits = True
        self._area = QtCore.QRectF()
        self._anchor = QtCore.QPointF()
        self._pixels_per_velocity = 1.0
        self._projection = False
        self.v1 = Arrow(style.MOL1)
        self.v2 = Arrow(style.MOL2)
        self.rel = Arrow(style.REL, width=0.28)
        self.proj = Arrow(style.PROJ, width=0.35)
        self.arrows = (self.v1, self.v2, self.rel, self.proj)
        self.axes = (QtWidgets.QGraphicsLineItem(), QtWidgets.QGraphicsLineItem())
        self.x_label = pg.TextItem("x", color="#888888", anchor=(1, 1))
        for item in (*self.arrows, *self.axes, self.x_label):
            item.setParentItem(self)
            item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        for axis in self.axes:
            axis.setPen(pg.mkPen("#bbbbbb", width=1))
        self.rescale_layout()

    # Сообщает Qt границы всех дочерних элементов для корректного обновления сцены.
    def boundingRect(self):
        return self.childrenBoundingRect()

    # Сама группа не рисует фон: частицы под построением остаются видны.
    def paint(self, painter, option, widget=None):
        pass  # Рисуют дочерние элементы; фон — общий с сосудом.

    # Размер надписи x задаётся коэффициентом .8 относительно базового шрифта.
    def rescale_layout(self):
        self.x_label.setFont(style.font(.8))

    # Характерная скорость определяет длину наконечников и протяжённость вспомогательных осей.
    def set_radius(self, radius):
        self.radius = radius

    # Получает от BoxView доступную область и предпочитаемый якорь построения.
    def set_area(self, area, anchor):
        """Допустим весь холст, в том числе поля за чёрной границей сосуда."""
        self._area = QtCore.QRectF(area)
        self._anchor = QtCore.QPointF(anchor)
        self._place()

    # Сохраняет общий масштаб с сосудом; не нормирует каждый вектор по отдельности.
    def match_pixel_scale(self, pixels_per_velocity):
        if pixels_per_velocity > 0:
            self._pixels_per_velocity = pixels_per_velocity
            self._place()

    # Сдвигает построение целиком; если оно больше холста, временно скрывает все его стрелки.
    def _place(self):
        self.prepareGeometryChange()
        scale = self._pixels_per_velocity
        transform = QtGui.QTransform.fromScale(scale, -scale)
        self.setTransform(transform)
        # Считаем весь треугольник, включая наконечники и проекцию. Толщина
        # косметического пера измеряется в пикселях, поэтому запас добавляем после масштаба.
        bounds = QtCore.QRectF()
        for arrow in self.arrows:
            if not arrow.path().isEmpty():
                bounds = bounds.united(transform.mapRect(arrow.path().boundingRect()))
        pad = max(4., max(arrow.pen().widthF() for arrow in self.arrows) + 2.)
        bounds.adjust(-pad, -pad, pad, pad)
        area = self._area
        self.fits = area.width() >= bounds.width() and area.height() >= bounds.height()
        if self.fits:
            x = min(max(self._anchor.x(), area.left() - bounds.left()), area.right() - bounds.right())
            y = min(max(self._anchor.y(), area.top() - bounds.top()), area.bottom() - bounds.bottom())
            self.setPos(x, y)
            # Оси конечные: они также не выходят за доступный холст.
            left = max((area.left() - x) / scale, -self.radius)
            right = min((area.right() - x) / scale, self.radius)
            bottom = max((y - area.bottom()) / scale, -self.radius)
            top = min((y - area.top()) / scale, self.radius)
            self.axes[0].setLine(left, 0, right, 0)
            self.axes[1].setLine(0, bottom, 0, top)
            self.x_label.setPos(right, 0)
        for arrow in (self.v1, self.v2, self.rel):
            arrow.setVisible(self.fits)
        self.proj.setVisible(self.fits and self._projection)
        for item in (*self.axes, self.x_label):
            item.setVisible(self.fits and self._projection)

    # Строит разность от конца v2 к концу v1; projection_of выбирает дополнительную проекцию.
    def update_view(self, exp, projection_of=None):
        self.prepareGeometryChange()
        self._projection = projection_of is not None
        head = HEAD * self.radius
        v1, v2 = exp.gas.vel[exp.i], exp.gas.vel[exp.j]
        self.v1.set((0., 0.), v1, head)
        self.v2.set((0., 0.), v2, head)
        # Чёрный вектор соединяет концы синего и красного: это геометрическое построение vотн = v1 − v2.
        self.rel.set(v2, v1 - v2, head)
        if projection_of is None:
            self.proj.clear()
        else:
            self.proj.set((0., 0.), (exp.velocity(projection_of)[0], 0.), head)
        self._place()
