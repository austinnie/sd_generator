# scripts/remove_clothes.py
"""
衣服移除工具 - 使用本地 SD Inpaint 模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import torch
import numpy as np
from PIL import Image, ImageDraw
import cv2
from typing import Optional


class ClothesRemover:
    """衣服移除器"""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._yolo_model = None
        self._sd_pipe = None
        print("👕 衣服移除器已初始化")
    
    def _get_yolo_model(self):
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n-seg.pt")
                print("   ✅ YOLO 加载成功")
            except:
                self._yolo_model = False
        return self._yolo_model
    
    def _load_sd_model(self):
        """加载本地 SD Inpaint 模型"""
        if self._sd_pipe is None:
            try:
                from diffusers import StableDiffusionInpaintPipeline
                
                model_path = r"E:\SD_OpenVINO\models\sd-v1-5\sd-v1-5-inpainting-tiny.safetensors"
                
                if not os.path.exists(model_path):
                    print(f"   ⚠️ 模型不存在: {model_path}")
                    print("   🔄 尝试使用 runwayml/stable-diffusion-inpainting")
                    model_path = "runwayml/stable-diffusion-inpainting"
                
                print(f"   📦 加载模型: {os.path.basename(model_path) if os.path.exists(model_path) else model_path}")
                self._sd_pipe = StableDiffusionInpaintPipeline.from_single_file(
                    model_path,
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
                self._sd_pipe.to(self.device)
                if self.device == "cpu":
                    self._sd_pipe.enable_attention_slicing()
                print("   ✅ SD Inpaint 模型加载成功")
            except ImportError:
                print("   ⚠️ 未安装 diffusers")
                print("   💡 安装: pip install diffusers transformers accelerate")
                self._sd_pipe = False
            except Exception as e:
                print(f"   ⚠️ SD 模型加载失败: {e}")
                self._sd_pipe = False
        return self._sd_pipe
    
    def _generate_mask(self, image: Image.Image) -> Image.Image:
        """生成衣服遮罩"""
        h, w = image.size[1], image.size[0]
        
        yolo = self._get_yolo_model()
        if yolo and yolo is not False:
            try:
                results = yolo(image, verbose=False)
                if len(results) > 0 and results[0].masks is not None:
                    masks = results[0].masks.data.cpu().numpy()
                    combined = np.zeros((h, w), dtype=np.uint8)
                    for m in masks:
                        m_resized = cv2.resize(m, (w, h))
                        combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)
                    
                    coords = np.where(combined > 0)
                    if len(coords[0]) > 0:
                        y_min, y_max = coords[0].min(), coords[0].max()
                        body_h = y_max - y_min
                        neck = y_min + int(body_h * 0.18)
                        hip = y_min + int(body_h * 0.70)
                        
                        x_min, x_max = coords[1].min(), coords[1].max()
                        body_w = x_max - x_min
                        left = x_min + int(body_w * 0.10)
                        right = x_max - int(body_w * 0.10)
                        
                        clothes = np.zeros_like(combined)
                        clothes[neck:hip, left:right] = combined[neck:hip, left:right]
                        clothes = cv2.GaussianBlur(clothes, (9, 9), 0)
                        return Image.fromarray(clothes, mode="L")
            except Exception as e:
                print(f"   ⚠️ YOLO 失败: {e}")
        
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        cx, cy = w // 2, h // 2
        draw.ellipse((cx - w//4, cy - h//3, cx + w//4, cy + h//3), fill=255)
        return mask
    
    def remove_clothes(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        prompt: str = "nude, naked body, beautiful skin, realistic body, masterpiece",
        negative_prompt: str = "clothes, fabric, ugly, deformed, bad anatomy",
        strength: float = 0.85,
        steps: int = 30,
        seed: Optional[int] = None,
        save_mask: bool = False
    ) -> str:
        """去除衣服 - 保持原始尺寸"""
        sd = self._load_sd_model()
        if sd is None or sd is False:
            raise RuntimeError("SD 模型不可用")
        
        # 🔥 保存原始尺寸
        image = Image.open(image_path).convert("RGB")
        original_size = image.size  # (width, height)
        
        print(f"   📷 处理: {os.path.basename(image_path)} ({original_size[0]}x{original_size[1]})")
        
        # 🔥 如果图片太大，缩小到 768x768 以内（加速）
        max_size = 768
        if max(original_size) > max_size:
            ratio = max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            # 确保是 64 的倍数（SD 要求）
            new_size = (new_size[0] - new_size[0] % 64, new_size[1] - new_size[1] % 64)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"   📐 缩放至: {new_size[0]}x{new_size[1]}")
        
        print("   🎯 生成遮罩...")
        mask = self._generate_mask(image)
        
        if save_mask:
            mask_path = image_path.replace('.png', '_mask.png').replace('.jpg', '_mask.png')
            mask.save(mask_path)
            print(f"   📋 遮罩: {os.path.basename(mask_path)}")
        
        print(f"   🎨 SD Inpaint 生成中...")
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # 🔥 使用当前图片尺寸
        current_size = image.size
        result = sd(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=7.5,
            generator=generator,
            width=current_size[0],
            height=current_size[1],
        ).images[0]
        
        # 🔥 恢复原始尺寸
        if result.size != original_size:
            print(f"   📐 恢复原始尺寸: {original_size[0]}x{original_size[1]}")
            result = result.resize(original_size, Image.Resampling.LANCZOS)
        
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_nude{ext}"
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        result.save(output_path)
        print(f"   ✅ 保存: {os.path.basename(output_path)}")
        return output_path


def batch_process(input_dir: str, output_dir: Optional[str] = None, **kwargs) -> list:
    """批量处理"""
    if output_dir is None:
        output_dir = os.path.join(input_dir, "nude_output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    extensions = ('.png', '.jpg', '.jpeg')
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) 
             if f.lower().endswith(extensions)]
    files = sorted(files)
    
    if not files:
        print(f"❌ 未找到图片: {input_dir}")
        return []
    
    print(f"\n📁 找到 {len(files)} 个图片")
    print(f"📂 输出: {output_dir}")
    print("=" * 60)
    
    remover = ClothesRemover(device=kwargs.get('device', 'cpu'))
    results = []
    
    for i, input_path in enumerate(files):
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n[{i+1}/{len(files)}] {filename}")
        
        try:
            result = remover.remove_clothes(
                input_path, output_path,
                prompt=kwargs.get('prompt', "nude, naked body, beautiful skin, realistic body, masterpiece"),
                negative_prompt=kwargs.get('negative_prompt', "clothes, fabric, ugly, deformed"),
                strength=kwargs.get('strength', 0.85),
                steps=kwargs.get('steps', 30),
                seed=kwargs.get('seed'),
                save_mask=kwargs.get('save_mask', False)
            )
            results.append(result)
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    print(f"\n✅ 完成: {len(results)} 张")
    return results


def main():
    parser = argparse.ArgumentParser(description="去除图片中的衣服")
    parser.add_argument("input", help="图片路径或目录")
    parser.add_argument("-o", "--output", help="输出路径")
    parser.add_argument("--batch", action="store_true", help="批量模式")
    parser.add_argument("--prompt", type=str, 
                        default="nude, naked body, beautiful skin, realistic body, masterpiece",
                        help="生成提示词")
    parser.add_argument("--negative", type=str,
                        default="clothes, fabric, ugly, deformed, bad anatomy",
                        help="负面提示词")
    parser.add_argument("--strength", type=float, default=0.85, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    
    args = parser.parse_args()
    
    if args.batch:
        if not os.path.isdir(args.input):
            print(f"❌ 批量模式需要目录: {args.input}")
            return
        batch_process(args.input, args.output, 
                      prompt=args.prompt, negative_prompt=args.negative,
                      strength=args.strength, steps=args.steps,
                      seed=args.seed, device=args.device, save_mask=args.save_mask)
        return
    
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        return
    
    remover = ClothesRemover(device=args.device)
    result = remover.remove_clothes(args.input, args.output,
                                    prompt=args.prompt, negative_prompt=args.negative,
                                    strength=args.strength, steps=args.steps,
                                    seed=args.seed, save_mask=args.save_mask)
    print(f"\n✅ 完成: {result}")


if __name__ == "__main__":
    main()