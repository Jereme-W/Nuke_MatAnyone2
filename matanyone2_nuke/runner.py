"""MatAnyone2 sequence runner independent of Nuke node UI code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .exr import write_alpha_half_exr


ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class RunSettings:
    frames_dir: str
    frame_numbers: list[int]
    frame_pattern: str
    mask_path: str
    output_dir: str
    output_pattern: str
    checkpoint_path: str = ""
    device: str = "cuda:0"
    warmup: int = 10
    erode: int = 10
    dilate: int = 10
    max_size: int = -1


def run_sequence(settings: RunSettings, progress: ProgressCallback | None = None) -> list[str]:
    """Run MatAnyone2 over exported frames and write alpha EXR frames."""

    _progress(progress, "Importing MatAnyone2 dependencies")

    import torch
    import torch.nn.functional as F

    from matanyone2 import InferenceCore, MatAnyone2
    from matanyone2.utils.get_default_model import get_matanyone2_model
    from matanyone2.utils.inference_utils import gen_dilate, gen_erosion

    if not settings.frame_numbers:
        raise ValueError("No frames were supplied for MatAnyone2 processing.")

    device = torch.device(settings.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available to PyTorch inside Nuke.")

    _progress(progress, "Loading MatAnyone2 model")
    if settings.checkpoint_path and os.path.exists(settings.checkpoint_path):
        model = get_matanyone2_model(settings.checkpoint_path, device)
    else:
        model = MatAnyone2.from_pretrained("PeiqingYang/MatAnyone2")
        model.to(device).eval()

    processor = InferenceCore(model, cfg=model.cfg, device=device)

    mask_np = _read_mask(settings.mask_path)
    if settings.dilate > 0:
        mask_np = gen_dilate(mask_np, int(settings.dilate), int(settings.dilate))
    if settings.erode > 0:
        mask_np = gen_erosion(mask_np, int(settings.erode), int(settings.erode))

    first_frame = _read_rgb_frame(_frame_path(settings, settings.frame_numbers[0]))
    orig_h, orig_w = first_frame.shape[:2]
    proc_size = _processing_size(orig_h, orig_w, settings.max_size)

    mask = torch.from_numpy(mask_np).float().to(device)
    if mask.shape != proc_size:
        mask = F.interpolate(
            mask.unsqueeze(0).unsqueeze(0),
            size=proc_size,
            mode="nearest",
        )[0, 0]

    outputs: list[str] = []
    objects = [1]
    warmup = max(0, int(settings.warmup))
    total_steps = warmup + len(settings.frame_numbers)

    with torch.inference_mode():
        autocast_type = "cuda" if device.type == "cuda" else "cpu"
        with torch.amp.autocast(device_type=autocast_type, enabled=True):
            for ti in range(total_steps):
                if ti <= warmup:
                    frame_number = settings.frame_numbers[0]
                else:
                    frame_number = settings.frame_numbers[ti - warmup]

                image_np = _read_rgb_frame(_frame_path(settings, frame_number))
                image = _image_to_tensor(image_np, device=device, size=proc_size)

                if ti == 0:
                    output_prob = processor.step(image, mask, objects=objects)
                    output_prob = processor.step(image, first_frame_pred=True)
                elif ti <= warmup:
                    output_prob = processor.step(image, first_frame_pred=True)
                else:
                    output_prob = processor.step(image)

                if ti <= warmup - 1:
                    continue

                out_frame_number = settings.frame_numbers[ti - warmup]
                matte = processor.output_prob_to_mask(output_prob)
                matte_np = matte.detach().float().cpu().numpy()
                if matte_np.ndim == 3:
                    matte_np = matte_np[0]

                if matte_np.shape != (orig_h, orig_w):
                    matte = F.interpolate(
                        matte[None, None].float(),
                        size=(orig_h, orig_w),
                        mode="bilinear",
                        align_corners=False,
                    )[0, 0]
                    matte_np = matte.detach().cpu().numpy()

                output_path = settings.output_pattern % out_frame_number
                if not os.path.isabs(output_path):
                    output_path = os.path.join(settings.output_dir, output_path)
                write_alpha_half_exr(output_path, matte_np)
                outputs.append(output_path)

                done = len(outputs)
                _progress(progress, f"Processed {done}/{len(settings.frame_numbers)} frames")

    if device.type == "cuda":
        torch.cuda.empty_cache()

    return outputs


def _read_rgb_frame(path: str) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def _read_mask(path: str) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as image:
        if image.mode in ("RGBA", "LA"):
            alpha = image.getchannel("A")
            return np.asarray(alpha)
        return np.asarray(image.convert("L"))


def _image_to_tensor(image: np.ndarray, *, device, size: tuple[int, int]):
    import torch
    import torch.nn.functional as F

    tensor = torch.from_numpy(image).permute(2, 0, 1).float()
    if image.shape[:2] != size:
        tensor = F.interpolate(
            tensor.unsqueeze(0),
            size=size,
            mode="area",
        )[0]
    return (tensor / 255.0).to(device)


def _processing_size(height: int, width: int, max_size: int) -> tuple[int, int]:
    max_size = int(max_size)
    if max_size <= 0:
        return (height, width)
    min_side = min(height, width)
    if min_side <= max_size:
        return (height, width)
    return (int(height / min_side * max_size), int(width / min_side * max_size))


def _frame_path(settings: RunSettings, frame_number: int) -> str:
    path = settings.frame_pattern % frame_number
    if os.path.isabs(path):
        return path
    return os.path.join(settings.frames_dir, path)


def _progress(progress: ProgressCallback | None, message: str) -> None:
    if progress:
        progress(message)
