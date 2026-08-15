# core/postprocessor.py
"""图片后处理 - 消除AI痕迹"""

import os
import sys
import random
import time
import cv2
import numpy as np
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 修改：从 config.app 导入
from config.app import (
    REMOVE_AI_TRACES,
    AI_CLEAR_METADATA,
    AI_REALISTIC,
    AI_CAMERA,
    AI_STRENGTH,
    AI_INJECT_EXIF,
    AI_CHROMATIC_ABERRATION,
    AI_CHROMATIC_STRENGTH,
    AI_REALISTIC_NOISE,
    AI_NOISE_ISO_BASE,
    AI_NOISE_RANDOMIZE,
    AI_MINOR_CROP,
    AI_CROP_PERCENT,
    AI_FINGERPRINT_OBFUSCATION,
    AI_DISTORTION_STRENGTH,
    SKETCH_KEYWORDS,  # ✅ 添加这一行
)


def is_sketch_style(prompt_or_style: str) -> bool:
    """检测是否为素描/线稿风格"""
    lower = prompt_or_style.lower()
    return any(kw in lower for kw in SKETCH_KEYWORDS)


def remove_ai_traces(image_path: str, is_sketch: bool = False) -> str:
    """消除AI痕迹处理，返回处理后的文件路径"""
    try:
        print(f"\n📷 消除AI痕迹处理...")
        final_path = image_path
        
        if AI_CLEAR_METADATA:
            final_path = _clear_metadata(final_path)
        
        if AI_REALISTIC and not is_sketch:
            final_path = _apply_photo_realistic(final_path)
        
        if AI_INJECT_EXIF and not is_sketch:
            final_path = _inject_exif(final_path)
        
        if AI_CHROMATIC_ABERRATION and not is_sketch:
            final_path = _apply_chromatic_aberration(final_path)
        
        if AI_REALISTIC_NOISE and not is_sketch:
            final_path = _apply_realistic_noise(final_path)
        
        if AI_MINOR_CROP:
            final_path = _apply_minor_crop(final_path)
        
        if AI_FINGERPRINT_OBFUSCATION and not is_sketch:
            final_path = _apply_fingerprint_obfuscation(final_path)
        
        return final_path
    except Exception as e:
        print(f"   ⚠️ 消除AI痕迹整体流程失败: {e}")
        return image_path


def _clear_metadata(image_path: str) -> str:
    try:
        from utils.imagemeta_cleaner import smart_clean_image
        jpg_path = image_path.replace('.png', '.jpg')
        final_path = smart_clean_image(
            image_path,
            output_path=jpg_path,
            method='jpg',
            jpg_quality=92
        )
        print(f"   ✅ 元数据已清除 -> JPG")
        if final_path != image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        return final_path
    except Exception as e:
        print(f"   ⚠️ 元数据清除失败: {e}")
        return image_path


def _apply_photo_realistic(image_path: str) -> str:
    try:
        from utils.photo_realistic import make_photo_realistic
        final_path = make_photo_realistic(
            image_path,
            image_path,
            camera=AI_CAMERA,
            style="portrait",
            inject_exif_data=False,
            randomize=True,
            strength=AI_STRENGTH,
            add_noise_flag=AI_REALISTIC_NOISE
        )
        print(f"   ✅ 照片真实化完成 (强度: {AI_STRENGTH})")
        return final_path
    except Exception as e:
        print(f"   ⚠️ 照片真实化失败: {e}")
        return image_path


def _inject_exif(image_path: str) -> str:
    try:
        from utils.exif_injector import inject_exif
        time.sleep(0.5)
        final_path = inject_exif(
            image_path,
            image_path,
            camera=AI_CAMERA,
            style="portrait",
            randomize=True
        )
        print(f"   ✅ EXIF 已注入")
        return final_path
    except Exception as e:
        print(f"   ⚠️ EXIF 注入跳过: {e}")
        return image_path


