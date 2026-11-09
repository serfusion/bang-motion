"""Content database (SQLite) for the video engine.

  python3 tools/db.py init                 create db/konten.db from db/schema.sql (drops the old file)
  python3 tools/db.py import               load db/data/*.json + db/data/episode/*.json (upsert)
  python3 tools/db.py validate [ID ...]    check scenes, cues, subtitle pages, icons, facts
  python3 tools/db.py list                 episodes with status
  python3 tools/db.py export ID            write episodes/ID/episode.json (everything the pipeline needs)
  python3 tools/db.py musik                analyse BPM / first full beat of every track without them (writes musik.json + db)

The JSON files under db/data are the editable source of truth (diff-friendly); the SQLite file is what a web/app
backend reads and writes. A backend can also insert rows directly and run `export` + tools/make_video.py.
"""
import glob, json, os, sqlite3, sys
from common import (DATA, DBFILE, PROJ, ENGINE, SCENE_TYPES, ep_dir, load_json, save_json, parse_vo, pages_en,
                    icon_names, icon_svg)

TABLES = [("kategori", "kategori.json"), ("sumber", "sumber.json"), ("suara", "suara.json"), ("musik", "musik.json"),
          ("aset", "aset.json"), ("fakta", "fakta.json")]


def connect():
    con = sqlite3.connect(DBFILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def cmd_init():
    if os.path.exists(DBFILE):
        os.remove(DBFILE)
    con = connect()
    con.executescript(open(os.path.join(PROJ, "db", "schema.sql"), encoding="utf-8").read())
    con.commit()
    print("created", os.path.relpath(DBFILE, PROJ))


def upsert(con, table, row):
    cols = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
    vals = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in row.items() if k in cols}
    keys = ",".join(vals)
    con.execute(f"INSERT OR REPLACE INTO {table} ({keys}) VALUES ({','.join('?' * len(vals))})", list(vals.values()))


def cmd_import():
    if not os.path.exists(DBFILE):
        cmd_init()
    con = connect()
    for table, fname in TABLES:
        for row in load_json(os.path.join(DATA, fname)):
            upsert(con, table, row)
    n = 0
    for f in sorted(glob.glob(os.path.join(DATA, "episode", "*.json"))):
        ep = load_json(f)
        upsert(con, "episode", ep)
        con.execute("DELETE FROM adegan WHERE episode_id=?", (ep["id"],))
        con.execute("DELETE FROM episode_fakta WHERE episode_id=?", (ep["id"],))
        for i, sc in enumerate(ep["adegan"]):
            upsert(con, "adegan", {"episode_id": ep["id"], "urutan": i + 1, "jenis": sc["jenis"], "vo": sc["vo"],
                                   "vo_en": sc["vo_en"], "param": sc.get("param", {})})
        for fid in ep.get("fakta", []):
            con.execute("INSERT INTO episode_fakta VALUES (?,?)", (ep["id"], fid))
        n += 1
    con.commit()
    print(f"imported {n} episodes into {os.path.relpath(DBFILE, PROJ)}")


def load_episode(con, eid):
    """Episode row joined with scenes, facts, sources, voice, music and assets (same shape as the JSON seed)."""
    r = con.execute("SELECT * FROM episode WHERE id=?", (eid,)).fetchone()
    if not r:
        sys.exit(f"episode not found: {eid}")
    ep = dict(r)
    ep["adegan"] = [{"jenis": a["jenis"], "vo": a["vo"], "vo_en": a["vo_en"], "param": json.loads(a["param"] or "{}")}
                    for a in con.execute("SELECT * FROM adegan WHERE episode_id=? ORDER BY urutan", (eid,))]
    ep["fakta"] = [dict(f) for f in con.execute(
        "SELECT f.* FROM fakta f JOIN episode_fakta ef ON ef.fakta_id=f.id WHERE ef.episode_id=? ORDER BY f.id", (eid,))]
    sids = sorted({f["sumber_id"] for f in ep["fakta"] if f["sumber_id"]})
    ep["sumber"] = [dict(s) for s in con.execute(f"SELECT * FROM sumber WHERE id IN ({','.join('?' * len(sids))})", sids)]
    v = dict(con.execute("SELECT * FROM suara WHERE id=?", (ep["suara_id"],)).fetchone())
    v["pengaturan"] = json.loads(v["pengaturan"] or "{}")
    ep["suara"] = v
    ep["musik"] = dict(con.execute("SELECT * FROM musik WHERE id=?", (ep["musik_id"],)).fetchone())
    ep["aset"] = {a["id"]: dict(a) for a in con.execute("SELECT * FROM aset")}
    return ep


