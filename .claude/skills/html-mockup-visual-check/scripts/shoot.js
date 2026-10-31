// usage: NODE_PATH=$(npm root -g) node scripts/shoot.js <file.html> <outdir>
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const [file, outDir] = process.argv.slice(2);
if (!file || !outDir) {
  console.error('usage: node shoot.js <file.html> <outdir>');
  process.exit(2);
}
fs.mkdirSync(outDir, { recursive: true });

const VIEWS = [[1440, 900], [1100, 800], [768, 1024], [390, 844]];

(async () => {
  const browser = await chromium.launch();
  const url = 'file://' + path.resolve(file);
  let bad = 0;
  for (const dark of [false, true]) {
    for (const [w, h] of VIEWS) {
      const name = `${w}${dark ? '-dark' : ''}`;
      const ctx = await browser.newContext({
        viewport: { width: w, height: h },
        colorScheme: dark ? 'dark' : 'light',
      });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      await page.goto(url);
      await page.evaluate(() => document.fonts.ready);
      const m = await page.evaluate(() => ({
        overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        h1: document.querySelectorAll('h1').length,
      }));
      await page.screenshot({ path: path.join(outDir, name + '.png'), fullPage: true });
      const flag = m.overflowX > 0 || errors.length ? ' <-- CHECK' : '';
      if (flag) bad++;
      console.log(`${name}: overflowX=${m.overflowX} h1=${m.h1} errors=${errors.length}${flag}`);
      for (const e of errors) console.log('  ' + e);
      await ctx.close();
    }
  }
  await browser.close();
  process.exitCode = bad ? 1 : 0;
})();
