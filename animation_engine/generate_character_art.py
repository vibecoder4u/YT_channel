#!/usr/bin/env python3
"""Create original layered character artwork for the Rigby2D skeletal pipeline.

Every moving part is a separate transparent raster layer on one shared canvas.
The layers are deliberately overlapped at joints so AutoRig can form stable meshes.
"""
from pathlib import Path
import json
import cairosvg
from PIL import Image

W, H = 1000, 1100
OUT = Path("build/character-art")
OUT.mkdir(parents=True, exist_ok=True)

DEFS = """
<defs>
 <linearGradient id="skin" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#f4c49a"/><stop offset=".52" stop-color="#d99770"/><stop offset="1" stop-color="#ad684f"/>
 </linearGradient>
 <linearGradient id="skinLight" x1="0" y1="0" x2="0.8" y2="1">
  <stop offset="0" stop-color="#f8d2ad"/><stop offset="1" stop-color="#cf8967"/>
 </linearGradient>
 <linearGradient id="hair" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#62413a"/><stop offset=".52" stop-color="#34252a"/><stop offset="1" stop-color="#201a23"/>
 </linearGradient>
 <linearGradient id="coat" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#45b8a9"/><stop offset=".45" stop-color="#177f82"/><stop offset="1" stop-color="#10525f"/>
 </linearGradient>
 <linearGradient id="coatSide" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#155b69"/><stop offset=".48" stop-color="#208f8c"/><stop offset="1" stop-color="#0e4655"/>
 </linearGradient>
 <linearGradient id="pants" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#7b8790"/><stop offset=".5" stop-color="#455766"/><stop offset="1" stop-color="#263b4e"/>
 </linearGradient>
 <linearGradient id="boots" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#d9b071"/><stop offset="1" stop-color="#926340"/>
 </linearGradient>
 <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#fff0bf"/><stop offset=".5" stop-color="#d9a75f"/><stop offset="1" stop-color="#95663d"/>
 </linearGradient>
 <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
  <feGaussianBlur stdDeviation="4"/>
 </filter>
</defs>
"""

def svg(fragment):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{fragment}</svg>'

OUTLINES = '#26343d'
def render(name, body, hidden=False):
    data = cairosvg.svg2png(bytestring=svg(body).encode(), output_width=W, output_height=H)
    raw = OUT / f"{name}.png"
    raw.write_bytes(data)
    im = Image.open(raw).convert("RGBA")
    box = im.getbbox()
    if not box:
        raise ValueError(f"{name} is blank")
    im.crop(box).save(raw)
    return {"name": name, "file": str(raw), "hidden": hidden, "left": box[0], "top": box[1], "width": box[2]-box[0], "height": box[3]-box[1]}

layers = []

# Back hair sits behind the head. The head views themselves are individually drawn,
# not rotations of a single front-facing face.
layers.append(render("hair_back", """
<path d="M414 239 C389 142 443 89 510 92 C601 91 642 157 618 258
 C639 288 634 339 601 369 L430 354 C393 330 390 276 414 239Z"
 fill="url(#hair)" stroke="#241b22" stroke-width="13" stroke-linejoin="round"/>
<path d="M420 190 C439 117 500 108 553 126 C587 139 606 164 607 205
 C563 173 524 177 493 208 C465 235 438 248 415 244Z"
 fill="#6b463b" opacity=".62"/>
<path d="M420 256 C405 298 423 336 445 353 M603 245 C625 292 610 330 589 352"
 fill="none" stroke="#8a5a49" stroke-width="9" stroke-linecap="round" opacity=".55"/>
"""))

