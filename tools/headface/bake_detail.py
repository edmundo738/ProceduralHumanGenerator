"""Coze a camada corretiva estatística da face e os parâmetros para o gerador.

K(az, el) = [ (alvo facial médio − casca) − passa-baixo 20 mm ] − campos anatómicos
  * alvo = média alinhada por marcos de femalebase/bodytopo/femalechar (face_target.py)
  * simetrizada (média de az e −az); aberturas (olhos/boca) preenchidas por convolução
    normalizada; atenuada a 0 fora do domínio medido (pescoço, topo, nuca) em ~6 mm.
Saída: human_generator/data/face_detail_v1.bin (int16, 0.01 mm, linhas = el) + .json
       human_generator/data/face_fields_v1.json (campos + olho)
"""
import os, sys, json
import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from human_generator.generators import face_fields as FF
from face_target import OUT
import fit_face

DATA = os.path.join(ROOT, "human_generator", "data")
AZ_LIM, EL_LO, EL_HI = 115.0, -70.0, 65.0


def main():
    U, Ddet, ok, w, d = fit_face.load()            # Ddet = detalhe (sem baixa frequência)
    AZ, EL = d["AZ"], d["EL"]
    prims = [tuple(p) for p in json.load(open(os.path.join(OUT, "face_params.json")))]
    F = FF.field(np, prims, U[..., 0], U[..., 1], U[..., 2])
    zsurf = d["mean"] * U[..., 2] + 0.52 * 226.1
    valid = np.isfinite(Ddet) & (np.abs(Ddet) < 40) & (zsurf > 2.0)
    K = np.where(valid, Ddet - F, np.nan)
    # despeckle (OBSERVED: salpicos do mapa radial em ângulos rasantes — orelha, mandíbula):
    # só pontos que se afastam > 1.2 mm da mediana 5×5 são substituídos por ela
    from scipy.ndimage import generic_filter
    med = generic_filter(np.nan_to_num(K, nan=0.0), np.median, size=5)
    spk = np.isfinite(K) & (np.abs(K - med) > 1.2)
    K = np.where(spk, med, K)
    print("salpicos substituídos", int(spk.sum()))
    v0 = np.isfinite(K)
    Kg = gaussian_filter(np.where(v0, K, 0.0), 0.6) / np.maximum(gaussian_filter(v0.astype(float), 0.6), 1e-6)
    K = np.where(v0, Kg, np.nan)
    # simetria
    Km = K[:, ::-1]
    K = np.where(np.isfinite(K) & np.isfinite(Km), 0.5 * (K + Km), np.where(np.isfinite(K), K, Km))
    v = np.isfinite(K)
    # preencher aberturas pequenas (olhos, boca): convolução normalizada σ = 2 mm
    sb = 2.0 / (100 * np.radians(0.5))
    num = gaussian_filter(np.where(v, K, 0.0), sb); den = gaussian_filter(v.astype(float), sb)
    Kf = np.where(v, K, num / np.maximum(den, 1e-6))
    hole_small = ~v & (den > 0.15)
    domain = v | hole_small
    # atenuação a 0 fora do domínio (~6 mm)
    dist = distance_transform_edt(domain) * (100 * np.radians(0.5))
    taper = np.clip(dist / 6.0, 0, 1); taper = taper * taper * (3 - 2 * taper)
    Kf = np.where(domain, Kf, 0.0) * taper
    # zona do olho: as pálpebras vêm do modelo do olho, não do preenchimento de buracos
    E = json.load(open(os.path.join(OUT, "eye_params.json")))
    Ua = np.stack([np.abs(U[..., 0]), U[..., 1], U[..., 2]], -1)
    Kf = Kf * (1.0 - FF.eye_zone_weight(np, Ua[..., 0], Ua[..., 1], Ua[..., 2], E))
    # recorte para a janela guardada
    ia = (AZ >= -AZ_LIM - 1e-9) & (AZ <= AZ_LIM + 1e-9); ie = (EL >= EL_LO - 1e-9) & (EL <= EL_HI + 1e-9)
    Ks = Kf[np.ix_(ie, ia)]
    q = np.clip(np.round(Ks * 100), -32767, 32767).astype("<i2")
    os.makedirs(DATA, exist_ok=True)
    q.tofile(os.path.join(DATA, "face_detail_v1.bin"))
    meta = {"az0": float(AZ[ia][0]), "el0": float(EL[ie][0]), "step": 0.5, "n_az": int(ia.sum()), "n_el": int(ie.sum()),
            "unit_mm": 0.01, "frame": "mm@H226, centro head_mass.CENTRE; az = atan2(ux, uy), el = asin(uz) (graus)",
            "source": "média alinhada por marcos (TPS) de femalebase, bodytopo, femalechar − casca radial_cont_a2 − passa-baixo 20 mm − campos face_fields_v1",
            "note": "camada corretiva estatística (prioridade 2 do utilizador); simetrizada; atenuada fora do domínio medido"}
    json.dump(meta, open(os.path.join(DATA, "face_detail_v1.json"), "w"), indent=1, ensure_ascii=False)
    E = json.load(open(os.path.join(OUT, "eye_params.json")))
    json.dump({"fields": [[p[0], p[1], p[2], p[3], p[4]] for p in prims], "eye": E},
              open(os.path.join(DATA, "face_fields_v1.json"), "w"), indent=0, ensure_ascii=False)
    tot = np.where(valid, Ddet, np.nan)
    print("detalhe RMS", np.sqrt(np.nanmean(tot ** 2)), "| campos explicam", 1 - np.nanmean((tot - F) ** 2) / np.nanmean(tot ** 2),
          "| corretiva RMS", np.sqrt(np.nanmean(np.where(valid, K, np.nan) ** 2)), "| ficheiro", q.nbytes, "bytes")


if __name__ == "__main__":
    main()
