"""Drawing helpers for the drum-lesson animation (logical canvas 1920x1080)."""
import math, random, json, re
import cairo


W, H = 1920, 1080
FONT = "Fredoka"

# palette
NAVY = (0.09, 0.11, 0.30)
WHITE = (1, 1, 1)
YELLOW = (1.0, 0.86, 0.20)
ORANGE = (1.0, 0.55, 0.10)
PINK = (1.0, 0.33, 0.62)
GREEN = (0.22, 0.85, 0.45)
RED = (0.95, 0.22, 0.25)
PURPLE = (0.58, 0.36, 0.95)
TEAL = (0.10, 0.80, 0.80)
WOOD = (0.93, 0.74, 0.45)
WOOD_D = (0.80, 0.58, 0.30)
SKY = (0.17, 0.55, 1.0)
LIGHT = (0.82, 0.90, 1.0)
GLOVE = (1, 1, 1)
LW = 6  # outline width


# ---------- math / easing ----------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def lerpc(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))

def smooth(t):
    t = clamp(t); return t * t * (3 - 2 * t)

def ease_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3

def ease_in_out(t):
    t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def back(t, s=1.9):
    t = clamp(t); t -= 1; return t * t * ((s + 1) * t + s) + 1

def elastic(t):
    t = clamp(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - .75) * (2 * math.pi / 3)) + 1

def prog(t, t0, d):
    """0..1 progress of an animation that starts at t0 lasting d."""
    return clamp((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)

def pop(t, t0, d=0.45):
    return back(prog(t, t0, d)) if t >= t0 else 0.0

def wob(t, f=1.0, a=1.0, ph=0.0):
    return a * math.sin(2 * math.pi * f * t + ph)


# ---------- primitives ----------
def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()

def fill_stroke(ctx, fill, stroke=NAVY, lw=LW, alpha=1.0):
    if fill is not None:
        ctx.set_source_rgba(*fill, alpha)
        if stroke is not None:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke is not None:
        ctx.set_source_rgba(*stroke, alpha)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()

def circle(ctx, x, y, r, fill, stroke=NAVY, lw=LW, alpha=1.0):
    ctx.new_path(); ctx.arc(x, y, max(r, 0.01), 0, 2 * math.pi)
    fill_stroke(ctx, fill, stroke, lw, alpha)

def ellipse(ctx, x, y, rx, ry, fill, stroke=NAVY, lw=LW, alpha=1.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, max(rx, .01), max(ry, .01))
    ctx.new_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    fill_stroke(ctx, fill, stroke, lw, alpha)

def capsule(ctx, x1, y1, x2, y2, r, fill, stroke=NAVY, lw=LW, alpha=1.0):
    a = math.atan2(y2 - y1, x2 - x1)
    ctx.new_path()
    ctx.arc(x2, y2, r, a - math.pi / 2, a + math.pi / 2)
    ctx.arc(x1, y1, r, a + math.pi / 2, a + 3 * math.pi / 2)
    ctx.close_path()
    fill_stroke(ctx, fill, stroke, lw, alpha)

def line(ctx, x1, y1, x2, y2, col=NAVY, lw=LW, alpha=1.0, dash=None):
    ctx.new_path(); ctx.move_to(x1, y1); ctx.line_to(x2, y2)
    ctx.set_source_rgba(*col, alpha); ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if dash: ctx.set_dash(dash)
    ctx.stroke(); ctx.set_dash([])

def star_path(ctx, x, y, r, n=5, inner=0.48, rot=-math.pi / 2):
    ctx.new_path()
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * inner
        a = rot + i * math.pi / n
        (ctx.move_to if i == 0 else ctx.line_to)(x + rr * math.cos(a), y + rr * math.sin(a))
    ctx.close_path()

def star(ctx, x, y, r, fill=YELLOW, stroke=NAVY, lw=LW, alpha=1.0, rot=-math.pi / 2, n=5, inner=0.48):
    star_path(ctx, x, y, r, n, inner, rot); fill_stroke(ctx, fill, stroke, lw, alpha)

def burst(ctx, x, y, r, fill=YELLOW, stroke=NAVY, n=12, rot=0.0, alpha=1.0, lw=LW):
    star(ctx, x, y, r, fill, stroke, lw, alpha, rot, n, 0.72)


# ---------- text ----------
def text(ctx, s, x, y, size=60, fill=WHITE, stroke=NAVY, lw=None, align="center",
         alpha=1.0, weight="bold", scale=1.0, rot=0.0, shadow=True):
    if alpha <= 0.001 or scale <= 0.001: return
    fam = {"bold": "Fredoka", "semi": "Fredoka SemiBold", "med": "Fredoka Medium"}[weight]
    ctx.save()
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if weight == "bold" else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    ctx.translate(x, y); ctx.rotate(rot); sscale(ctx, scale, scale)
    if align == "center": ox = -(ext.x_advance) / 2
    elif align == "right": ox = -ext.x_advance
    else: ox = 0
    oy = size * 0.35
    lw = lw if lw is not None else max(4, size * 0.14)
    if shadow:
        ctx.new_path(); ctx.move_to(ox + size * 0.04, oy + size * 0.07); ctx.text_path(s)
        ctx.set_source_rgba(*NAVY, 0.35 * alpha); ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve(); ctx.fill()
    ctx.new_path(); ctx.move_to(ox, oy); ctx.text_path(s)
    if stroke is not None:
        ctx.set_source_rgba(*stroke, alpha); ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgba(*fill, alpha); ctx.fill()
    ctx.restore()

def text_width(ctx, s, size, weight="bold"):
    fam = {"bold": "Fredoka", "semi": "Fredoka SemiBold", "med": "Fredoka Medium"}[weight]
    ctx.save()
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if weight == "bold" else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size); w = ctx.text_extents(s).x_advance; ctx.restore()
    return w

