import sys, time, runpy
sys.path.insert(0, ".")
sys.argv = ["main.py", "--smoke-test", "build/s.txt"]
import pages.demo.page as pg_
orig = pg_.DemoPage.on_tick
t0 = time.perf_counter()
def on_tick(self, fast, factor):
    a = time.perf_counter(); s0 = self.exp.steps_since_reset
    orig(self, fast, factor)
    b = time.perf_counter()
    print("t=%.2f tick %.3f s steps %d fast=%s" % (b - t0, b - a, self.exp.steps_since_reset - s0, fast), flush=True)
pg_.DemoPage.on_tick = on_tick
runpy.run_path("main.py", run_name="__main__")
