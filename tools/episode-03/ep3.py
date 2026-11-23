"""Episode 3 - Your first rock beat in 5 minutes. Fully animated (no detailed hands: sleeve + round fist only).
usage: python3 ep3.py still T scale out.png
       python3 ep3.py range F0 F1 scale out.mp4 [crf]
Timeline = episode3_mix.mp3 (narration + 5 s synthesized drum loop inserted at loop_hits.json t_ins). Run prep.py + make_captions.py first.
"""
import sys, os, math, json, random, subprocess, re, bisect
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import *

FPS = 30
CUES = json.load(open(os.path.join(HERE, "cues.json")))
WORDS = json.load(open(os.path.join(HERE, "words_final.json")))
ENV = np.load(os.path.join(HERE, "env.npy"))
LOOP = json.load(open(os.path.join(HERE, "loop_hits.json")))
TOTAL = WORDS[-1]["end"] + 0.6
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
    if T_LOOP0 - .15 <= t < T_LOOP1: return        # no captions while the drum loop plays
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
    label(ctx, "EPISODE 3", 320, y, 30, PINK, WHITE)
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
    gift(ctx, x1 + 70, y + 8, .28, t, 0, shake=1.0 if GIFT_SHAKE[0] < t < GIFT_SHAKE[1] else 0)
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

def kick_side(ctx, x, y, t, press=0.0, sc=1.0):
    """Side view inset: drummer sits to the RIGHT; batter head faces right; beater swings front-to-back into the head."""
    if sc <= 0.01: return
    ctx.save(); ctx.translate(x, y); sscale(ctx, sc, sc)
    panel(ctx, 0, 0, 520, 470, WHITE)
    text(ctx, "SIDE VIEW", 0, -195, 30, NAVY, None, shadow=False)
    fl = 190                                   # floor line
    line(ctx, -240, fl, 240, fl, (0.75, 0.78, 0.85), 4)
    # drum shell seen from the side (round heads on left/right edges)
    hx = -10                                   # batter head x (faces the drummer, to the right)
    rrect(ctx, -200, -150, 190, 330, 18); fill_stroke(ctx, RED, NAVY, LW)
    ellipse(ctx, hx, 15, 18, 165, (0.97, 0.97, 0.99), NAVY, 5)
    ellipse(ctx, -200, 15, 14, 165, lerpc(RED, NAVY, .25), NAVY, 5)
    for k in range(4): rrect(ctx, -185 + k * 45, -150, 14, 330, 4); fill_stroke(ctx, CHROME, NAVY, 2)
    # pedal frame + axle
    ax, ay = hx + 75, fl - 95                 # axle low on the pedal frame
    line(ctx, ax - 10, fl, ax - 10, ay, DARK, 8)
    # footboard hinged at the heel (right); front end goes down when pressed
    heel = (ax + 190, fl - 8)
    fang = -0.42 + 0.30 * press
    fx = heel[0] - 175 * math.cos(fang); fy = heel[1] + 175 * math.sin(fang)
    capsule(ctx, heel[0], heel[1], fx, fy, 12, DARK, NAVY, 4)
    line(ctx, fx, fy, ax + 18, ay + 12, (0.4, 0.42, 0.5), 4)   # chain/strap
    # beater: rest leans back toward the drummer, press swings it forward into the head
    a = lerp(0.45, -0.39, press)               # pressed: ball lands on the CENTRE of the head
    L = 108
    bxp, byp = ax + L * math.sin(a), ay - L * math.cos(a)
    line(ctx, ax, ay, bxp, byp, CHROME, 9); line(ctx, ax, ay, bxp, byp, NAVY, 2)
    circle(ctx, bxp, byp, 26, (1, .95, .9), NAVY, 5)
    circle(ctx, ax, ay, 10, DARK, None)
    if press > .85:
        for k in range(3):
            line(ctx, hx - 10, byp - 40 + 40 * k, hx - 60, byp - 55 + 55 * k, ORANGE, 6)
    # foot hint arrow over the footboard
    mx, my = (heel[0] + fx) / 2, (heel[1] + fy) / 2 - 55
    ctx.new_path(); ctx.move_to(mx - 14, my - 34); ctx.line_to(mx + 14, my - 34); ctx.line_to(mx + 14, my - 6); ctx.line_to(mx + 28, my - 6)
    ctx.line_to(mx, my + 20); ctx.line_to(mx - 28, my - 6); ctx.line_to(mx - 14, my - 6); ctx.close_path(); fill_stroke(ctx, YELLOW, NAVY, 4, alpha=.9)
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


def clock(ctx, x, y, r, t, tick_t=None):
    circle(ctx, x, y, r, WHITE, NAVY, 8)
    for k in range(12):
        a = k * math.pi / 6; line(ctx, x + r * .8 * math.cos(a), y + r * .8 * math.sin(a), x + r * .9 * math.cos(a), y + r * .9 * math.sin(a), NAVY, 5)
    ang = -math.pi / 2 + (int(t * 2) % 60) * math.pi / 30 if tick_t is None else tick_t
    line(ctx, x, y, x + r * .75 * math.cos(ang), y + r * .75 * math.sin(ang), RED, 8); circle(ctx, x, y, 12, NAVY, None)

# ================================================================== Episode 3
SKIN = (1.0, .82, .66); SKIN_D = (0.93, .72, .55)
HH_C, SN_C, KK_C = GOLD_D, RED, ORANGE
PATTERN = {'hihat': set(range(8)), 'snare': {2, 6}, 'kick': {0, 4}}
ROWS = [('hihat', "HI-HAT", "RIGHT HAND", HH_C, TEAL), ('snare', "SNARE", "LEFT HAND", SN_C, GREEN), ('kick', "KICK", "RIGHT FOOT", KK_C, PINK)]
COLS = ["1", "&", "2", "&", "3", "&", "4", "&"]

T = {}   # key times
def _k(name, word, after): T[name] = wt(word, after)
for n, w, a in [('recap', 'In', 21), ('plan', "Here's", 44), ('cross', 'Now,', 66), ('l1', 'Layer', 81), ('l1play', 'Now', 101),
                ('l2', 'Layer', 123), ('l3', 'Layer', 152), ('slow', 'Now', 177), ('normal', 'Feeling', 205), ('listen', 'Listen', 220),
                ('tips', 'If', 230), ('recap2', "Let's", 255), ('bonus', 'You', 270), ('outro', 'Now', 300), ('next', 'Next', 303)]:
    _k(n, w, a)
SECTIONS = [(0, "START"), (T['plan'], "PLAN"), (T['l1'], "LAYER 1"), (T['l2'], "LAYER 2"), (T['l3'], "LAYER 3"),
            (T['slow'], "TOGETHER"), (T['tips'], "TIPS"), (T['bonus'], "BONUS"), (T['outro'], "NEXT")]
GIFT_SHAKE = (T['bonus'] - 8, T['bonus'])

# ---------- spoken counting -> beat events ----------
TOK = {"one": 'n', "two": 'n', "three": 'n', "four": 'n', "and": '&', "boom": 'b', "crack": 'c', "tick": 't'}
def layer_at(t):
    if t < T['recap']: return {'hihat', 'snare', 'kick'}          # hook plays the whole beat
    if t < T['l1play']: return set()                                # counting only
    if t < T['l2']: return {'hihat'}
    if t < T['l3']: return {'hihat', 'kick'}
    return {'hihat', 'snare', 'kick'}
BARS, COUNTINS, EVENTS = [], [], []    # bar: dict(t0,t1,words=[(t,col)],pieces) ; events: (t,col,pieces)
i = 0
while i < len(WORDS):
    j = i
    while j < len(WORDS) and norm(WORDS[j]["text"]) in TOK: j += 1
    run = WORDS[i:j]; k = 0
    while k < len(run):
        toks = [norm(w["text"]) for w in run[k:k + 4]]
        if toks == ["one", "two", "three", "four"]:
            COUNTINS.append([w["start"] for w in run[k:k + 4]]); k += 4
        elif len(run) - k >= 8 and norm(run[k]["text"]) in ("one", "boom"):
            ws = run[k:k + 8]; lay = layer_at(ws[0]["start"])
            BARS.append(dict(t0=ws[0]["start"], t1=ws[-1]["end"], words=[(w["start"], c) for c, w in enumerate(ws)], layer=lay))
            for c, w in enumerate(ws):
                EVENTS.append((w["start"], c, {p for p in lay if c in PATTERN[p]}))
            k += 8
        else: k += 1
    i = max(j, i + 1)
