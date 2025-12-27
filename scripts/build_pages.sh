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
#start-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.85);
  color: #fff;
  font-family: system-ui, -apple-system, sans-serif;
  text-align: center;
  padding: 24px;
  z-index: 9999;
}
#start-overlay button {
  font-size: 18px;
  padding: 12px 18px;
  border: 1px solid #666;
  background: #111;
  color: #fff;
  border-radius: 10px;
}
#start-overlay p { max-width: 34em; line-height: 1.4; }
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

function startGame() {
  const overlay = document.getElementById("start-overlay");
  if (overlay) overlay.remove();

  // Create <pyxel-run> dynamically so iOS counts it as a user gesture
  // (needed to enable audio playback).
  const el = document.createElement("pyxel-run");
  el.setAttribute("root", ".");
  el.setAttribute("name", "main.py");
  el.setAttribute("gamepad", "enabled");
  document.body.appendChild(el);

  let tries = 0;
  const t = setInterval(() => {
    tries += 1;
    if (focusPyxelCanvas() || tries > 300) clearInterval(t);
  }, 50);
}

window.addEventListener("load", () => {
  const btn = document.getElementById("start-button");
  if (btn) {
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      startGame();
    }, { passive: false });
  }
});
</script>

<div id="start-overlay">
  <div>
    <button id="start-button">Tap to Start</button>
    <p>On iPhone/iPad, audio is disabled until the first user interaction. Please tap to start.</p>
  </div>
</div>
HTML

echo "Built: site/index.html"
