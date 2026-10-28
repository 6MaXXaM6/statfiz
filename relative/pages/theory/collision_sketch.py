"""Схема упругого удара: та же нормальная компонента импульса, что в модели."""
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from ui import style


class CollisionSketch(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(style.px(14), style.px(12))

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(self.rect(), QtCore.Qt.white)
        u = min(self.width(), self.height()) / 11
        center = QtCore.QPointF(self.width()/2, self.height()/2)
        def at(v):
            return center + QtCore.QPointF(v[0]*u, -v[1]*u)
        def caption(text, point, color):
            doc = QtGui.QTextDocument()
            doc.setDefaultFont(style.font(.95, True))
            doc.setDocumentMargin(0)
            doc.setHtml(f'<span style="color:{color}">{text}</span>')
            p.save()
            p.translate(point)
            doc.drawContents(p)
            p.restore()
        def arrow(start, end, color, head=.45):
            a,b = at(start),at(end)
            delta = end-start
            length = np.linalg.norm(delta)
            if length == 0:
                return
            n = delta/length
            h = min(head,length*.6)
            base = end-n*h
            normal = np.array([-n[1],n[0]])*h*.45
            p.setPen(QtGui.QPen(QtGui.QColor(color),style.px(.22)))
            p.drawLine(a,at(base))
            p.setBrush(QtGui.QColor(color))
            p.drawPolygon(QtGui.QPolygonF([b,at(base+normal),at(base-normal)]))
        p1,p2 = np.array([-1.1,.35]),np.array([1.3,-.45])
        v1,v2 = np.array([2.2,-.6]),np.array([-1.4,.9])
        d = p2-p1
        n = d/np.linalg.norm(d)
        vn = np.dot(v2-v1,n)
        after1,after2 = v1+n*(4/3*vn),v2-n*(2/3*vn)
        p.setPen(QtGui.QPen(QtGui.QColor("#888888"),1,QtCore.Qt.DashLine))
        p.drawLine(at(p1-n*2.5),at(p2+n*2.5))
        for point,r,color in ((p1,1.1,style.MOL1),(p2,1.4,style.MOL2)):
            fill = QtGui.QColor(color)
            fill.setAlphaF(.35)
            p.setPen(QtGui.QPen(QtGui.QColor(color),2))
            p.setBrush(fill)
            p.drawEllipse(at(point),r*u,r*u)
        arrow(p1-v1,p1,"black")
        arrow(p2-v2,p2,"black")
        arrow(p1,p1+after1,style.HILITE)
        arrow(p2,p2+after2,style.HILITE)
        arrow(p1+n*1.1,p1+n*2.3,style.PROJ,.36)
        for text,point,offset,color in (
            ("n",p1+n*2.3,(0,-.8),style.PROJ),
            ("v₁",p1-v1,(-.9,-.3),"black"),("v₂",p2-v2,(.1,-.2),"black"),
            ("v′₁",p1+after1,(-.9,-.6),style.HILITE),("v′₂",p2+after2,(.1,-.2),style.HILITE)):
            caption(text,at(point)+QtCore.QPointF(offset[0]*u,offset[1]*u),color)
        caption("чёрные — до удара, оранжевые — после",QtCore.QPointF(.3*u,self.height()-.8*u),"#555555")
