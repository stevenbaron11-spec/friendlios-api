from __future__ import annotations
import numpy as np
from PIL import Image
from typing import List

def resize(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size))

def phash64(img: Image.Image) -> bytes:
    g = np.asarray(resize(img, 32).convert("L"), dtype=np.float32)
    F = np.fft.fft2(g)
    mag = np.abs(F)
    low = mag[:8, :8].copy()
    low[0, 0] = np.median(low)
    m = np.median(low)
    bits = (low > m).astype(np.uint8).flatten()
    out = 0
    for b in bits:
        out = (out << 1) | int(b)
    return out.to_bytes(8, byteorder="big", signed=False)

def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    a = 0.055
    return np.where(c <= 0.04045, c / 12.92, ((c + a) / (1 + a)) ** 2.4)

def _rgb_to_xyz(rgb: np.ndarray) -> np.ndarray:
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
    return np.tensordot(rgb, M.T, axes=1)

def _xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    x = xyz[..., 0] / Xn
    y = xyz[..., 1] / Yn
    z = xyz[..., 2] / Zn
    def f(t):
        eps = (6/29)**3
        kappa = (29/3)**3 / 3
        return np.where(t > eps, np.cbrt(t), (kappa * t + 4/29))
    fx, fy, fz = f(x), f(y), f(z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return np.stack([L, a, b], axis=-1)

def lab_histogram(img: Image.Image, bins: int = 16) -> list[float]:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    lin = _srgb_to_linear(arr)
    xyz = _rgb_to_xyz(lin)
    lab = _xyz_to_lab(xyz)
    L = np.clip(lab[..., 0], 0, 100)
    a = np.clip(lab[..., 1], -128, 127)
    b = np.clip(lab[..., 2], -128, 127)
    hL, _ = np.histogram(L, bins=bins, range=(0, 100), density=True)
    ha, _ = np.histogram(a, bins=bins, range=(-128, 127), density=True)
    hb, _ = np.histogram(b, bins=bins, range=(-128, 127), density=True)
    hist = np.concatenate([hL, ha, hb]).astype(np.float32)
    return hist.tolist()

def lbp_histogram(gray: np.ndarray) -> list[float]:
    H, W = gray.shape
    g = np.pad(gray, 1, mode="edge")
    n0 = g[0:H,     0:W]
    n1 = g[0:H,     1:W+1]
    n2 = g[0:H,     2:W+2]
    n3 = g[1:H+1,   2:W+2]
    n4 = g[2:H+2,   2:W+2]
    n5 = g[2:H+2,   1:W+1]
    n6 = g[2:H+2,   0:W]
    n7 = g[1:H+1,   0:W]
    c  = g[1:H+1,   1:W+1]
    code = ((n0 >= c).astype(np.uint8) << 7) |            ((n1 >= c).astype(np.uint8) << 6) |            ((n2 >= c).astype(np.uint8) << 5) |            ((n3 >= c).astype(np.uint8) << 4) |            ((n4 >= c).astype(np.uint8) << 3) |            ((n5 >= c).astype(np.uint8) << 2) |            ((n6 >= c).astype(np.uint8) << 1) |            ((n7 >= c).astype(np.uint8) << 0)
    hist, _ = np.histogram(code, bins=256, range=(0, 256), density=True)
    return hist.astype(np.float32).tolist()

def gradient_map(gray: np.ndarray) -> np.ndarray:
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:-1] = (gray[:, 2:] - gray[:, :-2]) * 0.5
    gy[1:-1, :] = (gray[2:, :] - gray[:-2, :]) * 0.5
    mag = np.sqrt(gx * gx + gy * gy)
    return mag

def nms_boxes(boxes: List[tuple[int,int,int,int]], scores: List[float], iou_thr: float = 0.3) -> List[int]:
    if not boxes: return []
    import numpy as np
    boxes = np.array(boxes, dtype=np.float32)
    scores = np.array(scores, dtype=np.float32)
    x1, y1 = boxes[:,0], boxes[:,1]
    w,  h  = boxes[:,2], boxes[:,3]
    x2, y2 = x1 + w, y1 + h
    areas = w * h
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_thr)[0]
        order = inds + 1 if hasattr(inds, "__len__") else []
    return keep

def pick_distinctive_patches(img: Image.Image, k: int = 5, win: int = 64, stride: int = 32) -> List[tuple[int,int,int,int,float]]:
    S = 256
    scale = S / min(img.size)
    new_w = int(img.width * scale); new_h = int(img.height * scale)
    im = img.resize((new_w, new_h)).convert("L")
    g = np.asarray(im, dtype=np.float32)
    mag = gradient_map(g)
    boxes, scores = [], []
    for y in range(0, new_h - win + 1, stride):
        for x in range(0, new_w - win + 1, stride):
            patch = mag[y:y+win, x:x+win]
            score = float(patch.mean())
            boxes.append((x, y, win, win))
            scores.append(score)
    if not boxes:
        return []
    import numpy as np
    idxs = np.argsort(scores)[::-1][:max(50, 5*k)]
    boxes_sel = [boxes[i] for i in idxs]
    scores_sel = [scores[i] for i in idxs]
    keep = nms_boxes(boxes_sel, scores_sel, iou_thr=0.4)[:k]
    return [(boxes_sel[i][0], boxes_sel[i][1], boxes_sel[i][2], boxes_sel[i][3], scores_sel[i]) for i in keep]
