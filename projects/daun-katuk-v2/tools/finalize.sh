#!/bin/bash
# Encode the deliverables from the frame exports + the two mixes:
#   out/daun-katuk-v2.mp4            subtitle ID, VO + SFX + musik
#   out/daun-katuk-v2-tanpa-bgm.mp4  subtitle ID, VO + SFX (pasang musik sendiri di platform)
#   out/daun-katuk-v2-en.mp4         subtitle EN, VO + SFX + musik   (perlu build-en/video.mp4:
#                                    URL="file://$PWD/index.html?clean=1&lang=en" OUT=build-en node tools/export.mjs)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
enc() { ffmpeg -v error -y -i "$1/video.mp4" -c:v libx264 -preset slow -crf "${CRF:-21}" -maxrate 5M -bufsize 10M \
          -pix_fmt yuv420p -profile:v high -level 4.2 -an "$1/video-final.mp4"; }
mux() { ffmpeg -v error -y -i "$1/video-final.mp4" -i "build/$2.wav" -map 0:v -map 1:a -c:v copy \
          -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "out/$3.mp4"; }
enc build
mux build mix daun-katuk-v2
mux build mix-nobgm daun-katuk-v2-tanpa-bgm
if [ -f build-en/video.mp4 ]; then enc build-en; mux build-en mix daun-katuk-v2-en; fi
python3 tools/srt.py
ls -la out
