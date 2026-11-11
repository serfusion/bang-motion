// Bangun portofolio superfal-dev.com dari templat yang terbaca.
//
//   npm install                               sekali (ikon Iconify, pengacak skrip, pemerkecil HTML)
//   node bangun.mjs                           -> ../index.html   (situs: skrip diacak, perangkap devtools, terkunci ke domain superfal-dev.com)
//   node bangun.mjs --artifact <berkas.html>  -> pratinjau claude.ai (skrip diacak, tanpa kunci domain / perangkap devtools)
//   node bangun.mjs --baca <berkas.html>      -> versi situs yang terbaca (untuk memeriksa / membandingkan)
//   DOMAIN=domainbaru.com node bangun.mjs     -> pindah domain: alamat situs, formulir kunci & kunci domain ikut diganti
//
// Templat: portofolio.src.html (format "kepala artifact": <title>, meta, <style> ... <!-- /kepala --> lalu isi <body>).
// {{i:set:nama|kelas}} diganti SVG Iconify (lucide = ikon garis, logos / vscode = logo merek berwarna).
// Catatan jujur: pengacakan hanya memperlambat orang yang ingin menyalin; HTML, CSS dan teks tetap terkirim ke peramban.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SETS = { lucide: '@iconify-json/lucide/icons.json', logos: '@iconify-json/logos/icons.json', vscode: '@iconify-json/vscode-icons/icons.json' };
const cache = {};
const DOMAIN = process.env.DOMAIN || 'superfal-dev.com';

function ikon(spec, cls = 'ic') {
  const [set, name] = spec.split(':');
  const d = (cache[set] ||= JSON.parse(fs.readFileSync(require.resolve(SETS[set]), 'utf8')));
  let ic = d.icons[name];
  if (!ic) { const al = (d.aliases || {})[name]; if (!al) throw new Error('ikon tidak ada: ' + spec); ic = d.icons[al.parent]; }
  const w = ic.width || d.width || 24, h = ic.height || d.height || 24;
  let body = ic.body;
  if (set === 'lucide') body = body.replaceAll('stroke-width="2"', 'stroke-width="1.75"');
  const pre = name.replace(/[^a-z0-9]/g, '').slice(0, 10);
  for (const id of new Set([...body.matchAll(/id="([^"]+)"/g)].map(m => m[1])))
    body = body.replaceAll(`id="${id}"`, `id="${pre}${id}"`).replaceAll(`url(#${id})`, `url(#${pre}${id})`).replaceAll(`href="#${id}"`, `href="#${pre}${id}"`);
  return `<svg class="${cls}" viewBox="0 0 ${w} ${h}" aria-hidden="true">${body}</svg>`;
}

function sisipIkon(t) {
  t = t.replace(/\{\{i:([a-z]+:[a-z0-9-]+)(?:\|([a-z0-9 -]+))?\}\}/g, (_, spec, cls) => ikon(spec, cls || 'ic'));
  const sisa = t.match(/\{\{[^}]+\}\}/g);
  if (sisa) throw new Error('penanda tersisa: ' + sisa.join(', '));
  return t;
}

// format artifact -> dokumen utuh untuk situs
function keSitus(t) {
  const [head, body] = t.split('<!-- /kepala -->');
  if (!body) throw new Error('penanda <!-- /kepala --> tidak ada');
  const h = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
    .replace('<meta name="description"', `<link rel="canonical" href="https://${DOMAIN}/">\n<meta name="description"`);
  return '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + h.trim() + '\n</head>\n<body>\n' + body.trim() + '\n</body>\n</html>\n';
}

async function lindungi(html, { situs }) {
  const JO = require('javascript-obfuscator');
  const { minify } = require('html-minifier-terser');
  const opt = {
    compact: true, target: 'browser', identifierNamesGenerator: 'hexadecimal', renameGlobals: false,
    controlFlowFlattening: true, controlFlowFlatteningThreshold: 0.4, deadCodeInjection: true, deadCodeInjectionThreshold: 0.15,
    stringArray: true, stringArrayEncoding: ['base64'], stringArrayThreshold: 0.8, stringArrayRotate: true, stringArrayShuffle: true,
    splitStrings: true, splitStringsChunkLength: 10, transformObjectKeys: true, numbersToExpressions: true, unicodeEscapeSequence: false,
    selfDefending: true, disableConsoleOutput: true,
    ...(situs ? { debugProtection: true, debugProtectionInterval: 4000, domainLock: ['.' + DOMAIN],
                  domainLockRedirectUrl: `https://${DOMAIN}/` } : {}),
  };
  let out = await minify(html, { collapseWhitespace: true, conservativeCollapse: true, removeComments: true, minifyCSS: true,
                                 minifyJS: false, decodeEntities: false, useShortDoctype: true });
  let n = 0;
  out = out.replace(/<script>([\s\S]*?)<\/script>/g, (m, js) => {
    if (js.length < 600) return m;                      // skrip tema kecil di <head>: dibiarkan supaya tidak ada kedip
    n++;
    return '<script>' + JO.obfuscate(js, opt).getObfuscatedCode() + '</script>';
  });
  if (!n) throw new Error('skrip utama tidak ditemukan');
  return out;
}

const a = process.argv.slice(2);
const src = sisipIkon(fs.readFileSync(path.join(HERE, 'portofolio.src.html'), 'utf8')).replaceAll('superfal-dev.com', DOMAIN);
if (a[0] === '--artifact') {
  fs.writeFileSync(a[1], await lindungi(src, { situs: false }));
  console.log('artifact ->', a[1]);
} else if (a[0] === '--baca') {
  fs.writeFileSync(a[1], keSitus(src));
  console.log('terbaca ->', a[1]);
} else {
  const out = path.join(HERE, '..', 'index.html');
  const html = await lindungi(keSitus(src), { situs: true });
  fs.writeFileSync(out, html);
  console.log('situs ->', path.relative(process.cwd(), out), Math.round(html.length / 1024), 'KB');
}
