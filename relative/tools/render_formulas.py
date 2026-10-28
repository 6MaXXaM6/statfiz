"""Пересобрать SVG из <math> в assets/theory/*.html.

Только для подготовки ресурсов: pip install matplotlib==3.7.5.
Приложение использует готовые SVG и не требует matplotlib или LaTeX.
"""
import ast
import hashlib
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import mathtext  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "assets" / "theory"


def main():
    output = ROOT / "formulas"
    output.mkdir(exist_ok=True)
    expressions = {expr for page in ROOT.glob("*.html")
                   for expr in re.findall(r"<math>(.*?)</math>", page.read_text(encoding="utf-8"), re.S)}
    for source in (ROOT.parents[1] / "pages" / "theory").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                expressions.update(re.findall(r"<math>(.*?)</math>", node.value, re.S))
    matplotlib.rcParams.update({"mathtext.fontset": "dejavusans", "svg.hashsalt": "relative-theory"})
    for expr in sorted(expressions):
        name = hashlib.sha256(expr.encode("utf-8")).hexdigest()[:20]
        mathtext.math_to_image("$" + expr + "$", output / (name + ".svg"),
                              dpi=96, format="svg", color="#182c49")
    print("Формул:", len(expressions))


if __name__ == "__main__":
    main()
