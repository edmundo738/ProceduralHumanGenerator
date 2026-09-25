"""HEAD STUDY 01 — figuras com um instrumento ÚNICO para todas as fontes.

Rasterizador numpy (sem Blender, sem materiais, sem cabelo): amostragem densa dos
triângulos + z-buffer + Lambert cinza neutro, câmara ortográfica.  O mesmo código,
luz e enquadramento (mm@H226) para todas as fontes, para que a beleza do render
não mascare geometria.

Saída: docs/head_study_01/*.png
  renders.png        frente / lado / ¾ (superfície suavizada, só pele)
  wire.png           cage (Subdivision 0) frente e ¾, polos (valência ≠ 4) a vermelho
  profiles.png       perfil sagital da frente sobreposto + larguras por altura
  orbit_maps.png     mapa de profundidade da frente (y) e mapa de recesso da órbita
"""
import os
import sys
import math
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C          # noqa: E402
import analyse as A         # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

H = C.H_MM
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "head_study_01")
ALL = A.GEOM + ["ff11"]
LABEL = {"ours": "NOSSA (c7ab2932)", "whitewalker": "whitewalker", "makehuman": "makehuman (Lucia fbx)",
         "femalechar": "femalechar", "bodytopo": "bodytopo", "femalebase": "femalebase",
         "ff11": "ff11 (só render; mentón inválido)"}


def view_matrix(kind):
    """Devolve R (3x3): linhas = eixo u (direita do ecrã), v (cima), d (para a câmara)."""
    if kind == "front":
        a = 0.0
    elif kind == "side":
        a = 90.0
    else:
        a = 40.0
    t = math.radians(a)
    # câmara no plano horizontal, a olhar para -d; d roda de +y (frente) para +x
    d = np.array([math.sin(t), math.cos(t), 0.0])
    u = np.array([math.cos(t), -math.sin(t), 0.0])
    if kind == "side":
        u = -u
    v = np.array([0.0, 0.0, 1.0])
    return np.stack([u, v, d])


def raster(V, T, kind, box, px=1.0, light=(-0.45, 0.55, 0.70)):
    """Imagem cinza + z-buffer. box = (umin, umax, vmin, vmax) em mm."""
    R = view_matrix(kind)
    P = V @ R.T
    u0, u1, v0, v1 = box
    W = int((u1 - u0) / px); Hh = int((v1 - v0) / px)
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    n = np.cross(b - a, c - a)
    area2 = np.linalg.norm(n[:, :2], axis=1) / (px * px)       # área projetada (px²)×2
    ln = np.linalg.norm(n, axis=1) + 1e-12
    nn = n / ln[:, None]
    L = np.array(light); L = L / np.linalg.norm(L)
    # normais por vértice (média ponderada por área), orientadas pela normal da face
    # antes de somar (fontes com orientação mista); sombreamento Gouraud |n·L|
    vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, T[:, k], n)
    vn /= np.linalg.norm(vn, axis=1)[:, None] + 1e-12
    vs = np.clip(np.abs(vn @ L), 0, 1) * 0.78 + 0.18
    cnt = np.clip(np.ceil(area2 * 4.0).astype(int), 2, 8000)
    idx = np.repeat(np.arange(len(T)), cnt)
    rng = np.random.default_rng(0)
    r1 = rng.random(len(idx)); r2 = rng.random(len(idx))
    s = np.sqrt(r1)
    w0 = 1 - s; w1 = s * (1 - r2); w2 = s * r2
    Q = a[idx] * w0[:, None] + b[idx] * w1[:, None] + c[idx] * w2[:, None]
    # vértices também (arestas finas)
    iu = ((Q[:, 0] - u0) / px).astype(int); iv = ((v1 - Q[:, 1]) / px).astype(int)
    ok = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < Hh)
    shv = vs[T[idx, 0]] * w0 + vs[T[idx, 1]] * w1 + vs[T[idx, 2]] * w2
    iu, iv, dep, sh = iu[ok], iv[ok], Q[ok, 2], shv[ok]
    lin = iv * W + iu
    zb = np.full(W * Hh, -np.inf)
    np.maximum.at(zb, lin, dep)
    # píxeis em que a superfície da frente não recebeu amostra deixavam passar a de
    # trás (medido: salpicos).  Dilata-se o z-buffer 3×3 e só se aceitam amostras
    # próximas da frente dilatada; os buracos restantes são preenchidos pelo vizinho.
    from scipy.ndimage import maximum_filter, distance_transform_edt
    zb2 = zb.reshape(Hh, W)
    zd = maximum_filter(np.where(np.isfinite(zb2), zb2, -1e9), size=3).ravel()
    win = dep >= zd[lin] - 1.5 * px
    img = np.full(W * Hh, np.nan)
    img[lin[win]] = sh[win]
    img = img.reshape(Hh, W)
    cover = np.isfinite(zb2)
    hole = np.isnan(img) & cover
    if hole.any():
        _, (ii, jj) = distance_transform_edt(np.isnan(img), return_indices=True)
        img[hole] = img[ii[hole], jj[hole]]
    img[~cover] = 1.0
    return img, zb2, R


