/* Frame-accurate MP4 export (same method as bang-motion scripts/export-frames.mjs:
   set the timeline time -> wait two rAF -> screenshot), split into parallel shards that
   pipe JPEG frames straight into one ffmpeg encoder each, then concatenated losslessly.
   Each shard gets its own browser: a background tab of a shared browser gets no rAF, so it would stall.

   Run from projects/daun-katuk (needs puppeteer + ffmpeg; PUPPETEER_EXECUTABLE_PATH for a local Chrome):
     node tools/export.mjs                 -> build/video.mp4 (no audio, 1080x1920, 30 fps)
   env: FPS=30 SHARDS=3 FROM=0 TO=<frames> OUT=build
*/
import puppeteer from 'puppeteer';
import { pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';

const FPS = Number(process.env.FPS || 30), SHARDS = Number(process.env.SHARDS || 3), OUT = process.env.OUT || 'build';
const URL = process.env.URL || pathToFileURL(process.cwd()).href + '/index.html?clean=1';
await mkdir(OUT, { recursive: true });

const launch = () => puppeteer.launch({ headless: 'new', protocolTimeout: 600000,
  args: ['--no-sandbox', '--force-device-scale-factor=1', '--hide-scrollbars', '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'] });
const browser = await launch();
const probe = await browser.newPage();
await probe.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
await probe.goto(URL, { waitUntil: 'networkidle0' });
await probe.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 120000 });
const DURATION = await probe.evaluate(() => window.OPENER.DURATION);
await probe.close();
await browser.close();
const FROM = Number(process.env.FROM || 0), TO = Number(process.env.TO || Math.round(DURATION * FPS));
const per = Math.ceil((TO - FROM) / SHARDS);
const t0 = Date.now();

async function shard(k, f0, f1) {
  const br = await launch();
  const page = await br.newPage();
  page.on('pageerror', e => console.log(`[${k}] PAGEERROR`, e.message));
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto(URL, { waitUntil: 'networkidle0' });
  await page.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 120000 });
  await page.evaluate(() => document.fonts.ready);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(process.env.CRF || 17), '-pix_fmt', 'yuv420p', '-r', String(FPS), `${OUT}/seg${k}.mp4`],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = f0; i < f1; i++) {
    await page.evaluate(async (t) => {
      window.OPENER.seek(t);
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      window.OPENER.seek(t);                       // GSAP wrote styles, render(t) drew the procedural layers
    }, i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95, clip: { x: 0, y: 0, width: 1080, height: 1920 }, optimizeForSpeed: true });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((i - f0) % 60 === 0) console.log(`[${k}] frame ${i}/${f1}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await br.close();
}

const jobs = [];
for (let k = 0; k < SHARDS; k++) { const a = FROM + k * per, b = Math.min(TO, a + per); if (a < b) jobs.push(shard(k, a, b)); }
await Promise.all(jobs);
await writeFile(`${OUT}/segs.txt`, jobs.map((_, k) => `file 'seg${k}.mp4'`).join('\n') + '\n');
await new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', `${OUT}/segs.txt`, '-c', 'copy', `${OUT}/video.mp4`],
  { stdio: 'inherit' }).on('close', c => c ? rej(new Error('concat ' + c)) : res()));
console.log(`done: ${TO - FROM} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}/video.mp4`);
