# core/model.py
"""模型管理"""

import os
import gc
import torch  # ✅ 添加这行
from typing import List, Optional
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler


class ModelManager:
    """模型管理器"""
    
    def __init__(self, model_dir: str):
        # 如果是相对路径，转为绝对路径
        if not os.path.isabs(model_dir):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.model_dir = os.path.normpath(os.path.join(base, model_dir))
        else:
            self.model_dir = model_dir
        
        self.pipeline: Optional[StableDiffusionPipeline] = None
        self.current: Optional[str] = None
    
    def list_models(self) -> List[str]:
        """列出所有模型"""
        if not os.path.exists(self.model_dir):
            print(f"⚠️ 模型目录不存在: {self.model_dir}")
            return []
        
        models = []
        for f in os.listdir(self.model_dir):
            if f.endswith(('.safetensors', '.ckpt')):
                path = os.path.join(self.model_dir, f)
                size_gb = os.path.getsize(path) / (1024**3)
                if size_gb > 2:  # > 2GB
                    models.append(f)
                else:
                    print(f"   ⏭️ 跳过: {f} ({size_gb:.1f}GB < 2GB)")
        return sorted(models)
    
    def load(self, name: str) -> bool:
        """加载模型"""
        path = os.path.join(self.model_dir, name)
        if not os.path.exists(path):
            print(f"❌ 模型不存在: {path}")
            return False
        
        self.unload()
        
        try:
            print(f"📦 加载模型: {name}")
            
            self.pipeline = StableDiffusionPipeline.from_single_file(
                path,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True,
            )
            self.pipeline.to("cpu")
            self.pipeline.enable_vae_slicing()
            self.pipeline.enable_attention_slicing()
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
                if hasattr(self.pipeline, 'to'):
                    self.pipeline.to("cpu")
                del self.pipeline
            except:
                pass
            self.pipeline = None
        self.current = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_pipeline(self):
        return self.pipeline