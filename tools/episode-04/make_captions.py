import json, re
W=json.load(open('words_final.json'))
KEY={"staff","lines","spaces","line","space","note","notes","snare","kick","hi-hat","x","clef","bar","bars","stem","boom","crack","tick","map","code","read","mistake","bonus","layer"}
iskey=lambda t: re.sub(r"[^a-z\-]","",t.lower()) in KEY
cues=[]; cur=[]
for i,w in enumerate(W):
    cur.append(w); nxt=W[i+1] if i+1<len(W) else None
    gap=(nxt['start']-w['end']) if nxt else 9
    if (w['text'][-1] in '.?!:' and (len(cur)>=4 or gap>0.5)) or len(cur)>=10 or (w['text'][-1]==',' and len(cur)>=7) or gap>0.9:
        cues.append(cur); cur=[]
if cur: cues.append(cur)
def lines(c):
    if len(c)<=5: return [c]
    tot=sum(len(w['text']) for w in c); acc=0
    for k,w in enumerate(c):
        acc+=len(w['text'])+1
        if acc>=tot/2: return [c[:k+1],c[k+1:]] if c[k+1:] else [c]
def ts(x):
    cs=int(round(x*100)); return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"
UP="&HFFE3CC&"; PAST="&HFFFFFF&"; ACT="&H33DBFF&"; KEYC="&H9E54FF&"; PASTKEY="&H33DBFF&"
out=["[Script Info]","Title: Episode 4 - How to read drum music (karaoke)","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","WrapStyle: 2","ScaledBorderAndShadow: yes","",
"[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Fun,Fredoka,66,&H00FFFFFF,&H00FFFFFF,&H004D1C17,&H804D1C17,-1,0,0,0,100,100,1,0,1,6,3,2,120,120,48,1","",
"[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
cj=[]
for ci,c in enumerate(cues):
    start=c[0]['start']; end=cues[ci+1][0]['start'] if ci+1<len(cues) else c[-1]['end']+0.6
    ls=lines(c); cj.append({"start":start,"end":end,"words":[dict(text=w['text'],start=w['start'],end=w['end'],line=li,key=iskey(w['text'])) for li,l in enumerate(ls) for w in l]})
    bounds=sorted(set([start]+[w['start'] for w in c]+[end]))
    for i in range(len(bounds)-1):
        a,b=bounds[i],bounds[i+1]
        if b-a<0.005: continue
        parts=[]
        for li,l in enumerate(ls):
            if li: parts.append("\\N")
            for k,w in enumerate(l):
                if k: parts.append(" ")
                ke=iskey(w['text'])
                if w['start']<=a<max(w['end'],w['start']+0.05): parts.append("{\\c"+(KEYC if ke else ACT)+"\\bord7}"+w['text']+"{\\bord6}")
                elif a>=w['end']: parts.append("{\\c"+(PASTKEY if ke else PAST)+"}"+w['text'])
                else: parts.append("{\\c"+UP+"}"+w['text'])
        out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Fun,,0,0,0,,"+("{\\fad(120,0)}" if i==0 else "")+"".join(parts))
open('episode4_karaoke_DRAFT.ass','w').write("\n".join(out)+"\n"); json.dump(cj,open('cues.json','w'))
print('cues',len(cues),'events',len(out)-15)
