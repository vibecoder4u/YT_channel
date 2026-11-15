#!/usr/bin/env python3
"""Long-form illustrated educational video renderer.

Each scene's visual duration is derived from its generated narration audio, so
the animation never advances on an unrelated fixed timer.
"""
import argparse
import asyncio
import json
import math
import os
import shutil
import subprocess
import textwrap
import html
import io
from pathlib import Path

import cairosvg

from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
BG = (247, 248, 244)
INK = (27, 38, 53)
MUTED = (103, 117, 132)
PALETTE = [(42, 163, 145), (244, 180, 62), (80, 135, 211), (226, 112, 92)]
SVG_CACHE = {}


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rounded(draw, xy, radius=18, fill=(255, 255, 255), outline=None, width=2):
    draw.rounded_rectangle(tuple(int(v) for v in xy), radius=radius, fill=fill, outline=outline, width=width)


def stroke(draw, points, fill=INK, width=7):
    draw.line(points, fill=fill, width=width, joint="curve")


def accent_rgb(value):
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid accent color: {value}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def wrap(text, width=34):
    return textwrap.wrap(str(text), width=width) or [""]


def arrow(draw, start, end, color, width=6):
    stroke(draw, [start, end], color, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 17
    p1 = (end[0] - size * math.cos(angle - .55), end[1] - size * math.sin(angle - .55))
    p2 = (end[0] - size * math.cos(angle + .55), end[1] - size * math.sin(angle + .55))
    draw.polygon([end, p1, p2], fill=color)


def draw_character(draw, action, x, y, t, scale=1.0, color=INK):
    """Thin, expressive, hand-drawn stick figure with articulated limbs."""
    s = scale
    x = int(x + math.sin(t * 0.7) * 4 * s)
    y = int(y + math.sin(t * 3.0) * 2.5 * s)
    line = max(3, int(5 * s))
    joint_r = max(4, int(5 * s))
    head_r = int(29 * s)
    head_x = x + int(math.sin(t * 0.55) * 3 * s)
    head_y = y - int(145 * s)
    # Ground contact and a light-grey, expressive head.
    draw.ellipse((x-int(48*s), y+int(5*s), x+int(48*s), y+int(14*s)), fill=(226,231,231))
    draw.ellipse((head_x-head_r, head_y-head_r, head_x+head_r, head_y+head_r),
                 fill=(232,234,235), outline=color, width=max(2, int(3*s)))
    # Neck and central spine: no shirt, trousers, filled torso or body silhouette.
    neck = (x, y-int(109*s))
    shoulder = (x, y-int(99*s))
    hip = (x+int(math.sin(t*1.1)*3*s), y-int(8*s))
    stroke(draw, [neck, shoulder, hip], color, line)
    draw.ellipse((neck[0]-4, neck[1]-4, neck[0]+4, neck[1]+4), fill=color)
    # Face direction, blinking, brows and a speech mouth.
    look = 3 if action in ("point", "demonstrate", "walk") else int(math.sin(t*1.4)*3)
    blink = (t % 4.3) < 0.11
    for ex in (head_x-int(11*s), head_x+int(11*s)):
        brow_y = head_y-int(9*s) + (int(2*s) if action == "think" else 0)
        draw.arc((ex-int(6*s), brow_y-int(5*s), ex+int(6*s), brow_y+int(3*s)),
                 190, 345, fill=color, width=max(2, int(2*s)))
        if blink:
            draw.line((ex-int(4*s), head_y, ex+int(4*s), head_y), fill=color, width=2)
        else:
            draw.ellipse((ex-int(4*s), head_y-int(3*s), ex+int(4*s), head_y+int(5*s)),
                         fill=(255,255,255), outline=color, width=1)
            draw.ellipse((ex+look-1, head_y, ex+look+2, head_y+3), fill=color)
    draw.arc((head_x-int(7*s), head_y+int(10*s), head_x+int(7*s), head_y+int(21*s)),
             5, 175, fill=(125,65,63), width=max(2, int(2*s)))
    # Small head tilt on thinking / listening beats.
    if action == "think":
        draw.arc((head_x-int(19*s), head_y-int(20*s), head_x+int(19*s), head_y+int(17*s)),
                 195, 260, fill=color, width=2)
    def dot(p, r=joint_r):
        rr=max(3,int(r*s/1.0))
        draw.ellipse((p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr), fill=(232,234,235), outline=color, width=2)
    def hand(p, direction=1):
        rr=max(4,int(5*s))
        draw.ellipse((p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr), fill=(232,234,235), outline=color, width=2)
        # Four fine fingers and a thumb make pointing and open-hand gestures readable.
        if action in ("point", "demonstrate") and direction > 0:
            end=(p[0]+int(19*s),p[1]-int(4*s))
            stroke(draw,[p,end],color,max(2,int(3*s)))
            for k in range(3):
                q=(p[0]+int((7+k*3)*s),p[1]+int((7+k*2)*s))
                stroke(draw,[p,q],color,max(1,int(2*s)))
        else:
            for k in range(3):
                q=(p[0]+int((k-1)*5*s),p[1]+int(11*s))
                stroke(draw,[p,q],color,max(1,int(2*s)))
    ls=(x-int(17*s),shoulder[1]+int(2*s))
    rs=(x+int(17*s),shoulder[1]+int(2*s))
    wave=math.sin(t*3.6)
    if action == "think":
        elbows=[(x-int(34*s),y-int(55*s)),(x+int(25*s),head_y+int(24*s))]
        wrists=[(x-int(45*s),y-int(32*s)),(x+int(5*s),head_y+int(17*s))]
    elif action in ("point","demonstrate"):
        elbows=[(x-int(39*s),y-int(55*s)),(x+int(43*s),y-int(83*s))]
        wrists=[(x-int(49*s),y-int(29*s)),(x+int(105*s),y-int(111*s)+int(wave*5*s))]
    elif action == "celebrate":
        elbows=[(x-int(39*s),y-int(119*s)),(x+int(39*s),y-int(119*s))]
        wrists=[(x-int(62*s),y-int(145*s)),(x+int(62*s),y-int(145*s))]
    elif action == "walk":
        swing=math.sin(t*5.2)*20*s
        elbows=[(x-int(38*s),y-int(52*s)+int(swing*.3)),(x+int(38*s),y-int(52*s)-int(swing*.3))]
        wrists=[(x-int(49*s),y-int(24*s)+int(swing)),(x+int(49*s),y-int(24*s)-int(swing))]
    elif action == "type":
        elbows=[(x-int(36*s),y-int(47*s)),(x+int(36*s),y-int(47*s))]
        wrists=[(x-int(42*s),y-int(17*s)+int(wave*3*s)),(x+int(42*s),y-int(17*s)-int(wave*3*s))]
    else:
        elbows=[(x-int(39*s),y-int(52*s)),(x+int(39*s),y-int(56*s)+int(wave*4*s))]
        wrists=[(x-int(49*s),y-int(23*s)),(x+int(58*s),y-int(91*s)+int(wave*9*s))]
    for idx,(sh,el,wr) in enumerate(((ls,elbows[0],wrists[0]),(rs,elbows[1],wrists[1]))):
        stroke(draw,[sh,el,wr],color,line)
        dot(el)
        hand(wr, 1 if idx else -1)
    # Hip, knees, ankles and feet are independent line segments with visible joints.
    if action == "walk":
        stride=math.sin(t*5.2)*27*s
        knees=[(x-int(17*s)+int(stride*.45),y+int(34*s)),
               (x+int(17*s)-int(stride*.45),y+int(34*s))]
        ankles=[(x-int(22*s)+int(stride),y+int(82*s)),
                (x+int(22*s)-int(stride),y+int(82*s))]
    elif action == "celebrate":
        knees=[(x-int(20*s),y+int(35*s)),(x+int(20*s),y+int(35*s))]
        ankles=[(x-int(31*s),y+int(82*s)),(x+int(31*s),y+int(82*s))]
    else:
        knees=[(x-int(18*s),y+int(34*s)),(x+int(18*s),y+int(34*s))]
        ankles=[(x-int(22*s),y+int(82*s)),(x+int(22*s),y+int(82*s))]
    stroke(draw,[hip,knees[0],ankles[0]],color,line)
    stroke(draw,[hip,knees[1],ankles[1]],color,line)
    for knee,ankle in zip(knees,ankles):
        dot(knee)
        stroke(draw,[ankle,(ankle[0]+int(12*s),ankle[1]+int(3*s))],color,line)
        draw.ellipse((ankle[0]+int(8*s),ankle[1],ankle[0]+int(25*s),ankle[1]+int(7*s)),
                     fill=(232,234,235), outline=color, width=2)

def draw_flow(draw, items, x0, y, width, color, t):
    items = items[:5]
    if not items: return
    gap = 18
    boxw = min(190, (width - gap*(len(items)-1)) // len(items))
    total = boxw*len(items)+gap*(len(items)-1)
    x = x0 + (width-total)//2
    for i, label in enumerate(items):
        cx=x+boxw//2
        active = (int(t * 0.85) % len(items)) == i
        rounded(draw,(x,y-43,x+boxw,y+43),16,(235,247,244) if active else (255,255,255),color if active else (205,215,218),4 if active else 2)
        lines=wrap(label,15)[:2]
        for j,txt in enumerate(lines):
            draw.text((cx,y+(j-(len(lines)-1)/2)*25),txt,font=font(18,True),fill=INK,anchor="mm")
        if i < len(items)-1:
            arrow(draw,(x+boxw+3,y),(x+boxw+gap-3,y),color,4)
        if active:
            draw.ellipse((cx-7,y+54,cx+7,y+68),fill=color)
        x += boxw+gap


def draw_timeline(draw, items, x0, y, width, color, t):
    items=items[:5]
    if not items: return
    left=x0+35; right=x0+width-35
    if len(items)>1: arrow(draw,(left,y),(right,y),color,5)
    for i,label in enumerate(items):
        x=left if len(items)==1 else left+(right-left)*i/(len(items)-1)
        draw.ellipse((x-12,y-12,x+12,y+12),fill=color,outline=INK,width=2)
        lines=wrap(label,15)[:2]
        yy=y+35 if i%2==0 else y-58
        for j,txt in enumerate(lines):
            draw.text((x,yy+j*22),txt,font=font(16,True),fill=INK,anchor="mm")
    # A moving marker makes the timeline feel like an unfolding explanation.
    progress=(t*0.12)%1.0
    marker_x=left+(right-left)*progress
    draw.ellipse((marker_x-10,y-10,marker_x+10,y+10),fill=(255,255,255),outline=INK,width=3)


def draw_visual(draw, scene, t, w, h, color):
    kind=scene.get("visual","concept")
    area=(int(w*.36),int(h*.18),int(w*.94),int(h*.65))
    x0,y0,x1,y1=area
    rounded(draw,area,24,(255,255,255),(226,231,234),2)
    if kind in ("flow","process"):
        draw_flow(draw,scene.get("items",[]),x0+12,(y0+y1)//2,x1-x0-24,color,t)
    elif kind=="timeline":
        draw_timeline(draw,scene.get("items",[]),x0+8,(y0+y1)//2,x1-x0-16,color,t)
    elif kind=="compare":
        cols=scene.get("items",["Before","After"])[:2]
        for i,label in enumerate(cols):
            xx=x0+int((i+.5)*(x1-x0)/2)
            rounded(draw,(xx-125,y0+55,xx+125,y1-35),18,(247,249,250),color,3)
            draw.text((xx,(y0+y1)//2),label,font=font(23,True),fill=INK,anchor="mm")
    elif kind=="cycle":
        labels=scene.get("items",["Notice","Connect","Practice","Recall"])[:4]
        cx=(x0+x1)//2; cy=(y0+y1)//2
        positions=[]
        for i,label in enumerate(labels):
            a=-math.pi/2+i*2*math.pi/len(labels)
            positions.append((int(cx+145*math.cos(a)),int(cy+105*math.sin(a))))
        for i,p in enumerate(positions):
            q=positions[(i+1)%len(positions)]
            arrow(draw,p,q,color,4)
        for p,label in zip(positions,labels):
            rounded(draw,(p[0]-75,p[1]-27,p[0]+75,p[1]+27),14,(255,255,255),color,3)
            draw.text(p,label,font=font(17,True),fill=INK,anchor="mm")
    elif kind=="stat":
        vals=scene.get("values",[35,65,90,55])[:5]
        labels=scene.get("items",["A","B","C","D"])[:len(vals)]
        base=y1-65; maxv=max(vals) or 1
        bw=min(68,(x1-x0-70)//max(1,len(vals)))
        reveal=min(1.0,max(0.0,t/2.5))
        for i,v in enumerate(vals):
            xx=x0+48+i*(bw+22)
            stagger=max(0.0,min(1.0,(t-i*0.32)/1.1))
            bh=int((y1-y0-145)*v/maxv*min(reveal,stagger))
            rounded(draw,(xx,base-bh,xx+bw,base),10,color)
            draw.text((xx+bw//2,base+22),labels[i] if i<len(labels) else str(i+1),font=font(15,True),fill=INK,anchor="mm")
    elif kind=="network":
        nodes=scene.get("items",["Input","Signal","Response","Feedback"])[:5]
        draw_flow(draw,nodes,x0+8,(y0+y1)//2,x1-x0-16,color,t)
    else:
        title=scene.get("visual_title",scene.get("caption","A useful idea"))
        draw.text(((x0+x1)//2,(y0+y1)//2),title,font=font(28,True),fill=INK,anchor="mm")



def draw_svg_diagram(image, scene, t, w, h, color):
    """Render a vivid, layered SVG infographic and animate its build in stages."""
    x0, y0 = int(w * .36), int(h * .18)
    box_w, box_h = int(w * .58), int(h * .47)
    items = [str(v) for v in scene.get("items", [])[:5]] or ["Observe", "Understand", "Apply"]
    kind = scene.get("visual", "flow")
    title = html.escape(str(scene.get("diagram_title", scene.get("visual_title", scene.get("heading", "How it works")))))
    subtitle = html.escape(str(scene.get("diagram_subtitle", scene.get("caption", "A process in motion"))))
    colors = ["#20A68A", "#3979D8", "#F2A93B", "#E66D59", "#8067C8"]
    stage = min(len(items), max(1, int(max(0, t) / 1.7) + 1))
    cache_key = (id(scene), kind, stage, tuple(items), title, subtitle)
    png = SVG_CACHE.get(cache_key)
    if png is None:
        esc = html.escape
        parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="740" height="338" viewBox="0 0 740 338">',
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F2FAFF"/><stop offset="1" stop-color="#E8F7F0"/></linearGradient>',
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#31546B" flood-opacity=".14"/></filter>',
            '<marker id="arr" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#55758A"/></marker></defs>',
            '<rect x="2" y="2" width="736" height="334" rx="26" fill="url(#bg)"/>',
            '<circle cx="675" cy="56" r="62" fill="#BFE9E0" opacity=".55"/><circle cx="70" cy="290" r="74" fill="#C9E0FA" opacity=".38"/>',
            '<path d="M0 258 Q150 220 285 270 T560 258 T740 245 L740 338 L0 338Z" fill="#D8F0E8" opacity=".72"/>',
            f'<text x="30" y="39" font-family="DejaVu Sans" font-size="17" font-weight="700" fill="#31546B">{title[:52]}</text>',
            f'<text x="30" y="64" font-family="DejaVu Sans" font-size="11" fill="#638092">{subtitle[:78]}</text>',
        ]
        n = len(items)
        if kind == "cycle" and n >= 3:
            cx, cy, rx, ry = 370, 194, 245, 105
            coords = []
            for i in range(n):
                a = -math.pi / 2 + i * 2 * math.pi / n
                coords.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
            for i, (px, py) in enumerate(coords):
                qx, qy = coords[(i + 1) % n]
                parts.append(f'<path d="M {px:.1f} {py:.1f} L {qx:.1f} {qy:.1f}" stroke="#64879A" stroke-width="7" stroke-linecap="round" marker-end="url(#arr)" opacity=".8"/>')
            for i, ((cxn, cyn), label) in enumerate(zip(coords, items)):
                if i >= stage: continue
                fill = colors[i % len(colors)]
                parts.append(f'<g filter="url(#shadow)"><rect x="{cxn-79:.1f}" y="{cyn-28:.1f}" width="158" height="56" rx="18" fill="{fill}"/><circle cx="{cxn-52:.1f}" cy="{cyn:.1f}" r="15" fill="#FFFFFF" opacity=".24"/><text x="{cxn-52:.1f}" y="{cyn+5:.1f}" text-anchor="middle" font-family="DejaVu Sans" font-size="14" font-weight="700" fill="#FFFFFF">{i+1}</text><text x="{cxn+10:.1f}" y="{cyn+5:.1f}" text-anchor="middle" font-family="DejaVu Sans" font-size="13" font-weight="700" fill="#FFFFFF">{esc(label[:17])}</text></g>')
        elif kind == "compare" and n >= 2:
            for i, label in enumerate(items[:2]):
                xx = 42 + i * 340
                fill = colors[(i + 1) % len(colors)]
                parts.append(f'<g filter="url(#shadow)"><rect x="{xx}" y="105" width="300" height="174" rx="24" fill="{fill}"/><circle cx="{xx+150}" cy="151" r="27" fill="#FFFFFF" opacity=".22"/><text x="{xx+150}" y="161" text-anchor="middle" font-family="DejaVu Sans" font-size="27" font-weight="700" fill="#FFFFFF">{"A" if i == 0 else "B"}</text><text x="{xx+150}" y="218" text-anchor="middle" font-family="DejaVu Sans" font-size="18" font-weight="700" fill="#FFFFFF">{esc(label[:25])}</text><rect x="{xx+80}" y="239" width="140" height="8" rx="4" fill="#FFFFFF" opacity=".45"/></g>')
        else:
            gap, node_w = 20, min(128, (684 - 20 * (n - 1)) // n)
            total = node_w * n + gap * (n - 1)
            left = (740 - total) / 2
            for i, label in enumerate(items):
                cx = left + i * (node_w + gap)
                fill = colors[i % len(colors)]
                if i < n - 1:
                    parts.append(f'<path d="M{cx+node_w+3:.1f} 183 H{cx+node_w+gap-4:.1f}" stroke="#55758A" stroke-width="7" stroke-linecap="round" marker-end="url(#arr)"/>')
                if i >= stage: continue
                parts.append(f'<g filter="url(#shadow)"><rect x="{cx:.1f}" y="112" width="{node_w}" height="142" rx="19" fill="{fill}"/><circle cx="{cx+node_w/2:.1f}" cy="151" r="23" fill="#FFFFFF" opacity=".24"/><text x="{cx+node_w/2:.1f}" y="158" text-anchor="middle" font-family="DejaVu Sans" font-size="20" font-weight="700" fill="#FFFFFF">{i+1}</text>')
                words = textwrap.wrap(label, width=13)[:2]
                for j, word in enumerate(words):
                    parts.append(f'<text x="{cx+node_w/2:.1f}" y="{205+j*18}" text-anchor="middle" font-family="DejaVu Sans" font-size="12" font-weight="700" fill="#FFFFFF">{esc(word)}</text>')
                parts.append('</g>')
        parts.append('<rect x="28" y="309" width="684" height="7" rx="3.5" fill="#C4DCD9"/>')
        parts.append(f'<rect x="28" y="309" width="{684*stage/len(items):.1f}" height="7" rx="3.5" fill="#168F80"/>')
        parts.append('</svg>')
        png = cairosvg.svg2png(bytestring="".join(parts).encode("utf-8"), output_width=box_w, output_height=box_h)
        if len(SVG_CACHE) > 180:
            SVG_CACHE.clear()
        SVG_CACHE[cache_key] = png
    diagram = Image.open(io.BytesIO(png)).convert("RGB")
    image.paste(diagram, (x0, y0))
    if kind not in ("compare", "cycle") and len(items) > 1:
        progress = (t * .22) % 1.0
        mx = x0 + int(box_w * (.08 + .84 * progress))
        my = y0 + int(box_h * .53)
        d = ImageDraw.Draw(image)
        d.ellipse((mx-9, my-9, mx+9, my+9), fill=(255,255,255), outline=(30,94,112), width=3)


def make_frame(scene, frame, frames, size, scene_number, scene_count, title):
    w,h=size
    im=Image.new("RGB",size,BG)
    d=ImageDraw.Draw(im)
    color=accent_rgb(scene.get("accent","#2AA391"))
    d.rectangle((0,0,w,13),fill=color)
    # subtle editorial grid
    for xx in range(40,w,80):
        d.ellipse((xx,h-28,xx+3,h-25),fill=(222,227,225))
    d.text((int(w*.055),int(h*.085)),title[:58],font=font(21,True),fill=MUTED)
    d.text((int(w*.94),int(h*.085)),f"{scene_number:02d} / {scene_count:02d}",font=font(18,True),fill=MUTED,anchor="ra")
    headline=scene.get("heading",scene.get("caption",""))
    for i,txt in enumerate(wrap(headline,26)[:2]):
        d.text((int(w*.055),int(h*.25)+i*52),txt,font=font(36,True),fill=INK)
    t=frame/max(1,frames-1)*float(scene.get("_render_duration",scene.get("duration",5)))
    draw_svg_diagram(im,scene,t,w,h,color)
    action=scene.get("action","explain")
    # Change poses during long narration, not just the mouth or a bobbing sprite.
    if action == "explain":
        action = ("explain","point","walk","think","demonstrate")[int(t/5.5)%5]
    # Floating motion marks and drifting background particles add subtle life.
    for k in range(5):
        px=int(w*.42 + ((k*137 + t*19) % (w*.48)))
        py=int(h*.20 + (k%3)*int(h*.13) + math.sin(t*.8+k)*5)
        d.ellipse((px-3,py-3,px+3,py+3),fill=tuple(int(v*.72) for v in color))
    draw_character(d,action,int(w*.19),int(h*.77),t,1.08)
    # Phrase-level subtitles follow actual Edge TTS word-boundary timestamps.
    cues=scene.get("_caption_cues",[])
    active=next((c for c in cues if c["start"] <= t < c["end"]),None)
    if active is None and cues and t >= cues[-1]["end"]:
        active=cues[-1]
    rounded(d,(int(w*.34),int(h*.865),int(w*.94),int(h*.965)),16,(255,255,255),(218,225,228),2)
    subtitle=(active or {}).get("text","")
    lines=wrap(subtitle,48)[:2]
    for i,txt in enumerate(lines):
        d.text((int(w*.64),int(h*.905)+(i-(len(lines)-1)/2)*27),txt,
               font=font(21,True),fill=INK,anchor="mm")
    # continuous chapter progress
    prog=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rounded_rectangle((int(w*.055),int(h*.965),int(w*.94),int(h*.978)),radius=6,fill=(222,227,225))
    d.rounded_rectangle((int(w*.055),int(h*.965),int(w*(.055+.885*prog)),int(h*.978)),radius=6,fill=color)
    return im


async def synthesize(text, voice, path, rate):
    """Try Edge TTS with a hard timeout; fall back to local eSpeak audio."""
    boundaries = []

    async def collect_edge_audio():
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        with open(path, "wb") as audio:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    audio.write(chunk["data"])
                elif chunk.get("type") == "WordBoundary":
                    boundaries.append({
                        "text": chunk.get("text", ""),
                        "start": float(chunk.get("offset", 0)) / 10_000_000,
                        "duration": float(chunk.get("duration", 0)) / 10_000_000,
                    })

    try:
        await asyncio.wait_for(collect_edge_audio(), timeout=35)
        if path.stat().st_size == 0:
            raise RuntimeError("Edge TTS returned an empty audio file")
        return boundaries
    except Exception as exc:
        # Never leave a partial MP3 behind after a failed/timeout stream.
        path.unlink(missing_ok=True)
        print(f"Edge TTS unavailable ({type(exc).__name__}: {exc}); using local eSpeak fallback.", flush=True)

    text_file = path.with_suffix(".txt")
    wav_file = path.with_suffix(".wav")
    text_file.write_text(text, encoding="utf-8")
    try:
        subprocess.run(
            ["espeak-ng", "-v", "en-us", "-s", "155", "-f", str(text_file), "-w", str(wav_file)],
            check=True, timeout=25, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_file),
             "-codec:a", "libmp3lame", "-q:a", "4", str(path)],
            check=True, timeout=25, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    finally:
        text_file.unlink(missing_ok=True)
        wav_file.unlink(missing_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Both Edge TTS and local eSpeak fallback failed")
    return boundaries


def build_caption_cues(boundaries, narration, duration):
    """Group real TTS word timings into short, readable subtitle phrases."""
    words = [b for b in boundaries if b.get("text")]
    if not words:
        tokens = narration.split()
        if not tokens:
            return []
        count = max(1, math.ceil(len(tokens) / 7))
        cues = []
        for i in range(count):
            part = tokens[i*7:(i+1)*7]
            cues.append({"start": duration*i/count, "end": duration*min(1,(i+1)/count),
                         "text": " ".join(part)})
        return cues
    cues, group = [], []
    for word in words:
        group.append(word)
        token = str(word["text"])
        if len(group) >= 7 or token.endswith((".", "?", "!", ",", ";", ":")):
            cues.append({
                "start": max(0.0, group[0]["start"]),
                "end": min(duration, max(group[-1]["start"] + group[-1]["duration"], group[0]["start"] + .35)),
                "text": " ".join(str(item["text"]) for item in group),
            })
            group = []
    if group:
        cues.append({
            "start": max(0.0, group[0]["start"]),
            "end": min(duration, max(group[-1]["start"] + group[-1]["duration"], group[0]["start"] + .35)),
            "text": " ".join(str(item["text"]) for item in group),
        })
    return cues


def probe_duration(path):
    result=subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],
        check=True,capture_output=True,text=True
    )
    return float(result.stdout.strip())


def validate_story(story):
    if not isinstance(story.get("scenes"),list) or not story["scenes"]:
        raise ValueError("Story must contain a non-empty scenes array")
    for i,scene in enumerate(story["scenes"],1):
        if not scene.get("narration","").strip():
            raise ValueError(f"Scene {i} has no narration")
        if not scene.get("caption") and not scene.get("heading"):
            raise ValueError(f"Scene {i} needs a caption or heading")
        if float(scene.get("duration",0)) < 0:
            raise ValueError(f"Scene {i} has a negative duration")


def run(story_path, output):
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    validate_story(story)
    fps=int(story.get("fps",24))
    size=(int(story.get("width",1280)),int(story.get("height",720)))
    voice=story.get("voice","en-US-GuyNeural")
    rate=story.get("rate","+0%")
    OUT.mkdir(exist_ok=True)
    audio_dir=OUT/"audio"
    audio_dir.mkdir(exist_ok=True)
    audio_files=[]
    durations=[]
    print(f"Preparing narration for {len(story['scenes'])} scenes...")
    for i,scene in enumerate(story["scenes"]):
        path=audio_dir/f"scene_{i:03}.mp3"
        boundaries=asyncio.run(synthesize(scene["narration"],voice,path,rate))
        audio_files.append(path)
        duration=probe_duration(path)
        durations.append(duration)
        scene["_render_duration"]=duration+float(story.get("reading_beat",0.35))
        scene["_caption_cues"]=build_caption_cues(boundaries,scene["narration"],duration)
    total_audio=sum(durations)
    print(f"Narration duration: {total_audio/60:.2f} minutes")
    # Add the same short reading beat to each audio segment that is reserved
    # in its visual scene. This keeps every scene boundary synchronized.
    reading_beat=float(story.get("reading_beat",0.35))
    padded_dir=OUT/"padded_audio"
    padded_dir.mkdir(exist_ok=True)
    padded_audio=[]
    for i,path in enumerate(audio_files):
        padded=padded_dir/f"scene_{i:03}.mp3"
        subprocess.run([
            "ffmpeg","-y","-loglevel","error","-i",str(path),
            "-af",f"apad=pad_dur={reading_beat}","-c:a","libmp3lame",str(padded)
        ],check=True)
        padded_audio.append(padded)
    audio_files=padded_audio
    raw=OUT/"silent.mp4"
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{size[0]}x{size[1]}","-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(raw)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i,(scene,duration) in enumerate(zip(story["scenes"],durations),1):
            # Hold the scene for the full generated speech plus a short reading beat.
            scene_duration=max(float(scene.get("duration",0)),duration+float(story.get("reading_beat",0.35)))
            count=max(1,math.ceil(scene_duration*fps))
            for frame in range(count):
                proc.stdin.write(make_frame(scene,frame,count,size,i,len(story["scenes"]),story.get("title","Learning, illustrated")).tobytes())
            print(f"Rendered scene {i}/{len(story['scenes'])}: {scene_duration:.1f}s")
    finally:
        proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("Video frame encoding failed")
    concat=OUT/"audio.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in audio_files),encoding="utf-8")
    voice_file=OUT/"voiceover.mp3"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c:a","libmp3lame",str(voice_file)],check=True)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(voice_file),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(output)],check=True)
    video_duration=probe_duration(output)
    if video_duration+1 < total_audio:
        raise RuntimeError(f"Output ({video_duration:.1f}s) is shorter than narration ({total_audio:.1f}s)")
    report={"title":story.get("title",""),"scenes":len(story["scenes"]),"narration_seconds":round(total_audio,2),"video_seconds":round(video_duration,2),"fps":fps,"resolution":f"{size[0]}x{size[1]}","caption_timing":"edge_tts_word_boundaries" if all(scene.get("_caption_cues") for scene in story["scenes"]) else "fallback_estimated","caption_cues":sum(len(scene.get("_caption_cues",[])) for scene in story["scenes"]),"presenter_style":"thin_line_art_stickman","diagram_renderer":"solid_colour_svg","svg_diagrams":len(story["scenes"]),"output":str(output)}
    (output.parent/"render_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Long-form illustrated educational video renderer")
    parser.add_argument("--script",default="demo/learning.json")
    parser.add_argument("--output",default="output/educational-5min.mp4")
    args=parser.parse_args()
    run(args.script,args.output)