def load_norm(name, tag="smooth"):
    """(Vn, T) normalizados.  ff11: enquadramento pela caixa (declarado, sem métricas)."""
    if name != "ff11":
        Vn, T, fs, fi, info = C.normalise(name, tag)
        return Vn, T, info
    V, T, fs, fi = C.load_raw(name, tag)
    top = V[:, 2].max()
    # cabeça da ff11: medido no orient.png ~ 0.23 da altura do asset acima do pescoço
    hh = 0.21 * (top - V[:, 2].min())
    s = H / hh
    Vn = V.copy(); Vn[:, 2] = (V[:, 2] - (top - hh)) * s; Vn[:, 0] *= s
    Vn[:, 1] = -V[:, 1] * s; Vn[:, 0] *= -1          # ff11 olha para −y (observado no render)
    Vn[:, 1] -= 0.5 * (Vn[:, 1][Vn[:, 2] > 0.6 * H].max() + Vn[:, 1][Vn[:, 2] > 0.6 * H].min())
    keep = (Vn[:, 2] > -0.45 * H) & (np.abs(Vn[:, 0]) < 0.62 * H)
    return Vn, T[keep[T].all(1)], {"scale": s}


def cage_norm(name, info):
    V, T, fs, fi = C.load_raw(name, "cage")
    s = info["scale"]
    Vn = V.copy(); Vn[:, 2] = (V[:, 2] - info["z_menton_src"]) * s; Vn[:, 0] *= s
    Vn[:, 1] = V[:, 1] * s - info["y0_mm_before"]
    return Vn, T, fs, fi


BOX = {"front": (-120, 120, -60, 240), "side": (-130, 150, -60, 240), "q": (-130, 150, -60, 240)}