def label(ctx, s, x, y, size=40, bg=YELLOW, fg=NAVY, scale=1.0, rot=0.0, alpha=1.0, pad=22):
    """Rounded sticker label centred at x,y."""
    if scale <= 0.001 or alpha <= 0.001: return
    w = text_width(ctx, s, size) + pad * 2; h = size * 1.45
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); sscale(ctx, scale, scale)
    rrect(ctx, -w / 2 + 5, -h / 2 + 8, w, h, h / 2); ctx.set_source_rgba(*NAVY, 0.35 * alpha); ctx.fill()
    rrect(ctx, -w / 2, -h / 2, w, h, h / 2); fill_stroke(ctx, bg, NAVY, LW, alpha)
    text(ctx, s, 0, 0, size, fg, None, alpha=alpha, shadow=False)
    ctx.restore()


# ---------- props ----------
def stick(ctx, x, y, ang, L=520, w=26, face=None, t=0.0, color=WOOD, alpha=1.0, hi=None):
    """Drumstick with butt at (x,y) pointing along ang. hi = part to highlight."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
    hw = w / 2
    sh0, sh1 = 0.70 * L, 0.93 * L   # shoulder taper zone
    tipw = hw * 0.42
    ctx.new_path()
    ctx.move_to(0, -hw)
    ctx.line_to(sh0, -hw)
    ctx.curve_to(sh0 + (sh1 - sh0) * .5, -hw, sh1 - 20, -tipw, sh1, -tipw)
    ctx.line_to(sh1, tipw)
    ctx.curve_to(sh1 - 20, tipw, sh0 + (sh1 - sh0) * .5, hw, sh0, hw)
    ctx.line_to(0, hw)
    ctx.arc(0, 0, hw, math.pi / 2, 3 * math.pi / 2)
    ctx.close_path()
    fill_stroke(ctx, color, NAVY, LW, alpha)
    # grain highlight
    line(ctx, 18, -hw * 0.45, sh0 - 10, -hw * 0.45, (1, 1, 1), 3, 0.45 * alpha)
    # tip
    ellipse(ctx, sh1 + tipw * 1.4, 0, tipw * 1.9, tipw * 1.35, color, NAVY, LW, alpha)
    if hi:
        zones = {"tip": (sh1 - 4, sh1 + tipw * 3.4), "shoulder": (sh0, sh1),
                 "shaft": (hw, sh0), "butt": (-hw, 0.14 * L)}
        a, b = zones[hi]
        ctx.save(); rrect(ctx, a - 8, -hw - 14, b - a + 16, w + 28, 18)
        ctx.set_source_rgba(*YELLOW, 0.35 * alpha); ctx.fill_preserve()
        ctx.set_source_rgba(*YELLOW, alpha); ctx.set_line_width(5); ctx.set_dash([14, 10]); ctx.stroke(); ctx.set_dash([])
        ctx.restore()
    if face:
        ctx.translate(0.55 * L, 0); ctx.rotate(-ang)
        fs = max(1.0, w / 26)
        sscale(ctx, fs, fs)
        fx = 0
        blink = (t * 0.7) % 3.3 < 0.12
        for dx in (-16, 16):
            if blink: line(ctx, fx + dx - 7, -2, fx + dx + 7, -2, NAVY, 4, alpha)
            else:
                ellipse(ctx, fx + dx, -3, 8, 10, WHITE, NAVY, 3, alpha)
                circle(ctx, fx + dx + 2, -1, 4, NAVY, None, alpha=alpha)
        if face == "wink":
            ellipse(ctx, fx + 16, -3, 9, 10, color, None, alpha=alpha)
            ctx.new_path(); ctx.arc(fx + 16, 0, 8, math.pi * 1.1, math.pi * 1.9); ctx.set_source_rgba(*NAVY, alpha); ctx.set_line_width(4); ctx.stroke()
        ctx.new_path(); ctx.arc(fx, 4, 9, 0.15 * math.pi, 0.85 * math.pi)
        ctx.set_source_rgba(*NAVY, alpha); ctx.set_line_width(4); ctx.stroke()
        if face in ("sad", "squeezed"):
            ctx.new_path(); ctx.arc(fx, 14, 8, 1.15 * math.pi, 1.85 * math.pi); ctx.set_source_rgba(*NAVY, alpha); ctx.stroke()
    ctx.restore()


def glove_grip(ctx, x, y, ang, curl=1.0, squeeze=0.0, thumb_top=False, t=0.0, cuff=PINK,
               alpha=1.0, flip=False, splay=0.0, scale=1.0):
    """Side-view cartoon glove gripping a stick passing horizontally through (x,y)."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); sscale(ctx, scale, -scale if flip else scale)
    sx = wob(t, 22, 3 * squeeze) if squeeze else 0
    ctx.translate(sx, 0)
    gcol = lerpc(GLOVE, (1, 0.72, 0.72), squeeze)
    # cuff + palm (behind/below the stick, toward the butt side)
    rrect(ctx, -170, -10, 70, 120, 26); fill_stroke(ctx, cuff, NAVY, LW, alpha)
    rrect(ctx, -125, -55, 150, 150, 60); fill_stroke(ctx, gcol, NAVY, LW, alpha)
    # stick passes here (drawn by caller first). fingers in front:
    for i in range(3):
        fx = -78 + i * 34
        ang_f = lerp(0.0, 1.0, curl)
        if curl >= 0.5:
            ln = lerp(70, 92, squeeze)
            rrect(ctx, fx - 16, -26, 32, ln, 16); fill_stroke(ctx, gcol, NAVY, LW, alpha)
        else:
            # sticking out downward-forward
            a = math.pi / 2 - 0.35 - splay * 0.25 * (i + 1)
            l = 95
            capsule(ctx, fx, 20, fx + l * math.cos(a), 20 + l * math.sin(a), 16, gcol, NAVY, LW, alpha)
    # index finger (curled around near the front)
    if curl >= 0.5:
        rrect(ctx, 10 - 18, -30, 36, lerp(78, 96, squeeze), 18); fill_stroke(ctx, gcol, NAVY, LW, alpha)
    else:
        capsule(ctx, 12, 18, 80, 80, 17, gcol, NAVY, LW, alpha)
    # thumb
    if thumb_top:
        capsule(ctx, -10, -70, 60, -22, 19, gcol, NAVY, LW, alpha)
        ellipse(ctx, 56, -28, 11, 6, (1, .6, .6), None, alpha=alpha * 0.8)
    else:
        capsule(ctx, -20, -40, 70, -8, 19, gcol, NAVY, LW, alpha)
    # glove stitching lines
    for i in range(3):
        line(ctx, -95 + i * 18, -40, -95 + i * 18, -20, NAVY, 3, 0.5 * alpha)
    if squeeze > 0.3:
        for k in range(3):
            a = -1.9 + k * 0.5
            r1, r2 = 120, 150 + wob(t, 6, 8)
            line(ctx, -40 + r1 * math.cos(a), r1 * math.sin(a), -40 + r2 * math.cos(a), r2 * math.sin(a), RED, 6, alpha * squeeze)
    ctx.restore()


