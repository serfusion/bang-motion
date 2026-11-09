// Dump the SFX pin table computed by the page (single source of truth) to sfx.json.
// Run from projects/daun-katuk:  node tools/dump-sfx.mjs   (needs puppeteer; CHROME env for a local browser)
import puppeteer from 'puppeteer';
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';
const url = pathToFileURL(process.cwd()).href + '/index.html?clean=1';
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
page.on('pageerror', e => console.log('PAGEERROR', e.message));
await page.goto(url, { waitUntil: 'networkidle0' });
await page.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 60000 });
const sfx = await page.evaluate(() => window.OPENER.sfx);
await writeFile('sfx.json', JSON.stringify(sfx, null, 1));
console.log(`${sfx.length} SFX pins -> sfx.json`);
await browser.close();
