"""Episode 3 YouTube Shorts (1080x1920), fully animated, loop-back endings.
Reuses the Episode 3 kit, sticks and beat chart (ep3.py); per-Short beat events are swapped into ep3's globals.
usage: python3 shorts3.py still N T scale out.png
       python3 shorts3.py render N out.mp4 [scale fps crf]
"""
import sys, os, math, json, random, subprocess, re
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import ep3
from lib import *
from ep3 import (kick_side, hihat, sfx, rings, clock, beat_chart, ep3_kit, lap_kid, PATTERN, GOLD_D, HH_C, SN_C, KK_C)

W, H = 1080, 1920
FPS = 30
AUD = {1: "short1_take1.mp3", 2: "short2.mp3"}
ADIR = os.path.join(HERE, "../../../episode-03/shorts/audio")
WORDS = {int(k): v for k, v in json.load(open(os.path.join(HERE, "words.json"))).items()}
DUR = {n: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 os.path.join(ADIR, AUD[n])], capture_output=True, text=True).stdout) for n in AUD}
ENV = {n: np.load(os.path.join(HERE, f"env{n}.npy")) for n in AUD}
def env_at(n, t):
    i = int(t * FPS); e = ENV[n]
    return float(np.mean(e[max(0, i - 1):i + 1])) if 0 <= i < len(e) else 0.0
def nm(s): return re.sub(r"[^a-z0-9'\-]", "", s.lower())
def wt(n, word, after=0.0):
    for w in WORDS[n]:
        if w["start"] >= after - 1e-6 and nm(w["text"]) == nm(word): return w["start"]
    raise KeyError((n, word, after))

# ---------- per-Short beat events (fed to ep3's chart/kit) ----------
def build_events(n):
    ws = WORDS[n]; bars, ev = [], []
    first = ws[:8]
    lay = {'hihat'} if n == 1 else {'hihat', 'kick'}
    bars.append(dict(t0=first[0]["start"], t1=first[-1]["end"], words=[(w["start"], c) for c, w in enumerate(first)], layer=lay))
    for c, w in enumerate(first): ev.append((w["start"], c, {p for p in lay if c in PATTERN[p]}))
    if n == 1:      # "Eight even taps": 8 even hi-hat ticks under that line
        t0 = wt(1, "Eight"); step = (wt(1, "ticking.") + .3 - t0) / 8
        ts = [t0 + i * step for i in range(8)]
        bars.append(dict(t0=ts[0], t1=ts[-1] + .3, words=[(x, i) for i, x in enumerate(ts)], layer={'hihat'}))
        for i, x in enumerate(ts): ev.append((x, i, {'hihat'}))
        TAPS[1] = ts
    else:           # "Keep the hi-hat ticking ... same moment": steady hi-hat + kick on 1 and 3
        t0 = wt(2, "Keep"); t1 = wt(2, "Now", 19); step = .36; i = 0; x = t0
        cur = []
        while x < t1 - .2:
            c = i % 8; ev.append((x, c, {'hihat'} | ({'kick'} if c in (0, 4) else set()))); cur.append((x, c)); x += step; i += 1
            if c == 7: bars.append(dict(t0=cur[0][0], t1=cur[-1][0] + .3, words=cur, layer={'hihat', 'kick'})); cur = []
        if cur: bars.append(dict(t0=cur[0][0], t1=cur[-1][0] + .3, words=cur, layer={'hihat', 'kick'}))
    ev.sort(key=lambda e: e[0])
    return bars, {p: [e[0] for e in ev if p in e[2]] for p in PATTERN}
TAPS = {}
EVENTS = {n: build_events(n) for n in AUD}
def use(n):
    ep3.BARS, ep3.PIECE_T = EVENTS[n]