def _apply_chromatic_aberration(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        arr = np.array(img).astype(np.float32)
        h, w = arr.shape[:2]
        strength = AI_CHROMATIC_STRENGTH
        
        for y in range(h):
            for x in range(w):
                dist_from_edge = min(x, w-1-x, y, h-1-y)
                if dist_from_edge < 40:
                    shift_factor = (40 - dist_from_edge) / 40
                    shift = shift_factor * strength * random.uniform(0.5, 1.0)
                    arr[y, x, 0] += random.uniform(-shift, shift * 0.5)
                    arr[y, x, 2] += random.uniform(-shift * 0.5, shift)
        
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        if arr.ndim == 3 and arr.shape[2] == 3:
            img = Image.fromarray(arr).convert('RGB')
        else:
            img = Image.fromarray(arr[:, :, :3]).convert('RGB')
        img.save(image_path, quality=92)
        print(f"      ✅ 紫边模拟完成 (强度: {strength})")
        return image_path
    except Exception as e:
        print(f"   ⚠️ 紫边模拟失败: {e}")
        return image_path


def _apply_realistic_noise(image_path: str) -> str:
    try:
        if AI_NOISE_RANDOMIZE:
            iso = AI_NOISE_ISO_BASE + random.randint(-200, 200)
            iso = max(100, min(1600, iso))
        else:
            iso = AI_NOISE_ISO_BASE
        
        img = Image.open(image_path)
        img_np = np.array(img).astype(np.uint8)
        if img_np.ndim == 3 and img_np.shape[2] == 4:
            img_np = img_np[:, :, :3]
        
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        noise_std = 0.005 * (iso / 100) ** 0.5
        
        gaussian_noise = np.random.normal(0, noise_std * 255, img_cv.shape)
        shot_noise = np.random.poisson(np.abs(img_cv) * 0.005) * 0.1
        img_cv = img_cv + gaussian_noise + shot_noise
        
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        dark_mask = gray < 80
        if np.any(dark_mask):
            dark_noise = np.random.normal(0, noise_std * 255 * 0.5, img_cv.shape)
            img_cv[dark_mask] = img_cv[dark_mask] + dark_noise[dark_mask]
        
        img_cv = np.clip(img_cv, 0, 255).astype(np.uint8)
        img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        img.save(image_path, quality=92)
        print(f"      ✅ 真实噪点添加完成 (ISO: {iso})")
        return image_path
    except Exception as e:
        print(f"   ⚠️ 真实噪点添加失败: {e}")
        return image_path


def _apply_minor_crop(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        w, h = img.size
        
        crop_pct = AI_CROP_PERCENT * random.uniform(0.5, 1.5)
        crop_w = int(w * crop_pct)
        crop_h = int(h * crop_pct)
        
        crop_w = max(5, min(crop_w, int(w * 0.05)))
        crop_h = max(5, min(crop_h, int(h * 0.05)))
        
        corners = [(0, 0), (0, crop_h), (crop_w, 0), (crop_w, crop_h)]
        if random.random() < 0.5:
            left = random.randint(0, crop_w)
            top = random.randint(0, crop_h)
        else:
            left, top = random.choice(corners)
        
        right = w - random.randint(0, crop_w)
        bottom = h - random.randint(0, crop_h)
        
        if right > left + 50 and bottom > top + 50:
            img = img.crop((left, top, right, bottom))
            try:
                img = img.resize((w, h), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize((w, h), Image.LANCZOS)
            img.save(image_path, quality=92)
            print(f"      ✅ 轻微裁剪完成 (裁切: {crop_pct*100:.1f}%)")
        else:
            print(f"      ⚠️ 裁剪跳过 (区域无效)")
        return image_path
    except Exception as e:
        print(f"   ⚠️ 轻微裁剪失败: {e}")
        return image_path


def _apply_fingerprint_obfuscation(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        arr = np.array(img).astype(np.float32)
        h, w = arr.shape[:2]
        strength = AI_DISTORTION_STRENGTH
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                dx = random.uniform(-strength, strength) * 100
                dy = random.uniform(-strength, strength) * 100
                for dy2 in range(4):
                    for dx2 in range(4):
                        ny = min(h-1, max(0, y + dy2 + int(dy * 0.5)))
                        nx = min(w-1, max(0, x + dx2 + int(dx * 0.5)))
                        pass
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        img.save(image_path, quality=92)
        print(f"      ✅ 指纹混淆完成 (强度: {strength})")
        return image_path
    except Exception as e:
        print(f"   ⚠️ 指纹混淆失败: {e}")
        return image_path