"""Episode 2 YouTube Shorts (1080x1920), fully animated, loop-back endings.
usage: python3 shorts2.py still N T scale out.png
       python3 shorts2.py render N out.mp4 [scale fps crf]
"""
import sys, os, math, json, random, subprocess, re
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
EP2 = os.path.join(HERE, "..", "ep2")
sys.path.insert(0, EP2)
import ep2
from lib import *
from ep2 import kick, kick_side, tom, hihat, cymbal, clock, sfx, rings, stand, GOLD, GOLD_D, TEAL_D, BLUE_D

W, H = 1080, 1920
FPS = 30
WORDS = {int(k): v for k, v in json.load(open(os.path.join(HERE, "words.json"))).items()}
DUR = {n: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 os.path.join(HERE, f"s{n}.mp3")], capture_output=True, text=True).stdout) for n in (1, 2, 3)}
ENV = {n: np.load(os.path.join(HERE, f"env{n}.npy")) for n in (1, 2, 3)}

def env_at(n, t):
    i = int(t * FPS); e = ENV[n]
    return float(np.mean(e[max(0, i - 1):i + 1])) if 0 <= i < len(e) else 0.0

def nm(s): return re.sub(r"[^a-z0-9'\-]", "", s.lower())
def wt(n, word, after=0.0):
    for w in WORDS[n]:
        if w["start"] >= after - 1e-6 and nm(w["text"]) == nm(word): return w["start"]
    raise KeyError((n, word, after))

# ------------------------------------------------------------------ background
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

# ------------------------------------------------------------------ captions (big, 1-3 words)
CAP = 96
KEYS = {1: {"boom", "crack", "heartbeat", "kick", "snare", "beat", "clap"},
        2: {"secret", "clock", "hi-hat", "tick", "sizzle", "groove", "time"},
        3: {"fireworks", "ping", "crash", "ride", "groove", "cymbal", "cymbals"}}
def chunks(n):
    out, cur = [], []
    for w in WORDS[n]:
        cur.append(w)
        if len(cur) >= 3 or w["text"][-1] in ".,!?:": out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CH = {n: chunks(n) for n in (1, 2, 3)}

def captions(ctx, n, t, y=1440):
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
    label(ctx, "FULL LESSON: EPISODE 2", 400, 225, 28, WHITE, NAVY, rot=-.02)
    e = env_at(n, t); drum(ctx, 930, 200, .42, t, mouth=e * 1.1, look=-.6)

def sticker(ctx, t, t0, s, x, y, size=58, bg=YELLOW, fg=NAVY, rot=-.03):
    label(ctx, s, x, y, size, bg, fg, scale=pop(t, t0), rot=rot + wob(t, .5, .02))
def hold(ctx, s, x, y, size, bg, fg, t, rot=-.03):
    label(ctx, s, x, y, size, bg, fg, scale=1.0, rot=rot + wob(t, .5, .02))
def decay(t, k, d=.35): return max(0.0, 1 - prog(t, k, d)) if t >= k else 0.0

def heart(ctx, x, y, s):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    ctx.new_path(); ctx.move_to(0, 60); ctx.curve_to(-120, -20, -60, -110, 0, -50); ctx.curve_to(60, -110, 120, -20, 0, 60); fill_stroke(ctx, PINK, NAVY, LW)
    ctx.restore()

def snare_with_stick(ctx, x, y, s, t, hits, bnc=0.0):
    tom(ctx, x, y, s, t, RED, bounce=bnc)
    stand(ctx, x, y + 100 * s, y + 300 * s, s)
    hit = 0.0
    for k in hits:
        if t >= k: hit = max(hit, 1 - clamp(abs(t - k - .1) / .18))
    head_y = y - 75 * s - bnc
    tx, ty = x + 20 * s, lerp(head_y - 65 * s, head_y - 2, hit)
    bx, by = x + 230 * s, lerp(head_y - 150 * s, head_y - 115 * s, hit)
    stick(ctx, bx, by, math.atan2(ty - by, tx - bx), math.hypot(tx - bx, ty - by) - 15 * s, 24 * s / 1.2, t=t)

