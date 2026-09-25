"""HEAD STUDY 01 — métricas da cabeça (mesmo instrumento para todas as fontes).

Saída: out/head/metrics.json + out/head/metrics.txt

Classes (declaradas; ver docs/HEAD_STUDY_01.md §3):
  S  perfil sagital (marcos do corte médio)
  W  larguras (cortes horizontais; proxies declarados)
  PL planos (quão "plana" é a frente de um corte comparada com uma elipse do mesmo aspeto)
  CV cavidades + MASSA À VOLTA (recesso sob a ponte superior/inferior e medial/lateral)
  TR transições (crânio→face, face→pescoço, occipital)
  TP topologia (cage, sem Subdivision)
Unidades: mm à escala H = 226.1 mm (H = vértex − mentón); ângulos em graus.
"""
import json, os, sys, math
from collections import defaultdict, deque
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

H = C.H_MM
GEOM = ["ours", "whitewalker", "makehuman", "femalechar", "bodytopo", "femalebase"]   # ff11 excluído (declarado)


def ang(p, q, r):
    """Ângulo em q do triângulo p-q-r (graus), pontos (y,z)."""
    a = np.array(p) - np.array(q); b = np.array(r) - np.array(q)
    return float(np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))


def width_at(Vn, T, z, ymin=None):
    S = C.hsection(Vn, T, z)
    if not len(S):
        return np.nan
    P = S.reshape(-1, 2)
    if ymin is not None:
        P = P[P[:, 1] > ymin]
    return float(P[:, 0].max() - P[:, 0].min()) if len(P) else np.nan


def depth_map(Vn, T, xs, zs):
    D = np.full((len(zs), len(xs)), np.nan)
    for i, z in enumerate(zs):
        D[i] = C.front_contour(Vn, T, z, xs, ymin=0.0)
    return D


def planarity(Vn, T, z):
    """Frente de um corte horizontal: meia-largura onde a tangente chega a 45°
    (x45) sobre a meia-largura a (lateral máxima da metade da frente), comparada
    com a mesma razão numa elipse de semi-eixos (a, b), b = y_frente − y(a).
    PL > 1: frente mais plana que a elipse (planos); PL < 1: mais redonda/pontiaguda."""
    xs = np.arange(0.0, 0.6 * H, 0.5)
    y = C.front_contour(Vn, T, z, xs)
    g = ~np.isnan(y)
    if g.sum() < 10:
        return dict(PL=np.nan)
    xs, y = xs[g], y[g]
    # só até ao ponto lateral (onde a frente deixa de existir de forma contínua)
    cut = np.nonzero(np.diff(xs) > 1.01)[0]
    if len(cut):
        xs, y = xs[:cut[0] + 1], y[:cut[0] + 1]
    from scipy.ndimage import gaussian_filter1d
    ys = gaussian_filter1d(y, 2)
    sl = -np.gradient(ys, xs)
    a = xs[-1]; b = ys[0] - ys[-1]
    k = np.nonzero(sl >= 1.0)[0]
    x45 = xs[k[0]] if len(k) else a
    ell = a / math.sqrt(a * a + b * b) if b > 0 else np.nan
    return dict(x45=float(x45), a=float(a), b=float(b), ratio=float(x45 / a), ellipse_ratio=float(ell),
                PL=float((x45 / a) / ell) if ell == ell else np.nan)


