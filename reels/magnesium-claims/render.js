// Usage: node render.js stills <out.jpg-prefix> t1 t2 ...   |   node render.js video <out.mp4>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [mode, out, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'index.html'));
  await p.waitForFunction('window.ready===true');
  if (mode === 'stills') {
    for (const t of ts) { await p.evaluate(t => render(t), +t); await p.screenshot({ path: `${out}_${t}.jpg`, quality: 80 }); }
  } else {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-i', '-',
      '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', '-movflags', '+faststart', out],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < 960; f++) {
      await p.evaluate(t => render(t), f / 30);
      const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
