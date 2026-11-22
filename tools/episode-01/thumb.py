import cairo, math, sys
from lib import *
from photo import photo_card
PH='/tmp/claude-0/-home-user-Tinder-Nope-TinDOG/181f8862-8b46-53a1-808e-9ac6a1f21b55/scratchpad/photos/'
Wt,Ht=1280,720; S=2
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,Wt*S,Ht*S); ctx=cairo.Context(surf); sscale(ctx,S,S)
fo=cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); ctx.set_font_options(fo)
g=cairo.RadialGradient(380,360,60,380,360,1100); g.add_color_stop_rgb(0,.25,.66,1); g.add_color_stop_rgb(1,.04,.33,.88); ctx.set_source(g); ctx.paint()
ctx.save(); ctx.translate(330,380)
for i in range(18):
    a=i*2*math.pi/18; ctx.new_path(); ctx.move_to(0,0); ctx.arc(0,0,1600,a,a+math.pi/36); ctx.close_path(); ctx.set_source_rgba(1,1,1,.07); ctx.fill()
ctx.restore()
# mascot with sticks + burst (left)
burst(ctx,330,400,250,YELLOW,NAVY,16,.2); burst(ctx,330,400,195,ORANGE,None,16,-.1)
for sgn in (-1,1): stick(ctx,330-sgn*210,620,-math.pi/2+sgn*.55,470,30,face="smile",t=1.0)
drum(ctx,330,420,1.05,1.0,mouth=.9,look=.4)
for (x,y,r) in [(90,140,26),(560,610,22),(95,640,18)]: star(ctx,x,y,r,YELLOW,NAVY,4)
# right: wrong vs right photos
photo_card(ctx,PH+'r1_deathgrip.jpg',790,520,250,250,rot=-.07,tag="",focus=(.5,.62))
photo_card(ctx,PH+'p5_vgrip.png',1085,515,250,250,rot=.06,tag="",focus=(.5,.5))
cross(ctx,880,420,.62); check(ctx,1180,415,.62)
ctx.save(); ctx.translate(937,520)
ctx.new_path(); ctx.move_to(-26,-14); ctx.line_to(4,-14); ctx.line_to(4,-32); ctx.line_to(34,0); ctx.line_to(4,32); ctx.line_to(4,14); ctx.line_to(-26,14); ctx.close_path()
fill_stroke(ctx,YELLOW,NAVY,6); ctx.restore()
# headline
text(ctx,"HOLD STICKS",940,105,96,WHITE,NAVY,lw=18,rot=-.03)
text(ctx,"LIKE A PRO!",945,220,104,YELLOW,NAVY,lw=18,rot=-.03)
label(ctx,"EPISODE 1",650,315,34,PINK,WHITE,rot=-.06)
label(ctx,"IN 5 MIN",1120,315,34,GREEN,WHITE,rot=.05)
surf.write_to_png('/tmp/_thumb_big.png')
