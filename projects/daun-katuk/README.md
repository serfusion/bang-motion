# Manfaat Daun Katuk — video edukasi 60 detik (9:16)

Konten video pendek bahasa Indonesia dengan **voice-over + subtitle per kata** dan **hook di 3 detik
pertama** ("Daun ini, vitamin C-nya tiga kali lipat jeruk!"). Dibuat dengan skill **Bang Motion**
(repo ini: HTML + GSAP, rig kamera kolase, hukum anti-PPT) dan **video-shotcraft** (kartu shot,
aturan estetika, pustaka audio, review independen).

| Berkas | Isi |
|---|---|
| `out/daun-katuk.mp4` | video final 1080×1920, 30 fps, 60 dtk — VO + SFX + musik |
| `out/daun-katuk-tanpa-bgm.mp4` | versi tanpa musik (VO + SFX) untuk memakai musik dari platform |
| `out/daun-katuk.id.srt` | subtitle bahasa Indonesia terpisah (YouTube, editor video) |
| `index.html` | sumber animasi — buka langsung (klik dua kali), autoplay + loop; `?debug=1` untuk scrub |
| `vo-script.md` | naskah VO per adegan + tabel angka gizi |
| `DESIGN.md` | style brief, kartu shot yang dipakai, rundown per detik |

## Fakta & sumber

Angka gizi per 100 g diambil dari **Data Komposisi Pangan Indonesia, Kementerian Kesehatan RI**
(https://www.panganku.org): daun katuk segar (kode DR0035) vitamin C 164 mg, kalsium 233 mg,
karotenoid total 10.020 µg, besi 3,0 mg; daun katuk rebus (DP0005) vitamin C 66 mg; jeruk manis
(ER0039) vitamin C 49 mg; susu sapi segar (JR0006) kalsium 143 mg; wortel segar (DR0166)
karotenoid total 11.046 µg; bayam segar (DR0008) besi 3,0 mg.

- **Pelancar ASI** — penggunaan turun-temurun; bukti ilmiahnya menjanjikan tetapi belum seragam,
  sehingga naskah memakai kalimat "beberapa penelitian hasilnya menjanjikan". Contoh: uji klinis
  ekstrak daun katuk vs plasebo (Sa'roni dkk., 2004) melaporkan peningkatan produksi ASI;
  [Handayani dkk., 2022 — Global Medical & Health Communication](https://ejournal.unisba.ac.id/index.php/gmhc/article/view/8948)
  tidak menemukan perbedaan bermakna terhadap produk pembanding.
- **Peringatan jus mentah** — konsumsi jus daun katuk mentah berlebihan untuk diet di Taiwan (1995)
  dikaitkan dengan *bronchiolitis obliterans*; ringkasan:
  [Hospital Authority Hong Kong — toxic plant database](https://www3.ha.org.hk/toxicplant/en/sauropus_androgynus.html),
  [ulasan di PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4564651/).
- Penutup video memuat sumber gizi dan disclaimer "Edukasi umum, bukan pengganti saran tenaga kesehatan".

## Kredit aset

- Foto daun katuk: **Forest & Kim Starr**, CC BY 3.0 — [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Starr-120606-7012-Sauropus_androgynus-flowers_and_leaves-Kahanu_Gardens_Veggie_Garden_Hana-Maui_(24514001724).jpg) (dipotong; kredit tampil di layar).
- Ilustrasi (tangkai katuk, ibu & bayi, jeruk, tulang, mata, panci, dll.): digambar dengan SVG di `index.html`.
- Musik & efek suara: Mixkit (free license), dari pustaka video-shotcraft — daftar per berkas di `assets/audio/ATTRIBUTION.md`.
- Voice-over: TTS neural Microsoft Edge (`id-ID-ArdiNeural`). Ganti dengan suara sendiri bila perlu — lihat `vo-script.md`.
- Font: Fraunces, Plus Jakarta Sans, Kalam (Google Fonts, SIL OFL).

## Membangun ulang

```
python3 tools/tts.py                 # VO per adegan + waktu kata (edge-tts)
python3 tools/layout.py              # cut adegan di ketukan musik, halaman subtitle -> timeline.json
python3 tools/inject.py              # timeline.json -> index.html
node tools/dump-sfx.mjs              # tabel pin SFX dari halaman -> sfx.json
python3 tools/mix.py                 # VO + SFX + BGM (edit di batas bar, ducking) -> build/mix*.wav
node tools/export.mjs                # render frame-demi-frame -> build/video.mp4
bash tools/finalize.sh               # encode + mux -> out/*.mp4 + subtitle .srt
```

Butuh Python 3 (`edge-tts`, `numpy`), Node (`puppeteer`), dan ffmpeg. Di mesin tanpa Chrome bawaan
puppeteer, set `PUPPETEER_EXECUTABLE_PATH` ke Chrome/Chromium lokal.
