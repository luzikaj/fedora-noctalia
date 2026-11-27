# Renders the "noctalia-night" wallpaper. Usage:
#   rsvg-convert -w 3840 -h 2160 noctalia-night-shapes.svg -o shapes.png && python3 make-wallpaper.py
# Original artwork for this repo (no third-party assets).
import numpy as np
from PIL import Image
W,H=3840,2160
rng=np.random.default_rng(45)
y,x=np.mgrid[0:H,0:W].astype(np.float32)
t=np.clip((x/W*0.45+y/H*0.75)/1.2,0,1)[...,None]
top=np.array([10,12,30],np.float32); bot=np.array([34,16,52],np.float32)
img=top*(1-t)+bot*t
# violet haze near moon and a cool haze bottom-left
def radial(cx,cy,r,col,a):
    d=np.sqrt((x-cx)**2+(y-cy)**2)/r
    return (np.exp(-d**2)*a)[...,None]*np.array(col,np.float32)
img+=radial(2930,610,1100,[70,45,130],0.55)
img+=radial(700,1900,1300,[20,30,80],0.45)
# stars
n=1400
sx=rng.integers(0,W,n); sy=rng.integers(0,H,n)
b=rng.power(6,n)*200
for px,py,v in zip(sx,sy,b):
    img[py,px]+=v
    if v>150:
        for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
            if 0<=px+dx<W and 0<=py+dy<H: img[py+dy,px+dx]+=v*0.35
# composite shapes
s=np.asarray(Image.open("shapes.png").convert("RGBA"),np.float32)
a=s[...,3:]/255
img=img*(1-a)+s[...,:3]*a
# grain against banding
img+=rng.normal(0,1.6,img.shape).astype(np.float32)
out=Image.fromarray(np.clip(img,0,255).astype(np.uint8))
for w,h in((3840,2160),(2560,1440),(1920,1080)):
    out.resize((w,h),Image.LANCZOS).save(f"noctalia-night-{w}x{h}.png",optimize=True)
out.resize((1280,720),Image.LANCZOS).save("preview.png")
