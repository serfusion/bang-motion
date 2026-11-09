"""Inject timeline.json into index.html (<script id="tldata">) so the page stays a single file."""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
p = os.path.join(ROOT, "index.html")
html = open(p, encoding="utf-8").read()
data = json.dumps(tl, ensure_ascii=False, separators=(",", ":"))
assert "</script" not in data
html2, n = re.subn(r'(<script id="tldata" type="application/json">)(.*?)(</script>)',
                   lambda m: m.group(1) + data + m.group(3), html, flags=re.S)
assert n == 1
open(p, "w", encoding="utf-8").write(html2)
print("timeline injected:", len(data), "bytes")
