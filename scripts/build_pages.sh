#!/usr/bin/env bash
set -euo pipefail

rm -rf site
mkdir -p site

pyxel package . main.py
pyxel app2html 2d_shooting_pyxel.pyxapp
mv 2d_shooting_pyxel.html site/index.html

# Browser UX: prevent arrow keys from scrolling the page and ensure canvas focus.
python - <<'PY'
from pathlib import Path

p = Path("site/index.html")
html = p.read_text(encoding="utf-8")

inject = """<style>
html, body { margin: 0; padding: 0; overflow: hidden; background: #000; }
canvas { outline: none; }
</style>
<script>
// Prevent arrow keys from scrolling the page while playing.
window.addEventListener("keydown", (e) => {
  const keys = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "];
  if (keys.includes(e.key)) e.preventDefault();
}, { passive: false });

// Ensure the Pyxel canvas can receive keyboard focus.
function focusPyxelCanvas() {
  const c = document.querySelector("canvas");
  if (!c) return false;
  c.tabIndex = 0;
  c.focus();
  c.addEventListener("pointerdown", () => c.focus());
  return true;
}
let tries = 0;
const t = setInterval(() => {
  tries += 1;
  if (focusPyxelCanvas() || tries > 100) clearInterval(t);
}, 50);
</script>
"""

marker = '<script src="https://cdn.jsdelivr.net/gh/kitao/pyxel@'
idx = html.find(marker)
if idx == -1:
    raise SystemExit("unexpected HTML format; cannot inject key handling")

after_first_script = html.find("</script>", idx)
if after_first_script == -1:
    raise SystemExit("unexpected HTML format; missing </script>")

after_first_script += len("</script>")
html = html[:after_first_script] + "\n" + inject + "\n" + html[after_first_script:]
p.write_text(html, encoding="utf-8")
PY

echo "Built: site/index.html"
