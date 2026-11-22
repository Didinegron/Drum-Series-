"""Vertical YouTube Shorts (1080x1920) for the drum lessons.
usage: python3 shorts.py still N T out.png [scale]
       python3 shorts.py render N out.mp4
"""
import sys, os, math, json, random, subprocess, re
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.join(HERE, "..", "anim")
sys.path.insert(0, ANIM)
from lib import *
from photo import photo_card, video_card

W, H = 1080, 1920
FPS = 30
PH = os.path.join(HERE, "..", "photos") + "/"
WORDS = {int(k): v for k, v in json.load(open(os.path.join(HERE, "words.json"))).items()}
DUR = {1: 22.047, 2: 19.409, 3: 21.002}
ENV = {n: np.load(os.path.join(HERE, f"env{n}.npy")) for n in (1, 2, 3)}

def env_at(n, t):
    i = int(t * FPS); e = ENV[n]
    return float(np.mean(e[max(0, i - 1):i + 1])) if 0 <= i < len(e) else 0.0

def wt(n, word, after=0.0):
    k = re.sub(r"[^a-z0-9']", "", word.lower())
    for w in WORDS[n]:
        if w["start"] >= after - 1e-6 and re.sub(r"[^a-z0-9']", "", w["text"].lower()) == k:
            return w["start"]
    raise KeyError(word)

# ------------------------------------------------------------------ background
_R = random.Random(5)
BG = [(_R.uniform(0, W), _R.uniform(0, H), _R.uniform(.6, 1.2), _R.uniform(10, 26), _R.choice([0, 1, 2]), _R.uniform(0, 6.28)) for _ in range(30)]
def background(ctx, t, tint=None):
    g = cairo.RadialGradient(W / 2, H * 0.42, 100, W / 2, H * 0.5, 1500)
    c0, c1 = (0.22, 0.62, 1.0), (0.05, 0.38, 0.92)
    if tint: c0 = lerpc(c0, tint, .35); c1 = lerpc(c1, tint, .25)
    g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); ctx.set_source(g); ctx.paint()
    ctx.save(); ctx.translate(W / 2, H * .42); ctx.rotate(t * .05)
    for i in range(16):
        a = i * 2 * math.pi / 16
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 2200, a, a + math.pi / 32); ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, .035); ctx.fill()
    ctx.restore()
    for (x, y, s, sp, k, ph) in BG:
        yy = (y - t * sp) % (H + 200) - 100; xx = x + wob(t, .08, 30, ph)
        if k == 0: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph))
        elif k == 1: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph), double=True)
        else: star(ctx, xx, yy, 18 * s, WHITE, None, alpha=.13, rot=t * .5 + ph)

# ------------------------------------------------------------------ captions (big, 1-3 words)
CAP = 96
KEYS = {1: {"tight", "bounce", "mistake", "bird", "never"}, 2: {"balance", "third", "pinch", "fulcrum", "secret"},
        3: {"drop", "bounces", "relaxed", "thuds", "loosen", "minute"}}
def chunks(n):
    out, cur = [], []
    for w in WORDS[n]:
        cur.append(w)
        if len(cur) >= 3 or w["text"][-1] in ".,!?:":
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CH = {n: chunks(n) for n in (1, 2, 3)}

def captions(ctx, n, t, y=1380):
    ch = CH[n]; cur = None
    for i, c in enumerate(ch):
        end = ch[i + 1][0]["start"] if i + 1 < len(ch) else DUR[n] + 1
        if c[0]["start"] - 0.05 <= t < end: cur = c
    if cur is None: return
    sp = CAP * .5
    ws = [text_width(ctx, w["text"], CAP) for w in cur]
    total = sum(ws) + sp * (len(ws) - 1)
    lines = [list(range(len(cur)))]
    if total > W - 160 and len(cur) > 1:   # wrap into two lines
        lines = [[0], list(range(1, len(cur)))] if len(cur) == 2 else [[0, 1], [2]]
    ap = back(prog(t, cur[0]["start"] - .05, .2))
    for li, ln in enumerate(lines):
        lw = sum(ws[i] for i in ln) + sp * (len(ln) - 1)
        x = W / 2 - lw / 2; yy = y + li * CAP * 1.15
        for i in ln:
            w = cur[i]; key = re.sub(r"[^a-z]", "", w["text"].lower()) in KEYS[n]
            active = w["start"] <= t < w["end"] + .08
            done = t >= w["end"] + .08
            if active:
                b = math.sin(math.pi * clamp(prog(t, w["start"], .2)))
                sc = 1.03 + .09 * b; col = PINK if key else YELLOW; dy = -12 * b
            else:
                sc = 1.0; dy = 0; col = (YELLOW if key else WHITE) if done else (0.85, 0.9, 1.0)
            text(ctx, w["text"], x + ws[i] / 2, yy + dy, CAP, col, NAVY, lw=16, scale=sc * lerp(.7, 1, ap), alpha=clamp(ap * 1.5))
            x += ws[i] + sp

