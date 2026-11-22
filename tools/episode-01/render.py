"""Episode 1 drum-lesson animation renderer.
usage: python3 render.py still T [scale] out.png
       python3 render.py range F0 F1 scale out.mp4
"""
import sys, os, math, json, random, subprocess, re
import numpy as np
import cairo
from lib import *
from hands import hand_grip, hand_point, hand_thumbsup, hand_cup, SKIN
from photo import photo_card, img_to_card, video_card
def _no_hands(*a, **k): raise RuntimeError('drawn hand used')
glove_grip = glove_point = glove_thumbsup = hand_grip = hand_point = hand_thumbsup = hand_cup = _no_hands
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "photos") + "/"

def ring(ctx, x, y, r, t):
    rr = r * (1 + .04 * math.sin(t * 6))
    ctx.new_path(); ctx.arc(x, y, rr, 0, 2 * math.pi); ctx.set_source_rgba(*NAVY, 1); ctx.set_line_width(16); ctx.stroke()
    ctx.new_path(); ctx.arc(x, y, rr, 0, 2 * math.pi); ctx.set_source_rgba(*YELLOW, 1); ctx.set_line_width(9); ctx.set_dash([26, 14]); ctx.stroke(); ctx.set_dash([])

def arrow(ctx, x1, y1, x2, y2, col=YELLOW, s=1.0):
    if s <= 0.01: return
    x1, y1 = lerp(x2, x1, s), lerp(y2, y1, s)
    a = math.atan2(y2 - y1, x2 - x1)
    line(ctx, x1, y1, x2 - 30 * math.cos(a), y2 - 30 * math.sin(a), NAVY, 22); line(ctx, x1, y1, x2 - 30 * math.cos(a), y2 - 30 * math.sin(a), col, 12)
    ctx.new_path(); ctx.move_to(x2, y2)
    for d in (2.6, -2.6): ctx.line_to(x2 + 50 * math.cos(a + d), y2 + 50 * math.sin(a + d))
    ctx.close_path(); fill_stroke(ctx, col, NAVY, 6)

def card_in(t, t0, dur=None):
    return back(prog(t, t0, 0.45))

def kb(t, t0, d, z0=1.0, z1=1.06):
    return lerp(z0, z1, smooth(prog(t, t0, d)))

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
CUES = json.load(open(os.path.join(HERE, "words.json")))
ENV = np.load(os.path.join(HERE, "env.npy"))
WORDS = [w for c in CUES for w in c["words"]]
TOTAL = 286.5

def norm(s): return re.sub(r"[^a-z0-9']", "", s.lower())

def wt(word, after=0.0):
    word = norm(word)
    for w in WORDS:
        if w["start"] >= after - 1e-6 and norm(w["text"]) == word:
            return w["start"]
    raise KeyError((word, after))

def env_at(t):
    i = int(WARP(t) * FPS)
    if i < 0 or i >= len(ENV): return 0.0
    return float(np.mean(ENV[max(0, i - 1):i + 1]))

# ---------------------------------------------------------------- background
_BG_RND = random.Random(7)
BG_ITEMS = [(_BG_RND.uniform(0, W), _BG_RND.uniform(0, H), _BG_RND.uniform(.5, 1.1),
             _BG_RND.uniform(8, 22), _BG_RND.choice([0, 1, 2]), _BG_RND.uniform(0, 6.28)) for _ in range(26)]

def background(ctx, t, tint=None):
    g = cairo.RadialGradient(W / 2, H * 0.42, 100, W / 2, H * 0.5, 1250)
    c0, c1 = (0.22, 0.62, 1.0), (0.05, 0.38, 0.92)
    if tint is not None:
        c0 = lerpc(c0, tint, 0.35); c1 = lerpc(c1, tint, 0.25)
    g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1)
    ctx.set_source(g); ctx.paint()
    # rotating sunburst rays
    ctx.save(); ctx.translate(W / 2, H * 0.45); ctx.rotate(t * 0.05)
    for i in range(16):
        a = i * 2 * math.pi / 16
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 1600, a, a + math.pi / 32); ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, 0.035); ctx.fill()
    ctx.restore()
    for (x, y, s, sp, k, ph) in BG_ITEMS:
        yy = (y - t * sp) % (H + 200) - 100
        xx = x + wob(t, 0.08, 30, ph)
        a = 0.13
        if k == 0: note(ctx, xx, yy, s, WHITE, a, wob(t, .1, .3, ph))
        elif k == 1: note(ctx, xx, yy, s, WHITE, a, wob(t, .1, .3, ph), double=True)
        else: star(ctx, xx, yy, 18 * s, WHITE, None, alpha=a, rot=t * 0.5 + ph)

# ---------------------------------------------------------------- captions
CAP_SIZE = 62

def captions(ctx, t):
    cue = None
    for c in CUES:
        if c["start"] <= t < c["end"] + 0.03:
            cue = c
    if cue is None: return
    nlines = max(w["line"] for w in cue["words"]) + 1
    lines = [[w for w in cue["words"] if w["line"] == i] for i in range(nlines)]
    space = CAP_SIZE * 0.40
    widths = [sum(text_width(ctx, w["text"], CAP_SIZE) for w in ln) + space * (len(ln) - 1) for ln in lines]
    lh = CAP_SIZE * 1.22
    box_w = max(widths) + 80; box_h = lh * nlines + 36
    cy0 = 1048 - box_h
    appear = back(prog(t, cue["start"], 0.25))
    ctx.save(); ctx.translate(W / 2, cy0 + box_h / 2); sscale(ctx, lerp(0.85, 1, appear), lerp(0.85, 1, appear))
    rrect(ctx, -box_w / 2, -box_h / 2, box_w, box_h, 30)
    ctx.set_source_rgba(*NAVY, 0.62 * clamp(appear * 1.5)); ctx.fill()
    ctx.restore()
    for li, ln in enumerate(lines):
        x = W / 2 - widths[li] / 2
        y = cy0 + 18 + lh * (li + 0.5)
        for w in ln:
            ww = text_width(ctx, w["text"], CAP_SIZE)
            cx = x + ww / 2
            if t < w["start"]:
                col, sc, dy, rot = (0.80, 0.88, 1.0), 1.0, 0, 0
                a = 0.75
            elif t < w["end"]:
                p = prog(t, w["start"], 0.22)
                bump = math.sin(math.pi * clamp(p)) if p < 1 else 0
                sc = 1.0 + (0.16 if w["key"] else 0.10) * bump + (0.08 if w["key"] else 0.03)
                dy = -10 * bump
                col = PINK if w["key"] else YELLOW
                rot = wob(t, 3, 0.05) if w["key"] else 0
                a = 1
            else:
                col = YELLOW if w["key"] else WHITE
                sc, dy, rot, a = 1.0, 0, 0, 1
            text(ctx, w["text"], cx, y + dy, CAP_SIZE, col, NAVY, lw=11, alpha=a * clamp(appear * 1.4), scale=sc, rot=rot)
            x += ww + space

# ---------------------------------------------------------------- HUD
SECTIONS = [(0, "START"), (33.5, "GEAR"), (58.6, "PARTS"), (75.8, "BALANCE"), (93.6, "GRIP"),
            (163.7, "BOUNCE"), (198.2, "MISTAKES"), (243.9, "BONUS"), (276.8, "NEXT")]

def hud(ctx, t):
    a = smooth(prog(t, 6.0, 0.6))
    if a <= 0: return
    ctx.save(); ctx.translate(0, -80 * (1 - a))
    x0, x1, y = 470, 1450, 52
    label(ctx, "EPISODE 1", 320, y, 30, PINK, WHITE)
    rrect(ctx, x0, y - 16, x1 - x0, 32, 16); fill_stroke(ctx, (0.08, 0.25, 0.65), NAVY, 5)
    f = clamp(t / TOTAL)
    if f > 0.005:
        rrect(ctx, x0 + 5, y - 11, (x1 - x0 - 10) * f, 22, 11)
        g = cairo.LinearGradient(x0, 0, x1, 0); g.add_color_stop_rgb(0, *YELLOW); g.add_color_stop_rgb(1, *ORANGE)
        ctx.set_source(g); ctx.fill()
    for (st, name) in SECTIONS[1:]:
        sx = x0 + (x1 - x0) * st / TOTAL
        done = t >= st
        pp = pop(t, st, 0.5)
        r = 20 * (1 + 0.5 * math.sin(math.pi * clamp(prog(t, st, .5)))) if done else 16
        star(ctx, sx, y, r, YELLOW if done else (0.55, 0.65, 0.85), NAVY, 4)
        if done and t - st < 1.5:
            confetti(ctx, sx, y + 10, t - st, seed=int(st), n=18, spread=160, dur=1.4)
    gift(ctx, x1 + 70, y + 8, 0.28, t, 0, shake=1.0 if 230 < t < 244 else 0)
    ctx.restore()

def narrator(ctx, t, x=150, y=905, s=0.62, alpha=1.0):
    e = env_at(t)
    bounce = -abs(math.sin(t * 6)) * 6 * e
    drum(ctx, x, y + bounce, s, t, mouth=e * 1.1, alpha=alpha, look=0.6)

# ---------------------------------------------------------------- scene helpers
CX, CY = 960, 440   # content centre

def title_slam(ctx, t, t0, s, x, y, size, fill=YELLOW, rot=0.0):
    p = prog(t, t0, 0.35)
    if p <= 0: return
    sc = lerp(2.6, 1.0, back(p, 1.4)); a = clamp(p * 3)
    text(ctx, s, x, y, size, fill, NAVY, lw=size * 0.16, alpha=a, scale=sc, rot=rot)

def caption_sticker(ctx, t, t0, s, x, y, size=46, bg=YELLOW, fg=NAVY, rot=-0.04):
    p = pop(t, t0)
    label(ctx, s, x, y, size, bg, fg, scale=p, rot=rot + wob(t, .5, .02))

def shake_amt(t):
    hits = [0.0, 0.32, 0.9, 17.7 + 2.5, 203.14, 244.0]
    a = 0
    for h in hits:
        d = t - h
        if 0 <= d < 0.35: a += (1 - d / 0.35) * 14
    return a

# ---------------------------------------------------------------- scenes
def sc_hook(ctx, t, e):
    # 0 - 6.32: BOOM + title + episode
    # big drum slams in
    p = prog(t, 0.0, 0.5)
    y = lerp(1300, 600, back(p, 1.6))
    sq = 1 + 0.12 * math.sin(min(1, prog(t, .3, .3)) * math.pi)
    # burst behind
    bp = ease_out(prog(t, 0.05, 0.4))
    burst(ctx, 960, 590, 330 * bp, YELLOW, NAVY, 16, t * 0.4, alpha=1)
    burst(ctx, 960, 590, 260 * bp, ORANGE, None, 16, -t * 0.5)
    # crossed sticks spin in behind drum
    sp = back(prog(t, 0.15, 0.6))
    for sgn in (-1, 1):
        a = -math.pi / 2 + sgn * 0.55 + (1 - sp) * sgn * 3
        stick(ctx, 960 - sgn * 300 * sp, 820, a, 520 * max(sp, .01), 34, face="smile" if sp > .9 else None, t=t)
    drum(ctx, 960, y, 1.05 * sq, t, mouth=env_at(t) * 1.2, look=0)
    confetti(ctx, 960, 520, t - 0.3, seed=3, n=60, spread=800, dur=2.2)
    # comic BOOM word
    bm = pop(t, 0.12, 0.3) * (1 - smooth(prog(t, 1.4, 0.3)))
    if bm > 0:
        ctx.save(); ctx.translate(1430, 420); ctx.rotate(0.18)
        burst(ctx, 0, 0, 150 * bm, WHITE, NAVY, 12)
        text(ctx, "BOOM!", 0, 0, 74, RED, NAVY, scale=bm)
        ctx.restore()
    # title
    title_slam(ctx, t, 0.35, "LEARN DRUMS", 960, 120, 110, WHITE, -0.03)
    title_slam(ctx, t, 0.75, "IN 5 MINUTES!", 960, 240, 110, YELLOW, 0.02)
    # stopwatch "5"
    sw = pop(t, 1.1, 0.5)
    if sw > 0:
        ctx.save(); ctx.translate(1620, 620); sscale(ctx, sw, sw); ctx.rotate(wob(t, 1.2, 0.08))
        circle(ctx, 0, 0, 120, WHITE, NAVY, 8); rrect(ctx, -22, -160, 44, 40, 10); fill_stroke(ctx, RED, NAVY, 6)
        hand = t * 4
        line(ctx, 0, 0, 80 * math.sin(hand), -80 * math.cos(hand), RED, 8)
        text(ctx, "5", 0, 6, 110, ORANGE, NAVY); text(ctx, "MIN", 0, 72, 34, NAVY, None, shadow=False)
        ctx.restore()
    # episode ribbon & topic
    ep = pop(t, 1.85, 0.5)
    if ep > 0:
        ctx.save(); ctx.translate(310, 600); ctx.rotate(-0.12); sscale(ctx, ep, ep)
        panel(ctx, 0, 0, 380, 230, PINK)
        text(ctx, "EPISODE", 0, -55, 52, WHITE, NAVY)
        text(ctx, "1", 0, 40, 130, YELLOW, NAVY)
        ctx.restore()
    tp = prog(t, 3.6, 0.4)
    if tp > 0:
        label(ctx, "HOLD YOUR STICKS LIKE A PRO!", 960, 770, 50, YELLOW, NAVY, scale=back(tp), rot=wob(t, .7, .015))

def sc_never(ctx, t, e):  # 6.32-9.16
    p = pop(t, 6.32)
    drum(ctx, 820, 480, 1.25 * p, t, mouth=e, look=0.4, body=PURPLE)
    for i in range(6):
        a = i * math.pi / 3 + t
        star(ctx, 820 + 330 * math.cos(a), 470 + 240 * math.sin(a), 22 * p * (1 + .3 * math.sin(t * 5 + i)), YELLOW, NAVY, 4)
    caption_sticker(ctx, t, 6.6, "NEVER TOUCHED A DRUM?", 820, 180, 50, WHITE)
    check(ctx, 1380, 520, 1.5, p=prog(t, wt("before", 6.3), .45))
    caption_sticker(ctx, t, wt("worry", 6.3), "NO WORRIES!", 1380, 300, 44, GREEN, WHITE, 0.08)

