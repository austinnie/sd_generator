# core/engine.py
"""生成引擎 - 支持 SD 1.5 和 SDXL"""

import random
import torch
from typing import Optional
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler


class GenerationEngine:
    """图片生成引擎 - 支持 SD 1.5 和 SDXL"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        # 判断是否为 SDXL
        self.is_sdxl = isinstance(pipeline, StableDiffusionXLPipeline)
    
    def generate_single(
        self,
        prompt: str,
        negative: str = "worst quality, low quality, ugly, deformed",
        width: int = 512,
        height: int = 768,
        steps: int = 25,
        cfg: float = 7.5,
        seed: Optional[int] = None,
        image: Optional[Image.Image] = None,
        strength: float = 0.4,
    ) -> Image.Image:
        """生成单张图片"""
        # 尺寸对齐
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        # SDXL 最小尺寸要求
        if self.is_sdxl:
            width = max(width, 512)
            height = max(height, 512)
            # SDXL 推荐尺寸
            if width < 768 and height < 768:
                width = 768
                height = 768
        
        # 限制最大尺寸
        width = min(width, 1024)
        height = min(height, 1024)
        
        # 种子
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(seed)
        
        # ===== SDXL 需要额外的参数 =====
        if self.is_sdxl:
            # SDXL 需要 added_cond_kwargs
            added_cond_kwargs = {
                "text_embeds": None,
                "time_ids": self._get_time_ids(width, height),
            }
            
            if image:
                # 图生图模式 (SDXL)
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative,
                    image=image,
                    strength=strength,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                    added_cond_kwargs=added_cond_kwargs,
                )
            else:
                # 文生图模式 (SDXL)
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    width=width,
                    height=height,
                    generator=generator,
                    added_cond_kwargs=added_cond_kwargs,
                )
        else:
            # SD 1.5
            if image:
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative,
                    image=image,
                    strength=strength,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                )
            else:
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    width=width,
                    height=height,
                    generator=generator,
                )
        
        return result.images[0]
    
    def _get_time_ids(self, width: int, height: int):
        """获取 SDXL 的 time_ids"""
        # SDXL 需要 6 个值: (original_size, target_size, crop)
        # 这里简化为相同的尺寸
        return torch.tensor([
            height, width,  # original_size
            height, width,  # target_size
            0, 0,           # crop
        ], dtype=torch.float32)