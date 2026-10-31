// Kiểm ảnh giao diện (kế hoạch P1, G0): chụp các trang ở 1440/768/390, sáng và tối; báo cuộn ngang, số h1,
// phông không tải được, yêu cầu mạng ra ngoài 127.0.0.1, lỗi JS. Chỉ là công cụ đo, không phải test.
//
// App phải chạy sẵn bằng Python, ví dụ kho nhỏ từ tests/fixtures:
//   SOILUAT_DATA=/tmp/kho python -c "from pathlib import Path; from soiluat.db import connect, init_schema; from soiluat.ingest import ingest_path; c=connect(Path('/tmp/kho/soiluat.db')); init_schema(c); ingest_path(c, Path('tests/fixtures/nd15.txt'), Path('tests/fixtures'))"
//   SOILUAT_DATA=/tmp/kho python -c "import uvicorn; from soiluat.app import app; uvicorn.run(app, host='127.0.0.1', port=8765)"
// Chạy: NODE_PATH=$(npm root -g) node bench/kiem_anh.js [http://127.0.0.1:8765] [thư mục ảnh] [đường dẫn trang ...]
const { chromium } = require('playwright');

const base = process.argv[2] || 'http://127.0.0.1:8765';
const out = process.argv[3] || 'kiem-anh';
const paths = process.argv.slice(4).length ? process.argv.slice(4) : ['/', '/?q=b%C3%A1o%20c%C3%A1o'];
const sizes = [[1440, 900], [768, 1024], [390, 844]];

(async () => {
  require('fs').mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  let bad = 0;
  for (const scheme of ['light', 'dark']) {
    for (const [w, h] of sizes) {
      const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme });
      for (const path of paths) {
        const p = await ctx.newPage();
        const errs = [], outside = [];
        p.on('pageerror', e => errs.push(e.message));
        p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
        p.on('request', r => { if (!r.url().startsWith(base) && !r.url().startsWith('data:')) outside.push(r.url()); });
        await p.goto(base + path, { waitUntil: 'networkidle' });
        const m = await p.evaluate(async () => {
          await document.fonts.ready;
          return { over: document.scrollingElement.scrollWidth - innerWidth, h1: document.querySelectorAll('h1').length,
                   font: document.fonts.check('16px "Be Vietnam Pro"') && [...document.fonts].some(f => f.family.includes('Be Vietnam Pro') && f.status === 'loaded') };
        });
        const name = `${scheme}-${w}-${path.replace(/[^a-z0-9]+/gi, '_') || 'home'}`;
        await p.screenshot({ path: `${out}/${name}.png` });
        const ok = m.over <= 0 && m.h1 === 1 && m.font && !errs.length && !outside.length;
        if (!ok) bad++;
        console.log(`${ok ? 'ok ' : 'LỖI'} ${name}: cuộn ngang ${m.over}px, h1=${m.h1}, phông ${m.font ? 'có' : 'KHÔNG'}${errs.length ? ', lỗi JS: ' + errs.join(' | ') : ''}${outside.length ? ', ra ngoài: ' + outside.join(' ') : ''}`);
        await p.close();
      }
      await ctx.close();
    }
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})();
