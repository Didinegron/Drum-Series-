"""Anatomically-shaped cartoon hands (skin tone, jointed fingers, nails)."""
import math
import cairo
from lib import *

SKIN = (0.98, 0.80, 0.64)
SKIN_D = (0.86, 0.62, 0.47)
NAIL = (1.0, 0.90, 0.86)
OUT = NAVY


def _stroke_path(ctx, pts, width, col, alpha=1.0, outline=True):
    """Smooth finger: Catmull-Rom through pts, drawn as a thick round stroke with outline."""
    def path():
        ctx.new_path(); ctx.move_to(*pts[0])
        for i in range(len(pts) - 1):
            p0 = pts[i - 1] if i > 0 else pts[i]
            p1, p2 = pts[i], pts[i + 1]
            p3 = pts[i + 2] if i + 2 < len(pts) else p2
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            ctx.curve_to(*c1, *c2, *p2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if outline:
        path(); ctx.set_source_rgba(*OUT, alpha); ctx.set_line_width(width + 2 * 5); ctx.stroke()
    path(); ctx.set_source_rgba(*col, alpha); ctx.set_line_width(width); ctx.stroke()


def _nail(ctx, x, y, ang, w=16, h=12, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
    rrect(ctx, -w / 2, -h / 2, w, h, h / 2.2); fill_stroke(ctx, NAIL, OUT, 3, alpha)
    ctx.restore()


def _crease(ctx, x, y, r, a0, a1, alpha=1.0):
    ctx.new_path(); ctx.arc(x, y, r, a0, a1)
    ctx.set_source_rgba(*SKIN_D, alpha); ctx.set_line_width(4); ctx.stroke()


def _lerp_pts(a, b, t):
    return [(lerp(p[0], q[0], t), lerp(p[1], q[1], t)) for p, q in zip(a, b)]


def hand_grip(ctx, x, y, ang, curl=1.0, squeeze=0.0, thumb_top=False, t=0.0, cuff=PINK,
              alpha=1.0, flip=False, splay=0.0, scale=1.0):
    """Side view (thumb side) of a hand holding a stick that runs along +x through (x,y).
    Thumb lies along the side of the stick pointing at the tip; index curls under;
    middle/ring/pinky wrap loosely (curl=1) or stick out (curl=0)."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); sscale(ctx, scale, -scale if flip else scale)
    if squeeze: ctx.translate(wob(t, 22, 3 * squeeze), 0)
    skin = lerpc(SKIN, (0.98, 0.66, 0.62), 0.6 * squeeze)
    tight = squeeze
    # sleeve
    ctx.save(); ctx.translate(-195, -62); ctx.rotate(-0.42)
    rrect(ctx, -70, -52, 135, 104, 26); fill_stroke(ctx, cuff, OUT, LW, alpha)
    ctx.restore()
    # back of hand / palm mass (stick hidden behind it)
    ctx.new_path()
    ctx.move_to(-175, -50)
    ctx.curve_to(-140, -72, -70, -78, -28, -58)      # top edge to index knuckle
    ctx.curve_to(-8, -48, 2, -22, -4, 2)             # front, down to stick
    ctx.curve_to(-20, 40, -70, 62, -120, 62)         # under side (finger bases)
    ctx.curve_to(-150, 62, -172, 50, -178, 30)
    ctx.close_path(); fill_stroke(ctx, skin, OUT, LW, alpha)
    # knuckle bumps / creases on back of hand
    for i, kx in enumerate((-40, -70, -100)):
        _crease(ctx, kx, -48 + i * 2, 12, math.pi * 1.15, math.pi * 1.85, alpha)
    # pinky -> ring -> middle -> index, back to front (index nearest the tip side)
    fingers = [(-112, 24), (-82, 27), (-50, 30)]  # base x, width
    for i, (bx, fw) in enumerate(fingers):
        k = (2 - i) * 4
        wrapped = [(bx, 26), (bx + 24, 46 - k * .5), (bx + 22, 70 - k), (bx + 6, 80 - k)]
        if tight:
            wrapped = [(bx, 26), (bx + 20, 42), (bx + 16, 62 - k * .5), (bx + 2, 66 - k * .5)]
        a = 0.62 + 0.22 * splay * (2 - i)
        out = [(bx, 26), (bx + 34 * math.cos(a), 26 + 40 * math.sin(a)), (bx + 68 * math.cos(a), 26 + 80 * math.sin(a)),
               (bx + 98 * math.cos(a), 26 + 116 * math.sin(a))]
        pts = _lerp_pts(out, wrapped, smooth(curl))
        _stroke_path(ctx, pts, fw, skin, alpha)
        d = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
        tx, ty = pts[-1]
        _nail(ctx, tx + 2 * math.cos(d) - 5 * math.sin(d), ty + 2 * math.sin(d) + 5 * math.cos(d) * 0, d, 13, 10, alpha)
    # index finger: curls under the stick, frontmost
    idx = [(-14, 8), (20, 26), (30, 54), (14, 76)]
    if tight: idx = [(-14, 8), (16, 22), (22, 46), (8, 60)]
    _stroke_path(ctx, idx, 32, skin, alpha)
    d = math.atan2(idx[-1][1] - idx[-2][1], idx[-1][0] - idx[-2][0])
    _nail(ctx, idx[-1][0] + 2 * math.cos(d), idx[-1][1] + 2 * math.sin(d), d, 15, 11, alpha)
    # thumb
    if thumb_top:
        th = [(-120, -40), (-60, -62), (-8, -54), (22, -32)]
        _stroke_path(ctx, th, 32, skin, alpha)
        _crease(ctx, -40, -60, 12, 0.2, 1.4, alpha)
        _nail(ctx, 20, -40, 0.75, 18, 13, alpha)
    else:
        th = [(-130, -22), (-70, -24), (-15, -14), (32, -8)]
        _stroke_path(ctx, th, 32, skin, alpha)
        _crease(ctx, -50, -20, 13, -0.9, 0.9, alpha)
        _nail(ctx, 26, -14, 0.08, 20, 13, alpha)
    if tight:
        for kx in (-40, -70, -100):
            ellipse(ctx, kx, -52, 8, 4, (1, 1, 1), None, alpha=0.7 * alpha)
    if squeeze > 0.3:
        for k in range(3):
            a = -1.9 + k * 0.5
            r1, r2 = 125, 155 + wob(t, 6, 8)
            line(ctx, -60 + r1 * math.cos(a), r1 * math.sin(a), -60 + r2 * math.cos(a), r2 * math.sin(a), RED, 6, alpha * squeeze)
    ctx.restore()


def hand_point(ctx, x, y, ang=0, alpha=1.0, cuff=TEAL, scale=1.0):
    """Fist with index finger pointing up; fingertip at (x,y)."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); sscale(ctx, scale, scale)
    rrect(ctx, -52, 190, 104, 70, 22); fill_stroke(ctx, cuff, OUT, LW, alpha)
    # index (behind fist top)
    _stroke_path(ctx, [(-14, 120), (-12, 70), (-10, 12)], 34, SKIN, alpha)
    _crease(ctx, -11, 70, 12, 0.3, 2.8, alpha)
    # fist
    rrect(ctx, -70, 90, 135, 120, 48); fill_stroke(ctx, SKIN, OUT, LW, alpha)
    for i in range(3):
        _stroke_path(ctx, [(10 + i * 2, 110 + i * 30), (52, 112 + i * 30), (40, 132 + i * 30)], 26, SKIN, alpha)
        _nail(ctx, 34, 132 + i * 30, math.pi * 0.9, 12, 9, alpha)
    # thumb across the front
    _stroke_path(ctx, [(-62, 150), (-30, 128), (8, 118)], 30, SKIN, alpha)
    _nail(ctx, 2, 116, -0.3, 15, 11, alpha)
    ctx.restore()


def hand_thumbsup(ctx, x, y, s=1.0, alpha=1.0, rot=0.0, cuff=GREEN):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); sscale(ctx, s, s)
    rrect(ctx, -62, 70, 96, 62, 20); fill_stroke(ctx, cuff, OUT, LW, alpha)
    rrect(ctx, -78, -40, 140, 118, 44); fill_stroke(ctx, SKIN, OUT, LW, alpha)
    _stroke_path(ctx, [(-40, -30), (-36, -80), (-30, -122)], 40, SKIN, alpha)
    _nail(ctx, -20, -112, -1.45, 22, 15, alpha)
    for i in range(4):
        _stroke_path(ctx, [(0, -22 + i * 26), (58, -18 + i * 26), (48, -2 + i * 26)], 24, SKIN, alpha)
    ctx.restore()


def hand_cup(ctx, alpha=1.0):
    """Cupped open hand (palm up) centred at origin, for the bird."""
    ctx.new_path(); ctx.move_to(-230, -20); ctx.curve_to(-220, 190, 220, 190, 230, -20)
    ctx.curve_to(150, 40, -150, 40, -230, -20); ctx.close_path(); fill_stroke(ctx, SKIN, OUT, LW, alpha)
    _crease(ctx, 0, -40, 150, 0.6, 2.5, alpha)
    for k in range(4):
        bx = -175 + k * 62
        top = -70 - 12 * (1.5 - abs(k - 1.5))
        _stroke_path(ctx, [(bx, 10), (bx - 6, (10 + top) / 2), (bx + 6, top)], 40 - k * 2, SKIN, alpha)
        _nail(ctx, bx + 6, top - 4, -1.4, 20, 14, alpha)
    _stroke_path(ctx, [(205, 10), (235, -60), (215, -125)], 40, SKIN, alpha)
    _nail(ctx, 214, -126, -1.75, 22, 15, alpha)
