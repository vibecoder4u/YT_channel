#!/usr/bin/env python3
"""30-second illustrated 2D explainer pilot renderer.
Creates a reusable, layered cartoon presenter and animated brain/neuron scenes.
"""
import argparse, math, subprocess, shutil
from pathlib import Path
import cairosvg
from PIL import Image
import io

W,H,FPS=1920,1080,24
OUT=Path("output/brain-sleep-30s")
def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def character(t, x=520, y=760, scale=1.0, pose="explain"):
    bob=math.sin(t*3.1)*8
    arm=math.sin(t*2.4)
    headtilt=math.sin(t*1.5)*4
    left_arm=f"M {x-75} {y-215} Q {x-150} {y-170+arm*25} {x-165} {y-95}"
    right_arm=f"M {x+75} {y-215} Q {x+145} {y-280-arm*25} {x+205} {y-330 if pose=='point' else y-190}"
    return f"""
    <g transform="translate(0 {bob})" stroke="#24354B" stroke-width="17" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="{x}" cy="{y+18}" rx="100" ry="18" fill="#23364A" opacity=".12" stroke="none"/>
      <path d="M{x-64} {y-218} Q{x-105} {y-75} {x-68} {y-12} Q{x} {y+22} {x+68} {y-12} Q{x+105} {y-75} {x+64} {y-218}Z" fill="#26A69A"/>
      <path d="M{x-48} {y-15} L{x-64} {y+115} L{x-116} {y+208} L{x-45} {y+208} L{x} {y+100} L{x+45} {y+208} L{x+116} {y+208} L{x+64} {y-15}" fill="#344A68"/>
      <path d="{left_arm}" fill="none"/>
      <path d="{right_arm}" fill="none"/>
      <circle cx="{x-165}" cy="{y-92}" r="18" fill="#F4C7A1"/>
      <circle cx="{x+(205 if pose=='point' else 145)}" cy="{y+(-330 if pose=='point' else -190)}" r="18" fill="#F4C7A1"/>
      <g transform="rotate({headtilt} {x} {y-300})">
        <ellipse cx="{x}" cy="{y-300}" rx="104" ry="112" fill="#F4C7A1"/>
        <path d="M{x-100} {y-325} Q{x-110} {y-445} {x-12} {y-432} Q{x+85} {y-462} {x+105} {y-350} Q{x+40} {y-385} {x-4} {y-373} Q{x-54} {y-355} {x-100} {y-325}" fill="#47352E" stroke="none"/>
        <ellipse cx="{x-36}" cy="{y-300}" rx="9" ry="13" fill="#24354B" stroke="none"/>
        <ellipse cx="{x+36}" cy="{y-300}" rx="9" ry="13" fill="#24354B" stroke="none"/>
        <path d="M{x-22} {y-255} Q{x} {y-238} {x+25} {y-255}" fill="none" stroke="#A84D4D" stroke-width="7"/>
        <circle cx="{x-78}" cy="{y-260}" r="15" fill="#E98F85" opacity=".55" stroke="none"/>
        <circle cx="{x+78}" cy="{y-260}" r="15" fill="#E98F85" opacity=".55" stroke="none"/>
      </g>
    </g>"""
def neuron(cx,cy,t,idx):
    pulse=(math.sin(t*5+idx)*.5+.5)
    r=22+10*pulse
    return f'<g stroke="#6B62C8" stroke-width="7" stroke-linecap="round" fill="none"><path d="M{cx} {cy} l-55 -45 m55 45 l60 -50 m-60 50 l-45 65 m45 -65 l55 60"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="#8F83EA" stroke="#5148A8"/><circle cx="{cx-7}" cy="{cy-8}" r="7" fill="#FFF" stroke="none"/></g>'
