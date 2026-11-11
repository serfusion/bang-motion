"""Content database (SQLite) for the video engine.

  python3 tools/db.py init                    create db/konten.db from db/schema.sql (drops the old file)
  python3 tools/db.py import                  load db/data/*.json + db/data/episode/*.json (upsert; API keys untouched)
  python3 tools/db.py dump                    write the database back to db/data JSON (never the API keys)
  python3 tools/db.py validate [ID ...]       check scenes, cues, scripts, icons, facts for both languages
  python3 tools/db.py list                    episodes with format and status
  python3 tools/db.py export ID [id|en ...]   write episodes/ID/episode.json (validated for the given languages)
  python3 tools/db.py musik                   analyse BPM / first full beat of tracks without them
  python3 tools/db.py kunci tambah LABEL      add an ElevenLabs key (read from stdin, never echoed)
  python3 tools/db.py kunci daftar|tes|hapus ID

The JSON files under db/data are the version-controlled seed; the SQLite file is what the web panel (panel/app.py)
reads and writes. `dump` brings panel edits back into JSON.
"""
import glob, json, os, sqlite3, sys
from common import (DATA, DBFILE, PROJ, ENGINE, SCENE_TYPES, FORMAT_SCENES, LANGS, ep_dir, load_json, save_json,
                    parse_vo, merged_param, script, icon_names, icon_svg)

TABLES = [("kategori", "kategori.json"), ("sumber", "sumber.json"), ("suara", "suara.json"), ("musik", "musik.json"),
          ("aset", "aset.json"), ("fakta", "fakta.json")]
JSON_COLS = {"pengaturan", "param", "param_en"}


# columns added after the first release: (table, column, type) -> ALTER TABLE on older database files
MIGRATE = [("tugas", "sampai", "TEXT"), ("kunci_api", "paket", "TEXT"), ("episode", "watermark", "INTEGER")]
# watermark: nama channel/akun + maskot di pojok kanan atas, sedikit pudar (pengaturan panel -> Watermark)
WM_BAWAAN = {"watermark_nama": "", "watermark_gambar": "", "watermark_atas_cm": "0.75", "watermark_opacity": "60",
             "watermark_bawaan": "1"}
WM_PX_CM = 150             # video 1080 px selebar layar HP (±7 cm): 1 cm ≈ 150 px


def pengaturan(con):
    try:
        d = {r[0]: r[1] for r in con.execute("SELECT kunci, nilai FROM pengaturan")}
    except sqlite3.OperationalError:
        d = {}
    return {**WM_BAWAAN, **{k: v for k, v in d.items() if v is not None}}


def watermark_cfg(con, ep):
    """Watermark yang dipakai episode ini (None = tanpa). Kolom episode.watermark kosong = ikut bawaan panel."""
    s = pengaturan(con)
    on = ep.get("watermark")
    if not (s["watermark_bawaan"] == "1" if on is None else bool(on)):
        return None

    def num(k, lo, hi):
        try:
            v = float(str(s[k]).replace(",", ".") or WM_BAWAAN[k])
        except ValueError:
            v = float(WM_BAWAAN[k])
        return min(hi, max(lo, v))
    gambar = s["watermark_gambar"] or "maskot"          # "maskot" = Si Katuk, "tanpa" = teks saja, selain itu id aset
    teks = (s["watermark_nama"] or "").strip()[:40]
    if not teks and gambar == "tanpa":
        return None
    return {"teks": teks, "gambar": gambar, "atas": round(num("watermark_atas_cm", 0, 12) * WM_PX_CM),
            "opacity": round(num("watermark_opacity", 15, 100) / 100, 2)}


def connect():
    fresh = not os.path.exists(DBFILE)
    if fresh:
        init_schema()
    con = sqlite3.connect(DBFILE, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    if not fresh:
        for table, col, typ in MIGRATE:
            have = cols(con, table)
            if have and col not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
                con.commit()
    return con


def init_schema():
    """Create every table that does not exist yet (CREATE TABLE IF NOT EXISTS: safe on an existing file)."""
    con = sqlite3.connect(DBFILE)
    con.executescript(open(os.path.join(PROJ, "db", "schema.sql"), encoding="utf-8").read())
    con.commit()
    con.close()


def cmd_init():
    if os.path.exists(DBFILE):
        os.remove(DBFILE)
    init_schema()
    print("created", os.path.relpath(DBFILE, PROJ))


def cols(con, table):
    return [c[1] for c in con.execute(f"PRAGMA table_info({table})")]


def pkey(con, table):
    return [c[1] for c in sorted(con.execute(f"PRAGMA table_info({table})"), key=lambda c: c[5]) if c[5]]


def upsert(con, table, row):
    """Insert or update in place. (Not INSERT OR REPLACE: that deletes the old row first, and with foreign keys on
    the delete would cascade, e.g. wiping an episode's renders and queued tasks every time it is saved.)"""
    vals = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in row.items() if k in cols(con, table)}
    keys = pkey(con, table)
    sql = f"INSERT INTO {table} ({','.join(vals)}) VALUES ({','.join('?' * len(vals))})"
    upd = [k for k in vals if k not in keys]
    if keys:
        sql += f" ON CONFLICT({','.join(keys)}) DO " + ("UPDATE SET " + ",".join(f"{k}=excluded.{k}" for k in upd) if upd else "NOTHING")
    con.execute(sql, list(vals.values()))


