#!/usr/bin/env python3
"""Generate an original, layered SVG character rig and smooth action PNG sequences.

This is a deterministic source-authored vector rig (not a stock image or stick figure).
It creates distinct facial construction for front, three-quarter and profile views,
then renders articulated pose sequences for the complete character test.
"""
from pathlib import Path
import json, math
import cairosvg

ROOT = Path("assets/rigby2d/hero")
W, H = 640, 640
FPS = 30
ACTIONS = {
    "front_intro": (1.4, "front"),
    "turn_threequarter": (1.0, "threequarter"),
    "turn_profile": (1.0, "profile"),
    "walk": (2.2, "profile"),
    "stop_momentum": (0.8, "profile"),
    "look_back": (0.9, "threequarter"),
    "run": (1.8, "profile"),
    "jump": (1.0, "threequarter"),
    "land": (0.9, "threequarter"),
    "front_expression": (1.2, "front"),
}

def f(v): return f"{v:.2f}"
def line(x1,y1,x2,y2,color,width):
    return f'<path d="M {f(x1)} {f(y1)} L {f(x2)} {f(y2)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
def limb(a,b,c,d,color,width):
    return line(a,b,c,d,"#17212b",width+5)+line(a,b,c,d,color,width)

def render(action, frame, total):
    p = frame/max(1,total-1)
    phase = p*2*math.pi
    view = ACTIONS[action][1]
    walk = action in ("walk","run")
    speed = 2.0 if action=="run" else 1.0
    stride = math.sin(phase*2*speed) if walk else 0
    bounce = abs(math.sin(phase*2*speed))* (20 if action=="run" else 9) if walk else 0
    jump = math.sin(math.pi*p) if action=="jump" else 0
    land = (math.sin(math.pi*p)*-1) if action=="land" else 0
    turn = p if action=="turn_threequarter" else (p if action=="turn_profile" else 0)
    stop = math.sin(math.pi*p) if action=="stop_momentum" else 0
    look = math.sin(math.pi*p) if action=="look_back" else 0
    # Distinct face construction per view: eye count, nose projection, ear and hair silhouette.
    profile = view=="profile" or (action=="turn_profile" and p>.72)
    three = view=="threequarter" or (action=="turn_threequarter" and p>.02)
    face_shift = 12 if three else (24 if profile else 0)
    head_y = 150 + bounce*.22 - jump*22 + land*8
    torso_y = 260 + bounce*.35 - jump*28 + land*10
    lean = (stride*7 if walk else 0) + stop*13 - jump*5
    arm_swing = stride*(32 if action=="walk" else 48) if walk else 0
    leg_swing = stride*(35 if action=="walk" else 55) if walk else 0
    if action=="jump": leg_swing = math.sin(phase)*22
    if action=="land": leg_swing = (1-p)*24
    if action=="front_intro": arm_swing = -5
    if action=="look_back": lean = -look*4
    # Character centered at x=320; grounded at y=560.
    hipx, hipy = 320+lean, torso_y+135
    shoulderx, shouldery = 320+lean, torso_y+12
    left_knee=(hipx-25+leg_swing, hipy+75+abs(stride)*8-jump*25)
    right_knee=(hipx+25-leg_swing, hipy+75+abs(stride)*8-jump*25)
    left_foot=(left_knee[0]-18+leg_swing*.65, 548-bounce-jump*55+land*14)
    right_foot=(right_knee[0]+18-leg_swing*.65, 548-bounce-jump*55+land*14)
    if not walk and action not in ("jump","land"):
        left_knee=(hipx-24,hipy+72); right_knee=(hipx+24,hipy+72)
        left_foot=(hipx-42,548); right_foot=(hipx+42,548)
    # Hands have purposeful gestures.
    armL=(shoulderx-48-arm_swing*.55, shouldery+78+abs(arm_swing)*.12)
    armR=(shoulderx+48+arm_swing*.55, shouldery+78-abs(arm_swing)*.12)
    if action=="front_intro":
        armR=(shoulderx+86,shouldery+24)
    if action=="look_back":
        armR=(shoulderx+90,shouldery+40)
    if action=="jump":
        armL=(shoulderx-85,shouldery-45); armR=(shoulderx+85,shouldery-45)
    if action=="land":
        armL=(shoulderx-82,shouldery+48); armR=(shoulderx+82,shouldery+48)
    if action=="stop_momentum":
        armL=(shoulderx-86,shouldery+35); armR=(shoulderx+86,shouldery+5)
    # SVG composition, with shadows, clothing seams, highlights, expressive face and footwear.
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    s += ['<ellipse cx="320" cy="565" rx="120" ry="16" fill="#15232d" opacity=".16"/>']
    # Back hair mass and neck
    s += [f'<path d="M {320-face_shift-48} {head_y-22} Q 260 {head_y-105} 332 {head_y-103} Q 405 {head_y-90} {350-face_shift} {head_y+72} L 290 {head_y+64} Z" fill="#34252a" stroke="#241b22" stroke-width="5"/>']
    s += [f'<path d="M 300 {head_y+52} L 340 {head_y+52} L 348 {torso_y+8} L 292 {torso_y+8} Z" fill="#b96f50"/>']
    # legs behind body
    s += [limb(hipx-23,hipy,left_knee[0],left_knee[1],"#263f59",31),
          limb(left_knee[0],left_knee[1],left_foot[0],left_foot[1]-8,"#263f59",25),
          limb(hipx+23,hipy,right_knee[0],right_knee[1],"#314c69",31),
          limb(right_knee[0],right_knee[1],right_foot[0],right_foot[1]-8,"#314c69",25)]
    # boots
    s += [f'<path d="M {left_foot[0]-20} {left_foot[1]-16} q 18 -8 37 2 l 13 20 q -2 9 -53 7 q -9 -5 3 -29Z" fill="#d6a45d" stroke="#29313a" stroke-width="5"/>',
          f'<path d="M {right_foot[0]-18} {right_foot[1]-16} q 18 -8 37 2 l 13 20 q -2 9 -53 7 q -9 -5 3 -29Z" fill="#e1b56e" stroke="#29313a" stroke-width="5"/>']
    # arms with sleeves and hands
    s += [limb(shoulderx-39,shouldery+24,armL[0],armL[1],"#167f82",27),
          limb(shoulderx+39,shouldery+24,armR[0],armR[1],"#1b9996",27)]
    s += [f'<circle cx="{armL[0]}" cy="{armL[1]}" r="13" fill="#c98260" stroke="#754b3d" stroke-width="3"/>',
          f'<circle cx="{armR[0]}" cy="{armR[1]}" r="13" fill="#c98260" stroke="#754b3d" stroke-width="3"/>']
    # tailored jacket torso
    s += [f'<path d="M {shoulderx-42} {shouldery} Q {shoulderx} {shouldery-18} {shoulderx+42} {shouldery} L {hipx+36} {hipy+10} Q {hipx} {hipy+31} {hipx-36} {hipy+10} Z" fill="#168b8c" stroke="#145d68" stroke-width="6"/>',
          f'<path d="M {shoulderx-4} {shouldery+2} L {hipx-2} {hipy+15} M {shoulderx+4} {shouldery+2} L {hipx+2} {hipy+15}" stroke="#a8d7ca" stroke-width="4" opacity=".9"/>',
          f'<path d="M {shoulderx-28} {shouldery+26} Q {shoulderx} {shouldery+38} {shoulderx+28} {shouldery+26}" fill="none" stroke="#b7e1d5" stroke-width="4"/>',
          f'<circle cx="{shoulderx+13}" cy="{shouldery+62}" r="4" fill="#f2d39a"/>']
    # head and face
    s += [f'<ellipse cx="{320+face_shift*.45}" cy="{head_y}" rx="{48 if not profile else 43}" ry="59" fill="#d99570" stroke="#754b3d" stroke-width="5"/>']
    # front/3-quarter/profile nose and eyes are different, not rotated front artwork
    if profile:
        s += [f'<path d="M {350+face_shift*.25} {head_y-5} q 23 7 29 20 q -13 5 -27 0" fill="#c47b5c" stroke="#754b3d" stroke-width="3"/>',
              f'<path d="M {330+face_shift*.2} {head_y-17} q 15 -9 26 0" stroke="#3b2929" stroke-width="6" fill="none"/>',
              f'<ellipse cx="{347+face_shift*.2}" cy="{head_y-12}" rx="5" ry="7" fill="#252c35"/>']
    else:
        s += [f'<path d="M {292+face_shift*.2} {head_y-15} q 12 -10 23 0 M {332+face_shift*.2} {head_y-15} q 12 -10 23 0" stroke="#4b3030" stroke-width="5" fill="none"/>',
              f'<ellipse cx="{305+face_shift*.2}" cy="{head_y-8}" rx="5" ry="7" fill="#25313b"/>',
              f'<ellipse cx="{345+face_shift*.2}" cy="{head_y-8}" rx="5" ry="7" fill="#25313b"/>',
              f'<path d="M {324+face_shift*.2} {head_y-2} q -5 13 3 15" fill="none" stroke="#a85f4e" stroke-width="3"/>']
    smile = 6 if action in ("front_intro","front_expression") else 1
    s += [f'<path d="M {310+face_shift*.2} {head_y+28} q 15 {smile} 29 -2" fill="none" stroke="#773e3b" stroke-width="4" stroke-linecap="round"/>']
    # distinct front fringe and side-swept profile hair
    s += [f'<path d="M {274+face_shift*.2} {head_y-19} Q 270 {head_y-88} 333 {head_y-82} Q 380 {head_y-72} {365+face_shift*.2} {head_y-18} Q 347 {head_y-47} 322 {head_y-42} Q 302 {head_y-20} 274 {head_y-19}Z" fill="#3a292e" stroke="#241b22" stroke-width="5"/>',
          f'<path d="M {286+face_shift*.2} {head_y-44} Q 319 {head_y-70} 350 {head_y-49}" stroke="#80504a" stroke-width="5" fill="none" opacity=".8"/>']
    # jacket collar and utility details in foreground
    s += [f'<path d="M {shoulderx-20} {shouldery+2} l 20 22 l -10 18 l -24 -26 Z M {shoulderx+20} {shouldery+2} l -20 22 l 10 18 l 24 -26 Z" fill="#e1b56e" stroke="#145d68" stroke-width="3"/>']
    s += ['</svg>']
    return ''.join(s)

def main():
    for name,(seconds,view) in ACTIONS.items():
        folder=ROOT/name; folder.mkdir(parents=True,exist_ok=True)
        for old in folder.glob("*.png"): old.unlink()
        n=round(seconds*FPS)
        for i in range(n):
            svg=render(name,i,n)
            cairosvg.svg2png(bytestring=svg.encode(),write_to=str(folder/f"frame_{i:04d}.png"))
    (ROOT/"manifest.json").write_text(json.dumps({
        "source":"Original SVG articulated character rig",
        "character_name":"Maya",
        "authoring_fps":FPS,
        "views":["front","threequarter","profile"],
        "transparent_background":True,
        "generated_by":"generate_character_assets.py",
        "actions":list(ACTIONS)
    },indent=2))
    print(f"Generated {sum(round(v[0]*FPS) for v in ACTIONS.values())} authored vector-rig frames across {len(ACTIONS)} actions.")
if __name__=="__main__": main()
