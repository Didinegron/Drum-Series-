"""Episode 4 - How to read drum music. Fully animated; reuses the Episode 3 kit, sticks, beat chart, captions and HUD (ep3.py),
with Episode 4's own words/cues/envelope swapped into ep3's globals.
usage: python3 ep4.py still T scale out.png
       python3 ep4.py range F0 F1 scale out.mp4 [crf] [fps]
NOTE: words_final.json is a DRAFT (estimated from the script) until the narration exists; re-time then.
"""
import sys, os, math, json, subprocess, bisect
import numpy as np
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "episode-03"))
import ep3
from lib import *
from ep3 import (norm, sfx, clock, ep3_kit, beat_chart, kick, tom, hihat, cymbal, nameplate, lesson_card, block, flame, turtle,
                 GOLD, GOLD_D, CHROME, DARK, HH_C, SN_C, KK_C, PATTERN, captions, narrator, background, stand)

FPS = 30
WORDS = json.load(open(os.path.join(HERE, "words_final.json")))
CUES = json.load(open(os.path.join(HERE, "cues.json")))
ENV = np.load(os.path.join(HERE, "env.npy"))
TOTAL = WORDS[-1]["end"] + 0.6
ep3.WORDS, ep3.CUES, ep3.ENV, ep3.TOTAL = WORDS, CUES, ENV, TOTAL
ep3.T_LOOP0 = ep3.T_LOOP1 = 1e9           # no drum loop in this episode (captions never hidden)
wt = ep3.wt

def phrase(s, after=0.0):
    """start time of a multi-word phrase (robust to repeated single words)"""
    ps = [norm(x) for x in s.split()]; ws = [norm(w["text"]) for w in WORDS]
    for i in range(len(WORDS) - len(ps) + 1):
        if WORDS[i]["start"] >= after - 1e-6 and ws[i:i + len(ps)] == ps: return WORDS[i]["start"]
    raise KeyError(s)
T = {}
for n, s in [('recap', 'In the last video'), ('staff', 'Reading music is'), ('clef', 'At the very start'), ('map', "Now, here's the coolest"),
             ('notes', 'Each note has'), ('build', "Let's build our beat"), ('read', "Here's how drummers read"),
             ('play', "Now let's read it and play"), ('recap2', "Let's say the map"), ('bonus', 'You stuck around'),
             ('outro', 'Now you can read the staff')]:
    T[n] = phrase(s)
SECTIONS = [(0, "START"), (T['staff'], "STAFF"), (T['clef'], "CLEF"), (T['map'], "DRUM MAP"), (T['notes'], "NOTES"),
            (T['build'], "BUILD"), (T['read'], "READ"), (T['bonus'], "BONUS"), (T['outro'], "NEXT")]
ep3.SECTIONS = SECTIONS; ep3.GIFT_SHAKE = (T['bonus'] - 8, T['bonus'])

# ---------- spoken counting -> beat events (same idea as Episode 3) ----------
TOK = {"one", "two", "three", "four", "and", "boom", "crack"}
def layer_at(t):
    if t < T['staff']: return {'hihat', 'snare', 'kick'}
    if t < T['build']: return set()                  # counting only (bars section)
    if t < T['read']: return {'hihat'}               # layer 1 written on the staff
    return {'hihat', 'snare', 'kick'}
BARS, COUNTINS, EVENTS = [], [], []
i = 0
while i < len(WORDS):
    j = i
    while j < len(WORDS) and norm(WORDS[j]["text"]) in TOK: j += 1
    run = WORDS[i:j]; k = 0
    while k < len(run):
        toks = [norm(w["text"]) for w in run[k:k + 4]]
        if toks == ["one", "two", "three", "four"] and run[k]["start"] > T['play']:
            COUNTINS.append([w["start"] for w in run[k:k + 4]]); k += 4
        elif len(run) - k >= 8 and norm(run[k]["text"]) in ("one", "boom"):
            ws = run[k:k + 8]; lay = layer_at(ws[0]["start"])
            BARS.append(dict(t0=ws[0]["start"], t1=ws[-1]["end"], words=[(w["start"], c) for c, w in enumerate(ws)], layer=lay))
            for c, w in enumerate(ws): EVENTS.append((w["start"], c, {p for p in lay if c in PATTERN[p]}))
            k += 8
        else: k += 1
    i = max(j, i + 1)
EVENTS.sort(key=lambda e: e[0])
ep3.BARS, ep3.COUNTINS = BARS, COUNTINS
ep3.PIECE_T = {p: [e[0] for e in EVENTS if p in e[2]] for p in PATTERN}

def hud(ctx, t):
    a = smooth(prog(t, 5.0, .6))
    if a <= 0: return
    ctx.save(); ctx.translate(0, -80 * (1 - a))
    x0, x1, y = 470, 1450, 52
    label(ctx, "EPISODE 4", 320, y, 30, PINK, WHITE)
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
    gift(ctx, x1 + 70, y + 8, .28, t, 0, shake=1.0 if ep3.GIFT_SHAKE[0] < t < ep3.GIFT_SHAKE[1] else 0)
    ctx.restore()