def head_front():
    return """
<ellipse cx="506" cy="236" rx="99" ry="119" fill="url(#skinLight)" stroke="#784c3e" stroke-width="11"/>
<path d="M413 235 C414 150 458 117 516 119 C587 119 614 164 603 241
 C582 219 565 192 548 169 C532 204 480 214 448 245Z"
 fill="url(#hair)" stroke="#241b22" stroke-width="12" stroke-linejoin="round"/>
<path d="M431 179 C450 133 489 126 526 137" fill="none" stroke="#a16a56" stroke-width="8" stroke-linecap="round" opacity=".7"/>
<path d="M431 244 C429 276 436 304 452 324 M582 245 C584 279 576 304 559 324" fill="none" stroke="#b8755a" stroke-width="7" opacity=".45"/>
<path d="M453 235 Q473 221 491 235 M526 235 Q545 221 564 235" stroke="#51362f" stroke-width="8" fill="none" stroke-linecap="round"/>
<ellipse cx="474" cy="248" rx="8" ry="12" fill="#253340"/><ellipse cx="545" cy="248" rx="8" ry="12" fill="#253340"/>
<circle cx="477" cy="244" r="2.7" fill="#fff4dc"/><circle cx="548" cy="244" r="2.7" fill="#fff4dc"/>
<path d="M508 250 Q497 278 511 281" fill="none" stroke="#a9604d" stroke-width="5" stroke-linecap="round"/>
<path d="M481 302 Q507 318 534 300 Q511 335 481 302Z" fill="#8d4745"/>
<path d="M487 303 Q507 309 528 303" stroke="#ffd8be" stroke-width="4" fill="none"/>
<ellipse cx="437" cy="276" rx="13" ry="8" fill="#e88c78" opacity=".22"/>
<ellipse cx="573" cy="276" rx="13" ry="8" fill="#e88c78" opacity=".22"/>
<path d="M413 248 Q397 260 414 283 M601 248 Q617 260 601 283" fill="url(#skin)" stroke="#784c3e" stroke-width="7"/>
<circle cx="418" cy="284" r="8" fill="url(#metal)"/><circle cx="593" cy="284" r="8" fill="url(#metal)"/>
<path d="M456 338 Q506 354 555 338 L553 370 Q506 388 458 370Z" fill="url(#skin)" stroke="#784c3e" stroke-width="8"/>
"""
layers.append(render("head_front", head_front()))

layers.append(render("head_threequarter", """
<path d="M417 230 C416 152 462 116 526 122 C595 127 621 178 596 268
 C585 326 547 354 489 344 C440 335 414 290 417 230Z"
 fill="url(#skinLight)" stroke="#784c3e" stroke-width="11"/>
<path d="M414 239 C411 165 465 111 532 122 C590 132 616 176 603 232
 C579 198 550 173 521 175 C488 176 465 217 414 239Z"
 fill="url(#hair)" stroke="#241b22" stroke-width="12"/>
<path d="M453 229 Q470 212 491 226" stroke="#51362f" stroke-width="8" fill="none" stroke-linecap="round"/>
<ellipse cx="476" cy="239" rx="8" ry="12" fill="#253340"/>
<path d="M526 225 Q552 219 564 236" stroke="#51362f" stroke-width="7" fill="none" stroke-linecap="round"/>
<ellipse cx="548" cy="242" rx="6" ry="10" fill="#253340"/>
<path d="M554 246 Q582 258 586 278 Q571 286 550 277" fill="#c77d5d" stroke="#784c3e" stroke-width="5"/>
<path d="M490 306 Q518 318 546 300 Q524 334 490 306Z" fill="#8d4745"/>
<path d="M432 273 Q422 315 452 335 M581 276 Q577 313 553 333" stroke="#b8755a" stroke-width="7" fill="none" opacity=".45"/>
<path d="M420 256 Q404 274 422 291 M597 249 Q612 268 596 288" fill="url(#skin)" stroke="#784c3e" stroke-width="7"/>
<circle cx="424" cy="285" r="7" fill="url(#metal)"/>
<path d="M458 338 Q509 356 554 338 L550 371 Q504 388 463 370Z" fill="url(#skin)" stroke="#784c3e" stroke-width="8"/>
""", hidden=True))

