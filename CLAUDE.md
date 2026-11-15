# Working with Shadi

Read this before every task. The user does not name skills. Pick the right
skills yourself from the request and combine them. Do not ask which skill to use.

## Two separate businesses: never mix them

| | Skincare | Art |
|---|---|---|
| Brand | Instagram @shadibeautyy, sells skincare products | Instagram @art_rada_dxb (Art Rada DXB, formerly @artdxb1975): daily UAE art news reels, gallery work, Les Sens |
| Tone | warm, personal, emotional, her face on camera | professional, curatorial, art-world |
| Audience | women who follow her for her face and her skin routine | collectors, buyers, gallerists, curators, art lovers |

If a request could belong to either one and the context does not make it clear,
ask in one short question. Never put skincare content in art work, or art
content in skincare work.

## Skincare marketing method (always)

1. **Value first, product last.** A reel never opens by selling. It opens on the
   viewer's problem or feeling, then what happens to the skin and how it feels,
   and only at the end shows the product and the invitation to order.
2. **Marketing psychology in everything:** emotion before logic, the feeling of
   the problem, relief and pleasure, social proof, honest scarcity, one clear ask.
   No fake claims, numbers, reviews or medical promises.
3. **Her face is the brand.** Her followers want to see her. Prefer formats where
   Shadi is on camera (talking, applying, reacting). Product-only shots support
   her, they don't replace her.
4. Mix social media know-how (hooks, formats, posting) with the psychology, and
   think in series, not one-off posts.

## Video and reel production rules

- Shadi films herself for every shot she is in. Never write AI prompts for her
  shots: give plain filming directions instead (where, light, what to do, what to say).
- AI prompts only for product, cream, texture and volume shots.
- Images first (Higgsfield Soul), then video (Kling / Veo). Video prompts describe motion only.
- Product shots use a real photo of the product.
- 9:16, 15 to 18 seconds, hook in the first 2 seconds.
- Prompts in English. Persian text and the @shadibeautyy watermark are added in CapCut, never in prompts.
- Write an English ASMR sound line for every shot.
- Story: feel the problem, then the calm and pleasure of the product, then the invitation to order.
- Every video (skincare and art) comes with a voiceover script for ElevenLabs:
  timed line by line to the video's scenes, ready to paste (with <break time="0.5s" /> pauses),
  plus suggested ElevenLabs settings and how to lay it over the music in CapCut.
- Never use relative dates (tomorrow, today, tonight, next week) in captions, voiceovers or on-screen
  text: always write the date ("16 November"). Posts are often published a day later.
- The voiceover script is short (about 2.5 words per second of video), separate from the caption,
  and spells hard names phonetically so ElevenLabs says them right.
- Background music must be engaging, with a beat the cuts follow (art reels: art-reels/tools/music.py).

## Skill routing (choose automatically, combine freely)

| Request | Skills to use |
|---|---|
| Reel / video idea or script | `ig-reel` + `marketing-psychology` + `video-producer` (+ `shadi-motion-style-menu` for edits) |
| Caption, hashtags | `ig-caption` + `ig-human` |
| Carousel | `ig-carousel` + `copywriting` |
| Stories, selling softly | `ig-story` + `marketing-psychology` |
| Weekly plan, what to post | `ig-plan` + `content-strategy` + `social` |
| What's trending in the niche | `ig-viral` |
| Analytics / what worked | `ig-audit` (+ Metricool connector if available) |
| Comments and DMs | `ig-reply`, `ig-dm`, `ig-comment` |
| Profile / bio | `ig-profile` |
| Offers, discounts, bundles | `offers` + `pricing` + `marketing-psychology` |
| Ads | `ads` + `ad-creative` |
| Influencers / collabs | `influencer-marketing` + `co-marketing` |
| Long content to cut into reels | `ig-repurpose` |
| Art news reels (@art_rada_dxb) | `ig-reel` + `social` + `content-strategy` + `ig-caption` (art tone; skincare video rules above do not apply; no @shadibeautyy watermark) |
| Art gallery work | `les-sens-art-scout`, `public-relations`, `events`, `competitor-profiling` (art tone, never skincare) |

Always run final text through `ig-human` so it does not sound like AI.

## Replies

Answer in Persian, line by line with the English translation under each line.
Keep prompts and code in English. Use simple words: the user is not technical,
so do not talk about git, branches or files unless she asks. Do the technical
steps yourself (commit and push finished work) without asking her to.