def sc_steps(ctx, t, e):  # 9.16-15.6
    t0 = 9.16
    for i in range(3):
        p = pop(t, t0 + 0.2 + i * 0.35)
        x = 520 + i * 330; y = 700 - i * 150
        ctx.save(); ctx.translate(x, y); sscale(ctx, 1, p)
        rrect(ctx, -150, 0, 300, 120 + i * 150, 16); fill_stroke(ctx, [TEAL, ORANGE, PINK][i], NAVY, LW)
        ctx.restore()
        if p > .5: text(ctx, str(i + 1), x, y + 60, 80, WHITE, NAVY, alpha=clamp(p))
    # hopping stick buddy
    hop_t = prog(t, wt("step", 9) , 2.6)
    stepi = min(2, int(hop_t * 3)); f = (hop_t * 3) % 1 if hop_t < 1 else 1
    if t > 9.5:
        sx = 520 + 330 * min(2, hop_t * 3 - 0.0 if hop_t < 1 else 2)
        base = 700 - 150 * stepi
        hy = base - 70 - 120 * math.sin(math.pi * f) if hop_t < 1 else base - 70 - abs(math.sin(t * 5)) * 30
        stick(ctx, sx - 30, hy, -math.pi / 2 + 0.1, 260, 24, face="smile", t=t)
    caption_sticker(ctx, t, 9.3, "ONE STEP AT A TIME", 760, 150, 52, YELLOW)
    # first beat payoff
    fb = wt("beat", 12)
    tp = pop(t, fb - 0.6)
    if tp > 0:
        ctx.save(); ctx.translate(1520, 260); sscale(ctx, tp, tp); ctx.rotate(wob(t, .8, .1))
        star(ctx, 0, 0, 140, YELLOW, NAVY, 8)
        text(ctx, "1ST", 0, -12, 52, PINK, NAVY); text(ctx, "BEAT!", 0, 40, 40, WHITE, NAVY)
        ctx.restore()
        for i in range(5):
            ph = (t * 0.6 + i / 5) % 1
            note(ctx, 1520 + 200 * math.cos(i * 1.3) * ph, 260 - 260 * ph, 1.2, [PINK, WHITE, YELLOW][i % 3], 1 - ph, wob(t, 1, .3), i % 2 == 0)
        confetti(ctx, 1520, 260, t - fb + 0.6, seed=11, n=40, spread=500)

def sc_secret(ctx, t, e):  # 15.6-17.68
    p = pop(t, 15.6)
    ctx.save(); ctx.translate(960, 470); sscale(ctx, p, p)
    # treasure chest glowing
    glow = 0.5 + 0.5 * math.sin(t * 8)
    burst(ctx, 0, -40, 260 + 20 * glow, YELLOW, None, 18, t, alpha=0.8)
    rrect(ctx, -200, -40, 400, 200, 20); fill_stroke(ctx, WOOD_D, NAVY, LW)
    ctx.save(); ctx.translate(-200, -40); ctx.rotate(-0.5 * ease_out(prog(t, 16.4, .4)))
    rrect(ctx, 0, -110, 400, 110, 50); fill_stroke(ctx, WOOD, NAVY, LW); ctx.restore()
    rrect(ctx, -30, -10, 60, 70, 10); fill_stroke(ctx, YELLOW, NAVY, 5)
    ctx.restore()
    title_slam(ctx, t, 16.0, "SHHH... A SECRET!", 960, 170, 96, PINK, -0.03)
    # finger to lips mascot-ish
    for i in range(4): star(ctx, 1450 + 120 * math.cos(i * 1.57 + t), 420 + 90 * math.sin(i * 1.57 + t), 26 * pop(t, 15.9 + i * .1), YELLOW, NAVY, 4)

def sc_tight(ctx, t, e):  # 17.68-25.96
    t_tight = wt("tight.", 17)
    sq = smooth(prog(t, t_tight - 0.4, 0.4))
    in_p = pop(t, 17.68)
    ctx.save(); ctx.translate(600, 450); sscale(ctx, 1.35 * in_p, 1.35 * in_p)
    stick(ctx, -300, 0, 0, 560, 30, face="squeezed" if sq > .5 else "smile", t=t)
    glove_grip(ctx, -110, 0, 0, curl=1, squeeze=sq, t=t)
    ctx.restore()
    if sq > 0:
        ctx.save(); ctx.translate(620, 210); ctx.rotate(-0.08)
        sp = pop(t, t_tight - 0.3)
        burst(ctx, 0, 0, 170 * sp, RED, NAVY, 14, t)
        text(ctx, "TOO TIGHT!", 0, 0, 60, WHITE, NAVY, scale=sp)
        ctx.restore()
    # three icons: sound, speed, wrists
    t1 = wt("sound,", 20); t2 = wt("speed,", 20); t3 = wt("wrists.", 20)
    for i, (tt, name) in enumerate([(t1, "SOUND"), (t2, "SPEED"), (t3, "WRISTS")]):
        p = pop(t, tt)
        if p <= 0: continue
        x, y = 1180 + i * 250, 420
        ctx.save(); ctx.translate(x, y); sscale(ctx, p, p)
        panel(ctx, 0, 0, 210, 250, WHITE)
        if i == 0:   # speaker
            rrect(ctx, -60, -60, 40, 50, 6); fill_stroke(ctx, PURPLE, NAVY, 5)
            ctx.new_path(); ctx.move_to(-20, -60); ctx.line_to(20, -95); ctx.line_to(20, 25); ctx.line_to(-20, -10); ctx.close_path(); fill_stroke(ctx, PURPLE, NAVY, 5)
            for k in range(2):
                ctx.new_path(); ctx.arc(30, -35, 25 + k * 20, -0.7, 0.7); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
        elif i == 1:  # speedometer
            ctx.new_path(); ctx.arc(0, -10, 70, math.pi, 2 * math.pi); ctx.close_path(); fill_stroke(ctx, YELLOW, NAVY, 5)
            na = math.pi + 0.4 + 0.3 * math.sin(t * 9)
            line(ctx, 0, -10, 60 * math.cos(na), -10 + 60 * math.sin(na), RED, 7)
        else:  # wrist w/ ouch
            capsule(ctx, -70, 30, 10, -20, 26, (1, .85, .7), NAVY, 5)
            circle(ctx, 30, -40, 40, GLOVE, NAVY, 5)
            star(ctx, 10, -20, 30 + 5 * math.sin(t * 10), RED, NAVY, 4, n=7, inner=.5)
        text(ctx, name, 0, 80, 38, NAVY, None, shadow=False)
        ctx.restore()
        cross(ctx, x + 80, y - 110, 0.55, p=prog(t, tt + 0.25, 0.4))

def sc_fix(ctx, t, e):  # 25.96-28.24
    p = pop(t, 25.96)
    ctx.save(); ctx.translate(760, 450); sscale(ctx, p, p); ctx.rotate(-0.05)
    panel(ctx, 0, 0, 340, 360, WHITE, r=30)
    rrect(ctx, -170, -180, 340, 100, 30); fill_stroke(ctx, RED, NAVY, LW)
    text(ctx, "DAY", 0, -130, 58, WHITE, NAVY)
    text(ctx, "1", 0, 50, 190, PINK, NAVY)
    ctx.restore()
    check(ctx, 1220, 450, 2.0, p=prog(t, wt("fix", 25.9), .5))
    caption_sticker(ctx, t, wt("fix", 25.9), "LET'S FIX IT!", 1220, 230, 56, GREEN, WHITE, 0.05)
    confetti(ctx, 1220, 450, t - wt("fix", 25.9), seed=5, n=50)

def sc_stickaround(ctx, t, e):  # 28.24-33.52
    tp = wt("intended,", 28)
    for k, (x, ph) in enumerate([(700, 0), (980, 1.4)]):
        p = pop(t, 28.3 + k * 0.2)
        y = 520 - abs(math.sin(t * 3.2 + ph)) * 60
        stick(ctx, x, y + 200 * (1 - p) + 200, -math.pi / 2 + wob(t, .9, .12, ph), 460, 48,
              face="wink" if (k == 1 and t > tp) else "smile", t=t + ph)
    pp = pop(t, tp - 0.15)
    if pp > 0:
        ctx.save(); ctx.translate(420, 300); ctx.rotate(-0.1 + wob(t, 1.5, .03)); sscale(ctx, pp, pp)
        burst(ctx, 0, 0, 190, PINK, NAVY, 14)
        text(ctx, "PUN", 0, -30, 64, WHITE, NAVY); text(ctx, "INTENDED!", 0, 35, 46, YELLOW, NAVY)
        ctx.restore()
    tb = wt("bonus", 31)
    gp = pop(t, tb - 0.3)
    gift(ctx, 1450, 520, 1.3 * gp, t, 0, shake=1)
    if gp > 0:
        text(ctx, "?", 1450 + wob(t, 2, 10), 280, 110, YELLOW, NAVY, scale=gp, rot=wob(t, 1.4, .2))
        caption_sticker(ctx, t, tb, "BONUS AT THE END!", 1450, 760, 44, YELLOW)

def sc_gear(ctx, t, e):  # 33.52-41.28
    p = pop(t, 33.6)
    for k in range(2):
        a = -math.pi / 2 + (-0.25 if k == 0 else 0.25) + wob(t, .6, .05, k)
        stick(ctx, 800 + k * 160 - 80, 760, a + (0 if k else 0), 560 * max(p, .01), 32, t=t)
    caption_sticker(ctx, t, 33.8, "ALL YOU NEED: STICKS!", 880, 140, 50, WHITE)
    t5 = wt("5A", 36)
    tp = pop(t, t5)
    if tp > 0:
        ctx.save(); ctx.translate(1350, 420); ctx.rotate(0.12 + wob(t, .8, .05)); sscale(ctx, tp, tp)
        # price-tag style
        ctx.new_path(); ctx.move_to(-150, -90); ctx.line_to(120, -90); ctx.line_to(190, 0); ctx.line_to(120, 90); ctx.line_to(-150, 90); ctx.close_path()
        fill_stroke(ctx, YELLOW, NAVY, 8)
        circle(ctx, 125, 0, 16, WHITE, NAVY, 5)
        text(ctx, "SIZE", -20, -40, 40, NAVY, None, shadow=False)
        text(ctx, "5A", -20, 30, 110, PINK, NAVY)
        ctx.restore()
        star(ctx, 1560, 250, 50 * pop(t, wt("common", 36)), YELLOW, NAVY, 6, rot=t)
        caption_sticker(ctx, t, wt("common", 36), "#1 FOR BEGINNERS", 1350, 640, 40, PINK, WHITE, 0.03)

def sc_goldilocks(ctx, t, e):  # 41.28-44.24
    t_thick = wt("thick,", 41); t_thin = wt("thin.", 41)
    items = [(560, 60, "TOO THICK", t_thick, False), (960, 32, "JUST RIGHT", 41.4, True), (1360, 14, "TOO THIN", t_thin, False)]
    for (x, w, name, tt, good) in items:
        p = pop(t, tt if not good else 41.4)
        if p <= 0: continue
        ctx.save(); ctx.translate(x, 700); sscale(ctx, p, p)
        stick(ctx, 0, 0, -math.pi / 2, 470, w, face="smile" if good else None, t=t)
        ctx.restore()
        label(ctx, name, x, 160, 40, GREEN if good else RED, WHITE, scale=p)
        if good: check(ctx, x + 110, 280, 0.6, p=prog(t, 43.0, 0.4))
        else: cross(ctx, x + 110, 280, 0.6, p=prog(t, tt + 0.2, 0.4))

def sc_padpillow(ctx, t, e):  # 44.24-51.84
    tk = 44.3
    p = pop(t, tk)
    # mini drum kit with NOT YET stamp
    ctx.save(); ctx.translate(450, 460); sscale(ctx, 0.9 * p, 0.9 * p)
    circle(ctx, 0, 60, 150, (0.95, 0.3, 0.3), NAVY, LW); circle(ctx, 0, 60, 110, WHITE, NAVY, 5)
    ellipse(ctx, -150, -110, 80, 22, YELLOW, NAVY, 5); line(ctx, -150, -100, -150, 200, NAVY, 6)
    rrect(ctx, 60, -120, 120, 80, 20); fill_stroke(ctx, RED, NAVY, 5)
    rrect(ctx, -90, -140, 110, 70, 20); fill_stroke(ctx, RED, NAVY, 5)
    ctx.restore()
    sp = pop(t, wt("kit", 44) + 0.1)
    if sp > 0:
        ctx.save(); ctx.translate(450, 470); ctx.rotate(-0.25); sscale(ctx, lerp(2, 1, sp), lerp(2, 1, sp))
        rrect(ctx, -170, -50, 340, 100, 16); ctx.set_source_rgba(1, 1, 1, clamp(sp)); ctx.fill_preserve(); ctx.set_source_rgba(*RED, clamp(sp)); ctx.set_line_width(10); ctx.stroke()
        text(ctx, "NOT YET!", 0, 0, 64, RED, None, alpha=clamp(sp), shadow=False)
        ctx.restore()
    # practice pad
    tpad = wt("practice", 46)
    pp = pop(t, tpad)
    if pp > 0:
        ctx.save(); ctx.translate(1060, 440); sscale(ctx, pp, pp)
        pad_top(ctx, 0, 0, 150)
        ctx.restore()
        label(ctx, "PRACTICE PAD", 1060, 660, 40, WHITE, NAVY, scale=pp)
        check(ctx, 1180, 300, 0.6, p=prog(t, tpad + 0.4, .4))
    tpil = wt("pillow", 48)
    lp = pop(t, tpil)
    if lp > 0:
        ctx.save(); ctx.translate(1540, 440); sscale(ctx, lp, lp); ctx.rotate(wob(t, .7, .04))
        ctx.new_path()
        ctx.move_to(-170, -90); ctx.curve_to(-60, -70, 60, -70, 170, -90)
        ctx.curve_to(150, 0, 150, 0, 170, 90); ctx.curve_to(60, 70, -60, 70, -170, 90)
        ctx.curve_to(-150, 0, -150, 0, -170, -90); ctx.close_path()
        fill_stroke(ctx, (0.75, 0.85, 1.0), NAVY, LW)
        circle(ctx, 0, 0, 10, (0.55, 0.65, 0.95), None)
        ctx.restore()
        label(ctx, "PILLOW", 1540, 660, 40, WHITE, NAVY, scale=lp)
        check(ctx, 1680, 300, 0.6, p=prog(t, tpil + 0.4, .4))
        sn = wt("now.", 49)
        caption_sticker(ctx, t, sn, "START RIGHT NOW!", 1300, 150, 50, YELLOW, NAVY, 0.04)

