# core/model.py
import os
import gc
import torch
from typing import List, Optional, Dict
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, EulerDiscreteScheduler

from config.app import (
    SD_MODEL_PATH, AVAILABLE_MODELS, MODEL_INDEX,
    resolve_model_path_from_index, MODEL_SELECTION_MODE
)


class ModelManager:
    def __init__(self):
        self.pipeline = None
        self.current = None
        self.model_type = None
        self._current_path = None
        self._models_cache = AVAILABLE_MODELS  # 直接使用 config 中的索引
    
    def list_models(self, model_type: str = None) -> List[Dict]:
        """获取模型列表"""
        models = self._models_cache
        if model_type:
            models = [m for m in models if m.get('type') == model_type]
        return models
    
    def get_default_model(self) -> Optional[str]:
        """获取默认推荐模型"""
        return MODEL_INDEX.get('default') if MODEL_INDEX else None
    
    def find_by_name(self, name: str, model_type: str = None) -> Optional[Dict]:
        """根据名称查找模型"""
        models = self.list_models(model_type)
        name_lower = name.lower()
        for m in models:
            if m['name'].lower() == name_lower or name_lower in m['name'].lower():
                return m
        return None
    
    def load(self, name: str = None, model_type: str = None) -> bool:
        """加载模型"""
        if name is None:
            # 使用 config 中解析的路径
            path = SD_MODEL_PATH
            if not path or not os.path.exists(path):
                print(f"❌ 模型路径不存在: {path}")
                return False
            return self._load_from_path(path)
        
        target = self.find_by_name(name, model_type)
        if not target:
            print(f"❌ 模型不存在: {name}")
            return False
        
        path = resolve_model_path_from_index(target)
        if not path or not os.path.exists(path):
            print(f"❌ 模型文件不存在: {path}")
            return False
        
        return self._load_from_path(path)
    
    def _load_from_path(self, path: str) -> bool:
        """从路径加载模型（自动识别 SD1.5 / SDXL）"""
        self.unload()
        try:
            # 从 config 获取 MODEL_TYPE
            from config.app import MODEL_TYPE
            
            # 如果路径包含 sdxl 或 xl，自动识别
            is_sdxl = "sdxl" in path.lower() or "xl" in path.lower()
            
            # 优先使用 config 中的 MODEL_TYPE
            if MODEL_TYPE == "sdxl" or is_sdxl:
                model_type = "sdxl"
                print(f"📦 加载 SDXL 模型: {os.path.basename(path)}")
                self.pipeline = StableDiffusionXLPipeline.from_single_file(
                    path, torch_dtype=torch.float32,
                    safety_checker=None, requires_safety_checker=False
                )
            else:
                model_type = "sd15"
                print(f"📦 加载 SD1.5 模型: {os.path.basename(path)}")
                self.pipeline = StableDiffusionPipeline.from_single_file(
                    path, torch_dtype=torch.float32,
                    safety_checker=None, requires_safety_checker=False
                )
            
            self.model_type = model_type
            
            self.pipeline.to("cpu")
            self.current = os.path.basename(path)
            
            # 优化设置
            if hasattr(self.pipeline, 'vae'):
                try: self.pipeline.vae.enable_slicing()
                except: pass
            try: self.pipeline.enable_attention_slicing()
            except: pass
            
            print(f"✅ 模型加载成功: {self.current}")
            return True
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False
    
    def unload(self):
        if self.pipeline:
            try: del self.pipeline
            except: pass
            self.pipeline = None
        self.current = None
        self.model_type = None
        gc.collect()
    
    def get_pipeline(self): return self.pipeline
    def get_model_type(self) -> str: return self.model_type or "unknown"
    def is_loaded(self) -> bool: return self.pipeline is not None