# ---------- background / header / captions ----------
_R = random.Random(5)
BG = [(_R.uniform(0, W), _R.uniform(0, H), _R.uniform(.6, 1.2), _R.uniform(10, 26), _R.choice([0, 1, 2]), _R.uniform(0, 6.28)) for _ in range(30)]
def background(ctx, t, tint=None):
    g = cairo.RadialGradient(W / 2, H * .42, 100, W / 2, H * .5, 1500)
    c0, c1 = (0.22, 0.62, 1.0), (0.05, 0.38, 0.92)
    if tint: c0 = lerpc(c0, tint, .35); c1 = lerpc(c1, tint, .25)
    g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); ctx.set_source(g); ctx.paint()
    ctx.save(); ctx.translate(W / 2, H * .42); ctx.rotate(t * .05)
    for i in range(16):
        a = i * 2 * math.pi / 16
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 2200, a, a + math.pi / 32); ctx.close_path(); ctx.set_source_rgba(1, 1, 1, .035); ctx.fill()
    ctx.restore()
    for (x, y, s, sp, k, ph) in BG:
        yy = (y - t * sp) % (H + 200) - 100; xx = x + wob(t, .08, 30, ph)
        if k == 0: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph))
        elif k == 1: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph), double=True)
        else: star(ctx, xx, yy, 18 * s, WHITE, None, alpha=.13, rot=t * .5 + ph)

CAP = 96
KEYS = {1: {"one", "two", "three", "four", "and", "secret", "clock", "count", "counts", "eight", "beat", "rock"},
        2: {"boom", "kick", "pedal", "beater", "center", "hi-hat", "foot", "together", "one", "three", "sound"}}
def chunks(n):
    out, cur = [], []
    for w in WORDS[n]:
        cur.append(w)
        if len(cur) >= 3 or w["text"][-1] in ".,!?:": out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CH = {n: chunks(n) for n in AUD}
def captions(ctx, n, t, y=1500):
    ch = CH[n]; cur = None
    for i, c in enumerate(ch):
        end = ch[i + 1][0]["start"] if i + 1 < len(ch) else DUR[n] + 1
        if c[0]["start"] - 0.05 <= t < end: cur = c
    if cur is None: return
    sp = CAP * .5
    ws = [text_width(ctx, w["text"], CAP) for w in cur]
    total = sum(ws) + sp * (len(ws) - 1)
    lines = [list(range(len(cur)))]
    if total > W - 160 and len(cur) > 1:
        lines = [[0], list(range(1, len(cur)))] if len(cur) == 2 else [[0, 1], [2]]
    ap = back(prog(t, cur[0]["start"] - .05, .2))
    for li, ln in enumerate(lines):
        lw = sum(ws[i] for i in ln) + sp * (len(ln) - 1)
        x = W / 2 - lw / 2; yy = y + li * CAP * 1.15
        for i in ln:
            w = cur[i]; key = re.sub(r"[^a-z\-]", "", w["text"].lower()) in KEYS[n]
            active = w["start"] <= t < w["end"] + .08; done = t >= w["end"] + .08
            if active:
                b = math.sin(math.pi * clamp(prog(t, w["start"], .2)))
                sc = 1.03 + .09 * b; col = PINK if key else YELLOW; dy = -12 * b
            else:
                sc = 1.0; dy = 0; col = (YELLOW if key else WHITE) if done else (0.85, 0.9, 1.0)
            text(ctx, w["text"], x + ws[i] / 2, yy + dy, CAP, col, NAVY, lw=16, scale=sc * lerp(.7, 1, ap), alpha=clamp(ap * 1.5))
            x += ws[i] + sp

def header(ctx, n, t):
    label(ctx, "DRUMS IN 5 MIN", 400, 150, 42, PINK, WHITE, rot=-.02)
    label(ctx, "FULL LESSON: EPISODE 3", 400, 225, 28, WHITE, NAVY, rot=-.02)
    e = env_at(n, t); drum(ctx, 930, 200, .42, t, mouth=e * 1.1, look=-.6)
def sticker(ctx, t, t0, s, x, y, size=58, bg=YELLOW, fg=NAVY, rot=-.03):
    label(ctx, s, x, y, size, bg, fg, scale=pop(t, t0), rot=rot + wob(t, .5, .02))
def hold(ctx, s, x, y, size, bg, fg, t, rot=-.03):
    label(ctx, s, x, y, size, bg, fg, scale=1.0, rot=rot + wob(t, .5, .02))