# ---------- the big staff ----------
SP = 46                                   # space between staff lines
COLS = ["1", "&", "2", "&", "3", "&", "4", "&"]
def staff_y(cy, line_from_bottom):        # line_from_bottom: 0..4 = lines, 0.5 = 1st space, ...
    return cy + 2 * SP - line_from_bottom * SP
POS = {'kick': .5, 'snare': 2.5, 'hihat': 4.5}     # kick 1st space, snare 3rd space, hi-hat x above the top line

def draw_staff(ctx, cx, cy, s, t, lines=5.0, line_hl=None, space_hl=None, clef=1.0, timesig=1.0, bars=0.0, counts=0.0,
               notes=None, follow=True, col_hl=(), wrong=False, alpha=1.0, panel_=True, w=1500):
    """notes: dict piece -> appear time (or None = hidden). wrong=True puts the snare on 1 and 3 (bonus challenge)."""
    notes = notes or {}
    ctx.save(); ctx.translate(cx, cy); sscale(ctx, s, s)
    if panel_: panel(ctx, 0, 0, w + 80, 9 * SP + 170, WHITE, alpha)
    x0, x1 = -w / 2, w / 2; top = staff_y(0, 4)
    nx0 = x0 + 300; nstep = (x1 - 60 - nx0) / 8; xs = [nx0 + nstep * (k + .5) for k in range(8)]
    b = ep3.bar_at(t) if follow else None; cur = ep3.col_at(b, t) if b else -1
    for c in col_hl:
        rrect(ctx, xs[c] - nstep / 2 + 6, top - 2.6 * SP, nstep - 12, 7.4 * SP, 20); ctx.set_source_rgba(*PINK, .25 * alpha); ctx.fill()
    if cur >= 0:
        rrect(ctx, xs[cur] - nstep / 2 + 6, top - 2.6 * SP, nstep - 12, 7.4 * SP, 20); ctx.set_source_rgba(*YELLOW, .45 * alpha); ctx.fill()
    # lines (can draw in one by one: lines = 0..5)
    for k in range(5):
        a = clamp(lines - k) * alpha
        if a <= 0: continue
        y = staff_y(0, k); hl = line_hl is not None and k in line_hl
        line(ctx, x0, y, lerp(x0, x1, ease_out(clamp(lines - k))), y, PINK if hl else NAVY, 9 if hl else 4, a)
        if hl: text(ctx, str(k + 1), x0 - 40, y, 40, PINK, NAVY, alpha=a)
    if space_hl:
        for k in space_hl:
            y = staff_y(0, k + .5); rrect(ctx, x0 + 10, y - SP / 2 + 6, x1 - x0 - 20, SP - 12, 10); ctx.set_source_rgba(*TEAL, .35 * alpha); ctx.fill()
    if clef > 0:
        for dx in (-22, 0): rrect(ctx, x0 + 40 + dx, top + SP * .9, 12, SP * 2.2, 3); ctx.set_source_rgba(*NAVY, alpha * clef); ctx.fill()
    if timesig > 0:
        text(ctx, "4", x0 + 140, staff_y(0, 3), 92, NAVY, None, shadow=False, alpha=alpha * timesig)
        text(ctx, "4", x0 + 140, staff_y(0, 1), 92, NAVY, None, shadow=False, alpha=alpha * timesig)
    if bars > 0:
        for x in (x0 + 230, x1 - 20):
            line(ctx, x, top, x, staff_y(0, 0), NAVY, 6, alpha * bars)
    if counts > 0:
        for k, lab in enumerate(COLS):
            sc = 1.0
            if b and k == cur:
                tw_ = [x for x, cc in b["words"] if cc == k][0]; sc = 1 + .35 * max(0, 1 - (t - tw_) / .25)
            text(ctx, lab, xs[k], top - 3.7 * SP + (0 if lab != "&" else 4), 46 if lab != "&" else 38, NAVY if lab != "&" else (0.45, .5, .65), None,
                 shadow=False, alpha=alpha * counts, scale=sc)
    # notes
    def shown(p):
        t0 = notes.get(p); return None if t0 is None else pop(t, t0)
    yh, ysn, yk = staff_y(0, POS['hihat']), staff_y(0, POS['snare']), staff_y(0, POS['kick'])
    beam_y = top - 2.9 * SP + 18
    ph, ps, pk = shown('hihat'), shown('snare'), shown('kick')
    sn_cols = (0, 4) if wrong else (2, 6)
    lit = lambda p, k: b is not None and p in b["layer"] and k <= cur and k in PATTERN[p]
    for k, x in enumerate(xs):
        if ph:
            sc = ph; col = ORANGE if lit('hihat', k) else NAVY
            r = 14 * sc
            line(ctx, x - r, yh - r, x + r, yh + r, col, 6, alpha); line(ctx, x + r, yh - r, x - r, yh + r, col, 6, alpha)
            line(ctx, x + 15, yh, x + 15, beam_y, NAVY, 4, alpha * clamp(sc))
        if ps and k in sn_cols:
            ell_c = RED if (wrong or lit('snare', k)) else NAVY
            ctx.save(); ctx.translate(x, ysn); ctx.rotate(-.35); sscale(ctx, ps, ps); ellipse(ctx, 0, 0, 19, 13, ell_c, NAVY, 3, alpha); ctx.restore()
            if not ph: line(ctx, x + 15, ysn, x + 15, beam_y, NAVY, 4, alpha * clamp(ps))
            if wrong: circle(ctx, x, ysn, 36, None, RED, 6, alpha * .9) if False else None
        if pk and k in (0, 4):
            col = ORANGE if lit('kick', k) else NAVY
            ctx.save(); ctx.translate(x, yk); ctx.rotate(-.35); sscale(ctx, pk, pk); ellipse(ctx, 0, 0, 19, 13, col, NAVY, 3, alpha); ctx.restore()
            line(ctx, x - 15, yk, x - 15, yk + 3.2 * SP, NAVY, 4, alpha * clamp(pk))
    if ph:
        for k in range(0, 8, 2):
            rrect(ctx, xs[k] + 13, beam_y - 6, nstep + 4, 13, 3); ctx.set_source_rgba(*NAVY, alpha * clamp(ph)); ctx.fill()
    ctx.restore()
    return xs

