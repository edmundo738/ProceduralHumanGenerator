#!/usr/bin/env python3
"""Make ``import bpy`` work on headless Linux boxes without X11/GL libraries.

The official ``bpy`` wheels from PyPI are linked against a handful of system
libraries (``libXrender``, ``libXi``, ``libGL`` ...) that minimal CI/sandbox
images do not ship and that cannot always be apt-installed.  This tool parses
the real load closure of the installed ``bpy`` extension module and emits tiny
stub ``.so`` files (no-op functions, correctly versioned where ``ld.so``
demands it) so the import succeeds.  Nothing here is ever *called*: background
mode never creates a GL context and Cycles CPU never touches X11.

Usage::

    python3 tools/headless_blender.py build            # write stubs
    python3 tools/headless_blender.py run script.py    # run with the env set
    python3 tools/headless_blender.py test             # smoke: import + render

Stubs land in ``tools/.hcg_env/stubs`` (git-ignored).  On a normal machine the
tool is a no-op because every ``DT_NEEDED`` resolves against the system.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.join(HERE, ".hcg_env")
STUB_DIR = os.path.join(ENV_DIR, "stubs")

SYS_DIRS = [
    "/usr/lib/x86_64-linux-gnu",
    "/usr/lib64",
    "/lib/x86_64-linux-gnu",
    "/usr/lib",
]

# family → name prefixes; unversioned symbols matching a prefix are stubbed in
# that library so consumers that don't declare DT_NEEDED still resolve them in
# their local scope (e.g. libusd → glXGetProcAddress via libGL).
PREFIXES = {
    "libXrender": ("XRender", "XRenderQuery", "XRenderFind"),
    "libXi": ("Xi", "XInput", "XCloseDevice", "XOpenDevice", "XQueryDevice",
              "XDevice", "XListDevice", "XSelect", "XSetEventMask", "XGetEventData",
              "XFreeEventData", "XQueryExtension"),
    "libXext": ("XShape", "dbe", "DPMS", "XShm", "Xext"),
    "libXfixes": ("XFixes",),
    "libXt": ("Xt",),
    "libXrandr": ("XRR",),
    "libXcursor": ("Xcursor",),
    "libXinerama": ("Xinerama",),
    "libXxf86vm": ("XF86VidMode",),
    "libICE": ("Ice",),
    "libSM": ("Sm",),
    "libxkbcommon": ("xkb",),
    "libGL": ("gl", "GL", "wgl"),
    "libGLX": ("glX", "GLX"),
    "libOpenGL": ("gl", "glvnd"),
    "libEGL": ("egl", "EGL"),
    "libcuda": ("cu", "nvcu"),
    "libnvoptix": ("optix",),
    "libamdhip64": ("hip",),
    "libze_loader": ("ze",),
    "libur_loader": ("ur_",),
    "libwayland": ("wl_", "wayland"),
}


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def find_bpy_dir() -> str:
    """Locate the installed bpy package directory."""
    code = (
        "import glob,os,sys\n"
        "for p in sys.path:\n"
        "    d=os.path.join(p,'bpy')\n"
        "    if os.path.isdir(d) and (glob.glob(os.path.join(d,'__init__.so')) or glob.glob(os.path.join(d,'*bpy*.so'))):\n"
        "        print(d); break\n"
    )
    out = run([sys.executable, "-c", code]).strip()
    if not out:
        sys.exit("bpy not found for this interpreter")
    return out


def sonames_needed(path: str) -> list[str]:
    out = run(["readelf", "-d", path])
    return re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", out)


def has_bindnow(path: str) -> bool:
    out = run(["readelf", "-d", path])
    return "BIND_NOW" in out or "NOW" in re.findall(r"\(FLAGS\)\s+(\S.*)", out or [""])[0:1] and "NOW" in out


def dyn_syms(path: str):
    """Parse readelf --dyn-syms -W → dict sym→(type, verneed_idx|None, vername|None)."""
    out = run(["readelf", "--dyn-syms", "-W", path])
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if not line.endswith("UND") and "UND" not in line:
            continue
        m = re.match(r"^\d+:\s+\S+\s+\d+\s+(\S+)\s+\S+\s+\S+\s+UND\s+(.*)$", line)
        if not m:
            continue
        sym_type, rest = m.groups()
        ver = None
        name = rest.strip()
        # forms: "sym@VER (3)"  or "sym (3)"
        mm = re.match(r"^(\S+)@(\S+)\s+\((\d+)\)$", name)
        if mm:
            name, ver, _idx = mm.groups()
            res[name] = (sym_type, None, ver)
            continue
        mm = re.match(r"^(\S+)\s+\((\d+)\)$", name)
        if mm:
            name, idx = mm.groups()
            res[name] = (sym_type, int(idx), None)
        else:
            res[name] = (sym_type, None, None)
    return res


def verneed_map(path: str) -> dict[int, tuple[str, str]]:
    """readelf -V → {version_idx: (filename, version_name)}."""
    out = run(["readelf", "-V", path])
    idx_map: dict[int, tuple[str, str]] = {}
    cur_file = None
    for line in out.splitlines():
        m = re.search(r"File:\s+(\S+)", line)
        if m:
            cur_file = m.group(1)
            continue
        m = re.search(r"Name:\s+(\S+)\s+Flags:.*Version:\s+(\d+)", line)
        if m and cur_file:
            idx_map[int(m.group(2))] = (cur_file, m.group(1))
    return idx_map


def defined_syms(path: str) -> set[str]:
    out = run(["nm", "-D", "--defined-only", path])
    res = set()
    for line in out.splitlines():
        t = line.split()
        if len(t) >= 3 and re.match(r"^[0-9a-f]+$", t[0]):
            res.add(t[-1])
        elif len(t) == 2:
            res.add(t[-1])
    return res


def collect(paths: list[str]) -> set[str]:
    syms: set[str] = set()
    for p in paths:
        try:
            syms |= defined_syms(p)
        except Exception:
            pass
    return syms


def cmd_build() -> None:
    bpy_dir = find_bpy_dir()
    lib_dir = os.path.join(bpy_dir, "lib")
    search = [bpy_dir, lib_dir] + SYS_DIRS
    present: dict[str, str] = {}
    for d in search:
        for f in glob.glob(os.path.join(d, "*.so*")):
            present.setdefault(os.path.basename(f), f)

    entry = glob.glob(os.path.join(bpy_dir, "__init__.so")) or glob.glob(os.path.join(bpy_dir, "*bpy*.so"))
    if not entry:
        sys.exit("no bpy .so found")
    entry = entry[0]

    # transitive load closure of the bpy module
    closure: list[str] = []
    seen: set[str] = set()
    queue = [entry]
    while queue:
        obj = queue.pop()
        if obj in seen:
            continue
        seen.add(obj)
        closure.append(obj)
        for need in sonames_needed(obj):
            if need in present:
                queue.append(present[need])

    # system-provided and bundle-provided symbol sets
    system_syms = collect(glob.glob("/usr/lib/x86_64-linux-gnu/*.so*") + glob.glob("/lib/x86_64-linux-gnu/*.so*"))
    bundle_syms = collect(glob.glob(os.path.join(lib_dir, "*.so*")) + glob.glob(os.path.join(bpy_dir, "*.so")))

    # missing DT_NEEDED (not present in any search dir)
    missing: set[str] = set()
    for obj in closure:
        for need in sonames_needed(obj):
            if need not in present:
                missing.add(need)

    # undefined symbols inside the closure
    unversioned: dict[str, str] = {}     # sym → type
    versioned: dict[str, dict[str, tuple[str, str]]] = {}  # lib → sym → (type, ver)
    for obj in closure:
        vmap = verneed_map(obj)
        for name, (sym_type, idx, ver) in dyn_syms(obj).items():
            if ver is not None:
                # readelf printed the version inline; find owning file
                owner = next((f for f, vn in vmap.values() if vn == ver), None)
                if owner:
                    versioned.setdefault(owner, {}).setdefault(name, (sym_type, ver))
                continue
            if idx is not None and idx in vmap:
                f, ver_name = vmap[idx]
                versioned.setdefault(f, {}).setdefault(name, (sym_type, ver_name))
                continue
            unversioned.setdefault(name, sym_type)

    safe_unver = {s for s in unversioned if s not in system_syms}
    mega = {s for s in safe_unver if s not in bundle_syms}

    os.makedirs(STUB_DIR, exist_ok=True)
    stubs = glob.glob(os.path.join(STUB_DIR, "*.so*"))
    for f in stubs:
        os.remove(f)

    def asm_path(names: set[str], tag: str) -> str:
        lines = ["\t.text"]
        data = []
        for s in sorted(names):
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", s):
                continue
            if unversioned.get(s) == "OBJECT" or unversioned.get(s) == "TLS":
                data.append(s)
                continue
            lines.append(f"\t.globl {s}\n{s}:\n\txor %eax, %eax\n\tret")
        for s in data:
            lines.append(f"\t.section .bss\n\t.align 8\n\t.globl {s}\n{s}:\n\t.zero 64")
        p = os.path.join(STUB_DIR, f"{tag}.s")
        with open(p, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        return p

    # the big preloadable stub (safe extras only)
    src = asm_path(mega, "megastub")
    extra = [present[n] for n in ("libX11.so.6", "libXext.so.6", "libxcb.so.1") if n in present]
    subprocess.check_call(
        ["gcc", "-shared", "-nostdlib", "-fPIC", "-o", os.path.join(STUB_DIR, "libblenderstub.so"), src,
         "-Wl,--no-as-needed"] + extra)

    def lib_family(name: str) -> str | None:
        for fam in PREFIXES:
            if name.startswith(fam):
                return fam
        return None

    count = 0
    for lib in sorted(missing):
        fam = lib_family(lib)
        vmap = versioned.get(lib, {})
        names: set[str] = set(vmap.keys())
        if fam:
            names |= {s for s in safe_unver if s.startswith(PREFIXES[fam])}
        elif fam is None and not vmap:
            names |= {s for s in safe_unver if s.startswith(("X", "gl")) and lib.startswith("libX")}
        if not names and lib not in ("libcuda.so.1",):
            # nothing to define: still create the file so DT_NEEDED resolves
            names = set()
        src = asm_path(names, "stub_" + re.sub(r"\W", "_", lib))
        cmd = ["gcc", "-shared", "-nostdlib", "-fPIC", "-Wl,-soname," + lib,
               "-o", os.path.join(STUB_DIR, lib), src]
        if vmap:
            by_ver: dict[str, list[str]] = {}
            for s, (_t, ver) in vmap.items():
                by_ver.setdefault(ver, []).append(s)
            mapfile = os.path.join(STUB_DIR, "stub_" + re.sub(r"\W", "_", lib) + ".map")
            with open(mapfile, "w") as fh:
                for ver, syms in sorted(by_ver.items()):
                    fh.write(f"{ver} {{ global: {'; '.join(sorted(syms))}; }};\n")
            cmd += ["-Wl,--version-script," + mapfile]
        if fam and fam.startswith(("libX", "libICE", "libSM")):
            cmd += ["-Wl,--no-as-needed"] + [present[n] for n in
                                             ("libX11.so.6", "libXext.so.6", "libxcb.so.1") if n in present]
        elif fam == "libGL":
            cmd += ["-Wl,--no-as-needed", os.path.join(STUB_DIR, "libblenderstub.so")]
        subprocess.check_call(cmd)
        count += 1

    with open(os.path.join(ENV_DIR, "env.sh"), "w") as fh:
        fh.write(f'export LD_LIBRARY_PATH="{STUB_DIR}${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"\n')
        fh.write(f'export LD_PRELOAD="{os.path.join(STUB_DIR, "libblenderstub.so")}"\n')
    print(f"stubs: {count} libs, megastub {len(mega)} syms → {STUB_DIR}")


def env() -> dict[str, str]:
    e = dict(os.environ)
    e["LD_LIBRARY_PATH"] = STUB_DIR + (":" + e["LD_LIBRARY_PATH"] if e.get("LD_LIBRARY_PATH") else "")
    pre = os.path.join(STUB_DIR, "libblenderstub.so")
    if os.path.exists(pre):
        e["LD_PRELOAD"] = pre + (":" + e["LD_PRELOAD"] if e.get("LD_PRELOAD") else "")
    return e


def cmd_run(script: str, args: list[str]) -> int:
    return subprocess.call([sys.executable, script, *args], env=env())


def cmd_test() -> int:
    code = r"""
import bpy, bmesh, math
print("blender", bpy.app.version_string)
me = bpy.data.meshes.new("t"); bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("t", me); bpy.context.scene.collection.objects.link(ob)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4
sc.render.resolution_x = sc.render.resolution_y = 32
sc.camera = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
bpy.context.scene.collection.objects.link(sc.camera)
sc.camera.location = (3, 3, 2); sc.camera.rotation_euler = (1.1, 0, 0.78)
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
sc.render.filepath = "/tmp/hcg_smoke.png"
bpy.ops.render.render(write_still=True)
print("render ok, gltf:", hasattr(bpy.ops.export_scene, "gltf"))
"""
    return subprocess.call([sys.executable, "-c", code], env=env())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("test")
    rp = sub.add_parser("run")
    rp.add_argument("script")
    rp.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.cmd == "build":
        cmd_build()
    elif a.cmd == "test":
        sys.exit(cmd_test())
    else:
        sys.exit(cmd_run(a.script, a.args))


if __name__ == "__main__":
    main()