def full_row(con, table, row, keep=("dibuat",)):
    """Every column of the table: a key missing from the JSON clears the column (so JSON -> database is exact),
    except columns in `keep` (e.g. the creation time, which the JSON never carries)."""
    return {c: row.get(c) for c in cols(con, table) if c in row or c not in keep}


def save_episode(con, ep):
    """Write one episode (same shape as db/data/episode/*.json) with its scenes and fact links."""
    row = full_row(con, "episode", ep)
    row["format"], row["status"] = row.get("format") or "tebakan", row.get("status") or "draf"
    upsert(con, "episode", row)
    con.execute("DELETE FROM adegan WHERE episode_id=?", (ep["id"],))
    con.execute("DELETE FROM episode_fakta WHERE episode_id=?", (ep["id"],))
    for i, sc in enumerate(ep.get("adegan", [])):
        upsert(con, "adegan", {"episode_id": ep["id"], "urutan": i + 1, "jenis": sc["jenis"], "vo": sc.get("vo", ""),
                               "vo_en": sc.get("vo_en", ""), "param": sc.get("param") or {}, "param_en": sc.get("param_en") or {}})
    for fid in ep.get("fakta", []):
        fid = fid["id"] if isinstance(fid, dict) else fid
        con.execute("INSERT OR IGNORE INTO episode_fakta VALUES (?,?)", (ep["id"], fid))


def cmd_import():
    con = connect()
    for table, fname in TABLES:
        for row in load_json(os.path.join(DATA, fname)):
            upsert(con, table, full_row(con, table, row))
    n = 0
    for f in sorted(glob.glob(os.path.join(DATA, "episode", "*.json"))):
        save_episode(con, load_json(f))
        n += 1
    con.commit()
    print(f"imported {n} episodes into {os.path.relpath(DBFILE, PROJ)}")


def row_dict(r):
    d = dict(r)
    for k in JSON_COLS & d.keys():
        d[k] = json.loads(d[k] or "{}")
    return d


def cmd_dump():
    con = connect()
    for table, fname in TABLES:
        rows = [{k: v for k, v in row_dict(r).items() if v is not None} for r in con.execute(f"SELECT * FROM {table} ORDER BY rowid")]
        save_json(os.path.join(DATA, fname), rows)
    os.makedirs(os.path.join(DATA, "episode"), exist_ok=True)
    keep = set()
    for r in con.execute("SELECT id FROM episode ORDER BY id"):
        ep = load_episode(con, r["id"], full=False)
        save_json(os.path.join(DATA, "episode", r["id"] + ".json"), ep)
        keep.add(r["id"] + ".json")
    gone = [f for f in glob.glob(os.path.join(DATA, "episode", "*.json")) if os.path.basename(f) not in keep]
    for f in gone:                       # episodes deleted in the panel
        os.remove(f)
    print(f"dumped {len(keep)} episodes to db/data, removed {len(gone)} (API keys are never written)")


def load_episode(con, eid, full=True):
    """Episode joined with scenes (+ facts, sources, voices, music, assets when full)."""
    r = con.execute("SELECT * FROM episode WHERE id=?", (eid,)).fetchone()
    if not r:
        sys.exit(f"episode not found: {eid}")
    ep = {k: v for k, v in dict(r).items() if v is not None and k != "dibuat"}
    ep["adegan"] = [{"jenis": a["jenis"], "vo": a["vo"], "vo_en": a["vo_en"] or "", "param": json.loads(a["param"] or "{}"),
                     "param_en": json.loads(a["param_en"] or "{}")}
                    for a in con.execute("SELECT * FROM adegan WHERE episode_id=? ORDER BY urutan", (eid,))]
    fids = [f["fakta_id"] for f in con.execute("SELECT fakta_id FROM episode_fakta WHERE episode_id=? ORDER BY fakta_id", (eid,))]
    if not full:
        ep["fakta"] = fids
        return ep
    ep["fakta"] = [dict(f) for f in con.execute(f"SELECT * FROM fakta WHERE id IN ({','.join('?' * len(fids))}) ORDER BY id", fids)]
    sids = sorted({f["sumber_id"] for f in ep["fakta"] if f["sumber_id"]})
    ep["sumber"] = [dict(s) for s in con.execute(f"SELECT * FROM sumber WHERE id IN ({','.join('?' * len(sids))})", sids)]
    for k, col in (("suara", "suara_id"), ("suara_en", "suara_en_id")):
        v = con.execute("SELECT * FROM suara WHERE id=?", (ep.get(col),)).fetchone()
        ep[k] = row_dict(v) if v else None
    m = con.execute("SELECT * FROM musik WHERE id=?", (ep.get("musik_id"),)).fetchone()
    ep["musik"] = dict(m) if m else None
    ep["aset"] = {a["id"]: dict(a) for a in con.execute("SELECT * FROM aset")}
    return ep