for h in LOOP["hits"]:
    EVENTS.append((h["t"], h["col"], set(h["pieces"])))
T_LOOP0 = LOOP["hits"][0]["t"]; T_LOOP1 = LOOP["hits"][-1]["t"] + 0.6
BARS.append(dict(t0=T_LOOP0, t1=T_LOOP1 - .3, words=[(h["t"], h["col"]) for h in LOOP["hits"][:8]], layer={'hihat', 'snare', 'kick'}))
BARS.append(dict(t0=LOOP["hits"][8]["t"], t1=T_LOOP1, words=[(h["t"], h["col"]) for h in LOOP["hits"][8:]], layer={'hihat', 'snare', 'kick'}))
BARS.sort(key=lambda b: b["t0"]); EVENTS.sort(key=lambda e: e[0])
for b in BARS:     # loop bars were added whole: fix first-bar end
    pass
PIECE_T = {p: [e[0] for e in EVENTS if p in e[2]] for p in PATTERN}

def hit(p, t, d=.28):
    """decay 1->0 after the most recent hit of piece p"""
    ts = PIECE_T[p]; k = bisect.bisect_right(ts, t) - 1
    return max(0.0, 1 - (t - ts[k]) / d) if k >= 0 else 0.0
def strike(p, t, w=.11):
    """0..1 stick-down amount, peaking exactly at each hit time"""
    ts = PIECE_T[p]; k = bisect.bisect_left(ts, t - w); best = 0.0
    for q in ts[k:k + 3]: best = max(best, 1 - clamp(abs(t - q) / w))
    return smooth(best)
def bar_at(t):
    for b in BARS:
        if b["t0"] - .05 <= t <= b["t1"] + .45: return b
    return None
def col_at(b, t):
    c = -1
    for (wt_, cc) in b["words"]:
        if t >= wt_: c = cc
    return c

# ---------- the beat chart ----------
def beat_chart(ctx, cx, cy, t, s=1.0, rows_on=('hihat', 'snare', 'kick'), alpha=1.0, highlight_row=None, highlight_cols=(), show_limbs=True, follow=True, band=True):
    ctx.save(); ctx.translate(cx, cy); sscale(ctx, s, s)
    cw, rh, lw_ = 92, 104, 300
    w = lw_ + cw * 8 + 40; h = rh * 4 + 40
    panel(ctx, 0, 0, w, h, WHITE, alpha)
    x0 = -w / 2 + lw_ + 20; y0 = -h / 2 + 20
    b = bar_at(t) if follow else None; cur = col_at(b, t) if b else -1
    lay = b["layer"] if b else set()
    # column highlight band for the current count
    if cur >= 0 and band:
        rrect(ctx, x0 + cur * cw + 4, y0 + 4, cw - 8, h - 48, 22); ctx.set_source_rgba(*YELLOW, .45 * alpha); ctx.fill()
    for c in highlight_cols:
        rrect(ctx, x0 + c * cw + 4, y0 + 4, cw - 8, h - 48, 22); ctx.set_source_rgba(*PINK, .35 * alpha); ctx.fill()
    # header numbers
    for c, lab in enumerate(COLS):
        sc = 1.0
        if b and cur >= 0:
            tw_ = [x for x, cc in b["words"] if cc == c]
            if tw_ and t >= tw_[0]: sc = 1 + .35 * max(0, 1 - (t - tw_[0]) / .25)
        text(ctx, lab, x0 + c * cw + cw / 2, y0 + rh / 2, 54 if lab != "&" else 44, NAVY if lab != "&" else (0.45, .5, .65), None, shadow=False, alpha=alpha, scale=sc)
    line(ctx, x0 - 10, y0 + rh, x0 + 8 * cw, y0 + rh, (0.8, .83, .9), 4, alpha)
    for r, (p, name, limb, col, lcol) in enumerate(ROWS):
        yy = y0 + rh * (r + 1) + rh / 2; on = p in rows_on; a = alpha * (1 if on else .22)
        if highlight_row == p:
            rrect(ctx, -w / 2 + 12, yy - rh / 2 + 6, w - 24, rh - 12, 26); ctx.set_source_rgba(*col, .22 * alpha); ctx.fill()
        # row icon
        ix = -w / 2 + 60
        if p == 'hihat':
            ellipse(ctx, ix, yy + 8, 38, 10, GOLD, NAVY, 4, a); ellipse(ctx, ix, yy - 4, 38, 10, GOLD, NAVY, 4, a)
        elif p == 'snare':
            rrect(ctx, ix - 36, yy - 14, 72, 34, 6); fill_stroke(ctx, RED, NAVY, 4, a); ellipse(ctx, ix, yy - 14, 36, 9, WHITE, NAVY, 4, a)
        else:
            circle(ctx, ix, yy, 34, RED, NAVY, 4, a); circle(ctx, ix, yy, 25, WHITE, NAVY, 3, a)
        text(ctx, name, ix + 52, yy - (14 if show_limbs else 0), 36, col if on else NAVY, None, align="left", shadow=False, alpha=a)
        if show_limbs: text(ctx, limb, ix + 52, yy + 22, 22, (0.35, .4, .55), None, align="left", shadow=False, alpha=a, weight="semi")
        for c in range(8):
            x = x0 + c * cw + cw / 2
            if c in PATTERN[p] and on:
                lit = False; pop_ = 0.0
                if b and p in lay and c <= cur:
                    lit = True
                    tw_ = [x_ for x_, cc in b["words"] if cc == c][0]
                    pop_ = max(0, 1 - (t - tw_) / .3)
                if lit:
                    circle(ctx, x, yy, 34 + 12 * pop_, col, NAVY, 5, alpha)
                    if pop_ > 0: circle(ctx, x, yy, 34 + 40 * (1 - pop_), YELLOW, None, alpha=alpha * .5 * pop_)
                    if p == 'hihat': line(ctx, x - 12, yy - 12, x + 12, yy + 12, WHITE, 6, alpha); line(ctx, x + 12, yy - 12, x - 12, yy + 12, WHITE, 6, alpha)
                else:
                    circle(ctx, x, yy, 30, lerpc(col, WHITE, .55), lerpc(col, NAVY, .3), 4, alpha * .9)
            else:
                circle(ctx, x, yy, 9, (0.85, .87, .93), None, alpha=a)
    ctx.restore()

def countin(ctx, t, x=960, y=330):
    for ts in COUNTINS:
        for i, q in enumerate(ts):
            nxt = ts[i + 1] if i + 1 < 4 else q + .55
            if q <= t < nxt:
                text(ctx, str(i + 1), x, y, 240, YELLOW, NAVY, lw=26, scale=lerp(1.6, 1, back(prog(t, q, .25))), alpha=1 - prog(t, nxt - .1, .1), rot=wob(t, 2, .05))

