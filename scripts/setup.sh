#!/usr/bin/env bash
# Prepara o ambiente: venv com yt-dlp, Whisper, Shazam e Pillow. Idempotente.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v ffmpeg >/dev/null; then
  if command -v apt-get >/dev/null; then
    (apt-get update -qq && apt-get install -y -qq ffmpeg) >/dev/null 2>&1 || true
  fi
  command -v ffmpeg >/dev/null || { echo "Instale o ffmpeg (brew install ffmpeg / apt install ffmpeg)." >&2; exit 1; }
fi

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if ! cmp -s requirements.txt .venv/.requirements 2>/dev/null; then
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
  cp requirements.txt .venv/.requirements
fi
# O Instagram muda com frequência; o yt-dlp acompanha. Atualiza sem travar a sessão se falhar.
.venv/bin/pip install -q --upgrade yt-dlp >/dev/null 2>&1 || true
echo "ambiente pronto"
