#!/usr/bin/env python3
"""12-second 2D cutout-rig fox animation test.

The character is authored as a layered vector puppet with a hierarchical
skeleton: shoulder/hip pivots, elbow/knee pivots, head/neck pivot and tail
root. Animation is keyframed with eased transitions and planted-foot walk
timing. It is deliberately a short motion test, not the documentary renderer.
"""
import argparse, math, subprocess
from pathlib import Path
import cairosvg

W,H,FPS=1280,720,24
DARK="#50352b"; RUST="#d96e2e"; LIGHT="#f39a4f"; CREAM="#f7e5c2"
SHADOW="#9c4827"; PAW="#49342d"; GOLD="#e9b45b"

def clamp(x): return max(0.0,min(1.0,x))
def smooth(x):
    x=clamp(x); return x*x*(3-2*x)
def mix(a,b,t): return a+(b-a)*t
def phase(t,a,b): return smooth((t-a)/(b-a))
def pulse(t,a,b): return math.sin(math.pi*clamp((t-a)/(b-a))) if a<=t<=b else 0
def fmt(x): return f"{x:.2f}"

def limb(x,y,upper,lower,hip_angle,knee_angle,far=False):
    coat="#b85b2c" if far else RUST
    shade="#743d2a" if far else DARK
    # Local bone direction is downward. Nested lower leg rotates at the knee.
    return f'''<g transform="translate({x} {y}) rotate({hip_angle})">
      <path d="M -15 0 C -24 26 -20 58 -12 {upper} Q 0 {upper+10} 14 {upper-2} C 12 48 19 23 13 0 Z" fill="{coat}" stroke="{shade}" stroke-width="4"/>
      <path d="M -8 12 Q 1 44 5 {upper-7}" fill="none" stroke="{LIGHT}" stroke-width="7" opacity=".55"/>
      <g transform="translate(0 {upper}) rotate({knee_angle})">
        <path d="M -12 -5 Q -20 25 -9 {lower-4} Q 0 {lower+5} 13 {lower-5} L 10 0 Z" fill="{coat}" stroke="{shade}" stroke-width="4"/>
        <path d="M -4 12 Q 1 37 5 {lower-12}" fill="none" stroke="{LIGHT}" stroke-width="5" opacity=".45"/>
        <path d="M -9 {lower-8} Q -15 {lower+2} -7 {lower+9} L 22 {lower+9} Q 30 {lower+6} 21 {lower-3} L 10 {lower-9} Z" fill="{PAW}" stroke="{DARK}" stroke-width="3"/>
        <path d="M 12 {lower+1} l 6 1 M 3 {lower+2} l 5 1" stroke="#c8a18a" stroke-width="2" stroke-linecap="round"/>
      </g>
    </g>'''

