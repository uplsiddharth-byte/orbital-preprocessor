const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 1920, height: 1080 } })).newPage();
  await p.goto('file://' + path.resolve(__dirname, 'index.html')); await p.evaluate(() => window.ready);
  await p.evaluate(() => { window.render(25.5); document.getElementById('sub').style.display = 'none'; });
  await p.screenshot({ path: '../brag.jpg', type: 'jpeg', quality: 94 }); await b.close(); })();