def big_counts(ctx, t, n, y, hl_nums=None, hl_ands=None):
    """1 & 2 & 3 & 4 & in big type; pops with the spoken counting in the first bar."""
    labs = ["1", "&", "2", "&", "3", "&", "4", "&"]; xs = [135 + i * 116 for i in range(8)]
    b = ep3.BARS[0]
    for i, (lab, x) in enumerate(zip(labs, xs)):
        tw = b["words"][i][0]; sc = 1 + .4 * max(0, 1 - (t - tw) / .3) if t >= tw and t < b["t1"] + .5 else 1
        col = WHITE
        if hl_nums is not None and lab != "&" and t >= hl_nums: col = YELLOW
        if hl_ands is not None and lab == "&" and t >= hl_ands: col = PINK
        text(ctx, lab, x, y, 120 if lab != "&" else 92, col, NAVY, lw=16, scale=sc)

# ---------- SHORT 1: the 1-2-3-4 trick ----------
def short1(ctx, t):
    n = 1; use(n)
    tthat = wt(n, "That's"); tfour = wt(n, "four", 6); tand = wt(n, "and", 8); tnow = wt(n, "Now"); tcount = wt(n, "Count"); tso = wt(n, "So")
    loop_t = DUR[n] - 0.9
    if t < tthat - .2 or t >= tso - .1:
        ep3_kit(ctx, 540, 760, .62, t)
        beat_chart(ctx, 540, 1180, t, .86, rows_on=('hihat',))
        if t < tthat: hold(ctx, "THE 1-2-3-4 TRICK", 540, 360, 64, PINK, WHITE, t)
        else: sticker(ctx, t, tso, "COUNT WITH ME!", 540, 360, 64, YELLOW, NAVY)
        return
    if t < tnow - .2:
        sticker(ctx, t, tthat, "THE DRUMMER'S SECRET", 540, 360, 56, YELLOW, NAVY)
        ctx.save(); ctx.translate(540, 720); s = 1 + .04 * math.sin(t * 3); sscale(ctx, s, s)
        circle(ctx, 0, 0, 190, (1.0, .82, .66), NAVY, LW)                          # simple head with a "thought"
        ctx.new_path(); ctx.arc(0, -20, 196, math.pi, math.pi * 2); ctx.close_path(); fill_stroke(ctx, (.35, .2, .1), NAVY, LW)
        for dx in (-60, 60): circle(ctx, dx, -10, 16, NAVY, None)
        ctx.new_path(); ctx.arc(0, 40, 50, .15 * math.pi, .85 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(8); ctx.stroke()
        ctx.restore()
        big_counts(ctx, t, n, 1080, hl_nums=tfour, hl_ands=tand)
        if t > tfour: sticker(ctx, t, tfour, "4 COUNTS", 300, 1250, 50, YELLOW, NAVY, -.04)
        if t > tand: sticker(ctx, t, tand, "+ \"AND\" IN BETWEEN", 700, 1250, 44, PINK, WHITE, .04)
        return
    if t < tcount - .2:
        lap_kid(ctx, 540, 900, t)
        sticker(ctx, t, tnow, "TAP IT ON YOUR LEG!", 540, 360, 56, GREEN, WHITE)
        k = sum(1 for x in TAPS[1] if t >= x)
        if k: text(ctx, f"{k}", 880, 640, 130, YELLOW, NAVY, lw=18, scale=1 + .3 * max(0, 1 - (t - TAPS[1][k - 1]) / .25))
        if t > wt(n, "clock"): clock(ctx, 200, 640, 100, t, -math.pi / 2 + k * math.pi / 4)
        sticker(ctx, t, wt(n, "Eight"), "8 EVEN TAPS", 540, 1300, 50, YELLOW, NAVY, .03) if t > wt(n, "Eight") else None
        return
    ep3_kit(ctx, 540, 760, .62, t, glow={'hihat': 1})
    beat_chart(ctx, 540, 1180, t, .86, rows_on=('hihat',), highlight_row='hihat', follow=False)
    sticker(ctx, t, tcount, "COUNT OUT LOUD", 540, 360, 60, PINK, WHITE)
    tc = wt(n, "clock", 17)
    if t > tc: sticker(ctx, t, tc, "THE CLOCK OF EVERY ROCK BEAT", 540, 450, 40, YELLOW, NAVY, .03)

# ---------- SHORT 2: add the boom ----------
def short2(ctx, t):
    n = 2; use(n)
    tthat = wt(n, "That's"); tone = wt(n, "one", 5); tthree = wt(n, "three.", 5); tyour = wt(n, "Your"); tkeep = wt(n, "Keep"); tnow = wt(n, "Now", 19)
    if t < tthat - .2 or t >= tnow - .1:
        ep3_kit(ctx, 540, 760, .62, t)
        beat_chart(ctx, 540, 1180, t, .86, rows_on=('hihat', 'kick'))
        if t < tthat: hold(ctx, "ADD THE BOOM!", 540, 360, 66, ORANGE, WHITE, t)
        else: sticker(ctx, t, tnow, "SAY IT WITH ME!", 540, 360, 64, YELLOW, NAVY)
        return
    if t < tyour - .2:
        hc = (0,) if tone <= t < tthree else ((0, 4) if t >= tthree else ())
        ep3_kit(ctx, 540, 760, .62, t, glow={'kick': 1})
        beat_chart(ctx, 540, 1180, t, .86, rows_on=('hihat', 'kick'), highlight_row='kick', highlight_cols=hc, follow=False)
        sticker(ctx, t, tthat, "KICK ON 1 AND 3", 540, 360, 62, ORANGE, WHITE)
        return
    if t < tkeep - .2:
        press = 0.0
        for k in (wt(n, "presses"), wt(n, "forward")):
            if k <= t < k + .3: press = max(press, smooth(prog(t, k, .2)))
            elif k + .3 <= t < k + .8: press = max(press, 1 - smooth(prog(t, k + .3, .5)))
        kick_side(ctx, 540, 860, t, press, 1.45 * pop(t, tyour - .2))
        sticker(ctx, t, tyour, "RIGHT FOOT PRESSES THE PEDAL", 540, 360, 42, PINK, WHITE)
        tc = wt(n, "center")
        if t > tc: sticker(ctx, t, tc, "BEATER HITS THE CENTER!", 540, 1300, 50, YELLOW, NAVY, .03)
        return
    ep3_kit(ctx, 540, 760, .62, t, glow={'hihat': .7, 'kick': .7})
    beat_chart(ctx, 540, 1180, t, .86, rows_on=('hihat', 'kick'))
    sticker(ctx, t, tkeep, "HI-HAT KEEPS TICKING", 540, 360, 56, TEAL, WHITE)
    ts = wt(n, "same")
    if t > ts: sticker(ctx, t, ts, "SAME MOMENT = ONE SOUND!", 540, 450, 44, YELLOW, NAVY, .03)

SHORTS = {1: (short1, TEAL), 2: (short2, PINK)}
def frame(ctx, n, t):
    fn, tint = SHORTS[n]
    background(ctx, t, tint); fn(ctx, t); header(ctx, n, t); captions(ctx, n, t)
def surface(n, t, scale=1.0):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale)); ctx = cairo.Context(s)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo); sscale(ctx, scale, scale); frame(ctx, n, t); return s

if __name__ == "__main__":
    if sys.argv[1] == "still":
        n, t, sc, out = int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        surface(n, t, sc).write_to_png(out)
    else:
        n, out = int(sys.argv[2]), sys.argv[3]
        sc = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        fps = int(sys.argv[5]) if len(sys.argv) > 5 else FPS
        crf = sys.argv[6] if len(sys.argv) > 6 else "18"
        w, h = int(W * sc) // 2 * 2, int(H * sc) // 2 * 2
        nf = int(DUR[n] * fps)
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{int(W * sc)}x{int(H * sc)}", "-r", str(fps), "-i", "-",
                              "-i", os.path.join(ADIR, AUD[n]), "-map", "0:v", "-map", "1:a", "-vf", f"scale={w}:{h}",
                              "-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                              "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(nf): p.stdin.write(surface(n, f / fps, sc).get_data())
        p.stdin.close(); p.wait()