def glove_point(ctx, x, y, ang=0, alpha=1.0, cuff=TEAL, scale=1.0):
    """Glove with index finger pointing up (for balancing). Fingertip at (x,y)."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); sscale(ctx, scale, scale)
    rrect(ctx, -40, 160, 80, 70, 22); fill_stroke(ctx, cuff, NAVY, LW, alpha)
    rrect(ctx, -70, 60, 140, 120, 50); fill_stroke(ctx, GLOVE, NAVY, LW, alpha)
    capsule(ctx, -10, 120, -10, 12, 19, GLOVE, NAVY, LW, alpha)
    capsule(ctx, -60, 110, -95, 70, 18, GLOVE, NAVY, LW, alpha)
    for i in range(3):
        rrect(ctx, 0 + i * 22 - 4, 70, 26, 40, 13); fill_stroke(ctx, GLOVE, NAVY, 4, alpha)
    ctx.restore()


def glove_thumbsup(ctx, x, y, s=1.0, alpha=1.0, rot=0.0, cuff=GREEN):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); sscale(ctx, s, s)
    rrect(ctx, -60, 60, 90, 60, 20); fill_stroke(ctx, cuff, NAVY, LW, alpha)
    rrect(ctx, -75, -40, 140, 110, 40); fill_stroke(ctx, GLOVE, NAVY, LW, alpha)
    capsule(ctx, -30, -40, -30, -120, 24, GLOVE, NAVY, LW, alpha)
    for i in range(3):
        line(ctx, 10, -10 + i * 25, 60, -10 + i * 25, NAVY, 4, alpha)
    ctx.restore()


def bird(ctx, x, y, s=1.0, t=0.0, flap=0.0, alpha=1.0, happy=True):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    # tail
    ctx.new_path(); ctx.move_to(-55, 0); ctx.line_to(-95, -25); ctx.line_to(-90, 15); ctx.close_path()
    fill_stroke(ctx, ORANGE, NAVY, 5, alpha)
    ellipse(ctx, 0, 0, 62, 54, YELLOW, NAVY, 5, alpha)
    ellipse(ctx, 10, 18, 36, 26, (1, .95, .7), None, alpha=alpha)
    # wing
    fa = wob(t, 6, 0.6) * flap
    ctx.save(); ctx.translate(-10, 0); ctx.rotate(-0.3 + fa)
    ellipse(ctx, -10, 0, 34, 20, ORANGE, NAVY, 5, alpha); ctx.restore()
    # eye, cheek, beak
    circle(ctx, 28, -16, 9, NAVY, None, alpha=alpha); circle(ctx, 31, -19, 3, WHITE, None, alpha=alpha)
    ellipse(ctx, 34, 4, 9, 6, PINK, None, alpha=alpha * 0.8)
    ctx.new_path(); ctx.move_to(54, -10); ctx.line_to(80, -2); ctx.line_to(54, 6); ctx.close_path()
    fill_stroke(ctx, ORANGE, NAVY, 4, alpha)
    ctx.restore()


def pad_top(ctx, x, y, r=170, alpha=1.0):
    circle(ctx, x, y, r, (0.28, 0.30, 0.38), NAVY, LW, alpha)
    circle(ctx, x, y, r * 0.8, (0.45, 0.47, 0.55), None, alpha=alpha)
    circle(ctx, x - r * 0.25, y - r * 0.25, r * 0.18, (1, 1, 1), None, alpha=alpha * 0.12)


def pad_side(ctx, x, y, w=420, alpha=1.0, stand=True):
    """Practice pad on stand, side view. (x,y) is top centre of the rubber."""
    if stand:
        line(ctx, x, y + 40, x, y + 300, NAVY, 12, alpha)
        line(ctx, x, y + 300, x - 90, y + 360, NAVY, 10, alpha)
        line(ctx, x, y + 300, x + 90, y + 360, NAVY, 10, alpha)
    rrect(ctx, x - w / 2, y + 8, w, 40, 14); fill_stroke(ctx, (0.25, 0.27, 0.35), NAVY, LW, alpha)
    rrect(ctx, x - w * 0.4, y - 6, w * 0.8, 22, 10); fill_stroke(ctx, (0.50, 0.52, 0.60), NAVY, 5, alpha)


def drum(ctx, x, y, s=1.0, t=0.0, mouth=0.0, alpha=1.0, body=RED, eyes=True, blink_off=0.0, look=0.0):
    """Mascot snare drum, (x,y) centre."""
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    rw, bh = 150, 150
    # body
    ctx.new_path()
    ctx.move_to(-rw, -bh / 2); ctx.line_to(-rw, bh / 2)
    ctx.save(); ctx.translate(0, bh / 2); sscale(ctx, rw, 40); ctx.arc_negative(0, 0, 1, math.pi, 0); ctx.restore()
    ctx.line_to(rw, -bh / 2); ctx.close_path()
    fill_stroke(ctx, body, NAVY, LW, alpha)
    # zigzag lugs
    for i in range(5):
        lx = -110 + i * 55
        rrect(ctx, lx - 8, -bh / 2 + 20, 16, 40, 6); fill_stroke(ctx, (0.85, 0.87, 0.92), NAVY, 3, alpha)
    # bottom rim
    ctx.save(); ctx.translate(0, bh / 2); sscale(ctx, rw, 40); ctx.new_path(); ctx.arc(0, 0, 1, 0, math.pi); ctx.restore()
    ctx.set_source_rgba(*NAVY, alpha); ctx.set_line_width(LW); ctx.stroke()
    # top head
    ellipse(ctx, 0, -bh / 2, rw, 40, (0.96, 0.96, 0.98), NAVY, LW, alpha)
    ellipse(ctx, 0, -bh / 2, rw * 0.86, 30, WHITE, None, alpha=alpha)
    if eyes:
        blink = ((t + blink_off) % 4.1) < 0.13
        for dx in (-48, 48):
            if blink:
                line(ctx, dx - 16, 10, dx + 16, 10, NAVY, 6, alpha)
            else:
                ellipse(ctx, dx, 8, 22, 27, WHITE, NAVY, 5, alpha)
                circle(ctx, dx + 5 + look * 8, 12, 11, NAVY, None, alpha=alpha)
                circle(ctx, dx + 9 + look * 8, 7, 4, WHITE, None, alpha=alpha)
        ellipse(ctx, -88, 48, 16, 10, PINK, None, alpha=alpha * 0.7)
        ellipse(ctx, 88, 48, 16, 10, PINK, None, alpha=alpha * 0.7)
        m = clamp(mouth, 0, 1)
        if m < 0.08:
            ctx.new_path(); ctx.arc(0, 40, 22, 0.15 * math.pi, 0.85 * math.pi)
            ctx.set_source_rgba(*NAVY, alpha); ctx.set_line_width(6); ctx.stroke()
        else:
            ellipse(ctx, 0, 52, 24 + 6 * m, 6 + 26 * m, (0.45, 0.05, 0.12), NAVY, 5, alpha)
            ellipse(ctx, 0, 52 + 14 * m, 13, 6 * m, PINK, None, alpha=alpha)
    ctx.restore()


def gift(ctx, x, y, s=1.0, t=0.0, open_=0.0, alpha=1.0, shake=0.0):
    ctx.save(); ctx.translate(x + wob(t, 9, 6 * shake), y); ctx.rotate(wob(t, 7, 0.08 * shake)); sscale(ctx, s, s)
    rrect(ctx, -110, -40, 220, 160, 16); fill_stroke(ctx, PURPLE, NAVY, LW, alpha)
    rrect(ctx, -20, -40, 40, 160, 4); fill_stroke(ctx, YELLOW, NAVY, 4, alpha)
    ctx.save(); ctx.translate(0, -40 - 160 * ease_out(open_)); ctx.rotate(-0.6 * ease_out(open_))
    rrect(ctx, -125, -50, 250, 55, 14); fill_stroke(ctx, PURPLE, NAVY, LW, alpha)
    rrect(ctx, -22, -50, 44, 55, 4); fill_stroke(ctx, YELLOW, NAVY, 4, alpha)
    ellipse(ctx, -40, -70, 40, 22, YELLOW, NAVY, 5, alpha); ellipse(ctx, 40, -70, 40, 22, YELLOW, NAVY, 5, alpha)
    circle(ctx, 0, -62, 16, ORANGE, NAVY, 5, alpha)
    ctx.restore(); ctx.restore()


def check(ctx, x, y, s=1.0, alpha=1.0, p=1.0):
    if p <= 0: return
    ctx.save(); ctx.translate(x, y); sscale(ctx, s * back(p), s * back(p))
    circle(ctx, 0, 0, 60, GREEN, NAVY, LW, alpha)
    ctx.new_path(); ctx.move_to(-28, 2); ctx.line_to(-8, 24); ctx.line_to(30, -20)
    ctx.set_source_rgba(1, 1, 1, alpha); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke(); ctx.restore()

def cross(ctx, x, y, s=1.0, alpha=1.0, p=1.0):
    if p <= 0: return
    ctx.save(); ctx.translate(x, y); sscale(ctx, s * back(p), s * back(p))
    circle(ctx, 0, 0, 60, RED, NAVY, LW, alpha)
    line(ctx, -24, -24, 24, 24, WHITE, 14, alpha); line(ctx, 24, -24, -24, 24, WHITE, 14, alpha)
    ctx.restore()


def confetti(ctx, x, y, age, seed=1, n=40, spread=520, dur=1.8, alpha=1.0):
    if age < 0 or age > dur: return
    rnd = random.Random(seed)
    cols = [YELLOW, PINK, GREEN, ORANGE, TEAL, WHITE, PURPLE]
    a = alpha * (1 - smooth((age - dur * 0.6) / (dur * 0.4)))
    for i in range(n):
        ang = rnd.uniform(-math.pi, 0) + rnd.uniform(-.3, .3)
        sp = rnd.uniform(0.4, 1.0) * spread
        px = x + math.cos(ang) * sp * ease_out(age / 0.9)
        py = y + math.sin(ang) * sp * ease_out(age / 0.9) + 260 * age * age
        ctx.save(); ctx.translate(px, py); ctx.rotate(age * rnd.uniform(-8, 8))
        k = i % 3
        ctx.set_source_rgba(*cols[i % len(cols)], a)
        if k == 0: ctx.rectangle(-9, -5, 18, 10); ctx.fill()
        elif k == 1: ctx.arc(0, 0, 7, 0, 2 * math.pi); ctx.fill()
        else: star_path(ctx, 0, 0, 12); ctx.fill()
        ctx.restore()


def note(ctx, x, y, s=1.0, col=WHITE, alpha=1.0, rot=0.0, double=False):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); sscale(ctx, s, s)
    ctx.set_source_rgba(*col, alpha)
    ctx.save(); sscale(ctx, 1.3, 1); ctx.arc(0, 0, 14, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.rectangle(14, -60, 6, 60); ctx.fill()
    if double:
        ctx.save(); ctx.translate(46, -12); sscale(ctx, 1.3, 1); ctx.arc(0, 0, 14, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        ctx.rectangle(60, -72, 6, 60); ctx.fill()
        ctx.new_path(); ctx.move_to(14, -60); ctx.line_to(66, -72); ctx.line_to(66, -60); ctx.line_to(14, -48); ctx.close_path(); ctx.fill()
    else:
        ctx.new_path(); ctx.move_to(20, -60); ctx.curve_to(40, -50, 44, -30, 34, -18); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()


def motion_lines(ctx, x, y, ang, n=3, l=50, gap=22, col=WHITE, alpha=1.0, lw=7):
    for i in range(n):
        o = (i - (n - 1) / 2) * gap
        px, py = x - math.sin(ang) * o, y + math.cos(ang) * o
        line(ctx, px, py, px - math.cos(ang) * l, py - math.sin(ang) * l, col, lw, alpha)


def panel(ctx, x, y, w, h, fill=WHITE, alpha=1.0, r=36, s=1.0):
    ctx.save(); ctx.translate(x, y); sscale(ctx, s, s)
    rrect(ctx, -w / 2 + 8, -h / 2 + 12, w, h, r); ctx.set_source_rgba(*NAVY, 0.3 * alpha); ctx.fill()
    rrect(ctx, -w / 2, -h / 2, w, h, r); fill_stroke(ctx, fill, NAVY, LW, alpha)
    ctx.restore()


def sscale(ctx, sx, sy):
    def f(v): return v if abs(v) > 1e-4 else (1e-4 if v >= 0 else -1e-4)
    cairo.Context.scale(ctx, f(sx), f(sy))