# ---------- kit with closed hi-hat + sticks that land on the top heads ----------
def ep3_kit(ctx, cx, cy, s, t, glow=None, sticks=True, faces=True, bursts=True, stick_style="classic"):
    glow = glow or {}
    hk, hs, hh = hit('kick', t), hit('snare', t), hit('hihat', t)
    def gl(p, x, y, r):
        g = glow.get(p, 0)
        if g > 0: circle(ctx, x, y, r, YELLOW, None, alpha=.35 * g)
    ctx.save(); ctx.translate(cx, cy); sscale(ctx, s, s)
    stand(ctx, 430, -230, 260); stand(ctx, -390, -300, 260)
    cymbal(ctx, -390, -300, 150, t, GOLD, faces, look=.4)
    cymbal(ctx, 430, -230, 175, t, (0.92, 0.72, 0.30), faces, look=-.4)
    gl('hihat', -560, -40, 160)
    hihat(ctx, -560, -40 + 4 * hh, .75, t, open_=.05)          # always CLOSED (left foot holds the pedal down)
    for tx, bc in [(-150, PURPLE), (120, TEAL_D)]: tom(ctx, tx, -150, .62, t, bc)
    gl('kick', 0, 110, 240)
    kick(ctx, 0, 110, .78, t, m=.6 * hk, boom=hk)
    tom(ctx, 330, 130, .78, t, BLUE_D)
    for dx in (-60, 60): line(ctx, 330 + dx, 190, 330 + dx * 1.2, 300, CHROME, 8)
    gl('snare', -330, 150, 150)
    tom(ctx, -330, 150, .74, t, RED, m=.5 * hs)
    stand(ctx, -330, 215, 300, .9)
    if sticks:
        if stick_style == "plan":
            # "who plays what" scene only: hi-hat stick straight down between the label and the crash,
            # snare stick in from the left (above the LEFT HAND label, under the hi-hat)
            d = strike('hihat', t); tx, ty = -590, lerp(-125, -52, d)
            bx, by = -590, lerp(-400, -330, d)
            stick(ctx, bx, by, math.pi / 2, ty - by - 16, 22, t=t)
            d = strike('snare', t); tx, ty = -320, lerp(22, 92, d)
            bx, by = -820, lerp(40, 55, d)
            stick(ctx, bx, by, math.atan2(ty - by, tx - bx), math.hypot(tx - bx, ty - by) - 16, 22, t=t)
        else:
            # all other scenes (approved look): both sticks come in from the upper right
            d = strike('hihat', t); tx, ty = -540, lerp(-150, -52, d)
            bx, by = -250, lerp(-330, -300, d)
            stick(ctx, bx, by, math.atan2(ty - by, tx - bx), math.hypot(tx - bx, ty - by) - 16, 22, t=t)
            d = strike('snare', t); tx, ty = -310, lerp(10, 90, d)
            bx, by = -40, lerp(-60, -30, d)
            stick(ctx, bx, by, math.atan2(ty - by, tx - bx), math.hypot(tx - bx, ty - by) - 16, 22, t=t)
    ctx.restore()
    if bursts:
        for p, word, x, y, c in (('kick', "BOOM!", 0, 300, ORANGE), ('snare', "CRACK!", -250, 330, RED), ('hihat', "TICK!", -560, -230, TEAL)):
            ts = PIECE_T[p]; k = bisect.bisect_right(ts, t) - 1
            if k >= 0 and t - ts[k] < .45:
                sfx(ctx, t, ts[k], word, cx + x * s, cy + y * s, 70 * s + 14, c, (-.08 if p == 'snare' else .07), .45)

def fist(ctx, x, y, r=30, col=SKIN):
    circle(ctx, x, y, r, col, NAVY, 5)
def arm(ctx, x0, y0, x1, y1, sleeve, r=26):
    capsule(ctx, x0, y0, x1, y1, r, sleeve, NAVY, 5)

