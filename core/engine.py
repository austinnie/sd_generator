# core/engine.py
"""生成引擎"""

import random
import torch
from typing import Optional
from PIL import Image
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler


class GenerationEngine:
    """图片生成引擎"""
    
    def __init__(self, pipeline: StableDiffusionPipeline):
        self.pipeline = pipeline
    
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
        
        # 限制最大尺寸
        width = min(width, 1024)
        height = min(height, 1024)
        
        # 种子
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        generator = torch.Generator("cpu").manual_seed(seed)
        
        # 生成
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
