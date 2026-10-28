"""Движки температуры и масс меняют теоретические распределения."""
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets
import settings
from pages.theory.formula_browser import FormulaReadout
from model import theory as tf
from model.physics import K_B
from model.experiment import ENERGY_UNIT
from ui import labels, style
from ui.plots.base import StaticPlot, pen
from ui.widgets import ParamControl, button, hbox, vbox


SIGMA = r'<math>\sigma = \sqrt{\frac{kT}{m}}</math>'
VMP = r'<math>v_{\mathrm{вер}} = \sqrt{\frac{kT}{m}}</math>'
MU = r'<math>\mu = \frac{m_1m_2}{m_1+m_2}</math>'
RATIO = r'<math>\frac{\langle |\mathbf{v}_{\mathrm{отн}}|\rangle}{\langle |\mathbf{v}_1|\rangle}</math>'
SCALE = r'<math>\sqrt{\frac{m_1}{\mu}}</math>'


class CurveDemo(QtWidgets.QWidget):
    def __init__(self, variant):
        super().__init__()
        self.variant = variant
        self.start_m2 = 4 if variant == "mixture" else 28
        two = variant in ("relative", "mixture")
        self.temperature = ParamControl("Температура T, К", 50, 1500, 300)
        self.mass_1 = ParamControl("Масса m₁, а.е.м." if two else "Масса m, а.е.м.", 1, 200, 28)
        self.mass_2 = ParamControl("Масса m₂, а.е.м.", 1, 200, self.start_m2)
        self.mass_2.setVisible(two)
        self.plot = StaticPlot()
        self.plot.setMinimumHeight(style.px(12))
        self.legend = self.plot.addLegend(offset=(-10, 10), labelTextSize=f"{style.px(.8)}px")
        self.readout = FormulaReadout()
        self.items = []
        self.setLayout(vbox((self.plot, 1), self.readout, self.temperature, self.mass_1, self.mass_2,
            hbox(None, button("Подогнать масштаб", self.fit_axis), button("Сбросить", self.reset),
                 spacing=style.px(.4)), spacing=style.px(.3)))
        for c in (self.temperature, self.mass_1, self.mass_2):
            c.slider.valueChanged.connect(self.update_view)
            c.spin.valueChanged.connect(self.update_view)
        self.reset()

    @property
    def kind(self):
        return self.variant if self.variant in (tf.PROJECTION, tf.ENERGY) else tf.MODULUS

    def reset(self):
        for c, value in ((self.temperature, 300), (self.mass_1, 28), (self.mass_2, self.start_m2)):
            c.set_value_silently(value)
        self.fit_axis()

    def fit_axis(self):
        t, m1, m2 = self.temperature.value(), self.mass_1.value(), self.mass_2.value()
        mass = tf.reduced_mass(m1, m2) if self.variant in ("relative", "mixture") else m1
        scale = K_B*t/ENERGY_UNIT if self.kind == tf.ENERGY else tf.sigma_for(mass, t)
        self.high = tf.value_range(self.kind, scale)[1] * settings.THEORY_AXIS_ROOM
        self.update_view()

    def update_view(self, *_):
        if not hasattr(self, "high"):
            return
        t, m1, m2 = self.temperature.value(), self.mass_1.value(), self.mass_2.value()
        low = -self.high if self.kind == tf.PROJECTION else 0
        xs = np.linspace(low, self.high, 300)
        s = tf.sigma_for(m1, t)
        curves = [(tf.sigma_for(28, 300), "#9a9a9a", True, "T = 300 К, m = 28")]
        if self.variant == "projection":
            curves += [(s, style.PROJ, False, "f(vₓ)")]
            markers = [(-s, style.PROJ, "−σ"), (s, style.PROJ, "+σ")]
            text = f"{SIGMA} = <b>{style.fmt(s)}</b> м/с &nbsp; ⟨vₓ⟩ = 0 &nbsp; D = σ² = <b>{style.fmt(s*s/1e3,1)}</b>·10³ (м/с)²"
        elif self.variant == "modulus":
            mean, rms = tf.mean(tf.MODULUS, s), s*np.sqrt(2)
            curves += [(s, style.REL, False, "f(|v|)")]
            markers = [(s, style.MOL2, "vвер"), (mean, style.THEORY, "⟨v⟩"), (rms, style.PROJ, "√⟨v²⟩")]
            text = f"{VMP} = <b>{style.fmt(s)}</b> &nbsp; ⟨v⟩ = <b>{style.fmt(mean)}</b> &nbsp; √⟨v²⟩ = <b>{style.fmt(rms)}</b> м/с"
        elif self.variant in ("relative", "mixture"):
            mu = tf.reduced_mass(m1, m2)
            s2, sr = tf.sigma_for(m2, t), tf.sigma_for(mu, t)
            curves = [(tf.sigma_for(tf.reduced_mass(28, self.start_m2),300), "#9a9a9a",True,"vотн в начале"),
                      (s,style.MOL1,False,"|v₁|"), (s2,style.MOL2,m1 == m2,"|v₂|"), (sr,style.REL,False,"|vотн|")]
            mean1, meanr = tf.mean(tf.MODULUS,s), tf.mean(tf.MODULUS,sr)
            markers = [(mean1,style.MOL1,"⟨|v₁|⟩"), (meanr,style.REL,"⟨|vотн|⟩")]
            ratio = "√2 ≈ 1.414" if m1 == m2 else f"{SCALE} = {np.sqrt(m1/mu):.3f}"
            text = f"{MU} = <b>{style.fmt(mu,1)}</b> а.е.м.<br>⟨|v₁|⟩ = {style.fmt(mean1)}, ⟨|v₂|⟩ = {style.fmt(tf.mean(tf.MODULUS,s2))}, ⟨|vотн|⟩ = <b>{style.fmt(meanr)}</b> м/с<br>{RATIO} = <b>{ratio}</b>"
        else:
            s = K_B*t/ENERGY_UNIT
            curves = [(K_B*300/ENERGY_UNIT,"#9a9a9a",True,"T = 300 К"), (s,style.THEORY,False,"f(E)")]
            markers = [(s,style.REL,"⟨E⟩ = kT")]
            text = f"kT = <b>{style.fmt(s,2)}</b>·10⁻²¹ Дж &nbsp; ⟨E⟩ = kT &nbsp; D = (kT)²<br>Масса m = {m1} а.е.м. в формулу не входит — подвигайте её движок."
        for item in self.items:
            self.plot.removeItem(item)
        self.items = []
        self.legend.clear()
        densities = [tf.pdf(self.kind,xs,c[0]) for c in curves]
        peak = max(float(y.max()) for y in densities)
        exponent = 0 if self.kind == tf.ENERGY else int(np.floor(np.log10(peak)))
        factor = 10.**(-exponent)
        for (_,color,dashed,name), ys in zip(curves,densities):
            self.items.append(self.plot.plot(xs, ys*factor, pen=pen(color,.1 if dashed else .16,dashed),name=name))
        for row,(x,color,text_label) in enumerate(markers):
            line = pg.InfiniteLine(x, angle=90, pen=pen(color,.08,True))
            self.plot.addItem(line)
            text_item = pg.TextItem(text_label,color=color,anchor=(0,0))
            text_item.setFont(style.font(.8))
            text_item.setPos(x,peak*factor*(1.12-row*.09))
            self.plot.addItem(text_item)
            self.items.extend((line,text_item))
        self.plot.setXRange(low,self.high,padding=0)
        self.plot.setYRange(0,peak*factor*1.15,padding=0)
        value = "E" if self.kind == tf.ENERGY else "vₓ" if self.kind == tf.PROJECTION else "|v|"
        power = f"10{style.sup(exponent)} " if exponent else ""
        self.plot.set_axis_label("bottom",f"{value}, {labels.unit(self.kind)}")
        self.plot.set_axis_label("left",f"f, {power}{labels.density_unit(self.kind)}")
        self.readout.setText(text)
