#!/bin/bash
# Encode the two deliverables from the frame export + the two mixes:
#   out/daun-katuk.mp4            (VO + SFX + BGM)
#   out/daun-katuk-tanpa-bgm.mp4  (VO + SFX, for adding your own music on the platform)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
ffmpeg -v error -y -i build/video.mp4 -c:v libx264 -preset slow -crf "${CRF:-21}" -maxrate 4M -bufsize 8M \
  -pix_fmt yuv420p -profile:v high -level 4.2 -an build/video-final.mp4
for v in "mix:daun-katuk" "mix-nobgm:daun-katuk-tanpa-bgm"; do
  ffmpeg -v error -y -i build/video-final.mp4 -i "build/${v%%:*}.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "out/${v##*:}.mp4"
done
python3 tools/srt.py
ls -la out