def kid(ctx, x, y, t, straight=1.0, alpha=1.0, arms_up=0.0, shoulders=0.0, shake=0.0):
    """Side view kid on a stool, facing right. (x,y)= seat top."""
    sx = wob(t, 18, 4 * shake)
    ctx.save(); ctx.translate(x + sx, y)
    # stool
    rrect(ctx, -70, 0, 140, 26, 12); fill_stroke(ctx, ORANGE, NAVY, 5)
    line(ctx, -50, 26, -60, 230, NAVY, 10); line(ctx, 50, 26, 60, 230, NAVY, 10)
    # legs (thigh forward, shin down, feet flat)
    capsule(ctx, 0, -20, 130, -20, 28, PURPLE, NAVY, 5)
    capsule(ctx, 140, -20, 140, 200, 26, PURPLE, NAVY, 5)
    rrect(ctx, 120, 200, 90, 32, 14); fill_stroke(ctx, RED, NAVY, 5)
    # torso (lean)
    lean = lerp(0.45, 0.0, straight)
    ctx.save(); ctx.rotate(lean)
    rrect(ctx, -45, -260 - 12 * shoulders, 100, 250, 40); fill_stroke(ctx, TEAL, NAVY, 5)
    # head
    circle(ctx, 5, -330 - 14 * shoulders, 70, (1.0, 0.82, 0.66), NAVY, 5)
    ctx.new_path(); ctx.arc(5, -345 - 14 * shoulders, 72, math.pi * 1.0, math.pi * 1.95); ctx.close_path(); fill_stroke(ctx, (0.35, 0.2, 0.1), NAVY, 5)
    circle(ctx, 45, -330 - 14 * shoulders, 8, NAVY, None)
    ctx.new_path(); ctx.arc(40, -305 - 14 * shoulders, 16, 0.1 * math.pi, 0.8 * math.pi); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
    # arm
    capsule(ctx, 10, -220 - 12 * shoulders, 120, -130 + 60 * arms_up, 22, TEAL, NAVY, 5)
    circle(ctx, 130, -125 + 60 * arms_up, 26, GLOVE, NAVY, 5)
    ctx.restore()
    ctx.restore()

def sc_posture(ctx, t, e):  # 51.84-58.67
    p = pop(t, 51.9)
    ctx.save(); ctx.translate(CX - 120, 0); sscale(ctx, 1, 1)
    st = smooth(prog(t, wt("straight,", 51.8), 0.6))
    ctx.save(); ctx.translate(-100, 330); sscale(ctx, p * 0.95, p * 0.95)
    kid(ctx, 0, 330, t, straight=st)
    ctx.restore()
    # pad at waist height
    tpad = wt("place", 54)
    pp = pop(t, tpad)
    if pp > 0:
        ctx.save(); ctx.translate(230, 520); sscale(ctx, pp * 0.9, pp * 0.9)
        pad_side(ctx, 0, 0, 300)
        ctx.restore()
        tw = wt("waist", 54)
        wp = smooth(prog(t, tw, .5))
        if wp > 0:
            line(ctx, -250, 525, lerp(-250, 480, wp), 525, YELLOW, 7, dash=[20, 14])
            label(ctx, "WAIST HEIGHT", 480, 470, 38, YELLOW, NAVY, scale=pop(t, tw + .2))
    ctx.restore()
    caption_sticker(ctx, t, wt("straight,", 51.8), "SIT UP STRAIGHT", 520, 150, 46, GREEN, WHITE, -0.05)
    tf = wt("feet", 51.8)
    caption_sticker(ctx, t, tf, "FEET FLAT", 560, 760, 42, WHITE, NAVY, -0.05)
    if t > tf:
        a = smooth(prog(t, tf, .4))
        line(ctx, 690, 770, 860, 830, WHITE, 7, a)

def sc_parts(ctx, t, e):  # 58.67-75.84
    t0 = 58.7
    p = pop(t, t0)
    L = 1300
    x0 = 960 - L / 2 - 30; y0 = 440
    hi = None
    marks = [("tip", wt("tip", 60), TEAL, 1.0), ("shoulder", wt("shoulder,", 63), ORANGE, 0.82),
             ("shaft", wt("shaft.", 67), PURPLE, 0.42), ("butt", wt("butt.", 69), PINK, 0.03)]
    for (name, tt, col, f) in marks:
        if tt <= t < tt + 2.4: hi = name
    if t > 72.0: hi = "butt"
    ctx.save(); ctx.translate(960, y0); sscale(ctx, p, p); ctx.translate(-960, -y0)
    stick(ctx, x0, y0, 0, L, 48, t=t, hi=hi)
    ctx.restore()
    caption_sticker(ctx, t, t0 + 0.4, "4 PARTS OF A DRUMSTICK", 960, 160, 52, WHITE)
    for i, (name, tt, col, f) in enumerate(marks):
        pp = pop(t, tt)
        if pp <= 0: continue
        px = x0 + L * f + (60 if name == "tip" else 0)
        up = i % 2 == 0
        ly = y0 + (-150 if up else 150)
        line(ctx, px, y0 + (-40 if up else 40), px, ly + (40 if up else -40), WHITE, 6, clamp(pp))
        lbl = name.upper()
        label(ctx, lbl, px, ly, 46, col, WHITE, scale=pp, rot=wob(t, .6, .03, i))
    tb = wt("butt.", 69)
    if t > tb:
        # giggle face
        gp = pop(t, tb + 0.15)
        ctx.save(); ctx.translate(x0 + 40, y0 + 290); sscale(ctx, gp, gp); ctx.rotate(wob(t, 4, .15))
        circle(ctx, 0, 0, 52, YELLOW, NAVY, 5)
        for dx in (-18, 18):
            ctx.new_path(); ctx.arc(dx, -6, 10, math.pi * 1.1, math.pi * 1.9); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
        ctx.new_path(); ctx.arc(0, 8, 24, 0.05 * math.pi, 0.95 * math.pi); ctx.close_path(); fill_stroke(ctx, (0.45, 0.05, 0.12), NAVY, 5)
        ctx.restore()
        text(ctx, "hehe!", x0 + 150, y0 + 270, 44, WHITE, NAVY, scale=gp, rot=-0.15)
    ts = wt("start.", 72)
    if t > ts - 0.8:
        ap = pop(t, ts - 0.8)
        bx = x0 + 40 + wob(t, 2.5, 18)
        ctx.save(); ctx.translate(bx - 170, y0); sscale(ctx, ap, ap)
        ctx.new_path(); ctx.move_to(-90, -40); ctx.line_to(20, -40); ctx.line_to(20, -80); ctx.line_to(100, 0); ctx.line_to(20, 80); ctx.line_to(20, 40); ctx.line_to(-90, 40); ctx.close_path()
        fill_stroke(ctx, YELLOW, NAVY, 6)
        ctx.restore()
        caption_sticker(ctx, t, ts - 0.6, "START HERE!", x0 + 180, y0 - 170, 44, YELLOW, NAVY, -0.06)

def sc_fulcrum(ctx, t, e):  # 75.84-93.6
    L = 900
    fx, fy = 960, 470
    # balance point offset from butt as fraction; slides to 1/3
    ts = wt("slide", 84)
    tf = wt("third", 89)
    if t < ts:
        bal = 0.5
    else:
        bal = lerp(0.5, 1 / 3, ease_in_out(prog(t, ts, 1.6)))
    # tilt: when not at balance, wobble; at 1/3 settle
    settled = smooth(prog(t, ts + 1.6, 0.6))
    tilt = (0.18 * math.sin(t * 2.2)) * (1 - settled) + 0.03 * math.sin(t * 3) * settled
    p = pop(t, 75.9)
    ctx.save(); ctx.translate(fx, fy); sscale(ctx, p, p)
    glove_point(ctx, 0, 30, 0, scale=1.0)
    ctx.save(); ctx.rotate(tilt)
    stick(ctx, -L * bal, 0, 0, L, 34, face="smile", t=t)
    if t > tf:
        # ruler thirds
        rp = smooth(prog(t, tf, .5))
        for k in range(4):
            xx = -L * bal + L * k / 3
            line(ctx, xx, -40, xx, -75, WHITE, 6, rp)
        line(ctx, -L * bal, -58, -L * bal + L, -58, WHITE, 4, rp, dash=[12, 10])
        label(ctx, "1/3", -L * bal + L / 6, -110, 44, PINK, WHITE, scale=pop(t, tf + .2))
    ctx.restore()
    ctx.restore()
    tfu = wt("fulcrum.", 77)
    tbal = wt("balance", 75.8)
    caption_sticker(ctx, t, tbal, "BALANCE POINT", 960, 150, 52, YELLOW, NAVY, -0.03)
    fp = pop(t, tfu)
    if fp > 0:
        ctx.save(); ctx.translate(1560, 300); sscale(ctx, fp, fp); ctx.rotate(0.08 + wob(t, .5, .03))
        burst(ctx, 0, 0, 200, PINK, NAVY, 22, t * .3)
        text(ctx, "FULCRUM", 0, -5, 56, WHITE, NAVY)
        ctx.restore() if False else ctx.restore()
    tl = wt("light", 80)
    if tl < t < ts:
        for i in range(3):
            ph = (t * 1.5 + i / 3) % 1
            text(ctx, "boing!", 420 + 40 * i, 420 - 200 * ph, 44, YELLOW, NAVY, alpha=1 - ph, rot=-0.2)

def sc_pinch(ctx, t, e):  # 93.6-108.32
    t0 = 93.6
    tpen = wt("pencil,", 98)
    tpiv = wt("pivot.", 103)
    p = pop(t, t0)
    if t < tpen - 0.3:
        f = PH + 'p7_pinch.jpg'; cx, cy, w, h = 880, 450, 1060, 700
        z = kb(t, t0, 4.5)
        photo_card(ctx, f, cx, cy, w, h, scale=p, zoom=z, focus=(.3, .5), tag="CLOSE-UP", t=t)
        m = lambda x, y: img_to_card(x, y, f, cx, cy, w, h, z, (.3, .5))
        if p > .9:
            X, Y = m(330, 420); ring(ctx, X, Y, 120 * pop(t, t0 + .5), t)
            tt = wt("thumb", 94); a = m(400, 320)
            arrow(ctx, a[0] + 420, a[1] - 150, a[0] + 40, a[1] - 20, YELLOW, s=ease_out(prog(t, tt, .4)))
            label(ctx, "THUMB", a[0] + 520, a[1] - 170, 42, YELLOW, NAVY, scale=pop(t, tt))
            tf = wt("first", 94); b = m(300, 610)
            arrow(ctx, b[0] - 330, b[1] + 70, b[0] - 40, b[1] + 10, TEAL, s=ease_out(prog(t, tf, .4)))
            label(ctx, "SIDE OF 1ST FINGER", b[0] - 330, b[1] + 130, 36, TEAL, WHITE, scale=pop(t, tf))
        caption_sticker(ctx, t, t0 + .2, "PINCH IT HERE", 1600, 260, 44, PINK, WHITE, 0.05)
    elif t < tpiv - 0.2:
        pp = pop(t, tpen - 0.3)
        ctx.save(); ctx.translate(780, 450); sscale(ctx, pp, pp); ctx.rotate(-0.4)
        rrect(ctx, -260, -24, 420, 48, 6); fill_stroke(ctx, YELLOW, NAVY, 5)
        ctx.new_path(); ctx.move_to(160, -24); ctx.line_to(240, 0); ctx.line_to(160, 24); ctx.close_path(); fill_stroke(ctx, (1, .87, .7), NAVY, 5)
        ctx.new_path(); ctx.move_to(220, -7); ctx.line_to(240, 0); ctx.line_to(220, 7); ctx.close_path(); ctx.set_source_rgb(*NAVY); ctx.fill()
        rrect(ctx, -300, -24, 50, 48, 10); fill_stroke(ctx, PINK, NAVY, 5)
        ctx.restore()
        # feather = lighter
        tl = wt("lighter.", 98)
        fp = pop(t, tl)
        if fp > 0:
            ctx.save(); ctx.translate(1350, 420 + wob(t, .8, 30)); ctx.rotate(0.5 + wob(t, .6, .3)); sscale(ctx, fp, fp)
            ctx.new_path(); ctx.move_to(0, -150); ctx.curve_to(90, -60, 70, 80, 0, 150); ctx.curve_to(-70, 80, -90, -60, 0, -150); ctx.close_path()
            fill_stroke(ctx, WHITE, NAVY, 5)
            line(ctx, 0, -130, 0, 190, NAVY, 5)
            ctx.restore()
            caption_sticker(ctx, t, tl, "LIGHTER!", 1350, 200, 56, YELLOW, NAVY, 0.06)
        caption_sticker(ctx, t, tpen - 0.2, "LIKE A PENCIL", 700, 150, 50, WHITE, NAVY, -0.04)
        tw = wt("fall.", 100)
        if t > tw - 0.6:
            caption_sticker(ctx, t, tw - 0.6, "JUST ENOUGH!", 760, 760, 44, GREEN, WHITE, 0.03)
    else:
        # seesaw pivot
        pp = pop(t, tpiv - 0.2)
        ang = 0.28 * math.sin((t - tpiv) * 3.2)
        ctx.save(); ctx.translate(960, 480); sscale(ctx, pp, pp)
        ctx.new_path(); ctx.move_to(0, 20); ctx.line_to(-80, 170); ctx.line_to(80, 170); ctx.close_path(); fill_stroke(ctx, ORANGE, NAVY, 6)
        ctx.save(); ctx.rotate(ang)
        stick(ctx, -300, 0, 0, 900, 34, face="smile", t=t)
        ctx.restore()
        circle(ctx, 0, 0, 20, PINK, NAVY, 5)
        ctx.restore()
        title_slam(ctx, t, tpiv, "PIVOT!", 960, 190, 110, YELLOW, -0.04)
        caption_sticker(ctx, t, wt("seesaw.", 105), "LIKE A SEESAW", 960, 760, 46, WHITE, NAVY)

