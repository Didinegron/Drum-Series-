"""Episode 3 thumbnail (1280x720). usage: python3 thumb3.py out.png"""
import cairo, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ep3
from lib import *
Wt, Ht = 1280, 720; S = 2
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, Wt * S, Ht * S); ctx = cairo.Context(surf); sscale(ctx, S, S)
fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); ctx.set_font_options(fo)
g = cairo.RadialGradient(400, 420, 60, 400, 420, 1150); g.add_color_stop_rgb(0, .25, .66, 1); g.add_color_stop_rgb(1, .04, .33, .88); ctx.set_source(g); ctx.paint()
ctx.save(); ctx.translate(400, 440)
for i in range(18):
    a = i * 2 * math.pi / 18; ctx.new_path(); ctx.move_to(0, 0); ctx.arc(0, 0, 1600, a, a + math.pi / 36); ctx.close_path(); ctx.set_source_rgba(1, 1, 1, .07); ctx.fill()
ctx.restore()
burst(ctx, 400, 430, 330, YELLOW, NAVY, 18, .2); burst(ctx, 400, 430, 260, ORANGE, None, 18, -.1)
ep3.ep3_kit(ctx, 410, 450, .5, 1.52, bursts=False, stick_style="plan")          # t=1.55: hi-hat + snare sticks down on "crack"
for (s, x, y, c, r) in [("BOOM!", 575, 640, ORANGE, -.06), ("CRACK!", 255, 642, RED, .08), ("TICK!", 150, 175, TEAL, -.08)]:
    ctx.save(); ctx.translate(x, y); ctx.rotate(r); burst(ctx, 0, 0, 72, WHITE, NAVY, 12); text(ctx, s, 0, 0, 38, c, NAVY, lw=8); ctx.restore()
text(ctx, "YOUR FIRST", 965, 95, 88, WHITE, NAVY, lw=18, rot=-.03)
text(ctx, "ROCK BEAT!", 965, 205, 104, YELLOW, NAVY, lw=20, rot=-.03)
label(ctx, "EPISODE 3", 800, 300, 34, PINK, WHITE, rot=-.06); label(ctx, "IN 5 MIN", 1130, 300, 34, GREEN, WHITE, rot=.05)
ep3.beat_chart(ctx, 985, 500, 5.5, .43, band=False)                    # whole bar lit
label(ctx, "3 EASY LAYERS", 985, 665, 36, YELLOW, NAVY, rot=-.02)
surf.write_to_png(sys.argv[1])