def mascot(ctx, n, t):
    e = env_at(n, t)
    drum(ctx, 930, 200, .42, t, mouth=e * 1.1, look=-.6)

def footer(ctx, t):
    label(ctx, "FULL LESSON: EPISODE 1", 400, 225, 28, WHITE, NAVY, rot=-.02)

# ------------------------------------------------------------------ helpers
CX, CY, CW, CHH = 520, 820, 920, 760   # main media card (leave right edge for YT buttons)
def vid(ctx, t, name, t_in, speed=1.0, mode="loop", focus=(.6, .55), tag="REAL LIFE", scale=None):
    sc = 1.0 if scale is not None else card_in(t, t_in)
    video_card(ctx, name, t - t_in, CX, CY, CW, CHH, scale=sc if scale is None else scale, focus=focus, tag=tag, t=t, speed=speed, mode=mode)
def pic(ctx, t, f, t_in, focus=(.5, .5), tag="REAL LIFE", zoom=None, pre=False):
    sc = 1.0 if pre else card_in(t, t_in)
    z = zoom if zoom else lerp(1.0, 1.06, smooth(prog(t, t_in, 5)))
    photo_card(ctx, PH + f, CX, CY, CW, CHH, scale=sc, zoom=z, focus=focus, tag=tag, t=t)
def card_in(t, t0): return back(prog(t, t0, .4))
def kb(t, t0, d, a=1.0, b=1.06): return lerp(a, b, smooth(prog(t, t0, d)))
def sticker(ctx, t, t0, s, x, y, size=58, bg=YELLOW, fg=NAVY, rot=-.03, pre=False):
    p = 1.0 if pre else pop(t, t0)
    label(ctx, s, x, y, size, bg, fg, scale=p, rot=rot + wob(t, .5, .02))
def boom(ctx, t, t0, s, x, y, r=170, col=RED, fg=WHITE, size=60, rot=-.08, pre=False):
    p = 1.0 if pre else pop(t, t0)
    if p <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot + wob(t, 2, .03)); sscale(ctx, p, p)
    burst(ctx, 0, 0, r, col, NAVY, 14, t * .3); text(ctx, s, 0, 0, size, fg, NAVY); ctx.restore()

# ------------------------------------------------------------------ SHORT 1: too tight
def short1(ctx, t):
    tm = wt(1, "It's"); tbird = wt(1, "Instead,"); ttry = wt(1, "Try"); tnev = wt(1, "because")
    if t < tm - .2:                       # hook (identical look at t=0 and loop end)
        vid(ctx, t, 'deadstroke', 0, scale=1.0)
        boom(ctx, t, -1, "TOO TIGHT!", 790, 470, pre=True)
        if t > wt(1, "kill"): sticker(ctx, t, wt(1, "kill"), "= NO BOUNCE", 520, 1290, 56, RED, WHITE, .03)
    elif t < tbird - .2:
        pic(ctx, t, 'r1_deathgrip.jpg', tm - .2, focus=(.5, .6))
        sticker(ctx, t, tm, "#1 BEGINNER MISTAKE", 520, 340, 54, RED, WHITE)
        if t > wt(1, "tires"):
            for i in range(3):
                ph = (t * .9 + i / 3) % 1
                ellipse(ctx, 840 + 40 * (i - 1), 600 - 160 * ph, 22, 16, WHITE, None, alpha=.8 * (1 - ph))
            sticker(ctx, t, wt(1, "tires"), "TIRED HANDS", 520, 1290, 52, WHITE, NAVY, .02)
    elif t < ttry - .2:
        if t < wt(1, "small") - .1:
            vid(ctx, t, 'curl', tbird - .2)
            sticker(ctx, t, tbird, "INSTEAD...", 520, 340, 60, GREEN, WHITE)
        else:
            tb = wt(1, "small") - .1; p = pop(t, tb)
            ctx.save(); ctx.translate(520, 860); sscale(ctx, p, p)
            ellipse(ctx, 0, 90, 300, 100, (0.62, 0.42, 0.22), NAVY, LW); ellipse(ctx, 0, 65, 230, 55, (0.45, 0.28, 0.14), None)
            fl = 1.0 if wt(1, "fly") <= t < wt(1, "fly") + 1.2 else .2
            bird(ctx, 0, -30 - (40 if fl > .5 else 0) * abs(math.sin(t * 6)), 2.2, t, fl)
            ctx.restore()
            sticker(ctx, t, tb, "HOLD IT LIKE A BIRD", 520, 340, 54, YELLOW, NAVY)
            if t > wt(1, "firm"): sticker(ctx, t, wt(1, "firm"), "FIRM...", 300, 1290, 52, TEAL, WHITE, -.08)
            if t > wt(1, "soft"): sticker(ctx, t, wt(1, "soft"), "...SOFT!", 760, 1290, 52, PINK, WHITE, .08)
    elif t < tnev - .2:
        vid(ctx, t, 'rebound', ttry - .2)
        sticker(ctx, t, ttry, "TRY IT NOW!", 520, 340, 62, GREEN, WHITE)
        boom(ctx, t, wt(1, "feel"), "BOING!", 830, 1100, 120, YELLOW, NAVY, 46, .1)
    else:                                  # tease -> loops back into the hook
        vid(ctx, t, 'deadstroke', tnev - .2)
        sticker(ctx, t, wt(1, "never"), "NEVER DO THIS", 520, 340, 58, RED, WHITE)
        if t > DUR[1] - .6: boom(ctx, t, DUR[1] - .6, "TOO TIGHT!", 790, 470)