def orbit(Vn, T, L):
    """Órbita = máximo do recesso da pele sob a ponte vertical (sobrancelha acima,
    malar abaixo) numa janela lateral ao nariz.  Mede a MASSA à volta da cavidade."""
    zn, zsn = L["nasion"][1], L["subnasale"][1]
    xs = np.arange(0.0, 0.34 * H, 1.0)
    zs = np.arange(zsn, L["glabella"][1] + 0.10 * H, 1.0)
    D = depth_map(Vn, T, xs, zs)
    up_w, dn_w = int(0.12 * H), int(0.15 * H)
    R = np.full_like(D, np.nan)
    for j in range(len(xs)):
        col = D[:, j]
        for i in range(len(zs)):
            if np.isnan(col[i]):
                continue
            u = col[i + 1:i + 1 + up_w]; d = col[max(0, i - dn_w):i]
            if np.all(np.isnan(u)) or np.all(np.isnan(d)):
                continue
            R[i, j] = min(np.nanmax(u), np.nanmax(d)) - col[i]
    win = (xs[None, :] > 0.08 * H) & (xs[None, :] < 0.22 * H) & \
          (zs[:, None] > zn - 0.14 * H) & (zs[:, None] < zn + 0.02 * H)
    Rw = np.where(win, R, -np.inf)
    i, j = np.unravel_index(np.nanargmax(Rw), Rw.shape)
    ze, xe, ye = zs[i], xs[j], D[i, j]
    col = D[:, j]
    up = np.nanmax(col[i + 1:i + 1 + up_w]); dn = np.nanmax(col[max(0, i - dn_w):i])
    row = D[i]
    med = np.nanmax(row[: j + 1])                          # ponte nasal / parede medial
    lat_x = xe + 0.10 * H
    lat = row[int(np.argmin(np.abs(xs - lat_x)))]
    # "hole": a pele existe no centro da órbita? (NaN = abertura sem pálpebra na coluna)
    return dict(orbit_z=float(ze), orbit_x=float(xe), orbit_recess=float(R[i, j]),
                brow_over_eye=float(up - ye), malar_below_eye=float(dn - ye),
                medial_wall=float(med - ye), lateral_rim_offset=float(lat - ye) if lat == lat else np.nan,
                nasion_minus_orbit_y=float(L["nasion"][0] - ye), _D=D, _xs=xs, _zs=zs, _R=R)


def nose_mouth(Vn, T, L):
    out = {}
    z_al = L["subnasale"][1] + 0.03 * H
    xs = np.arange(0.0, 0.30 * H, 0.5)
    y = C.front_contour(Vn, T, z_al, xs)
    from scipy.ndimage import gaussian_filter1d
    g = ~np.isnan(y)
    ys = np.interp(xs, xs[g], y[g]) if g.sum() > 3 else y
    ys = gaussian_filter1d(ys, 2)
    # sulco alar = ponto de CONCAVIDADE máxima (y'' máximo) em x ∈ [0.04, 0.16] H:
    # medido, a regra do mínimo local nunca disparava (a face também recua para o lado)
    d2 = np.gradient(np.gradient(ys, xs), xs)
    idx = np.nonzero((xs > 0.04 * H) & (xs < 0.16 * H))[0]
    k = int(idx[np.argmax(d2[idx])])
    out["alar_width"] = float(2 * xs[k]); out["nose_standoff_at_ala"] = float(ys[0] - ys[k])
    out["alar_concavity_peak"] = float(d2[k])
    # lábios relativos à linha subnasale→pogónio
    (ysn, zsn), (ypg, zpg) = L["subnasale"], L["pogonion"]
    line = lambda z: ysn + (z - zsn) / (zpg - zsn) * (ypg - ysn)
    out["upper_lip_vs_sn_pg"] = float(L["labrale_sup"][0] - line(L["labrale_sup"][1]))
    out["lower_lip_vs_sn_pg"] = float(L["labrale_inf"][0] - line(L["labrale_inf"][1]))
    out["mentolabial_depth"] = float(min(L["labrale_inf"][0], L["pogonion"][0]) - L["sulcus_mentolabial"][0])
    out["stomion_recess"] = float(min(L["labrale_sup"][0], L["labrale_inf"][0]) - L["stomion"][0])
    # comissura: no corte do estómio, primeiro mínimo local da frente para x > 0.06 H
    z_st = L["stomion"][1]
    y2 = C.front_contour(Vn, T, z_st + 1.0, xs)
    g2 = ~np.isnan(y2)
    if g2.sum() > 3:
        y2s = gaussian_filter1d(np.interp(xs, xs[g2], y2[g2]), 2)
        d22 = np.gradient(np.gradient(y2s, xs), xs)
        idx2 = np.nonzero((xs > 0.06 * H) & (xs < 0.18 * H))[0]
        k2 = int(idx2[np.argmax(d22[idx2])])
        out["mouth_width_proxy"] = float(2 * xs[k2]); out["commissure_concavity_peak"] = float(d22[k2])
    return out