layers.append(render("head_profile", """
<path d="M462 126 C532 104 592 151 586 224 C585 264 567 300 544 321
 C531 335 518 343 496 343 C465 337 445 310 443 277
 C423 262 404 254 389 241 Q410 227 432 216 C426 176 438 143 462 126Z"
 fill="url(#skinLight)" stroke="#784c3e" stroke-width="11" stroke-linejoin="round"/>
<path d="M435 211 C419 147 469 103 533 120 C579 131 601 171 585 224
 C560 186 532 170 502 178 C476 186 463 203 435 211Z"
 fill="url(#hair)" stroke="#241b22" stroke-width="12"/>
<path d="M436 196 C459 141 506 126 545 145" fill="none" stroke="#8e5c4b" stroke-width="8" opacity=".65" stroke-linecap="round"/>
<path d="M432 218 Q407 232 388 242 Q410 259 444 254 Q449 240 432 218Z" fill="#d9936c" stroke="#784c3e" stroke-width="6"/>
<path d="M455 220 Q472 211 488 221" stroke="#51362f" stroke-width="8" fill="none" stroke-linecap="round"/>
<ellipse cx="475" cy="231" rx="7" ry="11" fill="#253340"/>
<path d="M476 273 Q496 281 511 269" stroke="#a9604d" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="M481 304 Q503 314 521 298 Q508 324 481 304Z" fill="#8d4745"/>
<path d="M449 268 Q440 306 473 332" stroke="#b8755a" stroke-width="7" fill="none" opacity=".45"/>
<path d="M478 338 Q520 353 552 337 L548 370 Q516 385 481 370Z" fill="url(#skin)" stroke="#784c3e" stroke-width="8"/>
""", hidden=True))

layers.append(render("head_back3q", """
<path d="M420 232 C422 149 463 116 524 123 C593 131 613 185 588 271
 C574 330 537 351 486 342 C443 335 414 290 420 232Z"
 fill="url(#skinLight)" stroke="#784c3e" stroke-width="11"/>
<path d="M412 240 C404 158 459 109 527 122 C599 137 616 192 588 249
 C576 210 554 183 522 181 C489 182 460 222 412 240Z"
 fill="url(#hair)" stroke="#241b22" stroke-width="12"/>
<path d="M558 226 Q581 215 599 236 Q582 250 557 244Z" fill="#d9936c" stroke="#784c3e" stroke-width="6"/>
<path d="M534 229 Q549 219 564 228" stroke="#51362f" stroke-width="8" fill="none" stroke-linecap="round"/>
<ellipse cx="552" cy="239" rx="7" ry="11" fill="#253340"/>
<path d="M531 300 Q554 313 573 295 Q559 322 531 300Z" fill="#8d4745"/>
<path d="M430 268 Q419 305 450 333" stroke="#b8755a" stroke-width="7" fill="none" opacity=".45"/>
<path d="M458 338 Q507 356 551 338 L548 370 Q507 386 462 370Z" fill="url(#skin)" stroke="#784c3e" stroke-width="8"/>
""", hidden=True))

# Neck
layers.append(render("neck", """
<path d="M457 321 Q500 350 547 320 L566 409 Q505 441 438 407Z"
 fill="url(#skin)" stroke="#784c3e" stroke-width="10"/>
<path d="M459 355 Q503 382 547 354 L542 395 Q502 413 464 393Z" fill="#b97256" opacity=".45"/>
"""))

