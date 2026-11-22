"""Episode 2 - The drum kit explained. Fully animated (no hands).
usage: python3 ep2.py still T scale out.png
       python3 ep2.py range F0 F1 scale out.mp4 [crf]
"""
import sys, os, math, json, random, subprocess, re
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import *
from photo import photo_card

FPS = 30
CUES = json.load(open(os.path.join(HERE, "cues.json")))
WORDS = json.load(open(os.path.join(HERE, "words_final.json")))
ENV = np.load(os.path.join(HERE, "env.npy"))
TOTAL = 326.35
PHOTO_EP1 = "/home/user/drum-series-/episode-01/photos/p5_vgrip.png"

GOLD = (0.98, 0.78, 0.25); GOLD_D = (0.85, 0.62, 0.12)
CHROME = (0.86, 0.88, 0.93); DARK = (0.22, 0.24, 0.32)
BLUE_D = (0.20, 0.40, 0.95); TEAL_D = (0.05, 0.62, 0.66)

def norm(s): return re.sub(r"[^a-z0-9'\-]", "", s.lower())
def wt(word, after=0.0):
    k = norm(word)
    for w in WORDS:
        if w["start"] >= after - 1e-6 and norm(w["text"]) == k: return w["start"]
    raise KeyError((word, after))
def env_at(t):
    i = int(t * FPS)
    return float(np.mean(ENV[max(0, i - 1):i + 1])) if 0 <= i < len(ENV) else 0.0

# ------------------------------------------------------------------ background / captions / hud
_R = random.Random(7)
BG = [(_R.uniform(0, W), _R.uniform(0, H), _R.uniform(.5, 1.1), _R.uniform(8, 22), _R.choice([0, 1, 2]), _R.uniform(0, 6.28)) for _ in range(26)]
def background(ctx, t, tint=None):
    g = cairo.RadialGradient(W / 2, H * .42, 100, W / 2, H * .5, 1250)
    c0, c1 = (0.22, 0.62, 1.0), (0.05, 0.38, 0.92)
    if tint: c0 = lerpc(c0, tint, .35); c1 = lerpc(c1, tint, .25)
    g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); ctx.set_source(g); ctx.paint()
    ctx.save(); ctx.translate(W / 2, H * .45); ctx.rotate(t * .05)
    for i in range(16):
        a = i * 2 * math.pi / 16
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 1600, a, a + math.pi / 32); ctx.close_path(); ctx.set_source_rgba(1, 1, 1, .035); ctx.fill()
    ctx.restore()
    for (x, y, s, sp, k, ph) in BG:
        yy = (y - t * sp) % (H + 200) - 100; xx = x + wob(t, .08, 30, ph)
        if k == 0: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph))
        elif k == 1: note(ctx, xx, yy, s, WHITE, .13, wob(t, .1, .3, ph), double=True)
        else: star(ctx, xx, yy, 18 * s, WHITE, None, alpha=.13, rot=t * .5 + ph)

CAP = 62
def captions(ctx, t):
    cue = None
    for c in CUES:
        if c["start"] <= t < c["end"] + .03: cue = c
    if cue is None: return
    nl = max(w["line"] for w in cue["words"]) + 1
    lines = [[w for w in cue["words"] if w["line"] == i] for i in range(nl)]
    sp = CAP * .32
    widths = [sum(text_width(ctx, w["text"], CAP) for w in ln) + sp * (len(ln) - 1) for ln in lines]
    lh = CAP * 1.22; bw = max(widths) + 80; bh = lh * nl + 36; cy0 = 1048 - bh
    ap = back(prog(t, cue["start"], .25))
    ctx.save(); ctx.translate(W / 2, cy0 + bh / 2); sscale(ctx, lerp(.85, 1, ap), lerp(.85, 1, ap))
    rrect(ctx, -bw / 2, -bh / 2, bw, bh, 30); ctx.set_source_rgba(*NAVY, .62 * clamp(ap * 1.5)); ctx.fill(); ctx.restore()
    for li, ln in enumerate(lines):
        x = W / 2 - widths[li] / 2; y = cy0 + 18 + lh * (li + .5)
        for w in ln:
            ww = text_width(ctx, w["text"], CAP); cx = x + ww / 2
            if t < w["start"]: col, sc, dy, rot, a = (0.80, 0.88, 1.0), 1.0, 0, 0, .75
            elif t < max(w["end"], w["start"] + .08):
                p = prog(t, w["start"], .22); bump = math.sin(math.pi * clamp(p)) if p < 1 else 0
                sc = 1 + (.16 if w["key"] else .12) * bump + (.10 if w["key"] else .04); dy = -10 * bump
                col = PINK if w["key"] else YELLOW; rot = wob(t, 3, .05) if w["key"] else 0; a = 1
            else: col = YELLOW if w["key"] else WHITE; sc, dy, rot, a = 1.0, 0, 0, 1
            text(ctx, w["text"], cx, y + dy, CAP, col, NAVY, lw=11, alpha=a * clamp(ap * 1.4), scale=sc, rot=rot)
            x += ww + sp

SECTIONS = [(0, "START"), (74.48, "SNARE"), (110.18, "KICK"), (144.4, "HI-HAT"), (174.26, "TOMS"),
            (207.38, "CYMBALS"), (238.82, "TEAM"), (268.99, "RECAP"), (288.77, "BONUS"), (314.78, "NEXT")]
def hud(ctx, t):
    a = smooth(prog(t, 5.0, .6))
    if a <= 0: return
    ctx.save(); ctx.translate(0, -80 * (1 - a))
    x0, x1, y = 470, 1450, 52
    label(ctx, "EPISODE 2", 320, y, 30, PINK, WHITE)
    rrect(ctx, x0, y - 16, x1 - x0, 32, 16); fill_stroke(ctx, (0.08, 0.25, 0.65), NAVY, 5)
    f = clamp(t / TOTAL)
    if f > .005:
        rrect(ctx, x0 + 5, y - 11, (x1 - x0 - 10) * f, 22, 11)
        g = cairo.LinearGradient(x0, 0, x1, 0); g.add_color_stop_rgb(0, *YELLOW); g.add_color_stop_rgb(1, *ORANGE); ctx.set_source(g); ctx.fill()
    for (s, name) in SECTIONS[1:]:
        sx = x0 + (x1 - x0) * s / TOTAL; done = t >= s
        r = 20 * (1 + .5 * math.sin(math.pi * clamp(prog(t, s, .5)))) if done else 16
        star(ctx, sx, y, r, YELLOW if done else (0.55, 0.65, 0.85), NAVY, 4)
        if done and t - s < 1.5: confetti(ctx, sx, y + 10, t - s, seed=int(s), n=18, spread=160, dur=1.4)
    gift(ctx, x1 + 70, y + 8, .28, t, 0, shake=1.0 if 280 < t < 289 else 0)
    ctx.restore()