def staff_to_screen(cx, cy, s, x, line_from_bottom):
    return cx + x * s, cy + staff_y(0, line_from_bottom) * s

def bird(ctx, x, y, s, t, ph=0.0):
    ctx.save(); ctx.translate(x, y + math.sin(t * 3 + ph) * 3); sscale(ctx, s, s)
    ellipse(ctx, 0, -18, 28, 22, SKY, NAVY, 4); circle(ctx, 20, -36, 14, SKY, NAVY, 4); circle(ctx, 24, -38, 3, NAVY, None)
    ctx.new_path(); ctx.move_to(32, -36); ctx.line_to(44, -32); ctx.line_to(32, -30); ctx.close_path(); fill_stroke(ctx, ORANGE, NAVY, 3)
    ctx.restore()

def big_note(ctx, x, y, s, kind, t, hl=None):
    """note anatomy: kind 'note' or 'x'; hl in {'head','stem'}"""
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    if kind == 'x':
        line(ctx, -26, -26, 26, 26, NAVY, 12); line(ctx, 26, -26, -26, 26, NAVY, 12)
    else:
        ctx.save(); ctx.rotate(-.35); ellipse(ctx, 0, 0, 38, 26, NAVY, NAVY, 3); ctx.restore()
    line(ctx, 32, 0, 32, -230, NAVY, 9)
    if hl == 'head': circle(ctx, 0, 0, 60, None, PINK, 7)
    if hl == 'stem': rrect(ctx, 14, -240, 36, 250, 16); ctx.set_source_rgba(*PINK, .3); ctx.fill()
    ctx.restore()

# ---------- scenes ----------
def sc_intro(ctx, t):
    tsec = wt('secret', 3); tdr = wt('Drummers', 4); tread = wt('read', 10); tbon = wt('bonus', 12)
    if t < tsec - .2:
        ep3_kit(ctx, 520, 560, .62, t); beat_chart(ctx, 1380, 520, t, .7)
        return
    m = smooth(prog(t, tsec - .2, .8))
    if m < 1: beat_chart(ctx, 960, 520, t, .85, alpha=1 - m, follow=False)
    draw_staff(ctx, 960, 520, lerp(.6, .78, m), t, notes={'hihat': tsec, 'snare': tsec, 'kick': tsec}, counts=1, bars=1, alpha=m)
    label(ctx, "THE SECRET CODE", 960, 170, 64, PINK, WHITE, scale=pop(t, tsec), rot=-.03)
    if t > tdr: label(ctx, "DRUMMERS ALL OVER THE WORLD CAN READ IT", 960, 795, 40, YELLOW, NAVY, scale=pop(t, tdr))
    if t > tread:
        ctx.save(); ctx.set_source_rgba(*NAVY, .35 * smooth(prog(t, tread, .3))); ctx.paint(); ctx.restore()
        text(ctx, "READ YOUR", 960, 330, 120, WHITE, NAVY, lw=20, scale=pop(t, tread), rot=-.03)
        text(ctx, "FIRST BEAT!", 960, 470, 150, YELLOW, NAVY, lw=24, scale=pop(t, tread + .3), rot=.02)
    if t > tbon:
        gift(ctx, 640, 760, .8 * pop(t, tbon), t, 0, shake=1)
        label(ctx, "BONUS: SPOT THE MISTAKE!", 1160, 760, 42, PINK, WHITE, scale=pop(t, tbon + .2), rot=.03)