def sc_check(ctx, t, e):  # 108.32-118.16
    t0 = 108.32
    title_slam(ctx, t, t0, "QUICK CHECK!", 960, 160, 100, YELLOW, -0.03)
    tstuck = wt("stuck,", 113)
    tloose = wt("loosen", 116)
    p = pop(t, t0 + 0.3)
    stuck = smooth(prog(t, tstuck, .3)) * (1 - smooth(prog(t, tloose, .5)))
    wig = math.sin(t * 9) * 0.22 * (1 - stuck)
    ctx.save(); ctx.translate(640, 470); sscale(ctx, p, p)
    ctx.save(); ctx.rotate(wig)
    stick(ctx, -170, 0, 0, 560, 30, face="squeezed" if stuck > .5 else "smile", t=t)
    ctx.restore()
    hand_grip(ctx, -30, 0, 0, curl=stuck, squeeze=stuck, t=t, scale=1.0)
    if stuck < .5 and t > t0 + 1.5:
        motion_lines(ctx, 420, -100 + 120 * math.sin(t * 9), math.pi / 2, 3, 40, 22, WHITE, .8)
    ctx.restore()
    if t < tstuck:
        check(ctx, 640, 250, 0.7, p=prog(t, wt("great.", 111), .4))
    # squeeze-o-meter
    mp = pop(t, tstuck - 0.2)
    if mp > 0:
        ctx.save(); ctx.translate(1380, 520); sscale(ctx, mp, mp)
        panel(ctx, 0, -20, 500, 360, WHITE)
        for k, col in enumerate([GREEN, YELLOW, RED]):
            a0 = math.pi + k * math.pi / 3
            ctx.new_path(); ctx.arc(0, 60, 180, a0, a0 + math.pi / 3); ctx.arc_negative(0, 60, 110, a0 + math.pi / 3, a0); ctx.close_path()
            fill_stroke(ctx, col, NAVY, 5)
        v = lerp(0.15, 0.92, stuck) + 0.03 * math.sin(t * 15) * stuck
        na = math.pi + v * math.pi
        line(ctx, 0, 60, 150 * math.cos(na), 60 + 150 * math.sin(na), NAVY, 10)
        circle(ctx, 0, 60, 18, NAVY, None)
        text(ctx, "SQUEEZE-O-METER", 0, -150, 40, NAVY, None, shadow=False)
        ctx.restore()
        if t > tloose:
            caption_sticker(ctx, t, tloose, "LOOSEN UP!", 1380, 790, 48, GREEN, WHITE, 0.04)

def sc_bird(ctx, t, e):  # 118.16-141.12
    t0 = 118.16
    tcurl = wt("curl", 120)
    tbird = wt("bird.", 128)
    tclamp = wt("clamp", 135)
    tpoke = wt("poke", 137)
    curl = smooth(prog(t, tcurl, 1.2))
    if t >= tpoke - 0.3:
        f = PH + 'p1_sidegrip.jpg'; cx, cy, w, h = 900, 450, 1180, 650
        cp = card_in(t, tpoke - 0.3)
        photo_card(ctx, f, cx, cy, w, h, scale=cp, zoom=1.0, tag="REAL LIFE", t=t)
        if cp > .9:
            hx, hy = img_to_card(1300, 600, f, cx, cy, w, h); ring(ctx, hx, hy, 150 * pop(t, tpoke + .1), t)
            bx, by = img_to_card(1465, 735, f, cx, cy, w, h)
            arrow(ctx, bx + 230, by + 150, bx + 25, by + 20, PINK, s=ease_out(prog(t, tpoke + .3, .4)))
            label(ctx, "FINGERS WRAPPED LOOSELY", cx - 120, cy - 260, 40, YELLOW, NAVY, rot=-.03, scale=pop(t, tpoke + .2))
            label(ctx, "END POKES OUT!", 1620, 800, 40, PINK, WHITE, rot=.05, scale=pop(t, tpoke + .5))
        return
    if t < tbird - 0.8 or t > tclamp - 0.3:
        p = pop(t, t0 if t < tbird else tclamp - 0.3)
        ctx.save(); ctx.translate(800, 450); sscale(ctx, 1.35 * p, 1.35 * p)
        stick(ctx, -330, 0, 0, 640, 30, t=t, hi="butt" if t > tpoke else None)
        glove_grip(ctx, -120, 0, 0, curl=0.0 if curl < 0.5 else 1.0, t=t)
        ctx.restore()
        if t < tbird:
            caption_sticker(ctx, t, t0 + .2, "CURL YOUR FINGERS", 1400, 200, 46, YELLOW, NAVY, 0.04)
            for i, (nm, tw) in enumerate([("MIDDLE", wt("middle,", 120)), ("RING", wt("ring,", 120)), ("PINKY", wt("pinky", 120))]):
                label(ctx, nm, 1420, 360 + i * 110, 40, [PINK, TEAL, PURPLE][i], WHITE, scale=pop(t, tw))
            caption_sticker(ctx, t, wt("loosely.", 124), "LOOSELY!", 1420, 720, 44, GREEN, WHITE, -0.04)
        else:
            caption_sticker(ctx, t, tclamp - 0.3, "TOUCH, DON'T CLAMP", 1400, 200, 46, YELLOW, NAVY, 0.04)
            if t > tpoke:
                caption_sticker(ctx, t, tpoke, "END POKES OUT A LITTLE", 1250, 720, 42, PINK, WHITE, -0.03)
    else:
        p = pop(t, tbird - 0.8)
        tfly = wt("fly", 129); thurt = wt("hurt", 131)
        flap = 1.0 if tfly <= t < tfly + 1.5 else 0.2
        ctx.save(); ctx.translate(960, 500); sscale(ctx, p, p)
        hand_cup(ctx)
        bird(ctx, 0, -110 + wob(t, 2, 6) - (30 if flap > .5 else 0) * abs(math.sin(t * 6)), 1.4, t, flap)
        ctx.restore()
        for i in range(3):
            ph = (t * 0.8 + i / 3) % 1
            hx = 960 + 160 * (i - 1); hy = 300 - 180 * ph
            ctx.save(); ctx.translate(hx, hy); sscale(ctx, 1 - ph * .3, 1 - ph * .3)
            ctx.new_path(); ctx.move_to(0, 18); ctx.curve_to(-40, -10, -20, -40, 0, -20); ctx.curve_to(20, -40, 40, -10, 0, 18)
            fill_stroke(ctx, PINK, NAVY, 4, alpha=1 - ph); ctx.restore()
        caption_sticker(ctx, t, tbird - 0.6, "HOLD IT LIKE A SMALL BIRD", 960, 150, 50, YELLOW, NAVY, -0.03)
        if t > tfly:
            caption_sticker(ctx, t, tfly, "FIRM ENOUGH...", 470, 470, 44, TEAL, WHITE, -0.08)
        if t > thurt:
            caption_sticker(ctx, t, thurt, "...SOFT ENOUGH!", 1450, 470, 44, PINK, WHITE, 0.08)

def sc_matched(ctx, t, e):  # 141.12-163.76
    t0 = 141.12
    tthumb = wt("thumbs", 145)
    ttips = wt("tips", 149)
    tv = wt("V", 152)
    tmatch = wt("matched", 154)
    tsame = wt("same", 155)
    tgreat = wt("great", 160)
    if t < tgreat - 0.2:
        f = PH + 'p5_vgrip.png'; cx, cy, w, h, fo = 900, 450, 980, 700, (.5, .42)
        z = kb(t, t0, tgreat - t0, 1.0, 1.05)
        cp = card_in(t, t0)
        photo_card(ctx, f, cx, cy, w, h, scale=cp, zoom=z, focus=fo, tag="CLOSE-UP", t=t)
        m = lambda x, y: img_to_card(x, y, f, cx, cy, w, h, z, fo)
        if cp > .9:
            if t > tthumb:
                for (x, y) in [(487, 672), (783, 676)]:
                    X, Y = m(x, y); ring(ctx, X, Y, 62 * pop(t, tthumb), t)
                lx, ly = m(487, 672); rx, ry = m(783, 676)
                label(ctx, "THUMBS POINT IN!", (lx + rx) / 2, ly + 120, 40, YELLOW, NAVY, scale=pop(t, tthumb + .3))
            if t > ttips:
                tx, ty = m(618, 280); label(ctx, "TIPS CLOSE TOGETHER", tx, ty - 60, 36, PINK, WHITE, rot=-.03, scale=pop(t, ttips))
        caption_sticker(ctx, t, t0 + .3, "PALMS DOWN", 1590, 200, 42, WHITE, NAVY, -0.04)
        if t > tv:
            label(ctx, "V", 1590, 350, 110, PINK, WHITE, rot=.08, scale=pop(t, tv))
        if t > tmatch:
            mp = pop(t, tmatch)
            ctx.save(); ctx.translate(1590, 520); sscale(ctx, mp, mp); ctx.rotate(-.04 + wob(t, .5, .02))
            panel(ctx, 0, 0, 470, 96, YELLOW, r=48)
            text(ctx, "MATCHED GRIP", 0, 0, 54, PINK, NAVY)
            ctx.restore()
        if t > tsame:
            label(ctx, "BOTH HANDS THE SAME", 1590, 660, 34, GREEN, WHITE, rot=.03, scale=pop(t, tsame))
    else:
        f = PH + 'p4_playing.jpg'
        photo_card(ctx, f, 900, 440, 1100, 660, rot=-.03, scale=card_in(t, tgreat - 0.2), zoom=kb(t, tgreat, 4), tag="REAL LIFE", t=t)
        label(ctx, "MATCHED GRIP", 1560, 250, 52, YELLOW, NAVY, rot=.06, scale=pop(t, tgreat))
        for i in range(4):
            star(ctx, 1560 + 170 * math.cos(i * 1.6 + t), 560 + 120 * math.sin(i * 1.6 + t), 30 * pop(t, tgreat + .2), YELLOW, NAVY, 4)
        label(ctx, "GREAT PLACE TO START!", 1560, 700, 38, GREEN, WHITE, rot=-.03, scale=pop(t, tgreat + .3))

def sc_bounce(ctx, t, e):  # 163.76-198.27
    t0 = 163.76
    _treb = wt("rebound,", 179); _tthud = wt("thuds", 184)
    if _treb - 0.3 <= t < _tthud - 0.3:
        f = PH + 'p6_pad.jpg'; cx, cy, w, h = 880, 450, 1060, 700
        photo_card(ctx, f, cx, cy, w, h, scale=card_in(t, _treb - 0.3), zoom=kb(t, _treb, 4.5), focus=(.5, .5), tag="CLOSE-UP", t=t)
        z = kb(t, _treb, 4.5)
        X, Y = img_to_card(560, 440, f, cx, cy, w, h, z, (.5, .5))
        beat = (t * 1.6) % 1
        for i in range(3):
            ph = (t * 1.3 + i / 3) % 1
            ctx.new_path(); ctx.arc(X, Y - 10, 40 + 110 * ph, math.pi * 1.05, math.pi * 1.95); ctx.set_source_rgba(1, 1, 1, 1 - ph); ctx.set_line_width(8); ctx.stroke()
        if beat < .25:
            burst(ctx, X - 70, Y + 40, 34 * (1 - beat * 4), YELLOW, None, 10, t)
            burst(ctx, X + 40, Y + 60, 26 * (1 - beat * 4), YELLOW, None, 10, -t)
        label(ctx, "BOING!", X + 40, Y - 190, 56, YELLOW, NAVY, rot=-.1, scale=1 + .12 * max(0, 1 - beat * 4))
        ctx.save(); ctx.translate(1580, 300); ctx.rotate(-.06); rp = pop(t, _treb)
        sscale(ctx, rp, rp); burst(ctx, 0, 0, 190, PINK, NAVY, 16, t * .5); text(ctx, "REBOUND!", 0, 0, 56, WHITE, NAVY); ctx.restore()
        caption_sticker(ctx, t, wt("easy.", 182), "DRUMMING = EASY!", 1580, 600, 40, GREEN, WHITE, -0.04)
        return
    tdrop = wt("drop.", 166)
    tlet = wt("gravity", 172)
    treb = wt("rebound,", 179)
    tthud = wt("thuds", 184)
    trelax = wt("relax", 188)
    ttaps = wt("slow", 190)
    padx, pady = 960, 520
    title_slam(ctx, t, t0, "THE BOUNCE TEST!", 960, 150, 90, YELLOW, -0.03)
    p = pop(t, t0 + .2)
    ctx.save(); ctx.translate(padx, pady); sscale(ctx, p, p)
    pad_side(ctx, 0, 0, 460)
    # stick pivot (glove) at left, tip near pad
    gx, gy = -420, -120
    # angle of stick: 0 = horizontal-ish touching pad
    rest = -0.32   # raised
    hit = 0.17     # touching pad
    tight = (tthud - 0.3 <= t < trelax)
    if t < tdrop:
        ang = rest + 0.02 * math.sin(t * 2)
    elif t < ttaps:
        # bounce physics: periodic drop/bounce
        period = 1.6
        ph = ((t - tdrop) % period) / period
        if tight:
            # fall then stop
            fall = smooth(clamp(ph / 0.3))
            ang = lerp(rest, hit, fall) if ph < 0.85 else lerp(hit, rest, (ph - .85) / .15)
        else:
            # fall, then bouncy decaying rebounds
            if ph < 0.25:
                ang = lerp(rest, hit, (ph / 0.25) ** 2)
            else:
                q = (ph - 0.25) / 0.75
                amp = (rest - hit) * 0.85 * math.exp(-3.0 * q)
                ang = hit + amp * abs(math.sin(q * math.pi * 3.0))
    else:
        # alternating slow taps
        ph = ((t - ttaps) % 1.2) / 1.2
        ang = lerp(rest, hit, abs(math.cos(ph * math.pi)) ** 3) if True else rest
        ang = hit + (rest - hit) * (1 - abs(math.sin(ph * math.pi)) ** 0.5) * 0 + (rest - hit) * (0.5 - 0.5 * math.cos(ph * 2 * math.pi))
    stick(ctx, gx - 150, gy - 150 * math.tan(ang) * 0, ang, 640, 30, face="sad" if tight and t > tthud else "smile", t=t)
    glove_grip(ctx, gx - 20, gy, ang, curl=1, squeeze=1.0 if tight else 0.0, t=t, scale=0.8)
    ctx.restore()
    # contact effects
    if tdrop < t < ttaps:
        period = 1.6
        ph = ((t - tdrop) % period) / period
        if 0.24 < ph < 0.4:
            if tight:
                text(ctx, "THUD.", padx + 260, pady - 120, 70, (0.7, 0.75, 0.85), NAVY, scale=1, rot=0.1)
            else:
                burst(ctx, padx + 100, pady - 20, 70 * (1 - (ph - .24) / .16), YELLOW, None, 10)
                text(ctx, "BOING!", padx + 120, pady - 230, 64, YELLOW, NAVY, scale=back((ph - .24) / .16), rot=-0.1)
    if t < tdrop:
        caption_sticker(ctx, t, wt("inches", 166), "A FEW INCHES UP", 1500, 330, 42, WHITE, NAVY, 0.04)
    if tlet - 2.5 < t < treb:
        caption_sticker(ctx, t, wt("push", 168), "DON'T PUSH - LET IT DROP!", 1440, 330, 40, WHITE, NAVY, 0.04)
    rp = pop(t, treb)
    if treb < t < tthud - 0.3:
        ctx.save(); ctx.translate(1450, 330); sscale(ctx, rp, rp); ctx.rotate(-0.06 + wob(t, 2, .04))
        burst(ctx, 0, 0, 190, PINK, NAVY, 16, t * .5)
        text(ctx, "REBOUND!", 0, 0, 58, WHITE, NAVY)
        ctx.restore()
        caption_sticker(ctx, t, wt("easy.", 182), "DRUMMING = EASY!", 1450, 560, 42, GREEN, WHITE, -0.04)
    if tthud - 0.3 < t < trelax:
        ctx.save(); ctx.translate(1450, 330); ctx.rotate(0.08)
        sp = pop(t, wt("tight.", 186))
        burst(ctx, 0, 0, 170 * sp, RED, NAVY, 14)
        text(ctx, "TOO TIGHT!", 0, 0, 52, WHITE, NAVY, scale=sp)
        ctx.restore()
    if t > trelax:
        caption_sticker(ctx, t, trelax, "RELAX & TRY AGAIN", 1450, 330, 44, GREEN, WHITE, 0.04)
    if t > ttaps:
        caption_sticker(ctx, t, ttaps, "SLOW TAPS - ONE HAND", 1450, 470, 40, YELLOW, NAVY, -0.03)
        n = int((t - ttaps) / 1.2) + 1
        label(ctx, f"TAP x{n}", 1450, 600, 44, PINK, WHITE, scale=1 + 0.15 * max(0, 1 - ((t - ttaps) % 1.2) / .3))