# ------------------------------------------------------------------ SHORT 1: boom and crack
def short1(ctx, t):
    n = 1
    bc = [wt(n, "Boom,"), wt(n, "crack,"), wt(n, "boom,", 1.5), wt(n, "crack.")]
    tthat = wt(n, "That's"); tkick = wt(n, "The"); tsn = wt(n, "The", 15); tput = wt(n, "Put"); tso = wt(n, "So")
    loop_t = DUR[n] - 0.9
    if t < tthat - .2 or t >= loop_t:
        # hook (also the loop-back ending)
        beat = 0.0; kb = 0.0; sb = 0.0
        if t < tthat:
            for i, k in enumerate(bc):
                d = decay(t, k)
                if i % 2 == 0: kb = max(kb, d)
                else: sb = max(sb, d)
        else:
            ph = ((t - loop_t) * 2.2) % 1; kb = max(0, 1 - ph * 3)
        kick(ctx, 330, 800, .75, t, m=.6 * kb, boom=kb)
        tom(ctx, 790, 840, 1.0, t, RED, m=.4 * sb, bounce=25 * sb)
        heart(ctx, 540, 520, 1.2 + .25 * max(kb, sb))
        for i, k in enumerate(bc): sfx(ctx, t, k, ["BOOM!", "CRACK!"][i % 2], [330, 790][i % 2], 1180, 62, [ORANGE, RED][i % 2], [-.06, .06][i % 2], .7)
        return
    if t < tkick - .2:
        heart(ctx, 540, 760, 2.0 + .15 * abs(math.sin(t * 5)))
        sticker(ctx, t, tthat, "THE HEARTBEAT", 540, 340, 62, PINK, WHITE)
        sticker(ctx, t, wt(n, "every"), "OF EVERY SONG!", 540, 1200, 56, YELLOW, NAVY, .03)
        for i in range(5):
            ph = (t * .6 + i / 5) % 1
            note(ctx, 540 + 330 * math.cos(i * 1.3) * ph, 760 - 380 * ph, 1.5, [PINK, WHITE, YELLOW][i % 3], 1 - ph, wob(t, 1, .3), i % 2 == 0)
    elif t < tsn - .2:
        tpress = wt(n, "press"); tthump = wt(n, "thumps")
        press = max(decay(t, tpress + .15, .5), decay(t, tthump, .5))
        bm = decay(t, tthump + .1, .6)
        kick(ctx, 540, 620, 1.0 + .05 * bm, t, m=.7 * bm, boom=bm)
        sticker(ctx, t, tkick, "BOOM = KICK DRUM", 540, 340, 56, ORANGE, WHITE)
        if t > tpress - .3: kick_side(ctx, 540, 1060, t, press, .85 * pop(t, tpress - .3))
        if t > tthump: rings(ctx, 540, 620, t, tthump + .1, WHITE, 4, 200, 520, 1.1); sfx(ctx, t, tthump + .1, "BOOM!", 860, 420, 70, ORANGE, .08, 1.4)
        if t > wt(n, "right"): sticker(ctx, t, wt(n, "right"), "RIGHT FOOT", 540, 1340 - 60, 44, YELLOW, NAVY, .02)
    elif t < tput - .2:
        hits = [wt(n, "crack", 15), wt(n, "snare,"), wt(n, "clap.")]
        sb = max(decay(t, k, .3) for k in hits)
        snare_with_stick(ctx, 540, 840, 1.6, t, hits, bnc=20 * sb)
        sticker(ctx, t, tsn, "CRACK = SNARE", 540, 340, 58, RED, WHITE)
        for k in hits[:2]: sfx(ctx, t, k + .1, "CRACK!", 860, 470, 66, RED, -.08, 1.1)
        if t > hits[2]:
            for i in range(2):
                ph = (t * 2) % 1; text(ctx, "CLAP!", 200 + i * 680, 1130 - 30 * ph, 60, PINK, NAVY, alpha=1 - ph * .5, rot=(-1) ** i * .15)
    else:
        beat_t = t - tput; ph = (beat_t * 2.2) % 2
        kb = max(0, 1 - ph * 3) if ph < 1 else 0; sb = max(0, 1 - (ph - 1) * 3) if ph >= 1 else 0
        kick(ctx, 330, 800, .75, t, m=.6 * kb, boom=kb)
        tom(ctx, 790, 840, 1.0, t, RED, m=.4 * sb, bounce=25 * sb)
        heart(ctx, 540, 520, 1.2 + .25 * max(kb, sb))
        sticker(ctx, t, tput, "BOOM + CRACK = A BEAT!", 540, 340, 52, GREEN, WHITE)
        if t > tso: sticker(ctx, t, tso, "LISTEN FOR IT!", 540, 1200, 56, YELLOW, NAVY, .03)