# required cues per scene type, written as {name} in the script of each language
NEED = {"jawaban": ["jawab"]}
ITEM_CUES = {"langkah": ("item", "l"), "banding": ("item", "b"), "catatan": ("kartu", "k")}


def check_scene(i, sc, prev, fmt, lang, errs, warns):
    j, p = sc["jenis"], merged_param(sc, lang)
    tag = f"[{lang}] adegan {i + 1} ({j})"
    if j not in SCENE_TYPES:
        errs.append(f"{tag}: jenis tidak dikenal"); return
    if j not in FORMAT_SCENES.get(fmt, SCENE_TYPES):
        errs.append(f"{tag}: jenis '{j}' tidak dipakai format '{fmt}' (boleh: {', '.join(FORMAT_SCENES[fmt])})")
    text = script(sc, lang)
    if not text.strip():
        errs.append(f"{tag}: naskah {'Inggris (vo_en)' if lang == 'en' else 'Indonesia (vo)'} kosong"); return
    try:
        _, words = parse_vo(text)
    except ValueError as e:
        errs.append(f"{tag}: {e}"); return
    cues = [c for w in words for c in w["cues"]]
    need = lambda k: p.get(k) not in (None, "", []) or errs.append(f"{tag}: param '{k}' wajib")
    for c in NEED.get(j, []):
        if c not in cues:
            errs.append(f"{tag}: butuh isyarat {{{c}}} di naskah")
    if j == "kuis":
        need("judul"); need("pilihan")
        if not 2 <= len(p.get("pilihan", [])) <= 3:
            errs.append(f"{tag}: pilihan harus 2-3")
        if not 0 <= p.get("jawaban", -1) < len(p.get("pilihan", [])):
            errs.append(f"{tag}: 'jawaban' harus indeks pilihan")
    if j == "jawaban":
        if not prev or prev["jenis"] != "kuis":
            errs.append(f"{tag}: harus tepat setelah adegan kuis")
        if p.get("label") and prev and len(p["label"]) != len(merged_param(prev, lang).get("pilihan", [])):
            errs.append(f"{tag}: 'label' harus sejumlah pilihan kuis")
    if j in ITEM_CUES:
        key, pre = ITEM_CUES[j]
        need(key)
        lim = {"langkah": (2, 4), "banding": (2, 3), "catatan": (1, 4)}[j]
        if not lim[0] <= len(p.get(key, [])) <= lim[1]:
            errs.append(f"{tag}: {key} harus {lim[0]}-{lim[1]}")
        miss = [f"{pre}{k}" for k in range(len(p.get(key, []))) if f"{pre}{k}" not in cues]
        if miss:
            warns.append(f"{tag}: isyarat {miss} tidak ada -> muncul merata sepanjang adegan")
    if j == "twist":
        need("headline")
    if j == "cta":
        need("judul")
    if j == "pembuka":
        need("judul")
    if j == "ibarat":
        need("kutipan")
    if j == "tanya":
        need("pertanyaan")
    if p.get("teaser") and "teaser" not in cues:
        errs.append(f"{tag}: 'teaser' butuh isyarat {{teaser}}")


def validate(ep, langs=LANGS):
    errs, warns = [], []
    fmt = ep.get("format", "tebakan")
    for lang in langs:
        if lang == "en" and not any((sc.get("vo_en") or "").strip() for sc in ep["adegan"]):
            warns.append("[en] naskah Inggris belum diisi: video berbahasa Inggris belum bisa dibuat")
            continue
        prev = None
        for i, sc in enumerate(ep["adegan"]):
            check_scene(i, sc, prev, fmt, lang, errs, warns)
            prev = sc
    first, last = (ep["adegan"][0]["jenis"], ep["adegan"][-1]["jenis"]) if ep["adegan"] else (None, None)
    if fmt == "tebakan" and first != "kuis":
        warns.append("format tebakan sebaiknya dibuka dengan adegan kuis")
    if fmt == "fakta" and first != "pembuka":
        warns.append("format fakta sebaiknya dibuka dengan adegan pembuka")
    if last not in ("cta", "tanya"):
        warns.append("adegan terakhir sebaiknya cta atau tanya")
    for name in icon_names(ep):
        if not icon_svg(name, ep.get("aset", {})):
            errs.append(f"ikon tidak ditemukan: {name}")
    for lang in langs:
        v = ep.get("suara_en" if lang == "en" else "suara")
        if not v and (lang == "id" or any((sc.get("vo_en") or "").strip() for sc in ep["adegan"])):
            errs.append(f"[{lang}] suara untuk bahasa ini belum dipilih")
    if not ep.get("musik") or not ep["musik"].get("bpm"):
        errs.append("musik belum dipilih atau belum dianalisis (python3 tools/db.py musik)")
    return errs, warns


