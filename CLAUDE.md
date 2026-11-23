# Drum Series: project handoff (read this first)

Kid-friendly (and adult-friendly) beginner drum course on YouTube. Per lesson: **one ~5-minute 4K episode + three ~25 s YouTube Shorts + a thumbnail + YouTube copy**.
Episode list and status: `DRUM_SERIES_PLAN.md`. **Only work on the episode the creator asks for.**

## Status
- Episode 1 (hold drumsticks): DONE (episode, 3 Shorts, thumbnail). Uses real photos/footage of the creator's hands.
- Episode 2 (drum kit explained): DONE (4K episode, 3 Shorts, thumbnail, YouTube copy in `episode-02/youtube.md`). Fully animated.
- **Next: Episode 3, "Your first rock beat in 5 minutes."** (It is 5 minutes, not 10.)

## The creator's preferences (learned the hard way)
- **Never draw detailed hands/fingers.** Cartoon hands looked wrong. Use the creator's real photos/video for hand technique; for cartoon people use simple round fists (sleeve + ball) only.
- **Drum mechanics must be physically correct.** The creator checks closely:
  - A stick must strike the **top drumhead**, never the shell; between hits keep the tip hovering above the head.
  - The kick-drum beater swings **front-to-back** into the head (shown in a side-view inset), never side to side.
  - Hi-hat: pedal down = closed (tight tick), foot up = open (sizzle).
- **Highlighted word-by-word captions are a must** (active word yellow, key words pink, Fredoka font).
- Workflow the creator likes: **stills → super-low-res preview → fix → full render.** Never render full quality before approval.
- Logos: keep them on the creator's own photos/video and on AI images; blur only third-party stock photos.
- AI-generated images get a "CLOSE-UP" tag (not "REAL LIFE"); remind them to tick YouTube's altered/synthetic-content box.
- Deliver files to the phone via GitHub raw links (`https://github.com/Didinegron/Drum-Series-/raw/main/<path>`); the chat file card can't save to iPhone. Files over 100 MB (4K masters) can't go on GitHub; send those as file cards.
- Keep replies short and plain; the creator works from an iPhone.

## Style (keep every episode consistent)
- Bright blue radial background with slow rays and floating notes; section tint per scene.
- Red snare-drum mascot with a face in the bottom-left (episodes) / top-right (Shorts), mouth lip-synced to the narration loudness.
- Top bar: "EPISODE N" pill, progress bar with a star per section, gift box teasing the bonus.
- Sticker labels, comic bursts (BOOM!/CRACK!/TICK!), confetti, pop-in animations.
- Episode 2 kit characters (snare, kick, hi-hat, toms, crash, ride, throne, seated drummer) are in `tools/episode-02/ep2.py` and are reusable.
- Shorts: 1080x1920, big 2-3-word captions mid-screen, "DRUMS IN 5 MIN" / "FULL LESSON: EPISODE N" header, **loop-back ending** (script ends mid-sentence so it flows into the first line).
- Thumbnail: 1280x720, huge 2-line headline, mascot/kit on a burst, "EPISODE N" + "IN 5 MIN" pills.

## Audio, captions, ElevenLabs
- Narration voice: **Drum Channel Narrator** (the creator's own designed voice), voice_id `pOGS4nGBqPulBSkdAAlJ`, model `eleven_v4` (ElevenLabs connector). **Not** the stock "Roger" voice (`CwhRBWXzGAHq8TQ4Fs17`): Roger sounded wrong to the creator in Episode 3 (old Roger takes kept in `episode-03/audio/roger_takes/`).
- I can generate narration directly with the ElevenLabs connector (creative_generate_speech) and download it.
- Exact word timings: push the MP3 to this repo, attach it to an ElevenLabs flow by raw GitHub URL (creative_attach_reference_file), run creative_transcribe_audio (~1,800 credits per 5 min; ~140 per Short). Self-estimated timings drifted up to 2 s, so always use real transcription timings.
- The ElevenLabs CDN host (`elevenlabsusercontent.com`) is allowed only in the personal cloud environment **"Drum Series"**; use that environment.
- Captions: `tools/episode-02/make_captions.py` builds the karaoke `.ass` + `cues.json` from word timings.

## Tools
- Python 3 + pycairo + numpy + Pillow + ffmpeg (libass). Fonts: Fredoka (convert `@fontsource/fredoka` woff2 to TTF with fontTools, install to `~/.local/share/fonts`, `fc-cache -f`; fix family names so "Fredoka" = bold).
- `tools/episode-02/ep2.py`: episode renderer (`still T scale out.png`, `range F0 F1 scale out.mp4`); 4K = scale 2.0, render in 4 parallel chunks (~20 min), then concat + mux narration.
- `tools/episode-02/shorts/shorts2.py`: Shorts renderer (`render N out.mp4 [scale fps crf]`); preview = scale 0.33, 15 fps, crf 30.
- `tools/episode-02/thumb2.py`: thumbnail. Scripts use absolute scratch paths; adjust paths at the top when reusing.

## Ideas for Episode 3: "Your first rock beat in 5 minutes"
- Builds directly on Episode 2's "team plays" scene: hi-hat 8ths + kick on 1 & 3 + snare on 2 & 4.
- Teach it in layers: hi-hat alone, counting "1 & 2 & 3 & 4 &", then add kick, then add snare, then play together; show a slow and a normal tempo.
- Visual: animated beat grid / "light-up" pads per count, with the kit characters hitting in sync; right hand / left hand / right foot labels.
- Real footage of the creator playing the beat (overhead + side) would fit; ask before planning.
- Shorts ideas: "The 1-2-3-4 trick", "Add the boom", "Your first beat in 20 seconds".
- Suggested workflow: write script → generate Roger narration → transcribe for timings → scene plan → stills → low-res preview → 4K.
