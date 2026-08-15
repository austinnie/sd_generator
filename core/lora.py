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
    
    # core/lora.py - LoraManager.load 方法

    def load(self, pipeline, path: str, weight: float = 1.0, name: str = None) -> bool:
        """加载 LoRA（参考 v8 的方式）"""
        if not os.path.exists(path):
            print(f"❌ LoRA 不存在: {path}")
            return False
        
        if name is None:
            name = os.path.basename(path)
        
        try:
            # ✅ 修复：生成合法的适配器名称（移除文件扩展名和特殊字符）
            import re
            # 获取不带扩展名的文件名
            base_name = os.path.splitext(os.path.basename(path))[0]
            # 只保留字母、数字和下划线，移除其他特殊字符
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
            # 截断到合理长度，并添加前缀
            adapter_name = f"lora_{clean_name[:40]}"
            # 确保名称不是以数字开头（Python 模块命名规范）
            if adapter_name[0].isdigit():
                adapter_name = f"lora_{adapter_name}"
            
            print(f"   🔗 加载 LoRA: {os.path.basename(path)} (权重: {weight})")
            print(f"      📛 适配器名称: {adapter_name}")
            
            pipeline.load_lora_weights(path, adapter_name=adapter_name)
            
            # 设置权重
            if weight != 1.0:
                try:
                    # 检查适配器是否已加载
                    if hasattr(pipeline, 'get_adapter_names'):
                        # 获取已加载的适配器列表
                        loaded_adapters = pipeline.get_adapter_names()
                        if adapter_name in loaded_adapters:
                            pipeline.set_adapters([adapter_name], adapter_weights=[weight])
                        else:
                            # 如果适配器名称不匹配，尝试使用默认方式
                            pipeline.set_adapters([adapter_name], adapter_weights=[weight])
                    else:
                        pipeline.set_adapters([adapter_name], adapter_weights=[weight])
                except Exception as e:
                    print(f"   ⚠️ 设置权重失败: {e}")
            
            self._loaded_loras.append({
                "path": path, 
                "weight": weight,
                "name": name,
                "adapter_name": adapter_name  # 保存适配器名称以便后续管理
            })
            return True
            
        except TypeError as e:
            # adapter_name 参数不被支持（旧版 diffusers）
            if "unexpected keyword argument" in str(e) or "adapter_name" in str(e):
                try:
                    print(f"   🔗 使用兼容模式加载...")
                    pipeline.load_lora_weights(path)
                    if weight != 1.0 and hasattr(pipeline, 'set_adapters'):
                        # 兼容模式下，适配器名称默认为 "default"
                        pipeline.set_adapters(["default"], adapter_weights=[weight])
                    self._loaded_loras.append({"path": path, "weight": weight, "name": name})
                    return True
                except Exception as e2:
                    print(f"❌ LoRA 加载失败: {e2}")
                    return False
            else:
                print(f"❌ LoRA 加载失败: {e}")
                return False
        
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