def narrator(ctx, t):
    e = env_at(t); drum(ctx, 150, 905 - abs(math.sin(t * 6)) * 6 * e, .62, t, mouth=e * 1.1, look=.6)

# ------------------------------------------------------------------ kit characters
def eyes(ctx, x, y, s, t, look=0.0, off=0.0, blink=True):
    b = blink and ((t + off) % 3.7) < .13
    for dx in (-1, 1):
        ex = x + dx * 26 * s
        if b: line(ctx, ex - 14 * s, y, ex + 14 * s, y, NAVY, 5 * s)
        else:
            ellipse(ctx, ex, y, 18 * s, 22 * s, WHITE, NAVY, 4 * s)
            circle(ctx, ex + (4 + look * 6) * s, y + 3 * s, 9 * s, NAVY, None); circle(ctx, ex + (7 + look * 6) * s, y - 2 * s, 3 * s, WHITE, None)

def mouth(ctx, x, y, s, m=0.0, smile=True):
    if m < .08:
        ctx.new_path(); ctx.arc(x, y, 16 * s, .15 * math.pi, .85 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5 * s); ctx.stroke()
    else:
        ellipse(ctx, x, y + 6 * s, (18 + 5 * m) * s, (5 + 20 * m) * s, (0.45, .05, .12), NAVY, 4 * s)

def stand(ctx, x, y0, y1, s=1.0, tripod=True):
    line(ctx, x, y0, x, y1, DARK, 8 * s); line(ctx, x, y0, x, y1, CHROME, 4 * s)
    if tripod:
        for dx in (-1, 1): line(ctx, x, y1 - 30 * s, x + dx * 70 * s, y1 + 20 * s, DARK, 7 * s)

def cymbal(ctx, x, y, r, t, col=GOLD, face=True, wobble=0.0, look=0.0, m=0.0, tilt=0.0, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt + wob(t, 7, .12 * wobble))
    ellipse(ctx, 0, 0, r, r * .24, col, NAVY, LW, alpha)
    ellipse(ctx, 0, -r * .03, r * .85, r * .16, lerpc(col, WHITE, .25), None, alpha=alpha)
    for k in range(3): ellipse(ctx, 0, 0, r * (.3 + .2 * k), r * .24 * (.3 + .2 * k), None, (*GOLD_D,), 2, alpha * .6)
    ellipse(ctx, 0, -r * .05, r * .15, r * .06, GOLD_D, NAVY, 3, alpha)
    if face:
        eyes(ctx, -r * .02, r * .48, r / 140, t, look, off=x * .01)
        mouth(ctx, 0, r * .74, r / 140, m)
    ctx.restore()

def tom(ctx, x, y, s, t, body=PURPLE, m=0.0, look=0.0, bounce=0.0):
    drum(ctx, x, y - bounce, s, t, mouth=m, body=body, look=look, blink_off=x * .01)

def kick(ctx, x, y, s, t, m=0.0, boom=0.0, look=0.0, pedal=False, press=0.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s * (1 + .06 * boom), s * (1 + .06 * boom))
    for dx in (-1, 1): line(ctx, dx * 120, 110, dx * 175, 205, CHROME, 10)
    circle(ctx, 0, 0, 205, RED, NAVY, LW); circle(ctx, 0, 0, 180, (0.97, 0.97, 0.99), NAVY, 5)
    for k in range(10):
        a = k * 2 * math.pi / 10; rrect(ctx, 190 * math.cos(a) - 9, 190 * math.sin(a) - 9, 18, 18, 5); fill_stroke(ctx, CHROME, NAVY, 3)
    eyes(ctx, 0, -30, 1.9, t, look, off=1.3)
    ellipse(ctx, -95, 45, 26, 15, PINK, None, alpha=.7); ellipse(ctx, 95, 45, 26, 15, PINK, None, alpha=.7)
    mouth(ctx, 0, 60, 2.0, m)
    ctx.restore()
    if pedal:
        px, py = x, y + 205 * s
        ctx.save(); ctx.translate(px, py); sscale(ctx, s, s)
        rrect(ctx, -60, 40, 120, 26, 8); fill_stroke(ctx, DARK, NAVY, 4)
        ctx.save(); ctx.translate(0, 60); ctx.rotate(-0.35 + 0.25 * press)
        rrect(ctx, -10, -150, 20, 150, 8); fill_stroke(ctx, CHROME, NAVY, 4); ctx.restore()
        ctx.save(); ctx.translate(-10, 20); ctx.rotate(-0.3 + 0.75 * press)
        line(ctx, 0, 0, 0, -150, CHROME, 8); circle(ctx, 0, -160, 26, (1, .95, .9), NAVY, 4); ctx.restore()
        ctx.restore()

def hihat(ctx, x, y, s, t, open_=0.6, m=0.0, look=0.0):
    stand(ctx, x, y, y + 420 * s, s)
    gap = 10 + 60 * open_
    cymbal(ctx, x, y + gap * s * .5, 120 * s, t, GOLD, face=False)
    cymbal(ctx, x, y - gap * s * .5, 120 * s, t, GOLD, face=False)
    eyes(ctx, x, y - gap * s * .5 + 34 * s, s * .9, t, look, off=2.1)
    if open_ > .3:
        ellipse(ctx, x, y, 34 * s, gap * s * .32, (0.45, .05, .12), None)
    # pedal
    rrect(ctx, x - 45 * s, y + 420 * s, 90 * s, 22 * s, 6 * s); fill_stroke(ctx, DARK, NAVY, 3)

