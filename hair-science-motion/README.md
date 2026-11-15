# Hair Science: Water vs Bleach (Shadi Beauty)

60-second vertical motion graphic (1080 x 1920, 30 fps, silent, 8 scenes).
On-screen text is Persian by default; open `index.html?lang=en` for English.

- `index.html` : the playable, editable animation. Open it in any browser.
  Text wording is in `TEXT`, colours in `COLOR`, one function per scene
  (`scene1_IntoTheHair` ... `scene8_Comparison`), timing in `SCENES`.
- `hair-science-water-vs-bleach.mp4` : rendered video, no audio.
- `stills/with-text`, `stills/no-text` : one 1080 x 1920 PNG per scene.
- `render.js` : re-renders stills and MP4 after an edit
  (`node render.js all`, needs Playwright and ffmpeg).