# Arms: character's right is on the viewer's left.
def upperarm(x1,y1,x2,y2,flip=False):
    if not flip:
        return f"""
<path d="M{x1} {y1} C{x1-20} {y1+30} {x2-34} {y2-36} {x2} {y2}
 C{x2+28} {y2+28} {x2+13} {y2+47} {x2-16} {y2+35}
 C{x1-4} {y1+73} {x1-55} {y1+55} {x1} {y1}Z"
 fill="url(#coat)" stroke="{OUTLINES}" stroke-width="12" stroke-linejoin="round"/>
<path d="M{x1-1} {y1+17} Q{x1-17} {y1+52} {x2-13} {y2+19}" stroke="#a6e2cf" stroke-width="8" fill="none" opacity=".72"/>
<path d="M{x1-20} {y1+25} Q{x1-9} {y1+13} {x1+8} {y1+13}" stroke="#e1c27b" stroke-width="7" fill="none"/>
"""
    return f"""
<path d="M{x1} {y1} C{x1+20} {y1+30} {x2+34} {y2-36} {x2} {y2}
 C{x2-28} {y2+28} {x2-13} {y2+47} {x2+16} {y2+35}
 C{x1+4} {y1+73} {x1+55} {y1+55} {x1} {y1}Z"
 fill="url(#coat)" stroke="{OUTLINES}" stroke-width="12" stroke-linejoin="round"/>
<path d="M{x1+1} {y1+17} Q{x1+17} {y1+52} {x2+13} {y2+19}" stroke="#a6e2cf" stroke-width="8" fill="none" opacity=".72"/>
<path d="M{x1+20} {y1+25} Q{x1+9} {y1+13} {x1-8} {y1+13}" stroke="#e1c27b" stroke-width="7" fill="none"/>
"""
def forearm(x1,y1,x2,y2,side):
    return f"""
<path d="M{x1-35} {y1-15} Q{x1} {y1-34} {x1+30} {y1-10}
 C{x2+32} {y2-48} {x2+30} {y2+5} {x2+13} {y2+16}
 Q{x2-3} {y2+28} {x2-22} {y2+11} C{x1-45} {y1+48} {x1-56} {y1+22} {x1-35} {y1-15}Z"
 fill="url(#coat)" stroke="{OUTLINES}" stroke-width="12" stroke-linejoin="round"/>
<path d="M{x1-25} {y1+12} Q{x1+5} {y1+29} {x2+1} {y2-1}" fill="none" stroke="#a6e2cf" stroke-width="7" opacity=".7"/>
<path d="M{x2-28} {y2+4} Q{x2-2} {y2+22} {x2+24} {y2+8}" fill="none" stroke="#e4c27c" stroke-width="6"/>
"""
def hand(cx,cy):
    return f"""
<path d="M{cx-25} {cy-6} Q{cx-31} {cy-29} {cx-18} {cy-35}
 Q{cx-8} {cy-39} {cx-4} {cy-22} L{cx-1} {cy-48}
 Q{cx+10} {cy-56} {cx+13} {cy-40} L{cx+16} {cy-49}
 Q{cx+28} {cy-53} {cx+29} {cy-34} L{cx+35} {cy-39}
 Q{cx+47} {cy-35} {cx+42} {cy-15} Q{cx+34} {cy+18} {cx+13} {cy+25}
 Q{cx-13} {cy+20} {cx-25} {cy-6}Z"
 fill="url(#skin)" stroke="#754b3d" stroke-width="8" stroke-linejoin="round"/>
<path d="M{cx-7} {cy-12} Q{cx+2} {cy-3} {cx+2} {cy+8} M{cx+15} {cy-15} Q{cx+25} {cy-7} {cx+23} {cy+5}"
 fill="none" stroke="#9f604a" stroke-width="4" stroke-linecap="round"/>
"""
# Back arm segments
layers.append(render("upperarm_r", upperarm(410,390,354,500)))
layers.append(render("forearm_r", forearm(354,500,376,610,"r")))
layers.append(render("hand_r", hand(374,638)))
layers.append(render("upperarm_l", upperarm(590,390,646,500,True)))
layers.append(render("forearm_l", forearm(646,500,624,610,"l")))
layers.append(render("hand_l", hand(626,638)))

