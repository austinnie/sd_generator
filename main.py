#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SD Generator - 简洁版
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import GenerationEngine
from core.model import ModelManager
from core.prompts import PromptLoader
from core.lora import LoraManager
from config.app import config


def main():
    print("=" * 50)
    print("🎨 SD Generator")
    print("=" * 50)
    print(f"📂 模型目录: {config.model_dir}")
    print(f"📂 输出目录: {config.output_dir}")
    print()
    
    # 1. 加载模型
    model_mgr = ModelManager(config.model_dir)
    models = model_mgr.list_models()
    if not models:
        print("❌ 未找到模型，请将模型放到:", config.model_dir)
        return
    
    print(f"📦 加载模型: {models[0]}")
    if not model_mgr.load(models[0]):
        print("❌ 加载失败")
        return
    
    # 2. 加载提示词
    prompts = PromptLoader(config.prompts_dir)
    styles = prompts.list_styles()
    print(f"📝 已加载 {len(styles)} 个风格")
    
    # 3. 交互式生成
    print("\n💡 输入风格名称生成图片，输入 q 退出")
    while True:
        style_name = input("\n风格: ").strip()
        if style_name.lower() == 'q':
            break
        
        style = prompts.get_style(style_name)
        if not style:
            print(f"❌ 未找到: {style_name}")
            print(f"   可用: {', '.join(styles[:5])}...")
            continue
        
        prompt = prompts.get_random_prompt(style_name)
        if not prompt:
            print("❌ 该风格没有提示词")
            continue
        
        print(f"🎨 生成: {prompt[:50]}...")
        
        engine = GenerationEngine(model_mgr.get_pipeline())
        image = engine.generate_single(prompt)
        
        # 保存
        from datetime import datetime
        filename = f"{style_name}_{datetime.now():%Y%m%d_%H%M%S}.png"
        filepath = os.path.join(config.output_dir, filename)
        os.makedirs(config.output_dir, exist_ok=True)
        image.save(filepath)
        print(f"✅ 已保存: {filepath}")
    
    print("👋 再见!")


if __name__ == "__main__":
    main()