def fig_renders(data):
    names = [n for n in ALL if n in data]
    fig, ax = plt.subplots(len(names), 3, figsize=(9.6, 3.35 * len(names)))
    for r, nm in enumerate(names):
        Vn, T = data[nm]["smooth"]
        for c, kind in enumerate(("front", "side", "q")):
            img, _, _ = raster(Vn, T, kind, BOX[kind])
            ax[r, c].imshow(img, cmap="gray", vmin=0, vmax=1, extent=BOX[kind])
            ax[r, c].set_xticks([]); ax[r, c].set_yticks([])
            if c == 0:
                ax[r, c].set_ylabel(LABEL[nm], fontsize=9)
            if r == 0:
                ax[r, c].set_title({"front": "frente", "side": "lado", "q": "¾ (40°)"}[kind], fontsize=10)
            for z in (0, H):
                ax[r, c].axhline(z, color="#48c", lw=0.5, alpha=0.6)
    fig.suptitle("HEAD STUDY 01 — mesmo rasterizador, cinza neutro, sem cabelo/materiais; mm@H226 (linhas azuis: mentón e vértex)",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(os.path.join(OUT, "renders.png"), dpi=110)
    plt.close(fig)


def edges_of(fs, fi):
    starts = np.concatenate([[0], np.cumsum(fs)[:-1]])
    E = set()
    val = {}
    for a0, n in zip(starts, fs):
        f = fi[a0:a0 + n]
        for i in range(n):
            p, q = int(f[i]), int(f[(i + 1) % n])
            E.add((min(p, q), max(p, q)))
    E = np.array(sorted(E))
    return E


def fig_wire(data):
    names = [n for n in A.GEOM if n in data]
    fig, ax = plt.subplots(2, len(names), figsize=(3.3 * len(names), 7.2))
    for c, nm in enumerate(names):
        Vc, Tc, fs, fi = data[nm]["cage"]
        E = edges_of(fs, fi)
        # valência só com arestas da cabeça, e só para vértices interiores (não fronteira)
        inh = (Vc[:, 2] > -0.05 * H) & (np.abs(Vc[:, 0]) < 0.62 * H)
        Eh = E[inh[E].all(1)]
        val = np.bincount(Eh.ravel(), minlength=len(Vc))
        # fronteira: arestas usadas por 1 face
        starts = np.concatenate([[0], np.cumsum(fs)[:-1]])
        from collections import Counter
        ec = Counter()
        for a0, n in zip(starts, fs):
            f = fi[a0:a0 + n]
            for i in range(n):
                p, q = int(f[i]), int(f[(i + 1) % n]); ec[(min(p, q), max(p, q))] += 1
        bnd = np.zeros(len(Vc), bool)
        for (p, q), k in ec.items():
            if k == 1:
                bnd[p] = bnd[q] = True
        pole = inh & ~bnd & (val > 0) & (val != 4) & (Vc[:, 2] > 0.0)   # sem a linha de recorte
        for r, kind in enumerate(("front", "q")):
            img, zb, R = raster(Vc, Tc, kind, BOX[kind], px=1.0)
            a_ = ax[r, c]
            a_.imshow(img * 0.35 + 0.65, cmap="gray", vmin=0, vmax=1, extent=BOX[kind])
            P = Vc @ R.T
            u0, u1, v0, v1 = BOX[kind]
            Wd = zb.shape[1]; Hd = zb.shape[0]

            def vis(pts):
                iu = np.clip(((pts[:, 0] - u0)).astype(int), 0, Wd - 1)
                iv = np.clip(((v1 - pts[:, 1])).astype(int), 0, Hd - 1)
                return pts[:, 2] >= zb[iv, iu] - 2.5
            mid = 0.5 * (P[Eh[:, 0]] + P[Eh[:, 1]])
            ok = vis(mid)
            segs = np.stack([P[Eh[ok, 0], :2], P[Eh[ok, 1], :2]], 1)
            from matplotlib.collections import LineCollection
            a_.add_collection(LineCollection(segs, colors="k", linewidths=0.35))
            pv = np.nonzero(pole)[0]
            pv = pv[vis(P[pv])]
            a_.scatter(P[pv, 0], P[pv, 1], s=5, c=np.where(val[pv] > 4, "#d11", "#16c"), zorder=5, lw=0)
            a_.set_xlim(u0, u1); a_.set_ylim(v0, v1)
            a_.set_xticks([]); a_.set_yticks([])
            if r == 0:
                a_.set_title(f"{LABEL[nm]}\ncage {int(inh.sum())} v cabeça", fontsize=8)
    fig.suptitle("Cage (Subdivision 0). Polos interiores: vermelho = valência > 4, azul = 3.  Fronteiras (aberturas) excluídas.", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "wire.png"), dpi=120)
    plt.close(fig)


COL = {"ours": "#d62728", "whitewalker": "#7f7f7f", "makehuman": "#1f77b4", "femalechar": "#9467bd",
       "bodytopo": "#2ca02c", "femalebase": "#ff7f0e"}


