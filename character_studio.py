#!/usr/bin/env python3
"""Character Studio: reusable illustrated character turnarounds (SVG master + PNG proof)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import cairosvg
from PIL import Image, ImageDraw

W, H = 640, 900
INK = "#26343a"

# Reusable vector character construction. Each view is drawn independently so facial
# anatomy, hair silhouette, clothing overlaps and limb proportions change with angle.
def path(d, fill, stroke=INK, sw=5):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
def ellipse(cx,cy,rx,ry,fill,stroke=INK,sw=4):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(d, color=INK, sw=4):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'

def make_character(name="Maya", view="front", palette=None):
    c = {"skin":"#c9825e","hair":"#30272a","jacket":"#168c91","jacket_light":"#45b5ad",
         "jacket_dark":"#12666d","shirt":"#f0d7b0","trousers":"#344d58","boots":"#59433a",
         "accent":"#e3b35c","shadow":"#d9d1c1"}
    if palette: c.update(palette)
    S=[]
    # Editorial character-sheet background, with no stock or external assets.
    S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    S.append('<defs><linearGradient id="paper" x2="0" y2="1"><stop stop-color="#fbf8ef"/><stop offset="1" stop-color="#eee8d9"/></linearGradient><linearGradient id="cloth" x2="1" y2="1"><stop stop-color="'+c["jacket_light"]+'"/><stop offset="1" stop-color="'+c["jacket_dark"]+'"/></linearGradient><filter id="soft"><feGaussianBlur stdDeviation="12"/></filter></defs>')
    S.append('<rect width="640" height="900" fill="url(#paper)"/>')
    for x in range(40,641,40): S.append(f'<path d="M{x} 0V900" stroke="#d8d0c0" stroke-opacity=".22"/>')
    for y in range(40,901,40): S.append(f'<path d="M0 {y}H640" stroke="#d8d0c0" stroke-opacity=".22"/>')
    S.append('<path d="M320 65V835" stroke="#9f9a8c" stroke-dasharray="5 9" opacity=".55"/>')
    S.append('<ellipse cx="320" cy="824" rx="126" ry="20" fill="#817b6d" opacity=".18" filter="url(#soft)"/>')
    # boots / legs, angle-specific silhouette
    if view=="front":
        S += [path("M252 565 Q246 650 238 752 L224 800 Q224 818 246 821 L296 821 Q309 816 301 799 L292 748 L310 585Z",c["trousers"]),
              path("M330 580 L350 746 L345 795 Q333 814 353 821 L405 821 Q426 818 412 797 L395 748 L390 568Z",c["trousers"]),
              path("M224 790 Q251 780 298 797 L308 829 Q307 845 282 847 L217 843 Q202 837 211 819Z",c["boots"]),
              path("M346 790 Q373 780 412 797 L428 827 Q426 844 400 847 L344 843 Q329 836 337 817Z",c["boots"]),
              line("M224 818Q260 826 300 819","#b28a68",3),line("M345 818Q382 826 420 818","#b28a68",3)]
    elif view=="threequarter":
        S += [path("M270 560 Q264 653 258 752 L244 799 Q243 818 268 821 L311 820 Q326 815 314 795 L310 746 L335 580Z",c["trousers"]),
              path("M337 572 L365 746 L358 797 Q348 817 370 822 L415 820 Q431 813 416 793 L405 744 L391 570Z",c["trousers"]),
              path("M244 790Q276 783 314 798L323 830Q317 847 290 846L237 843Q225 836 234 817Z",c["boots"]),
              path("M358 790Q389 783 418 798L434 829Q430 845 405 847L354 843Q342 836 350 816Z",c["boots"])]
    elif view=="profile":
        S += [path("M300 560 Q318 650 311 750 L295 797 Q292 816 314 821 L357 820 Q371 813 354 794 L358 744 L367 570Z",c["trousers"]),
              path("M340 575 Q369 657 382 744 L379 795 Q367 815 389 821 L430 817 Q444 808 426 790 L414 743 L388 567Z",c["trousers"]),
              path("M295 790Q325 782 355 799L366 830Q359 846 334 845L290 842Q279 833 287 816Z",c["boots"]),
              path("M379 790Q407 782 430 798L445 828Q438 844 414 846L375 840Q364 832 371 815Z",c["boots"])]
    else:
        S += [path("M255 560Q246 656 244 753L229 798Q226 817 249 821L297 820Q311 813 297 795L294 747L313 570Z",c["trousers"]),
              path("M330 570L350 748L344 796Q332 815 354 821L405 820Q422 814 408 795L394 747L389 562Z",c["trousers"]),
              path("M228 790Q260 782 298 798L308 829Q303 846 277 846L218 842Q204 835 214 816Z",c["boots"]),
              path("M344 790Q380 782 409 798L425 829Q421 846 395 846L343 842Q330 834 338 816Z",c["boots"])]
    # torso, shoulder and jacket silhouette
    if view=="front":
        S += [path("M258 276 Q225 287 208 328 L183 472 Q180 495 204 503 L235 493 L246 584 Q319 607 395 584 L407 493 L436 505 Q459 496 453 471 L427 331 Q414 293 380 278 L349 261 L290 261Z","url(#cloth)"),
              path("M289 268L320 315L350 268L339 255L300 255Z",c["shirt"]),
              path("M320 315L320 576",c["jacket_dark"],sw=5),
              path("M258 294Q282 321 289 370L279 491", "none",c["jacket_light"],sw=8),
              path("M382 294Q359 324 353 370L365 490","none",c["jacket_dark"],sw=7),
              path("M245 499Q320 516 397 499L395 584Q319 606 246 584Z",c["jacket"]),
              path("M272 421L300 428L296 464L267 458Z",c["accent"],sw=3),
              path("M344 421L372 428L374 458L346 464Z",c["accent"],sw=3)]
    elif view=="threequarter":
        S += [path("M281 277Q242 286 224 331L201 468Q197 493 224 503L250 490L263 585Q330 606 395 581L405 485L426 499Q449 493 441 468L416 332Q402 293 367 278L340 260L300 259Z","url(#cloth)"),
              path("M301 267L330 315L350 269L340 255L307 255Z",c["shirt"]),
              path("M330 315L319 577", "none",c["jacket_dark"],sw=5),
              path("M277 297Q304 334 300 399L289 487","none",c["jacket_light"],sw=8),
              path("M373 295Q351 334 358 389L374 481","none",c["jacket_dark"],sw=7),
              path("M262 500Q330 520 400 495L395 582Q326 606 263 584Z",c["jacket"]),
              path("M283 423L310 430L302 464L276 458Z",c["accent"],sw=3)]
    elif view=="profile":
        S += [path("M321 277Q284 287 274 331L260 469Q258 494 283 500L307 490L309 584Q364 602 416 579L406 480L423 493Q444 488 436 464L405 329Q389 290 354 278L340 261Z","url(#cloth)"),
              path("M339 268L357 307L371 275L358 257L339 257Z",c["shirt"]),
              path("M357 308L343 578","none",c["jacket_dark"],sw=5),
              path("M302 300Q328 334 323 395L316 483","none",c["jacket_light"],sw=8),
              path("M365 498Q393 510 413 490L416 579Q365 603 310 584L309 493Z",c["jacket"]),
              path("M324 421L348 428L343 461L317 456Z",c["accent"],sw=3)]
    else:
        S += [path("M258 276Q225 287 208 328L183 472Q180 495 204 503L235 493L246 584Q319 607 395 584L407 493L436 505Q459 496 453 471L427 331Q414 293 380 278L349 261L290 261Z","url(#cloth)"),
              path("M289 268Q320 300 350 268L349 258L290 258Z",c["jacket_dark"]),
              path("M320 304L320 570","none",c["jacket_dark"],sw=5),
              path("M270 330Q320 353 370 330","none",c["jacket_light"],sw=6),
              path("M246 499Q320 516 397 499L395 584Q319 606 246 584Z",c["jacket"]),
              path("M294 365Q320 375 346 365","none",c["accent"],sw=4)]
    # arms, with different silhouette and hand placement by angle
    if view=="front":
        S += [path("M218 329Q195 362 184 446L174 522Q173 547 194 551Q216 550 220 525L241 408L257 359Z","url(#cloth)"),
              path("M420 329Q445 360 457 444L466 521Q466 547 444 551Q423 550 420 524L397 407L382 359Z","url(#cloth)"),
              ellipse(193,553,17,22,c["skin"]),ellipse(447,553,17,22,c["skin"])]
    elif view=="threequarter":
        S += [path("M231 331Q206 370 199 447L193 519Q194 546 216 550Q238 548 239 524L260 410L276 359Z","url(#cloth)"),
              path("M407 330Q442 364 455 441L459 516Q457 542 437 548Q416 546 416 521L390 404L370 359Z","url(#cloth)"),
              ellipse(211,551,17,22,c["skin"]),ellipse(440,550,17,22,c["skin"])]
    elif view=="profile":
        S += [path("M285 333Q258 370 263 446L266 520Q270 544 291 546Q312 541 305 516L304 410L328 361Z","url(#cloth)"),
              path("M398 331Q429 365 439 443L442 515Q439 540 419 546Q398 542 399 517L382 408L365 359Z","url(#cloth)"),
              ellipse(289,547,16,21,c["skin"]),ellipse(423,547,16,21,c["skin"])]
    else:
        S += [path("M218 329Q195 362 184 446L174 522Q173 547 194 551Q216 550 220 525L241 408L257 359Z","url(#cloth)"),
              path("M420 329Q445 360 457 444L466 521Q466 547 444 551Q423 550 420 524L397 407L382 359Z","url(#cloth)"),
              ellipse(193,553,17,22,c["skin"]),ellipse(447,553,17,22,c["skin"])]
    # head and hair: deliberately distinct construction per camera angle
    if view=="front":
        S += [path("M270 126Q272 70 321 65Q374 65 378 126L371 214Q361 264 321 269Q280 260 270 214Z",c["skin"]),
              path("M267 147Q244 89 287 55Q329 25 369 57Q405 88 378 159L367 119Q337 136 302 116Q293 145 270 160Z",c["hair"]),
              path("M270 143Q260 191 276 235Q261 221 256 184Z",c["hair"],sw=3),
              path("M370 133Q387 174 372 226L360 240L360 168Z",c["hair"],sw=3),
              ellipse(296,165,8,11,"#fffdf5",INK,2),ellipse(348,165,8,11,"#fffdf5",INK,2),
              ellipse(298,166,3.5,6,INK,INK,1),ellipse(350,166,3.5,6,INK,INK,1),
              line("M320 171L314 195L324 198", "#945a4a",3),line("M303 222Q321 235 340 220","#7e3e3b",3),
              line("M281 154Q293 146 307 153"," #30272a",4),line("M337 153Q351 145 363 154",c["hair"],4)]
    elif view=="threequarter":
        S += [path("M278 127Q279 72 326 66Q377 65 382 128L371 213Q360 262 323 267Q283 259 276 213Z",c["skin"]),
              path("M274 148Q252 87 294 54Q338 23 376 62Q409 99 374 166L367 124Q336 136 306 116Q294 145 274 162Z",c["hair"]),
              path("M274 147Q266 198 283 237L264 216L259 179Z",c["hair"],sw=3),
              ellipse(309,164,7,10,"#fffdf5",INK,2),ellipse(354,164,6,9,"#fffdf5",INK,2),
              ellipse(312,165,3,6,INK,INK,1),ellipse(356,165,3,5,INK,INK,1),
              path("M331 169Q342 182 333 196L346 200Q338 205 327 200","none","#945a4a",3),
              line("M316 222Q333 232 350 217","#7e3e3b",3)]
    elif view=="profile":
        S += [path("M322 75Q374 62 388 112Q396 143 379 167L398 184Q406 193 393 200L378 205Q376 247 345 264Q315 259 305 228L300 166Q297 100 322 75Z",c["skin"]),
              path("M300 160Q281 93 329 57Q374 28 404 77Q422 109 394 160L389 131Q371 145 350 123Q339 154 311 168L306 207Q291 188 300 160Z",c["hair"]),
              path("M305 164Q299 207 318 238Q298 222 292 191Z",c["hair"],sw=3),
              ellipse(369,159,6,9,"#fffdf5",INK,2),ellipse(371,160,2.8,5,INK,INK,1),
              path("M379 177Q392 185 399 190Q390 197 378 195","none","#945a4a",3),
              line("M351 222Q366 227 378 216","#7e3e3b",3)]
    else:
        S += [path("M270 127Q272 70 321 65Q374 65 378 126L371 214Q361 264 321 269Q280 260 270 214Z",c["skin"]),
              path("M267 147Q244 89 287 55Q329 25 369 57Q405 88 378 159L367 119Q337 136 302 116Q293 145 270 160Z",c["hair"]),
              path("M270 143Q260 191 276 235Q261 221 256 184Z",c["hair"],sw=3),
              path("M370 133Q387 174 372 226L360 240L360 168Z",c["hair"],sw=3),
              path("M289 111Q320 132 352 111","none","#514148",5),
              path("M302 137Q320 146 339 137","none","#514148",4)]
    # finishing costume details and character-specific ID marks
    S += [path("M300 258L320 313L340 258","none",c["accent"],5),
          line("M286 506L286 570",c["jacket_light"],3),line("M354 506L354 570",c["jacket_dark"],3),
          f'<text x="320" y="875" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="700" letter-spacing="3" fill="#58645e">{view.upper()} VIEW</text>',
          f'<text x="320" y="42" text-anchor="middle" font-family="sans-serif" font-size="20" font-weight="700" letter-spacing="4" fill="#344b4b">{name.upper()} • CHARACTER MODEL</text>',
          '</svg>']
    return ''.join(S)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--name",default="Maya")
    ap.add_argument("--out",default="output/character_studio")
    ap.add_argument("--palette",default="")
    args=ap.parse_args()
    palette=json.loads(args.palette) if args.palette else None
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    views=["front","threequarter","profile","back"]
    tiles=[]
    for view in views:
        svg=make_character(args.name,view,palette)
        svg_path=out/f"{args.name.lower()}_{view}.svg"
        png_path=out/f"{args.name.lower()}_{view}.png"
        svg_path.write_text(svg,encoding="utf-8")
        cairosvg.svg2png(bytestring=svg.encode(),write_to=str(png_path),output_width=640,output_height=900)
        tiles.append(Image.open(png_path).convert("RGB"))
    sheet=Image.new("RGB",(1280,1800),"#e9e2d4")
    for i,tile in enumerate(tiles):
        tile=tile.resize((640,900))
        sheet.paste(tile,((i%2)*640,(i//2)*900))
    sheet.save(out/f"{args.name.lower()}_turnaround.png",quality=95)
    report={"character":args.name,"views":views,"master_format":"SVG","preview":"PNG","canvas":"640x900","files":[p.name for p in sorted(out.iterdir())]}
    (out/"character_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
