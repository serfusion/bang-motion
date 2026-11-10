/* Editor adegan: kartu per adegan (naskah ID/EN + param JSON), pratinjau subtitle, cek isyarat, cari ikon. */
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const J = id => JSON.parse(document.getElementById(id).textContent);
  const TPL = J('d-templat'), BYFMT = J('d-format'), FMTS = J('d-formats');
  const form = $('#ep-form'), list = $('#adegan'), fmtSel = $('#format'), addSel = $('#add-jenis');
  let dirty = false;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  const pretty = v => (v && Object.keys(v).length) ? JSON.stringify(v, null, 1) : '';

  /* ---------- naskah: pratinjau subtitle, jumlah karakter TTS, isyarat ---------- */
  const shown = vo => vo.replace(/<([^=>]*)=([^>]*)>/g, '$1').replace(/\[[^\]]*\]/g, '').replace(/\{\w+\}/g, '');
  const spoken = vo => vo.replace(/<([^=>]*)=([^>]*)>/g, '$2').replace(/\{\w+\}/g, '').replace(/\|/g, ' ').replace(/\s+/g, ' ').trim();
  const cuesIn = vo => [...vo.matchAll(/\{(\w+)\}/g)].map(m => m[1]);
  const len = a => Array.isArray(a) ? a.length : 0;
  function merged(p, pe) { const o = { ...p }; for (const k in pe) o[k] = (pe[k] && typeof pe[k] === 'object' && !Array.isArray(pe[k]) && typeof o[k] === 'object') ? { ...o[k], ...pe[k] } : pe[k]; return o; }
  function expected(j, p) {           // [nama, wajib]
    const r = [], seq = (pre, n) => { for (let i = 0; i < n; i++) r.push([pre + i, false]); };
    switch (j) {
      case 'kuis': seq('p', len(p.pilihan)); break;
      case 'jawaban': r.push(['jawab', true]); if (p.label) r.push(['label', false]); if (p.besar) r.push(['besar', false]); if (p.teaser) r.push(['teaser', true]); break;
      case 'langkah': seq('l', len(p.item)); break;
      case 'banding': seq('b', len(p.item)); break;
      case 'twist': r.push(['k', false]); seq('i', len(p.baris)); if (p.angka) r.push(['angka', false]); break;
      case 'pembuka': seq('b', Array.isArray(p.judul) ? p.judul.length : 1); if (p.sorot) r.push(['sorot', false]); break;
      case 'catatan': seq('k', len(p.kartu)); break;
      case 'ibarat': r.push(['kutip', false]); seq('k', len(p.kartu)); break;
      case 'tanya': seq('k', len(p.kartu)); r.push(['tanya', false]); if (len(p.pilihan)) r.push(['pilih', false]); break;
    }
    return r;
  }
  function parse(ta) {
    const v = ta.value.trim();
    if (!v) { ta.classList.remove('bad'); return {}; }
    try { const o = JSON.parse(v); if (typeof o !== 'object' || Array.isArray(o) || o === null) throw new Error('harus objek { … }'); ta.classList.remove('bad'); ta.title = ''; return o; }
    catch (e) { ta.classList.add('bad'); ta.title = e.message; return null; }
  }
  function preview(card) {
    const j = $('.jenis', card).value, p = parse($('.param', card)), pe = parse($('.param_en', card));
    for (const [lang, voSel, pv] of [['id', '.vo', p], ['en', '.vo_en', pe === null ? null : merged(p || {}, pe || {})]]) {
      const vo = $(voSel, card).value, out = $(`.pv-${lang}`, card);
      if (!vo.trim()) { out.innerHTML = lang === 'en' ? '<span class="muted">belum ada naskah English</span>' : '<span class="err">naskah kosong</span>'; continue; }
      const pages = shown(vo).split('|').map(s => s.trim().replace(/\s+/g, ' ')).filter(Boolean);
      const have = new Set(cuesIn(vo)), exp = pv ? expected(j, pv) : [];
      const chips = exp.map(([n, req]) => `<span class="cue ${have.has(n) ? 'y' : req ? 'no' : 'miss'}" title="${have.has(n) ? 'ada' : req ? 'wajib ditulis' : 'tidak ditulis: muncul merata sepanjang adegan'}">{${n}}</span>`);
      const extra = [...have].filter(n => !exp.some(e => e[0] === n)).map(n => `<span class="cue x" title="tidak dipakai jenis adegan ini">{${n}}</span>`);
      out.innerHTML = `<div class="pages">${pages.map(s => `<span>${esc(s)}</span>`).join('')}</div>` +
        `<div class="meta"><span class="muted">${pages.length} halaman · ${spoken(vo).length} karakter</span> ${chips.join('')}${extra.join('')}</div>`;
    }
  }

  /* ---------- kartu adegan ---------- */
  function jenisOptions(sel) {
    const fmt = fmtSel.value, ok = BYFMT[fmt] || [];
    const opt = j => `<option value="${j}" ${j === sel ? 'selected' : ''}>${esc(TPL[j].nama)}</option>`;
    const other = Object.keys(TPL).filter(j => !ok.includes(j));
    return ok.map(opt).join('') + (other.length ? `<optgroup label="format lain">${other.map(opt).join('')}</optgroup>` : '');
  }
  function help(j) {
    const t = TPL[j];
    return `<b>${esc(t.nama)}</b> — ${esc(t.ket)}<br><span class="muted">Isyarat:</span> <code>${esc(t.isyarat)}</code> · <span class="muted">Param:</span> ${esc(t.param)}`;
  }
  function card(sc) {
    const d = document.createElement('div');
    d.className = 'sc';
    d.innerHTML = `
      <div class="sc-h"><b class="no"></b><select class="jenis">${jenisOptions(sc.jenis)}</select>
        <span class="fmt-warn" hidden>bukan jenis format ini</span><span class="grow"></span>
        <button type="button" class="sm ghost" data-a="contoh" title="Isi dengan contoh jenis ini">Contoh</button>
        <button type="button" class="sm ghost" data-a="up" title="Naik">↑</button><button type="button" class="sm ghost" data-a="down" title="Turun">↓</button>
        <button type="button" class="sm ghost" data-a="dup" title="Duplikat">⧉</button><button type="button" class="sm ghost danger" data-a="del" title="Hapus">✕</button></div>
      <div class="sc-help"></div>
      <div class="sc-cols">
        <div><label>Naskah Indonesia</label><textarea class="vo" rows="4" spellcheck="false"></textarea><div class="pv pv-id"></div>
          <label>Param (JSON)</label><textarea class="param mono" rows="6" spellcheck="false"></textarea></div>
        <div><label>Naskah English</label><textarea class="vo_en" rows="4" spellcheck="false"></textarea><div class="pv pv-en"></div>
          <label>Param English <span class="muted">(hanya teks layar yang berbeda)</span></label><textarea class="param_en mono" rows="6" spellcheck="false"></textarea></div>
      </div>`;
    $('.vo', d).value = sc.vo || ''; $('.vo_en', d).value = sc.vo_en || '';
    $('.param', d).value = typeof sc.param === 'string' ? sc.param : pretty(sc.param);
    $('.param_en', d).value = typeof sc.param_en === 'string' ? sc.param_en : pretty(sc.param_en);
    refresh(d);
    return d;
  }
  function refresh(d) {
    const j = $('.jenis', d).value;
    $('.sc-help', d).innerHTML = help(j);
    $('.fmt-warn', d).hidden = (BYFMT[fmtSel.value] || []).includes(j);
    preview(d);
  }
  function renumber() { $$('.sc', list).forEach((d, i) => $('.no', d).textContent = '#' + (i + 1)); }
  function fromTemplate(j) { const t = TPL[j]; return { jenis: j, vo: t.vo, vo_en: t.vo_en, param: t.contoh, param_en: t.contoh_en }; }
  function serialize() {
    return $$('.sc', list).map(d => ({ jenis: $('.jenis', d).value, vo: $('.vo', d).value, vo_en: $('.vo_en', d).value,
      param: $('.param', d).value, param_en: $('.param_en', d).value }));
  }
  function fillAdd() { addSel.innerHTML = jenisOptions({ tebakan: 'langkah', fakta: 'catatan' }[fmtSel.value]); }

  J('d-adegan').forEach(sc => list.appendChild(card(sc)));
  renumber(); fillAdd();

  list.addEventListener('input', e => { dirty = true; const d = e.target.closest('.sc'); if (d) preview(d); });
  list.addEventListener('change', e => { if (e.target.classList.contains('jenis')) { dirty = true; refresh(e.target.closest('.sc')); } });
  list.addEventListener('click', e => {
    const b = e.target.closest('button[data-a]'); if (!b) return;
    const d = b.closest('.sc'), a = b.dataset.a; dirty = true;
    if (a === 'up' && d.previousElementSibling) list.insertBefore(d, d.previousElementSibling);
    if (a === 'down' && d.nextElementSibling) list.insertBefore(d.nextElementSibling, d);
    if (a === 'dup') list.insertBefore(card(serialize()[$$('.sc', list).indexOf(d)]), d.nextSibling);
    if (a === 'del' && confirm('Hapus adegan ini?')) d.remove();
    if (a === 'contoh') {
      const j = $('.jenis', d).value, filled = $('.vo', d).value.trim() || $('.param', d).value.trim();
      if (!filled || confirm('Ganti isi adegan ini dengan contoh "' + TPL[j].nama + '"?')) d.replaceWith(card(fromTemplate(j)));
    }
    renumber();
  });
  $('#add-btn').addEventListener('click', () => { const d = card(fromTemplate(addSel.value)); list.appendChild(d); renumber(); dirty = true; d.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
  fmtSel.addEventListener('change', () => { $('#fmt-ket').textContent = FMTS[fmtSel.value].ket; fillAdd();
    $$('.sc', list).forEach(d => { const j = $('.jenis', d).value; $('.jenis', d).innerHTML = jenisOptions(j); refresh(d); }); });
  form.addEventListener('input', e => { if (!e.target.closest('#adegan') && !e.target.classList.contains('filter-fakta')) dirty = true; });

  form.addEventListener('submit', e => {
    const bad = $$('.param, .param_en', list).filter(ta => parse(ta) === null);
    if (bad.length) {
      e.preventDefault();
      bad[0].focus(); bad[0].scrollIntoView({ block: 'center' });
      alert('Param JSON belum sah di ' + bad.length + ' kotak (bertanda merah):\n' + bad[0].title);
      return;
    }
    $('#adegan-json').value = JSON.stringify(serialize());
    dirty = false;
  });
  addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); form.requestSubmit(); } });
  addEventListener('beforeunload', e => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  $$('form.rf').forEach(f => f.addEventListener('submit', e => {
    if (dirty && !confirm('Ada perubahan yang belum disimpan. Render versi yang tersimpan saja?')) e.preventDefault(); else dirty = false;
  }));

  /* ---------- cari ikon ---------- */
  const iq = $('#ikon-q'), ih = $('#ikon-hasil');
  let timer = 0;
  iq.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const s = iq.value.trim(); if (!s) { ih.innerHTML = ''; return; }
      const names = await (await fetch('/api/ikon?q=' + encodeURIComponent(s))).json();
      ih.innerHTML = names.length ? names.map(n => `<button type="button" title="${esc(n)}" data-n="${esc(n)}"><img loading="lazy" src="/ikon/${encodeURIComponent(n)}.svg" alt=""><span>${esc(n)}</span></button>`).join('')
        : '<p class="muted small">Tidak ada. Coba kata Inggris.</p>';
    }, 220);
  });
  ih.addEventListener('click', async e => {
    const b = e.target.closest('button[data-n]'); if (!b) return;
    try { await navigator.clipboard.writeText(b.dataset.n); } catch (_) { /* http tanpa izin clipboard */ }
    b.classList.add('copied'); setTimeout(() => b.classList.remove('copied'), 900);
  });
})();