def fig_profiles(data, metrics):
    fig, ax = plt.subplots(1, 3, figsize=(15, 6.2))
    for nm in A.GEOM:
        if nm not in metrics:
            continue
        zs, yf, yb, pts = metrics[nm]["_profile"]
        lw = 2.2 if nm == "ours" else 1.0
        ax[0].plot(yf, zs, color=COL[nm], lw=lw, label=nm)
        ax[0].plot(yb, zs, color=COL[nm], lw=lw * 0.6, ls=":")
        L = metrics[nm]["landmarks"]
        for k in ("glabella", "nasion", "pronasale", "subnasale", "stomion", "pogonion"):
            if k in L and L[k] is not None:
                ax[0].plot(*L[k], "o", ms=3, color=COL[nm])
        Vn, T = data[nm]["smooth"]
        zz = np.arange(-0.30 * H, H, 2.0)
        w = [A.width_at(Vn, T, z) for z in zz]
        ax[1].plot(w, zz, color=COL[nm], lw=lw, label=nm)
        # meio-perfil da face: frente em x = 0.15H (coluna para-sagital, passa pela órbita)
        zc, yc = C.column_profile(Vn, T, 0.15 * H, -0.1 * H, H)
        ax[2].plot(yc, zc, color=COL[nm], lw=lw, label=nm)
    ax[0].set_title("Perfil sagital (frente contínua, costas pontilhado)\nmm@H226; y = 0 no centro glabela–opistocrânio", fontsize=9)
    ax[1].set_title("Largura máxima do corte por altura", fontsize=9)
    ax[2].set_title("Perfil para-sagital em x = 0.15·H (≈ 34 mm): testa → órbita → malar → boca", fontsize=9)
    for a_ in ax:
        a_.set_aspect("equal"); a_.grid(alpha=0.3); a_.axhline(0, color="k", lw=0.4)
        a_.set_ylabel("z acima do mentón (mm)")
    ax[0].set_xlabel("y (mm, + = frente)"); ax[1].set_xlabel("largura (mm)"); ax[2].set_xlabel("y (mm)")
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "profiles.png"), dpi=110)
    plt.close(fig)


def fig_orbit(metrics):
    names = [n for n in A.GEOM if n in metrics]
    fig, ax = plt.subplots(2, len(names), figsize=(2.9 * len(names), 7.0))
    for c, nm in enumerate(names):
        O = metrics[nm]["_orbit_maps"]
        D, R, xs, zs = O["_D"], O["_R"], O["_xs"], O["_zs"]
        L = metrics[nm]["landmarks"]
        ext = (xs[0], xs[-1], zs[0], zs[-1])
        # profundidade relativa ao nasion (0 = plano do nasion)
        ax[0, c].imshow(D[::-1] - L["nasion"][0], cmap="viridis", vmin=-45, vmax=25, extent=ext, aspect="equal")
        ax[0, c].contour(xs, zs, D - L["nasion"][0], levels=np.arange(-45, 26, 5), colors="w", linewidths=0.35)
        ax[1, c].imshow(np.clip(R, 0, None)[::-1], cmap="magma", vmin=0, vmax=22, extent=ext, aspect="equal")
        for a_ in ax[:, c]:
            a_.plot(O["orbit_x"], O["orbit_z"], "c+", ms=10)
            a_.set_xticks([0, 30, 60]); a_.tick_params(labelsize=7)
        ax[0, c].set_title(f"{nm}\nfrente y − y(nasion) [−45, 25] mm", fontsize=8)
        ax[1, c].set_title(f"recesso sob a ponte vertical\nmáx {O['orbit_recess']:.1f} mm", fontsize=8)
    fig.suptitle("Órbita: meia-face direita, x = 0 (linha média) → 0.34·H; z de subnasale a glabela + 0.10·H. "
                 "Branco/NaN = abertura sem pele (olho não incluído em nenhuma fonte).", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "orbit_maps.png"), dpi=110)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    data, metrics = {}, {}
    for nm in ALL:
        Vn, T, info = load_norm(nm)
        data[nm] = {"smooth": (Vn, T)}
        if nm != "ff11":
            data[nm]["cage"] = cage_norm(nm, info)
            metrics[nm] = A.analyse(nm)
        print("carregado", nm)
    which = sys.argv[1:] or ["renders", "wire", "profiles", "orbit"]
    if "renders" in which:
        fig_renders(data)
    if "wire" in which:
        fig_wire(data)
    if "profiles" in which:
        fig_profiles(data, metrics)
    if "orbit" in which:
        fig_orbit(metrics)
    print("OK", which)


if __name__ == "__main__":
    main()