# ------------------------------------------------------------------ SHORT 2: balance point
def short2(ctx, t):
    trest = wt(2, "Rest"); tthird = wt(2, "That's"); tpinch = wt(2, "Pinch"); tful = wt(2, "fulcrum,"); tsec = wt(2, "real")
    if t < trest - .2:
        pic(ctx, t, 'r5_fulcrum.jpg', 0, focus=(.55, .55), pre=True, zoom=1.0)
        boom(ctx, t, -1, "SECRET!", 800, 400, 150, PINK, WHITE, 54, .1, pre=True)
        if t > wt(2, "Every"): sticker(ctx, t, wt(2, "Every"), "EVERY STICK HAS ONE", 520, 1290, 50, YELLOW, NAVY)
    elif t < tthird - .2:
        vid(ctx, t, 'fulcrum', trest - .2, mode="pingpong")
        sticker(ctx, t, trest, "REST IT ON ONE FINGER", 520, 340, 50, YELLOW, NAVY)
        if t > wt(2, "slide"): sticker(ctx, t, wt(2, "slide"), "SLIDE UNTIL IT BALANCES", 520, 1290, 46, PINK, WHITE, .02)
    elif t < tpinch - .2:
        p = pop(t, tthird - .2); L = 860
        ctx.save(); ctx.translate(540, 820); sscale(ctx, p, p)
        ctx.new_path(); ctx.move_to(0, 20); ctx.line_to(-80, 170); ctx.line_to(80, 170); ctx.close_path(); fill_stroke(ctx, ORANGE, NAVY, 6)
        ctx.save(); ctx.rotate(.03 * math.sin(t * 3))
        stick(ctx, -L / 3, 0, 0, L, 44, face="smile", t=t)
        for k in range(4):
            xx = -L / 3 + L * k / 3; line(ctx, xx, -44, xx, -90, WHITE, 7)
        ctx.restore(); ctx.restore()
        boom(ctx, t, wt(2, "third"), "1/3", 540, 560, 120, PINK, WHITE, 70, -.05)
        sticker(ctx, t, wt(2, "butt"), "FROM THE BUTT END", 540, 1290, 50, YELLOW, NAVY)
    elif t < tful - .3:
        vid(ctx, t, 'pinch', tpinch - .2, mode="pingpong")
        sticker(ctx, t, tpinch, "PINCH IT RIGHT THERE", 520, 340, 50, PINK, WHITE)
        if t > wt(2, "thumb"): sticker(ctx, t, wt(2, "thumb"), "THUMB + 1ST FINGER", 520, 1290, 48, YELLOW, NAVY)
    else:
        vid(ctx, t, 'pivot', tful - .3)
        boom(ctx, t, tful - .1, "FULCRUM!", 760, 380, 170, PINK, WHITE, 54, .08)
        if t > tsec: sticker(ctx, t, tsec, "THE REAL SECRET...", 520, 1290, 48, YELLOW, NAVY)
        if t > DUR[2] - .6:
            ctx.set_source_rgba(1, 1, 1, .5 * prog(t, DUR[2] - .6, .6)); ctx.paint()