# Pants and legs
layers.append(render("thigh_r", """
<path d="M438 594 Q487 579 505 610 L496 765 Q468 795 430 766 L411 645Z"
 fill="url(#pants)" stroke="#263744" stroke-width="13" stroke-linejoin="round"/>
<path d="M440 626 Q459 644 464 677 L452 753" fill="none" stroke="#a5b0ad" stroke-width="7" opacity=".45"/>
<path d="M421 662 Q450 675 480 663" fill="none" stroke="#263744" stroke-width="7"/>
<path d="M433 699 L463 709 L461 737 L432 730Z" fill="#b58a5b" stroke="#2f3d46" stroke-width="6"/>
"""))
layers.append(render("thigh_l", """
<path d="M504 610 Q526 579 573 594 L601 645 L582 766 Q546 793 516 765Z"
 fill="url(#pants)" stroke="#263744" stroke-width="13" stroke-linejoin="round"/>
<path d="M564 626 Q543 653 546 685 L558 753" fill="none" stroke="#a5b0ad" stroke-width="7" opacity=".45"/>
<path d="M523 663 Q553 677 588 662" fill="none" stroke="#263744" stroke-width="7"/>
<path d="M542 706 L572 697 L585 729 L554 738Z" fill="#b58a5b" stroke="#2f3d46" stroke-width="6"/>
"""))
layers.append(render("shin_r", """
<path d="M434 750 Q466 767 492 750 L480 900 Q462 925 431 903 L420 798Z"
 fill="url(#pants)" stroke="#263744" stroke-width="12" stroke-linejoin="round"/>
<path d="M440 786 Q457 796 480 785" stroke="#98a6a5" stroke-width="6" fill="none" opacity=".6"/>
<path d="M432 867 Q460 879 484 866" stroke="#273d4b" stroke-width="7" fill="none"/>
"""))
layers.append(render("shin_l", """
<path d="M520 750 Q550 766 586 750 L590 798 L575 904 Q546 924 520 900 L510 795Z"
 fill="url(#pants)" stroke="#263744" stroke-width="12" stroke-linejoin="round"/>
<path d="M525 786 Q551 797 580 785" stroke="#98a6a5" stroke-width="6" fill="none" opacity=".6"/>
<path d="M522 867 Q552 879 583 866" stroke="#273d4b" stroke-width="7" fill="none"/>
"""))
layers.append(render("foot_r", """
<path d="M431 881 Q455 893 483 881 L485 925 Q511 936 520 956
 Q520 975 494 980 L414 980 Q398 973 411 951 L426 923Z"
 fill="url(#boots)" stroke="#283640" stroke-width="13" stroke-linejoin="round"/>
<path d="M425 924 Q461 938 489 921" fill="none" stroke="#f0d49d" stroke-width="8"/>
<path d="M431 945 L488 952 M431 958 L480 965" stroke="#61442f" stroke-width="6" stroke-linecap="round"/>
<path d="M411 975 Q469 984 514 974" stroke="#2a3135" stroke-width="12" fill="none"/>
"""))
layers.append(render("foot_l", """
<path d="M527 881 Q552 893 579 881 L590 923 Q615 937 617 957
 Q617 975 591 980 L514 980 Q498 973 512 951 L525 923Z"
 fill="url(#boots)" stroke="#283640" stroke-width="13" stroke-linejoin="round"/>
<path d="M523 924 Q558 938 591 921" fill="none" stroke="#f0d49d" stroke-width="8"/>
<path d="M530 945 L588 952 M532 958 L582 965" stroke="#61442f" stroke-width="6" stroke-linecap="round"/>
<path d="M509 975 Q568 984 611 974" stroke="#2a3135" stroke-width="12" fill="none"/>
"""))

# Pelvis and torso: styled field jacket with pockets, piping, woven shoulder patch.
layers.append(render("pelvis", """
<path d="M412 560 Q500 536 588 560 L604 666 Q563 697 500 688 Q438 697 397 666Z"
 fill="url(#pants)" stroke="#263744" stroke-width="13" stroke-linejoin="round"/>
<path d="M407 580 Q500 602 593 580" stroke="#d5b16f" stroke-width="13" fill="none"/>
<path d="M480 570 L520 570 L527 596 Q500 611 473 596Z" fill="url(#metal)" stroke="#523e2d" stroke-width="7"/>
<rect x="435" y="613" width="54" height="42" rx="8" fill="#31495a" stroke="#b18c5b" stroke-width="6"/>
<rect x="510" y="613" width="54" height="42" rx="8" fill="#31495a" stroke="#b18c5b" stroke-width="6"/>
<path d="M500 617 L500 677" stroke="#a4b1b0" stroke-width="5"/>
"""))
layers.append(render("pelvis_profile", """
<path d="M452 556 Q516 547 557 581 L573 668 Q535 692 477 683 L438 646Z"
 fill="url(#pants)" stroke="#263744" stroke-width="13" stroke-linejoin="round"/>
<path d="M445 581 Q509 603 565 587" stroke="#d5b16f" stroke-width="13" fill="none"/>
<path d="M493 575 L531 579 L538 601 Q511 614 488 596Z" fill="url(#metal)" stroke="#523e2d" stroke-width="7"/>
<path d="M466 621 L518 646 L511 667 L472 651Z" fill="#31495a" stroke="#b18c5b" stroke-width="6"/>
""", hidden=True))