# ------------------------------------------------------------------ SHORT 2: secret clock
def short2(ctx, t):
    n = 2
    tevery = wt(n, "Every"); twall = wt(n, "wall."); tits = wt(n, "It's", 4.5); tpress = wt(n, "Press"); tlift = wt(n, "Lift")
    ticks = [wt(n, "Tick,"), wt(n, "tick,"), wt(n, "tick,", 17.9), wt(n, "tick.")]
    tthat = wt(n, "That"); tbec = wt(n, "Because")
    loop_t = DUR[n] - 0.9
    if t < tevery - .2 or t >= loop_t:
        clock(ctx, 540, 760, 300, t)
        hold(ctx, "SECRET CLOCK", 540, 340, 70, PINK, WHITE, t)
        sfx(ctx, t, -0.4, "TICK!", 860, 470, 60, TEAL, .1, 1.5)
        return
    if t < tits - .2:
        clock(ctx, 540, 760, 300, t)
        sticker(ctx, t, tevery, "EVERY BAND HAS ONE", 540, 340, 54, YELLOW, NAVY)
        if t > twall:
            cross(ctx, 840, 520, 1.0, p=prog(t, twall, .4)); sticker(ctx, t, twall, "NOT ON THE WALL!", 540, 1200, 54, RED, WHITE, .03)
        return
    if t < tpress - .2: op = .5
    elif t < tlift: op = lerp(.5, 0, smooth(prog(t, tpress + .3, .4)))
    elif t < ticks[0] - .2: op = lerp(0, 1, smooth(prog(t, tlift + .3, .4)))
    else: op = .1
    if t < ticks[0] - .2:
        hihat(ctx, 540, 640, 1.45, t, open_=op)
        sticker(ctx, t, tits, "IT'S THE HI-HAT!", 540, 340, 60, GOLD_D, WHITE)
        if t < tpress - .2:
            sticker(ctx, t, wt(n, "two"), "2 SMALL CYMBALS", 540, 1290, 48, WHITE, NAVY, .02)
        elif t < tlift - .2:
            sticker(ctx, t, wt(n, "left"), "LEFT FOOT", 300, 1290, 46, ORANGE, WHITE, -.04)
            sticker(ctx, t, wt(n, "tight"), "TIGHT TICK", 780, 1290, 46, TEAL, WHITE, .04)
            sfx(ctx, t, wt(n, "tick."), "TICK!", 860, 520, 60, TEAL, .1, 1.0)
        else:
            sticker(ctx, t, wt(n, "loose,"), "OPEN = SIZZLE!", 540, 1290, 50, PINK, WHITE, .02)
            if t > wt(n, "sizzle."):
                ph = (t * 1.5) % 1; text(ctx, "tssss", 860 + 20 * ph, 560 - 40 * ph, 58, YELLOW, NAVY, alpha=1 - ph, rot=-.1)
        return
    tick_ang = -math.pi / 2
    for i, k in enumerate(ticks):
        if t >= k: tick_ang = -math.pi / 2 + (i + 1) * math.pi / 6
    if t < tthat - .2:
        hihat(ctx, 300, 700, .95, t, open_=.1)
        clock(ctx, 780, 700, 210, t, tick_ang)
        for i, k in enumerate(ticks): sfx(ctx, t, k, "TICK!", 300 + (i - 1.5) * 110, 470, 46, TEAL, (-1) ** i * .1, .7)
        hold(ctx, "IT'S THE HI-HAT!", 540, 340, 60, GOLD_D, WHITE, t)
    else:
        clock(ctx, 540, 760, 300, t)
        sticker(ctx, t, tthat, "KEEPS THE SONG ON TIME", 540, 340, 50, YELLOW, NAVY)
        if t > tbec: sticker(ctx, t, tbec, "BEHIND EVERY GROOVE...", 540, 1200, 50, PINK, WHITE, .03)

