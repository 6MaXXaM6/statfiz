import faulthandler, sys, time, runpy
faulthandler.enable()
sys.path.insert(0, ".")
sys.argv = ["main.py", "--smoke-test", "build/s.txt"]
import main as m
orig_smoke = m.smoke_test
def smoke(app, window, path):
    print("smoke armed", flush=True)
    import PyQt5.QtCore as QC
    QC.QTimer.singleShot(1000, lambda: print("1s timer ok", flush=True))
    orig_smoke(app, window, path)
    t0 = time.perf_counter()
    def beat():
        print("heartbeat %.1f s" % (time.perf_counter() - t0), flush=True)
        QC.QTimer.singleShot(1000, beat)
    QC.QTimer.singleShot(1000, beat)
    app.aboutToQuit.connect(lambda: print("aboutToQuit", flush=True))
m.smoke_test = smoke
import pages.demo.page as pg_
orig = pg_.DemoPage.on_tick
n = [0]
def on_tick(self, fast, factor):
    n[0] += 1
    if n[0] % 20 == 0: print("tick", n[0], flush=True)
    orig(self, fast, factor)
pg_.DemoPage.on_tick = on_tick
m.main()
