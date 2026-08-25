# core/clothes_remover.py
"""衣服移除模块 - 使用 Stable Diffusion + ControlNet"""

import os
import torch
import numpy as np
from PIL import Image, ImageDraw
import cv2
from diffusers import StableDiffusionInpaintPipeline, ControlNetModel
from diffusers.utils import load_image

class ClothesRemover:
    """衣服移除器 - 保留姿态和脸部"""
    
    def __init__(self, model_path: str = None, device: str = "cpu"):
        self.device = device
        self.pipeline = None
        self.controlnet = None
        self._load_models(model_path)
    
    def _load_models(self, model_path):
        """加载模型"""
        try:
            # 加载 ControlNet 用于姿态保留
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
            
            # 使用 OpenPose ControlNet
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-openpose",
                torch_dtype=torch.float32
            )
            
            # 加载 Inpaint Pipeline
            self.pipeline = StableDiffusionControlNetPipeline.from_pretrained(
                model_path or "runwayml/stable-diffusion-v1-5",
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
            )
            self.pipeline.to(self.device)
            print("✅ 模型加载完成")
        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}")
            print("💡 降级到简单模式")
            self.pipeline = None
    
    def remove_clothes(
        self,
        image_path: str,
        output_path: str = None,
        prompt: str = "nude, naked body, artistic nude, no clothes",
        negative_prompt: str = "clothes, fabric, ugly, deformed",
        mask_padding: int = 20,
        strength: float = 0.8,
        steps: int = 30
    ) -> str:
        """
        移除图片中的衣服
        
        参数:
            image_path: 原图路径
            output_path: 输出路径
            prompt: 生成提示词
            mask_padding: 遮罩扩展像素
            strength: 重绘强度
        
        返回:
            处理后的图片路径
        """
        # 1. 加载图片
        image = Image.open(image_path).convert("RGB")
        
        # 2. 生成衣服遮罩（使用人体分割）
        mask = self._generate_clothes_mask(image)
        
        # 3. 如果有模型，使用 Inpaint
        if self.pipeline:
            result = self._inpaint_clothes(image, mask, prompt, negative_prompt, strength, steps)
        else:
            # 降级：简单模糊填充
            result = self._simple_remove(image, mask)
        
        # 4. 保存结果
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_nude{ext}"
        
        result.save(output_path)
        print(f"✅ 已保存: {output_path}")
        return output_path
    
    def _generate_clothes_mask(self, image: Image.Image) -> Image.Image:
        """生成衣服遮罩"""
        # 转换为 OpenCV 格式
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        
        # 方法1: 使用 YOLOv8 人体分割（需要安装 ultralytics）
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n-seg.pt")
            results = model(image, verbose=False)
            
            if len(results) > 0 and results[0].masks is not None:
                # 获取人体遮罩
                masks = results[0].masks.data.cpu().numpy()
                # 合并所有人体遮罩
                combined_mask = np.zeros((h, w), dtype=np.uint8)
                for mask in masks:
                    mask_resized = cv2.resize(mask, (w, h))
                    combined_mask = np.maximum(combined_mask, (mask_resized > 0.5).astype(np.uint8) * 255)
                
                # 提取躯干区域（排除头部）
                combined_mask = self._extract_torso(combined_mask)
                
                return Image.fromarray(combined_mask, mode="L")
        except ImportError:
            print("   ⚠️ 未安装 ultralytics，使用简单遮罩")
        except Exception as e:
            print(f"   ⚠️ 人体分割失败: {e}")
        
        # 方法2: 简单的中心区域遮罩（备用）
        return self._simple_mask(image)
    
    def _extract_torso(self, mask: np.ndarray) -> np.ndarray:
        """从全身遮罩中提取躯干部分"""
        # 假设人体遮罩中，头部在顶部，躯干在中部
        h, w = mask.shape
        
        # 找到人体区域
        coords = np.where(mask > 0)
        if len(coords[0]) == 0:
            return mask
        
        y_min, y_max = coords[0].min(), coords[0].max()
        body_height = y_max - y_min
        
        # 躯干区域：从头部下方到腿部上方
        torso_top = y_min + int(body_height * 0.2)  # 头部下方
        torso_bottom = y_max - int(body_height * 0.15)  # 腿部上方
        
        # 创建躯干遮罩
        torso_mask = np.zeros_like(mask)
        torso_mask[torso_top:torso_bottom, :] = mask[torso_top:torso_bottom, :]
        
        # 稍微膨胀
        kernel = np.ones((10, 10), np.uint8)
        torso_mask = cv2.dilate(torso_mask, kernel, iterations=2)
        
        return torso_mask
    
    def _simple_mask(self, image: Image.Image) -> Image.Image:
        """简单遮罩生成"""
        w, h = image.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        
        # 躯干区域（假设人物在中心）
        x = w // 2
        y = h // 2
        width = int(w * 0.4)
        height = int(h * 0.4)
        
        # 椭圆遮罩
        draw.ellipse(
            (x - width//2, y - height//2, x + width//2, y + height//2),
            fill=255
        )
        return mask
    
    def _inpaint_clothes(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompt: str,
        negative_prompt: str,
        strength: float,
        steps: int
    ) -> Image.Image:
        """使用 Inpaint 去除衣服"""
        try:
            # 使用 ControlNet 保持姿态
            # 这里简化处理，使用普通 inpaint
            from diffusers import StableDiffusionInpaintPipeline
            
            # 使用独立 inpaint pipeline
            pipe = StableDiffusionInpaintPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting",
                torch_dtype=torch.float32,
                safety_checker=None,
            )
            pipe.to(self.device)
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                mask_image=mask,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=7.5,
            ).images[0]
            
            return result
        except Exception as e:
            print(f"   ⚠️ Inpaint 失败: {e}")
            return self._simple_remove(image, mask)
    
    def _simple_remove(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """简单去除（模糊填充）"""
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        mask_cv = np.array(mask)
        
        # 使用 inpaint
        result = cv2.inpaint(img_cv, mask_cv, 3, cv2.INPAINT_TELEA)
        result = cv2.GaussianBlur(result, (5, 5), 0)
        
        return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))