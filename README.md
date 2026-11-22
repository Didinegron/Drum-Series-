# Drum Series

A kid-friendly (and adult-friendly) beginner drum course: one ~5-minute animated episode plus three YouTube Shorts per lesson.
See **[DRUM_SERIES_PLAN.md](DRUM_SERIES_PLAN.md)** for the episode list and the style rules.

## Layout

```
DRUM_SERIES_PLAN.md          episode list, status, style + workflow rules
episode-01/                  How to hold drumsticks (DONE)
  audio/narration_final.mp3          final narration (2nd/3rd "pun intended" removed)
  captions/                          word-by-word karaoke .ass (+ original captions supplied)
  photos/                            photos used in the video (see credits below)
  footage/drum_video_source.mp4      creator's own drum footage (clips were cut from this)
  video/episode1_1080p.mp4           final episode, 1080p (4K master kept off GitHub: >100 MB)
  shorts/audio, shorts/video         the three Shorts (1080x1920)
  thumbnail/episode1_thumbnail.png   1280x720 YouTube thumbnail
tools/
  episode-01/                        animation + render code (Python, pycairo, ffmpeg)
  shorts/                            vertical Shorts renderer
```

## Photo credits

| File | Source |
|---|---|
| `r1_*.jpg`–`r5_*.jpg` | Creator's own photos |
| `p5_vgrip.png`, `p6_pad.jpg`, `p7_pinch.jpg` | AI-generated (ChatGPT / Gemini) — tick "altered or synthetic content" on YouTube |
| `p1_sidegrip.jpg` | Pavel Danilyuk, Pexels |
| `p3_kit.jpg` | cottonbro studio, Pexels (cymbal logos blurred) |
| `p4_playing.jpg` | Oscar Ivan Esquivel Arteaga, Unsplash (cropped; logo/face removed) |

## Notes for future sessions

- The tools currently use absolute paths from the session they were built in; adjust the paths at the top of each script before re-running.
- Requirements: `ffmpeg` (with libass), Python 3 with `pycairo`, `numpy`, `Pillow`; the Fredoka font (from the `@fontsource/fredoka` npm package, converted to TTF).
