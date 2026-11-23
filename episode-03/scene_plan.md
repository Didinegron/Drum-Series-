# Episode 3: "Your first rock beat in 5 minutes" — scene plan

Narration: `episode-03/audio/narration_final.mp3` (5:12, Drum Channel Narrator). Times below come from `captions/word_timings.json`.
Everything animated (no footage). Same look as Episode 2: blue ray background, red snare mascot bottom-left (lip-synced), karaoke captions, "EPISODE 3" pill, star progress bar, gift box teasing the bonus. Reuse the Episode 2 kit characters and seated drummer (round fists only, no drawn fingers).

## The star of the episode: the BEAT CHART

```
            1  &  2  &  3  &  4  &
HI-HAT  (R hand) ●  ●  ●  ●  ●  ●  ●  ●
SNARE   (L hand)       ●           ●
KICK    (R foot) ●           ●
```
- 8 columns, 3 rows; each row has the instrument icon + "RIGHT HAND / LEFT HAND / RIGHT FOOT" sticker.
- A glowing cursor moves column to column, **timed to each spoken word** ("one", "and", "boom", "crack"...), not to a metronome, so it always matches the narration.
- Lit cells pop + comic burst: TICK! (hi-hat), BOOM! (kick), CRACK! (snare).
- Rows are added one layer at a time (empty rows shown faded until their layer).

## Progress-bar sections (stars)
START · WHO PLAYS WHAT · LAYER 1 · LAYER 2 · LAYER 3 · ALL TOGETHER · TIPS · BONUS

## Scenes

| # | Time | Scene | What's on screen |
|---|---|---|---|
| 1 | 0:00–0:21 | **Hook** | Kit plays the full beat in sync with "Boom, tick, crack, tick" (bursts per word). Title card "YOUR FIRST ROCK BEAT" pops in on "rock beat". Gift box wiggles on "bonus trick". |
| 2 | 0:21–0:45 | **Recap of Lesson 2** | Three Episode-2 characters pop in one by one: kick = BOOM, snare = CRACK, hi-hat = CLOCK (clock face sticker). "LESSON 2" thumbnail card on "pause this". Seated drummer grabs sticks / sits on throne at "let's build a beat". |
| 3 | 0:45–1:06 | **Who plays what** | Stacking-blocks animation (3 blocks drop in: HI-HAT, SNARE, KICK). Drummer at the kit, top-down-ish view; colored labels appear on cue: right hand → hi-hat, left hand → snare, right foot → kick pedal. Left foot: hi-hat pedal pressed **down**, cymbals closed, "CLOSED = TICK" sticker. |
| 3b | 1:06–1:22 | **Crossed arms** | Top-down view of drummer: right arm crosses over left to the hi-hat, a big pink "X" outline flashes on "little X". "TOTALLY NORMAL!" sticker + thumbs-up from mascot. |
| 4 | 1:22–2:03 | **Layer 1: the clock** | Beat chart appears with only the HI-HAT row active. "1 & 2 & 3 & 4 &" counters light up word by word during "Say it with me" (no hits yet, just the counting). Clock sticker ticks on "like a clock ticking". |
| 4b | 1:42–2:03 | **Play the hi-hat** | Now each count also triggers a hi-hat hit (stick strikes the top cymbal, tip hovers between hits). "8 TICKS!" counter. "SLOW DOWN = OK" and "STEADY > FAST" stickers. |
| 5 | 2:03–2:32 | **Layer 2: add the boom** | KICK row lights up. **Side-view inset of the pedal: beater swings front-to-back** into the head on each "boom". Sync flash where kick + hi-hat land together ("TOGETHER!" on 2:28–2:31). |
| 6 | 2:32–2:57 | **Layer 3: add the crack** | SNARE row lights up; snare hits land on the top head. At 2:44 "on one / on two" mini-diagram: count 1 = foot + right hand glow, count 2 = both hands glow. |
| 7 | 2:57–3:26 | **All together, slow** | Full chart + full kit, "SLOW" tempo badge (turtle sticker). Cursor follows the count-in "1, 2, 3, 4" then both bars. "DON'T STOP!" sticker on "keep going". |
| 8 | 3:26–3:47 | **Normal speed** | "ROCK SPEED" badge (rocket/flame), faster ray background, confetti + "YOU DID IT!" on "you just played your first rock beat" (3:42). |
| 9 | 3:47–4:14 | **Common mix-ups** | Two tip cards. #1 RUSHING: speedometer needle drifting up, then "COUNT OUT LOUD". #2 NOT TOGETHER: kick and hi-hat flashes slightly apart, then snapping into one flash. |
| 10 | 4:14–4:27 | **Recap** | The finished chart alone, rows highlighted as named ("every count / 1 and 3 / 2 and 4"), then cursor runs once on the last "boom and crack and". |
| 11 | 4:27–4:58 | **Bonus: lap drumming** | Gift box opens. Simple cartoon kid on a chair (round fists, no fingers): right fist taps right leg = HI-HAT, left fist taps left leg = SNARE, right foot taps floor = KICK; same chart mini in the corner, lit in sync. Icons for table / couch / TV. |
| 12 | 4:58–5:12 | **Outro + notation tease** | On "read beats like this one right off the page" (5:05) the beat chart morphs into a real 1-bar drum staff (hi-hat x's on top, snare on 2 & 4, kick on 1 & 3) with a "COMING SOON" sticker — **no explanation, just a peek**. "EPISODE 4: READING MUSIC" card, subscribe button, mascot waves. |

## Things to check
- **The narration's "normal speed" bar is about the same pace as the "slow" one** (both ≈2.7–2.8 s per bar). Visuals follow the voice, so scene 8 won't look much faster.
  Suggested fix: right after the narrator's normal-speed count (≈3:39), add a **real drum loop** (synthesized kick/snare/hi-hat at ~100 BPM, 2 bars, ~5 s) under the "Listen to that!" line, with the kit and chart playing at that real tempo. Same could be used softly under scene 1.
- Mechanics (creator checks closely): sticks hit the **top** of the snare head and the top of the hi-hat; tips hover above between hits; kick beater front-to-back in side-view inset; hi-hat stays **closed** (left foot down) the whole episode.
- Captions: build with `tools/episode-02/make_captions.py`; pink key words: hi-hat, snare, kick, boom, crack, tick, clock, layer, together, bonus.

## Next
1. Creator approves this plan (and the drum-loop idea).
2. Stills of each scene (low res) → review.
3. Super-low-res preview → fixes → 4K render.
4. Then: 3 Shorts, thumbnail, YouTube copy.
