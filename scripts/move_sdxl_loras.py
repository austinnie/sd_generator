# scripts/move_sdxl_loras.py
"""识别并移动 SDXL LoRA 到正确的目录"""

import os
import shutil
import json
from pathlib import Path
from safetensors import safe_open

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD15_LORA_DIR = os.path.join(PROJECT_ROOT, "../models/sd15-lora")
SDXL_LORA_DIR = os.path.join(PROJECT_ROOT, "../models/sdxl-lora")

# 标准化路径
SD15_LORA_DIR = os.path.normpath(SD15_LORA_DIR)
SDXL_LORA_DIR = os.path.normpath(SDXL_LORA_DIR)

# SDXL 关键词（用于快速识别）
SDXL_KEYWORDS = [
    "xl", "sdxl", "xl_", "_xl", "xl-", "-xl",
    "sd_xl", "sd-xl", "sdxl_", "sdxl-",
    "pony", "ponyxl", "pony_xl",
    "base_1.0", "sd_xl_base",
]

def is_sdxl_lora(filepath: str) -> tuple:
    """
    检查 LoRA 文件是否为 SDXL 格式
    返回: (是否SDXL, 判断依据)
    """
    filename = os.path.basename(filepath).lower()
    
    # 1. 先根据文件名快速判断
    for kw in SDXL_KEYWORDS:
        if kw in filename:
            return True, f"文件名包含 '{kw}'"
    
    # 2. 检查文件元数据
    try:
        with safe_open(filepath, framework="pt") as f:
            # 检查是否有 SDXL 特有的键名
            keys = list(f.keys())
            keys_str = " ".join(keys[:50]).lower()
            
            # SDXL 有两个 text encoder (te1, te2)
            if "lora_te1_" in keys_str and "lora_te2_" in keys_str:
                return True, "包含 te1 和 te2 (SDXL 双编码器)"
            
            # 检查元数据
            if hasattr(f, 'metadata') and f.metadata():
                metadata = f.metadata()
                # 检查 model_spec
                if 'modelspec.architecture' in metadata:
                    arch = metadata['modelspec.architecture'].lower()
                    if 'sdxl' in arch or 'xl' in arch:
                        return True, f"元数据指定: {arch}"
                if 'ss_base_model_version' in metadata:
                    version = metadata['ss_base_model_version'].lower()
                    if 'sdxl' in version or 'xl' in version:
                        return True, f"训练基础模型: {version}"
    except Exception as e:
        print(f"   ⚠️ 无法读取元数据: {e}")
    
    return False, "SD1.5 格式"

def move_lora(src_path: str, dst_dir: str, dry_run: bool = True):
    """移动 LoRA 文件到目标目录"""
    filename = os.path.basename(src_path)
    dst_path = os.path.join(dst_dir, filename)
    
    if dry_run:
        print(f"   [模拟] 移动: {filename}")
        print(f"          -> {dst_path}")
        return
    
    # 检查目标是否已存在
    if os.path.exists(dst_path):
        print(f"   ⚠️ 目标已存在: {dst_path}")
        print(f"   💡 跳过移动 (请手动处理)")
        return
    
    try:
        shutil.move(src_path, dst_path)
        print(f"   ✅ 已移动: {filename}")
        print(f"          -> {dst_path}")
    except Exception as e:
        print(f"   ❌ 移动失败: {e}")

def main():
    print("=" * 70)
    print("🔍 SDXL LoRA 识别与移动工具")
    print("=" * 70)
    
    print(f"\n📁 SD1.5 LoRA 目录: {SD15_LORA_DIR}")
    print(f"📁 SDXL LoRA 目录:   {SDXL_LORA_DIR}")
    
    if not os.path.exists(SD15_LORA_DIR):
        print(f"\n❌ SD1.5 LoRA 目录不存在!")
        return
    
    if not os.path.exists(SDXL_LORA_DIR):
        print(f"\n⚠️ SDXL LoRA 目录不存在，正在创建...")
        os.makedirs(SDXL_LORA_DIR, exist_ok=True)
    
    # 获取所有 .safetensors 文件
    lora_files = []
    for ext in ['.safetensors', '.ckpt', '.pt']:
        for f in Path(SD15_LORA_DIR).glob(f"*{ext}"):
            lora_files.append(str(f))
    
    print(f"\n📊 找到 {len(lora_files)} 个 LoRA 文件")
    print("=" * 70)
    
    # 检查每个文件
    sdxl_loras = []
    sd15_loras = []
    unknown_loras = []
    
    for i, filepath in enumerate(lora_files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{i}/{len(lora_files)}] 检查: {filename}")
        
        is_sdxl, reason = is_sdxl_lora(filepath)
        
        if is_sdxl:
            print(f"   🔵 SDXL 格式: {reason}")
            sdxl_loras.append(filepath)
        else:
            print(f"   🟢 SD1.5 格式: {reason}")
            sd15_loras.append(filepath)
    
    # 显示统计
    print("\n" + "=" * 70)
    print("📊 统计结果:")
    print(f"   🟢 SD1.5 LoRA: {len(sd15_loras)} 个")
    print(f"   🔵 SDXL LoRA:  {len(sdxl_loras)} 个")
    
    if sdxl_loras:
        print("\n🔵 需要移动到 sdxl-lora 的 LoRA:")
        for l in sdxl_loras:
            print(f"   - {os.path.basename(l)}")
    
    # 询问是否移动
    if sdxl_loras:
        print("\n" + "=" * 70)
        response = input("是否将这些 SDXL LoRA 移动到正确目录? (y/n): ").strip().lower()
        
        if response == 'y':
            print("\n🔄 开始移动...")
            for src in sdxl_loras:
                move_lora(src, SDXL_LORA_DIR, dry_run=False)
            print("\n✅ 移动完成!")
            
            # 提示重新生成索引
            print("\n💡 请重新生成 LoRA 索引:")
            print("   python scripts/lora_index.py --refresh")
        else:
            print("\n⏭️ 已取消移动")
    else:
        print("\n✅ 没有发现需要移动的 SDXL LoRA")

if __name__ == "__main__":
    main()