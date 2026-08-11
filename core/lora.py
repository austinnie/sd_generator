# core/lora.py
"""LoRA 管理"""

import os
from typing import List, Dict


class LoraManager:
    """LoRA 管理器"""
    
    def __init__(self, lora_dir: str):
        self.lora_dir = lora_dir
    
    def list(self) -> List[Dict]:
        """列出所有 LoRA"""
        if not os.path.exists(self.lora_dir):
            return []
        return [
            {
                "name": f,
                "path": os.path.join(self.lora_dir, f),
                "size_mb": os.path.getsize(os.path.join(self.lora_dir, f)) / (1024**2),
            }
            for f in os.listdir(self.lora_dir)
            if f.endswith('.safetensors')
        ]
    
    def load(self, pipeline, path: str, weight: float = 1.0) -> bool:
        """加载 LoRA"""
        if not os.path.exists(path):
            return False
        try:
            pipeline.load_lora_weights(path)
            if weight != 1.0 and hasattr(pipeline, 'set_adapters'):
                pipeline.set_adapters(["default"], adapter_weights=[weight])
            return True
        except:
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