MISTAKES = None

def sc_mistakes(ctx, t, e):  # 198.27-243.95
    t0 = 198.27
    marks = [wt("one.", 201), wt("two.", 209), wt("three.", 217), wt("four.", 228), wt("five.", 235)]
    if t < marks[0] - 0.2:
        title_slam(ctx, t, t0 + .1, "5 BEGINNER", 960, 300, 120, WHITE, -0.03)
        title_slam(ctx, t, t0 + .6, "MISTAKES!", 960, 450, 140, RED, 0.02)
        for i in range(5):
            pp = pop(t, wt("five", 198) + i * 0.15)
            label(ctx, f"#{i + 1}", 560 + i * 200, 650, 56, [PINK, ORANGE, TEAL, PURPLE, GREEN][i], WHITE, scale=pp, rot=wob(t, .6, .06, i))
        return
    k = max(i for i in range(5) if t >= marks[i] - 0.2)
    tm = marks[k]
    end = marks[k + 1] if k < 4 else 243.95
    names = ["DEATH GRIP", "THUMB ON TOP", "HOLDING THE END", "FINGERS OUT", "TENSE SHOULDERS"]
    fixes = ["HOLD THE BIRD", "THUMB ON THE SIDE", "BALANCE POINT", "CURL THEM IN", "BREATHE & SHAKE"]
    fix_words = [("fix", tm), ("keep", tm), ("go", tm), ("keep", tm), ("take", tm)]
    tfix = wt(*fix_words[k])
    colk = [PINK, ORANGE, TEAL, PURPLE, GREEN][k]
    # badge
    bp = pop(t, tm - 0.2)
    ctx.save(); ctx.translate(250, 220); ctx.rotate(-0.12); sscale(ctx, bp, bp)
    star(ctx, 0, 0, 130, colk, NAVY, 7, rot=t * 0.3)
    text(ctx, f"#{k + 1}", 0, 0, 92, WHITE, NAVY)
    ctx.restore()
    label(ctx, names[k], 960, 150, 64, RED, WHITE, scale=pop(t, tm), rot=wob(t, .6, .02))
    fixed = t >= tfix
    fp = smooth(prog(t, tfix, .5))
    cxs, cys = 960, 470
    ctx.save(); ctx.translate(cxs, cys)
    if k == 0:
        sq = 1 - fp
        stick(ctx, -360, 0, 0, 640, 30, face="squeezed" if sq > .5 else "smile", t=t)
        glove_grip(ctx, -160, 0, 0, curl=1, squeeze=sq, t=t)
        if fixed: bird(ctx, 330, -110, 0.9 * pop(t, tfix), t, 0.5)
        else:
            for i in range(3):
                ph = (t * 1.3 + i / 3) % 1
                ellipse(ctx, -160 + 40 * (i - 1), -140 - 120 * ph, 18, 12, WHITE, None, alpha=.7 * (1 - ph))
    elif k == 1:
        stick(ctx, -360, 0, 0, 640, 30, t=t)
        glove_grip(ctx, -160, 0, 0, curl=1, thumb_top=not fixed, t=t)
        if not fixed:
            ctx.save(); ctx.translate(-120, -200 + wob(t, 3, 12))
            ctx.new_path(); ctx.move_to(-25, -60); ctx.line_to(25, -60); ctx.line_to(25, 0); ctx.line_to(50, 0); ctx.line_to(0, 50); ctx.line_to(-50, 0); ctx.line_to(-25, 0); ctx.close_path()
            fill_stroke(ctx, RED, NAVY, 5); ctx.restore()
    elif k == 2:
        wobble = (1 - fp) * 0.25 * math.sin(t * 7)
        bal = lerp(0.02, 1 / 3, fp)
        ctx.save(); ctx.rotate(wobble)
        stick(ctx, -700 * bal, 0, 0, 700, 30, face="squeezed" if not fixed else "smile", t=t)
        ctx.restore()
        hand_grip(ctx, -10, 0, 0, curl=1.0, t=t)
        if not fixed: motion_lines(ctx, 520, -60, math.pi / 2, 3, 40, 22, WHITE, .8)
    elif k == 3:
        stick(ctx, -360, 0, 0, 640, 30, t=t)
        glove_grip(ctx, -160, 0, 0, curl=fp, splay=1 - fp, t=t)
    else:
        kid(ctx, -200, 140, t, straight=1, shoulders=1 - fp, shake=fp if fixed and t < tfix + 3 else 0, arms_up=0.3)
        if not fixed:
            for i in range(2):
                ctx.save(); ctx.translate(-180 + 160 * i, -260); ctx.rotate(0.3 * (i - .5))
                ctx.new_path(); ctx.move_to(0, -40); ctx.line_to(-18, 0); ctx.line_to(4, 0); ctx.line_to(-10, 40); ctx.line_to(22, -8); ctx.line_to(2, -8); ctx.line_to(14, -40); ctx.close_path()
                fill_stroke(ctx, YELLOW, NAVY, 4); ctx.restore()
        else:
            for i in range(3):
                ph = (t * 0.7 + i / 3) % 1
                ctx.new_path(); ctx.arc(-120, -360, 60 + 120 * ph, -2.3, -0.8); ctx.set_source_rgba(1, 1, 1, 1 - ph); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()
    if not fixed:
        cross(ctx, 1500, 470, 1.2, p=prog(t, tm + 0.6, .4))
    else:
        check(ctx, 1500, 470, 1.2, p=prog(t, tfix, .4))
        label(ctx, fixes[k], 1500, 650, 44, GREEN, WHITE, scale=pop(t, tfix + .1), rot=0.03)
        confetti(ctx, 1500, 470, t - tfix, seed=20 + k, n=30, spread=380, dur=1.5)

def sc_bonus(ctx, t, e):  # 243.95-254.04
    t0 = 243.95
    tb = wt("bonus:", 248)
    tt = wt("tips.", 250)
    op = smooth(prog(t, tb, 0.6))
    gift(ctx, 960, 520, 1.6 * pop(t, t0), t, op, shake=1 - op)
    if op > 0:
        burst(ctx, 960, 400, 340 * ease_out(op), YELLOW, None, 20, t * .5, alpha=.8 * op)
        confetti(ctx, 960, 420, t - tb, seed=33, n=90, spread=900, dur=2.5)
        title_slam(ctx, t, tb + .2, "BONUS!", 960, 330, 150, YELLOW, -0.04)
    caption_sticker(ctx, t, wt("minute,", 245), "ONE MORE MINUTE!", 960, 150, 50, WHITE, NAVY, 0.03)
    if t > tt:
        for i in range(2):
            label(ctx, f"SECRET TIP {i + 1}", 600 + 720 * i, 740, 46, [PINK, TEAL][i], WHITE, scale=pop(t, tt + .2 * i), rot=wob(t, .5, .04, i))

def sc_tip1(ctx, t, e):  # 254.04-267.56
    t0 = 254.04
    label(ctx, "TIP 1: DAILY PRACTICE", 960, 145, 56, PINK, WHITE, scale=pop(t, t0))
    ttimer = wt("timer", 256)
    tp = pop(t, ttimer - 0.2)
    if tp > 0:
        ctx.save(); ctx.translate(380, 450); sscale(ctx, tp, tp)
        circle(ctx, 0, 0, 170, WHITE, NAVY, 9)
        rrect(ctx, -30, -225, 60, 50, 12); fill_stroke(ctx, RED, NAVY, 6)
        rem = max(0, 60 - (t - ttimer - 0.6) * 1.0) if t > ttimer + .6 else 60
        frac = rem / 60
        ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 150, -math.pi / 2, -math.pi / 2 + 2 * math.pi * frac); ctx.close_path()
        ctx.set_source_rgba(*YELLOW, .7); ctx.fill()
        text(ctx, f"0:{int(rem):02d}" if rem < 60 else "1:00", 0, 0, 80, NAVY, None, shadow=False)
        ctx.restore()
    # R L R L taps
    tr = wt("right,", 258)
    ctx.save(); ctx.translate(1180, 520)
    pad_top(ctx, 0, 0, 200)
    rl = [w for w in WORDS if tr - 0.01 <= w["start"] < 264 and norm(w["text"]) in ("right", "left", "one", "two")]
    active = None
    for w in rl:
        if w["start"] <= t: active = w
    for sgn, side in ((-1, "left"), (1, "right")):
        hitting = active is not None and norm(active["text"]) == side and t - active["start"] < 0.35
        lift = 0 if hitting else 1
        if active is not None and norm(active["text"]) in ("one", "two"):
            hitting = (norm(active["text"]) == "one") == (sgn > 0) and t - active["start"] < .35
            lift = 0 if hitting else 1
        a = -math.pi / 2 - sgn * 0.45
        ctx.save(); ctx.translate(sgn * 330, 300); ctx.rotate(a + sgn * 0.0)
        ctx.restore()
        tipx, tipy = sgn * 40, -20 - lift * 130
        bx, by = sgn * 380, 330
        ang = math.atan2(tipy - by, tipx - bx)
        Lst = math.hypot(tipx - bx, tipy - by)
        stick(ctx, bx, by, ang, Lst, 26, t=t)
        if hitting:
            burst(ctx, tipx, -20, 70, YELLOW, None, 10)
        lab = "R" if sgn > 0 else "L"
        label(ctx, lab, sgn * 300, -230, 64, YELLOW if hitting else WHITE, NAVY, scale=1.25 if hitting else 1.0)
    ctx.restore()
    if active is not None and t - active["start"] < .6:
        txt = active["text"].strip(",.").upper()
        text(ctx, txt + "!", 1640, 330 - 30 * prog(t, active["start"], .6), 64, PINK, NAVY, alpha=1 - prog(t, active["start"] + .3, .3))
    tl = wt("loose,", 264)
    if t > tl:
        caption_sticker(ctx, t, tl, "STAY LOOSE & LISTEN FOR THE BOUNCE", 960, 790 - 20, 40, GREEN, WHITE, 0.0)

def sc_tip2(ctx, t, e):  # 267.56-276.85
    t0 = 267.56
    label(ctx, "TIP 2: A LITTLE EVERY DAY", 960, 145, 56, TEAL, WHITE, scale=pop(t, t0))
    days = ["M", "T", "W", "T", "F", "S", "S"]
    for i, d in enumerate(days):
        p = pop(t, t0 + 0.3 + i * 0.12)
        x = 420 + i * 180; y = 430
        ctx.save(); ctx.translate(x, y); sscale(ctx, p, p)
        panel(ctx, 0, 0, 150, 170, WHITE, r=24)
        rrect(ctx, -75, -85, 150, 50, 20); fill_stroke(ctx, RED, NAVY, 5)
        text(ctx, d, 0, -60, 36, WHITE, NAVY)
        ctx.restore()
        tchk = wt("day,", 268) + 0.15 * i
        if t > tchk: check(ctx, x, y + 30, 0.6, p=prog(t, tchk, .35))
    tw = wt("week.", 268)
    if t > tw:
        sp = pop(t, tw)
        ctx.save(); ctx.translate(960, 680); ctx.rotate(-0.04); sscale(ctx, sp, sp)
        label(ctx, "NOT ONCE A WEEK!", 0, 0, 48, RED, WHITE)
        ctx.restore()
    tn = wt("natural", 274)
    if t > tn - .6:
        rp = prog(t, tn - .6, 2.5)
        ctx.save(); ctx.translate(1650, 700 - 600 * ease_in_out(rp)); ctx.rotate(-0.5)
        rrect(ctx, -40, -110, 80, 200, 40); fill_stroke(ctx, WHITE, NAVY, 6)
        circle(ctx, 0, -40, 20, TEAL, NAVY, 5)
        ctx.new_path(); ctx.move_to(-40, 40); ctx.line_to(-75, 100); ctx.line_to(-40, 90); ctx.close_path(); fill_stroke(ctx, RED, NAVY, 5)
        ctx.new_path(); ctx.move_to(40, 40); ctx.line_to(75, 100); ctx.line_to(40, 90); ctx.close_path(); fill_stroke(ctx, RED, NAVY, 5)
        for i in range(3):
            ellipse(ctx, wob(t, 9, 8, i), 130 + i * 35, 22 - i * 5, 30 - i * 5, [YELLOW, ORANGE, RED][i], None)
        ctx.restore()
        caption_sticker(ctx, t, tn - .3, "FEELS NATURAL FAST!", 1300, 790 - 30, 44, YELLOW, NAVY, -0.04)