def topology(name, Vn_cage_scale):
    """Cage (Subdivision 0): densidade face/crânio, polos e anéis concêntricos à volta dos olhos."""
    V, T, fs, fi = C.load_raw(name, "cage")
    s, zme, y0 = Vn_cage_scale
    Vn = V.copy(); Vn[:, 2] = (V[:, 2] - zme) * s; Vn[:, 0] *= s; Vn[:, 1] = V[:, 1] * s - y0
    starts = np.concatenate([[0], np.cumsum(fs)[:-1]])
    faces = [fi[a:a + n] for a, n in zip(starts, fs)]
    inhead = (Vn[:, 2] > -0.05 * H) & (np.abs(Vn[:, 0]) < 0.62 * H)
    faces_h = [f for f in faces if inhead[f].all()]
    adj = defaultdict(set); edge_count = defaultdict(int)
    for f in faces_h:
        for a, b in zip(f, np.roll(f, -1)):
            a, b = int(a), int(b)
            adj[a].add(b); adj[b].add(a); edge_count[(min(a, b), max(a, b))] += 1
    boundary = {e for e, c in edge_count.items() if c == 1}
    bverts = {v for e in boundary for v in e}
    verts = sorted(adj)
    val = {v: len(adj[v]) for v in verts}
    # "face" = frente (y > 0.25 H) e abaixo da glabela aproximada (z < 0.70 H)
    P = Vn
    face_v = [v for v in verts if P[v, 1] > 0.25 * H and P[v, 2] < 0.70 * H]
    cran_v = [v for v in verts if P[v, 2] > 0.75 * H]
    def med_edge(vs):
        vs = set(vs); L_ = [np.linalg.norm(P[a] - P[b]) for (a, b) in edge_count if a in vs and b in vs]
        return float(np.median(L_)) if L_ else np.nan
    poles = [v for v in verts if v not in bverts and val[v] != 4]
    poles_face = [v for v in poles if v in set(face_v)]
    fs_h = np.array([len(f) for f in faces_h])
    # laços de fronteira (aberturas) e anéis concêntricos limpos
    loops = []
    left = set(boundary)
    bad = defaultdict(set)
    for a, b in boundary:
        bad[a].add(b); bad[b].add(a)
    seen = set()
    for v0 in bverts:
        if v0 in seen:
            continue
        comp, st = [], [v0]
        while st:
            u = st.pop()
            if u in seen:
                continue
            seen.add(u); comp.append(u); st.extend(bad[u] - seen)
        loops.append(comp)
    res_loops = []
    for comp in loops:
        c = P[comp].mean(0)
        kind = None
        if abs(c[0]) > 0.07 * H and 0.40 * H < c[2] < 0.75 * H and c[1] > 0.2 * H:
            kind = "eye"
        elif abs(c[0]) < 0.05 * H and 0.05 * H < c[2] < 0.30 * H and c[1] > 0.2 * H:
            kind = "mouth"
        if kind is None:
            continue
        # BFS a partir do laço; anel k limpo = cada vértice tem exactamente 2 vizinhos no anel,
        # o anel é um ciclo único e tem o mesmo nº de vértices do laço (±25 %)
        dist = {v: 0 for v in comp}; q = deque(comp)
        while q:
            u = q.popleft()
            if dist[u] >= 8:
                continue
            for w in adj[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1; q.append(w)
        clean = 0
        for k in range(1, 8):
            ring = [v for v, d in dist.items() if d == k]
            rs = set(ring)
            if not ring:
                break
            ok = all(len(adj[v] & rs) == 2 for v in ring) and abs(len(ring) - len(comp)) <= 0.25 * len(comp) + 2
            if ok:
                st, cyc = [ring[0]], set()
                while st:
                    u = st.pop()
                    if u in cyc:
                        continue
                    cyc.add(u); st.extend((adj[u] & rs) - cyc)
                ok = len(cyc) == len(ring)
            if not ok:
                break
            clean += 1
        ext = P[comp].max(0) - P[comp].min(0)
        res_loops.append(dict(kind=kind, n=len(comp), centre=[round(float(x), 1) for x in c],
                              extent_xz=[round(float(ext[0]), 1), round(float(ext[2]), 1)], clean_rings=clean))
    return dict(head_verts=len(verts), head_faces=len(faces_h), quad_ratio=float((fs_h == 4).mean()),
                tris=int((fs_h == 3).sum()), ngons=int((fs_h > 4).sum()),
                face_verts=len(face_v), cranium_verts=len(cran_v),
                median_edge_face=med_edge(face_v), median_edge_cranium=med_edge(cran_v),
                poles=len(poles), poles_face=len(poles_face),
                poles_face_pos=[[round(float(x), 1) for x in P[v]] for v in poles_face],
                open_loops=res_loops, _P=P, _faces=faces_h, _poles=poles)


def analyse(name):
    Vn, T, fs, fi, info = C.normalise(name)
    L, (zs, yf, yb, pts) = C.sagittal_landmarks(Vn, T)
    M = {"info": info, "landmarks": L}
    g, n, prn, sn = L["glabella"], L["nasion"], L["pronasale"], L["subnasale"]
    pg, op, c = L["pogonion"], L["opisthocranion"], L["cervical"]
    # --- S
    S = {}
    S["S1_nasal_projection"] = prn[0] - sn[0]
    S["S2_nasion_depth"] = g[0] - n[0]
    S["S3_facial_convexity_g_sn_pg"] = ang(g, sn, pg)
    S["S4_chin_vs_sn"] = pg[0] - sn[0]
    S["S5_glabella_ahead_of_centre"] = g[0]
    S["S6_pronasale_ahead_of_centre"] = prn[0]
    S["S7_head_length_g_op"] = g[0] - op[0]
    k = lambda z: int(np.argmin(np.abs(zs - z)))
    zf = g[1] + 0.20 * H
    S["S8_forehead_incl_deg"] = float(np.degrees(np.arctan2(yf[k(g[1])] - yf[k(zf)], zf - g[1])))
    S["S9_nasion_z"] = n[1]; S["S9_subnasale_z"] = sn[1]; S["S9_stomion_z"] = L["stomion"][1]
    S["S10_lower_face_ratio_sn_sto_over_sto_me"] = (sn[1] - L["stomion"][1]) / L["stomion"][1]
    S["S11_mid_face_n_sn_over_sn_me"] = (n[1] - sn[1]) / sn[1]
    M["S"] = S
    # --- TR
    TR = {}
    TR["TR1_occipital_overhang"] = L["nape_recess"][0] - op[0]
    # ângulo cervicomentoniano: linha submentoniana (pogónio-inferior → cervical) vs pescoço
    zlow = c[1] - 0.20 * H
    neck_pt = (yf[k(zlow)], zlow)
    sub_pt = (yf[k(0.5)], 0.5)
    TR["TR2_cervicomental_deg"] = ang(sub_pt, c, neck_pt)
    TR["TR3_submental_len"] = float(math.hypot(sub_pt[0] - c[0], sub_pt[1] - c[1]))

    M["TR"] = TR
    # --- W
    W = {}
    W["W1_head_breadth_max"] = max(width_at(Vn, T, z) for z in np.arange(0.62 * H, 0.90 * H, 2.0))
    W["W2_bizygomatic_proxy"] = max(width_at(Vn, T, z, ymin=20.0) for z in np.arange(sn[1], n[1], 2.0))
    W["W3_min_frontal_proxy"] = min(width_at(Vn, T, z, ymin=20.0) for z in np.arange(g[1], g[1] + 0.15 * H, 2.0))
    W["W4_face_w_at_stomion"] = width_at(Vn, T, L["stomion"][1], ymin=0.0)
    W["W5_face_w_at_0.10H"] = width_at(Vn, T, 0.10 * H, ymin=0.0)
    W["W6_neck_min_w"] = min(width_at(Vn, T, z) for z in np.arange(-0.30 * H, -0.04 * H, 2.0))
    W["R_cephalic_breadth_over_length"] = W["W1_head_breadth_max"] / S["S7_head_length_g_op"]
    W["R_bizyg_over_breadth"] = W["W2_bizygomatic_proxy"] / W["W1_head_breadth_max"]
    W["R_jaw_taper_0.10H_over_bizyg"] = W["W5_face_w_at_0.10H"] / W["W2_bizygomatic_proxy"]
    W["R_minfrontal_over_bizyg"] = W["W3_min_frontal_proxy"] / W["W2_bizygomatic_proxy"]
    TR["TR4_neck_min_w_over_bizyg"] = W["W6_neck_min_w"] / W["W2_bizygomatic_proxy"]
    M["W"] = W
    # --- PL
    PL = {}
    for tag, z in (("forehead", g[1] + 0.08 * H), ("cheek", 0.5 * (n[1] + sn[1])), ("mouth", 0.5 * (sn[1] + L["stomion"][1])),
                   ("chin", 0.08 * H), ("cranium", 0.85 * H)):
        PL[tag] = planarity(Vn, T, z)
    M["PL"] = PL
    # --- CV
    O = orbit(Vn, T, L)
    M["CV_orbit"] = {k_: v for k_, v in O.items() if not k_.startswith("_")}
    M["CV_nose_mouth"] = nose_mouth(Vn, T, L)
    M["_orbit_maps"] = O
    M["_profile"] = (zs, yf, yb, pts)
    M["_mesh"] = (Vn, T)
    # --- TP
    tp = topology(name, (info["scale"], info["z_menton_src"], info["y0_mm_before"]))
    M["TP"] = {k_: v for k_, v in tp.items() if not k_.startswith("_")}
    M["_topo"] = tp
    return M


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if o != o else round(float(o), 3)
    if isinstance(o, np.integer):
        return int(o)
    return o


def run():
    R = {}
    for n in GEOM:
        R[n] = analyse(n)
        print("analisado", n, flush=True)
    json.dump({n: clean(m) for n, m in R.items()}, open(os.path.join(C.WORK, "metrics.json"), "w"), indent=1)
    return R


if __name__ == "__main__":
    R = run()
    J = json.load(open(os.path.join(C.WORK, "metrics.json")))
    rows = []
    for sec in ("S", "W", "TR", "CV_orbit", "CV_nose_mouth"):
        for k in J["ours"][sec]:
            vals = [J[n][sec].get(k) for n in GEOM]
            refs = [v for v in vals[1:] if v is not None]
            rng = f"{min(refs):8.2f} … {max(refs):8.2f}" if refs else "—"
            rows.append(f"{sec:14s} {k:42s} " + " ".join(f"{(v if v is not None else float('nan')):9.2f}" for v in vals) + f"   refs {rng}")
    for tag in J["ours"]["PL"]:
        vals = [J[n]["PL"][tag].get("PL") for n in GEOM]
        refs = [v for v in vals[1:] if v is not None]
        rows.append(f"{'PL':14s} {tag:42s} " + " ".join(f"{(v if v is not None else float('nan')):9.2f}" for v in vals) + f"   refs {min(refs):8.2f} … {max(refs):8.2f}")
    for k in ("head_verts", "quad_ratio", "median_edge_face", "median_edge_cranium", "poles", "poles_face"):
        vals = [J[n]["TP"][k] for n in GEOM]
        rows.append(f"{'TP':14s} {k:42s} " + " ".join(f"{float(v):9.2f}" for v in vals))
    head = f"{'':14s} {'métrica':42s} " + " ".join(f"{n[:9]:>9s}" for n in GEOM)
    txt = head + "\n" + "\n".join(rows)
    open(os.path.join(C.WORK, "metrics.txt"), "w").write(txt)
    print(txt)
    for n in GEOM:
        print(n, "loops", J[n]["TP"]["open_loops"])
