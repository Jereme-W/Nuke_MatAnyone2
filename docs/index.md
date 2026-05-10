# MatAnyone2 for Nuke

Cached Nuke node wrapper for MatAnyone2 video matting.

## What It Does

- Takes an RGB plate/video on input 0.
- Takes a first-frame mask from input 1 alpha.
- Runs MatAnyone2 over the selected frame range.
- Writes a half-float EXR alpha cache.
- Outputs the original RGB with the refined soft matte in alpha.

## Requirements

- Windows
- Nuke 15.x or newer
- Python 3.10 inside Nuke
- NVIDIA CUDA GPU
- MatAnyone2 checkpoint

Nuke 14.1 is not the direct-mode target because its Python version is too old for MatAnyone2.

## No-Admin Install

Clone or copy the repository to:

```text
C:\Users\<user>\.nuke\matanyone2_nuke
```

Install user-local dependencies:

```powershell
.\scripts\install_user.ps1 -PythonExe "C:\Path\To\Nuke15.x\python.exe"
```

The installer also registers the plugin path in your user `.nuke\init.py`. Then restart Nuke and create:

```text
Nodes > Keyer > MatAnyone2 Soft Matte
```

## First Smoke Test

Use a short 3-5 frame range first. Connect a plate to input 0, a Roto or mask Read to input 1, set the checkpoint path, and press **Run MatAnyone2**.
