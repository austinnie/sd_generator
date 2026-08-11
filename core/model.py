# core/model.py
"""模型管理 - 支持 SD 1.5 和 SDXL"""

import os
import gc
import torch
from typing import List, Optional, Dict
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler

from config.app import get_sd15_model_dir, get_sdxl_model_dir


class ModelManager:
    """模型管理器 - 支持 SD 1.5 和 SDXL"""
    
    def __init__(self):
        self.sd15_dir = get_sd15_model_dir()
        self.sdxl_dir = get_sdxl_model_dir()
        self.pipeline = None
        self.current = None
        self.model_type = None  # "sd15" 或 "sdxl"
    
    def list_models(self) -> List[Dict]:
        """列出所有模型，带类型标记"""
        models = []
        
        # SD 1.5
        if os.path.exists(self.sd15_dir):
            for f in os.listdir(self.sd15_dir):
                if f.endswith(('.safetensors', '.ckpt')):
                    path = os.path.join(self.sd15_dir, f)
                    size_gb = os.path.getsize(path) / (1024**3)
                    if size_gb > 1.5:
                        models.append({
                            "name": f,
                            "path": path,
                            "type": "sd15",
                            "size_gb": round(size_gb, 2),
                        })
        
        # SDXL
        if os.path.exists(self.sdxl_dir):
            for f in os.listdir(self.sdxl_dir):
                if f.endswith(('.safetensors', '.ckpt')):
                    path = os.path.join(self.sdxl_dir, f)
                    size_gb = os.path.getsize(path) / (1024**3)
                    if size_gb > 3.0:  # SDXL 通常 > 4GB
                        models.append({
                            "name": f,
                            "path": path,
                            "type": "sdxl",
                            "size_gb": round(size_gb, 2),
                        })
        
        return sorted(models, key=lambda x: x["size_gb"], reverse=True)
    
    def load(self, name: str, model_type: str = None) -> bool:
        """加载模型"""
        # 查找模型
        all_models = self.list_models()
        target = None
        for m in all_models:
            if m["name"] == name:
                target = m
                break
        
        if not target:
            print(f"❌ 模型不存在: {name}")
            return False
        
        self.unload()
        
        try:
            print(f"📦 加载模型: {name} ({target['type'].upper()})")
            self.model_type = target["type"]
            
            if target["type"] == "sdxl":
                self.pipeline = StableDiffusionXLPipeline.from_single_file(
                    target["path"],
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                    use_safetensors=True,
                )
            else:
                self.pipeline = StableDiffusionPipeline.from_single_file(
                    target["path"],
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                    use_safetensors=True,
                )
            
            self.pipeline.to("cpu")
            
            # VAE 切片
            if hasattr(self.pipeline, 'vae'):
                try:
                    self.pipeline.vae.enable_slicing()
                except:
                    pass
                try:
                    self.pipeline.vae.enable_tiling()
                except:
                    pass
            
            # 注意力切片
            try:
                self.pipeline.enable_attention_slicing()
            except:
                pass
            
            # 调度器
            self.pipeline.scheduler = EulerDiscreteScheduler.from_config(
                self.pipeline.scheduler.config
            )
            
            self.current = name
            print(f"✅ 模型加载成功: {name}")
            return True
            
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload(self):
        """卸载模型"""
        if self.pipeline:
            try:
                del self.pipeline
            except:
                pass
            self.pipeline = None
        self.current = None
        self.model_type = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_pipeline(self):
        return self.pipeline
    
    def get_model_type(self) -> str:
        return self.model_type or "unknown"