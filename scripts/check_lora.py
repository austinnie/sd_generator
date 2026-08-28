# scripts/check_lora.py
"""检查 LoRA 文件格式"""

import os
import sys
import json
import argparse
from safetensors import safe_open

def check_lora_format(filepath: str):
    """检查 LoRA 文件的内部结构"""
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return
    
    print(f"\n📁 检查文件: {os.path.basename(filepath)}")
    print("=" * 60)
    
    # 1. 检查文件大小
    size_mb = os.path.getsize(filepath) / (1024**2)
    print(f"📊 文件大小: {size_mb:.2f} MB")
    
    # 2. 检查是否为 safetensors 格式
    try:
        with safe_open(filepath, framework="pt") as f:
            keys = f.keys()
            print(f"✅ 格式: safetensors")
            print(f"📋 包含 {len(keys)} 个张量")
            
            # 显示前 20 个键名
            print(f"\n🔑 前 20 个键名:")
            for i, key in enumerate(list(keys)[:20]):
                tensor = f.get_tensor(key)
                print(f"   {i+1:2d}. {key[:60]:60s} shape: {list(tensor.shape)}")
            
            # 检查关键特征
            print(f"\n🔍 关键特征检测:")
            
            # 检查是否有 PEFT 元数据
            has_peft = any('peft' in key.lower() for key in keys)
            print(f"   PEFT 元数据: {'✅ 有 (新版格式)' if has_peft else '❌ 无 (旧版格式)'}")
            
            # 检查是否有 lora_A/lora_B（标准 LoRA）
            has_lora_a = any('lora_a' in key.lower() for key in keys)
            has_lora_b = any('lora_b' in key.lower() for key in keys)
            print(f"   lora_A 权重: {'✅' if has_lora_a else '❌'}")
            print(f"   lora_B 权重: {'✅' if has_lora_b else '❌'}")
            
            # 检查是否有 alpha 值
            has_alpha = any('alpha' in key.lower() for key in keys)
            print(f"   alpha 值: {'✅' if has_alpha else '❌'}")
            
            # 判断格式类型
            if has_peft:
                print(f"\n📌 判断: 新版 PEFT 格式 (diffusers >= 0.27.0)")
            elif has_lora_a and has_lora_b:
                print(f"\n📌 判断: 标准 LoRA 格式 (旧版，但兼容)")
            else:
                print(f"\n📌 判断: 未知格式或损坏的文件")
                
            # 显示文件元数据（如果有）
            if hasattr(f, 'metadata') and f.metadata():
                print(f"\n📝 文件元数据:")
                for k, v in f.metadata().items():
                    print(f"   {k}: {v[:100] if len(v) > 100 else v}")
                    
    except Exception as e:
        print(f"❌ 无法读取 safetensors: {e}")
        
        # 尝试作为普通文件读取
        try:
            with open(filepath, 'rb') as f:
                header = f.read(100)
                print(f"\n📄 文件头 (hex): {header[:50].hex()}")
        except:
            pass

def check_multiple_loras(directory: str, limit: int = 5):
    """检查目录下的多个 LoRA 文件"""
    
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return
    
    files = []
    for ext in ['.safetensors', '.ckpt', '.pt']:
        for f in os.listdir(directory):
            if f.endswith(ext):
                files.append(os.path.join(directory, f))
    
    files = files[:limit]  # 只检查前几个
    
    if not files:
        print(f"❌ 在 {directory} 中没有找到 LoRA 文件")
        return
    
    print(f"\n📁 检查目录: {directory}")
    print(f"📊 找到 {len(files)} 个文件，将检查前 {len(files)} 个")
    print("=" * 60)
    
    for filepath in files:
        check_lora_format(filepath)
        print("\n" + "-" * 60)

def main():
    parser = argparse.ArgumentParser(description="检查 LoRA 文件格式")
    parser.add_argument("path", help="LoRA 文件路径或目录")
    parser.add_argument("--batch", action="store_true", help="批量检查目录")
    parser.add_argument("--limit", type=int, default=5, help="批量检查时限制文件数量")
    
    args = parser.parse_args()
    
    if args.batch or os.path.isdir(args.path):
        check_multiple_loras(args.path, args.limit)
    else:
        check_lora_format(args.path)

if __name__ == "__main__":
    main()