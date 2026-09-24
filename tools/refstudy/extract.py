"""Passo 1 (bpy): exporta cada malha para WORK/raw_<nome>.npz.
Uso: python tools/headless_blender.py run tools/refstudy/extract.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, refload
from _paths import WORK
for n in refload.NAMES:
    V, T = refload.load(n)
    print(f"{n:12s} v={len(V):6d} tris={len(T):6d} ext={np.round(V.max(0)-V.min(0),3)}")
    np.savez(os.path.join(WORK, f"raw_{n}.npz"), V=V, T=T)
