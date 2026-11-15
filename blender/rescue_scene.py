import bpy, math, os
from mathutils import Vector
# Standalone low-poly 3D rescue previs. No external assets required.
OUT=os.environ.get("BLENDER_OUTPUT","output/blender-rescue.mp4")
os.makedirs(os.path.dirname(OUT),exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=16
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.fps=24; scene.frame_start=1; scene.frame_end=480
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'; scene.render.ffmpeg.codec='H264'; scene.render.ffmpeg.constant_rate_factor='MEDIUM'
scene.render.filepath=os.path.abspath(OUT)
scene.world.color=(0.22,0.28,0.32)
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metal; m.roughness=.72; return m
sand=mat('warm riverbank',(0.48,.34,.19)); water=mat('deep turquoise river',(.025,.28,.36),.15)
rock=mat('river stones',(.27,.30,.27)); skin=mat('warm skin',(.72,.43,.29))
hair=mat('dark hair',(.055,.035,.028)); teal=mat('Maya teal',(.035,.38,.42)); gold=mat('Arun ochre',(.72,.38,.08)); green=mat('Leena olive',(.24,.34,.14))
ropeMat=mat('rope',(.48,.27,.09)); leaf=mat('forest green',(.07,.22,.12))
def cube(name,loc,scale,ma,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma)
 if bevel: mod=o.modifiers.new('soft edges','BEVEL'); mod.width=bevel; mod.segments=2
 return o
def uv(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(ma); bpy.ops.object.shade_smooth(); return o
def cyl(name,a,b,r,ma):
 mid=(Vector(a)+Vector(b))/2; vec=Vector(b)-Vector(a)
 bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=vec.length, location=mid); o=bpy.context.object; o.name=name; o.data.materials.append(ma); o.rotation_mode='QUATERNION'; o.rotation_quaternion=vec.to_track_quat('Z','Y'); return o
# Ground, river, forest ridge and stones
cube('bank',(0,0,-.28),(24,15,.5),sand)
cube('river',(0,3,-.02),(24,5,.22),water)
for i in range(12):
 x=-10+i*1.8
 uv('river ripple',(x,3+math.sin(i)*.6,.12),(.7,.035,.018),mat('ripple%d'%i,(.16,.55,.59)))
for i in range(9):
 x=-10+i*2.5
 uv('distant tree',(x,6,1.6),(1.1,1.1,2.4),leaf)
for x in (-4,-2,0,2,4):
 uv('stepping stone',(x,1,.28),(0.85,.55,.32),rock)
# Camera / lighting
bpy.ops.object.camera_add(location=(0,-17,9)); cam=bpy.context.object
cam.rotation_euler=(Vector((0,1.1,1.0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'; cam.data.ortho_scale=19; scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-4,-8,12)); light=bpy.context.object; light.data.energy=1700; light.data.shape='DISK'; light.data.size=10
# Character made of separate articulated meshes; limb segments keyframed for motion.
def character(name,x,coat):
 parts={}
 parts['root']=bpy.data.objects.new(name+'_root',None); scene.collection.objects.link(parts['root']); parts['root'].location=(x,-1,0)
 def add(key,obj,loc):
  obj.parent=parts['root']; obj.location=loc; parts[key]=obj; return obj
 add('torso',cube(name+'_jacket',(0,0,0),(.72,.42,1.05),coat,.12),(0,0,1.45))
 add('head',uv(name+'_head',(0,0,0),(.31,.29,.34),skin),(0,-.01,2.23))
 add('hair',uv(name+'_hair',(0,0,0),(.32,.3,.16),hair),(0,.015,2.48))
 # limb segments as thin cuboids, pivots represented by origins for simple swing
 for side,sgn in [('L',-1),('R',1)]:
  arm=cube(name+'_arm_'+side,(0,0,0),(.18,.2,.78),coat,.07); add('arm'+side,arm,(sgn*.48,0,1.63))
  leg=cube(name+'_leg_'+side,(0,0,0),(.22,.25,.78),mat(name+'_trousers',(.12,.15,.16)),.06); add('leg'+side,leg,(sgn*.22,0,.52))
  shoe=cube(name+'_shoe_'+side,(0,0,0),(.38,.48,.16),hair,.04); add('shoe'+side,shoe,(sgn*.22,-.1,.12))
 return parts
maya=character('Maya',-4.2,teal); arun=character('Arun',0,gold); leena=character('Leena',4.2,green)
def key(obj,frame,loc=None,rot=None):
 if loc is not None: obj.location=loc; obj.keyframe_insert(data_path='location',frame=frame)
 if rot is not None: obj.rotation_euler=rot; obj.keyframe_insert(data_path='rotation_euler',frame=frame)
# continuous walk-in
for ch,start,end in [(maya,-6,-3.5),(arun,-2,0),(leena,6,3.5)]:
 for f in (1,100): key(ch['root'],f,(start+(end-start)*(f-1)/99,-1,0))
 for side,sgn in [('L',1),('R',-1)]:
  for f in range(1,101,12):
   phase=(f/100*math.tau)+(0 if side=='L' else math.pi)
   key(ch['leg'+side],f,(sgn*.22,0,.52),(math.sin(phase)*.42,0,0))
   key(ch['arm'+side],f,(sgn*.48,0,1.63),(-math.sin(phase)*.34,0,0))
# Plan / slip / fall / pull / recover beats, 20 seconds (480 frames)
for ch in (maya,arun,leena):
 for f in (101,170,240,360,420,480): key(ch['root'],f,ch['root'].location)
# Maya braces, Arun slips down then recovers; Leena reaches for rope
key(arun['root'],170,(-.2,-1,0)); key(arun['root'],205,(.1,-1,-.55)); key(arun['root'],260,(.1,-1,-.55)); key(arun['root'],360,(.1,-1,0)); key(arun['root'],420,(.3,-1,0)); key(arun['root'],480,(.8,-1,0))
key(arun['torso'],170,(0,0,1.45)); key(arun['torso'],205,(.35,0,.85),(0,0,-.5)); key(arun['torso'],260,(.35,0,.85),(0,0,-.5)); key(arun['torso'],360,(0,0,1.45)); key(arun['torso'],480,(0,0,1.45))
for ch in (maya,leena):
 for f,ang in ((170,0),(205,-.8),(260,-.8),(360,-.35),(420,0),(480,0)):
  key(ch['armR'],f,(.48,0,1.63),(0,0,ang))
# Rope as animated bevelled curve between friends
cu=bpy.data.curves.new('rescue rope','CURVE'); cu.dimensions='3D'; cu.bevel_depth=.035; cu.bevel_resolution=3
sp=cu.splines.new('POLY'); sp.points.add(2)
for p,co in zip(sp.points,[(-.1,-1.2,1.55),(.0,-1.3,1.2),(.2,-1.2,.9)]): p.co=(*co,1)
rope=bpy.data.objects.new('rope',cu); scene.collection.objects.link(rope); rope.data.materials.append(ropeMat)
for f,z in ((1,1.2),(205,.65),(300,.75),(360,1.15),(480,1.2)):
 rope.location.z=z; rope.keyframe_insert(data_path='location',frame=f)
# camera subtle push
cam.data.lens=48
for f,s in ((1,19),(240,17.8),(480,19)):
 cam.data.ortho_scale=s; cam.data.keyframe_insert(data_path='ortho_scale',frame=f)
scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='Standard'
scene.frame_set(1)
bpy.ops.render.render(animation=True)
print('BLENDER_RENDER_COMPLETE',OUT)