def sc_recap(ctx, t):
    t0 = T['recap']; th = wt('hi-hat', t0); tk = wt('kick', th); ts = wt('snare', tk); tc = wt('One', ts); tp = wt('pause', tc); tn = wt('Now,', tp)
    hr = 'hihat' if th <= t < tk else ('kick' if tk <= t < ts else ('snare' if ts <= t < tc else None))
    label(ctx, "LAST TIME: YOUR FIRST ROCK BEAT", 960, 150, 52, WHITE, NAVY, scale=pop(t, t0))
    ep3_kit(ctx, 470, 560, .52, t, glow={hr: 1} if hr else {})
    beat_chart(ctx, 1330, 545, t, .78, highlight_row=hr)
    if t > tp:
        ctx.save(); ctx.set_source_rgba(*NAVY, .45 * smooth(prog(t, tp, .3))); ctx.paint(); ctx.restore()
        lesson_card(ctx, 960, 480, pop(t, tp) * 1.1, 3, "YOUR FIRST ROCK BEAT")
        label(ctx, "WATCH LESSON 3 FIRST!", 960, 740, 44, YELLOW, NAVY, scale=pop(t, tp + .3))
    if t > tn:
        ctx.save(); ctx.set_source_rgba(*NAVY, .6 * smooth(prog(t, tn, .3))); ctx.paint(); ctx.restore()
        text(ctx, "LET'S CRACK THE CODE!", 960, 470, 110, YELLOW, NAVY, lw=20, scale=pop(t, tn), rot=-.03)

def sc_staff(ctx, t):
    t0 = T['staff']; tmusic = phrase('Music is made', t0); tstaff = wt('staff.', t0); tfive = wt('five', tstaff); tfour = wt('four', tfive)
    tcount = wt('Count', tfour); tbird = wt('Every', tcount); twhere = wt('Where', tbird)
    if t < tmusic - .2:
        label(ctx, "READING MUSIC = READING WORDS", 960, 170, 52, YELLOW, NAVY, scale=pop(t, t0))
        panel(ctx, 960, 520, 900, 360, WHITE)
        for k, ch in enumerate("DRUM"):
            text(ctx, ch, 690 + k * 180, 520, 170, [RED, ORANGE, TEAL, PURPLE][k], NAVY, lw=16, scale=pop(t, wt('letters', t0) + .15 * k), rot=wob(t, 1, .05, k))
        return
    lines = clamp(prog(t, tstaff - .3, 1.6) * 5) if t < tcount else 5
    lh = None; sh = None
    if tcount <= t < tbird:
        nums = [w["start"] for w in WORDS if w["start"] >= tcount and norm(w["text"]) in ("one", "two", "three", "four", "five")][:5]
        lh = [k for k, x in enumerate(nums) if t >= x]
    elif tfour <= t < tcount: sh = [0, 1, 2, 3]
    if t < tstaff - .2:
        label(ctx, "MUSIC = NOTES ON A STAFF", 960, 170, 52, PINK, WHITE, scale=pop(t, tmusic))
    else:
        label(ctx, "THE STAFF", 960, 150, 70, PINK, WHITE, scale=pop(t, tstaff), rot=-.02)
    draw_staff(ctx, 960, 500, .8, t, lines=lines, line_hl=lh, space_hl=sh, clef=0, timesig=0, follow=False, panel_=t >= tstaff - .3)
    if tfive <= t < tcount: label(ctx, "5 LINES", 700, 795, 48, NAVY if False else YELLOW, NAVY, scale=pop(t, tfive))
    if tfour <= t < tcount: label(ctx, "4 SPACES", 1220, 795, 48, TEAL, WHITE, scale=pop(t, tfour))
    if t >= tbird:
        for k, (lf, x) in enumerate([(1, 760), (1.5, 920), (3, 1080), (3.5, 1240), (2, 1400)]):
            sx, sy = staff_to_screen(960, 500, .8, x - 960, lf)
            bird(ctx, sx, sy + 8, .9 * pop(t, tbird + .2 * k), t, k)
        label(ctx, "ON A LINE OR IN A SPACE", 960, 795, 46, YELLOW, NAVY, scale=pop(t, wt('wires', tbird)))
    if t >= twhere: label(ctx, "WHERE IT SITS = WHAT TO PLAY", 960, 795, 46, GREEN, WHITE, scale=pop(t, twhere))