# ------------------------------------------------------------------ SHORT 3: let it drop
def short3(ctx, t):
    thold = wt(3, "Hold"); tif = wt(3, "If"); tthud = wt(3, "If", 9); tloose = wt(3, "Loosen"); tday = wt(3, "Do"); tnow = wt(3, "Now,")
    if t < thold - .2:
        vid(ctx, t, 'rebound', 0, scale=1.0)
        boom(ctx, t, -1, "LET IT DROP!", 760, 440, 200, YELLOW, NAVY, 40, -.06, pre=True)
    elif t < tif - .2:
        vid(ctx, t, 'rebound', thold - .2)
        sticker(ctx, t, thold, "A FEW INCHES UP", 520, 340, 54, WHITE, NAVY)
        if t > wt(3, "let", 4): sticker(ctx, t, wt(3, "let", 4), "...LET GO!", 520, 1290, 56, YELLOW, NAVY, .03)
    elif t < tthud - .2:
        vid(ctx, t, 'rebound', tif - .2)
        boom(ctx, t, wt(3, "bounces"), "BOING!", 790, 420, 150, YELLOW, NAVY, 56, -.1)
        if t > wt(3, "relaxed."):
            sticker(ctx, t, wt(3, "relaxed."), "RELAXED!", 520, 1290, 58, GREEN, WHITE)
    elif t < tloose - .2:
        vid(ctx, t, 'deadstroke', tthud - .2)
        boom(ctx, t, wt(3, "thuds,"), "THUD.", 790, 420, 140, (0.6, 0.65, 0.75), WHITE, 58, .08)
        if t > wt(3, "squeezing"): sticker(ctx, t, wt(3, "squeezing"), "TOO HARD!", 520, 1290, 58, RED, WHITE)
    elif t < tday - .2:
        vid(ctx, t, 'tap1', tloose - .2)
        sticker(ctx, t, tloose, "LOOSEN UP & TRY AGAIN", 520, 340, 48, GREEN, WHITE)
    elif t < tnow - .2:
        p = pop(t, tday - .2)
        ctx.save(); ctx.translate(540, 800); sscale(ctx, p, p)
        circle(ctx, 0, 0, 260, WHITE, NAVY, 12); rrect(ctx, -40, -330, 80, 70, 16); fill_stroke(ctx, RED, NAVY, 8)
        fr = 1 - prog(t, tday, 2.2)
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 230, -math.pi / 2, -math.pi / 2 + 2 * math.pi * fr); ctx.close_path(); ctx.set_source_rgba(*YELLOW, .75); ctx.fill()
        text(ctx, "1:00", 0, 0, 120, NAVY, None, shadow=False)
        ctx.restore()
        sticker(ctx, t, wt(3, "day."), "EVERY DAY!", 540, 1290, 60, PINK, WHITE)
    else:
        vid(ctx, t, 'slowtaps', tnow - .2)
        sticker(ctx, t, wt(3, "grab"), "GRAB A STICK!", 520, 340, 56, YELLOW, NAVY)
        if t > DUR[3] - .6: boom(ctx, t, DUR[3] - .6, "LET IT DROP!", 760, 440, 200, YELLOW, NAVY, 40, -.06)

SHORTS = {1: (short1, "TOO TIGHT?"), 2: (short2, "THE SECRET SPOT"), 3: (short3, "THE DROP TEST")}

def frame(ctx, n, t):
    fn, title = SHORTS[n]
    background(ctx, t)
    fn(ctx, t)
    # header (always visible so the loop is seamless)
    label(ctx, "DRUMS IN 5 MIN", 400, 150, 42, PINK, WHITE, rot=-.02)
    captions(ctx, n, t)
    mascot(ctx, n, t)
    footer(ctx, t)

def surface(n, t, scale=1.0):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale)); ctx = cairo.Context(s)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo); sscale(ctx, scale, scale); frame(ctx, n, t); return s

if __name__ == "__main__":
    if sys.argv[1] == "still":
        n, t, out = int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        surface(n, t, float(sys.argv[5]) if len(sys.argv) > 5 else 1.0).write_to_png(out)
    else:
        n, out = int(sys.argv[2]), sys.argv[3]
        nf = int(DUR[n] * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", os.path.join(HERE, f"s{n}.mp3"), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(nf): p.stdin.write(surface(n, f / FPS).get_data())
        p.stdin.close(); p.wait()
