#!/usr/bin/env bash
set -euo pipefail

rm -rf site
mkdir -p site

pyxel package . main.py
pyxel app2html 2d_shooting_pyxel.pyxapp
mv 2d_shooting_pyxel.html site/index.html

echo "Built: site/index.html"