def sc_clef(ctx, t):
    t0 = T['clef']; tdoor = wt('sign', t0); tfours = wt('Right', t0); tbars = wt('staff', tfours); tbox = wt('Each', tbars)
    zoom = t < tbars - .3
    if zoom:
        draw_staff(ctx, 1260, 560, 1.25, t, clef=1, timesig=smooth(prog(t, tfours, .4)), follow=False)
        cx, cy = staff_to_screen(1260, 560, 1.25, -750 + 30, 2)
        if t < tfours:
            circle(ctx, cx, cy, 120 + 8 * math.sin(t * 5), None, PINK, 8)
            label(ctx, "DRUM CLEF", 520, 330, 60, PINK, WHITE, scale=pop(t, t0 + .4))
            if t > tdoor:
                rrect(ctx, 330, 470, 380, 170, 20); fill_stroke(ctx, WHITE, NAVY, 6)
                text(ctx, "DRUMS", 520, 525, 54, RED, NAVY); text(ctx, "ONLY!", 520, 595, 46, NAVY, None, shadow=False)
        else:
            sx, sy = staff_to_screen(1260, 560, 1.25, -750 + 140, 2)
            circle(ctx, sx, sy, 140 + 8 * math.sin(t * 5), None, TEAL, 8)
            label(ctx, "4 / 4", 520, 330, 66, TEAL, WHITE, scale=pop(t, tfours))
            tf = wt('four', tfours)
            if t > tf: label(ctx, "= 4 COUNTS", 520, 450, 54, YELLOW, NAVY, scale=pop(t, tf))
        return
    draw_staff(ctx, 960, 520, .86, t, bars=smooth(prog(t, tbars, .5)), counts=1 if t > tbox else 0, follow=True)
    label(ctx, "BAR LINES", 960, 150, 64, ORANGE, WHITE, scale=pop(t, tbars), rot=-.02)
    if t > tbox: label(ctx, "1 BAR = 1 TIME THROUGH THE COUNT", 960, 795, 44, YELLOW, NAVY, scale=pop(t, tbox))

def sc_map(ctx, t):
    t0 = T['map']; tpiano = wt('piano,', t0); tdrums = wt('drums,', tpiano); tlow = wt('Low', tdrums); tkick = wt('kick', tlow)
    tsn = wt('snare', tkick); thh = wt('hi-hat?', tsn); tx = wt('x.', thh); tmap = wt('map.', tx)
    if t < tlow - .2:
        label(ctx, "THE COOLEST PART", 960, 150, 64, PINK, WHITE, scale=pop(t, t0))
        if t > tpiano:
            rrect(ctx, 260, 360, 620, 300, 20); fill_stroke(ctx, WHITE, NAVY, 6)
            for k in range(1, 8): line(ctx, 260 + k * 620 / 8, 360, 260 + k * 620 / 8, 660, NAVY, 4)
            for k in (1, 2, 4, 5, 6): rrect(ctx, 260 + k * 620 / 8 - 22, 360, 44, 170, 6); fill_stroke(ctx, NAVY, None)
            label(ctx, "PIANO: WHICH KEY", 570, 740, 40, WHITE, NAVY, scale=pop(t, tpiano))
        if t > tdrums:
            ep3_kit(ctx, 1380, 540, .5, t, sticks=False, bursts=False)
            label(ctx, "DRUMS: WHICH DRUM!", 1380, 795, 42, YELLOW, NAVY, scale=pop(t, tdrums))
        return
    S = 1.0; cx, cy = 1180, 500
    notes = {}
    if t >= tkick: notes['kick'] = wt('first', tkick)
    if t >= tsn: notes['snare'] = wt('third', tsn)
    if t >= tx: notes['hihat'] = tx
    draw_staff(ctx, cx, cy, S, t, notes=notes, clef=1, timesig=1, bars=1, follow=False, w=1100)
    label(ctx, "LOW SOUNDS SIT LOW, HIGH SOUNDS SIT HIGH", 960, 140, 44, YELLOW, NAVY, scale=pop(t, tlow))
    rows = [('kick', tkick, "KICK", "BOTTOM SPACE", KK_C), ('snare', tsn, "SNARE", "MIDDLE SPACE", SN_C), ('hihat', thh, "HI-HAT", "X ON TOP", HH_C)]
    for p, tp, name, where, col in rows:
        if t < tp: continue
        _, sy = staff_to_screen(cx, cy, S, 0, POS[p]); s_ = pop(t, tp)
        ctx.save(); ctx.translate(120, sy); sscale(ctx, s_, s_)
        if p == 'kick': kick(ctx, 0, 0, .2, t)
        elif p == 'snare': tom(ctx, 0, 8, .34, t, RED)
        else: cymbal(ctx, 0, 6, 52, t, GOLD, face=False); cymbal(ctx, 0, -6, 52, t, GOLD, face=True)
        ctx.restore()
        label(ctx, f"{name}: {where}", 370, sy, 30, col, WHITE, scale=s_)
        line(ctx, 545, sy, cx - 550 + 60, sy, col, 5, .8 * s_, dash=[12, 10])
    for p, word, after, s_, col in (('kick', 'Boom.', tkick, "BOOM!", ORANGE), ('snare', 'Crack.', tsn, "CRACK!", RED), ('hihat', 'Tick.', tx, "TICK!", TEAL)):
        try: tw_ = wt(word, after)
        except KeyError: continue
        _, sy = staff_to_screen(cx, cy, S, 0, POS[p]); sfx(ctx, t, tw_, s_, 1830, sy, 40, col, .06, 1.0)
    if tx - .3 <= t < tmap:
        label(ctx, "CYMBALS = METAL = X", 1300, 795, 44, TEAL, WHITE, scale=pop(t, wt('metal,', thh)))
    if t >= tmap: label(ctx, "THAT'S YOUR WHOLE MAP!", 1300, 795, 50, GREEN, WHITE, scale=pop(t, tmap))

