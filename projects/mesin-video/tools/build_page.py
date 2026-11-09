"""Assemble the single-file page for one episode: engine CSS + JS + GSAP + timeline + icon SVGs.

  python3 tools/build_page.py ID      -> episodes/ID/index.html   (open it directly; ?debug=1 scrub, ?lang=en)
"""
import json, os, sys
from common import ENGINE, NODE_MODULES, ep_dir, load_json, icon_names, icon_svg

ENGINE_ICONS = ["love-letter"]          # icons the templates use themselves
JS = ["core.js", "reuse.js", "scenes.js", "main.js"]


def main(eid):
    ep = load_json(ep_dir(eid, "episode.json"))
    tl = load_json(ep_dir(eid, "timeline.json"))
    tl["icons"] = {n: icon_svg(n, ep.get("aset", {})) for n in icon_names(ep) + ENGINE_ICONS}
    miss = [n for n, v in tl["icons"].items() if not v]
    if miss:
        sys.exit(f"ikon tidak ditemukan: {miss}")
    rd = lambda p: open(p, encoding="utf-8").read()
    css = rd(os.path.join(ENGINE, "page.css"))
    js = "\n".join(rd(os.path.join(ENGINE, "js", f)) for f in JS)
    gsap = rd(os.path.join(NODE_MODULES, "gsap", "dist", "gsap.min.js"))
    data = json.dumps(tl, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="id">
<!-- {ep['judul']} — dibangkitkan oleh mesin-video dari database (episode '{eid}'). Bang Motion (HTML + GSAP) + video-shotcraft.
     ?debug=1 scrub, ?clean=1 export, ?lang=en subtitle Inggris. -->
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ep['judul']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,100..900,0..100,0..1;1,9..144,100..900,0..100,0..1&family=Plus+Jakarta+Sans:ital,wght@0,400..800;1,400..800&family=Kalam:wght@400;700&display=block" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<svg id="filters" aria-hidden="true"><defs>
  <filter id="whip" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="whipG" stdDeviation="0 0"/></filter>
</defs></svg>
<div id="stage">
  <div id="cam"><div id="world"></div></div>
  <div id="hud"><div id="dim"></div><div id="teaser"></div><div id="lens"></div><div class="light" id="light"></div><div class="grain" id="grain"></div>
    <div class="vig"></div><div id="flash"></div><div id="prog"></div><div id="mascot"></div><div id="subs"></div></div>
</div>
<div id="dbg"><button id="dPlay">Pause</button><input id="dScrub" type="range" min="0" max="1000" value="0"><span id="dClock">0.00s</span></div>
<audio id="vo" src="mix.m4a" preload="auto"></audio>
<script>{gsap}</script>
<script id="tldata" type="application/json">{data}</script>
<script>
{js}
</script>
</body>
</html>
"""
    with open(ep_dir(eid, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"halaman: episodes/{eid}/index.html ({len(html) // 1024} KB, {len(tl['icons'])} ikon)")


if __name__ == "__main__":
    main(sys.argv[1])
