"""Episode 3 audio + timing prep.
- Inserts a 5 s real-tempo drum loop (synthesized, 110 BPM, 2 bars) after the normal-speed count, before "Listen to that!".
- Writes words_final.json (timings shifted after the insert), env.npy (narration loudness per frame, 30 fps),
  loop_hits.json (drum-loop hit times) and ../../episode-03/audio/episode3_mix.mp3.
usage: python3 prep.py
"""
import json, os, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.join(HERE, "../../episode-03")
SR = 44100; FPS = 30
INS_AFTER = "and."          # last word of the normal-speed bars
BPM = 110; E8 = 60 / BPM / 2; BARS = 2; LEAD = 0.25; GAP = 5.0

words = json.load(open(f"{EP}/captions/word_timings.json"))
# find "Listen" (start of "Listen to that!") and insert in the silence before it
li = next(i for i, w in enumerate(words) if w["text"].lower().startswith("listen"))
t_ins = round((words[li - 1]["end"] + words[li]["start"]) / 2, 3)

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{EP}/audio/narration_final.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
nar = np.frombuffer(raw, np.float32).copy()
i_ins = int(t_ins * SR)

# ---------- drum synth ----------
rng = np.random.default_rng(3)
def env(n, d): t = np.arange(n) / SR; return np.exp(-t / d)
def kick():
    n = int(.45 * SR); t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t / .045); ph = 2 * np.pi * np.cumsum(f) / SR
    click = rng.standard_normal(n) * env(n, .003) * .35
    return (np.sin(ph) * env(n, .16) + click) * .95
def snare():
    n = int(.3 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n); noise = noise - np.convolve(noise, np.ones(6) / 6, "same")   # crude highpass
    tone = np.sin(2 * np.pi * 185 * t) * env(n, .06) * .55
    return (noise * env(n, .085) * .6 + tone) * .85
def hat():
    n = int(.09 * SR)
    noise = rng.standard_normal(n)
    for _ in range(3): noise = noise - np.convolve(noise, np.ones(3) / 3, "same")
    return noise * env(n, .018) * .16
K, S, Hh = kick(), snare(), hat()
loop = np.zeros(int(GAP * SR), np.float32); hits = []
for i in range(8 * BARS):
    t = LEAD + i * E8; p = int(t * SR)
    pcs = ["hihat"] + (["kick"] if i % 8 in (0, 4) else []) + (["snare"] if i % 8 in (2, 6) else [])
    for pc, smp in (("hihat", Hh), ("kick", K), ("snare", S)):
        if pc in pcs: loop[p:p + len(smp)] += smp[:len(loop) - p]
    hits.append({"t": round(t_ins + t, 4), "col": i % 8, "pieces": pcs})
pk = np.max(np.abs(nar)); loop *= (pk * .9) / np.max(np.abs(loop))
fade = int(.4 * SR); loop[-fade:] *= np.linspace(1, 0, fade) ** 2

mix = np.concatenate([nar[:i_ins], loop, nar[i_ins:], np.zeros(int(1.5 * SR), np.float32)])
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libmp3lame", "-b:a", "192k",
                f"{EP}/audio/episode3_mix.mp3"], input=mix.astype(np.float32).tobytes(), check=True)

# ---------- shifted words ----------
out = []
for w in words:
    d = GAP if w["start"] >= t_ins else 0
    out.append({"text": w["text"], "start": round(w["start"] + d, 3), "end": round(w["end"] + d, 3)})
json.dump(out, open(f"{HERE}/words_final.json", "w"), indent=0)
json.dump({"t_ins": t_ins, "gap": GAP, "bpm": BPM, "hits": hits, "total": round(len(mix) / SR, 3)}, open(f"{HERE}/loop_hits.json", "w"), indent=1)

# ---------- narration loudness envelope (zeros during the loop, so the mascot doesn't talk over drums) ----------
narz = np.concatenate([nar[:i_ins], np.zeros(len(loop), np.float32), nar[i_ins:], np.zeros(int(1.5 * SR), np.float32)])
hop = SR // FPS; nfr = len(narz) // hop
rms = np.sqrt(np.mean(narz[:nfr * hop].reshape(nfr, hop) ** 2, axis=1))
e = np.clip(rms / np.percentile(rms[rms > 1e-3], 95), 0, 1)
np.save(f"{HERE}/env.npy", e.astype(np.float32))
print("insert at", t_ins, "total", round(len(mix) / SR, 2), "frames", nfr)
