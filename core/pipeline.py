# core/pipeline.py
"""Pipeline 管理和模型加载"""

import os
import sys
import torch
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    EulerDiscreteScheduler,
)

# 导入配置
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config.app import (
    MODEL_TYPE,
    USE_OPENVINO_MODEL,
    SD_MODEL_PATH,
)


def setup_pipeline():
    """加载 AI 模型 Pipeline"""
    print(f"\n[系统] 正在加载 AI 模型...")
    
    # ========== SDXL 分支 ==========
    if MODEL_TYPE == "sdxl":
        return _setup_sdxl_pipeline()
    
    # ========== OpenVINO 分支 ==========
    elif USE_OPENVINO_MODEL:
        return _setup_openvino_pipeline()
    
    # ========== SD1.5 分支 ==========
    else:
        return _setup_sd15_pipeline()


def _setup_sdxl_pipeline():
    """加载 SDXL 模型"""
    print(f"⚡ [配置] 使用 SDXL 模型")
    model_path = _resolve_model_path(SD_MODEL_PATH)
    
    try:
        pipe = StableDiffusionXLPipeline.from_single_file(
            model_path,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            variant="fp16"
        )
        pipe.to("cpu")
        print("✅ SDXL 模型加载成功！")
        
        # 加载 LoRA
        _load_loras(pipe)
        
        # 配置调度器
        _configure_scheduler(pipe)
        
        return pipe
    except Exception as e:
        print(f"❌ SDXL 模型加载失败: {e}")
        sys.exit(1)


def _setup_sd15_pipeline():
    """加载 SD1.5 模型"""
    print(f"⚡ [配置] 使用 SD1.5 模型")
    model_path = _resolve_model_path(SD_MODEL_PATH)
    
    try:
        pipe = StableDiffusionPipeline.from_single_file(
            model_path,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True
        )
        pipe.to("cpu")
        print("✅ SD1.5 模型加载成功！")
        
        ## 加载 LoRA
        _load_loras(pipe)
        
        # 配置调度器
        _configure_scheduler(pipe)
        
        return pipe
    except Exception as e:
        print(f"❌ SD1.5 模型加载失败: {e}")
        sys.exit(1)


def _setup_openvino_pipeline():
    """加载 OpenVINO 模型"""
    print(f"⚡ [配置] 使用 OpenVINO 加速模式")
    
    try:
        from optimum.intel import OVStableDiffusionPipeline
        print("⚡ 尝试加载 OpenVINO 接口...")
        pipe = OVStableDiffusionPipeline.from_pretrained(
            SD_MODEL_PATH, compile=False, export=True
        )
        print("✅ OpenVINO 模型加载成功！")
        return pipe
    except Exception as e:
        print(f"❌ OpenVINO 加载失败: {e}")
        sys.exit(1)


def _resolve_model_path(model_path):
    """解析模型路径（支持目录）"""
    if os.path.isdir(model_path):
        import glob
        safetensors_files = glob.glob(os.path.join(model_path, "*.safetensors"))
        if safetensors_files:
            model_path = safetensors_files[0]
            print(f"   🔍 自动定位到: {os.path.basename(model_path)}")
        else:
            print(f"❌ 在目录中找不到 .safetensors 文件")
            sys.exit(1)
    return model_path


# sd_generator/core/pipeline.py
def _load_loras(pipe):
    """加载 LoRA - 移植自 tools 的稳定版本"""
    try:
        from config.app import FINAL_LORA_LIST
        import os
        
        lora_list = FINAL_LORA_LIST
        
        if not lora_list:
            print("   ℹ️ 未配置 LoRA")
            return
        
        print(f"   📦 准备加载 {len(lora_list)} 个 LoRA...")
        adapter_names = []
        adapter_weights = []
        
        for i, lora_info in enumerate(lora_list):
            lora_path = lora_info.get('path', '')
            lora_weight = lora_info.get('weight', 0.8)
            
            if not os.path.exists(lora_path):
                print(f"      ⚠️ LoRA 文件不存在: {lora_path}")
                continue
            
            adapter_name = f"lora_{i}"
            print(f"      🔗 加载 LoRA {i+1}: {os.path.basename(lora_path)} (权重: {lora_weight})")
            
            try:
                pipe.load_lora_weights(lora_path, adapter_name=adapter_name)
                adapter_names.append(adapter_name)
                adapter_weights.append(lora_weight)
            except Exception as e:
                print(f"      ❌ LoRA {i+1} 加载失败: {e}")
                # 尝试兼容模式
                try:
                    pipe.load_lora_weights(lora_path)
                    print(f"      ✅ LoRA {i+1} 加载成功（兼容模式）")
                except Exception as e2:
                    print(f"      ❌ 兼容模式也失败: {e2}")
        
        if adapter_names:
            try:
                pipe.set_adapters(adapter_names, adapter_weights=adapter_weights)
                print(f"      ✅ 全部 {len(adapter_names)} 个 LoRA 加载成功！")
            except Exception as e:
                print(f"      ⚠️ 设置权重失败: {e}")
                
    except Exception as e:
        print(f"   ⚠️ LoRA 加载跳过: {e}")

def _configure_scheduler(pipe):
    """配置调度器"""
    try:
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing()
        
        print(f"   🎛️ 使用默认采样器: Euler")
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        print(f"   ✅ 采样器配置完成")
            
    except Exception as e:
        print(f"⚠️ 采样器加载失败，使用默认配置。错误: {e}")
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)


def get_pipeline():
    """获取已加载的 Pipeline（兼容旧接口）"""
    return setup_pipeline()


if __name__ == "__main__":
    # 测试加载
    pipe = setup_pipeline()
    print("\n✅ Pipeline 加载测试完成")