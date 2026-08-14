# tools/utils/watermark.py
"""水印去除工具"""

import os
import sys
import cv2
import numpy as np
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

#from tools.config import REMOVE_WATERMARK
# 是否启用去水印
REMOVE_WATERMARK = True

def remove_watermark(image_path: str) -> Image.Image:
    """
    检测并去除图片水印
    返回: PIL Image 对象
    """
    if not REMOVE_WATERMARK:
        print("[系统] 去水印功能已关闭，直接使用原图")
        return Image.open(image_path).convert('RGB')
    
    print("\n[AI预处理] 检测并去除图片水印...")
    
    try:
        # 使用 imdecode 读取（支持中文路径）
        with open(image_path, 'rb') as f:
            img_bytes = np.frombuffer(f.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            # 降级使用 PIL
            pil_img = Image.open(image_path).convert('RGB')
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            if img is None:
                raise ValueError("无法读取图片")
    except Exception as e:
        print(f"⚠️ 读取图片失败，跳过水印检测: {e}")
        return Image.open(image_path).convert('RGB')
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测白色/亮色区域
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印，继续生成。")
        return Image.open(image_path).convert('RGB')
    
    print("⚠️ 检测到水印，正在使用 OpenCV 修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印去除完成！")
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))