def cmd_validate(ids):
    con = connect()
    ids = ids or [r["id"] for r in con.execute("SELECT id FROM episode ORDER BY id")]
    bad = 0
    for eid in ids:
        errs, warns = validate(load_episode(con, eid))
        print(f"{eid}: {'OK' if not errs else str(len(errs)) + ' galat'}" + (f", {len(warns)} peringatan" if warns else ""))
        for e in errs:
            print("  x", e)
        for w in warns:
            print("  !", w)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


def cmd_list():
    con = connect()
    for r in con.execute("SELECT e.id, e.format, e.status, e.judul, COUNT(a.urutan) n FROM episode e LEFT JOIN adegan a "
                         "ON a.episode_id=e.id GROUP BY e.id ORDER BY e.id"):
        print(f"{r['id']:<24} {r['format']:<8} {r['status']:<9} {r['n']} adegan  {r['judul']}")


def cmd_export(eid, langs=LANGS):
    con = connect()
    ep = load_episode(con, eid)
    errs, warns = validate(ep, langs)
    if errs:
        sys.exit("validasi gagal:\n  " + "\n  ".join(errs))
    ep["wm"] = watermark_cfg(con, ep)
    if ep["wm"] and not ep["wm"]["teks"]:
        print("peringatan: watermark aktif tetapi nama channel belum diisi (panel -> Watermark): hanya gambar yang tampil")
    out = ep_dir(eid, "episode.json")
    save_json(out, ep)
    print("exported", os.path.relpath(out, PROJ))


def cmd_musik():
    import librosa, numpy as np
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM musik")]
    for m in rows:
        if m.get("bpm") and m.get("mulai") is not None:
            continue
        path = os.path.join(ENGINE, "audio", "bgm", m["berkas"])
        y, sr = librosa.load(path, sr=22050, mono=True, duration=120)
        _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
        bt = np.asarray(beats)
        T = float(np.median(np.diff(bt)))
        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
        med = float(np.median(rms))
        full = next((b for b in bt if b > 0.5 and np.mean(rms[(times >= b) & (times < b + 2 * T)]) >= 0.7 * med), bt[0])
        m["bpm"], m["mulai"] = round(60 / T, 2), round(float(full), 3)
        con.execute("UPDATE musik SET bpm=?, mulai=? WHERE id=?", (m["bpm"], m["mulai"], m["id"]))
        print(f"{m['id']}: {m['bpm']} BPM, mulai {m['mulai']} s")
    con.commit()


def cmd_kunci(a):
    import elevenlabs
    con = connect()
    if a[0] == "tambah":
        key = sys.stdin.readline().strip()
        if not key:
            sys.exit("kunci kosong")
        n = con.execute("SELECT COALESCE(MAX(urutan),0)+1 FROM kunci_api").fetchone()[0]
        con.execute("INSERT INTO kunci_api (label, kunci, urutan) VALUES (?,?,?)", (a[1] if len(a) > 1 else f"kunci {n}", key, n))
        con.commit()
        print("kunci disimpan (urutan", n, ")")
    elif a[0] == "hapus":
        con.execute("DELETE FROM kunci_api WHERE id=?", (int(a[1]),)); con.commit()
    elif a[0] == "tes":
        for r in con.execute("SELECT id, kunci FROM kunci_api WHERE aktif=1 ORDER BY urutan").fetchall():
            print(r["id"], *elevenlabs.check(r["id"], r["kunci"]))
    for r in con.execute("SELECT * FROM kunci_api ORDER BY urutan, id"):
        k = r["kunci"]
        print(f"{r['id']:>3} #{r['urutan']} {r['label'] or '':<14} {k[:4]}…{k[-4:]}  {r['status']}  sisa={r['sisa']}  {r['catatan'] or ''}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["list"]
    {"init": lambda: cmd_init(), "import": lambda: cmd_import(), "dump": lambda: cmd_dump(),
     "validate": lambda: cmd_validate(a[1:]), "list": lambda: cmd_list(),
     "export": lambda: cmd_export(a[1], a[2:] or LANGS), "musik": lambda: cmd_musik(),
     "kunci": lambda: cmd_kunci(a[1:] or ["daftar"])}[a[0]]()