def sc_outro(ctx, t, e):  # 276.85-end
    t0 = 276.85
    label(ctx, "NEXT EPISODE", 960, 140, 56, PINK, WHITE, scale=pop(t, t0))
    p = card_in(t, t0 + .3)
    photo_card(ctx, PH + 'p3_kit.jpg', 680, 480, 820, 500, rot=.02, scale=p, zoom=kb(t, t0, 9, 1.0, 1.08), tag="SNEAK PEEK", t=t)
    label(ctx, "EP 2", 1050, 250, 64, YELLOW, NAVY, rot=.1, scale=pop(t, t0 + .6))
    caption_sticker(ctx, t, wt("drum", 277.5), "MEET THE DRUM KIT!", 700, 790 - 30, 44, YELLOW, NAVY, -0.03)
    ts = wt("subscribe,", 281)
    sp = pop(t, ts - 0.3)
    if sp > 0:
        pulse = 1 + 0.06 * math.sin(t * 7)
        clicked = t > ts + 0.5
        ctx.save(); ctx.translate(1420, 440); sscale(ctx, sp * pulse, sp * pulse)
        rrect(ctx, -230, -70, 460, 140, 70); fill_stroke(ctx, (0.55, 0.55, 0.6) if clicked else RED, NAVY, 7)
        text(ctx, "SUBSCRIBED!" if clicked else "SUBSCRIBE", 0, 0, 58 if not clicked else 50, WHITE, NAVY)
        ctx.restore()
        # bell
        bp = pop(t, ts + .4)
        ctx.save(); ctx.translate(1720, 330); sscale(ctx, bp, bp); ctx.rotate(wob(t, 3, .3))
        ctx.new_path(); ctx.move_to(-50, 40); ctx.curve_to(-50, -60, 50, -60, 50, 40); ctx.close_path(); fill_stroke(ctx, YELLOW, NAVY, 5)
        circle(ctx, 0, 52, 12, YELLOW, NAVY, 5)
        ctx.restore()
        # glove clicking
        gp = prog(t, ts - 0.2, 0.7)
        if gp < 1 or t < ts + 2:
            burst(ctx, 1420, 440, 300 * ease_out(clamp((t - ts - .4) / .3)) * (1 - clamp((t - ts - .7) / .3)), YELLOW, None, 16, t, alpha=.3)
        confetti(ctx, 1420, 440, t - ts - 0.5, seed=44, n=50, spread=600)
    tsee = wt("next", 284)
    if t > tsee:
        title_slam(ctx, t, tsee, "SEE YOU IN EPISODE 2!", 1420, 690, 56, YELLOW, -0.02)


# ======================= photo-based replacements (no drawn hands) =======================
def _card(ctx, t, name, t_in, cx, cy, w, h, tag="REAL LIFE", focus=(.5, .5), zd=6.0, rot=0.0):
    f = PH + name
    z = kb(t, t_in, zd, 1.0, 1.05)
    sc = card_in(t, t_in)
    photo_card(ctx, f, cx, cy, w, h, rot=rot, scale=sc, zoom=z, focus=focus, tag=tag, t=t)
    return (lambda x, y: img_to_card(x, y, f, cx, cy, w, h, z, focus)), sc

def sc_tight(ctx, t, e):  # 17.68-25.96
    t_tight = wt("tight.", 17)
    m, sc = _card(ctx, t, 'r1_deathgrip.jpg', 17.68, 560, 470, 780, 585, focus=(.5, .58))
    if sc > .9 and t > t_tight - .4:
        X, Y = m(1000, 1080); ring(ctx, X, Y, 190 * pop(t, t_tight - .4) * .7, t)
        ctx.save(); ctx.translate(330, 230); ctx.rotate(-0.08)
        sp = pop(t, t_tight - 0.3); burst(ctx, 0, 0, 160 * sp, RED, NAVY, 14, t)
        text(ctx, "TOO TIGHT!", 0, 0, 52, WHITE, NAVY, scale=sp); ctx.restore()
    t1 = wt("sound,", 20); t2 = wt("speed,", 20); t3 = wt("wrists.", 20)
    for i, (tt, name) in enumerate([(t1, "SOUND"), (t2, "SPEED"), (t3, "WRISTS")]):
        p = pop(t, tt)
        if p <= 0: continue
        x, y = 1180 + i * 250, 470
        ctx.save(); ctx.translate(x, y); sscale(ctx, p, p)
        panel(ctx, 0, 0, 210, 250, WHITE)
        if i == 0:
            rrect(ctx, -60, -60, 40, 50, 6); fill_stroke(ctx, PURPLE, NAVY, 5)
            ctx.new_path(); ctx.move_to(-20, -60); ctx.line_to(20, -95); ctx.line_to(20, 25); ctx.line_to(-20, -10); ctx.close_path(); fill_stroke(ctx, PURPLE, NAVY, 5)
            for k in range(2):
                ctx.new_path(); ctx.arc(30, -35, 25 + k * 20, -0.7, 0.7); ctx.set_source_rgb(*NAVY); ctx.set_line_width(5); ctx.stroke()
        elif i == 1:
            ctx.new_path(); ctx.arc(0, -10, 70, math.pi, 2 * math.pi); ctx.close_path(); fill_stroke(ctx, YELLOW, NAVY, 5)
            na = math.pi + 0.4 + 0.3 * math.sin(t * 9)
            line(ctx, 0, -10, 60 * math.cos(na), -10 + 60 * math.sin(na), RED, 7)
        else:
            # bandage icon
            ctx.save(); ctx.rotate(-0.6); rrect(ctx, -80, -26, 160, 52, 26); fill_stroke(ctx, (1, .85, .7), NAVY, 5)
            rrect(ctx, -28, -26, 56, 52, 6); fill_stroke(ctx, (1, .93, .85), NAVY, 4)
            for dx in (-12, 0, 12):
                for dy in (-10, 6): circle(ctx, dx, dy, 3, (.85, .6, .45), None)
            ctx.restore()
        text(ctx, name, 0, 80, 38, NAVY, None, shadow=False)
        ctx.restore()
        cross(ctx, x + 80, y - 110, 0.55, p=prog(t, tt + 0.25, 0.4))

def sc_fulcrum(ctx, t, e):  # 75.84-93.6
    tbal = wt("balance", 75.8); tfu = wt("fulcrum.", 77); tl = wt("light", 80)
    ts = wt("slide", 84); tf = wt("third", 89)
    caption_sticker(ctx, t, tbal, "BALANCE POINT", 960, 150, 52, YELLOW, NAVY, -0.03)
    if t < tf - 0.3:
        m, sc = _card(ctx, t, 'r5_fulcrum.jpg', 75.9, 820, 520, 820, 560, focus=(.55, .55), zd=13)
        if sc > .9:
            X, Y = m(1118, 898); ring(ctx, X, Y, 80 * pop(t, 76.6), t)
            if t > ts:
                label(ctx, "SLIDE UNTIL IT BALANCES", X, Y + 150, 34, PINK, WHITE, scale=pop(t, ts), rot=.03)
        fp = pop(t, tfu)
        if fp > 0:
            ctx.save(); ctx.translate(1560, 330); sscale(ctx, fp, fp); ctx.rotate(0.08 + wob(t, .5, .03))
            burst(ctx, 0, 0, 200, PINK, NAVY, 22, t * .3); text(ctx, "FULCRUM", 0, -5, 56, WHITE, NAVY); ctx.restore()
        if tl < t < ts:
            for i in range(3):
                ph = (t * 1.5 + i / 3) % 1
                text(ctx, "boing!", 1520 + 40 * i, 700 - 200 * ph, 44, YELLOW, NAVY, alpha=1 - ph, rot=-0.2)
    else:
        # simple diagram (no hands): stick on a little seesaw, thirds marked
        L = 1000; bal = 1 / 3; p = pop(t, tf - 0.3)
        ctx.save(); ctx.translate(960, 470); sscale(ctx, p, p)
        ctx.new_path(); ctx.move_to(0, 18); ctx.line_to(-70, 150); ctx.line_to(70, 150); ctx.close_path(); fill_stroke(ctx, ORANGE, NAVY, 6)
        ctx.save(); ctx.rotate(0.03 * math.sin(t * 3))
        stick(ctx, -L * bal, 0, 0, L, 40, face="smile", t=t)
        rp = smooth(prog(t, tf, .5))
        for k in range(4):
            xx = -L * bal + L * k / 3; line(ctx, xx, -40, xx, -80, WHITE, 6, rp)
        line(ctx, -L * bal, -60, -L * bal + L, -60, WHITE, 4, rp, dash=[12, 10])
        label(ctx, "1/3 FROM THE BUTT END", -L * bal + L / 6, -130, 40, PINK, WHITE, scale=pop(t, tf + .2))
        ctx.restore(); ctx.restore()

def sc_check(ctx, t, e):  # 108.32-118.16
    t0 = 108.32
    title_slam(ctx, t, t0, "QUICK CHECK!", 960, 150, 96, YELLOW, -0.03)
    tstuck = wt("stuck,", 113); tloose = wt("loosen", 116)
    stuck = smooth(prog(t, tstuck, .3)) * (1 - smooth(prog(t, tloose, .5)))
    f = 'r1_deathgrip.jpg' if 0.5 < stuck else 'p7_pinch.jpg'
    tag = "REAL LIFE" if f.startswith('r1') else "CLOSE-UP"
    m, sc = _card(ctx, t, f, t0 + .2, 620, 500, 820, 560, tag=tag, focus=(.4, .5) if f.startswith('p7') else (.5, .58))
    if sc > .9 and stuck < .5:
        # wiggle arrows around the stick
        a = wob(t, 1.4, .25)
        for sgn in (-1, 1):
            ctx.save(); ctx.translate(620 + sgn * 300, 330); ctx.rotate(a * sgn)
            ctx.new_path(); ctx.arc(0, 0, 60, -2.4, -0.7); ctx.set_source_rgba(*YELLOW, 1); ctx.set_line_width(12); ctx.stroke()
            ctx.restore()
        if t > wt("great.", 111): check(ctx, 960, 290, 0.6, p=prog(t, wt("great.", 111), .4))
    mp = pop(t, tstuck - 0.2)
    if mp > 0:
        ctx.save(); ctx.translate(1480, 520); sscale(ctx, mp * .85, mp * .85)
        panel(ctx, 0, -20, 500, 360, WHITE)
        for k, col in enumerate([GREEN, YELLOW, RED]):
            a0 = math.pi + k * math.pi / 3
            ctx.new_path(); ctx.arc(0, 60, 180, a0, a0 + math.pi / 3); ctx.arc_negative(0, 60, 110, a0 + math.pi / 3, a0); ctx.close_path()
            fill_stroke(ctx, col, NAVY, 5)
        v = lerp(0.15, 0.92, stuck) + 0.03 * math.sin(t * 15) * stuck
        na = math.pi + v * math.pi
        line(ctx, 0, 60, 150 * math.cos(na), 60 + 150 * math.sin(na), NAVY, 10); circle(ctx, 0, 60, 18, NAVY, None)
        text(ctx, "SQUEEZE-O-METER", 0, -150, 40, NAVY, None, shadow=False)
        ctx.restore()
        if t > tloose: caption_sticker(ctx, t, tloose, "LOOSEN UP!", 1480, 790, 48, GREEN, WHITE, 0.04)

