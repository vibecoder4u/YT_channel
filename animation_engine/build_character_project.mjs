#!/usr/bin/env node
/**
 * Build an actual Rigby2D .rigby skeletal character, AutoRig it, author keyframes,
 * and produce validation reports. The upstream runtime is pinned by the workflow.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const ROOT = process.cwd();
const VENDOR = path.join(ROOT, 'vendor', 'rigby2d');
const CLI = path.join(VENDOR, 'bin', 'rigby.js');
const BUILD = path.join(ROOT, 'build');
const ART = path.join(BUILD, 'character-art');
const PSD = path.join(BUILD, 'maya-rigged-character.psd');
const RAW = path.join(BUILD, 'maya-character-artwork.rigby');
const RIG = path.join(BUILD, 'maya-character.rigby');
const requireRigby = createRequire(path.join(VENDOR, 'package.json'));
const { writePsd } = requireRigby('ag-psd');
const { decodePng } = await import(pathToFileURL(path.join(VENDOR, 'src', 'mcp', 'png.js')).href);

await fs.mkdir(BUILD, { recursive: true });
const manifest = JSON.parse(await fs.readFile(path.join(ART, 'layers.json'), 'utf8'));

function cli(args, label) {
  const p = spawnSync(process.execPath, [CLI, ...args], {
    cwd: ROOT, encoding: 'utf8', maxBuffer: 40 * 1024 * 1024,
    env: { ...process.env, CI: '1' },
  });
  if (p.status !== 0) {
    throw new Error(label + ' failed (exit ' + p.status + ').\nSTDOUT:\n' + p.stdout + '\nSTDERR:\n' + p.stderr);
  }
  return (p.stdout || '').trim();
}
function parseJson(out, label) {
  try { return JSON.parse(out); }
  catch { throw new Error(label + ' did not return JSON:\n' + out.slice(0, 5000)); }
}

const children = [];
for (const layer of manifest.layers) {
  const png = new Uint8Array(await fs.readFile(layer.file));
  const imageData = decodePng(png);
  children.push({
    name: layer.name,
    left: layer.left,
    top: layer.top,
    hidden: !!layer.hidden,
    opacity: 1,
    blendMode: 'normal',
    imageData: { width: imageData.width, height: imageData.height, data: imageData.data },
  });
}
const psd = {
  width: manifest.canvas.width,
  height: manifest.canvas.height,
  bitsPerChannel: 8,
  colorMode: 3,
  children,
};
const psdBytes = writePsd(psd, { generateThumbnail: false });
await fs.writeFile(PSD, Buffer.from(psdBytes));
console.log('PSD: ' + children.length + ' transparent parts, ' + manifest.canvas.width + 'x' + manifest.canvas.height);

cli(['import-psd', PSD, '--out', RAW, '--force', '--json'], 'Rigby2D PSD import');
cli(['autorig', RAW, '--out', RIG, '--meshes', 'deforming', '--force', '--json'], 'Rigby2D AutoRig');
const prep = spawnSync('python', ['animation_engine/prepare_rig.py', RIG], { cwd: ROOT, encoding: 'utf8' });
if (prep.status !== 0) throw new Error('Rig preparation failed: ' + prep.stderr + prep.stdout);
const rigControls = parseJson(prep.stdout.trim(), 'Rig preparation');
await fs.writeFile(path.join(BUILD, 'rig-controls-report.json'), JSON.stringify(rigControls, null, 2));
console.log(JSON.stringify(rigControls));

cli(['call', 'set_workspace', '--path', RIG, '--workspace', 'film', '--json'], 'Film workspace setup');
cli(['call', 'set_output', '--path', RIG, '--fps', '30', '--width', '1280', '--height', '720',
  '--background', 'transparent', '--framing', 'auto', '--json'], 'Film output setup');

const rigReport = parseJson(cli(['call', 'describe_rig', '--path', RIG, '--json'], 'Describe rig'), 'describe_rig');
await fs.writeFile(path.join(BUILD, 'rig-report.json'), JSON.stringify(rigReport, null, 2));
const boneNames = new Set((rigReport.bones || []).map(b => b.name));
const slotMap = new Map((rigReport.slots || []).map(s => [s.name, s]));
const ops = [{ op: 'add_animation', name: 'character_showcase', duration: 12.2 }];

function roundTime(t) { return Math.round(t * 30) / 30; }
function boneKey(name, time, channel, values, curve = 'linear') {
  if (!boneNames.has(name)) return;
  ops.push({ op: 'set_bone_key', animation: 'character_showcase', bone: name, channel, time: roundTime(time), ...values, curve });
}
function rot(name, time, degrees) {
  boneKey(name, time, 'rotate', { value: Number(degrees.toFixed(3)) });
}
function xy(name, time, x, y) {
  boneKey(name, time, 'translate', { x: Number(x.toFixed(3)), y: Number(y.toFixed(3)) });
}
function slotKey(name, time, show) {
  const slot = slotMap.get(name);
  if (!slot) return;
  const attachment = slot.attachments?.[0]?.name;
  if (!attachment && show) return;
  ops.push({
    op: 'set_attachment_key', animation: 'character_showcase', slot: name, time: roundTime(time),
    ...(show ? { attachment } : { hide: true }),
  });
}
function switchViews(time, view) {
  const groups = {
    front: ['head_front', 'torso', 'pelvis'],
    threequarter: ['head_threequarter', 'torso', 'pelvis'],
    profile: ['head_profile', 'torso_profile', 'pelvis_profile'],
    backlook: ['head_back3q', 'torso_profile', 'pelvis_profile'],
  };
  const all = ['head_front','head_threequarter','head_profile','head_back3q','torso','torso_profile','pelvis','pelvis_profile'];
  const visible = new Set(groups[view] || []);
  for (const name of all) if (slotMap.has(name)) slotKey(name, time, visible.has(name));
}
function sampleTimes(start, end, stepFrames = 3) {
  const a = Math.round(start * 30), b = Math.round(end * 30);
  const frames = [];
  for (let f = a; f <= b; f += stepFrames) frames.push(f / 30);
  if (frames.at(-1) !== b / 30) frames.push(b / 30);
  return frames;
}
function ease01(x) { x = Math.max(0, Math.min(1, x)); return x*x*(3-2*x); }

const root = boneNames.has('root') ? 'root' : (rigReport.bones?.[0]?.name ?? 'root');
const baseline = parseJson(cli(['call','sample_pose','--path',RIG,'--json'],'Sample setup pose'),'sample_pose');
const world = new Map((baseline.bones || []).map(b => [b.name, b]));
const footBase = {
  l: world.get('ik_foot_l') || world.get('foot_l') || { x: 80, y: 100 },
  r: world.get('ik_foot_r') || world.get('foot_r') || { x: -80, y: 100 },
};
const hasFootIK = boneNames.has('ik_foot_l') && boneNames.has('ik_foot_r');

switchViews(0, 'front');

// Intro: anticipation, breath, eyes-on-camera, then a clean three-quarter and profile turn.
for (const [t, h, c, n] of [
  [0,0,0,0],[0.45,1.5,-0.8,-0.6],[0.9,0,-0.2,0],[1.2,2,2,1],
  [1.6,4,4,2],[2.0,3,2,1],[2.2,0,0,0]
]) {
  rot('head', t, h); rot('chest', t, c); rot('neck', t, n);
}
switchViews(1.2, 'threequarter');
switchViews(2.2, 'profile');

// Walk: the root advances steadily while IK foot targets remain planted in stance,
// then lift and swing through to the next contact. Arms counter-swing and torso follows.
const walkStart = 3.0, walkEnd = 5.2, walkPeriod = 0.78, walkStride = 66;
for (const t of sampleTimes(walkStart, walkEnd, 3)) {
  const u = t - walkStart;
  const dx = u / walkPeriod * walkStride;
  const phaseL = (u / walkPeriod) % 1;
  const phaseR = (phaseL + 0.5) % 1;
  const bounce = Math.abs(Math.sin(2 * Math.PI * u / walkPeriod)) * 11;
  xy(root, t, dx, bounce);
  for (const [side, phase] of [['l',phaseL],['r',phaseR]]) {
    const cycle = Math.floor(u / walkPeriod + (side === 'r' ? 0.5 : 0));
    let targetX = cycle * walkStride;
    let targetY = 0;
    if (phase >= 0.62) {
      const swing = (phase - 0.62) / 0.38;
      targetX += walkStride * ease01(swing);
      targetY = 88 * Math.sin(Math.PI * swing);
    }
    if (hasFootIK) {
      const base = footBase[side];
      xy('ik_foot_' + side, t, targetX - dx, targetY);
    }
    const s = Math.sin(phase * 2 * Math.PI);
    // Arm IK is intentionally removed in prepare_rig.py so shoulder/elbow arcs are free to swing.
    rot('upperarm_' + side, t, -34 * s);
    rot('forearm_' + side, t, 18 + 18 * Math.max(0, -s));
  }
  rot('hip', t, -4.5 * Math.sin(2 * Math.PI * u / walkPeriod));
  rot('chest', t, 3.8 * Math.sin(2 * Math.PI * u / walkPeriod + 0.35));
  rot('head', t, 2.0 * Math.sin(2 * Math.PI * u / walkPeriod + 0.6));
}

// Stop with anticipation, heel plant and upper-body follow-through.
const walkDistance = (walkEnd-walkStart)/walkPeriod*walkStride;
for (const t of sampleTimes(5.2, 5.95, 2)) {
  const q = (t - 5.2) / 0.75;
  const settle = 1 - Math.pow(1-q, 3);
  xy(root, t, walkDistance + 15*settle, 0);
  rot('hip', t, -5*Math.exp(-q*4));
  rot('chest', t, 8*Math.exp(-q*3) - 1.5);
  rot('head', t, -3*Math.exp(-q*3));
  rot('upperarm_l', t, -8*Math.exp(-q*3));
  rot('upperarm_r', t, 7*Math.exp(-q*3));
}

// A deliberate over-the-shoulder look: separate back-three-quarter head art, not a spun front face.
switchViews(5.95, 'backlook');
for (const [t,h,n,c] of [[5.95,0,0,0],[6.15,-8,-4,1],[6.45,-18,-7,2],[6.8,-13,-5,1],[7.0,-7,-2,0]]) {
  rot('head',t,h); rot('neck',t,n); rot('chest',t,c);
}
switchViews(7.0, 'profile');

// Run: shorter flight phases, longer stride, stronger arm drive and higher vertical bounce.
const runStart = 7.0, runEnd = 8.85, runPeriod = 0.50, runStride = 78;
const xAtRun = walkDistance + 15;
for (const t of sampleTimes(runStart, runEnd, 2)) {
  const u = t - runStart;
  const dx = xAtRun + u / runPeriod * runStride;
  const pL = (u / runPeriod) % 1;
  const pR = (pL + 0.5) % 1;
  const bounce = 14 + 18 * Math.max(0, Math.sin(4*Math.PI*u/runPeriod));
  xy(root, t, dx, bounce);
  for (const [side, phase] of [['l',pL],['r',pR]]) {
    const cycle = Math.floor(u / runPeriod + (side === 'r' ? 0.5 : 0));
    let targetX = cycle * runStride;
    let targetY = 0;
    if (phase >= 0.48) {
      const swing = (phase - 0.48) / 0.52;
      targetX += runStride * ease01(swing);
      targetY = 138 * Math.sin(Math.PI*swing);
    }
    if (hasFootIK) xy('ik_foot_' + side, t, targetX - u/runPeriod*runStride, targetY);
    const s = Math.sin(phase * 2 * Math.PI);
    // Foot targets define the planted and flight arcs; limb rotations are solved by leg IK.
    rot('upperarm_' + side,t,-54*s);
    rot('forearm_' + side,t,34+24*Math.max(0,-s));
  }
  rot('hip',t,-6*Math.sin(2*Math.PI*u/runPeriod));
  rot('chest',t,9+5*Math.sin(2*Math.PI*u/runPeriod+0.4));
  rot('head',t,-2+2*Math.sin(2*Math.PI*u/runPeriod));
}
const runDistance = (runEnd-runStart)/runPeriod*runStride;
const xAtJump = xAtRun + runDistance;

// Jump sequence: crouch, explosive takeoff, airborne tuck, landing compression and settle.
for (const [t,x,y,hip,chest,arm,thigh,shin] of [
  [8.85,xAtJump,0,12,-7,-12,25,28],
  [9.0,xAtJump+5,-24,20,-9,-40,35,45],
  [9.18,xAtJump+10,125,-5,8,-100,-16,35],
  [9.38,xAtJump+14,245,-8,10,-112,-23,52],
  [9.56,xAtJump+18,258,-3,7,-96,-18,44],
  [9.74,xAtJump+22,175,4,3,-58,12,28],
  [9.9,xAtJump+24,52,15,-9,8,28,35],
  [10.02,xAtJump+25,-16,20,-11,10,18,46],
  [10.18,xAtJump+25,-6,8,-4,-5,8,18],
  [10.38,xAtJump+25,0,0,0,0,0,0],
]) {
  xy(root,t,x,y);
  rot('hip',t,hip); rot('chest',t,chest);
  rot('upperarm_l',t,arm); rot('upperarm_r',t,arm-8);
  rot('forearm_l',t,-18); rot('forearm_r',t,-12);
  rot('head',t,-3);
  // Tuck both feet during flight, then extend them back under the hips for landing.
  const tuck = Math.sin(Math.PI * Math.max(0, Math.min(1, (t-9.0)/0.95)));
  if (hasFootIK) {
    xy('ik_foot_l',t,-34*tuck,82*tuck);
    xy('ik_foot_r',t, 34*tuck,82*tuck);
  }
  rot('hand_l',t,-10*tuck); rot('hand_r',t,10*tuck);
}
switchViews(10.38,'front');
for (const [t,h,c] of [[10.38,0,0],[10.8,3,-1],[11.2,0,0],[11.6,-2,1],[12.2,0,0]]) {
  rot('head',t,h); rot('chest',t,c); rot('neck',t,0);
  rot('upperarm_l',t,0); rot('upperarm_r',t,0);
  rot('forearm_l',t,0); rot('forearm_r',t,0);
  rot('hand_l',t,0); rot('hand_r',t,0);
}
xy(root,10.38,xAtJump+25,0); xy(root,12.2,xAtJump+25,0);

const opFile = path.join(BUILD, 'animation-operations.json');
await fs.writeFile(opFile, JSON.stringify({ path: RIG, operations: ops, overwrite: true }, null, 2));
cli(['call','batch_edit','--args-file',opFile,'--json'],'Author skeletal animation keys');
const validation = parseJson(cli(['call','validate_project','--path',RIG,'--json'],'Rig validation'),'validate_project');
await fs.writeFile(path.join(BUILD,'rig-validation.json'), JSON.stringify(validation,null,2));
const animation = parseJson(cli(['call','describe_animation','--path',RIG,'--animation','character_showcase','--json'],'Animation inspection'),'describe_animation');
await fs.writeFile(path.join(BUILD,'animation-report.json'), JSON.stringify(animation,null,2));
console.log('Rig: ' + (rigReport.bones?.length || 0) + ' bones, ' + (rigReport.slots?.length || 0) + ' slots');
console.log('Animation: ' + animation.duration + 's, ' + (animation.bones?.length || 0) + ' animated bone timelines');
console.log('Validation: ' + JSON.stringify(validation).slice(0,1200));
