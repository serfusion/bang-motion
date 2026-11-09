"""Shared helpers for the mesin-video pipeline (paths, script parsing, icons)."""
import json, os, re

PROJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DATA = os.path.join(PROJ, "db", "data")
DBFILE = os.path.join(PROJ, "db", "konten.db")
ENGINE = os.path.join(PROJ, "engine")
EPISODES = os.path.join(PROJ, "episodes")
NODE_MODULES = os.environ.get("NODE_MODULES", os.path.join(PROJ, "node_modules"))

SCENE_TYPES = ("kuis", "jawaban", "langkah", "banding", "twist", "cta")
TAG = re.compile(r"\[([^\]]+)\]")
CUE = re.compile(r"\{(\w+)\}")


def ep_dir(eid, *p):
    return os.path.join(EPISODES, eid, *p)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj, indent=1):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def parse_vo(vo):
    """Parse a scene script.

    '[tag]'   ElevenLabs v3 delivery tag (kept for TTS, not a word, remembered as the mood of following words)
    '|'       subtitle page break (removed for TTS)
    '{cue}'   visual cue on the next word (removed for TTS)

    Returns (tts_text, words) where words = [{'w', 'page', 'cues': [...], 'tag': last tag or None}].
    """
    words, page, tag, pending = [], 0, None, []
    for tok in re.findall(r"\[[^\]]+\]|\||\S+", vo):
        if tok == "|":
            page += 1
            continue
        if TAG.fullmatch(tok):
            tag = TAG.fullmatch(tok).group(1)
            continue
        cues = CUE.findall(tok)
        word = CUE.sub("", tok)
        if not word:                      # a cue standing alone applies to the next word
            pending += cues
            continue
        words.append({"w": word, "page": page, "cues": pending + cues, "tag": tag})
        pending = []
    tts = CUE.sub("", vo).replace("|", " ")
    tts = re.sub(r"\s+", " ", tts).strip()
    return tts, words


def pages_en(vo_en):
    return [p.strip() for p in vo_en.split("|")]


def norm_word(s):
    return re.sub(r"[^0-9a-z]", "", s.lower())


# ---------- icons ----------
_FLUENT = None


def fluent_set():
    global _FLUENT
    if _FLUENT is None:
        p = os.path.join(NODE_MODULES, "@iconify-json", "fluent-emoji-flat", "icons.json")
        _FLUENT = load_json(p) if os.path.exists(p) else {"icons": {}, "aliases": {}}
    return _FLUENT


def icon_svg(name, assets):
    """Resolve an icon name to an inline SVG string. Custom assets (db aset) win over Fluent Emoji Flat names."""
    if name in assets:
        a = assets[name]
        path = os.path.join(ENGINE, "icons", a["berkas"])
        with open(path, encoding="utf-8") as f:
            return f.read()
    fs = fluent_set()
    key = name[7:] if name.startswith("fluent:") else name
    key = fs.get("aliases", {}).get(key, {}).get("parent", key)
    ic = fs["icons"].get(key)
    if not ic:
        return None
    w, h = ic.get("width", fs.get("width", 32)), ic.get("height", fs.get("height", 32))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{ic["body"]}</svg>'


def icon_names(ep):
    """All icon names referenced by an episode's scene params."""
    out = set()

    def walk(v, key=None):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, k)
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, str) and key and key.startswith("ikon"):
            out.add(v)
    for sc in ep["adegan"]:
        walk(sc["param"])
    return sorted(out)
