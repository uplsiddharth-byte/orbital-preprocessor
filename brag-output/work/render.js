const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const url = 'file://' + path.resolve(__dirname, 'index.html');
(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch();
  const mk = async () => { const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 }); const p = await ctx.newPage(); await p.goto(url); await p.evaluate(() => window.ready); return p; };
  if (mode === 'stills') {
    const times = process.argv.slice(3).map(Number); fs.mkdirSync('stills', { recursive: true });
    const p = await mk();
    for (const t of times) { await p.evaluate(t => window.render(t), t); await p.screenshot({ path: `stills/t_${t.toFixed(2)}.png` }); }
    const cues = await p.evaluate(() => ({ cues: window.CUES, scenes: window.SCENES }));
    fs.writeFileSync('cues.json', JSON.stringify(cues));
  } else if (mode === 'full') {
    const FPS = 30, N = 60 * FPS, W = 4; fs.mkdirSync('frames', { recursive: true });
    const pages = await Promise.all([...Array(W)].map(mk));
    let next = 0;
    await Promise.all(pages.map(async p => { for (;;) { const i = next++; if (i >= N) break; await p.evaluate(t => window.render(t), i / FPS); await p.screenshot({ path: `frames/f_${String(i + 1).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 94 }); if (i % 150 === 0) console.log('frame', i); } }));
  }
  await browser.close();
})();
