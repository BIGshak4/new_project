import hashlib,itertools,json,random,runpy
from collections import Counter
from pathlib import Path

root=Path(__file__).resolve().parents[1]
grid=runpy.run_path(str(root/'solutions/prep_353_sampling_grids.py'))
image=runpy.run_path(str(root/'solutions/prep_354_image_pyramid.py'))
basin=runpy.run_path(str(root/'solutions/prep_355_plateau_basins.py'))
random.seed(1115)

def oracle_grids(width,height,a,b):
    def points(g):
        x,y,dx,dy,nx,ny=g
        return [(x+i*dx,y+j*dy) for i in range(nx) for j in range(ny)]
    def valid(g):
        return (all(type(v)is int for v in (width,height,*g)) and width>0 and height>0
                and g[2]>0 and g[3]>0 and g[4]>0 and g[5]>0
                and all(0<=x<width and 0<=y<height for x,y in points(g)))
    return valid(a) and valid(b) and all((x-u)**2+(y-v)**2>4 or (x,y)==(u,v)
                                        for x,y in points(a) for u,v in points(b))

def oracle_image(frame,levels):
    frame=[row[:] for row in frame];answer=[frame]
    for _ in range(levels):
        h,w=len(frame),len(frame[0])
        padded=[[frame[min(h-1,max(0,y))][min(w-1,max(0,x))]
                 for x in range(-1,w+1)] for y in range(-1,h+1)]
        blurred=[[sum(padded[y+dy][x+dx] for dy in range(3) for dx in range(3))//9
                  for x in range(w)] for y in range(h)]
        frame=[row[::2] for row in blurred[::2]];answer.append(frame)
    return answer

def oracle_basins(frame):
    h,w=len(frame),len(frame[0]);owner={};components=[]
    def neighbors(y,x):
        return [(u,v) for u in range(max(0,y-1),min(h,y+2))
                for v in range(max(0,x-1),min(w,x+2)) if (u,v)!=(y,x)]
    for y in range(h):
        for x in range(w):
            if (y,x) in owner:continue
            number=len(components);component=[];todo=[(y,x)];owner[y,x]=number
            while todo:
                a,b=todo.pop();component.append((a,b))
                for u,v in neighbors(a,b):
                    if (u,v) not in owner and frame[u][v]==frame[y][x]:
                        owner[u,v]=number;todo.append((u,v))
            components.append(component)
    outgoing={}
    for i,component in enumerate(components):
        lower={(frame[u][v],u,v) for y,x in component for u,v in neighbors(y,x)
               if frame[u][v]<frame[y][x]}
        if lower:
            _,y,x=min(lower);outgoing[i]=owner[y,x]
    counts=Counter()
    for y,x in owner:
        destination=owner[y,x]
        while destination in outgoing:destination=outgoing[destination]
        counts[destination]+=1
    return sorted(counts.values(),reverse=True)

grid_count=0
for _ in range(10000):
    width,height=random.randrange(1,15),random.randrange(1,15)
    a=[random.randrange(-1,width+1),random.randrange(-1,height+1),random.randrange(1,5),random.randrange(1,5),random.randrange(1,5),random.randrange(1,5)]
    b=[random.randrange(-1,width+1),random.randrange(-1,height+1),random.randrange(1,5),random.randrange(1,5),random.randrange(1,5),random.randrange(1,5)]
    assert grid['colored_grids_valid'](width,height,a,b)==oracle_grids(width,height,a,b)
    grid_count+=1
progressions=0
for _ in range(3000):
    a,b=random.randrange(-10,11),random.randrange(-10,11)
    da,db=random.randrange(1,12),random.randrange(1,12)
    na,nb=random.randrange(1,12),random.randrange(1,12)
    expected=bool(set(a+i*da for i in range(na))&set(b+i*db for i in range(nb)))
    assert grid['progression_intersects'](a,da,na,b,db,nb)==expected
    progressions+=1
image_count=0
for h,w,levels in itertools.product(range(1,8),range(1,8),range(6)):
    frame=[[random.randrange(256) for _ in range(w)] for _ in range(h)]
    expected=oracle_image(frame,levels)
    assert image['image_pyramid'](frame,levels)==expected
    assert image['collect_stream_pyramid']((row for row in frame),levels)==expected
    image_count+=1
assert image['collect_stream_pyramid']([[37]],1200)==[[[37]]]*1201
basin_count=0
for h,w in ((1,1),(1,5),(5,1),(2,2),(3,3),(5,6)):
    for _ in range(300):
        frame=[[random.randrange(-2,3) for _ in range(w)] for _ in range(h)]
        assert basin['basin_sizes'](frame)==oracle_basins(frame)
        basin_count+=1
paths=['solutions/prep_353_sampling_grids.py','solutions/prep_354_image_pyramid.py',
       'solutions/prep_355_plateau_basins.py','checks/check_images_peer1115c.py']
proof=dict(result='passed',random_grid_pairs=grid_count,progression_pairs=progressions,
           image_shapes_levels=image_count,deep_stream_levels=1200,basin_matrices=basin_count,
           sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})
(root/'checks/nov15c-images-peer-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