def nest(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    ellipse(ctx, 0, 0, 230, 80, (0.62, 0.42, 0.22), NAVY, LW)
    ellipse(ctx, 0, -20, 180, 45, (0.45, 0.28, 0.14), None)
    for i in range(14):
        a = i * 0.45
        ctx.new_path(); ctx.arc(-150 + i * 22, 10 + 8 * math.sin(i), 40, a, a + 1.6)
        ctx.set_source_rgba(0.80, 0.60, 0.35, 1); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()

def sc_bird(ctx, t, e):  # 118.16-141.12
    t0 = 118.16
    tbird = wt("bird.", 128); tclamp = wt("clamp", 135); tpoke = wt("poke", 137)
    if t < tbird - 0.8 or t >= tclamp - 0.3:
        tin = t0 if t < tbird else tclamp - 0.3
        f = 'p1_sidegrip.jpg'; cx, cy, w, h = 820, 470, 1060, 590
        m, sc = _card(ctx, t, f, tin, cx, cy, w, h, zd=8)
        if sc > .9:
            hx, hy = m(1300, 600); ring(ctx, hx, hy, 140 * pop(t, tin + .4), t)
        if t < tbird:
            caption_sticker(ctx, t, t0 + .2, "CURL YOUR FINGERS", 960, 140, 46, YELLOW, NAVY, 0.03)
            for i, (nm, tw) in enumerate([("MIDDLE", wt("middle,", 120)), ("RING", wt("ring,", 120)), ("PINKY", wt("pinky", 120))]):
                label(ctx, nm, 1560, 330 + i * 110, 40, [PINK, TEAL, PURPLE][i], WHITE, scale=pop(t, tw))
            caption_sticker(ctx, t, wt("loosely.", 124), "LOOSELY!", 1560, 700, 44, GREEN, WHITE, -0.04)
        elif t < tpoke:
            caption_sticker(ctx, t, tclamp - 0.3, "TOUCH, DON'T CLAMP", 960, 140, 46, YELLOW, NAVY, 0.03)
        else:
            bx, by = m(1465, 735)
            arrow(ctx, bx + 230, by + 150, bx + 25, by + 20, PINK, s=ease_out(prog(t, tpoke + .3, .4)))
            label(ctx, "END POKES OUT!", 1560, 800, 40, PINK, WHITE, rot=.05, scale=pop(t, tpoke + .5))
            caption_sticker(ctx, t, tpoke, "FINGERS WRAPPED LOOSELY", 960, 140, 44, YELLOW, NAVY, -0.02)
    else:
        p = pop(t, tbird - 0.8)
        tfly = wt("fly", 129); thurt = wt("hurt", 131)
        flap = 1.0 if tfly <= t < tfly + 1.5 else 0.2
        nest(ctx, 960, 600, p)
        bird(ctx, 960, 520 + wob(t, 2, 6) - (40 if flap > .5 else 0) * abs(math.sin(t * 6)), 1.5 * p, t, flap)
        for i in range(3):
            ph = (t * 0.8 + i / 3) % 1
            hx = 960 + 160 * (i - 1); hy = 330 - 180 * ph
            ctx.save(); ctx.translate(hx, hy); sscale(ctx, 1 - ph * .3, 1 - ph * .3)
            ctx.new_path(); ctx.move_to(0, 18); ctx.curve_to(-40, -10, -20, -40, 0, -20); ctx.curve_to(20, -40, 40, -10, 0, 18)
            fill_stroke(ctx, PINK, NAVY, 4, alpha=1 - ph); ctx.restore()
        caption_sticker(ctx, t, tbird - 0.6, "HOLD IT LIKE A SMALL BIRD", 960, 150, 50, YELLOW, NAVY, -0.03)
        if t > tfly: caption_sticker(ctx, t, tfly, "FIRM ENOUGH...", 470, 470, 44, TEAL, WHITE, -0.08)
        if t > thurt: caption_sticker(ctx, t, thurt, "...SOFT ENOUGH!", 1450, 470, 44, PINK, WHITE, 0.08)

def sc_bounce(ctx, t, e):  # 163.76-198.27
    t0 = 163.76
    tdrop = wt("drop.", 166); treb = wt("rebound,", 179); tthud = wt("thuds", 184)
    trelax = wt("relax", 188); ttaps = wt("slow", 190)
    title_slam(ctx, t, t0, "THE BOUNCE TEST!", 960, 140, 84, YELLOW, -0.03)
    f = 'p6_pad.jpg'; cx, cy, w, h = 820, 520, 880, 580
    m, sc = _card(ctx, t, f, t0 + .2, cx, cy, w, h, tag="CLOSE-UP", zd=30)
    X, Y = m(560, 440)
    tight = tthud - 0.3 <= t < trelax
    bouncing = (tdrop <= t < tthud - 0.3) or (t >= trelax + 1.0)
    if sc > .9:
        if bouncing:
            per = 1.2 if t < ttaps else 1.0
            beat = ((t - tdrop) % per) / per
            for i in range(3):
                ph = (t * 1.3 + i / 3) % 1
                ctx.new_path(); ctx.arc(X, Y - 10, 40 + 110 * ph, math.pi * 1.05, math.pi * 1.95); ctx.set_source_rgba(1, 1, 1, 1 - ph); ctx.set_line_width(8); ctx.stroke()
            if beat < .25:
                burst(ctx, X - 70, Y + 40, 34 * (1 - beat * 4), YELLOW, None, 10, t)
                burst(ctx, X + 40, Y + 60, 26 * (1 - beat * 4), YELLOW, None, 10, -t)
            label(ctx, "BOING!", X + 40, Y - 190, 52, YELLOW, NAVY, rot=-.1, scale=1 + .12 * max(0, 1 - beat * 4))
        elif tight:
            text(ctx, "THUD.", X + 60, Y - 170, 70, (0.75, 0.8, 0.9), NAVY, rot=0.08, scale=pop(t, tthud - .3))
            for k in range(3):
                line(ctx, X - 80 + k * 80, Y + 70, X - 80 + k * 80, Y + 100, NAVY, 6, .7)
        else:
            # before the drop: stick held up, arrow showing the drop
            arrow(ctx, X + 10, Y - 260, X + 10, Y - 60, WHITE, s=.5 + .5 * abs(math.sin(t * 2)))
    side = 1560
    if t < tdrop + .5:
        caption_sticker(ctx, t, wt("inches", 166), "A FEW INCHES UP", side, 330, 40, WHITE, NAVY, 0.04)
        caption_sticker(ctx, t, tdrop - .2, "LET IT DROP!", side, 470, 44, YELLOW, NAVY, -0.03)
    elif t < treb - .3:
        caption_sticker(ctx, t, wt("push", 168), "DON'T PUSH", side, 330, 44, RED, WHITE, 0.04)
        caption_sticker(ctx, t, wt("gravity", 172), "LET GRAVITY WORK", side, 470, 40, GREEN, WHITE, -0.03)
    elif t < tthud - .3:
        ctx.save(); ctx.translate(side, 330); ctx.rotate(-.06); rp = pop(t, treb)
        sscale(ctx, rp, rp); burst(ctx, 0, 0, 180, PINK, NAVY, 16, t * .5); text(ctx, "REBOUND!", 0, 0, 52, WHITE, NAVY); ctx.restore()
        caption_sticker(ctx, t, wt("easy.", 182), "DRUMMING = EASY!", side, 600, 40, GREEN, WHITE, -0.04)
    elif t < trelax:
        ctx.save(); ctx.translate(side, 330); ctx.rotate(0.08); sp = pop(t, wt("tight.", 186))
        burst(ctx, 0, 0, 160 * sp, RED, NAVY, 14); text(ctx, "TOO TIGHT!", 0, 0, 48, WHITE, NAVY, scale=sp); ctx.restore()
    else:
        caption_sticker(ctx, t, trelax, "RELAX & TRY AGAIN", side, 330, 40, GREEN, WHITE, 0.04)
        if t > ttaps:
            caption_sticker(ctx, t, ttaps, "SLOW TAPS", side, 470, 44, YELLOW, NAVY, -0.03)
            n = int((t - ttaps) / 1.0) + 1
            label(ctx, f"TAP x{n}", side, 600, 44, PINK, WHITE, scale=1 + 0.15 * max(0, 1 - ((t - ttaps) % 1.0) / .3))

def sc_mistakes(ctx, t, e):  # 198.27-243.95
    t0 = 198.27
    marks = [wt("one.", 201), wt("two.", 209), wt("three.", 217), wt("four.", 228), wt("five.", 235)]
    if t < marks[0] - 0.2:
        title_slam(ctx, t, t0 + .1, "5 BEGINNER", 960, 300, 120, WHITE, -0.03)
        title_slam(ctx, t, t0 + .6, "MISTAKES!", 960, 450, 140, RED, 0.02)
        for i in range(5):
            pp = pop(t, wt("five", 198) + i * 0.15)
            label(ctx, f"#{i + 1}", 560 + i * 200, 650, 56, [PINK, ORANGE, TEAL, PURPLE, GREEN][i], WHITE, scale=pp, rot=wob(t, .6, .06, i))
        return
    k = max(i for i in range(5) if t >= marks[i] - 0.2)
    tm = marks[k]
    names = ["DEATH GRIP", "THUMB ON TOP", "HOLDING THE END", "FINGERS OUT", "TENSE SHOULDERS"]
    fixes = ["HOLD IT LIKE A BIRD", "THUMB ON THE SIDE", "BALANCE POINT", "CURL THEM IN", "BREATHE & SHAKE"]
    fix_words = [("fix", tm), ("keep", tm), ("go", tm), ("keep", tm), ("take", tm)]
    tfix = wt(*fix_words[k])
    colk = [PINK, ORANGE, TEAL, PURPLE, GREEN][k]
    bp = pop(t, tm - 0.2)
    ctx.save(); ctx.translate(150, 190); ctx.rotate(-0.12); sscale(ctx, bp * .8, bp * .8)
    star(ctx, 0, 0, 130, colk, NAVY, 7, rot=t * 0.3); text(ctx, f"#{k + 1}", 0, 0, 92, WHITE, NAVY); ctx.restore()
    label(ctx, names[k], 960, 140, 60, RED, WHITE, scale=pop(t, tm), rot=wob(t, .6, .02))
    fixed = t >= tfix
    if k < 4:
        bad = ['r1_deathgrip.jpg', 'r2_thumbtop_v2.jpg', 'r3_end_v2.jpg', 'r4_fingersout.jpg'][k]
        rings = [[(1000, 1080, 190)], [(525, 1015, 110), (975, 1035, 110)], [(385, 1215, 150), (930, 1250, 150)], [(700, 1150, 170)]][k]
        portrait = (k >= 1)
        if not fixed:
            w, h = (480, 600) if portrait else (900, 560)
            m, sc = _card(ctx, t, bad, tm - 0.2, 760, 500, w, h, focus=(.5, .55))
            if sc > .9:
                for (rx, ry, rr) in rings:
                    X, Y = m(rx, ry); ring(ctx, X, Y, rr * pop(t, tm + .4) * .6, t)
            cross(ctx, 1500, 470, 1.2, p=prog(t, tm + 0.6, .4))
        else:
            w, h = (360, 450) if portrait else (620, 390)
            fp = smooth(prog(t, tfix, .5))
            photo_card(ctx, PH + bad, lerp(760, 470, fp), 500, w, h, rot=-.04, scale=1.0, tag="", t=t, focus=(.5, .55))
            cross(ctx, lerp(760, 470, fp) + w / 2 - 20, 500 - h / 2 + 20, 0.6)
            good = ['p1_sidegrip.jpg', 'p7_pinch.jpg', 'p7_pinch.jpg', 'p1_sidegrip.jpg'][k]
            gtag = "CLOSE-UP" if good.startswith('p7') else "REAL LIFE"
            m2, sc2 = _card(ctx, t, good, tfix, 1350, 480, 700, 430, tag=gtag, rot=.03)
            check(ctx, 1350 + 330, 480 - 200, 0.75, p=prog(t, tfix + .2, .4))
            label(ctx, fixes[k], 1350, 760, 44, GREEN, WHITE, scale=pop(t, tfix + .1), rot=0.02)
            confetti(ctx, 1350, 480, t - tfix, seed=20 + k, n=30, spread=380, dur=1.5)
    else:
        fp = smooth(prog(t, tfix, .5))
        ctx.save(); ctx.translate(960, 470)
        kid(ctx, -200, 140, t, straight=1, shoulders=1 - fp, shake=fp if fixed and t < tfix + 3 else 0, arms_up=0.3)
        if not fixed:
            for i in range(2):
                ctx.save(); ctx.translate(-180 + 160 * i, -260); ctx.rotate(0.3 * (i - .5))
                ctx.new_path(); ctx.move_to(0, -40); ctx.line_to(-18, 0); ctx.line_to(4, 0); ctx.line_to(-10, 40); ctx.line_to(22, -8); ctx.line_to(2, -8); ctx.line_to(14, -40); ctx.close_path()
                fill_stroke(ctx, YELLOW, NAVY, 4); ctx.restore()
        else:
            for i in range(3):
                ph = (t * 0.7 + i / 3) % 1
                ctx.new_path(); ctx.arc(-120, -360, 60 + 120 * ph, -2.3, -0.8); ctx.set_source_rgba(1, 1, 1, 1 - ph); ctx.set_line_width(6); ctx.stroke()
        ctx.restore()
        if not fixed: cross(ctx, 1500, 470, 1.2, p=prog(t, tm + 0.6, .4))
        else:
            check(ctx, 1500, 470, 1.2, p=prog(t, tfix, .4))
            label(ctx, fixes[k], 1500, 650, 44, GREEN, WHITE, scale=pop(t, tfix + .1), rot=0.03)
            confetti(ctx, 1500, 470, t - tfix, seed=24, n=30, spread=380, dur=1.5)


# ======================= real video clips from the user's drum video =======================
def _vcard(ctx, t, name, t_in, cx, cy, w, h, tag="REAL LIFE", speed=1.0, mode="loop", rot=0.0, focus=(.5, .5), zoom=1.0):
    sc = card_in(t, t_in)
    video_card(ctx, name, t - t_in, cx, cy, w, h, rot=rot, scale=sc, zoom=zoom, focus=focus, tag=tag, t=t, speed=speed, mode=mode)
    return sc

_old_gear = sc_gear
def sc_gear(ctx, t, e):  # 33.52-41.28
    t5 = wt("5A", 36)
    if t < t5 - 0.3:
        _vcard(ctx, t, 'sticks', 33.6, 960, 470, 1040, 585)
        caption_sticker(ctx, t, 33.8, "ALL YOU NEED: STICKS!", 960, 140, 50, WHITE)
    else:
        _vcard(ctx, t, 'sticks', 33.6, 560, 470, 760, 428, speed=0.8)
        _old_gear_tag(ctx, t)

def _old_gear_tag(ctx, t):
    t5 = wt("5A", 36); tp = pop(t, t5)
    if tp > 0:
        ctx.save(); ctx.translate(1350, 420); ctx.rotate(0.12 + wob(t, .8, .05)); sscale(ctx, tp, tp)
        ctx.new_path(); ctx.move_to(-150, -90); ctx.line_to(120, -90); ctx.line_to(190, 0); ctx.line_to(120, 90); ctx.line_to(-150, 90); ctx.close_path()
        fill_stroke(ctx, YELLOW, NAVY, 8); circle(ctx, 125, 0, 16, WHITE, NAVY, 5)
        text(ctx, "SIZE", -20, -40, 40, NAVY, None, shadow=False); text(ctx, "5A", -20, 30, 110, PINK, NAVY)
        ctx.restore()
        star(ctx, 1560, 250, 50 * pop(t, wt("common", 36)), YELLOW, NAVY, 6, rot=t)
        caption_sticker(ctx, t, wt("common", 36), "#1 FOR BEGINNERS", 1350, 640, 40, PINK, WHITE, 0.03)

_old_fulcrum = sc_fulcrum
def sc_fulcrum(ctx, t, e):  # 75.84-93.6
    tbal = wt("balance", 75.8); tfu = wt("fulcrum.", 77); tl = wt("light", 80); ts = wt("slide", 84); tf = wt("third", 89)
    if t >= tf - 0.3: return _old_fulcrum(ctx, t, e)
    caption_sticker(ctx, t, tbal, "BALANCE POINT", 960, 150, 52, YELLOW, NAVY, -0.03)
    _vcard(ctx, t, 'fulcrum', 75.9, 820, 520, 860, 484, mode="pingpong")
    if t > ts: label(ctx, "SLIDE UNTIL IT BALANCES", 820, 800, 36, PINK, WHITE, scale=pop(t, ts), rot=.02)
    fp = pop(t, tfu)
    if fp > 0:
        ctx.save(); ctx.translate(1560, 330); sscale(ctx, fp, fp); ctx.rotate(0.08 + wob(t, .5, .03))
        burst(ctx, 0, 0, 200, PINK, NAVY, 22, t * .3); text(ctx, "FULCRUM", 0, -5, 56, WHITE, NAVY); ctx.restore()
    if tl < t < ts:
        for i in range(3):
            ph = (t * 1.5 + i / 3) % 1
            text(ctx, "boing!", 1520 + 40 * i, 700 - 200 * ph, 44, YELLOW, NAVY, alpha=1 - ph, rot=-0.2)

_old_pinch = sc_pinch
def sc_pinch(ctx, t, e):  # 93.6-108.32
    t0 = 93.6; tpen = wt("pencil,", 98); tpiv = wt("pivot.", 103)
    if t < tpen - 0.3:
        _vcard(ctx, t, 'pinch', t0, 820, 480, 960, 540, mode="pingpong")
        caption_sticker(ctx, t, t0 + .2, "PINCH IT HERE", 1600, 240, 44, PINK, WHITE, 0.05)
        label(ctx, "THUMB", 1600, 420, 42, YELLOW, NAVY, scale=pop(t, wt("thumb", 94)), rot=-.03)
        label(ctx, "+ SIDE OF 1ST FINGER", 1600, 530, 34, TEAL, WHITE, scale=pop(t, wt("first", 94)), rot=.02)
    elif t < tpiv - 0.2:
        return _old_pinch(ctx, t, e)
    else:
        _vcard(ctx, t, 'pivot', tpiv - 0.2, 820, 500, 960, 540)
        title_slam(ctx, t, tpiv, "PIVOT!", 1600, 300, 96, YELLOW, -0.04)
        caption_sticker(ctx, t, wt("seesaw.", 105), "LIKE A SEESAW", 1600, 520, 42, WHITE, NAVY, .03)

_old_check = sc_check
def sc_check(ctx, t, e):  # 108.32-118.16  (video plays the whole time, no photo swaps)
    t0 = 108.32; tstuck = wt("stuck,", 113); tloose = wt("loosen", 116)
    title_slam(ctx, t, t0, "QUICK CHECK!", 960, 150, 96, YELLOW, -0.03)
    _vcard(ctx, t, 'pivot', t0 + .2, 760, 520, 900, 506)
    if t < tstuck - 0.2:
        caption_sticker(ctx, t, t0 + .6, "WIGGLE IT!", 1580, 380, 50, PINK, WHITE, .05)
        if t > wt("great.", 111): check(ctx, 1580, 580, 0.9, p=prog(t, wt("great.", 111), .4))
        return
    stuck = smooth(prog(t, tstuck, .3)) * (1 - smooth(prog(t, tloose, .5)))
    mp = pop(t, tstuck - 0.2)
    ctx.save(); ctx.translate(1530, 500); sscale(ctx, mp * .8, mp * .8)
    panel(ctx, 0, -20, 500, 360, WHITE)
    for k, col in enumerate([GREEN, YELLOW, RED]):
        a0 = math.pi + k * math.pi / 3
        ctx.new_path(); ctx.arc(0, 60, 180, a0, a0 + math.pi / 3); ctx.arc_negative(0, 60, 110, a0 + math.pi / 3, a0); ctx.close_path()
        fill_stroke(ctx, col, NAVY, 5)
    v = lerp(0.15, 0.92, stuck) + 0.03 * math.sin(t * 15) * stuck
    na = math.pi + v * math.pi
    line(ctx, 0, 60, 150 * math.cos(na), 60 + 150 * math.sin(na), NAVY, 10); circle(ctx, 0, 60, 18, NAVY, None)
    text(ctx, "SQUEEZE-O-METER", 0, -150, 40, NAVY, None, shadow=False)
    ctx.restore()
    if t < tloose:
        caption_sticker(ctx, t, tstuck, "TOO HARD!", 1530, 760, 46, RED, WHITE, -0.04)
    else:
        caption_sticker(ctx, t, tloose, "LOOSEN UP!", 1530, 760, 48, GREEN, WHITE, 0.04)

_old_bird = sc_bird
def sc_bird(ctx, t, e):  # 118.16-141.12
    t0 = 118.16; tbird = wt("bird.", 128)
    if t >= tbird - 0.8: return _old_bird(ctx, t, e)
    _vcard(ctx, t, 'curl', t0, 800, 490, 980, 551)
    caption_sticker(ctx, t, t0 + .2, "CURL YOUR FINGERS", 960, 140, 46, YELLOW, NAVY, 0.03)
    for i, (nm, tw) in enumerate([("MIDDLE", wt("middle,", 120)), ("RING", wt("ring,", 120)), ("PINKY", wt("pinky", 120))]):
        label(ctx, nm, 1600, 330 + i * 110, 40, [PINK, TEAL, PURPLE][i], WHITE, scale=pop(t, tw))
    caption_sticker(ctx, t, wt("loosely.", 124), "LOOSELY!", 1600, 700, 44, GREEN, WHITE, -0.04)

_old_matched = sc_matched
def sc_matched(ctx, t, e):  # 141.12-163.76
    tmatch = wt("matched", 154); tsame = wt("same", 155); tgreat = wt("great", 160)
    if t < tmatch: return _old_matched(ctx, t, e)
    f = PH + 'p5_vgrip.png'; fo = (.5, .42); z = kb(t, 141.12, tgreat + 3 - 141.12, 1.0, 1.05)
    photo_card(ctx, f, 900, 450, 980, 700, scale=1.0, zoom=z, focus=fo, tag="CLOSE-UP", t=t)
    m = lambda x, y: img_to_card(x, y, f, 900, 450, 980, 700, z, fo)
    for (x, y) in [(487, 672), (783, 676)]:
        X, Y = m(x, y); ring(ctx, X, Y, 62, t)
    mp = pop(t, tmatch)
    ctx.save(); ctx.translate(1620, 300); sscale(ctx, mp, mp); ctx.rotate(-.04 + wob(t, .5, .02))
    panel(ctx, 0, 0, 440, 96, YELLOW, r=48); text(ctx, "MATCHED GRIP", 0, 0, 50, PINK, NAVY); ctx.restore()
    if t > tsame: label(ctx, "BOTH HANDS THE SAME", 1590, 450, 34, GREEN, WHITE, rot=.03, scale=pop(t, tsame))
    if t > tgreat:
        label(ctx, "GREAT PLACE TO START!", 1590, 600, 36, PINK, WHITE, rot=-.03, scale=pop(t, tgreat))
        for i in range(4): star(ctx, 1590 + 200 * math.cos(i * 1.6 + t), 450 + 150 * math.sin(i * 1.6 + t), 26 * pop(t, tgreat + .2), YELLOW, NAVY, 4)

_old_bounce = sc_bounce
def sc_bounce(ctx, t, e):  # 163.76-198.27
    tdrop = wt("drop.", 166); tthud = wt("thuds", 184); trelax = wt("relax", 188); ttaps = wt("slow", 190)
    if t < tdrop - 0.2: return _old_bounce(ctx, t, e)
    t0 = 163.76; treb = wt("rebound,", 179)
    title_slam(ctx, t, t0, "THE BOUNCE TEST!", 960, 140, 84, YELLOW, -0.03)
    if t < tthud - 0.3: _vcard(ctx, t, 'rebound', tdrop - 0.2, 800, 520, 900, 506)
    elif t < trelax: _vcard(ctx, t, 'deadstroke', tthud - 0.3, 800, 520, 900, 506)
    elif t < ttaps - 0.3: _vcard(ctx, t, 'tap1', trelax, 800, 520, 900, 506)
    else: _vcard(ctx, t, 'slowtaps', ttaps - 0.3, 800, 520, 900, 506)
    side = 1580
    if t < treb - .3:
        caption_sticker(ctx, t, wt("push", 168), "DON'T PUSH", side, 330, 44, RED, WHITE, 0.04)
        caption_sticker(ctx, t, wt("gravity", 172), "LET GRAVITY WORK", side, 470, 40, GREEN, WHITE, -0.03)
    elif t < tthud - 0.3:
        ctx.save(); ctx.translate(side, 330); ctx.rotate(-.06); rp = pop(t, treb)
        sscale(ctx, rp, rp); burst(ctx, 0, 0, 180, PINK, NAVY, 16, t * .5); text(ctx, "REBOUND!", 0, 0, 52, WHITE, NAVY); ctx.restore()
        caption_sticker(ctx, t, wt("easy.", 182), "DRUMMING = EASY!", side, 600, 40, GREEN, WHITE, -0.04)
    elif t < trelax:
        ctx.save(); ctx.translate(side, 330); ctx.rotate(0.08); sp = pop(t, tthud - 0.3)
        burst(ctx, 0, 0, 150 * sp, (0.6, 0.65, 0.75), NAVY, 14); text(ctx, "THUD.", 0, 0, 52, WHITE, NAVY, scale=sp); ctx.restore()
        caption_sticker(ctx, t, wt("tight.", 186), "TOO TIGHT!", side, 520, 46, RED, WHITE, -0.04)
    else:
        caption_sticker(ctx, t, trelax, "RELAX & TRY AGAIN", side, 330, 40, GREEN, WHITE, 0.04)
        if t > ttaps:
            caption_sticker(ctx, t, ttaps, "SLOW TAPS", side, 470, 44, YELLOW, NAVY, -0.03)

_old_tip1 = sc_tip1
def sc_tip1(ctx, t, e):  # 254.04-267.56
    tl = wt("loose,", 264)
    if t < tl - 0.3: return _old_tip1(ctx, t, e)
    label(ctx, "TIP 1: DAILY PRACTICE", 960, 145, 56, PINK, WHITE)
    _vcard(ctx, t, 'altern', tl - 0.3, 960, 480, 960, 540)
    caption_sticker(ctx, t, tl, "STAY LOOSE & LISTEN FOR THE BOUNCE", 960, 800, 40, GREEN, WHITE, 0.0)

SCENES = [
    (0.0, 6.32, sc_hook), (6.32, 9.16, sc_never), (9.16, 15.6, sc_steps), (15.6, 17.68, sc_secret),
    (17.68, 25.96, sc_tight), (25.96, 28.24, sc_fix), (28.24, 33.52, sc_stickaround),
    (33.52, 41.28, sc_gear), (41.28, 44.24, sc_goldilocks), (44.24, 51.84, sc_padpillow),
    (51.84, 58.67, sc_posture), (58.67, 75.84, sc_parts), (75.84, 93.6, sc_fulcrum),
    (93.6, 108.32, sc_pinch), (108.32, 118.16, sc_check), (118.16, 141.12, sc_bird),
    (141.12, 163.76, sc_matched), (163.76, 198.27, sc_bounce), (198.27, 243.95, sc_mistakes),
    (243.95, 254.04, sc_bonus), (254.04, 267.56, sc_tip1), (267.56, 276.85, sc_tip2),
    (276.85, 999, sc_outro),
]

TINTS = {sc_secret: PURPLE, sc_tight: RED, sc_mistakes: RED, sc_bonus: PURPLE, sc_outro: PINK}

def frame(ctx, t):
    sc = None
    for (s, e_, fn) in SCENES:
        if s <= t < e_: sc = (s, e_, fn)
    s, e_, fn = sc
    background(ctx, t, TINTS.get(fn))
    sh = shake_amt(t)
    ctx.save()
    if sh: ctx.translate(wob(t, 23, sh), wob(t, 19, sh, 1.3))
    # scene exit (shrink) in last 0.18s, entry handled by pops
    out = smooth(prog(t, e_ - 0.18, 0.18)) if e_ < 900 else 0
    if out > 0:
        ctx.translate(CX, CY); sscale(ctx, 1 - out, 1 - out); ctx.translate(-CX, -CY)
    fn(ctx, t, env_at(t))
    ctx.restore()
    # wipe flash at scene boundaries
    since = t - s
    if 0 < s and since < 0.2:
        ctx.set_source_rgba(1, 1, 1, 0.35 * (1 - since / 0.2)); ctx.paint()
    hud(ctx, t)
    if fn is not sc_hook:
        narrator(ctx, t, alpha=1.0)
    captions(ctx, t)

# caption-timeline <-> true-audio-timeline warp (fixes the drift in the supplied captions)
_ANC = json.load(open(os.path.join(HERE, "anchors_final.json")))
_AO = np.array([a for a, b in _ANC]); _AS = np.array([b for a, b in _ANC])
def WARP(t):   # caption time -> true time in the original narration
    return float(np.interp(t, _AO, _AS, left=t + (_AS[0] - _AO[0]), right=t + (_AS[-1] - _AO[-1])))
def INV(t):    # true time -> caption time
    return float(np.interp(t, _AS, _AO, left=t - (_AS[0] - _AO[0]), right=t - (_AS[-1] - _AO[-1])))
# the user's own edit of the narration (FullVid_Vox_2_2.mp3): two "pun intended" removed
USER_CUTS = [(244.52, 244.52 + 0.946), (248.66, 248.66 + 0.964)]   # in original-narration time
def user_to_true(T):
    for a, b in USER_CUTS:
        if T >= a: T += b - a
    return T
def true_to_user(t):
    sh = 0.0
    for a, b in USER_CUTS:
        if t >= b: sh += b - a
        elif t > a: return a - sh
    return t - sh
def src_t(T):
    """frame time in the final (user-edited) audio -> scene/caption timeline."""
    return max(0.0, INV(user_to_true(T)))

def render_surface(t, scale):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale))
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo)
    sscale(ctx, scale, scale)
    frame(ctx, t)
    return surf

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        t = float(sys.argv[2]); sc = float(sys.argv[3]); out = sys.argv[4]
        render_surface(t, sc).write_to_png(out)
    elif mode == "range":
        f0, f1, sc, out = int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        w, h = int(W * sc), int(H * sc)
        crf = sys.argv[6] if len(sys.argv) > 6 else "18"
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", crf,
                              "-pix_fmt", "yuv420p", "-threads", "2", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            surf = render_surface(src_t(f / FPS), sc)
            p.stdin.write(surf.get_data())
            if f % 300 == 0: print(f"{out}: frame {f}", flush=True)
        p.stdin.close(); p.wait()
