#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行入口
用法: python cli.py <风格名> [-n 数量]
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import GenerationEngine
from core.model import ModelManager
from core.prompts import PromptLoader
from config.app import config


def main():
    parser = argparse.ArgumentParser(description="SD Generator")
    parser.add_argument("--model-type", choices=["sd15", "sdxl"], help="模型类型")
    parser.add_argument("style", help="风格名称")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG")
    parser.add_argument("--width", type=int, default=512, help="宽度")
    parser.add_argument("--height", type=int, default=768, help="高度")
    parser.add_argument("--seed", type=int, default=-1, help="种子")
    args = parser.parse_args()
    
    # 1. 加载提示词
    print("📝 加载提示词...")
    prompts = PromptLoader(config.prompts_dir)
    style = prompts.get_style(args.style)
    if not style:
        print(f"❌ 未找到风格: {args.style}")
        print(f"   可用: {', '.join(prompts.list_styles()[:10])}")
        return
    
    print(f"📋 风格: {args.style}")
    print(f"📝 提示词数: {len(style.get('subjects', []))}")
    
    # 2. 加载模型
    print(f"📦 模型目录: {config.model_dir}")
    model_mgr = ModelManager(config.model_dir)
    models = model_mgr.list_models()
    if args.model_type:
        models = [m for m in models if m["type"] == args.model_type]
        
    if not models:
        print(f"❌ 未找到模型文件")
        print(f"   请将模型放到: {model_mgr.model_dir}")
        return
    
    print(f"📦 可用模型: {len(models)} 个")
    for m in models[:3]:
        print(f"   - {m}")
    
    # 加载第一个模型
    if not model_mgr.load(models[0]):
        print("❌ 模型加载失败，退出")
        return
    
    # 3. 生成
    print(f"🎨 开始生成 {args.count} 张...")
    engine = GenerationEngine(model_mgr.get_pipeline())
    os.makedirs(config.output_dir, exist_ok=True)
    
    for i in range(args.count):
        prompt = prompts.get_prompt(args.style, i)
        if not prompt:
            print(f"❌ 提示词不足（只有 {len(style.get('subjects', []))} 个）")
            break
        
        print(f"\n🎨 [{i+1}/{args.count}]")
        print(f"   📝 {prompt[:60]}...")
        
        try:
            image = engine.generate_single(
                prompt=prompt,
                steps=args.steps,
                cfg=args.cfg,
                width=args.width,
                height=args.height,
                seed=args.seed if args.seed != -1 else None,
            )
            
            filename = f"{args.style}_{datetime.now():%Y%m%d_%H%M%S}_{i+1}.png"
            filepath = os.path.join(config.output_dir, filename)
            image.save(filepath)
            print(f"   ✅ {filepath}")
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ 完成，共 {args.count} 张")
    print(f"📁 输出目录: {config.output_dir}")


if __name__ == "__main__":
    main()