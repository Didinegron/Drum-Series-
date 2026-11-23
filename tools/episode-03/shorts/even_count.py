"""Re-time the spoken count at the start of each Short onto an even grid (no new narration needed).
Each counted word ("one", "and", "two"...) is cut out and placed at an even spacing; total bar length is unchanged,
so everything after the count stays exactly where it was. Originals are kept as *_uneven.mp3.
usage: python3 even_count.py
"""
import json, os, shutil, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "../../../episode-03/shorts/audio")
SR = 44100
AUD = {1: "short1_take1.mp3", 2: "short2.mp3"}
words = {int(k): v for k, v in json.load(open(f"{HERE}/words.json")).items()}
for n, f in AUD.items():
    src = f"{A}/{f}"; orig = src.replace(".mp3", "_uneven.mp3")
    if not os.path.exists(orig): shutil.copy(src, orig)
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", orig, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32).copy()
    ws = words[n][:8]
    if "orig_count" not in ws[0]:                          # keep the transcription's own times for re-runs
        for w in ws: w["orig_count"] = [w["start"], w["end"]]
    for w in ws: w["start"], w["end"] = w["orig_count"]
    def loud_onset(a, b):
        """time (s, from a) where the word gets loud = where a listener hears the beat"""
        seg = x[a:b]; hop = 80; r = np.sqrt((seg[:len(seg) // hop * hop].reshape(-1, hop) ** 2).mean(1))
        r = np.convolve(r, np.ones(3) / 3, "same"); k = int(np.argmax(r > .4 * r.max())); return k * hop / SR
    # cut points = the quietest moment between two words (not the transcript times, which can clip a consonant)
    hopq = int(.005 * SR)
    def quietest(t0, t1):
        a, b = int(t0 * SR), int(t1 * SR); seg = x[a:b]
        r = np.sqrt((seg[:len(seg) // hopq * hopq].reshape(-1, hopq) ** 2).mean(1)); r = np.convolve(r, np.ones(3) / 3, "same")
        return a + int(np.argmin(r)) * hopq
    bounds = [int(max(0, ws[0]["start"] - .06) * SR)]
    for k in range(7):
        bounds.append(quietest(ws[k]["end"] - .05, ws[k + 1]["start"] + .05))
    bounds.append(int((ws[7]["end"] + .12) * SR))
    segs = [(bounds[k], bounds[k + 1], loud_onset(bounds[k], bounds[k + 1])) for k in range(8)]
    beats = [a / SR + o for a, b, o in segs]
    step = (beats[7] - beats[0]) / 7
    cut = bounds[8]
    out = x.copy(); out[:cut] = 0
    fade = int(.012 * SR)
    prev_end = 0
    for k, (w, (a, b, o)) in enumerate(zip(ws, segs)):
        seg = x[a:b].copy()
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        beat = beats[0] + k * step                         # even grid, measured on the loud part of each word
        g = max(0, int((beat - o) * SR))
        out[g:g + len(seg)] += seg[:len(out) - g]          # edges are quiet, so small overlaps just blend
        prev_end = max(prev_end, g + len(seg))
        dur = min(w["end"] - w["start"], step - .05)
        w["start"] = round(beat - .04, 3); w["end"] = round(w["start"] + dur, 3)
    cut = max(cut, prev_end)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libmp3lame", "-b:a", "192k", src],
                   input=out.astype(np.float32).tobytes(), check=True)
    print(n, "step", round(step, 3), [round(b_, 2) for b_ in beats])
json.dump(words, open(f"{HERE}/words.json", "w"), indent=0)
# refresh lip-sync envelopes
for n, f in AUD.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{A}/{f}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); hop = SR // 30; nf = len(x) // hop
    r = np.sqrt((x[:nf * hop].reshape(nf, hop) ** 2).mean(1)); np.save(f"{HERE}/env{n}.npy", np.clip(r / np.percentile(r[r > 1e-3], 95), 0, 1).astype(np.float32))
