import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import json, numpy as np, math
A=json.load(open(WORK + "/ansur_ratios.json"))["ratios"]
def ell(w,d): a,b=w/2,d/2; h=((a-b)/(a+b))**2; return math.pi*(a+b)*(1+3*h/(10+math.sqrt(4-3*h)))
def metrics(name):
    r=json.load(open(WORK + f"/prof_{name}.json")); P=r["prof"]; S=1700.0
    C=[p for p in P if p["center"]]
    def rng(lo,hi,src=C): return [p for p in src if lo*S<=p["z"]<=hi*S]
    m={}
    m["crotchheight"]=max(p["z"] for p in P if not p["center"] and p["z"]<0.62*S)
    ch=max(rng(.68,.78),key=lambda p:p["depth"]); m["chest_z"]=ch["z"]; m["chestdepth"]=ch["depth"]; m["chestbreadth"]=ch["width"]; m["chestcircumference"]=ch["circ"]
    wn=min(rng(.58,.70),key=lambda p:p["width"]); m["waist_nat_z"]=wn["z"]; m["waist_nat_breadth"]=wn["width"]
    om=min(C,key=lambda p:abs(p["z"]-0.6017*S)); m["waistbreadth"]=om["width"]; m["waistdepth"]=om["depth"]; m["waistcircumference"]=om["circ"]
    lo=m["crotchheight"]/S+0.005
    hb=max(rng(lo,.58),key=lambda p:p["width"]); m["hip_z"]=hb["z"]; m["hipbreadth"]=hb["width"]
    bd=max(rng(lo,.58),key=lambda p:p["depth"]); m["buttock_z"]=bd["z"]; m["buttockdepth"]=bd["depth"]
    m["buttockcircumference"]=max(p["circ"] for p in rng(lo,.58))
    nk=min(rng(.80,.875),key=lambda p:p["width"]); m["neck_z"]=nk["z"]; m["neck_breadth"]=nk["width"]; m["neck_depth"]=nk["depth"]; m["neckcircumference"]=nk["circ"]
    # legs
    L=[p for p in P if "legs" in p]
    def leg(p): return max(p["legs"],key=lambda l:l["cx"])      # left leg (+x)
    th=[p for p in L if (m["crotchheight"]-60)<=p["z"]<=m["crotchheight"]-20]
    m["thighcircumference"]=max(ell(leg(p)["w"],leg(p)["d"]) for p in th) if th else float("nan")
    kn=[p for p in L if .25*S<=p["z"]<=.31*S]; m["knee_min_circ"]=min(ell(leg(p)["w"],leg(p)["d"]) for p in kn)
    ca=[p for p in L if .17*S<=p["z"]<=.26*S]; cmax=max(ca,key=lambda p:ell(leg(p)["w"],leg(p)["d"])); m["calfcircumference"]=ell(leg(cmax)["w"],leg(cmax)["d"]); m["calf_z"]=cmax["z"]
    an=[p for p in L if .05*S<=p["z"]<=.12*S]
    if an: m["anklecircumference"]=min(ell(leg(p)["w"],leg(p)["d"]) for p in an)
    # leg axis: centre x of left leg at hip-ish, knee, ankle
    def cx_at(z): p=min(L,key=lambda p:abs(p["z"]-z)); return leg(p)["cx"]
    m["leg_cx_thigh"]=cx_at(m["crotchheight"]-40); m["leg_cx_knee"]=cx_at(.2756*S); m["leg_cx_ankle"]=cx_at(.07*S) if an else float("nan")
    m["leg_gap_knee"]=2*(cx_at(.2756*S))-leg(min(L,key=lambda p:abs(p["z"]-.2756*S)))["w"]
    # head
    H=[p for p in P if p["z"]>=.88*S and "sil_xmax" in p]
    m["headbreadth"]=max(p["sil_xmax"]-p["sil_xmin"] for p in H); m["headlength"]=max(p["sil_ymax"]-p["sil_ymin"] for p in H)
    # sagittal back curve (mid_back): thoracic apex, buttock apex, lumbar concavity
    B=[(p["z"],p["mid_back"],p["mid_front"]) for p in C if not math.isnan(p.get("mid_back",float("nan")))]
    B=np.array(B)
    def ap(lo,hi,col=1,f=np.argmin):
        s=B[(B[:,0]>=lo*S)&(B[:,0]<=hi*S)]; i=f(s[:,col]); return s[i]
    t=ap(.70,.82); b=ap(lo,.58)
    seg=B[(B[:,0]<t[0])&(B[:,0]>b[0])]
    yline=b[1]+(seg[:,0]-b[0])/(t[0]-b[0])*(t[1]-b[1])
    k=np.argmax(seg[:,1]-yline)
    m["thoracic_apex_z"]=t[0]; m["buttock_apex_z"]=b[0]; m["lumbar_concavity"]=float((seg[:,1]-yline)[k]); m["lumbar_z"]=float(seg[k,0])
    m["buttock_behind_thoracic"]=float(t[1]-b[1])   # + = nádega mais posterior que as costas torácicas
    # abdomen: front midline at omphalion vs under bust
    f_om=om["mid_front"]; f_wn=wn["mid_front"]; m["abdomen_front_minus_waist_front"]=f_om-f_wn
    # H3 (pré-registo docs/H3H2_TRUNK.md): barriga em COTAS FIXAS -- a métrica
    # acima usa a cota da largura mínima, que H3 desloca (risco de melhorar por
    # construção).  frente(omphalion 0.6017·S) - frente(0.70·S).
    f70=min(C,key=lambda p:abs(p["z"]-0.70*S))["mid_front"]; m["belly_front_fixed"]=f_om-f70
    # H1 (REF STUDY 01 §4.3): perfil cabeça–pescoço–costas altas na linha média
    N=[p for p in C if 1330<=p["z"]<=1640 and not math.isnan(p.get("mid_back",float("nan")))]
    zN=np.array([p["z"] for p in N]); bN=np.array([p["mid_back"] for p in N]); dN=np.array([p["depth"] for p in N])
    hi=zN>1520; zo=zN[hi][np.argmin(bN[hi])]; bo=bN[hi].min()                       # occipital
    mid=(zN>1380)&(zN<zo); zn=zN[mid][np.argmax(bN[mid])]; bn=bN[mid].max()           # nuca (mais anterior)
    lo_=(zN<zn); zs=zN[lo_][np.argmin(bN[lo_])]; bs=bN[lo_].min()                      # costas altas mais posteriores
    m["occiput_z"]=float(zo); m["nape_z"]=float(zn); m["nape_recess"]=float(bn-bo)
    m["upper_back_z"]=float(zs); m["upper_back_vs_occiput"]=float(bs-bo)
    # pico de profundidade na base do pescoço: máx. em [1380,1450] menos máx. em [1300,1360]
    m["neckbase_depth_max"]=float(dN[(zN>=1380)&(zN<=1450)].max())
    m["neckbase_depth_excess"]=float(dN[(zN>=1380)&(zN<=1450)].max()-dN[(zN>=1300)&(zN<=1360)].max())
    return m
