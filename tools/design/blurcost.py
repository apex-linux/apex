#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Glass cost model for ADR 0014: GPU time per frame of each blurred shell surface at
# 2880x1800 (scale 2), for stock ShellBlurEffect and for the Apex blur stage. It is a
# model, not a measurement: bandwidth and texture rate are assumed at half the Vega 7
# peak. The laptop measurement in roadmap S2b and S3a decides.
#
#   python3 tools/design/blurcost.py
import math
# Surfaces: name, logical w, h, CSS blur px (sigma, logical)
S=[("bar",1440,32,24),("dock",600,62,28),("quick settings",376,420,30),
   ("calendar",748,468,30),("spotlight",660,448,34),("toast",260,40,30),
   ("overview scrim",1440,900,36),("launcher scrim",1440,900,40),("lock bg",1440,900,30)]
SCALE=2
def stock_ds(w,h,r):
    ds=1.0; sw,sh,sr=w,h,r
    while sr>12 and sw>256 and sh>256:
        ds*=2; sw,sh,sr=w/ds,h/ds,r/ds
    return ds
def clutter_ds(w,h,r):
    ds=1.0; sw,sh,ss=w,h,r/2
    while ss>6 and sw>256 and sh>256:
        ds*=2; sw,sh,ss=w/ds,h/ds,r/(2*ds)
    return ds
def taps(sigma):
    return 1+int(math.ceil(1.5*sigma))*2
BW=25e9   # effective bytes/s (half of DDR4-3200 dual channel)
TX=25e9   # effective bilinear taps/s (half of 28 TMU x 1.8 GHz)
print(f"{'surface':16}{'dev WxH':>12}{'sigma':>6} | {'stock ds':>8}{'taps':>5}{'Mtaps':>7}{'MB':>6}{'ms':>6} | {'apex ds':>7}{'taps':>5}{'Mtaps':>7}{'MB':>6}{'ms':>6}")
for n,w,h,b in S:
    W,H=w*SCALE,h*SCALE; r=2*b*SCALE; sigma=r/2
    # stock
    ds=stock_ds(W,H,r); tw,th=math.floor(W/ds),math.floor(H/ds)
    cds=clutter_ds(tw,th,r/ds); sig=(r/ds/2)/cds; bw,bh=math.floor(tw/cds),math.floor(th/cds)
    t=taps(sig); mt=2*t*bw*bh/1e6
    mb=(W*H*4*2 + W*H*4 + tw*th*4*2 + W*H*4*2)/1e6  # blit r+w, downsample read, brightness fb, final write+blend
    ms=(mb*1e6/BW + (mt*1e6 + W*H)/TX)*1e3
    # apex: ds so sigma/ds<=4, progressive 2x downsample, saturation+mask in final pass
    ads=1
    while sigma/ads>4 and min(W,H)/(ads*2)>=4: ads*=2
    asig=sigma/ads; at=taps(asig); aw,ah=math.ceil(W/ads),math.ceil(H/ads)
    amt=2*at*aw*ah/1e6
    # downsample chain: each level reads prev level once (bilinear 2x2)
    chain=sum((W/2**k)*(H/2**k) for k in range(1,int(math.log2(ads))+1))
    amb=(W*H*4*2 + (W*H+chain)*4 + aw*ah*4*4 + W*H*4*2)/1e6
    ams=(amb*1e6/BW + (amt*1e6+chain+W*H)/TX)*1e3
    print(f"{n:16}{W:>6}x{H:<5}{sigma:>6.0f} | {ds*cds:>8.0f}{t:>5}{mt:>7.1f}{mb:>6.1f}{ms:>6.2f} | {ads:>7}{at:>5}{amt:>7.2f}{amb:>6.1f}{ams:>6.2f}")
