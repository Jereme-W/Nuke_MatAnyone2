# MatAnyone2 for Nuke

Nuke plugin scaffold for running [MatAnyone2](https://github.com/pq-yang/MatAnyone2) as a cached soft-matte node.

The target workflow is:

1. Connect the plate/video to input 0.
2. Connect a first-frame mask to input 1, using that input's alpha.
3. Press **Run MatAnyone2**.
4. The node writes a half-float EXR alpha cache and outputs the original RGB with the refined matte in alpha.

## Target

- Windows
- Nuke 15.x or newer with Python 3.10+
- NVIDIA CUDA GPU, intended target: 24 GB VRAM
- MatAnyone2 checkpoint from the upstream project

Nuke 14.1 uses Python 3.9.1, while MatAnyone2 requires Python 3.10+, so this package is intentionally aimed at Nuke 15.x for direct in-process use.

## Repository Layout

- `init.py` and `menu.py`: Nuke plugin entrypoints.
- `matanyone2_nuke/`: Python package used by the Nuke node.
- `scripts/install_user.ps1`: no-admin dependency installer into the user's `.nuke` folder.
- `requirements-nuke15.txt`: Python dependencies installed by the helper script.

## No-Admin Install

Copy or clone this repository into:

```text
C:\Users\<user>\.nuke\matanyone2_nuke
```

Then run PowerShell from the repository folder:

```powershell
.\scripts\install_user.ps1 -PythonExe "C:\Path\To\Nuke15.x\python.exe"
```

If your Nuke installation does not expose a standalone `python.exe`, use a normal Python 3.10 interpreter that matches Nuke's architecture:

```powershell
.\scripts\install_user.ps1 -PythonExe "py -3.10"
```

Dependencies are installed under:

```text
C:\Users\<user>\.nuke\matanyone2_nuke\vendor\py310
```

The installer deliberately installs MatAnyone2 itself with `--no-deps` after a curated inference dependency set. That avoids pulling upstream demo/UI packages such as PySide6 into Nuke's plugin path.

The installer also registers this repository in the user's `.nuke\init.py` with `nuke.pluginAddPath(...)`, so Nuke can find `init.py` and `menu.py` inside the plugin folder.

No administrator rights should be required unless the workstation still needs Nuke, NVIDIA drivers, or Microsoft runtime libraries installed.

## Checkpoint

Use the official MatAnyone2 checkpoint from the upstream release:

```text
matanyone2.pth
```

Point the node's **Checkpoint** knob at that file. If the checkpoint path is empty, the runner tries `MatAnyone2.from_pretrained("PeiqingYang/MatAnyone2")`, which may require network access and Hugging Face cache access from inside Nuke.

## Current Notes

- The node is button-driven and cached. It is not designed for random-access live viewer evaluation because MatAnyone2 is temporal and updates memory sequentially.
- The EXR writer prefers the Python `OpenEXR` package. A limited OpenCV EXR fallback is included, but `OpenEXR` is the recommended dependency.
- MatAnyone2 is licensed by upstream under the NTU S-Lab License 1.0. This wrapper repository is separate; redistribution of upstream weights/code should follow upstream terms.

## First Test

1. Restart Nuke after installation.
2. Create **Nodes > Keyer > MatAnyone2 Soft Matte**.
3. Connect a short plate to input 0.
4. Connect a Roto/Read mask to input 1 with useful alpha at the mask frame.
5. Set the checkpoint path.
6. Keep the test range short, for example 3-5 frames.
7. Press **Run MatAnyone2** and verify that the node reads back `matte.%05d.exr` from the cache directory.
