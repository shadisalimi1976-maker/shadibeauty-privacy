// Renders index.html to stills (PNG) and a silent MP4.
// Usage:  node render.js stills     -> stills/ (with and without text)
//         node render.js video      -> hair-science-water-vs-bleach.mp4
//         node render.js all
// Needs: Node, Playwright (Chromium) and ffmpeg.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const mode = process.argv[2] || 'all';
const dir = __dirname;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exitCode = 1; });
  await page.goto('file://' + path.join(dir, 'index.html'));
  await page.evaluate(() => HairFilm.ready);
  const info = await page.evaluate(() => ({ fps: HairFilm.FPS, dur: HairFilm.DURATION, scenes: HairFilm.SCENES.map(s => ({ id: s.id, still: s.still })), check: HairFilm.check() }));
  console.log('check:', JSON.stringify(info.check));

  if (mode === 'stills' || mode === 'all') {
    for (const sub of ['stills/with-text', 'stills/no-text']) fs.mkdirSync(path.join(dir, sub), { recursive: true });
    for (const s of info.scenes) for (const withText of [true, false]) {
      const url = await page.evaluate(([t, w]) => HairFilm.frame(t, w, 'image/png'), [s.still, withText]);
      fs.writeFileSync(path.join(dir, 'stills', withText ? 'with-text' : 'no-text', s.id + '.png'), Buffer.from(url.split(',')[1], 'base64'));
    }
    console.log('stills done');
  }

  if (mode === 'video' || mode === 'all') {
    const out = path.join(dir, 'hair-science-water-vs-bleach.mp4');
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(info.fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-r', String(info.fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const total = Math.round(info.fps * info.dur);
    for (let f = 0; f < total; f++) {
      const url = await page.evaluate(t => HairFilm.frame(t, true, 'image/jpeg', 0.96), f / info.fps);
      if (!ff.stdin.write(Buffer.from(url.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 150 === 0) console.log('frame', f, '/', total);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('video done:', out);
  }
  await browser.close();
})();
