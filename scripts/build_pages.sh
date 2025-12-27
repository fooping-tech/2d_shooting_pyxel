#!/usr/bin/env bash
set -euo pipefail

rm -rf site
mkdir -p site

# Copy runtime files for <pyxel-run>.
cp -f main.py site/main.py
cp -f README.md site/README.md || true
cp -rf config site/config
cp -rf src site/src

# Pyxel WASM loader uses synchronous XHR against directory paths (e.g. "src", "src/core").
# GitHub Pages serves directories only when an index.html exists, so add minimal ones.
for d in \
  site/config \
  site/src \
  site/src/core \
  site/src/scenes \
  site/src/entities \
  site/src/systems \
  site/src/ui
do
  mkdir -p "$d"
  printf '%s\n' '<!doctype html><meta charset="utf-8"><title>dir</title>' > "$d/index.html"
done

cat > site/index.html <<'HTML'
<!doctype html>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>2d_shooting_pyxel</title>
<script src="https://cdn.jsdelivr.net/gh/kitao/pyxel@2.5.11/wasm/pyxel.js"></script>
<style>
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
  if (focusPyxelCanvas() || tries > 200) clearInterval(t);
}, 50);
</script>

<!-- Gamepad support via custom element -->
<pyxel-run root="." name="main.py" gamepad="enabled"></pyxel-run>
HTML

echo "Built: site/index.html"
