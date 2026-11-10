"""Shared helpers for the mesin-video pipeline (paths, script parsing, icons)."""
import json, os, re

PROJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DATA = os.path.join(PROJ, "db", "data")
DBFILE = os.path.join(PROJ, "db", "konten.db")
ENGINE = os.path.join(PROJ, "engine")
EPISODES = os.path.join(PROJ, "episodes")
NODE_MODULES = os.environ.get("NODE_MODULES", os.path.join(PROJ, "node_modules"))

SCENE_TYPES = ("kuis", "jawaban", "langkah", "banding", "twist", "cta", "pembuka", "catatan", "ibarat", "tanya")
FORMAT_SCENES = {"tebakan": ("kuis", "jawaban", "langkah", "banding", "twist", "cta"),
                 "fakta": ("pembuka", "catatan", "ibarat", "tanya", "langkah", "banding")}
# pacing per format: max pause between words, pause after "...", after "?", default tempo, breath between scenes
PACE = {"tebakan": {"cap": 0.24, "suspense": 0.42, "question": 0.34, "tempo": None, "scene_gap": 0.0},
        "fakta": {"cap": 0.42, "suspense": 0.6, "question": 0.5, "tempo": 1.0, "scene_gap": 0.3}}
LANGS = ("id", "en")
TAG = re.compile(r"\[([^\]]+)\]")
CUE = re.compile(r"\{(\w+)\}")
SHOWN = re.compile(r"<([^=>]*)=([^>]*)>(.*)")
SHOWN_ANY = re.compile(r"<([^=>]*)=([^>]*)>")


def ep_dir(eid, *p):
    return os.path.join(EPISODES, eid, *p)


def lang_dir(eid, lang, *p):
    """Per-language output folder: episodes/ID/id/... or episodes/ID/en/..."""
    return os.path.join(EPISODES, eid, lang, *p)


def merged_param(sc, lang):
    """Scene params for a language: param_en overrides param (dicts merge, lists are replaced)."""
    def merge(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            out = dict(a)
            for k, v in b.items():
                out[k] = merge(a.get(k), v) if k in a else v
            return out
        return b
    p = sc.get("param") or {}
    return merge(p, sc.get("param_en") or {}) if lang == "en" else p


def script(sc, lang):
    return sc["vo_en"] if lang == "en" else sc["vo"]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj, indent=1):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def parse_vo(vo):
    """Parse a scene script.

    '[tag]'           ElevenLabs v3 delivery tag (kept for TTS, not a word, remembered as the mood of following words)
    '|'               subtitle page break (removed for TTS)
    '{cue}'           visual cue on the next word (removed for TTS)
    '<shown=spoken>'  the voice says 'spoken', the subtitle shows 'shown' (numbers: <1964=seribu sembilan ratus
                      enam puluh empat>, <0,05%=nol koma nol lima persen>); punctuation right after '>' is kept on both

    Returns (tts_text, words) where words = [{'w', 'page', 'cues': [...], 'tag': last tag or None}], one entry per
    spoken word; the 2nd.. spoken words of a <shown=spoken> group get w == '' (layout merges them into the first).
    """
    words, page, tag, pending = [], 0, None, []
    for tok in re.findall(r"\[[^\]]+\]|\||(?:\{[^}]*\})*<[^>]*>[^\s\[|<]*|\S+", vo):
        if tok == "|":
            page += 1
            continue
        if TAG.fullmatch(tok):
            tag = TAG.fullmatch(tok).group(1)
            continue
        cues = CUE.findall(tok)
        word = CUE.sub("", tok)
        g = SHOWN.fullmatch(word)
        if g:
            shown, spoken, tail = g.group(1).strip(), g.group(2).split(), g.group(3)
            if not shown or not spoken:
                raise ValueError(f"format <tampil=ucapan> salah: {tok}")
            words.append({"w": shown + tail, "page": page, "cues": pending + cues, "tag": tag})
            words += [{"w": "", "page": page, "cues": [], "tag": tag} for _ in spoken[1:]]
            pending = []
            continue
        if not word:                      # a cue standing alone applies to the next word
            pending += cues
            continue
        words.append({"w": word, "page": page, "cues": pending + cues, "tag": tag})
        pending = []
    tts = SHOWN_ANY.sub(lambda m: m.group(2), CUE.sub("", vo)).replace("|", " ")
    tts = re.sub(r"\s+", " ", tts).strip()
    return tts, words


def display_text(vo):
    """What the subtitle shows for a script (tags, cues and page breaks removed, <shown=spoken> -> shown)."""
    _, ws = parse_vo(vo)
    return " ".join(w["w"] for w in ws if w["w"])


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


def icon_names(ep, lang=None):
    """All icon names referenced by an episode's scene params (both languages unless one is given)."""
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
        walk(sc.get("param") or {})
        if lang in (None, "en"):
            walk(sc.get("param_en") or {})
    return sorted(out)
