import faulthandler, sys, runpy
faulthandler.dump_traceback_later(25, exit=True)
sys.argv = ["main.py", "--smoke-test", "build/s.txt"]
runpy.run_path("main.py", run_name="__main__")