def sc_notes(ctx, t):
    t0 = T['notes']; tstem = wt('stem.', t0); tpairs = wt('When', tstem); tfuture = wt("We'll", tpairs)
    label(ctx, "WHAT A NOTE LOOKS LIKE", 960, 150, 60, PINK, WHITE, scale=pop(t, t0))
    hl = 'head' if t < tstem - .3 else 'stem'
    big_note(ctx, 420, 720, 1.2 * pop(t, t0 + .2), 'note', t, hl if t < tpairs else None)
    big_note(ctx, 700, 720, 1.2 * pop(t, t0 + .5), 'x', t, hl if t < tpairs else None)
    label(ctx, "HEAD" if t < tstem - .3 else "STEM", 560, 795, 50, YELLOW, NAVY, scale=pop(t, t0 + .3 if t < tstem - .3 else tstem - .3)) if t < tpairs else None
    if t >= tpairs:
        p = pop(t, tpairs)
        ctx.save(); ctx.translate(1350, 480); sscale(ctx, p, p)
        panel(ctx, 0, 0, 640, 520, WHITE)
        for k, x in enumerate((-120, 120)):
            line(ctx, x - 26, 90, x + 26, 140, NAVY, 12); line(ctx, x + 26, 90, x - 26, 140, NAVY, 12)
            line(ctx, x + 30, 115, x + 30, -120, NAVY, 9)
            text(ctx, ["1", "&"][k], x, 200, 70, [NAVY, PINK][k], None, shadow=False)
        rrect(ctx, -92, -134, 246, 24, 4); ctx.set_source_rgb(*NAVY); ctx.fill()
        ctx.restore()
        label(ctx, "PAIR = A COUNT + ITS \"AND\"", 1350, 795, 40, YELLOW, NAVY, scale=pop(t, tpairs + .4))
    if t >= tfuture: label(ctx, "NAMES COMING IN A FUTURE LESSON!", 560, 795, 34, GREEN, WHITE, scale=pop(t, tfuture))

def sc_build(ctx, t):
    t0 = T['build']; t1 = phrase('Layer one the hi-hat', t0); t2 = phrase('Layer two the kick', t1); t3 = phrase('Layer three the snare', t2); tthere = wt('there', t3)
    notes = {'hihat': t1 + .4}
    if t >= t2: notes['kick'] = wt('bottom', t2)
    if t >= t3: notes['snare'] = wt('middle', t3)
    draw_staff(ctx, 960, 500, .86, t, notes=notes, counts=1, bars=1)
    lab = ("LAYER 1: HI-HAT", HH_C, t1) if t < t2 else (("LAYER 2: KICK", KK_C, t2) if t < t3 else ("LAYER 3: SNARE", SN_C, t3))
    if t < tthere: label(ctx, lab[0], 960, 150, 64, lab[1], WHITE, scale=pop(t, lab[2]), rot=-.02)
    else:
        label(ctx, "OUR ROCK BEAT, WRITTEN DOWN!", 960, 150, 58, GREEN, WHITE, scale=pop(t, tthere))
        confetti(ctx, 960, 300, t - tthere, seed=51, n=60, spread=800)
    if t < t1: label(ctx, "ONE LAYER AT A TIME", 960, 795, 46, YELLOW, NAVY, scale=pop(t, t0))

def sc_read(ctx, t):
    t0 = T['read']; tone = wt('On', t0); tand = wt('On', tone + .5); ttwo = wt('On', tand + .5)
    full = {'hihat': -9, 'snare': -9, 'kick': -9}
    hc = ()
    if tone <= t < tand: hc = (0,)
    elif tand <= t < ttwo: hc = (1,)
    elif t >= ttwo: hc = (2,)
    label(ctx, "READ STRAIGHT DOWN EACH COUNT", 960, 150, 52, YELLOW, NAVY, scale=pop(t, t0))
    draw_staff(ctx, 960, 470, .78, t, notes=full, counts=1, bars=1, col_hl=hc, follow=False)
    if hc:
        txt = {0: "HI-HAT + KICK", 1: "JUST HI-HAT", 2: "HI-HAT + SNARE"}[hc[0]]
        label(ctx, txt, 960, 795, 54, PINK, WHITE, scale=pop(t, [tone, tand, ttwo][hc[0]]))