# required cues / params per scene type (cue names are written as {name} in the script)
def check_scene(i, sc, prev, errs, warns):
    p, j = sc["param"], sc["jenis"]
    tag = f"adegan {i + 1} ({j})"
    if j not in SCENE_TYPES:
        errs.append(f"{tag}: jenis tidak dikenal")
        return
    _, words = parse_vo(sc["vo"])
    cues = [c for w in words for c in w["cues"]]
    n_id = max(w["page"] for w in words) + 1 if words else 0
    if n_id != len(pages_en(sc["vo_en"])):
        errs.append(f"{tag}: jumlah halaman subtitle ID ({n_id}) != EN ({len(pages_en(sc['vo_en']))})")
    need = lambda k: p.get(k) not in (None, "", []) or errs.append(f"{tag}: param '{k}' wajib")
    if j == "kuis":
        need("judul"); need("pilihan")
        if not 2 <= len(p.get("pilihan", [])) <= 3:
            errs.append(f"{tag}: pilihan harus 2-3")
        if not 0 <= p.get("jawaban", -1) < len(p.get("pilihan", [])):
            errs.append(f"{tag}: 'jawaban' harus indeks pilihan")
    if j == "jawaban":
        if not prev or prev["jenis"] != "kuis":
            errs.append(f"{tag}: harus tepat setelah adegan kuis")
        if "jawab" not in cues:
            errs.append(f"{tag}: butuh isyarat {{jawab}} pada kata jawaban")
        if p.get("label") and prev and len(p["label"]) != len(prev["param"].get("pilihan", [])):
            errs.append(f"{tag}: 'label' harus sejumlah pilihan kuis")
        if p.get("besar") and "besar" not in cues:
            warns.append(f"{tag}: 'besar' tanpa isyarat {{besar}} -> muncul 1 dtk setelah jawaban")
    if j in ("langkah", "banding"):
        need("item")
        lim = (2, 4) if j == "langkah" else (2, 3)
        if not lim[0] <= len(p.get("item", [])) <= lim[1]:
            errs.append(f"{tag}: item harus {lim[0]}-{lim[1]}")
        pre = "l" if j == "langkah" else "b"
        miss = [f"{pre}{k}" for k in range(len(p.get("item", []))) if f"{pre}{k}" not in cues]
        if miss:
            warns.append(f"{tag}: isyarat {miss} tidak ada -> item muncul merata sepanjang adegan")
    if j == "twist":
        need("headline")
        if p.get("nada", "peringatan") not in ("peringatan", "kejutan"):
            errs.append(f"{tag}: nada harus peringatan|kejutan")
    if j == "cta":
        need("judul")
    if p.get("teaser") and "teaser" not in cues:
        errs.append(f"{tag}: 'teaser' butuh isyarat {{teaser}}")


def validate(ep):
    errs, warns = [], []
    prev = None
    for i, sc in enumerate(ep["adegan"]):
        check_scene(i, sc, prev, errs, warns)
        prev = sc
    if ep["adegan"] and ep["adegan"][0]["jenis"] != "kuis":
        warns.append("adegan pertama bukan kuis: hook 3 detik pertama harus tetap kuat")
    if ep["adegan"] and ep["adegan"][-1]["jenis"] != "cta":
        warns.append("adegan terakhir bukan cta")
    for name in icon_names(ep):
        if not icon_svg(name, ep.get("aset", {})):
            errs.append(f"ikon tidak ditemukan: {name}")
    return errs, warns


def cmd_validate(ids):
    con = connect()
    ids = ids or [r["id"] for r in con.execute("SELECT id FROM episode ORDER BY id")]
    bad = 0
    for eid in ids:
        errs, warns = validate(load_episode(con, eid))
        print(f"{eid}: {'OK' if not errs else str(len(errs)) + ' error'}" + (f", {len(warns)} peringatan" if warns else ""))
        for e in errs:
            print("  x", e)
        for w in warns:
            print("  !", w)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


def cmd_list():
    con = connect()
    for r in con.execute("SELECT e.id, e.status, e.judul, COUNT(a.urutan) n FROM episode e LEFT JOIN adegan a "
                         "ON a.episode_id=e.id GROUP BY e.id ORDER BY e.id"):
        print(f"{r['id']:<22} {r['status']:<9} {r['n']} adegan  {r['judul']}")


def cmd_export(eid):
    con = connect()
    ep = load_episode(con, eid)
    errs, warns = validate(ep)
    if errs:
        sys.exit("validation failed:\n  " + "\n  ".join(errs))
    out = ep_dir(eid, "episode.json")
    save_json(out, ep)
    print("exported", os.path.relpath(out, PROJ))


def cmd_musik():
    import librosa, numpy as np
    rows = load_json(os.path.join(DATA, "musik.json"))
    for m in rows:
        if m.get("bpm") and m.get("mulai") is not None:
            continue
        path = os.path.join(ENGINE, "audio", "bgm", m["berkas"])
        y, sr = librosa.load(path, sr=22050, mono=True, duration=120)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
        bt = np.asarray(beats)
        T = float(np.median(np.diff(bt)))
        # first beat after which the band is playing (short-term RMS reaches 70 % of the track median)
        hop = 512
        rms = librosa.feature.rms(y=y, hop_length=hop)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
        med = float(np.median(rms))
        full = next((b for b in bt if b > 0.5 and np.mean(rms[(times >= b) & (times < b + 2 * T)]) >= 0.7 * med), bt[0])
        m["bpm"] = round(60 / T, 2)
        m["mulai"] = round(float(full), 3)
        print(f"{m['id']}: {m['bpm']} BPM, mulai {m['mulai']} s")
    save_json(os.path.join(DATA, "musik.json"), rows)
    con = connect()
    for m in rows:
        upsert(con, "musik", m)
    con.commit()


if __name__ == "__main__":
    a = sys.argv[1:] or ["list"]
    {"init": lambda: cmd_init(), "import": lambda: cmd_import(), "validate": lambda: cmd_validate(a[1:]),
     "list": lambda: cmd_list(), "export": lambda: cmd_export(a[1]), "musik": lambda: cmd_musik()}[a[0]]()
