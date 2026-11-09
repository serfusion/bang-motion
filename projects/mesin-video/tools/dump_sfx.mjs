// The page computes the SFX pin table from the same word times as the visuals; dump it to episodes/ID/sfx.json.
//   node tools/dump_sfx.mjs ID
import puppeteer from 'puppeteer';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
const id = process.argv[2], dir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'episodes', id);
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
const errs = [];
page.on('pageerror', e => errs.push(e.message));
await page.goto(pathToFileURL(path.join(dir, 'index.html')).href + '?clean=1', { waitUntil: 'networkidle0' });
await page.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 60000 }).catch(() => {});
if (errs.length) { console.error('PAGEERROR', errs.join('\n')); process.exit(1); }
const sfx = await page.evaluate(() => window.OPENER.sfx);
await writeFile(path.join(dir, 'sfx.json'), JSON.stringify(sfx, null, 1));
console.log(`${sfx.length} pin SFX -> episodes/${id}/sfx.json`);
await browser.close();