def sc_play(ctx, t):
    t0 = T['play']; tread = wt('You', t0 + 3); toff = wt('officially', tread)
    draw_staff(ctx, 1170, 600, .62, t, notes={'hihat': -9, 'snare': -9, 'kick': -9}, counts=1, bars=1)
    ep3_kit(ctx, 330, 600, .44, t)
    ep3.countin(ctx, t, 330, 330)
    if t < tread: label(ctx, "READ IT + PLAY IT!", 960, 170, 60, PINK, WHITE, scale=pop(t, t0))
    else:
        text(ctx, "YOU JUST READ", 960, 190, 100, WHITE, NAVY, lw=18, scale=pop(t, tread), rot=-.03)
        text(ctx, "YOUR FIRST BEAT!", 960, 310, 110, YELLOW, NAVY, lw=18, scale=pop(t, tread + .3), rot=.02)
        confetti(ctx, 960, 300, t - tread, seed=61, n=90, spread=900, dur=2.6)
        if t > toff: label(ctx, "OFFICIAL DRUM-MUSIC READER", 1150, 800, 44, GREEN, WHITE, scale=pop(t, toff))

def sc_recap2(ctx, t):
    t0 = T['recap2']; tk = wt('Kick', t0); ts = wt('Snare', tk); th = wt('Hi-hat', ts)
    label(ctx, "SAY THE MAP WITH ME!", 960, 150, 58, YELLOW, NAVY, scale=pop(t, t0))
    notes = {}
    if t >= tk: notes['kick'] = tk
    if t >= ts: notes['snare'] = ts
    if t >= th: notes['hihat'] = th
    draw_staff(ctx, 960, 500, .86, t, notes=notes, follow=False)
    for p, tp, txt, col in (('kick', tk, "BOTTOM", KK_C), ('snare', ts, "MIDDLE", SN_C), ('hihat', th, "X ON TOP", HH_C)):
        if t >= tp:
            _, sy = staff_to_screen(960, 500, .86, 0, POS[p]); label(ctx, txt, 1760, sy, 30, col, WHITE, scale=pop(t, tp))

def sc_bonus(ctx, t):
    t0 = T['bonus']; tlook = wt('Look', t0); tpause = wt('Pause', tlook); tready = wt('Ready?', tpause); tans = wt('The', tready); tgreat = wt('Great', tans)
    if t < tlook - .2:
        op = smooth(prog(t, t0 + .4, .8))
        gift(ctx, 960, 560, 1.6 * pop(t, t0), t, op, shake=1 - op)
        if op > 0:
            burst(ctx, 960, 420, 320 * ease_out(op), YELLOW, None, 20, t * .5, alpha=.8 * op)
            text(ctx, "SPOT THE MISTAKE!", 960, 300, 110, YELLOW, NAVY, lw=20, scale=lerp(2, 1, back(prog(t, t0 + .5, .4))), alpha=clamp(prog(t, t0 + .5, .15) * 3))
            confetti(ctx, 960, 420, t - t0 - .4, seed=33, n=90, spread=900, dur=2.5)
        return
    fixed = t >= tans + 1.0
    draw_staff(ctx, 960, 500, .86, t, notes={'hihat': -9, 'snare': -9, 'kick': -9}, counts=1, bars=1, follow=False, wrong=not fixed,
               col_hl=((0, 4) if tans <= t < tans + 1.0 else ((2, 6) if fixed else ())))
    if t < tans:
        label(ctx, "LOOK AT THE SNARE...", 960, 150, 58, PINK, WHITE, scale=pop(t, tlook))
        mx = 960 + 300 * math.sin(t * 1.3); my = 520
        circle(ctx, mx, my, 90, None, NAVY, 14); line(ctx, mx + 64, my + 64, mx + 140, my + 140, NAVY, 22)
        if t > tpause:
            ctx.save(); ctx.translate(960, 795); sscale(ctx, pop(t, tpause), pop(t, tpause))
            rrect(ctx, -110, -50, 220, 100, 28); fill_stroke(ctx, RED, NAVY, 6)
            for dx in (-22, 22): rrect(ctx, dx - 10, -28, 20, 56, 5); fill_stroke(ctx, WHITE, None)
            ctx.restore()
    elif not fixed:
        label(ctx, "SNARE ON 1 AND 3?  NOPE!", 960, 150, 56, RED, WHITE, scale=pop(t, tans))
        cross(ctx, 960, 795, .7, p=prog(t, tans, .4))
    else:
        label(ctx, "SNARE GOES ON 2 AND 4!", 960, 150, 56, GREEN, WHITE, scale=pop(t, tans + 1.0))
        check(ctx, 960, 795, .7, p=prog(t, tans + 1.1, .4))
        if t > tgreat: confetti(ctx, 960, 400, t - tgreat, seed=71, n=80, spread=900)

