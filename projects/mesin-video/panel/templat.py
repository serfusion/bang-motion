"""Scene templates for the episode editor: what each scene type shows, its cues and a starting example
(Indonesian + English). The examples are only a starting point; every value can be edited in the panel."""

FORMATS = {
    "tebakan": {"nama": "Tebakan", "ket": "Kuis cepat: hook pertanyaan, hitung mundur, jawaban, penjelasan, twist, ajakan. "
                "Tempo cepat, maskot bereaksi.", "kerangka": ["kuis", "jawaban", "langkah", "cta"], "musik": "comical"},
    "fakta": {"nama": "Fakta", "ket": "Penjelasan santai bergaya catatan dokumenter: kartu angka bertumpuk, ilustrasi, "
              "analogi sehari-hari, pertanyaan penutup. Tempo pelan dengan jeda wajar.",
              "kerangka": ["pembuka", "catatan", "ibarat", "tanya"], "musik": "gummies"},
}

SCENES = {
    "kuis": {
        "nama": "Kuis (hook)",
        "ket": "Pertanyaan + 2–3 pilihan yang muncul saat disebut. Harus diikuti adegan jawaban.",
        "isyarat": "{p0} {p1} {p2} tepat sebelum nama pilihan",
        "param": "judul, pilihan [{label, ikon}], jawaban (indeks mulai 0), ikon (opsional), stiker (opsional)",
        "vo": "[curious] Mana yang lebih tinggi proteinnya? | {p0}Tempe... | atau {p1}telur?",
        "vo_en": "[curious] Which one has more protein? | {p0}Tempeh... | or {p1}egg?",
        "contoh": {"judul": "Siapa juara protein?", "pilihan": [{"label": "Tempe", "ikon": "tempe"}, {"label": "Telur", "ikon": "egg"}], "jawaban": 0},
        "contoh_en": {"judul": "Protein champion?", "stiker": "QUIZ!", "pilihan": [{"label": "Tempeh", "ikon": "tempe"}, {"label": "Egg", "ikon": "egg"}]},
    },
    "jawaban": {
        "nama": "Jawaban",
        "ket": "Hitung mundur 3-2-1, sorotan, lalu jawaban + angka. 'teaser' membuka rasa penasaran sampai akhir video.",
        "isyarat": "{jawab} wajib (kata jawaban); {label} angka; {besar} teks besar; {teaser}",
        "param": "stempel, label [angka per pilihan], catatan, besar, teaser",
        "vo": "[excited] Jawabannya... | {jawab}TEMPE! | [excited] Per <100 g=seratus gram>, | {label}tempe <20 g=dua puluh gram> protein! | "
              "[whispers] Tapi ada jebakannya... | {teaser}di akhir video.",
        "vo_en": "[excited] The answer... | {jawab}TEMPEH! | [excited] Per <100 g=hundred grams>, | {label}tempeh has <20 g=twenty grams> of protein! | "
                 "[whispers] But there's a trap... | {teaser}at the end of the video.",
        "contoh": {"stempel": "MENANG!", "label": ["20,3 g", "12,6 g"], "catatan": "protein · per 100 g", "teaser": "di akhir video!"},
        "contoh_en": {"stempel": "WINNER!", "label": ["20.3 g", "12.6 g"], "catatan": "protein · per 100 g", "teaser": "at the end!"},
    },
    "langkah": {
        "nama": "Langkah / rantai",
        "ket": "2–4 langkah. gaya 'rantai' = sebab-akibat berpanah, 'daftar' = tips bernomor.",
        "isyarat": "{l0} {l1} {l2} {l3}",
        "param": "judul, gaya (rantai|daftar), item [{ikon, teks, sub}]",
        "vo": "[curious] Kok bisa? | {l0}Kedelai kaya protein. | {l1}Lalu difermentasi... | [excited] {l2}jadi mudah dicerna!",
        "vo_en": "[curious] How? | {l0}Soybeans are rich in protein. | {l1}Then they're fermented... | [excited] {l2}so it's easy to digest!",
        "contoh": {"judul": "Rahasianya", "gaya": "rantai", "item": [{"ikon": "kedelai", "teks": "kedelai", "sub": "kaya protein"},
                   {"ikon": "microbe", "teks": "fermentasi", "sub": "jamur Rhizopus"}, {"ikon": "flexed-biceps", "teks": "mudah dicerna", "sub": ""}]},
        "contoh_en": {"judul": "The secret", "item": [{"ikon": "kedelai", "teks": "soybeans", "sub": "protein-rich"},
                      {"ikon": "microbe", "teks": "fermentation", "sub": "Rhizopus mould"}, {"ikon": "flexed-biceps", "teks": "easy to digest", "sub": ""}]},
    },
    "banding": {
        "nama": "Banding (grafik)",
        "ket": "2–3 batang yang terisi saat angkanya disebut. 'juara': true menandai pemenang; tema 'kejutan' = halaman kuning.",
        "isyarat": "{b0} {b1} {b2}",
        "param": "judul, sub, tema, item [{label, ikon, nilai (angka), teks, juara}]",
        "vo": "[mischievously] Tapi per porsi? | {b0}Sebutir telur <7,6 g=tujuh koma enam gram>. | {b1}Dua potong tempe <10,2 g=sepuluh koma dua gram>!",
        "vo_en": "[mischievously] But per serving? | {b0}One egg: <7.6 g=seven point six grams>. | {b1}Two slices of tempeh: <10.2 g=ten point two grams>!",
        "contoh": {"judul": "Per porsi", "sub": "protein", "item": [{"label": "1 butir telur", "ikon": "egg", "nilai": 7.6, "teks": "7,6 g"},
                   {"label": "2 potong tempe", "ikon": "tempe-potong", "nilai": 10.2, "teks": "10,2 g", "juara": True}]},
        "contoh_en": {"judul": "Per serving", "sub": "protein", "item": [{"label": "1 egg", "ikon": "egg", "nilai": 7.6, "teks": "7.6 g"},
                      {"label": "2 slices of tempeh", "ikon": "tempe-potong", "nilai": 10.2, "teks": "10.2 g", "juara": True}]},
    },
    "twist": {
        "nama": "Twist / kejutan",
        "ket": "Kliping berita dengan judul tertutup stiker yang dirobek. nada 'peringatan' = gelap, 'kejutan' = biru. "
               "Kata di antara *bintang* diberi stabilo.",
        "isyarat": "{k} kartu berita, {i0} {i1} baris, {angka}, {stabilo}",
        "param": "nada, judul, kicker, headline, baris [{ikon, teks, nilai, ok}], angka {teks, sub}",
        "vo": "[serious] Jadi siapa pelakunya? | {k}GULA! | {i0}Air es tawar: nol kalori. | {i1}Es teh manis: | sekitar <100 kalori=seratus kalori>!",
        "vo_en": "[serious] So who's the culprit? | {k}SUGAR! | {i0}Plain iced water: zero calories. | {i1}Sweet iced tea: | about <100 calories=a hundred calories>!",
        "contoh": {"nada": "peringatan", "judul": "Pelakunya!", "kicker": "SUMBER · TAHUN", "headline": "Bukan esnya, tapi *GULANYA*",
                   "baris": [{"ikon": "ice", "teks": "air es tawar", "nilai": "0 kkal", "ok": True},
                             {"ikon": "cup-with-straw", "teks": "es teh manis", "nilai": "±100 kkal", "ok": False}]},
        "contoh_en": {"judul": "The culprit!", "kicker": "SOURCE · YEAR", "headline": "Not the ice, it's the *SUGAR*",
                      "baris": [{"ikon": "ice", "teks": "plain iced water", "nilai": "0 kcal", "ok": True},
                                {"ikon": "cup-with-straw", "teks": "sweet iced tea", "nilai": "±100 kcal", "ok": False}]},
    },
    "cta": {
        "nama": "Ajakan (penutup tebakan)",
        "ket": "Judul penutup, tagline, ajakan berbagi, kredit sumber + suara otomatis.",
        "isyarat": "—",
        "param": "judul, ikon, tagline [..], ajakan, ikon_ajakan",
        "vo": "[playful] Tempe: murah, asli Indonesia! | Kirim ke temanmu | yang suka meremehkan tempe!",
        "vo_en": "[playful] Tempeh: cheap and truly Indonesian! | Send this to a friend | who looks down on tempeh!",
        "contoh": {"judul": "Tempe juara!", "ikon": "tempe", "tagline": ["murah", "asli Indonesia"], "ajakan": "kirim ke temanmu"},
        "contoh_en": {"judul": "Tempeh wins!", "tagline": ["cheap", "from Indonesia"], "ajakan": "send to a friend"},
    },
    "pembuka": {
        "nama": "Pembuka (fakta)",
        "ket": "Kalimat pembuka besar di atas ilustrasi yang digelapkan + angka sorotan merah.",
        "isyarat": "{b0} {b1} baris judul, {sorot} angka sorotan",
        "param": "judul [baris..], sorot, kicker, ilustrasi {ikon: [utama, satelit..]} atau {gambar: id aset foto}",
        "vo": "[serious] {b0}<11=Sebelas> hari. | {b1}Tanpa tidur. | Ini {sorot}rekor anak SMA, | tahun <1964=seribu sembilan ratus enam puluh empat>.",
        "vo_en": "[serious] {b0}<11=Eleven> days. | {b1}No sleep. | This is {sorot}a high school kid's record, | back in <1964=nineteen sixty-four>.",
        "contoh": {"ilustrasi": {"ikon": ["alarm-clock", "sleeping-face", "spiral-calendar"]}, "judul": ["11 hari.", "Tanpa tidur."],
                   "sorot": "264 jam", "kicker": "REKOR 1964"},
        "contoh_en": {"judul": ["11 days.", "No sleep."], "sorot": "264 hours", "kicker": "RECORD · 1964"},
    },
    "catatan": {
        "nama": "Catatan (kartu angka)",
        "ket": "1–4 kartu (kicker kecil + nilai besar) bertumpuk saat disebut, ilustrasi besar di bawahnya. "
               "warna 'merah' untuk angka penting; {teks} untuk catatan pendek.",
        "isyarat": "{k0} {k1} {k2} {k3}",
        "param": "kartu [{kicker, nilai, warna} | {teks}], ilustrasi {ikon: [..]} atau {gambar: id aset foto}",
        "vo": "[warm] Namanya {k0}Randy Gardner, | <17 tahun=tujuh belas tahun>. | Ini {k1}proyek lomba sains sekolahnya.",
        "vo_en": "[warm] His name: {k0}Randy Gardner, | <17=seventeen>. | It was {k1}his school science fair project.",
        "contoh": {"ilustrasi": {"ikon": ["boy", "clipboard", "microscope"]},
                   "kartu": [{"kicker": "SIAPA", "nilai": "Randy Gardner, 17"}, {"kicker": "UNTUK APA", "nilai": "lomba sains sekolah"}]},
        "contoh_en": {"kartu": [{"kicker": "WHO", "nilai": "Randy Gardner, 17"}, {"kicker": "WHY", "nilai": "school science fair"}]},
    },
    "ibarat": {
        "nama": "Ibarat (analogi)",
        "ket": "Analogi sehari-hari dalam kartu kutipan + 1–3 catatan pendek.",
        "isyarat": "{kutip} kutipan, {k0} {k1} catatan",
        "param": "kutipan, kartu [{teks, warna}], ilustrasi",
        "vo": "[warm] {kutip}Ibarat ponsel yang baterainya tinggal <5%=lima persen>. | [playful] {k0}Bisa dipakai? | Bisa. | {k1}Bisa diandalkan? | Nanti dulu.",
        "vo_en": "[warm] {kutip}It's like a phone at <5%=five percent> battery. | [playful] {k0}Can you use it? | Sure. | {k1}Can you rely on it? | Not really.",
        "contoh": {"ilustrasi": {"ikon": ["low-battery", "mobile-phone"]}, "kutipan": "ibarat ponsel dengan baterai 5%",
                   "kartu": [{"teks": "Bisa dipakai? Bisa."}, {"teks": "Diandalkan? Nanti dulu.", "warna": "merah"}]},
        "contoh_en": {"kutipan": "like a phone at 5% battery", "kartu": [{"teks": "Usable? Sure."}, {"teks": "Reliable? Not really.", "warna": "merah"}]},
    },
    "tanya": {
        "nama": "Tanya (penutup fakta)",
        "ket": "Fakta terakhir, pertanyaan untuk penonton, dua pilihan, ajakan berkomentar, kredit sumber + suara otomatis.",
        "isyarat": "{k0} kartu, {tanya} pertanyaan, {pilih} pilihan",
        "param": "kartu [..], pertanyaan, pilihan [2], ajakan",
        "vo": "[warm] {k0}Orang dewasa butuh minimal <7 jam=tujuh jam> tidur. | [curious] {tanya}Menurutmu, | tidurmu sudah cukup, | {pilih}atau masih kurang? | Tulis di komentar.",
        "vo_en": "[warm] {k0}Adults need at least <7 hours=seven hours> of sleep. | [curious] {tanya}So, | are you getting enough, | {pilih}or not quite? | Tell us in the comments.",
        "contoh": {"kartu": [{"kicker": "ORANG DEWASA", "nilai": "≥ 7 jam semalam"}], "pertanyaan": "Tidurmu cukup?",
                   "pilihan": ["Cukup", "Kurang"], "ajakan": "tulis di komentar"},
        "contoh_en": {"kartu": [{"kicker": "ADULTS", "nilai": "≥ 7 hours a night"}], "pertanyaan": "Enough sleep?",
                      "pilihan": ["Enough", "Not enough"], "ajakan": "tell us in the comments"},
    },
}

TAGS = ["curious", "excited", "whispers", "surprised", "laughs", "serious", "dramatically", "mischievously", "playful", "warm"]

SYNTAX = [
    ("[tag]", "arahan intonasi ElevenLabs v3: " + ", ".join(TAGS)),
    ("|", "batas halaman subtitle"),
    ("{nama}", "isyarat waktu visual, ditulis tepat sebelum kata (lihat tiap jenis adegan)"),
    ("<tampil=ucapan>", "suara membaca 'ucapan', subtitle menampilkan 'tampil' — untuk angka: <1964=seribu sembilan ratus enam puluh empat>"),
    ("kata...", "jeda tegang; '?' di tengah adegan = jeda tanya"),
]
