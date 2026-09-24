import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
cfg={"ours":dict(flip=False),"femalebase":dict(flip=False),"femalechar":dict(flip=True),"bodytopo":dict(flip=True)}
bt=json.load(open(WORK + "/cfg_bodytopo.json")); drop=json.load(open(WORK + "/drop_ours.json"))
col={"ours":"#d62728","femalebase":"#1f77b4","femalechar":"#2ca02c","bodytopo":"#9467bd"}
fig,ax=plt.subplots(1,3,figsize=(18,10))
for n,c in cfg.items():
    d=np.load(WORK + f"/raw_{n}.npz"); V=d["V"].copy(); T=d["T"]; lab=np.load(WORK + f"/lab_{n}.npy")
    if n=="bodytopo": S,fl=bt["stature_override"],bt["floor_override"]
    else: S,fl=V[:,2].max()-V[:,2].min(),V[:,2].min()
    V[:,2]-=fl; V[:,0]-=(V[:,0].max()+V[:,0].min())/2; V*=1700/S
    if c["flip"]: V[:,1]*=-1
    keep=~np.isin(lab,drop) if n=="ours" else np.ones(len(V),bool)
    Tk=T[keep[T[:,0]]]; Tk=Tk[(np.abs(V[Tk][:,:,0]).max(1)<200)]          # sem braços
    # alinhar Y pela linha média das costas nas omoplatas
    sel=(V[:,2]>1220)&(V[:,2]<1360)&(np.abs(V[:,0])<15); V[:,1]-=V[sel,1].min()
    a=0.9 if n=="ours" else 0.0
    for k,(i,j) in enumerate(((0,2),(1,2))):
        ax[k].add_collection(PolyCollection(V[Tk][:,:,[i,j]],facecolor=col[n] if n=="ours" else "none",edgecolor="none",alpha=0.25 if n=="ours" else 0))
    # contornos via cortes: usar extents dos perfis já medidos
    P=json.load(open(WORK + f"/prof_{n}.json"))["prof"]
    z=np.array([p["z"] for p in P if p["center"]]); 
    for k,(lo,hi) in enumerate((("width",None),("front","back"))):
        pass
    C=[p for p in P if "sil_xmin" in p]
    zz=np.array([p["z"] for p in C])
    # lateral: contorno do tronco+pernas
    L=[p for p in P if p["center"]]
    zc=np.array([p["z"] for p in L]); w=np.array([p["width"] for p in L])
    ax[0].plot(w/2,zc,color=col[n],lw=3 if n=="ours" else 1.5,label=n); ax[0].plot(-w/2,zc,color=col[n],lw=3 if n=="ours" else 1.5)
    ref=np.nanmin([p["back"] for p in L if 1220<p["z"]<1360])
    ax[1].plot([p["front"]-ref for p in L],zc,color=col[n],lw=3 if n=="ours" else 1.5,label=n)
    ax[1].plot([p["back"]-ref for p in L],zc,color=col[n],lw=3 if n=="ours" else 1.5)
    # pernas: contorno da perna esquerda
    G=[p for p in P if "legs" in p]
    zg=np.array([p["z"] for p in G]); lg=[max(p["legs"],key=lambda l:l["cx"]) for p in G]
    cx=np.array([l["cx"] for l in lg]); lw_=np.array([l["w"] for l in lg]); ld=np.array([l["d"] for l in lg])
    ax[2].plot(cx-lw_/2,zg,color=col[n],lw=3 if n=="ours" else 1.5,label=n); ax[2].plot(cx+lw_/2,zg,color=col[n],lw=3 if n=="ours" else 1.5)
    ax[2].plot(cx,zg,color=col[n],lw=.8,ls=":")
for a,t in zip(ax,["FRENTE — largura do tronco (±w/2)","LADO — contorno frente/costas do tronco","PERNA ESQUERDA — bordos medial/lateral e eixo (:)"]):
    a.set_title(t); a.grid(alpha=.3); a.set_aspect("equal"); a.legend(loc="lower left",fontsize=8)
ax[0].set_ylim(750,1650); ax[1].set_ylim(750,1650); ax[2].set_ylim(0,900); ax[2].set_xlim(-50,250)
plt.tight_layout(); plt.savefig(WORK + "/fig_silhouettes.png",dpi=65)