def sc_outro(ctx, t):
    t0 = T['outro']; tnext = wt('Next', t0); tsub = wt('Subscribe', tnext); tsee = wt('See', tsub)
    if t < tnext - .2:
        draw_staff(ctx, 960, 500, .8, t, notes={'hihat': -9, 'snare': -9, 'kick': -9}, counts=1, bars=1, follow=False)
        label(ctx, "YOU CAN READ DRUM MUSIC!", 960, 150, 60, GREEN, WHITE, scale=pop(t, t0))
        confetti(ctx, 960, 300, t - t0, seed=101, n=70, spread=900)
        return
    label(ctx, "NEXT EPISODE", 960, 140, 56, PINK, WHITE, scale=pop(t, tnext - .2))
    p = pop(t, tnext)
    ctx.save(); ctx.translate(680, 500); sscale(ctx, p * .9, p * .9)
    panel(ctx, 0, 0, 760, 460, WHITE); ep3_kit(ctx, 0, 40, .42, t, bursts=False)
    ctx.restore()
    label(ctx, "ADD MORE TO YOUR BEAT!", 680, 790, 46, YELLOW, NAVY, scale=pop(t, wt('more', tnext)), rot=-.03)
    sp = pop(t, tsub - .3)
    if sp > 0:
        clicked = t > tsub + .5; pulse = 1 + .06 * math.sin(t * 7)
        ctx.save(); ctx.translate(1430, 450); sscale(ctx, sp * pulse, sp * pulse)
        rrect(ctx, -230, -70, 460, 140, 70); fill_stroke(ctx, (0.55, 0.55, 0.6) if clicked else RED, NAVY, 7)
        text(ctx, "SUBSCRIBED!" if clicked else "SUBSCRIBE", 0, 0, 50 if clicked else 58, WHITE, NAVY); ctx.restore()
        confetti(ctx, 1430, 450, t - tsub - .5, seed=44, n=50, spread=600)
    if t > tsee: text(ctx, "SEE YOU NEXT TIME, DRUMMERS!", 1430, 680, 50, YELLOW, NAVY, scale=pop(t, tsee), rot=-.02)

SCENES = [(0, T['recap'], sc_intro), (T['recap'], T['staff'], sc_recap), (T['staff'], T['clef'], sc_staff), (T['clef'], T['map'], sc_clef),
          (T['map'], T['notes'], sc_map), (T['notes'], T['build'], sc_notes), (T['build'], T['read'], sc_build), (T['read'], T['play'], sc_read),
          (T['play'], T['recap2'], sc_play), (T['recap2'], T['bonus'], sc_recap2), (T['bonus'], T['outro'], sc_bonus), (T['outro'], 9999, sc_outro)]
TINTS = {sc_staff: TEAL, sc_map: PURPLE, sc_build: TEAL, sc_bonus: PURPLE, sc_outro: PINK}

def frame(ctx, t):
    s, e, fn = [x for x in SCENES if x[0] <= t < x[1]][0]
    background(ctx, t, TINTS.get(fn))
    ctx.save()
    out = smooth(prog(t, e - .18, .18)) if e < 900 else 0
    if out > 0: ctx.translate(960, 480); sscale(ctx, 1 - out, 1 - out); ctx.translate(-960, -480)
    fn(ctx, t); ctx.restore()
    if 0 < s and t - s < .2: ctx.set_source_rgba(1, 1, 1, .35 * (1 - (t - s) / .2)); ctx.paint()
    hud(ctx, t)
    if fn is not sc_intro or t > 6: narrator(ctx, t)
    captions(ctx, t)

def surface(t, scale):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale)); ctx = cairo.Context(s)
    fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo); sscale(ctx, scale, scale); frame(ctx, t); return s

if __name__ == "__main__":
    if sys.argv[1] == "still":
        surface(float(sys.argv[2]), float(sys.argv[3])).write_to_png(sys.argv[4])
    elif sys.argv[1] == "info":
        print(json.dumps({k: round(v, 2) for k, v in T.items()}, indent=0)); print(len(BARS), "bars", len(COUNTINS), "count-ins")
        for b in BARS: print(round(b["t0"], 2), sorted(b["layer"]))
    else:
        f0, f1, sc, out = int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        crf = sys.argv[6] if len(sys.argv) > 6 else "20"
        ofps = int(sys.argv[7]) if len(sys.argv) > 7 else FPS; step = FPS // ofps
        w, h = int(W * sc), int(H * sc)
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(ofps), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", "-threads", "2", out], stdin=subprocess.PIPE)
        for f in range(f0, f1, step):
            p.stdin.write(surface(f / FPS, sc).get_data())
        p.stdin.close(); p.wait()
