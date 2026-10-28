"""Набор случайных скоростей: сходимость гистограммы к распределению Рэлея."""
import numpy as np
from PyQt5 import QtCore, QtWidgets
import settings
from model import theory as tf
from model.stats import Histogram
from ui import style
from ui.plots.hist_plot import HistPlot
from ui.widgets import button, hbox, label, vbox


class SamplingDemo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()
        self.sigma = tf.sigma_for(28, 300)
        low, high = tf.value_range(tf.MODULUS, self.sigma)
        self.hist = Histogram(low, high, 30)
        self.plot = HistPlot(False)
        self.plot.rotate_button.hide()
        self.plot.setMinimumHeight(style.px(12))
        xs = np.linspace(low, high, 301)
        self.plot.configure("|v|, м/с", xs, tf.pdf(tf.MODULUS, xs, self.sigma),
                            peak=tf.peak(tf.MODULUS, self.sigma))
        self.readout = label(size=.95, wrap=True)
        self.auto_button = button("▶ Набирать", checkable=True)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(lambda: self.add_samples(settings.SAMPLES_PER_TICK))
        self.auto_button.toggled.connect(lambda on: self.timer.start() if on else self.timer.stop())
        buttons = [button(f"+{n}", lambda _checked, count=n: self.add_samples(count)) for n in (10,100,1000)]
        self.setLayout(vbox((self.plot, 1), self.readout,
            hbox(*buttons, self.auto_button, None, button("Сбросить", self.reset), spacing=style.px(.3)),
            spacing=style.px(.3)))
        self.update_view()

    def add_samples(self, n):
        self.hist.add(self.sigma * np.sqrt(-2 * np.log1p(-self.rng.random(n))))
        self.update_view()

    def reset(self):
        self.auto_button.setChecked(False)
        self.hist.reset()
        self.update_view()

    def hideEvent(self, event):
        self.auto_button.setChecked(False)
        super().hideEvent(event)

    def update_view(self):
        self.plot.update_view(self.hist)
        distance = np.sum(np.abs(self.hist.density()-tf.pdf(tf.MODULUS,self.hist.centers,self.sigma)))*self.hist.width
        error = style.fmt(distance,3) if self.hist.total else "—"
        self.readout.setText(f"N = <b>{style.fmt(self.hist.total)}</b> отсчётов &nbsp; ⟨|v|⟩ = <b>{style.fmt(self.hist.mean())}</b> м/с (теор. {style.fmt(tf.mean(tf.MODULUS,self.sigma))})<br>отличие от теории L1 = <b>{error}</b> (≈ 1/√N: чтобы уменьшить вдвое, нужно вчетверо больше отсчётов)")
