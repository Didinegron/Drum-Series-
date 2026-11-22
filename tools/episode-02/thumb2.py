import cairo, math, sys
sys.path.insert(0,'.')
import ep2
from lib import *
Wt,Ht=1280,720; S=2
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,Wt*S,Ht*S); ctx=cairo.Context(surf); sscale(ctx,S,S)
fo=cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); ctx.set_font_options(fo)
g=cairo.RadialGradient(400,420,60,400,420,1150); g.add_color_stop_rgb(0,.25,.66,1); g.add_color_stop_rgb(1,.04,.33,.88); ctx.set_source(g); ctx.paint()
ctx.save(); ctx.translate(400,440)
for i in range(18):
    a=i*2*math.pi/18; ctx.new_path(); ctx.move_to(0,0); ctx.arc(0,0,1600,a,a+math.pi/36); ctx.close_path(); ctx.set_source_rgba(1,1,1,.07); ctx.fill()
ctx.restore()
burst(ctx,410,450,330,YELLOW,NAVY,18,.2); burst(ctx,410,450,260,ORANGE,None,18,-.1)
ep2.full_kit(ctx,410,470,.52,1.0,hits={'crash':.6})
# headline
text(ctx,"MEET THE",975,95,92,WHITE,NAVY,lw=18,rot=-.03)
text(ctx,"DRUM KIT!",980,205,112,YELLOW,NAVY,lw=20,rot=-.03)
label(ctx,"EPISODE 2",780,300,34,PINK,WHITE,rot=-.06); label(ctx,"IN 5 MIN",1130,300,34,GREEN,WHITE,rot=.05)
# sound words
for (s,x,y,c,r) in [("BOOM!",880,430,ORANGE,-.08),("CRACK!",1120,440,RED,.07),("TICK!",880,560,TEAL,.06),("CRASH!",1120,575,PINK,-.06)]:
    ctx.save(); ctx.translate(x,y); ctx.rotate(r); burst(ctx,0,0,92,WHITE,NAVY,12); text(ctx,s,0,0,44,c,NAVY,lw=9); ctx.restore()
label(ctx,"6 PIECES",1000,670,36,YELLOW,NAVY,rot=-.02)
surf.write_to_png('/tmp/_t2.png')
