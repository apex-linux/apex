#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GPU time per frame of each blurred shell surface at 2880x1800, stock ShellBlurEffect vs
# the Apex blur stage: a model, not a measurement, at half the Vega 7 peak rates.
import math
SURFACES=[("bar",1440,32,24),("dock",600,62,28),("quick settings",376,420,30),
   ("calendar",748,468,30),("spotlight",660,448,34),("toast",260,40,30),
   ("overview scrim",1440,900,36),("launcher scrim",1440,900,40),("lock bg",1440,900,30)]
SCALE=2
APEX_MAX_DOWNSAMPLED_SIGMA=4
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
BYTES_PER_S=25e9   # half of DDR4-3200 dual channel
BILINEAR_TAPS_PER_S=25e9   # half of 28 TMU x 1.8 GHz
def stock_cost(W,H,r):
    ds=stock_ds(W,H,r); tw,th=math.floor(W/ds),math.floor(H/ds)
    cds=clutter_ds(tw,th,r/ds); sig=(r/ds/2)/cds; bw,bh=math.floor(tw/cds),math.floor(th/cds)
    t=taps(sig); mt=2*t*bw*bh/1e6
    mb=(W*H*4*2 + W*H*4 + tw*th*4*2 + W*H*4*2)/1e6  # blit r+w, downsample read, brightness fb, final write+blend
    ms=(mb*1e6/BYTES_PER_S + (mt*1e6 + W*H)/BILINEAR_TAPS_PER_S)*1e3
    return ds*cds,t,mt,mb,ms
def apex_cost(W,H,sigma):
    ads=1
    while sigma/ads>APEX_MAX_DOWNSAMPLED_SIGMA and min(W,H)/(ads*2)>=4: ads*=2
    asig=sigma/ads; at=taps(asig); aw,ah=math.ceil(W/ads),math.ceil(H/ads)
    amt=2*at*aw*ah/1e6
    progressive_downsample_reads=sum((W/2**k)*(H/2**k) for k in range(1,int(math.log2(ads))+1))
    amb=(W*H*4*2 + (W*H+progressive_downsample_reads)*4 + aw*ah*4*4 + W*H*4*2)/1e6  # saturation and mask in the final pass
    ams=(amb*1e6/BYTES_PER_S + (amt*1e6+progressive_downsample_reads+W*H)/BILINEAR_TAPS_PER_S)*1e3
    return ads,at,amt,amb,ams
print(f"{'surface':16}{'dev WxH':>12}{'sigma':>6} | {'stock ds':>8}{'taps':>5}{'Mtaps':>7}{'MB':>6}{'ms':>6} | {'apex ds':>7}{'taps':>5}{'Mtaps':>7}{'MB':>6}{'ms':>6}")
for name,logical_w,logical_h,css_blur_logical_px in SURFACES:
    W,H=logical_w*SCALE,logical_h*SCALE; r=2*css_blur_logical_px*SCALE; sigma=r/2
    stock_ds_total,t,mt,mb,ms=stock_cost(W,H,r)
    ads,at,amt,amb,ams=apex_cost(W,H,sigma)
    print(f"{name:16}{W:>6}x{H:<5}{sigma:>6.0f} | {stock_ds_total:>8.0f}{t:>5}{mt:>7.1f}{mb:>6.1f}{ms:>6.2f} | {ads:>7}{at:>5}{amt:>7.2f}{amb:>6.1f}{ams:>6.2f}")