def throne(ctx, x, y, s=1.0, h=0.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    line(ctx, 0, 0, 0, 160 - h, DARK, 12)
    for dx in (-1, 1): line(ctx, 0, 140 - h, dx * 90, 210, DARK, 9)
    ellipse(ctx, 0, -h, 110, 28, (0.15, 0.15, 0.2), NAVY, LW); ctx.restore()

def full_kit(ctx, cx, cy, s, t, hits=None, glow=None, faces=True):
    """Front view kit. hits: dict piece->intensity 0..1 ; glow: piece to highlight."""
    hits = hits or {}; glow = glow or {}
    def gl(p, x, y, r):
        g = glow.get(p, 0)
        if g > 0: circle(ctx, x, y, r, YELLOW, None, alpha=.35 * g)
    ctx.save(); ctx.translate(cx, cy); sscale(ctx, s, s)
    # ride + crash stands
    stand(ctx, 430, -230, 260); stand(ctx, -390, -300, 260)
    gl('crash', -390, -300, 170); cymbal(ctx, -390, -300, 150, t, GOLD, faces, wobble=hits.get('crash', 0), look=.4)
    gl('ride', 430, -230, 190); cymbal(ctx, 430, -230, 175, t, (0.92, 0.72, 0.30), faces, wobble=hits.get('ride', 0), look=-.4)
    # hi-hat (left)
    gl('hihat', -560, -40, 150); hihat(ctx, -560, -40, .75, t, open_=.15 + .5 * hits.get('hihat', 0))
    # rack toms
    for i, (tx, bc) in enumerate([(-150, PURPLE), (120, TEAL_D)]):
        gl('toms', tx, -170, 120); tom(ctx, tx, -150, .62, t, bc, bounce=12 * hits.get('toms', 0))
    # kick
    gl('kick', 0, 110, 230); kick(ctx, 0, 110, .78, t, m=.6 * hits.get('kick', 0), boom=hits.get('kick', 0))
    # floor tom (right)
    gl('toms', 330, 110, 130); tom(ctx, 330, 130, .78, t, BLUE_D, bounce=10 * hits.get('toms', 0))
    for dx in (-60, 60): line(ctx, 330 + dx, 190, 330 + dx * 1.2, 300, CHROME, 8)
    # snare (front-left)
    gl('snare', -330, 150, 140); tom(ctx, -330, 150 - 10 * hits.get('snare', 0), .74, t, RED, m=.5 * hits.get('snare', 0))
    stand(ctx, -330, 215, 300, .9)
    ctx.restore()

def sfx(ctx, t, t0, s, x, y, size=80, col=YELLOW, rot=-.08, dur=1.2):
    p = prog(t, t0, dur)
    if p <= 0 or p >= 1: return
    sc = back(clamp(p / .3)) * (1 - smooth((p - .7) / .3) * .3)
    a = 1 - smooth((p - .7) / .3)
    ctx.save(); ctx.translate(x, y - 30 * p); ctx.rotate(rot)
    burst(ctx, 0, 0, size * 1.7 * sc, WHITE, NAVY, 12, alpha=a)
    text(ctx, s, 0, 0, size, col, NAVY, scale=sc, alpha=a); ctx.restore()

def rings(ctx, x, y, t, t0, col=WHITE, n=3, r0=60, r1=260, dur=.9):
    for k in range(n):
        p = prog(t, t0 + k * .12, dur)
        if 0 < p < 1:
            ctx.new_path(); ctx.arc(x, y, lerp(r0, r1, ease_out(p)), 0, 2 * math.pi); ctx.set_source_rgba(*col, 1 - p); ctx.set_line_width(10 * (1 - p) + 2); ctx.stroke()

def nameplate(ctx, t, t0, name, nick, x=960, y=170, col=PINK):
    label(ctx, name, x, y, 70, col, WHITE, scale=pop(t, t0), rot=-.03 + wob(t, .5, .015))
    if nick: label(ctx, nick, x, y + 95, 40, YELLOW, NAVY, scale=pop(t, t0 + .3), rot=.03)

# ------------------------------------------------------------------ scenes
def sc_intro(ctx, t):      # 0 - 20.84
    order = [('kick', 0.0), ('snare', .25), ('toms', .45), ('hihat', .65), ('crash', .85), ('ride', 1.05)]
    p_all = min(pop(t, 0, .5), 1.2)
    hits = {}
    for k in ('drums,', 'cymbals,', 'pedals,'):
        pass
    ts = [wt('drums,'), wt('cymbals,'), wt('pedals,'), wt('stands.')]
    hits['toms'] = max(0, 1 - prog(t, ts[0], .4)); hits['crash'] = max(0, 1 - prog(t, ts[1], .6)); hits['ride'] = hits['crash']
    hits['kick'] = max(0, 1 - prog(t, ts[2], .4)); hits['snare'] = max(0, 1 - prog(t, ts[3], .4))
    sh = 8 * max(0, 1 - t / .4)
    ctx.save(); ctx.translate(wob(t, 23, sh), wob(t, 19, sh, 1.3))
    full_kit(ctx, 960, 570 + 400 * (1 - back(prog(t, 0, .6))), 1.0, t, hits)
    ctx.restore()
    confetti(ctx, 960, 400, t - .3, seed=3, n=60, spread=800, dur=2.2)
    if t < 6.4:
        sfx(ctx, t, ts[0], "THUMP!", 1500, 300, 60, YELLOW, .1)
        sfx(ctx, t, ts[1], "CRASH!", 420, 260, 60, PINK, -.1)
        sfx(ctx, t, ts[2], "BOOM!", 1500, 640, 60, ORANGE, .08)
    tq = wt('Where')
    if tq < t < wt('In', 8):
        text(ctx, "?", 960 + wob(t, 2, 20), 220, 200, YELLOW, NAVY, scale=pop(t, tq), rot=wob(t, 1.4, .2))
    tf = wt('In', 8)
    if t >= tf:
        ctx.save(); ctx.set_source_rgba(*NAVY, .35 * smooth(prog(t, tf, .4))); ctx.paint(); ctx.restore()
        p = back(prog(t, tf, .45))
        text(ctx, "MEET THE KIT", 960, 300, 140, WHITE, NAVY, lw=22, scale=lerp(2.2, 1, p), alpha=clamp(p * 3), rot=-.03)
        text(ctx, "IN 5 MINUTES!", 960, 450, 130, YELLOW, NAVY, lw=22, scale=lerp(2.2, 1, back(prog(t, tf + .35, .45))), alpha=clamp(prog(t, tf + .35, .15)), rot=.02)
        for i, (k, lab) in enumerate([('name', 'NAME'), ('does,', 'WHAT IT DOES'), ('goes.', 'WHERE IT GOES')]):
            tk = wt(k, 10)
            label(ctx, lab, 560 + i * 400, 640, 44, [PINK, TEAL, ORANGE][i], WHITE, scale=pop(t, tk), rot=wob(t, .5, .03, i))
        tb = wt('bonus', 14)
        if t > tb:
            gift(ctx, 960, 790, .9 * pop(t, tb), t, 0, shake=1)
            label(ctx, "BONUS TIP AT THE END!", 1420, 790, 40, YELLOW, NAVY, scale=pop(t, tb + .2), rot=.04)

def sc_recap(ctx, t):      # 20.84 - 38.22
    t0 = 20.84; tg = wt('grab', 35)
    if t < tg - .3:
        photo_card(ctx, PHOTO_EP1, 700, 470, 760, 540, rot=-.04, scale=back(prog(t, t0, .45)), tag="EPISODE 1", t=t, focus=(.5, .45))
        label(ctx, "LAST TIME:", 1450, 260, 50, WHITE, NAVY, scale=pop(t, t0 + .2), rot=.04)
        label(ctx, "RELAXED GRIP", 1450, 380, 46, GREEN, WHITE, scale=pop(t, wt('relaxed', 23)), rot=-.03)
        label(ctx, "BOUNCY REBOUND", 1450, 490, 46, PINK, WHITE, scale=pop(t, wt('rebound.', 25)), rot=.03)
        tm = wt('missed', 27)
        if t > tm:
            ctx.save(); ctx.translate(1450, 650); sscale(ctx, pop(t, tm), pop(t, tm))
            rrect(ctx, -170, -60, 340, 120, 30); fill_stroke(ctx, RED, NAVY, 6)
            for dx in (-28, 28): rrect(ctx, dx - 12, -35, 24, 70, 6); fill_stroke(ctx, WHITE, None)
            ctx.restore()
            label(ctx, "WATCH LESSON 1 FIRST!", 1450, 760, 38, YELLOW, NAVY, scale=pop(t, tm + .3))
    else:
        for sgn in (-1, 1):
            a = -math.pi / 2 + sgn * .4 + wob(t, 2, .15, sgn)
            stick(ctx, 960 - sgn * 160, 760, a, 520, 40, face="smile", t=t + sgn)
        title = back(prog(t, tg - .2, .4))
        text(ctx, "GRAB YOUR STICKS!", 960, 230, 110, YELLOW, NAVY, lw=18, scale=lerp(2, 1, title), alpha=clamp(title * 3), rot=-.03)
        confetti(ctx, 960, 400, t - tg, seed=8, n=50, spread=700)

def sc_overview(ctx, t):   # 38.22 - 74.48
    tdr = wt('drums', 46); tcy = wt('cymbals', 52); tjob = wt('Every', 58); tteam = wt('Think', 63); thands = wt('Some', 67); tmeet = wt("Let's", 71)
    if t < tjob - .3:
        full_kit(ctx, 960, 590, .88, t, glow={'snare': 1, 'kick': 1, 'toms': 1} if tdr <= t < tcy else ({'crash': 1, 'ride': 1, 'hihat': 1} if t >= tcy else {}))
        if t < tdr:
            label(ctx, "JUST A FEW DRUMS + A FEW CYMBALS", 960, 170, 50, WHITE, NAVY, scale=pop(t, wt('really', 40)))
        elif t < tcy:
            label(ctx, "DRUMS", 960, 160, 70, PINK, WHITE, scale=pop(t, tdr))
            for i, (k, s) in enumerate([('thump', 'THUMP!'), ('crack', 'CRACK!'), ('boom.', 'BOOM!')]):
                tk = wt(k, 48); label(ctx, s, [230, 1690, 230][i], [360, 460, 600][i], 48, [ORANGE, RED, PURPLE][i], WHITE, scale=pop(t, tk), rot=wob(t, .7, .05, i))
        else:
            label(ctx, "CYMBALS", 960, 160, 70, GOLD_D, WHITE, scale=pop(t, tcy))
            for i, (k, s) in enumerate([('crash', 'CRASH!'), ('ping', 'PING!'), ('tick.', 'TICK!')]):
                tk = wt(k, 55); label(ctx, s, [230, 1690, 230][i], [360, 460, 600][i], 48, [PINK, TEAL, ORANGE][i], WHITE, scale=pop(t, tk), rot=wob(t, .7, .05, i))
    else:
        # team lineup
        names = [('SNARE', RED), ('KICK', RED), ('HI-HAT', GOLD_D), ('TOMS', PURPLE), ('CRASH', GOLD_D), ('RIDE', GOLD_D)]
        title = "EVERY PIECE HAS A JOB" if t < tteam else ("IT'S A TEAM!" if t < tmeet else "MEET THE TEAM!")
        label(ctx, title, 960, 170, 64, YELLOW, NAVY, scale=pop(t, tjob if t < tteam else (tteam if t < tmeet else tmeet)), rot=-.02)
        for i, (n, c) in enumerate(names):
            x = 260 + i * 280; p = pop(t, tjob + .15 * i); y = 520 + wob(t, 1.2, 10, i)
            ctx.save(); ctx.translate(x, y); sscale(ctx, p, p)
            rrect(ctx, -110, -150, 220, 300, 30); fill_stroke(ctx, WHITE, NAVY, LW)
            rrect(ctx, -110, -150, 220, 70, 30); fill_stroke(ctx, c, NAVY, LW)
            text(ctx, f"#{i + 1}", 0, -115, 42, WHITE, NAVY)
            if n in ('SNARE', 'TOMS'): tom(ctx, 0, 20, .42, t, RED if n == 'SNARE' else PURPLE)
            elif n == 'KICK': kick(ctx, 0, 20, .3, t)
            elif n == 'HI-HAT':
                cymbal(ctx, 0, 0, 80, t, GOLD, face=False); cymbal(ctx, 0, -20, 80, t, GOLD, face=True)
            else: cymbal(ctx, 0, 10, 85, t, GOLD, face=True)
            text(ctx, n, 0, 115, 36, NAVY, None, shadow=False)
            ctx.restore()
            if t > thands:
                feet = n in ('KICK', 'HI-HAT')
                label(ctx, "FOOT" if n == 'KICK' else ("HANDS + FOOT" if n == 'HI-HAT' else "HANDS"), x, 730, 28, GREEN if not feet else ORANGE, WHITE, scale=pop(t, thands + (.5 if feet else 0)))

def sc_snare(ctx, t):      # 74.48 - 110.18
    t0 = 74.48; tunder = wt('Underneath', 81); tcrack = wt('crack.', 89); ttry = wt('Try', 90); thear = wt('Hear', 97); tclap = wt('clap', 103); tsoif = wt('So', 105)
    nameplate(ctx, t, t0, "SNARE DRUM", "THE CRACK!" if t > tsoif else None)
    if tunder <= t < ttry - .2:
        # flip: show underneath wires
        p = smooth(prog(t, tunder, .6))
        ctx.save(); ctx.translate(960, 560); sscale(ctx, 1.6, 1.6 * (1 - 2 * p) if p < .5 else 1.6 * (2 * p - 1))
        if p < .5: tom(ctx, 0, 0, 1.0, t, RED)
        else:
            ellipse(ctx, 0, 0, 150, 40, (0.96, 0.96, 0.98), NAVY, LW)
            buzz = wob(t, 30, 3) if t > wt('buzz', 85) else 0
            for k in range(-4, 5): line(ctx, -125, k * 7 + buzz, 125, k * 7 - buzz, DARK, 4)
            for k in range(-4, 5): line(ctx, -125, k * 7 + buzz, 125, k * 7 - buzz, CHROME, 2)
        ctx.restore()
        if p > .5: label(ctx, "SNARE WIRES", 960, 800, 48, YELLOW, NAVY, scale=pop(t, tunder + .4))
        if t > wt('buzz', 85): text(ctx, "bzzzz", 1400 + wob(t, 6, 10), 520, 70, YELLOW, NAVY, rot=-.1, scale=pop(t, wt('buzz', 85)))
        sfx(ctx, t, tcrack, "CRACK!", 1450, 420, 80, RED, -.1, 1.4)
    else:
        bnc = 0
        for k in [ttry, wt('bounce', 95), thear, wt('crack?', 98)]:
            bnc = max(bnc, 30 * max(0, 1 - prog(t, k, .25)))
        tom(ctx, 960, 600, 1.7, t, RED, m=env_at(t) * .3 if t < ttry else 0.0, bounce=bnc)
        stand(ctx, 960, 700, 900, 1.2)
        if t < tunder:
            label(ctx, "RIGHT IN FRONT OF YOU", 960, 330, 44, WHITE, NAVY, scale=pop(t, wt('sits', 76)))
            label(ctx, "YOU'LL HIT IT THE MOST!", 960, 810, 44, GREEN, WHITE, scale=pop(t, wt('most.', 80)))
        if t >= ttry:
            for k in [ttry, wt('bounce', 95)]:
                stick(ctx, 1250, 330 - 80 * math.sin(math.pi * clamp(prog(t, k, .5))), 2.4, 380, 26, t=t)
            sfx(ctx, t, thear, "CRACK!", 1450, 400, 80, RED, -.1, 1.4); rings(ctx, 960, 480, t, thear)
        if t > tclap:
            for i in range(2):
                ph = (t * 2) % 1
                text(ctx, "CLAP!", 400 + i * 1120, 450 - 30 * ph, 60, PINK, NAVY, alpha=1 - ph * .5, rot=(-1) ** i * .15)

def sc_kick(ctx, t):       # 110.18 - 144.4
    t0 = 110.18; trest = wt('Rest', 120); tboom = wt('boom,', 126); tlow = wt('low', 127); ttog = wt('Together,', 135); tbc = wt('Boom,', 140)
    nameplate(ctx, t, t0, "BASS DRUM", "a.k.a. THE KICK!" if t > wt('kick', 112) else None, col=RED)
    press = 0
    for k in [wt('down.', 122), tboom] + ([wt('Boom,', 140), wt('boom,', 142)] if t > tbc else []):
        press = max(press, 1 - prog(t, k, .35) if t >= k else 0)
    bm = max(0, 1 - prog(t, tboom, .5)) if t >= tboom else 0
    if t >= tbc:
        for k in (wt('Boom,', 140), wt('boom,', 142)): bm = max(bm, max(0, 1 - prog(t, k, .5)) if t >= k else 0)
    if t < ttog - .2:
        kick(ctx, 960, 520, 1.0 + .05 * bm, t, m=.7 * bm, boom=bm, pedal=t > wt('pedal.', 118), press=press)
        if t > wt('right', 117): label(ctx, "RIGHT FOOT", 1450, 760, 44, ORANGE, WHITE, scale=pop(t, wt('right', 117)))
        if t > trest: label(ctx, "PRESS THE PEDAL", 470, 760, 44, YELLOW, NAVY, scale=pop(t, trest))
        if t > tboom:
            rings(ctx, 960, 520, t, tboom, WHITE, 4, 200, 700, 1.2); sfx(ctx, t, tboom, "BOOM!", 1460, 380, 90, ORANGE, .06, 1.8)
        if t > wt('chest.', 130): label(ctx, "FEEL IT IN YOUR CHEST!", 960, 330, 44, PINK, WHITE, scale=pop(t, wt('feel', 130)))
    else:
        # heart of the beat
        hb = max(0, 1 - prog(t, ttog, .4))
        bts = [wt('Boom,', 140), wt('crack,', 141), wt('boom,', 142), wt('crack.', 143)]
        beat = 0
        for k in bts: beat = max(beat, max(0, 1 - prog(t, k, .3)) if t >= k else 0)
        kick(ctx, 620, 560, .8, t, m=.6 * beat, boom=beat * (1 if t < bts[1] or bts[2] <= t < bts[3] else 0))
        tom(ctx, 1300, 580, 1.2, t, RED, m=.4 * beat)
        ctx.save(); ctx.translate(960, 350); s = 1 + .12 * (beat + hb); sscale(ctx, s, s)
        ctx.new_path(); ctx.move_to(0, 60); ctx.curve_to(-120, -20, -60, -110, 0, -50); ctx.curve_to(60, -110, 120, -20, 0, 60); fill_stroke(ctx, PINK, NAVY, LW)
        ctx.restore()
        label(ctx, "BOOM + CRACK = THE HEART OF THE BEAT", 960, 820, 44, YELLOW, NAVY, scale=pop(t, ttog))
        for k, s, x in zip(bts, ["BOOM", "CRACK", "BOOM", "CRACK"], [620, 1300, 620, 1300]):
            sfx(ctx, t, k, s + "!", x, 260, 64, ORANGE if s == "BOOM" else RED, -.05, .9)

def clock(ctx, x, y, r, t, tick_t=None):
    circle(ctx, x, y, r, WHITE, NAVY, 8)
    for k in range(12):
        a = k * math.pi / 6; line(ctx, x + r * .8 * math.cos(a), y + r * .8 * math.sin(a), x + r * .9 * math.cos(a), y + r * .9 * math.sin(a), NAVY, 5)
    ang = -math.pi / 2 + (int(t * 2) % 60) * math.pi / 30 if tick_t is None else tick_t
    line(ctx, x, y, x + r * .75 * math.cos(ang), y + r * .75 * math.sin(ang), RED, 8); circle(ctx, x, y, 12, NAVY, None)

def sc_hihat(ctx, t):      # 144.4 - 174.26
    t0 = 144.4; tpress = wt('Press', 150); tlift = wt('Lift', 155); tplay = wt('You', 159); tclock = wt('clock', 165)
    ticks = [wt('Tick,', 168), wt('tick,', 169), wt('tick,', 169.5), wt('tick.', 170)]
    nameplate(ctx, t, t0, "HI-HAT", "THE CLOCK!" if t > tclock else None, col=GOLD_D)
    if t < tpress: op = .5
    elif t < tlift: op = lerp(.5, 0, smooth(prog(t, tpress, .4)))
    elif t < tplay: op = lerp(0, 1, smooth(prog(t, tlift, .4)))
    else: op = .1 + .1 * math.sin(t * 6)
    if t < tclock - .3:
        hihat(ctx, 960, 420, 1.5, t, open_=op)
        if t > wt('left', 149): label(ctx, "LEFT FOOT PEDAL", 1450, 640, 40, ORANGE, WHITE, scale=pop(t, wt('left', 149)))
        if tpress <= t < tlift: label(ctx, "CLOSED = TIGHT TICK", 1450, 420, 44, TEAL, WHITE, scale=pop(t, wt('tight', 153)))
        if tlift <= t < tplay: label(ctx, "OPEN = SPLASHY SIZZLE", 1450, 420, 44, PINK, WHITE, scale=pop(t, wt('sizzle.', 158)))
        if t >= tplay: label(ctx, "STICK + FOOT", 1450, 420, 44, YELLOW, NAVY, scale=pop(t, tplay))
    else:
        hihat(ctx, 560, 420, 1.1, t, open_=.1)
        tick_ang = -math.pi / 2
        for i, k in enumerate(ticks):
            if t >= k: tick_ang = -math.pi / 2 + (i + 1) * math.pi / 6
        clock(ctx, 1330, 450, 230, t, tick_ang if t < ticks[-1] + 1.2 else None)
        label(ctx, "KEEPS THE TIME STEADY", 1330, 770, 44, YELLOW, NAVY, scale=pop(t, wt('steady.', 167)))
        for i, k in enumerate(ticks): sfx(ctx, t, k, "TICK!", 560 + (i - 1.5) * 120, 200, 46, TEAL, (-1) ** i * .1, .7)

def sc_toms(ctx, t):       # 174.26 - 207.38
    t0 = 174.26; track = wt('rack', 180); tfloor = wt('floor', 184); tsmall = wt('Small', 185); thit = wt('Hit', 190); tdrm = wt('Drummers', 195); tyou = wt("You'll", 201)
    nameplate(ctx, t, t0, "TOMS", "THE MELODY!", col=PURPLE)
    sizes = [(560, .8, PURPLE, "HIGH"), (960, 1.0, TEAL_D, "MID"), (1400, 1.25, BLUE_D, "LOW")]
    seq = [thit + .15 + i * .5 for i in range(3)]
    for i, (x, s, c, lab) in enumerate(sizes):
        b = max([30 * max(0, 1 - prog(t, k, .3)) for k in seq if t >= k and seq.index(k) == i] + [0])
        tom(ctx, x, 560, s, t, c, bounce=b)
        if tsmall <= t: label(ctx, lab, x, 800, 42, [PINK, TEAL, ORANGE][i], WHITE, scale=pop(t, tsmall + i * .4))
        if t >= seq[i] and t - seq[i] < .8: note(ctx, x + 60, 360 - 120 * prog(t, seq[i], .8), 1.4, YELLOW, 1 - prog(t, seq[i], .8))
    if track <= t < tsmall:
        label(ctx, "RACK TOMS", 760, 330, 40, WHITE, NAVY, scale=pop(t, track))
        if t > tfloor: label(ctx, "FLOOR TOM", 1400, 330, 40, WHITE, NAVY, scale=pop(t, tfloor))
    if thit <= t < tdrm:
        # tune tumbling down a slide
        p = prog(t, wt('tune', 192), 1.6)
        if p > 0:
            x = lerp(420, 1500, p); y = lerp(300, 420, p) + 30 * abs(math.sin(p * 9))
            line(ctx, 420, 320, 1500, 460, WHITE, 8, .6); note(ctx, x, y, 1.6, YELLOW, 1.0, p * 6, True)
    if t >= tdrm:
        label(ctx, "FILLS!", 960, 300, 80, YELLOW, NAVY, scale=pop(t, wt('fills,', 196)), rot=-.05)
        if t > tyou: label(ctx, "COMING IN A FUTURE EPISODE", 960, 410, 40, PINK, WHITE, scale=pop(t, tyou))

def sc_cymbals(ctx, t):    # 207.38 - 238.82
    t0 = 207.38; tcr = wt('crash', 209); thit = wt('Hit', 211); tfw = wt('fireworks.', 217); tride = wt('ride', 222); tping = wt('ping', 229); tsum = wt('Crash', 235)
    if t < tride - .3:
        nameplate(ctx, t, tcr - .2, "CRASH CYMBAL", "THE FIREWORKS!" if t > tfw - .2 else None, col=GOLD_D)
        wb = max(0, 1 - prog(t, thit, 2.0)) if t >= thit else 0
        stand(ctx, 960, 520, 950, 1.2); cymbal(ctx, 960, 520, 300, t, GOLD, True, wobble=wb, m=.5 * wb)
        if t > thit:
            for k in range(3): confetti(ctx, 600 + k * 360, 360, t - thit - k * .4, seed=40 + k, n=40, spread=420, dur=2.0)
            sfx(ctx, t, thit, "CRASH!", 1450, 380, 80, PINK, -.08, 1.6)
        if t > wt('start', 219): label(ctx, "FOR BIG MOMENTS!", 960, 830, 48, YELLOW, NAVY, scale=pop(t, wt('start', 219)))
    elif t < tsum - .2:
        nameplate(ctx, t, tride - .3, "RIDE CYMBAL", "THE STEADY PING!" if t > tping else None, col=(0.85, 0.6, 0.15))
        stand(ctx, 960, 520, 950, 1.2); cymbal(ctx, 960, 520, 340, t, (0.92, 0.72, 0.30), True, wobble=.15, look=-.3)
        if t > wt('biggest', 224): label(ctx, "THE BIGGEST", 1500, 640, 44, WHITE, NAVY, scale=pop(t, wt('biggest', 224)))
        if t > tping:
            ph = (t - tping) % .6
            text(ctx, "PING!", 1480 + wob(t, .5, 20), 400 - 60 * ph, 60, TEAL, NAVY, alpha=1 - ph / .6)
    else:
        cymbal(ctx, 600, 500, 230, t, GOLD, True, wobble=.6); cymbal(ctx, 1320, 500, 250, t, (0.92, 0.72, 0.30), True, wobble=.1)
        label(ctx, "CRASH = FIREWORKS", 600, 780, 44, PINK, WHITE, scale=pop(t, tsum)); label(ctx, "RIDE = STEADY GROOVE", 1320, 780, 44, TEAL, WHITE, scale=pop(t, wt('ride', 236)))
        confetti(ctx, 600, 330, t - tsum, seed=60, n=40, spread=380)

def sc_team(ctx, t):       # 238.82 - 268.99
    t0 = 238.82
    ticks = [wt('Tick,', 243), wt('tick,', 244), wt('tick,', 244.5), wt('tick.', 245)]
    tk = wt('kick', 245); tsn = wt('snare', 248)
    beats = [wt('Boom,', 250), wt('crack,', 251), wt('boom,', 251.5), wt('crack.', 252)]
    tall = wt('All', 253); tbeat = wt('beat.', 255); tlearn = wt("You're", 256); tsee = wt('See?', 265)
    hits = {}
    period = .5
    if t >= ticks[0]: hits['hihat'] = max(0, 1 - ((t - ticks[0]) % period) / .25)
    if t >= tk and t < tsn: hits['kick'] = max(0, 1 - prog(t, wt('boom.', 246), .4)) if t > wt('boom.', 246) else 0
    if t >= tsn and t < beats[0]: hits['snare'] = max(0, 1 - prog(t, wt('crack.', 249), .4)) if t > wt('crack.', 249) else 0
    if t >= beats[0]:
        ph = ((t - beats[0]) % (2 * period * 2)) / (2 * period)
        hits['kick'] = max(0, 1 - (ph % 2) * 4) if ph < 1 else 0
        hits['snare'] = max(0, 1 - ((ph - 1) % 2) * 4) if ph >= 1 else 0
    glow = {}
    if tlearn <= t < tsee:
        for k, w in (('kick', 'kick,'), ('snare', 'snare,'), ('hihat', 'hi-hat.')):
            try:
                if t > wt(w, 262): glow[k] = 1
            except KeyError: pass
    full_kit(ctx, 960, 590, .85, t, hits, glow)
    title = "THE TEAM PLAYS!" if t < tbeat else ("THAT'S A DRUM BEAT!" if t < tlearn else ("NEXT VIDEO: PLAY IT!" if t < tsee else "YOU ALREADY KNOW A LOT!"))
    label(ctx, title, 960, 150, 60, YELLOW, NAVY, scale=pop(t, [t0, tbeat, tlearn, tsee][[t0, tbeat, tlearn, tsee].index(max(x for x in [t0, tbeat, tlearn, tsee] if x <= t))]), rot=-.02)
    if t >= ticks[0] and t < tbeat:
        clock(ctx, 1620, 330, 90, t)
        for i, k in enumerate(ticks): sfx(ctx, t, k, "TICK", 260, 300 + 0 * i, 40, TEAL, (-1) ** i * .1, .6)
    sfx(ctx, t, wt('boom.', 246), "BOOM!", 1560, 640, 60, ORANGE, .06, 1.0)
    sfx(ctx, t, wt('crack.', 249), "CRACK!", 360, 640, 60, RED, -.06, 1.0)
    for i, k in enumerate(beats): sfx(ctx, t, k, ["BOOM!", "CRACK!"][i % 2], [1560, 360][i % 2], 640, 56, [ORANGE, RED][i % 2], .05, .8)
    if t > tsee: confetti(ctx, 960, 400, t - tsee, seed=77, n=70, spread=800, dur=2.2)

def sc_recap2(ctx, t):     # 268.99 - 288.77
    t0 = 268.99
    items = [('snare', "Snare,", "SNARE", "THE CRACK", RED), ('kick', "Kick,", "KICK", "THE BOOM", RED), ('hihat', "Hi-hat,", "HI-HAT", "THE CLOCK", GOLD_D),
             ('toms', "Toms,", "TOMS", "THE MELODY", PURPLE), ('crash', "Crash,", "CRASH", "THE FIREWORKS", GOLD_D), ('ride', "Ride,", "RIDE", "THE STEADY PING", (0.85, 0.6, 0.15))]
    times = [wt(w, 270) for _, w, *_ in items]
    glow = {}; cur = None
    for (k, w, n, nick, c), tt in zip(items, times):
        if t >= tt: glow[k] = 1 if t - tt < 1.6 else .35; cur = (n, nick, c, tt)
    full_kit(ctx, 960, 620, .72, t, {k: max(0, 1 - prog(t, tt, .5)) for (k, *_), tt in zip(items, times) if t >= tt}, glow)
    tw0 = wt("That's", 281)
    if t < tw0: label(ctx, "SAY IT WITH ME!", 960, 150, 60, YELLOW, NAVY, scale=pop(t, t0))
    if cur and t < wt("That's", 281):
        n, nick, c, tt = cur
        label(ctx, f"{n} = {nick}", 960, 270, 62, c, WHITE, scale=pop(t, tt, .3), rot=wob(t, .8, .02))
    # little checklist
    for i, ((k, w, n, nick, c), tt) in enumerate(zip(items, times)):
        if t >= tt:
            x = 120 + (i % 2) * 1680; y = 330 + (i // 2) * 120
            label(ctx, n, x, y, 30, c, WHITE, scale=pop(t, tt))
    tw = wt("That's", 281)
    if t > tw:
        label(ctx, "THAT'S YOUR WHOLE KIT!", 960, 170, 66, GREEN, WHITE, scale=pop(t, tw))
        confetti(ctx, 960, 380, t - tw, seed=90, n=80, spread=900, dur=2.4)
    if t > wt('Say', 283): label(ctx, "SAY THEM OUT LOUD!", 960, 830, 44, PINK, WHITE, scale=pop(t, wt('Say', 283)))

def sitter(ctx, x, y, t, good=True):
    """Simple side-view seated drummer silhouette (no hands visible: arms hidden behind body)."""
    seat_h = 0 if good else 70
    throne(ctx, x, y + 60, 1.0, seat_h)
    hy = y + 40 - (0 if good else -70)      # hip height
    kx, ky = x + 170, (hy + 30 if good else hy - 40)   # knee
    capsule(ctx, x, hy, kx, ky, 34, PURPLE, NAVY, 5)
    capsule(ctx, kx, ky, kx + 10, y + 270, 30, PURPLE, NAVY, 5)
    rrect(ctx, kx - 20, y + 260, 110, 34, 14); fill_stroke(ctx, RED, NAVY, 5)
    lean = 0 if good else .35
    ctx.save(); ctx.translate(x, hy); ctx.rotate(lean)
    # back arm (behind torso)
    capsule(ctx, -5, -235, 60, -120, 24, lerpc(TEAL, NAVY, .25), NAVY, 5)
    capsule(ctx, 60, -120, 175, -150, 21, lerpc(TEAL, NAVY, .25), NAVY, 5)
    stick(ctx, 175, -150, -0.25, 230, 16, t=t)
    circle(ctx, 178, -150, 24, (0.93, .76, .6), NAVY, 5)
    rrect(ctx, -55, -280, 115, 280, 46); fill_stroke(ctx, TEAL, NAVY, 5)
    circle(ctx, 5, -350, 72, (1.0, .82, .66), NAVY, 5)
    # front arm
    capsule(ctx, 15, -225, 85, -110, 26, TEAL, NAVY, 5)
    capsule(ctx, 85, -110, 205, -125, 23, TEAL, NAVY, 5)
    stick(ctx, 205, -125, -0.2, 240, 18, t=t)
    circle(ctx, 208, -125, 27, (1.0, .82, .66), NAVY, 5)
    ctx.new_path(); ctx.arc(5, -365, 74, math.pi, math.pi * 1.95); ctx.close_path(); fill_stroke(ctx, (.35, .2, .1), NAVY, 5)
    circle(ctx, 45, -350, 8, NAVY, None)
    if good:
        ctx.new_path(); ctx.arc(40, -325, 16, .1 * math.pi, .8 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
    else:
        ctx.new_path(); ctx.arc(40, -305, 14, 1.15 * math.pi, 1.85 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()
    return (x, hy), (kx, ky)

def sc_bonus(ctx, t):      # 288.77 - 314.78
    t0 = 288.77; tadj = wt('Adjust', 294); tthr = wt('throne,', 295); tlow = wt('If', 304); tcomf = wt('A', 311)
    if t < tadj - .3:
        op = smooth(prog(t, t0 + .4, .8))
        gift(ctx, 960, 560, 1.6 * pop(t, t0), t, op, shake=1 - op)
        if op > 0:
            burst(ctx, 960, 420, 320 * ease_out(op), YELLOW, None, 20, t * .5, alpha=.8 * op)
            text(ctx, "BONUS TIP!", 960, 300, 140, YELLOW, NAVY, lw=22, scale=lerp(2, 1, back(prog(t, t0 + .5, .4))), alpha=clamp(prog(t, t0 + .5, .15) * 3))
            confetti(ctx, 960, 420, t - t0 - .4, seed=33, n=90, spread=900, dur=2.5)
        if t > wt('Where', 291): label(ctx, "WHERE YOU SIT MATTERS!", 960, 830, 50, PINK, WHITE, scale=pop(t, wt('Where', 291)))
    elif t < tlow - .2:
        (hx, hy), (kx, ky) = sitter(ctx, 760, 430, t, True)
        label(ctx, "THE THRONE", 420, 720, 44, YELLOW, NAVY, scale=pop(t, tthr))
        if t > wt('thighs', 296):
            line(ctx, hx - 60, hy, kx + 120, hy, WHITE, 5, .8, dash=[16, 12])
            label(ctx, "KNEES A LITTLE LOWER THAN HIPS", 1420, 460, 40, GREEN, WHITE, scale=pop(t, wt('knees', 297)), rot=.03)
            check(ctx, 1420, 330, .9, p=prog(t, wt('knees', 297) + .3, .4))
        if t > wt('feet', 302): label(ctx, "FEET RESTING ON THE PEDALS", 1420, 640, 40, TEAL, WHITE, scale=pop(t, wt('feet', 302)))
    elif t < tcomf - .2:
        sitter(ctx, 760, 430, t, False)
        label(ctx, "TOO LOW!", 1420, 330, 60, RED, WHITE, scale=pop(t, tlow))
        cross(ctx, 1420, 480, .9, p=prog(t, tlow + .3, .4))
        if t > wt('tired', 307): label(ctx, "TIRED LEGS & BACK", 1420, 620, 40, WHITE, NAVY, scale=pop(t, wt('tired', 307)))
        if t > wt("won't", 308): label(ctx, "NO BOUNCE!", 1420, 730, 40, ORANGE, WHITE, scale=pop(t, wt("won't", 308)))
    else:
        sitter(ctx, 760, 430, t, True)
        label(ctx, "COMFY = FASTER & HAPPIER!", 1420, 300, 44, GREEN, WHITE, scale=pop(t, tcomf), rot=-.03)
        for i in range(5): star(ctx, 1420 + 200 * math.cos(i * 1.256 + t), 560 + 90 * math.sin(i * 1.256 + t), 26 * pop(t, tcomf + .2), YELLOW, NAVY, 4)

def sc_outro(ctx, t):      # 314.78 - end
    t0 = 314.78; tnext = wt('Next', 317); tsub = wt('Subscribe', 322); tsee = wt('See', 324)
    if t < tnext - .2:
        full_kit(ctx, 960, 600, .85, t, glow={k: .6 for k in ('snare', 'kick', 'hihat', 'toms', 'crash', 'ride')})
        label(ctx, "YOU KNOW EVERY PIECE!", 960, 160, 64, GREEN, WHITE, scale=pop(t, t0))
        confetti(ctx, 960, 300, t - t0, seed=101, n=70, spread=900)
        return
    label(ctx, "NEXT EPISODE", 960, 140, 56, PINK, WHITE, scale=pop(t, tnext - .2))
    p = pop(t, tnext)
    ctx.save(); ctx.translate(680, 500); sscale(ctx, p * .9, p * .9)
    panel(ctx, 0, 0, 760, 460, WHITE)
    full_kit(ctx, 0, 40, .42, t, {'kick': max(0, math.sin(t * 6)), 'snare': max(0, -math.sin(t * 6)), 'hihat': .5 + .5 * math.sin(t * 12)})
    ctx.restore()
    label(ctx, "YOUR FIRST ROCK BEAT!", 680, 790, 46, YELLOW, NAVY, scale=pop(t, wt('rock', 319)), rot=-.03)
    sp = pop(t, tsub - .3)
    if sp > 0:
        clicked = t > tsub + .5; pulse = 1 + .06 * math.sin(t * 7)
        ctx.save(); ctx.translate(1430, 450); sscale(ctx, sp * pulse, sp * pulse)
        rrect(ctx, -230, -70, 460, 140, 70); fill_stroke(ctx, (0.55, 0.55, 0.6) if clicked else RED, NAVY, 7)
        text(ctx, "SUBSCRIBED!" if clicked else "SUBSCRIBE", 0, 0, 50 if clicked else 58, WHITE, NAVY); ctx.restore()
        confetti(ctx, 1430, 450, t - tsub - .5, seed=44, n=50, spread=600)
    if t > tsee: text(ctx, "SEE YOU NEXT TIME, DRUMMERS!", 1430, 680, 50, YELLOW, NAVY, scale=pop(t, tsee), rot=-.02)

SCENES = [(0, 20.84, sc_intro), (20.84, 38.22, sc_recap), (38.22, 74.48, sc_overview), (74.48, 110.18, sc_snare),
          (110.18, 144.4, sc_kick), (144.4, 174.26, sc_hihat), (174.26, 207.38, sc_toms), (207.38, 238.82, sc_cymbals),
          (238.82, 268.99, sc_team), (268.99, 288.77, sc_recap2), (288.77, 314.78, sc_bonus), (314.78, 999, sc_outro)]
TINTS = {sc_snare: RED, sc_kick: ORANGE, sc_hihat: GOLD, sc_toms: PURPLE, sc_cymbals: GOLD, sc_bonus: PURPLE, sc_outro: PINK}

def frame(ctx, t):
    s, e, fn = [x for x in SCENES if x[0] <= t < x[1]][0]
    background(ctx, t, TINTS.get(fn))
    ctx.save()
    out = smooth(prog(t, e - .18, .18)) if e < 900 else 0
    if out > 0: ctx.translate(960, 480); sscale(ctx, 1 - out, 1 - out); ctx.translate(-960, -480)
    fn(ctx, t); ctx.restore()
    if 0 < s and t - s < .2: ctx.set_source_rgba(1, 1, 1, .35 * (1 - (t - s) / .2)); ctx.paint()
    hud(ctx, t)
    if fn is not sc_intro or t > 9: narrator(ctx, t)
    captions(ctx, t)

def surface(t, scale):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale)); ctx = cairo.Context(s)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo); sscale(ctx, scale, scale); frame(ctx, t); return s

if __name__ == "__main__":
    if sys.argv[1] == "still":
        surface(float(sys.argv[2]), float(sys.argv[3])).write_to_png(sys.argv[4])
    else:
        f0, f1, sc, out = int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        crf = sys.argv[6] if len(sys.argv) > 6 else "20"
        w, h = int(W * sc), int(H * sc)
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", "-threads", "2", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            p.stdin.write(surface(f / FPS, sc).get_data())
            if f % 300 == 0: print(f"{out}: frame {f}", flush=True)
        p.stdin.close(); p.wait()