layers.append(render("torso", """
<path d="M430 346 Q500 322 570 346 Q623 362 632 435 L604 592
 Q500 625 396 592 L368 435 Q377 362 430 346Z"
 fill="url(#coat)" stroke="#153f4b" stroke-width="16" stroke-linejoin="round"/>
<path d="M434 360 Q500 379 565 360 L550 590 Q500 609 450 590Z" fill="#19747a" opacity=".55"/>
<path d="M429 354 L500 423 L571 354" fill="none" stroke="#e2c48a" stroke-width="10" stroke-linejoin="round"/>
<path d="M500 420 L501 599" stroke="#a9d8c8" stroke-width="8"/>
<path d="M471 428 L500 450 L528 428" fill="#e5c687" stroke="#134d57" stroke-width="7" stroke-linejoin="round"/>
<path d="M403 440 Q432 460 459 450 L453 515 Q421 526 398 501Z" fill="#11616c" stroke="#0c4552" stroke-width="7"/>
<path d="M541 450 Q570 459 602 440 L606 503 Q581 525 545 515Z" fill="#11616c" stroke="#0c4552" stroke-width="7"/>
<path d="M409 452 Q430 461 449 456 M552 456 Q577 463 595 451" stroke="#7fcab8" stroke-width="7" fill="none"/>
<rect x="417" y="464" width="28" height="26" rx="4" fill="#d7a85f" stroke="#f0d49d" stroke-width="4"/>
<path d="M425 476 L438 476 M431 470 L431 484" stroke="#5b4a34" stroke-width="3"/>
<circle cx="500" cy="470" r="7" fill="url(#metal)" stroke="#725337" stroke-width="3"/>
<circle cx="500" cy="515" r="7" fill="url(#metal)" stroke="#725337" stroke-width="3"/>
<circle cx="500" cy="560" r="7" fill="url(#metal)" stroke="#725337" stroke-width="3"/>
<path d="M383 535 Q410 554 443 548 M558 548 Q590 553 618 530" fill="none" stroke="#58b8a9" stroke-width="7" opacity=".8"/>
<path d="M390 574 Q500 608 610 574" stroke="#0b4e5a" stroke-width="9" fill="none"/>
<path d="M390 399 Q400 372 429 369 M570 369 Q600 376 610 399" fill="none" stroke="#a0e0ce" stroke-width="7" opacity=".65"/>
"""))
layers.append(render("torso_profile", """
<path d="M455 347 Q510 327 562 352 Q594 382 585 447 L556 594
 Q499 613 444 589 L420 447 Q425 380 455 347Z"
 fill="url(#coatSide)" stroke="#153f4b" stroke-width="16" stroke-linejoin="round"/>
<path d="M468 357 Q514 381 560 358 L545 585 Q503 604 466 585Z" fill="#1c777b" opacity=".55"/>
<path d="M453 360 Q495 414 545 368" stroke="#dfc18a" stroke-width="10" fill="none"/>
<path d="M497 408 L496 594" stroke="#a9d8c8" stroke-width="8"/>
<path d="M467 449 Q490 459 521 448 L511 522 Q488 530 466 509Z" fill="#125d68" stroke="#0c4552" stroke-width="7"/>
<rect x="474" y="464" width="28" height="26" rx="4" fill="#d7a85f" stroke="#f0d49d" stroke-width="4"/>
<circle cx="501" cy="542" r="7" fill="url(#metal)" stroke="#725337" stroke-width="3"/>
<path d="M443 568 Q500 598 566 568" fill="none" stroke="#58b8a9" stroke-width="7"/>
""", hidden=True))

# Layer order: lower legs and back limbs behind torso, front arms/neck/head on top.
# Sort into a back-to-front order for the Rigby2D importer.
order = [
 "foot_r","foot_l","shin_r","shin_l","thigh_r","thigh_l","pelvis_profile","pelvis",
 "upperarm_r","upperarm_l","forearm_r","forearm_l","hand_r","hand_l",
 "torso_profile","torso","neck","hair_back","head_back3q","head_profile","head_threequarter","head_front"
]
by_name = {x["name"]:x for x in layers}
layers = [by_name[n] for n in order]
manifest = {"canvas":{"width":W,"height":H},"character":"Maya","style":"original illustrated 2D expedition character","layers":layers}
(OUT/"layers.json").write_text(json.dumps(manifest, indent=2))
print(f"Wrote {len(layers)} layered character parts to {OUT}")
