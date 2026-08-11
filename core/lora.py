# core/lora.py
"""LoRA 管理 - 支持 SD 1.5 和 SDXL"""

import os
from typing import List, Dict

from config.app import get_sd15_lora_dir, get_sdxl_lora_dir


class LoraManager:
    """LoRA 管理器"""
    
    def __init__(self):
        self.sd15_dir = get_sd15_lora_dir()
        self.sdxl_dir = get_sdxl_lora_dir()
    
    def list(self, model_type: str = None) -> List[Dict]:
        """列出 LoRA，可按类型过滤"""
        loras = []
        
        # SD 1.5 LoRA
        if model_type is None or model_type == "sd15":
            if os.path.exists(self.sd15_dir):
                for f in os.listdir(self.sd15_dir):
                    if f.endswith('.safetensors'):
                        path = os.path.join(self.sd15_dir, f)
                        loras.append({
                            "name": f,
                            "path": path,
                            "type": "sd15",
                            "size_mb": round(os.path.getsize(path) / (1024**2), 1),
                        })
        
        # SDXL LoRA
        if model_type is None or model_type == "sdxl":
            if os.path.exists(self.sdxl_dir):
                for f in os.listdir(self.sdxl_dir):
                    if f.endswith('.safetensors'):
                        path = os.path.join(self.sdxl_dir, f)
                        loras.append({
                            "name": f,
                            "path": path,
                            "type": "sdxl",
                            "size_mb": round(os.path.getsize(path) / (1024**2), 1),
                        })
        
        return sorted(loras, key=lambda x: x["name"])
    
    def load(self, pipeline, path: str, weight: float = 1.0) -> bool:
        """加载 LoRA"""
        if not os.path.exists(path):
            print(f"❌ LoRA 不存在: {path}")
            return False
        
        try:
            pipeline.load_lora_weights(path)
            if weight != 1.0 and hasattr(pipeline, 'set_adapters'):
                pipeline.set_adapters(["default"], adapter_weights=[weight])
            return True
        except Exception as e:
            print(f"❌ LoRA 加载失败: {e}")
            return False
    
    def unload(self, pipeline) -> bool:
        """卸载 LoRA"""
        try:
            if hasattr(pipeline, 'unload_lora_weights'):
                pipeline.unload_lora_weights()
                return True
        except:
            pass
        return False