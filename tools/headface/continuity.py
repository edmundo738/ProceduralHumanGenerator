# -*- coding: utf-8 -*-
"""CHECKPOINT CONT1 — continuidade anatómica: onde as massas parecem "coladas".

Instrumento comum para a nossa cabeça e as refs (mm@H226, mesma normalização do
HEAD STUDY 01):

  secções planares (interseção triângulo–plano → polilinha → κ(s))
    ear_h    horizontal pela meia-altura da orelha (z≈92.5)
    ear_v    vertical pela profundidade média da orelha (y=−25)
    orbit_h  horizontal pela linha da fenda (z≈105), canto lateral da órbita
    (as secções sagitais cruza também geometria escondida dentro do pescoço —
     por isso a nuca e o mento usam PERFIS DE SILHUETA, o que o olho vê)
  perfis de silhueta visível (front_profile do estudo)
    nape_p   costas: occipital → nuca → pescoço (yb por z)
    chin_p   frente: mento → submeno → garganta (yf por z)

κ = dθ/ds ao longo do arco (amostragem 0.5 mm, suavização caixa 2 mm).

MÉTRICAS por janela (a mesma janela anatómica para todos):
  κ_p99  pico de curvatura robusto (1/mm) — "quina"
  turn   ∫|κ| na janela (graus) — o quanto a secção vira
  conc   concentração: fração do turn a ±3 mm do pico de κ
         (alto = viragem súbita num ponto = massa colada; baixo = transição
          distribuída = tecido contínuo)

Uso:
  python tools/headface/continuity.py            # tabela + figuras
  python tools/headface/continuity.py dump       # + polilinhas em out/face/cont1/sections.npz
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "headstudy"))
import common as C  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = os.path.join(ROOT, "out", "face", "cont1")
REFS = ["bodytopo", "femalebase", "femalechar"]
OURS = ["oursN1", "oursF1", "oursF2"]
ALL = OURS + REFS

DS = 0.5          # amostragem (mm)
SMOOTH = 2.0      # suavização de κ (mm)


# ---------------------------------------------------------------- secções planares
def in_plane_basis(n):
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    a = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    return e1, e2


def plane_section(V, T, p0, n):
    """Polilinha mais longa da interseção malha∩plano (V em mm@H226).

    O plano é desviado 0.37 mm ao longo da normal: as refs têm vértices
    EXATAMENTE no plano de simetria (costura do espelhamento) e isso parte as
    cadeias (pontos de grau 4).  O desvio é comum a todas as fontes.
    """
    p0 = np.asarray(p0, float)
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    p0 = p0 + n * 0.37
    d = (V - p0) @ n
    sd = d[T]
    sel = np.where(((sd < 0).any(1) & (sd > 0).any(1)))[0]
    segs = []
    for t in sel:
        tri = T[t]
        pts = []
        for i in range(3):
            i1, i2 = tri[i], tri[(i + 1) % 3]
            d1, d2 = d[i1], d[i2]
            if (d1 < 0) != (d2 < 0):
                f = d1 / (d1 - d2)
                pts.append(V[i1] * (1 - f) + V[i2] * f)
        if len(pts) == 2:
            segs.append((pts[0], pts[1]))
    if not segs:
        return None
    key = lambda p: (round(p[0], 5), round(p[1], 5), round(p[2], 5))
    adj = {}
    for i, (a, b) in enumerate(segs):
        adj.setdefault(key(a), []).append((i, 0))
        adj.setdefault(key(b), []).append((i, 1))
    seen = set()
    chains = []
    for i0 in range(len(segs)):
        if i0 in seen:
            continue
        chain = [segs[i0][0], segs[i0][1]]
        seen.add(i0)
        for end in (1, 0):
            while True:
                cur = chain[-1] if end else chain[0]
                prev = chain[-2] if end else chain[1]
                k = key(cur)
                nxt = [(i, e) for i, e in adj.get(k, []) if i not in seen]
                if not nxt:
                    break
                # nas junções (grau > 2) continua o mais ALINHADO (menor viragem)
                dref = cur - prev

                def turn(ie):
                    i, e = ie
                    a, b = segs[i]
                    q = (b if e == 0 else a)
                    dq = q - cur
                    cos = np.dot(dref, dq) / (np.linalg.norm(dref) * np.linalg.norm(dq) + 1e-12)
                    return -cos

                i, e = min(nxt, key=turn)
                seen.add(i)
                a, b = segs[i]
                q = b if e == 0 else a
                (chain.append(q) if end else chain.insert(0, q))
        chains.append(np.array(chain))
    return max(chains, key=len)


def resample(P, ds=DS):
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    L = s[-1]
    if L < 4 * ds:
        return None, None
    ss = np.arange(0.0, L, ds)
    Q = np.stack([np.interp(ss, s, P[:, k]) for k in range(3)], axis=1)
    return Q, ss


def kappa(Q, ss, basis, smooth_mm=SMOOTH):
    e1, e2 = basis
    x, y = Q @ e1, Q @ e2
    th = np.unwrap(np.arctan2(np.gradient(y, ss), np.gradient(x, ss)))
    k = np.gradient(th, ss)
    w = max(1, int(round(smooth_mm / (ss[1] - ss[0]))))
    return np.convolve(k, np.ones(w) / w, mode="same")


SECTIONS = {
    # nome: (p0, normal, janela(anatómica) sobre amostras, rótulo)
    "ear_h": ((0, 0, 92.5), (0, 0, 1), lambda Q: Q[:, 0] > 55.0, "orelha — secção horizontal z=92.5"),
    "ear_v": ((0, -25, 0), (0, 1, 0), lambda Q: Q[:, 0] > 55.0, "orelha — secção vertical y=−25"),
    "orbit_h": ((0, 0, 105.0), (0, 0, 1), lambda Q: (Q[:, 0] > 25) & (Q[:, 0] < 70) & (Q[:, 1] > 20),
                "órbita — horizontal z=105, canto lateral"),
}

# perfis de SILHUETA visível (o que o olho vê; sem geometria escondida)
SILHOUETTES = {
    "nape_p": ("b", -45.0, 150.0, "nuca — silhueta visível (occipital→nuca→pescoço)"),
    "chin_p": ("f", -45.0, 70.0, "mento/garganta — silhueta visível"),
}


# ---------------------------------------------------------------- silhuetas
def silhouette_section(V, T, which, zlo, zhi):
    """Perfil visível y(z) (frente yf ou costas yb) → (Q, ss, κ).  Q = (0, y, z)."""
    zs, yf, yb, _pts = C.front_profile(V, T, zlo, zhi, 1.0)
    y = yf if which == "f" else yb
    ok = np.isfinite(y)
    if ok.sum() < 20:
        return None, None, None
    y = np.interp(zs, zs[ok], y[ok])
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.gradient(y, zs), 1.0))])[:-1]
    ss = np.arange(0.0, s[-1], DS)
    yy = np.interp(ss, s, y)
    zz = np.interp(ss, s, zs)
    th = np.unwrap(np.arctan2(np.gradient(yy, ss), np.gradient(zz, ss)))
    k = np.gradient(th, ss)
    w = max(1, int(round(SMOOTH / DS)))
    k = np.convolve(k, np.ones(w) / w, mode="same")
    Q = np.stack([np.zeros_like(zz), yy, zz], axis=1)
    return Q, ss, k


# ---------------------------------------------------------------- métricas
def window_metrics(ss, k, mask):
    kk = np.abs(k)
    kk = np.where(mask, kk, 0.0)
    if not kk.any() or kk.max() == 0:
        return None
    i = int(np.argmax(kk))
    turn = np.degrees(np.trapz(kk, ss))
    near = np.abs(ss - ss[i]) <= 3.0
    turn_near = np.degrees(np.trapz(np.where(near, kk, 0.0), ss))
    return {"kmax": float(kk.max()), "kp99": float(np.percentile(kk[mask], 99)),
            "turn": float(turn), "conc": float(turn_near / max(turn, 1e-9)),
            "s_at": float(ss[i])}


def _tri(fs, fi):
    out = []
    pos = 0
    for n in fs:
        out.append(fi[pos:pos + n])
        pos += n
    return [t for t in out if len(t) == 3]


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    dump = "dump" in sys.argv
    sections, table, curves = {}, [], {}
    for name in ALL:
        Vn, T, fs, fi, info = C.normalise(name)
        V = np.asarray(Vn, float)
        T = np.asarray(T if T is not None and len(T) else _tri(fs, fi), int)
        items = [(k, v[3], "plane", v) for k, v in SECTIONS.items()]
        items += [(k, v[3], "sil", v) for k, v in SILHOUETTES.items()]
        for sname, _lab, kind, cfg in items:
            if kind == "plane":
                p0, nrm, win, _ = cfg
                P = plane_section(V, T, p0, nrm)
                Q, ss = (resample(P) if P is not None else (None, None))
                if Q is None:
                    table.append((name, sname, None))
                    continue
                basis = in_plane_basis(nrm)
                k = kappa(Q, ss, basis)
                mask = win(Q)
            else:
                which, zlo, zhi, _ = cfg
                Q, ss, k = silhouette_section(V, T, which, zlo, zhi)
                if Q is None:
                    table.append((name, sname, None))
                    continue
                basis = (np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]))
                mask = np.ones(len(Q), bool)
            m = window_metrics(ss, k, mask)
            sections.setdefault(sname, []).append((name, Q, ss, k, mask, basis))
            curves[f"{sname}:{name}"] = Q
            table.append((name, sname, m))
    # ---- tabela
    lines = [f"{'secção':8s} {'fonte':11s} {'κ_max':>8s} {'κ_p99':>8s} {'turn°':>8s} {'conc':>6s}"]
    for name, sname, m in table:
        if m is None:
            lines.append(f"{sname:8s} {name:11s} {'—':>8s}")
        else:
            lines.append(f"{sname:8s} {name:11s} {m['kmax']:8.4f} {m['kp99']:8.4f} {m['turn']:8.1f} {m['conc']:6.2f}")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(OUT, "continuity.txt"), "w").write(txt + "\n")
    # ---- figuras
    labels = {k: v[3] for k, v in SECTIONS.items()}
    labels.update({k: v[3] for k, v in SILHOUETTES.items()})
    for sname, entries in sections.items():
        fig, ax = plt.subplots(1, 2, figsize=(13, 5.4))
        col = {"oursN1": "#1f77b4", "oursF1": "#d62728", "bodytopo": "#2ca02c",
               "femalebase": "#ff7f0e", "femalechar": "#9467bd"}
        for name, Q, ss, k, mask, basis in entries:
            lw = 2.2 if name in OURS else 1.0
            x, y = Q @ basis[0], Q @ basis[1]
            ax[0].plot(x, y, color=col.get(name, "k"), lw=lw, label=name)
            ax[1].plot(ss[mask], np.abs(k[mask]), color=col.get(name, "k"), lw=lw)
        ax[0].set_title(labels[sname] + " — (mm@H226)")
        ax[1].set_title("|κ| (1/mm) ao longo do arco")
        for a in ax:
            a.grid(alpha=0.3)
        ax[0].set_aspect("equal")
        ax[0].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"cont1_{sname}.png"), dpi=100)
        plt.close(fig)
    if dump:
        np.savez_compressed(os.path.join(OUT, "sections.npz"), **curves)
        print("polilinhas →", os.path.join(OUT, "sections.npz"))
    print("figuras →", OUT)


if __name__ == "__main__":
    main()
