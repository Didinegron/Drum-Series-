import cairo, math
from PIL import Image
from lib import *
_cache = {}
def load(path):
    if path not in _cache:
        im = Image.open(path).convert('RGBA'); w, h = im.size
        r, g, b, a = im.split(); data = bytearray(Image.merge('RGBA', (b, g, r, a)).tobytes())
        surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
        _cache[path] = (surf, w, h, data)
    return _cache[path]

def photo_card(ctx, path, cx, cy, w, h, rot=0.0, scale=1.0, zoom=1.0, focus=(0.5, 0.5), tag="REAL LIFE", t=0.0):
    """Framed photo, cover-fit into w x h, zoom about focus point (fractions of image)."""
    if scale <= 0.001: return
    surf, iw, ih, _ = load(path)
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); sscale(ctx, scale, scale)
    b = 18
    rrect(ctx, -w / 2 - b + 10, -h / 2 - b + 14, w + 2 * b, h + 2 * b, 34); ctx.set_source_rgba(*NAVY, .35); ctx.fill()
    rrect(ctx, -w / 2 - b, -h / 2 - b, w + 2 * b, h + 2 * b, 34); fill_stroke(ctx, WHITE, NAVY, LW)
    ctx.save(); rrect(ctx, -w / 2, -h / 2, w, h, 20); ctx.clip()
    s = max(w / iw, h / ih) * zoom
    fx, fy = focus[0] * iw, focus[1] * ih
    # keep focus point near centre but inside bounds
    ox = clamp(-fx * s, w / 2 - iw * s, -w / 2) if iw * s > w else -iw * s / 2
    oy = clamp(-fy * s, h / 2 - ih * s, -h / 2) if ih * s > h else -ih * s / 2
    ctx.translate(ox, oy); sscale(ctx, s, s)
    ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint()
    ctx.restore()
    if tag:
        label(ctx, tag, -w / 2 + 120, -h / 2 - 8, 30, RED, WHITE, rot=-0.05)
    ctx.restore()

def img_to_card(px, py, path, cx, cy, w, h, zoom=1.0, focus=(0.5, 0.5)):
    """map image pixel coords -> canvas coords for an unrotated card (for arrows)."""
    surf, iw, ih, _ = load(path)
    s = max(w / iw, h / ih) * zoom
    fx, fy = focus[0] * iw, focus[1] * ih
    ox = clamp(-fx * s, w / 2 - iw * s, -w / 2) if iw * s > w else -iw * s / 2
    oy = clamp(-fy * s, h / 2 - ih * s, -h / 2) if ih * s > h else -ih * s / 2
    return cx + ox + px * s, cy + oy + py * s


# ---------------- video clips (frame sequences) ----------------
import os as _os, json as _json
CLIPDIR = '/tmp/claude-0/-home-user-Tinder-Nope-TinDOG/181f8862-8b46-53a1-808e-9ac6a1f21b55/scratchpad/vid/clips'
_vcache = {}
def clip_frame_path(name, t_local, speed=1.0, mode="loop"):
    n = len([f for f in _os.listdir(_os.path.join(CLIPDIR, name)) if f.endswith('.jpg')]) if name not in _vcache else _vcache[name]
    _vcache[name] = n
    i = int(max(0.0, t_local) * 30 * speed)
    if mode == "loop": i %= n
    elif mode == "pingpong":
        i %= (2 * n - 2); i = i if i < n else 2 * n - 2 - i
    else: i = min(i, n - 1)
    return _os.path.join(CLIPDIR, name, f'{i:04d}.jpg')

def video_card(ctx, name, t_local, cx, cy, w, h, rot=0.0, scale=1.0, zoom=1.0, focus=(.5, .5), tag="REAL LIFE", t=0.0, speed=1.0, mode="loop"):
    path = clip_frame_path(name, t_local, speed, mode)
    _cache.pop(path, None)
    photo_card(ctx, path, cx, cy, w, h, rot=rot, scale=scale, zoom=zoom, focus=focus, tag=tag, t=t)
    _cache.pop(path, None)