ANS={"crotchheight":"crotchheight","chestdepth":"chestdepth","chestbreadth":"chestbreadth","chestcircumference":"chestcircumference",
     "waistbreadth":"waistbreadth","waistdepth":"waistdepth","waistcircumference":"waistcircumference","hipbreadth":"hipbreadth","buttockdepth":"buttockdepth",
     "buttockcircumference":"buttockcircumference","neckcircumference":"neckcircumference","thighcircumference":"thighcircumference",
     "calfcircumference":"calfcircumference","anklecircumference":"anklecircumference","headbreadth":"headbreadth","headlength":"headlength"}
if __name__=="__main__":
    names=["ours","femalebase","femalechar","bodytopo"]
    M={n:metrics(n) for n in names}; json.dump(M,open(WORK + "/metrics.json","w"),indent=1,default=float)
    print(f"{'@1700mm':28s} {'ANSUR':>7s} {'p5-p95':>11s} "+" ".join(f"{n:>10s}" for n in names)+"   ours/ANSUR")
    for k,a in ANS.items():
        R=A[a]; lo,hi=R["p5"]*1700,R["p95"]*1700
        vals=[M[n].get(k,float('nan')) for n in names]
        flag="" if lo<=vals[0]<=hi else "  <-- fora p5-p95"
        print(f"{k:28s} {R['r']*1700:7.0f} {lo:5.0f}-{hi:<5.0f} "+" ".join(f"{v:10.0f}" for v in vals)+f"   {vals[0]/(R['r']*1700):5.2f}{flag}")
    print()
    for a,b,key in [("chestdepth","chestbreadth","chestdepth/chestbreadth"),("waistdepth","waistbreadth","waistdepth/waistbreadth"),("buttockdepth","hipbreadth","buttockdepth/hipbreadth"),("waistbreadth","hipbreadth","waistbreadth/hipbreadth"),("waistcircumference","buttockcircumference","waistcircumference/buttockcircumference")]:
        R=A[key]; print(f"{key:40s} ANSUR {R['r']:.3f} [{R['p5']:.3f},{R['p95']:.3f}] "+" ".join(f"{n}={M[n][a]/M[n][b]:.3f}" for n in names))
    print()
    for k in ["chest_z","waist_nat_z","waist_nat_breadth","hip_z","buttock_z","neck_z","neck_breadth","neck_depth","calf_z","knee_min_circ","leg_cx_thigh","leg_cx_knee","leg_cx_ankle","leg_gap_knee","thoracic_apex_z","buttock_apex_z","lumbar_z","lumbar_concavity","buttock_behind_thoracic","abdomen_front_minus_waist_front","belly_front_fixed",
              "occiput_z","nape_z","nape_recess","upper_back_z","upper_back_vs_occiput","neckbase_depth_max","neckbase_depth_excess"]:
        print(f"{k:34s} "+" ".join(f"{n}={M[n].get(k,float('nan')):7.1f}" for n in names))