def turtle(ctx, x, y, s=1.0, t=0.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    for dx in (-40, 40): ellipse(ctx, dx, 34, 18, 12, GREEN, NAVY, 4)
    circle(ctx, 78 + wob(t, 1.5, 4), -4, 24, GREEN, NAVY, 4); circle(ctx, 86, -10, 5, NAVY, None)
    ctx.new_path(); ctx.arc(0, 20, 70, math.pi, 2 * math.pi); ctx.close_path(); fill_stroke(ctx, (0.15, .6, .35), NAVY, 5)
    for dx in (-30, 0, 30): circle(ctx, dx, -10, 12, (0.3, .75, .45), None)
    ctx.restore()

def flame(ctx, x, y, s=1.0, t=0.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    for k, (c, sz) in enumerate(((ORANGE, 1.0), (YELLOW, .62))):
        f = 1 + .08 * math.sin(t * 14 + k)
        ctx.new_path(); ctx.move_to(0, -90 * sz * f); ctx.curve_to(50 * sz, -30 * sz, 60 * sz, 40 * sz, 0, 60 * sz)
        ctx.curve_to(-60 * sz, 40 * sz, -50 * sz, -30 * sz, 0, -90 * sz * f); fill_stroke(ctx, c, NAVY if k == 0 else None, 5)
    ctx.restore()

def lesson_card(ctx, x, y, s, n, title):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    panel(ctx, 0, 0, 520, 300, WHITE)
    rrect(ctx, -240, -130, 480, 200, 24); fill_stroke(ctx, (0.17, .55, 1.0), NAVY, 5)
    ctx.new_path(); ctx.move_to(-28, -70); ctx.line_to(42, -30); ctx.line_to(-28, 10); ctx.close_path(); fill_stroke(ctx, WHITE, NAVY, 5)
    text(ctx, f"LESSON {n}", 0, 100, 40, NAVY, None, shadow=False); text(ctx, title, 0, 134, 22, (0.35, .4, .55), None, shadow=False, weight="semi")
    ctx.restore()

# ---------- scenes ----------
def sc_intro(ctx, t):
    sh = 8 * max(0, 1 - t / .4)
    ctx.save(); ctx.translate(wob(t, 23, sh), wob(t, 19, sh, 1.3))
    ep3_kit(ctx, 960, 590 + 400 * (1 - back(prog(t, 0, .6))), .95, t)
    ctx.restore()
    tr = wt('rock', 6)
    if t >= tr - .1:
        ctx.save(); ctx.set_source_rgba(*NAVY, .35 * smooth(prog(t, tr - .1, .4))); ctx.paint(); ctx.restore()
        p = back(prog(t, tr - .1, .45))
        text(ctx, "YOUR FIRST", 960, 250, 120, WHITE, NAVY, lw=20, scale=lerp(2.2, 1, p), alpha=clamp(p * 3), rot=-.03)
        text(ctx, "ROCK BEAT!", 960, 390, 160, YELLOW, NAVY, lw=24, scale=lerp(2.2, 1, back(prog(t, tr + .25, .45))), alpha=clamp(prog(t, tr + .25, .15)), rot=.02)
        tf = wt('five', 10)
        if t > tf: label(ctx, "IN 5 MINUTES", 960, 540, 56, PINK, WHITE, scale=pop(t, tf), rot=-.03)
        ty = wt('yourself.', 12)
        if t > ty: label(ctx, "YOU'LL PLAY IT YOURSELF!", 960, 650, 46, GREEN, WHITE, scale=pop(t, ty), rot=.02)
        tb = wt('bonus', 15)
        if t > tb:
            gift(ctx, 600, 800, .8 * pop(t, tb), t, 0, shake=1)
            label(ctx, "BONUS TRICK AT THE END!", 1130, 800, 42, YELLOW, NAVY, scale=pop(t, tb + .2), rot=.04)
        tk = wt('without', 19)
        if t > tk: label(ctx, "NO DRUM KIT NEEDED!", 1130, 890, 34, WHITE, NAVY, scale=pop(t, tk), rot=-.03)

def sc_recap(ctx, t):
    t0 = T['recap']; tg = wt('grab', 40)
    if t < tg - .25:
        label(ctx, "LAST TIME: MEET THE TEAM", 960, 160, 54, WHITE, NAVY, scale=pop(t, t0))
        items = [('kick,' if False else 'kick', "KICK", "THE BOOM", 520), ('snare', "SNARE", "THE CRACK", 960), ('hi-hat', "HI-HAT", "THE CLOCK", 1400)]
        tteam = wt('team.', 32); bounce = 0
        if t > tteam: bounce = 30 * abs(math.sin((t - tteam) * 6)) * max(0, 1 - (t - tteam) / 2.5)
        for k, (w, name, nick, x) in enumerate(items):
            tk = wt(w, 24)
            if t < tk: continue
            p = pop(t, tk); y = 470 - bounce * (1 if k != 1 else -1) * 0 - bounce
            ctx.save(); ctx.translate(x, y); sscale(ctx, p, p)
            if name == "KICK": kick(ctx, 0, 0, .55, t, m=.3)
            elif name == "SNARE": tom(ctx, 0, 0, 1.0, t, RED)
            else: hihat(ctx, 0, -40, .85, t, open_=.05)
            ctx.restore()
            label(ctx, name, x, 680, 46, [KK_C, SN_C, HH_C][k], WHITE, scale=pop(t, tk + .1))
            label(ctx, nick, x, 765, 36, YELLOW, NAVY, scale=pop(t, tk + .35), rot=wob(t, .6, .03, k))
        if t > wt('Today,', 33):
            label(ctx, "TODAY: YOU JOIN THE TEAM!", 960, 270, 48, PINK, WHITE, scale=pop(t, wt('Today,', 33)), rot=-.02)
        tm = wt('missed', 35)
        if t > tm:
            ctx.save(); ctx.set_source_rgba(*NAVY, .45 * smooth(prog(t, tm, .3))); ctx.paint(); ctx.restore()
            lesson_card(ctx, 960, 500, pop(t, tm) * 1.1, 2, "THE DRUM KIT EXPLAINED")
            label(ctx, "WATCH LESSON 2 FIRST!", 960, 760, 44, YELLOW, NAVY, scale=pop(t, tm + .3))
    else:
        for sgn in (-1, 1):
            a = -math.pi / 2 + sgn * .4 + wob(t, 2, .15, sgn)
            stick(ctx, 960 - sgn * 160, 760, a, 520, 40, face="smile", t=t + sgn)
        ts = wt('sit', 41)
        if t > ts: throne(ctx, 1500, 640, 1.2 * pop(t, ts))
        title = back(prog(t, tg - .2, .4))
        text(ctx, "GRAB YOUR STICKS!", 960, 230, 110, YELLOW, NAVY, lw=18, scale=lerp(2, 1, title), alpha=clamp(title * 3), rot=-.03)
        tb = wt('build', 43)
        if t > tb: label(ctx, "LET'S BUILD A BEAT!", 960, 360, 54, PINK, WHITE, scale=pop(t, tb))
        confetti(ctx, 960, 400, t - tg, seed=8, n=50, spread=700)

def block(ctx, x, y, w, h, col, s, txt, sub):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    rrect(ctx, -w / 2 + 6, -h / 2 + 10, w, h, 22); ctx.set_source_rgba(*NAVY, .3); ctx.fill()
    rrect(ctx, -w / 2, -h / 2, w, h, 22); fill_stroke(ctx, col, NAVY, LW)
    for dx in (-w / 4, w / 4): ellipse(ctx, dx, -h / 2, 34, 12, lerpc(col, WHITE, .3), NAVY, 4)
    text(ctx, txt, 0, -10, 52, WHITE, NAVY); text(ctx, sub, 0, 38, 28, NAVY, None, shadow=False, weight="semi")
    ctx.restore()

def sc_plan(ctx, t):
    t0 = T['plan']; tyour = wt('Your', 51); tleft = wt('Your', 57)
    if t < tyour - .25:
        label(ctx, "THE PLAN: BUILD IT IN LAYERS", 960, 170, 56, YELLOW, NAVY, scale=pop(t, wt('layers,', 46)))
        for k, (w, txt, sub, col) in enumerate([('one', "HI-HAT", "LAYER 1", HH_C), ('piece', "KICK", "LAYER 2", KK_C), ('time,', "SNARE", "LAYER 3", SN_C)]):
            tk = wt(w, 47.5); p = prog(t, tk, .45)
            if p <= 0: continue
            y = lerp(-200, 760 - k * 175, ease_out(p)); sq = 1 + .12 * math.sin(math.pi * clamp((p - .8) / .2)) if p > .8 else 1
            block(ctx, 960, y, 520, 150, col, 1, txt, sub)
        if t > wt('stacking', 49): label(ctx, "LIKE STACKING BLOCKS!", 1540, 560, 40, PINK, WHITE, scale=pop(t, wt('stacking', 49)), rot=.04)
        return
    glow = {}
    for p, w, a in (('hihat', 'hi-hat,', 52), ('snare', 'snare,', 54), ('kick', 'kick', 56)):
        tk = wt(w, a)
        if t >= tk - .3: glow[p] = 1 if t < tleft else .4
    ep3_kit(ctx, 820, 560, .82, t, glow, bursts=False, stick_style="plan")
    # limb stickers right next to their piece
    hx, hy = 820 - 560 * .82, 560 - 40 * .82          # hi-hat centre on screen
    sx, sy = 820 - 330 * .82, 560 + 150 * .82         # snare centre on screen
    tr = wt('right', 51); th = wt('hi-hat,', 52)
    if t >= tr:   # RIGHT HAND / = HI-HAT: upper left, pointer line down to the hi-hat (creator's preferred version)
        line(ctx, 300, 440, hx - 40, hy - 10, WHITE, 6, .8 * clamp(prog(t, tr, .3)), dash=[14, 10])
        label(ctx, "RIGHT HAND", 175, 430, 40, TEAL, WHITE, scale=pop(t, tr))
        if t >= th: label(ctx, "= HI-HAT", 175, 498, 32, WHITE, NAVY, scale=pop(t, th))
    tl = wt('left', 53); ts = wt('snare,', 54)
    if t >= tl:   # LEFT HAND / = SNARE: to the left of the snare
        line(ctx, 335, sy + 10, sx - 100, sy + 5, WHITE, 6, .8 * clamp(prog(t, tl, .3)), dash=[14, 10])
        label(ctx, "LEFT HAND", 215, sy + 10, 40, GREEN, WHITE, scale=pop(t, tl))
        if t >= ts: label(ctx, "= SNARE", 215, sy + 78, 32, WHITE, NAVY, scale=pop(t, ts))
    tf = wt('right', 55); tk = wt('kick', 56)
    if t >= tf:
        line(ctx, 1500, 860, 820, 560 + 230 * .82, WHITE, 6, .8 * clamp(prog(t, tf, .3)), dash=[14, 10])
        label(ctx, "RIGHT FOOT", 1500, 860, 40, PINK, WHITE, scale=pop(t, tf))
        if t >= tk: label(ctx, "= KICK PEDAL", 1500, 940, 32, WHITE, NAVY, scale=pop(t, tk))
    if t >= tleft:
        # left-foot inset: hi-hat pedal held DOWN -> cymbals closed
        p = pop(t, tleft)
        ctx.save(); ctx.translate(1560, 420); sscale(ctx, p, p)
        panel(ctx, 0, 0, 470, 560, WHITE)
        text(ctx, "LEFT FOOT", 0, -235, 34, NAVY, None, shadow=False)
        hihat(ctx, 0, -110, .7, t, open_=0.0)
        tp = wt('pressed', 60)
        if t > tp:
            ax, ay = 120, 150
            ctx.new_path(); ctx.move_to(ax - 14, ay - 70); ctx.line_to(ax + 14, ay - 70); ctx.line_to(ax + 14, ay - 20); ctx.line_to(ax + 30, ay - 20)
            ctx.line_to(ax, ay + 14); ctx.line_to(ax - 30, ay - 20); ctx.line_to(ax - 14, ay - 20); ctx.close_path(); fill_stroke(ctx, YELLOW, NAVY, 4)
            label(ctx, "PEDAL DOWN", 0, 230, 34, ORANGE, WHITE, scale=pop(t, tp))
        ctx.restore()
        tc = wt('closed', 63)
        if t > tc: label(ctx, "CLOSED = TIGHT TICK", 1560, 760, 38, TEAL, WHITE, scale=pop(t, tc), rot=-.02)
        if t > wt('easiest', 59): label(ctx, "EASIEST JOB!", 1560, 120, 40, PINK, WHITE, scale=pop(t, wt('easiest', 59)), rot=.03)

def topdown(ctx, t, cross_p):
    """Bird's-eye view: drummer at the bottom facing up. Right arm crosses OVER the left to reach the hi-hat."""
    cx = 960
    # kit from above
    rrect(ctx, cx - 40, 150, 260, 210, 40); fill_stroke(ctx, RED, NAVY, LW)              # kick (seen from above)
    rrect(ctx, cx - 10, 170, 200, 170, 34); fill_stroke(ctx, (0.97, .97, .99), NAVY, 4)
    circle(ctx, cx - 300, 380, 120, GOLD, NAVY, LW); circle(ctx, cx - 300, 380, 85, lerpc(GOLD, WHITE, .25), None)
    circle(ctx, cx - 300, 380, 22, GOLD_D, NAVY, 4)                                                       # hi-hat
    circle(ctx, cx - 40, 470, 115, (0.97, .97, .99), NAVY, LW); circle(ctx, cx - 40, 470, 98, WHITE, None)  # snare head
    circle(ctx, cx + 330, 470, 125, (0.95, .95, .98), NAVY, LW)                                           # floor tom
    text(ctx, "HI-HAT", cx - 300, 220, 34, WHITE, NAVY); text(ctx, "SNARE", cx + 120, 395, 30, WHITE, NAVY)
    # drummer from above
    sl, sr = (cx - 120, 800), (cx + 120, 800)
    lf = (cx - 60, 640)                                                       # left fist (stays low, over the snare edge)
    rf = (lerp(cx + 150, cx - 170, cross_p), lerp(660, 560, cross_p))        # right fist crosses over to the left
    ellipse(ctx, cx, 830, 200, 80, TEAL, NAVY, LW)                            # shoulders
    arm(ctx, sl[0], sl[1], lf[0], lf[1], lerpc(TEAL, NAVY, .1))
    stick(ctx, lf[0], lf[1], math.atan2(480 - lf[1], (cx - 20) - lf[0]), math.hypot(480 - lf[1], (cx - 20) - lf[0]) - 10, 22, t=t)
    fist(ctx, *lf)
    tipx, tipy = lerp(cx + 330, cx - 290, cross_p), lerp(470, 390, cross_p)
    arm(ctx, sr[0], sr[1], rf[0], rf[1], TEAL)
    stick(ctx, rf[0], rf[1], math.atan2(tipy - rf[1], tipx - rf[0]), math.hypot(tipy - rf[1], tipx - rf[0]) - 10, 22, t=t)
    fist(ctx, *rf)
    circle(ctx, cx, 870, 78, (.35, .2, .1), NAVY, LW)                          # head (hair, seen from above)

def sc_cross(ctx, t):
    tc = wt('crosses', 71); tx_ = wt('X.', 74); tn = wt('totally', 75); ta = wt('Almost', 76)
    cp = smooth(prog(t, tc - .2, .9))
    ctx.save(); ctx.translate(0, -40); topdown(ctx, t, cp); ctx.restore()
    label(ctx, "VIEW FROM ABOVE", 300, 170, 36, WHITE, NAVY, scale=pop(t, T['cross'] + .2))
    if t < tc: label(ctx, "MIGHT FEEL FUNNY...", 1560, 260, 44, YELLOW, NAVY, scale=pop(t, wt('funny.', 68)), rot=.03)
    else:
        label(ctx, "RIGHT HAND CROSSES OVER", 1560, 260, 40, TEAL, WHITE, scale=pop(t, tc), rot=.03)
    if t > tx_:
        p = back(prog(t, tx_, .35)); x, y, r = 900, 640, 130 * p
        line(ctx, x - r, y - r, x + r, y + r, PINK, 22, .85); line(ctx, x + r, y - r, x - r, y + r, PINK, 22, .85)
        text(ctx, "X", 1560, 440, 200, PINK, NAVY, lw=24, scale=p, rot=wob(t, 1.5, .08))
    if t > tn:
        label(ctx, "TOTALLY NORMAL!", 1560, 640, 50, GREEN, WHITE, scale=pop(t, tn), rot=-.03)
        check(ctx, 1560, 780, .8, p=prog(t, tn + .3, .4))
    if t > ta: label(ctx, "ALMOST EVERY DRUMMER PLAYS THIS WAY", 960, 150, 40, YELLOW, NAVY, scale=pop(t, ta))

def chart_scene(ctx, t, rows_on, title, title_t, col, glow=None, chart_kw=None):
    nameplate(ctx, t, title_t, title, None, x=960, y=150, col=col)
    ep3_kit(ctx, 470, 560, .52, t, glow or {})
    beat_chart(ctx, 1330, 545, t, .78, rows_on, **(chart_kw or {}))

def sc_layer1(ctx, t):
    tsay = wt('Say', 90); tclock = wt('clock', 100); tplay = T['l1play']; tei = wt('eight', 109); trel = wt('relaxed,', 113); tsh = wt('shaky,', 117); tst = wt('Steady', 119)
    if t < tsay - .2:
        nameplate(ctx, t, T['l1'], "LAYER 1: THE CLOCK", None, x=960, y=150, col=HH_C)
        clock(ctx, 600, 560, 200, t)
        tc = wt('count.', 85)
        if t > tc: text(ctx, "LET'S COUNT!", 1330, 400, 90, YELLOW, NAVY, scale=pop(t, tc), rot=-.03)
        tf = wt('four', 86)
        if t > tf: label(ctx, "4 COUNTS", 1330, 560, 54, PINK, WHITE, scale=pop(t, tf))
        ta = wt('and', 89.2)
        if t > ta: label(ctx, "+ AN \"AND\" IN BETWEEN", 1330, 680, 46, TEAL, WHITE, scale=pop(t, ta))
        return
    chart_scene(ctx, t, ('hihat',) if t >= tplay else (), "LAYER 1: THE CLOCK", T['l1'], HH_C, {'hihat': 1 if t >= tplay else 0})
    if t < tplay:
        label(ctx, "SAY IT WITH ME!", 1330, 800, 44, PINK, WHITE, scale=pop(t, tsay))
        if t > tclock: clock(ctx, 1770, 260, 80, t)
    else:
        if t < tei: label(ctx, "HI-HAT ON EVERY COUNT", 1330, 800, 40, YELLOW, NAVY, scale=pop(t, tplay))
        elif t < trel: label(ctx, "8 TICKS IN A ROW!", 1330, 800, 44, TEAL, WHITE, scale=pop(t, tei))
        elif t < tsh: label(ctx, "RELAXED GRIP + BOUNCE", 1330, 800, 42, GREEN, WHITE, scale=pop(t, trel))
        elif t < tst: label(ctx, "SHAKY? SLOW DOWN!", 1330, 800, 44, ORANGE, WHITE, scale=pop(t, tsh))
        else: label(ctx, "STEADY BEATS FAST!", 1330, 800, 48, PINK, WHITE, scale=pop(t, tst), rot=-.02)

def sc_layer2(ctx, t):
    tfoot = wt('foot', 130); tcount = wt("Let's", 137); thear = wt('Hear', 147); ttog = wt('together,', 149)
    rows = ('hihat', 'kick')
    if tfoot - .2 <= t < tcount - .2:
        nameplate(ctx, t, T['l2'], "LAYER 2: ADD THE BOOM", None, x=960, y=150, col=KK_C)
        press = 0
        for k in (wt('down', 131), wt('forward', 134)):
            if t >= k: press = max(press, 1 - prog(t, k + .35, .4)) if t < k + .75 else press
            if k <= t < k + .35: press = smooth(prog(t, k, .2))
        kick_side(ctx, 620, 560, t, press, pop(t, tfoot - .2) * 1.05)
        label(ctx, "SAME MOMENT AS YOUR RIGHT HAND", 1400, 420, 38, TEAL, WHITE, scale=pop(t, wt('same', 132)))
        tb = wt('beater', 134)
        if t > tb: label(ctx, "BEATER SWINGS FORWARD...", 1400, 560, 40, ORANGE, WHITE, scale=pop(t, tb))
        if t > wt('bounces', 136): label(ctx, "...AND BOUNCES BACK", 1400, 670, 40, YELLOW, NAVY, scale=pop(t, wt('bounces', 136)))
        return
    chart_scene(ctx, t, rows, "LAYER 2: ADD THE BOOM", T['l2'], KK_C, {'kick': 1})
    if t < tfoot:
        label(ctx, "KICK ON 1 AND 3", 1330, 800, 46, ORANGE, WHITE, scale=pop(t, wt('one', 128)))
    elif t < thear:
        label(ctx, "SAY \"BOOM\" ON THE KICK!", 1330, 800, 42, PINK, WHITE, scale=pop(t, tcount))
    else:
        label(ctx, "BOOM + TICK = ONE SOUND!", 1330, 800, 44, YELLOW, NAVY, scale=pop(t, ttog))

def sc_layer3(ctx, t):
    tfun = wt('fun', 155); tmid = wt('middle', 160); tso = wt('So', 163); tone = wt('one,', 164); ttwo = wt('two,', 167); tsay = wt("Let's", 169)
    hc = ()
    if tone - .1 <= t < ttwo - .1: hc = (0,)
    elif ttwo - .1 <= t < tsay: hc = (2,)
    chart_scene(ctx, t, ('hihat', 'snare', 'kick'), "LAYER 3: ADD THE CRACK", T['l3'], SN_C, {'snare': 1}, dict(highlight_cols=hc))
    if t < tmid: label(ctx, "THE FUN PART!", 1330, 800, 48, PINK, WHITE, scale=pop(t, tfun)) if t > tfun else label(ctx, "SNARE ON 2 AND 4", 1330, 800, 46, RED, WHITE, scale=pop(t, wt('two', 157)))
    elif t < tso: label(ctx, "MIDDLE OF THE HEAD", 1330, 800, 44, YELLOW, NAVY, scale=pop(t, tmid))
    elif t < ttwo: label(ctx, "ON 1: FOOT + RIGHT HAND", 1330, 800, 42, TEAL, WHITE, scale=pop(t, tone))
    elif t < tsay: label(ctx, "ON 2: BOTH HANDS", 1330, 800, 44, GREEN, WHITE, scale=pop(t, ttwo))
    else: label(ctx, "BOOM AND CRACK AND...", 1330, 800, 44, PINK, WHITE, scale=pop(t, tsay))

def sc_slow(ctx, t):
    trh = wt('Right', 180); tready = wt('Ready?', 187); tkeep = wt('Keep', 197); tmiss = wt('If', 198); treal = wt("That's", 203)
    hr = None
    if trh <= t < tready:
        hr = 'hihat' if t < wt('Right', 183) else ('kick' if t < wt('Left', 185) else 'snare')
    nameplate(ctx, t, T['slow'], "ALL TOGETHER!", None, x=960, y=150, col=GREEN)
    ep3_kit(ctx, 470, 560, .52, t)
    beat_chart(ctx, 1330, 545, t, .78, highlight_row=hr)
    ctx.save(); turtle(ctx, 1770, 250, .8 * pop(t, wt('slow.', 179)), t); ctx.restore()
    if t > wt('slow.', 179): label(ctx, "NICE + SLOW", 1770, 330, 30, GREEN, WHITE, scale=pop(t, wt('slow.', 179)))
    countin(ctx, t, 470, 300)
    if t > tkeep and t < treal: label(ctx, "MISSED A HIT? DON'T STOP!", 1330, 800, 42, ORANGE, WHITE, scale=pop(t, tmiss))
    elif t >= treal: label(ctx, "THAT'S WHAT REAL DRUMMERS DO!", 1330, 800, 40, GREEN, WHITE, scale=pop(t, treal))

def sc_normal(ctx, t):
    tl = T['listen']; tplayed = wt('played', tl); tdid = tplayed
    loop = T_LOOP0 - .3 <= t < T_LOOP1 + .2
    if t < tl - .2:
        nameplate(ctx, t, T['normal'], "ROCK SPEED!", None, x=960, y=150, col=ORANGE)
        k = smooth(prog(t, T_LOOP0 - .6, .5)) if t > T_LOOP0 - .6 else 0
        ep3_kit(ctx, lerp(470, 660, k), lerp(560, 560, k), lerp(.52, .62, k), t)
        beat_chart(ctx, lerp(1330, 1500, k), 545, t, lerp(.78, .58, k))
        flame(ctx, 1780 - 300 * k, 260, .7 * pop(t, wt('speed', 207)), t)
        countin(ctx, t, 470, 300)
        if loop:
            label(ctx, "THIS IS ROCK SPEED!", 1500, 780, 46, YELLOW, NAVY, scale=pop(t, T_LOOP0 - .3), rot=wob(t, 3, .02))
            for i in range(6):
                note(ctx, 300 + i * 260 + wob(t, .7, 30, i), 300 - ((t * 120 + i * 90) % 220), 1.2, WHITE, .5)
    else:
        ep3_kit(ctx, 960, 680, .62, t)
        text(ctx, "LISTEN TO THAT!", 960, 250, 90, YELLOW, NAVY, lw=16, scale=pop(t, tl), rot=-.03) if t < tdid else None
        if t >= tdid:
            text(ctx, "YOU DID IT!", 960, 250, 130, YELLOW, NAVY, lw=20, scale=lerp(2, 1, back(prog(t, tdid, .4))), alpha=clamp(prog(t, tdid, .12) * 3), rot=-.03)
            label(ctx, "YOUR FIRST ROCK BEAT!", 960, 370, 50, PINK, WHITE, scale=pop(t, tdid + .5))
            confetti(ctx, 960, 350, t - tdid, seed=21, n=90, spread=900, dur=2.6)
        tsong = wt('songs.', tl)
        if tsong <= t < tdid: label(ctx, "IT'S IN TONS OF SONGS!", 960, 370, 46, PINK, WHITE, scale=pop(t, tsong - 1.2))

def gauge(ctx, x, y, r, v, t):
    ctx.new_path(); ctx.arc(x, y, r, math.pi, 2 * math.pi); ctx.close_path(); fill_stroke(ctx, WHITE, NAVY, LW)
    for k, c in enumerate((GREEN, YELLOW, RED)):
        ctx.new_path(); ctx.arc(x, y, r * .85, math.pi + k * math.pi / 3, math.pi + (k + 1) * math.pi / 3); ctx.set_source_rgb(*c); ctx.set_line_width(r * .18); ctx.stroke()
    a = math.pi + math.pi * clamp(v, 0, 1)
    line(ctx, x, y, x + r * .7 * math.cos(a), y + r * .7 * math.sin(a), NAVY, 10); circle(ctx, x, y, 16, NAVY, None)

def sc_tips(ctx, t):
    t1 = wt('Number', 230); t2 = wt('Number', t1 + 1); tslow = wt('slow', t1); tgo = wt('Go', t2); tex = wt('exact', t2); tev = wt('Every', t2)
    label(ctx, "2 COMMON MIX-UPS", 960, 150, 56, YELLOW, NAVY, scale=pop(t, T['tips']))
    if t < t2 - .2:
        p = pop(t, t1)
        ctx.save(); ctx.translate(960, 520); sscale(ctx, p, p); panel(ctx, 0, 0, 1100, 520, WHITE); ctx.restore()
        if p > .5:
            text(ctx, "#1  RUSHING", 960, 330, 64, RED, NAVY)
            v = .2 + .7 * smooth(prog(t, t1 + .5, 3.0)) if t < tslow else lerp(.9, .3, smooth(prog(t, tslow, 1.2)))
            gauge(ctx, 720, 640, 170, v, t)
            text(ctx, "FASTER" if t < tslow else "STEADY", 720, 700, 34, NAVY, None, shadow=False)
            if t > tslow:
                label(ctx, "SLOW DOWN", 1210, 520, 44, GREEN, WHITE, scale=pop(t, tslow))
                label(ctx, "COUNT OUT LOUD!", 1210, 630, 44, PINK, WHITE, scale=pop(t, wt('loud.', tslow)))
    elif t < tev - .2:
        p = pop(t, t2)
        ctx.save(); ctx.translate(960, 520); sscale(ctx, p, p); panel(ctx, 0, 0, 1100, 560, WHITE); ctx.restore()
        if p > .5:
            text(ctx, "#2  NOT TOGETHER", 960, 330, 60, RED, NAVY)
            together = smooth(prog(t, tex, .5)) if t > tex else 0
            per = .9; ph = ((t - t2) % per) / per
            for k, (x, lab, c) in enumerate(((720, "KICK", ORANGE), (1200, "HI-HAT", GOLD))):
                off = 0 if k == 0 else lerp(.22, 0, together)
                q = (ph - off) % 1
                rr = 70 + 60 * max(0, 1 - q * 5)
                burst(ctx, x, 520, rr, c, NAVY, 12, t * .5)
                text(ctx, lab, x, 520, 40, WHITE, NAVY)
            if t > tgo: label(ctx, "GO BACK TO LAYER 2", 960, 680, 42, YELLOW, NAVY, scale=pop(t, tgo))
            if t > tex: label(ctx, "LAND AT THE SAME MOMENT!", 960, 755, 40, GREEN, WHITE, scale=pop(t, tex))
            if t > tex: check(ctx, 960, 520, .7, p=prog(t, tex + .3, .4))
    else:
        for k, (txt, col) in enumerate((("HI-HAT", HH_C), ("KICK", KK_C), ("SNARE", SN_C))):
            block(ctx, 960, 760 - k * 175, 520, 150, col, pop(t, tev + .25 * k), txt, f"LAYER {k + 1}")
        label(ctx, "ONE LAYER AT A TIME", 1550, 520, 44, PINK, WHITE, scale=pop(t, tev + .5), rot=.03)
        if t > wt('too.', tev): label(ctx, "...AND YOU DID IT TOO!", 1550, 640, 40, GREEN, WHITE, scale=pop(t, wt('too.', tev)), rot=-.03)

def sc_recap2(ctx, t):
    th = wt('Hi-hat', T['recap2']); tk = wt('Kick', th); ts = wt('Snare', tk); tb = wt('Boom', ts); tr = wt("That's", tb)
    hr = None
    if th <= t < tk: hr = 'hihat'
    elif tk <= t < ts: hr = 'kick'
    elif ts <= t < tb: hr = 'snare'
    label(ctx, "SAY IT TOGETHER!", 960, 150, 56, YELLOW, NAVY, scale=pop(t, T['recap2']))
    beat_chart(ctx, 960, 520, t, 1.02 * pop(t, T['recap2'], .5), highlight_row=hr)
    if hr:
        txt = {"hihat": "EVERY COUNT", "kick": "1 AND 3", "snare": "2 AND 4"}[hr]
        label(ctx, txt, 960, 800, 46, PINK, WHITE, scale=pop(t, {"hihat": th, "kick": tk, "snare": ts}[hr]))
    if t > tr:
        label(ctx, "THAT'S THE ROCK BEAT!", 960, 800, 50, GREEN, WHITE, scale=pop(t, tr))
        confetti(ctx, 960, 400, t - tr, seed=31, n=80, spread=900, dur=2.4)

def lap_kid(ctx, x, y, t):
    """Front view: kid sitting on a stool, tapping the lap (round fists only). Kid's RIGHT side is on the screen LEFT."""
    dh, ds, dk = strike('hihat', t, .1), strike('snare', t, .1), strike('kick', t, .1)
    for dx in (-150, 150): line(ctx, x + dx, y + 40, x + dx * 1.15, y + 300, WOOD_D, 16)       # stool legs
    rrect(ctx, x - 200, y - 6, 400, 46, 16); fill_stroke(ctx, WOOD, NAVY, 5)                      # stool seat
    rrect(ctx, x - 115, y - 300, 230, 310, 60); fill_stroke(ctx, TEAL, NAVY, 5)                   # body
    for side in (-1, 1):                                                                          # shins + shoes
        lx = x + side * 78; lift = (30 * dk) if side == -1 else 0     # kid's right foot (screen left) taps the floor
        capsule(ctx, lx, y + 60, lx, y + 250 - lift, 36, PURPLE, NAVY, 5)
        rrect(ctx, lx - 52, y + 250 - lift, 104, 40, 16); fill_stroke(ctx, RED, NAVY, 5)
    for side in (-1, 1):                                                                          # lap: thighs + knees toward us
        lx = x + side * 78
        rrect(ctx, lx - 62, y - 40, 124, 110, 44); fill_stroke(ctx, lerpc(PURPLE, WHITE, .15), NAVY, 5)
        ellipse(ctx, lx, y + 52, 48, 22, lerpc(PURPLE, WHITE, .3), None)
    if dk > .6:
        for k in range(3): line(ctx, x - 78 - 70 + k * 70, y + 320, x - 78 - 95 + k * 95, y + 352, ORANGE, 7)
    circle(ctx, x, y - 390, 95, SKIN, NAVY, 5)
    ctx.new_path(); ctx.arc(x, y - 405, 98, math.pi, math.pi * 2); ctx.close_path(); fill_stroke(ctx, (.35, .2, .1), NAVY, 5)
    for dx in (-34, 34): circle(ctx, x + dx, y - 380, 10, NAVY, None)
    ctx.new_path(); ctx.arc(x, y - 352, 26, .1 * math.pi, .9 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(6); ctx.stroke()
    for side, d in ((-1, dh), (1, ds)):                                                           # arms: sleeve + round fist
        sx, sy = x + side * 112, y - 255
        ex, ey = x + side * 165, y - 140
        fx, fy = x + side * 85, lerp(y - 120, y - 5, d)
        capsule(ctx, sx, sy, ex, ey, 27, TEAL, NAVY, 5)
        capsule(ctx, ex, ey, fx, fy, 25, TEAL, NAVY, 5)
        fist(ctx, fx, fy, 33)
        if d > .7:
            for k in range(3): line(ctx, fx - 40 + k * 40, fy + 40, fx - 55 + k * 55, fy + 62, YELLOW, 6)

def sc_bonus(ctx, t):
    t0 = T['bonus']; tsit = wt('Sit', t0); tb = wt('Boom', tsit); tpr = wt('Practice', tb); tbr = wt('brain', tpr)
    if t < tsit - .2:
        op = smooth(prog(t, t0 + .4, .8))
        gift(ctx, 960, 560, 1.6 * pop(t, t0), t, op, shake=1 - op)
        if op > 0:
            burst(ctx, 960, 420, 320 * ease_out(op), YELLOW, None, 20, t * .5, alpha=.8 * op)
            text(ctx, "BONUS TRICK!", 960, 300, 130, YELLOW, NAVY, lw=22, scale=lerp(2, 1, back(prog(t, t0 + .5, .4))), alpha=clamp(prog(t, t0 + .5, .15) * 3))
            confetti(ctx, 960, 420, t - t0 - .4, seed=33, n=90, spread=900, dur=2.5)
        ta = wt('anywhere,', t0)
        if t > ta: label(ctx, "PRACTICE ANYWHERE - NO KIT NEEDED!", 960, 830, 46, PINK, WHITE, scale=pop(t, ta))
        return
    lap_kid(ctx, 620, 600, t)
    for (w, txt, col, x, y, px, py) in (('right', "RIGHT HAND + RIGHT LEG = HI-HAT", HH_C, 330, 300, 540, 500),
                                        ('left', "LEFT HAND + LEFT LEG = SNARE", SN_C, 1000, 220, 700, 500),
                                        ('right', "RIGHT FOOT + FLOOR = KICK", KK_C, 330, 940, 545, 860)):
        tk = wt(w, tsit + (0 if 'HI-HAT' in txt else (2.5 if 'SNARE' in txt else 5)))
        if t >= tk and t < tpr:
            yy = {HH_C: 560, SN_C: 650, KK_C: 740}[col]
            label(ctx, txt, 1400, yy, 32, col, WHITE, scale=pop(t, tk))
    beat_chart(ctx, 1400, 340, t, .6, show_limbs=False)
    if t >= tpr:
        for k, (w, txt) in enumerate((('table,', "AT THE TABLE"), ('couch,', "ON THE COUCH"), ('TV.', "WATCHING TV"))):
            tk = wt(w, tpr); p = pop(t, tk)
            x = 1150 + k * 260
            ctx.save(); ctx.translate(x, 860); sscale(ctx, p, p)
            if k == 0: rrect(ctx, -90, -20, 180, 24, 6); fill_stroke(ctx, WOOD_D, NAVY, 4); line(ctx, -70, 4, -70, 60, WOOD_D, 10); line(ctx, 70, 4, 70, 60, WOOD_D, 10)
            elif k == 1: rrect(ctx, -95, -30, 190, 80, 24); fill_stroke(ctx, PINK, NAVY, 4); rrect(ctx, -105, -60, 210, 40, 18); fill_stroke(ctx, PINK, NAVY, 4)
            else: rrect(ctx, -85, -55, 170, 110, 12); fill_stroke(ctx, NAVY, NAVY, 4); rrect(ctx, -72, -44, 144, 88, 8); fill_stroke(ctx, SKY, None)
            ctx.restore()
            if p > 0: text(ctx, txt, x, 950, 24, WHITE, NAVY, scale=p)
    if t >= tbr: label(ctx, "YOUR BRAIN LEARNS THE PATTERN!", 1450, 180, 36, GREEN, WHITE, scale=pop(t, tbr), rot=-.02)

def staff(ctx, cx, cy, s, a=1.0):
    """1 bar of real drum notation: hi-hat x's above the staff, snare 3rd space, kick 1st space."""
    ctx.save(); ctx.translate(cx, cy); sscale(ctx, s, s)
    panel(ctx, 0, 0, 1080, 460, WHITE, a)
    sp = 30; top = -2 * sp; x0, x1 = -470, 470
    for k in range(5): line(ctx, x0, top + k * sp, x1, top + k * sp, NAVY, 3, a)
    line(ctx, x1, top, x1, top + 4 * sp, NAVY, 5, a)
    for dx in (-445, -430): line(ctx, dx, top + sp, dx, top + 3 * sp, NAVY, 7, a)   # percussion clef
    text(ctx, "4", -380, top + sp, 56, NAVY, None, shadow=False, alpha=a); text(ctx, "4", -380, top + 3 * sp, 56, NAVY, None, shadow=False, alpha=a)
    xs = [-300 + i * 95 for i in range(8)]
    yh = top - sp / 2; ysn = top + 1.5 * sp; yk = top + 3.5 * sp
    for i, x in enumerate(xs):
        line(ctx, x - 11, yh - 11, x + 11, yh + 11, NAVY, 5, a); line(ctx, x + 11, yh - 11, x - 11, yh + 11, NAVY, 5, a)
        line(ctx, x + 12, yh, x + 12, top - 3.3 * sp, NAVY, 4, a)
        if i in (2, 6):
            ellipse(ctx, x, ysn, 15, 11, NAVY, None, alpha=a); line(ctx, x + 13, ysn, x + 13, yh, NAVY, 4, a)
        if i in (0, 4):
            ellipse(ctx, x, yk, 15, 11, NAVY, None, alpha=a); line(ctx, x - 13, yk, x - 13, yk + 3 * sp, NAVY, 4, a)
    for i in range(0, 8, 2):
        rrect(ctx, xs[i] + 10, top - 3.3 * sp - 6, 99, 12, 2); ctx.set_source_rgba(*NAVY, a); ctx.fill()
    ctx.restore()

def sc_outro(ctx, t):
    t0 = T['outro']; tn = T['next']; tlike = wt('like', tn); tsub = wt('Subscribe', tn); tsee = wt('See', tsub)
    if t < tn - .2:
        ep3_kit(ctx, 960, 600, .8, t, glow={'hihat': .6, 'snare': .6, 'kick': .6})
        label(ctx, "YOU CAN PLAY A REAL ROCK BEAT!", 960, 160, 58, GREEN, WHITE, scale=pop(t, t0))
        confetti(ctx, 960, 300, t - t0, seed=101, n=70, spread=900)
        return
    if t < tsub - .3:
        label(ctx, "NEXT: HOW TO READ MUSIC", 960, 150, 56, PINK, WHITE, scale=pop(t, tn))
        m = smooth(prog(t, tlike - .2, .7))
        if m < 1: beat_chart(ctx, 960, 520, t, .85 * (1 - .15 * m), alpha=1 - m, follow=False)
        if m > 0:
            staff(ctx, 960, 520, .85 + .15 * m, m)
            label(ctx, "COMING SOON!", 1350, 300, 40, YELLOW, NAVY, scale=pop(t, tlike + .4), rot=.05)
        return
    label(ctx, "NEXT EPISODE: READING MUSIC", 960, 150, 52, PINK, WHITE)
    staff(ctx, 640, 520, .55)
    sp = pop(t, tsub - .3)
    if sp > 0:
        clicked = t > tsub + .5; pulse = 1 + .06 * math.sin(t * 7)
        ctx.save(); ctx.translate(1430, 450); sscale(ctx, sp * pulse, sp * pulse)
        rrect(ctx, -230, -70, 460, 140, 70); fill_stroke(ctx, (0.55, 0.55, 0.6) if clicked else RED, NAVY, 7)
        text(ctx, "SUBSCRIBED!" if clicked else "SUBSCRIBE", 0, 0, 50 if clicked else 58, WHITE, NAVY); ctx.restore()
        confetti(ctx, 1430, 450, t - tsub - .5, seed=44, n=50, spread=600)
    if t > tsee: text(ctx, "SEE YOU NEXT TIME, DRUMMERS!", 1430, 680, 50, YELLOW, NAVY, scale=pop(t, tsee), rot=-.02)

SCENES = [(0, T['recap'], sc_intro), (T['recap'], T['plan'], sc_recap), (T['plan'], T['cross'], sc_plan), (T['cross'], T['l1'], sc_cross),
          (T['l1'], T['l2'], sc_layer1), (T['l2'], T['l3'], sc_layer2), (T['l3'], T['slow'], sc_layer3), (T['slow'], T['normal'], sc_slow),
          (T['normal'], T['tips'], sc_normal), (T['tips'], T['recap2'], sc_tips), (T['recap2'], T['bonus'], sc_recap2),
          (T['bonus'], T['outro'], sc_bonus), (T['outro'], 9999, sc_outro)]
TINTS = {sc_layer1: TEAL, sc_layer2: PINK, sc_layer3: RED, sc_normal: PINK, sc_tips: PURPLE, sc_bonus: PURPLE, sc_outro: PINK, sc_cross: TEAL}

def frame(ctx, t):
    s, e, fn = [x for x in SCENES if x[0] <= t < x[1]][0]
    background(ctx, t, TINTS.get(fn))
    ctx.save()
    out = smooth(prog(t, e - .18, .18)) if e < 900 else 0
    if out > 0: ctx.translate(960, 480); sscale(ctx, 1 - out, 1 - out); ctx.translate(-960, -480)
    fn(ctx, t); ctx.restore()
    if 0 < s and t - s < .2: ctx.set_source_rgba(1, 1, 1, .35 * (1 - (t - s) / .2)); ctx.paint()
    hud(ctx, t)
    if fn is not sc_intro or t > 6.2: narrator(ctx, t)
    captions(ctx, t)

def surface(t, scale):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale)); ctx = cairo.Context(s)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo); sscale(ctx, scale, scale); frame(ctx, t); return s

if __name__ == "__main__":
    if sys.argv[1] == "still":
        surface(float(sys.argv[2]), float(sys.argv[3])).write_to_png(sys.argv[4])
    elif sys.argv[1] == "info":
        print(json.dumps({k: round(v, 2) for k, v in T.items()}, indent=0)); print(len(BARS), "bars", len(COUNTINS), "count-ins", len(EVENTS), "events")
        for b in BARS: print(round(b["t0"], 2), sorted(b["layer"]))
    else:
        f0, f1, sc, out = int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        crf = sys.argv[6] if len(sys.argv) > 6 else "20"
        ofps = int(sys.argv[7]) if len(sys.argv) > 7 else FPS      # e.g. 15 for previews (frame numbers stay in 30 fps units)
        step = FPS // ofps
        w, h = int(W * sc), int(H * sc)
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(ofps), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", "-threads", "2", out], stdin=subprocess.PIPE)
        for f in range(f0, f1, step):
            p.stdin.write(surface(f / FPS, sc).get_data())
            if f % 300 == 0: print(f"{out}: frame {f}", flush=True)
        p.stdin.close(); p.wait()
