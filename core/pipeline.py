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

import torch
from safetensors.torch import load_file

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
# core/pipeline.py
# core/pipeline.py - 第 174 行附近
# 将整个 _load_loras 函数替换为：

def _load_loras(pipe):
    """加载 LoRA - 兼容 Python 3.14 + 新版 diffusers"""
    try:
        from config.app import FINAL_LORA_LIST
        import os
        
        lora_list = FINAL_LORA_LIST
        
        if not lora_list:
            print("   ℹ️ 未配置 LoRA")
            return
        
        print(f"   📦 准备加载 {len(lora_list)} 个 LoRA...")
        
        for i, lora_info in enumerate(lora_list):
            if not isinstance(lora_info, dict):
                print(f"      ⚠️ LoRA {i+1} 格式错误")
                continue
            
            lora_path = lora_info.get('path', '')
            lora_weight = lora_info.get('weight', 0.8)
            
            if not lora_path or not os.path.exists(lora_path):
                print(f"      ⚠️ LoRA 文件不存在: {lora_path}")
                continue
            
            print(f"      🔗 加载 LoRA {i+1}: {os.path.basename(lora_path)} (权重: {lora_weight})")
            
            # 方法 1: 标准加载
            try:
                pipe.load_lora_weights(lora_path)
                print(f"      ✅ LoRA {i+1} 加载成功 (标准模式)")
                continue
            except Exception as e:
                print(f"      ⚠️ 标准模式失败: {e}")
            
            # ✅ 方法 4: 手动加载（最后的手段）
            try:
                if load_lora_manual(pipe, lora_path):
                    print(f"      ✅ LoRA {i+1} 加载成功 (手动模式)")
                    continue
            except Exception as e:
                print(f"      ⚠️ 手动模式失败: {e}")
            
            print(f"      ❌ LoRA {i+1} 所有方法都失败")
                
    except Exception as e:
        print(f"   ⚠️ LoRA 加载出错: {e}")
        import traceback
        traceback.print_exc()

def load_lora_manual(pipe, lora_path: str):
    """手动加载 LoRA（绕过 diffusers 的 PEFT 检查）"""
    try:
        print(f"      🔧 手动加载 LoRA...")
        
        # 1. 加载 LoRA 权重
        state_dict = load_file(lora_path)
        
        # 2. 分离 UNet 和 Text Encoder 的权重
        unet_state_dict = {}
        te_state_dict = {}
        
        for key, value in state_dict.items():
            # 跳过 alpha 值
            if 'alpha' in key:
                continue
            
            if 'lora_te_' in key:
                # Text Encoder 权重 - 保持原样
                te_state_dict[key] = value
            else:
                # UNet 权重
                unet_state_dict[key] = value
        
        # 3. 加载到 UNet
        if unet_state_dict:
            try:
                # 转换格式: lora_down -> lora_A, lora_up -> lora_B
                converted_unet = {}
                for key, value in unet_state_dict.items():
                    if 'lora_down' in key:
                        new_key = key.replace('lora_down', 'lora_A')
                        converted_unet[new_key] = value
                    elif 'lora_up' in key:
                        new_key = key.replace('lora_up', 'lora_B')
                        converted_unet[new_key] = value
                    else:
                        converted_unet[key] = value
                
                # 加载到 unet（strict=False 允许部分加载）
                pipe.unet.load_state_dict(converted_unet, strict=False)
                print(f"         ✅ UNet LoRA 加载完成 ({len(converted_unet)} 个权重)")
            except Exception as e:
                print(f"         ⚠️ UNet 加载失败: {e}")
        
        # 4. 加载到 Text Encoder
        if te_state_dict:
            try:
                # Text Encoder 也转换格式
                converted_te = {}
                for key, value in te_state_dict.items():
                    if 'lora_down' in key:
                        new_key = key.replace('lora_down', 'lora_A')
                        converted_te[new_key] = value
                    elif 'lora_up' in key:
                        new_key = key.replace('lora_up', 'lora_B')
                        converted_te[new_key] = value
                    else:
                        converted_te[key] = value
                
                pipe.text_encoder.load_state_dict(converted_te, strict=False)
                print(f"         ✅ Text Encoder LoRA 加载完成 ({len(converted_te)} 个权重)")
            except Exception as e:
                print(f"         ⚠️ Text Encoder 加载失败: {e}")
        
        print(f"      ✅ LoRA 手动加载完成")
        return True
        
    except Exception as e:
        print(f"      ❌ 手动加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
# core/pipeline.py
def _configure_scheduler(pipe):
    """配置调度器 - 兼容新旧版 diffusers"""
    try:
        # ✅ 新版 diffusers 使用 enable_vae_tiling 代替 enable_vae_slicing
        if hasattr(pipe, 'enable_vae_tiling'):
            pipe.enable_vae_tiling()
        elif hasattr(pipe, 'enable_vae_slicing'):
            pipe.enable_vae_slicing()
        else:
            print(f"   ⚠️ VAE slicing 不可用，跳过")
        
        # attention slicing 仍然可用
        if hasattr(pipe, 'enable_attention_slicing'):
            pipe.enable_attention_slicing()
        
        # 调度器配置
        from diffusers import EulerDiscreteScheduler
        try:
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            print(f"   ✅ 采样器配置完成")
        except Exception as e:
            print(f"⚠️ 采样器加载失败，使用默认配置。错误: {e}")
            
    except Exception as e:
        print(f"⚠️ Pipeline 优化配置失败: {e}")

def get_pipeline():
    """获取已加载的 Pipeline（兼容旧接口）"""
    return setup_pipeline()


if __name__ == "__main__":
    # 测试加载
    pipe = setup_pipeline()
    print("\n✅ Pipeline 加载测试完成")