# ------------------------------------------------------------------ SHORT 3: fireworks or steady ping
def short3(ctx, t):
    n = 3
    tthose = wt(n, "Those"); tcrash = wt(n, "The"); thit = wt(n, "Hit"); tride = wt(n, "The", 14.3); tping = wt(n, "ping", 18); tso = wt(n, "So")
    loop_t = DUR[n] - 0.9
    def pair(lab=True, hook=False):
        stand(ctx, 290, 760, 1180); stand(ctx, 790, 760, 1180)
        cymbal(ctx, 290, 760, 210, t, GOLD, True, wobble=.7 if hook else .2)
        cymbal(ctx, 790, 760, 230, t, (0.92, 0.72, 0.30), True, wobble=.08, look=-.3)
        if hook:
            for k in range(2): confetti(ctx, 290, 600, ((t + k * .9) % 1.8), seed=40 + k, n=30, spread=260, dur=1.8)
            ph = (t * 1.6) % 1; text(ctx, "PING!", 790, 520 - 40 * ph, 54, TEAL, NAVY, alpha=1 - ph)
    if t < tthose - .2 or t >= loop_t:
        pair(hook=True)
        hold(ctx, "FIREWORKS?", 290, 360, 50, PINK, WHITE, t, -.05)
        hold(ctx, "STEADY PING?", 790, 360, 50, TEAL, WHITE, t, .05)
        return
    if t < tcrash - .2:
        pair()
        sticker(ctx, t, tthose, "THE 2 BIGGEST CYMBALS", 540, 340, 50, YELLOW, NAVY)
        return
    if t < tride - .2:
        wb = decay(t, thit + .1, 2.0)
        stand(ctx, 540, 720, 1250); cymbal(ctx, 540, 720, 380, t, GOLD, True, wobble=wb, m=.5 * wb)
        sticker(ctx, t, tcrash, "CRASH CYMBAL", 540, 340, 62, PINK, WHITE)
        if t > thit:
            for k in range(3): confetti(ctx, 260 + k * 280, 520, t - thit - k * .35, seed=60 + k, n=40, spread=360, dur=2.0)
            sfx(ctx, t, thit + .1, "CRASH!", 820, 470, 70, PINK, -.08, 1.5)
        if t > wt(n, "big"): sticker(ctx, t, wt(n, "big"), "= FIREWORKS!", 540, 1290, 56, YELLOW, NAVY, .03)
        return
    if t < tso - .2:
        stand(ctx, 540, 720, 1250); cymbal(ctx, 540, 720, 420, t, (0.92, 0.72, 0.30), True, wobble=.12, look=-.3)
        sticker(ctx, t, tride, "RIDE CYMBAL", 540, 340, 62, TEAL, WHITE)
        if t > wt(n, "biggest", 15): sticker(ctx, t, wt(n, "biggest", 15), "THE BIGGEST", 820, 1050, 44, WHITE, NAVY, .05)
        if t > tping:
            ph = ((t - tping) % .6) / .6
            text(ctx, "PING!", 820 + wob(t, .5, 20), 520 - 50 * ph, 64, TEAL, NAVY, alpha=1 - ph)
            sticker(ctx, t, tping, "= STEADY GROOVE", 540, 1290, 54, YELLOW, NAVY, -.02)
        return
    pair()
    sticker(ctx, t, tso, "ASK YOURSELF...", 540, 340, 58, YELLOW, NAVY)

SHORTS = {1: (short1, ORANGE), 2: (short2, GOLD), 3: (short3, PURPLE)}

def frame(ctx, n, t):
    fn, tint = SHORTS[n]
    background(ctx, t, tint)
    fn(ctx, t)
    header(ctx, n, t)
    captions(ctx, n, t)

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
                              "-i", os.path.join(HERE, f"s{n}.mp3"), "-map", "0:v", "-map", "1:a", "-vf", f"scale={w}:{h}",
                              "-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                              "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(nf): p.stdin.write(surface(n, f / fps, sc).get_data())
        p.stdin.close(); p.wait()
