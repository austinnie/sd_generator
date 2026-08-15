# core/lora.py
import os
from typing import List, Dict, Optional

from config.app import AVAILABLE_LORAS, LORA_INDEX, FINAL_LORA_LIST


class LoraManager:
    def __init__(self):
        self._loaded_loras = []
        self._loras_cache = AVAILABLE_LORAS
    
    def list(self, model_type: str = None) -> List[Dict]:
        """获取 LoRA 列表，可按类型过滤"""
        loras = self._loras_cache
        if model_type:
            # ✅ 修复：使用 lora_type
            loras = [l for l in loras if l.get('lora_type') == model_type]
        return loras
    
    def get_default_lora(self) -> Optional[str]:
        return LORA_INDEX.get('default') if LORA_INDEX else None
    
    def find_by_name(self, name: str, model_type: str = None) -> Optional[Dict]:
        """根据名称查找 LoRA"""
        loras = self.list(model_type)
        name_lower = name.lower()
        for l in loras:
            if l['name'].lower() == name_lower or name_lower in l['name'].lower():
                return l
        return None
    
    def load_by_name(self, pipeline, name: str, weight: float = 1.0,
                     model_type: str = None) -> bool:
        """根据名称加载 LoRA（自动匹配模型类型）"""
        from config.app import MODEL_TYPE
        
        if model_type is None:
            model_type = MODEL_TYPE
        
        lora_info = self.find_by_name(name, model_type)
        if not lora_info:
            print(f"❌ 未找到 {model_type} 类型的 LoRA: {name}")
            return False
        
        # 解析路径
        path = None
        if "path" in lora_info and lora_info["path"]:
            from config.app import PROJECT_ROOT
            path = os.path.normpath(os.path.join(PROJECT_ROOT, lora_info["path"]))
        if not path or not os.path.exists(path):
            if "absolute_path" in lora_info:
                path = lora_info["absolute_path"]
        
        if not path or not os.path.exists(path):
            print(f"❌ LoRA 文件不存在: {path}")
            return False
        
        return self.load(pipeline, path, weight, name)
    
    # core/lora.py

    def load(self, pipeline, path: str, weight: float = 1.0, name: str = None) -> bool:
        """加载 LoRA - 只加载，不设置额外参数"""
        if not os.path.exists(path):
            print(f"❌ LoRA 不存在: {path}")
            return False
        
        if name is None:
            name = os.path.basename(path)
        
        try:
            print(f"   🔗 加载 LoRA: {os.path.basename(path)} (权重: {weight})")
            
            # ✅ 直接加载，不设置任何额外参数
            # diffusers 会在加载时自动处理权重
            pipeline.load_lora_weights(path)
            print(f"      ✅ LoRA 加载成功")
            self._loaded_loras.append({
                "path": path, 
                "weight": weight,
                "name": name
            })
            return True
                
        except Exception as e:
            print(f"❌ LoRA 加载失败: {e}")
            return False   

      
    def unload(self, pipeline) -> bool:
        try:
            if hasattr(pipeline, 'unload_lora_weights'):
                pipeline.unload_lora_weights()
                self._loaded_loras = []
                return True
        except:
            pass
        return False
    
    def get_loaded(self) -> List[Dict]:
        return self._loaded_loras.copy()