def scene_svg(t,scene):
    title,sub=scene
    bg=['#F3F8FF','#F4F2FF','#EFFAF6','#FFF7ED','#F3F8FF'][min(4,int(t//6))]
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="#DCEAF8"/></linearGradient><filter id="shadow"><feDropShadow dx="0" dy="12" stdDeviation="15" flood-opacity=".12"/></filter></defs><rect width="1920" height="1080" fill="url(#g)"/>'
    # soft decorative shapes
    s+='<circle cx="1620" cy="170" r="210" fill="#CFE6F3" opacity=".5"/><circle cx="240" cy="900" r="270" fill="#D7EFE8" opacity=".6"/>'
    s+=f'<text x="130" y="125" font-family="DejaVu Sans" font-size="30" font-weight="700" letter-spacing="5" fill="#52718A">THE SLEEPING BRAIN • EXPLAINED</text>'
    s+=f'<text x="130" y="230" font-family="DejaVu Sans" font-size="68" font-weight="800" fill="#20364D">{esc(title)}</text>'
    s+=f'<text x="135" y="292" font-family="DejaVu Sans" font-size="31" fill="#557086">{esc(sub)}</text>'
    # Character remains consistent; poses vary by scene.
    pose='point' if 6<=t<12 or 18<=t<24 else 'explain'
    s+=character(t,520,790,1,pose)
    # floating explanatory panel
    s+='<g filter="url(#shadow)"><rect x="900" y="390" width="850" height="480" rx="42" fill="#FFFFFF" stroke="#D6E2EC" stroke-width="4"/></g>'
    if t<6:
        s+='<path d="M1100 650 Q1320 450 1550 650 Q1320 850 1100 650Z" fill="#8C9AE8" opacity=".18" stroke="#6D77C9" stroke-width="8"/><path d="M1160 650 Q1320 510 1490 650 Q1320 790 1160 650Z" fill="#B6BDF5" stroke="#6D77C9" stroke-width="7"/>'
        for i in range(8):
            x=1190+i*42; y=625+math.sin(i*.8)*35
            s+=f'<circle cx="{x}" cy="{y}" r="10" fill="#FFFFFF"/>'
        s+='<text x="1325" y="820" text-anchor="middle" font-family="DejaVu Sans" font-size="27" fill="#536A82">Your brain stays active while you sleep</text>'
    elif t<12:
        s+='<path d="M1100 650 C1050 500 1240 430 1330 540 C1420 430 1620 500 1560 650 C1510 800 1390 800 1330 730 C1270 800 1150 800 1100 650Z" fill="#F2A7B8" stroke="#B85F83" stroke-width="10"/>'
        for i in range(5):
            s+=neuron(1180+i*105,590+(i%2)*95,t,i)
    elif t<18:
        for i in range(6):
            x=1080+(i%3)*230; y=530+(i//3)*170
            s+=f'<rect x="{x}" y="{y}" width="170" height="105" rx="24" fill="#E9E7FF" stroke="#766DC7" stroke-width="5"/><text x="{x+85}" y="{y+65}" text-anchor="middle" font-family="DejaVu Sans" font-size="24" font-weight="700" fill="#4F4B91">{["MEMORY","LEARNING","REPAIR","FOCUS","EMOTION","ENERGY"][i]}</text>'
            s+=f'<path d="M{x+85} {y+115} l0 24" stroke="#6B62C8" stroke-width="5" stroke-linecap="round"/>'
    elif t<24:
        for i in range(7):
            s+=neuron(1080+(i%4)*170,530+(i//4)*180,t,i+4)
        s+='<path d="M1080 790 Q1320 880 1580 790" fill="none" stroke="#20A68A" stroke-width="12" stroke-linecap="round"/>'
    else:
        s+='<circle cx="1325" cy="620" r="155" fill="#F9D77B" opacity=".8"/><path d="M1325 500 L1325 740 M1205 620 L1445 620" stroke="#FFFFFF" stroke-width="16" stroke-linecap="round"/>'
        s+='<text x="1325" y="835" text-anchor="middle" font-family="DejaVu Sans" font-size="31" font-weight="700" fill="#47627A">Sleep supports a healthier mind</text>'
    # moving accent dots and progress bar
    px=130+1660*(t/30)
    s+=f'<rect x="130" y="990" width="1660" height="10" rx="5" fill="#D5E0E9"/><rect x="130" y="990" width="{max(0,px-130)}" height="10" rx="5" fill="#20A68A"/>'
    s+=f'<circle cx="{px}" cy="995" r="14" fill="#20A68A" stroke="#FFFFFF" stroke-width="5"/>'
    return s+'</svg>'
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='output/brain-sleep-30s.mp4')
    a=p.parse_args()
    if not shutil.which('ffmpeg'): raise SystemExit('FFmpeg is required')
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    frames=OUT/'frames'; frames.mkdir(parents=True,exist_ok=True)
    scenes=[("Your brain never really switches off","Even when your eyes close, important work begins."),
            ("Inside your sleeping brain","Neurons keep communicating in carefully timed patterns."),
            ("Memories get organized","The brain strengthens useful connections and sorts new information."),
            ("Your brain restores balance","Sleep supports learning, attention and emotional regulation."),
            ("A better day starts at night","Good sleep is one of the foundations of a healthy mind.")]
    for i in range(FPS*30):
        t=i/FPS
        idx=min(4,int(t//6)); local=t-idx*6
        svg=scene_svg(t,scenes[idx])
        png=cairosvg.svg2png(bytestring=svg.encode(),output_width=W,output_height=H)
        Image.open(io.BytesIO(png)).save(frames/f'{i:05d}.png')
    out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-y','-framerate',str(FPS),'-i',str(frames/'%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-movflags','+faststart',str(out)],check=True)
    probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-show_entries','stream=width,height,r_frame_rate','-of','json',str(out)],text=True)
    (out.parent/'qa.json').write_text(probe)
    print(probe)
if __name__=='__main__': main()
