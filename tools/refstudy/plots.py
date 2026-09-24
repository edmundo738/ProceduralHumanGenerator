import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
A=json.load(open(WORK + "/ansur_ratios.json"))["ratios"]
names=["ours","femalebase","femalechar","bodytopo"]; col={"ours":"#d62728","femalebase":"#1f77b4","femalechar":"#2ca02c","bodytopo":"#9467bd"}
P={n:json.load(open(WORK + f"/prof_{n}.json"))["prof"] for n in names}
def arr(n,k): 
    C=[p for p in P[n] if p["center"] and k in p]; return np.array([p["z"] for p in C]), np.array([p[k] for p in C])
fig,ax=plt.subplots(1,4,figsize=(20,9),sharey=True)
for n in names:
    z,w=arr(n,"width"); _,d=arr(n,"depth"); _,c=arr(n,"circ")
    lw=3 if n=="ours" else 1.4
    ax[0].plot(w,z,color=col[n],lw=lw,label=n); ax[1].plot(d,z,color=col[n],lw=lw); ax[2].plot(c,z,color=col[n],lw=lw)
    _,f=arr(n,"mid_front"); _,b=arr(n,"mid_back")
    # alinhar: costas na altura da omoplata (z≈0.76S) em y=0
    z2,bb=arr(n,"mid_back"); ref=np.nanmin(bb[(z2>0.72*1700)&(z2<0.80*1700)])
    ax[3].plot(f-ref,z,color=col[n],lw=lw); ax[3].plot(b-ref,z,color=col[n],lw=lw,ls="--")
def band(a,key,zkey,sc=1700):
    R=A[key]; zr=A[zkey]["r"]*sc
    a.errorbar(R["r"]*sc,zr,xerr=[[R["r"]*sc-R["p5"]*sc],[R["p95"]*sc-R["r"]*sc]],fmt="ks",capsize=4,ms=6)
band(ax[0],"chestbreadth","chestheight"); band(ax[0],"waistbreadth","waistheightomphalion"); band(ax[0],"hipbreadth","trochanterionheight")
band(ax[1],"chestdepth","chestheight"); band(ax[1],"waistdepth","waistheightomphalion"); band(ax[1],"buttockdepth","buttockheight")
band(ax[2],"chestcircumference","chestheight"); band(ax[2],"waistcircumference","waistheightomphalion"); band(ax[2],"buttockcircumference","buttockheight"); band(ax[2],"neckcircumference","cervicaleheight")
for a,t in zip(ax,["LARGURA do tronco (mm)","PROFUNDIDADE do tronco (mm)","CIRCUNFERÊNCIA (casco convexo, mm)","PERFIL SAGITAL linha média (y mm)\n— frente   -- costas   (alinhado nas omoplatas)"]):
    a.set_title(t); a.grid(alpha=.3); a.set_ylim(700,1650)
for zk,lab in [("cervicaleheight","C7"),("suprasternaleheight","jugulum"),("chestheight","busto"),("tenthribheight","10ª costela"),("waistheightomphalion","umbigo"),("iliocristaleheight","crista ilíaca"),("trochanterionheight","trocânter"),("crotchheight","gancho")]:
    for a in ax: a.axhline(A[zk]["r"]*1700,color="gray",lw=.6,ls=":")
    ax[0].text(ax[0].get_xlim()[0] if False else 20,A[zk]["r"]*1700+4,f"ANSUR {lab}",fontsize=8,color="gray")
ax[0].set_xlim(0,650); ax[1].set_xlim(0,420); ax[2].set_xlim(0,1400)
ax[0].legend(loc="lower right"); ax[0].set_ylabel("altura (mm, estatura normalizada 1700)")
plt.suptitle("Tronco: BUILD (vermelho) vs 3 referências 3D do commit 408517a vs ANSUR II feminino (■ média, barra p5–p95)",fontsize=13)
plt.tight_layout(); plt.savefig(WORK + "/fig_torso_profiles.png",dpi=70)
