"""DRAFT word timings for Episode 4, estimated from the script (no narration yet).
Replace with real timings (local Whisper / ElevenLabs transcription) once the narration exists, then re-run make_captions.py.
Writes words_final.json + env.npy (fake lip-sync: mouth open while a word is 'spoken')."""
import json, re, numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__))
txt = open(os.path.join(HERE, "../../episode-04/script.txt")).read().split()
COUNT = {"one", "two", "three", "four", "and", "boom", "crack", "tick"}
t = 0.15; out = []
for i, w in enumerate(txt):
    core = re.sub(r"[^a-z]", "", w.lower())
    nxt = re.sub(r"[^a-z]", "", txt[i + 1].lower()) if i + 1 < len(txt) else ""
    counting = core in COUNT and (nxt in COUNT or w[-1] in ".,")
    d = .28 if counting else .07 + .045 * len(core)
    out.append({"text": w, "start": round(t, 3), "end": round(t + d, 3)})
    gap = .04
    if w[-1] in ".?!": gap = .45
    elif w[-1] in ",:": gap = .2
    if counting and w[-1] not in ".?!": gap = .06
    t += d + gap
json.dump(out, open(os.path.join(HERE, "words_final.json"), "w"), indent=0)
fps = 30; n = int((t + 2) * fps); e = np.zeros(n, np.float32)
for w in out:
    a, b = int(w["start"] * fps), int(w["end"] * fps)
    e[a:b] = .55 + .45 * np.abs(np.sin(np.arange(b - a) * 1.7))
np.save(os.path.join(HERE, "env.npy"), e)
print(len(out), "words, total", round(t, 1), "s")