def fox_svg(t):
    # Timeline: walk 0-3.2, settle 3.2-4.5, head turn 4.5-6.2,
    # sniff 6.2-8.4, crouch/pounce 8.4-10.3, land/recover 10.3-12.
    walk=1-phase(t,2.9,3.55)
    settle=phase(t,3.0,3.65)
    turn=phase(t,4.5,5.55)*(1-phase(t,5.8,6.25))
    sniff=phase(t,6.15,6.65)*(1-phase(t,8.05,8.45))
    crouch=pulse(t,8.35,9.05)
    jump=phase(t,9.0,9.45)*(1-phase(t,10.0,10.5))
    land=phase(t,10.0,10.7)
    cycle=t*2*math.pi*1.35
    bob=abs(math.sin(cycle))*7*walk
    x=330+min(t,3.1)*66 + max(0,t-9)*18
    y=445+bob+18*crouch-92*math.sin(math.pi*clamp((t-9.1)/1.05))*jump+12*land*(1-phase(t,10.4,11.2))
    body_rot=-5*crouch+2*math.sin(cycle)*walk
    head_rot=-8*turn+13*sniff+5*math.sin(t*9)*sniff
    tail_rot=12*math.sin(t*2.5)*.7+12*walk*math.sin(cycle-1)-20*crouch
    # Contralateral gait; alternating shoulder/hip swing and knee flex.
    lf_hip=24*math.sin(cycle)*walk+5*settle
    rf_hip=24*math.sin(cycle+math.pi)*walk+5*settle
    lh_hip=28*math.sin(cycle+math.pi)*walk-8*crouch
    rh_hip=28*math.sin(cycle)*walk-8*crouch
    knee=lambda a: -max(0,math.sin(a))*34*walk
    # Near/far leg order creates overlap and depth.
    legs = (
      limb(-67,-5,47,58,lh_hip,knee(cycle+math.pi),True)+
      limb(76,-4,48,57,rf_hip,knee(cycle+math.pi),True)+
      limb(-57,0,49,62,lh_hip,knee(cycle),False)+
      limb(82,0,49,62,lf_hip,knee(cycle+math.pi),False)
    )
    # Separate front shoulder/hip masses make limb attachment feel anatomical.
    head_y= -82 + 10*sniff + 8*crouch
    eye= f'''<ellipse cx="42" cy="-104" rx="8" ry="10" fill="#fff1cf"/>
      <ellipse cx="45" cy="-104" rx="4" ry="7" fill="#382820"/>
      <circle cx="46" cy="-107" r="2" fill="white"/>
      <path d="M 31 -120 Q 43 -127 54 -119" fill="none" stroke="{DARK}" stroke-width="3" stroke-linecap="round"/>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
    <defs>
      <linearGradient id="sky" x2="0" y2="1"><stop stop-color="#d8e9e3"/><stop offset="1" stop-color="#f4e7cb"/></linearGradient>
      <linearGradient id="fur" x2="0" y2="1"><stop stop-color="#f59a4d"/><stop offset="1" stop-color="#bd5629"/></linearGradient>
      <linearGradient id="tail" x2="1" y2="0"><stop stop-color="#a84c27"/><stop offset=".7" stop-color="#e67c37"/><stop offset="1" stop-color="#f7e7c9"/></linearGradient>
      <filter id="soft"><feGaussianBlur stdDeviation="12"/></filter>
    </defs>
    <rect width="1280" height="720" fill="url(#sky)"/>
    <circle cx="1030" cy="150" r="72" fill="#fff1c8" opacity=".55"/>
    <path d="M0 390 Q190 320 390 390 T790 370 T1280 380 V720 H0Z" fill="#b7cda7"/>
    <path d="M0 465 Q210 390 420 470 T840 445 T1280 455 V720 H0Z" fill="#789d72"/>
    <path d="M0 555 Q250 500 470 555 T900 540 T1280 550 V720 H0Z" fill="#456f50"/>
    <g opacity=".9">
      <path d="M80 0 L110 0 145 475 100 475Z" fill="#766b52"/>
      <path d="M110 0 Q30 55 45 145 Q105 180 165 118 Q190 45 110 0" fill="#668b69"/>
      <path d="M1080 0 L1112 0 1080 470 1040 470Z" fill="#766b52"/>
      <path d="M1100 0 Q1010 50 1030 145 Q1095 185 1165 120 Q1180 45 1100 0" fill="#668b69"/>
      <path d="M890 0 L910 0 935 350 900 350Z" fill="#8a7958"/>
      <path d="M910 0 Q850 38 860 105 Q920 150 970 90 Q975 28 910 0" fill="#779a70"/>
    </g>
    <ellipse cx="{fmt(x+5)}" cy="570" rx="185" ry="25" fill="#263f32" opacity=".22" filter="url(#soft)"/>
    <g transform="translate({fmt(x)} {fmt(y)}) rotate({fmt(body_rot)})">
      <!-- Tail is a true pivoted silhouette with layered fur tufts and a pale tip. -->
      <g transform="translate(-105 -45) rotate({fmt(tail_rot)})">
        <path d="M 0 0 C -65 -82 -160 -98 -220 -40 C -202 30 -130 65 -56 30 Q -20 20 0 0Z" fill="url(#tail)" stroke="{DARK}" stroke-width="7" stroke-linejoin="round"/>
        <path d="M -191 -40 Q -142 -62 -105 -18 Q -157 -8 -178 17 Q -201 -4 -191 -40Z" fill="#f7e5c2"/>
        <path d="M -12 -8 Q -84 -55 -150 -36" fill="none" stroke="#f7b36d" stroke-width="8" opacity=".6"/>
        <path d="M -25 5 Q -80 48 -130 35" fill="none" stroke="#9c4827" stroke-width="5" opacity=".5"/>
      </g>
      {legs}
      <!-- torso, shoulder and haunch volumes overlap the joints -->
      <path d="M -115 -85 Q -75 -137 12 -125 Q 105 -145 145 -77 Q 165 -22 105 10 Q 20 36 -75 7 Q -143 -8 -145 -48Z" fill="url(#fur)" stroke="{DARK}" stroke-width="7"/>
      <path d="M -54 -27 Q 14 -65 93 -44 Q 123 -20 93 7 Q 16 26 -54 -2Z" fill="#f5dfb7" opacity=".96"/>
      <path d="M -120 -57 Q -82 -101 -29 -91" fill="none" stroke="#ffbd77" stroke-width="9" opacity=".55"/>
      <path d="M 80 -75 Q 113 -64 130 -29 Q 102 7 76 9" fill="#f7e5c2" opacity=".95"/>
      <!-- Neck and head are independently articulated at the neck pivot. -->
      <g transform="translate(105 {fmt(head_y)}) rotate({fmt(head_rot)})">
        <path d="M -4 -18 Q 10 -69 55 -88 L 112 -81 Q 147 -70 177 -45 Q 188 -30 160 -22 L 96 -9 Q 56 12 19 26 Q -4 20 -4 -18Z" fill="#e97934" stroke="{DARK}" stroke-width="6"/>
        <path d="M 20 -5 Q 65 -40 113 -39 Q 147 -37 177 -44 Q 171 -18 132 -9 Q 76 6 33 21Z" fill="#f8e6c7"/>
        <!-- near ear -->
        <path d="M 5 -58 Q -8 -132 26 -171 Q 62 -143 65 -82Z" fill="#c85c2b" stroke="{DARK}" stroke-width="6"/>
        <path d="M 18 -81 Q 13 -132 28 -151 Q 47 -128 48 -86Z" fill="#f0bd8e"/>
        <!-- far ear -->
        <path d="M 61 -70 Q 78 -142 119 -154 Q 127 -102 101 -57Z" fill="#a84b28" stroke="{DARK}" stroke-width="6"/>
        <path d="M 78 -83 Q 91 -125 108 -134 Q 108 -99 95 -74Z" fill="#e6ae82"/>
        {eye}
        <path d="M 151 -31 Q 174 -36 187 -26 Q 180 -13 162 -16Z" fill="#3a2a25" stroke="{DARK}" stroke-width="3"/>
        <path d="M 90 -2 Q 119 9 145 -1" fill="none" stroke="#6f3b2b" stroke-width="3" stroke-linecap="round"/>
        <path d="M 112 -11 Q 132 -4 151 -11" fill="none" stroke="#fff1d6" stroke-width="5" opacity=".8"/>
        <g stroke="#6b4a37" stroke-width="2" opacity=".8">
          <path d="M 137 -16 l 24 -9 M 138 -8 l 26 1 M 130 -1 l 22 9"/>
        </g>
      </g>
      <!-- shoulder tufts and fur contours -->
      <path d="M 62 -112 Q 80 -137 98 -125 L 82 -105 M 40 -119 Q 55 -143 73 -132" fill="#f4a45f" stroke="{DARK}" stroke-width="4"/>
    </g>
    <!-- wind, grass and foreground depth -->
    <g stroke="#315b3d" stroke-width="5" stroke-linecap="round">
      <path d="M 80 615 q -20 -55 -38 -65 M 95 620 q 12 -48 33 -62 M 1150 625 q -10 -54 -31 -67 M 1174 625 q 17 -42 39 -53"/>
    </g>
    <g fill="#f6d88d" opacity=".75">
      <circle cx="{int((t*33+140)%1280)}" cy="260" r="4"/><circle cx="{int((t*21+760)%1280)}" cy="330" r="3"/><circle cx="{int((t*27+500)%1280)}" cy="215" r="3"/>
    </g>
    <rect x="48" y="42" width="360" height="48" rx="22" fill="#294b39" opacity=".92"/>
    <text x="72" y="74" font-family="DejaVu Sans" font-size="21" font-weight="bold" fill="#fff4df">FOX CHARACTER RIG TEST</text>
    </svg>'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="output/fox-rig-test.mp4")
    ap.add_argument("--seconds",type=float,default=12)
    args=ap.parse_args()
    frames=round(args.seconds*FPS)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(frames):
            t=i/FPS
            png=cairosvg.svg2png(bytestring=fox_svg(t).encode(),output_width=W,output_height=H)
            from PIL import Image
            import io
            im=Image.open(io.BytesIO(png)).convert("RGB")
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError("ffmpeg encoding failed")
    print(f"Rendered {frames} frames ({args.seconds:.1f}s) at {FPS}fps: {out}")
if __name__=="__main__": main()
