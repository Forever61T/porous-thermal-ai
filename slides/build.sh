#!/bin/sh
# Independent build entry point; never runs upstream init/clean targets.
set -eu
cd "$(dirname "$0")"
PATH="/Library/TeX/texbin:/usr/local/texlive/2026/bin/universal-darwin:$PATH"
export PATH
if [ ! -f zju_beamer.sty ] || [ ! -f figures/logo.pdf ] || [ ! -f figures/char.pdf ] || [ ! -f figures/background.png ]; then
  echo 'Missing pinned theme files. Run: python3 fetch_theme.py'
  exit 1
fi
xelatex -interaction=nonstopmode -halt-on-error main.tex > build-xelatex-1.log 2>&1
bibtex main > build-bibtex.log 2>&1
xelatex -interaction=nonstopmode -halt-on-error main.tex > build-xelatex-2.log 2>&1
xelatex -interaction=nonstopmode -halt-on-error main.tex > build-xelatex-3.log 2>&1
echo 'Built main.pdf. Inspect it before submission.'
