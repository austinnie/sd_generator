#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import GenerationEngine
from core.model import ModelManager
from core.lora import LoraManager
from core.prompts import PromptLoader
from config.app import (
    SD_MODEL_PATH, FINAL_LORA_LIST, OUTPUT_DIR, PROMPTS_DIR,
    STEPS, MODEL_SELECTION_MODE
)


def parse_lora_spec(spec: str) -> tuple:
    if '@' in spec:
        name, weight_str = spec.rsplit('@', 1)
        try: weight = float(weight_str)
        except: weight = 1.0
        return name.strip(), weight
    return spec.strip(), 1.0


def main():
    parser = argparse.ArgumentParser(description="SD Generator")
    parser.add_argument("style", nargs="?", help="风格名称")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--steps", type=int, default=STEPS, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG")
    parser.add_argument("--width", type=int, default=512, help="宽度")
    parser.add_argument("--height", type=int, default=768, help="高度")
    parser.add_argument("--seed", type=int, default=-1, help="种子")
    
    parser.add_argument("--model", "-m", help="指定模型名称")
    parser.add_argument("--model-type", choices=["sd15", "sdxl"], help="模型类型")
    parser.add_argument("--list-models", action="store_true", help="列出所有模型")
    
    parser.add_argument("--lora", "-l", action="append", help="LoRA (name@weight)")
    parser.add_argument("--list-loras", action="store_true", help="列出所有 LoRA")
    parser.add_argument("--no-lora", action="store_true", help="禁用所有 LoRA")
    
    parser.add_argument("--show-config", action="store_true", help="显示当前配置")
    
    args = parser.parse_args()
    
    model_mgr = ModelManager()
    lora_mgr = LoraManager()
    
    if args.list_models:
        models = model_mgr.list_models(args.model_type)
        print(f"\n📚 可用模型 (共 {len(models)} 个):")
        for i, m in enumerate(models):
            default = " 👑" if m['name'] == model_mgr.get_default_model() else ""
            print(f"  [{i:2d}] {m['name'][:45]} {m.get('size_gb', 0):.1f}GB{m.get('type', '')}{default}")
        return
    
    if args.list_loras:
        loras = lora_mgr.list(args.model_type)
        print(f"\n📚 可用 LoRA (共 {len(loras)} 个):")
        for i, l in enumerate(loras):
            default = " 👑" if l['name'] == lora_mgr.get_default_lora() else ""
            print(f"  [{i:2d}] {l['name'][:45]} {l.get('size_mb', 0):.1f}MB{l.get('type', '')}{default}")
        return
    
    if args.show_config:
        print(f"\n📊 当前配置:")
        print(f"  模式: {MODEL_SELECTION_MODE}")
        print(f"  模型: {os.path.basename(SD_MODEL_PATH) if SD_MODEL_PATH else '未设置'}")
        if FINAL_LORA_LIST:
            print(f"  LoRA: {len(FINAL_LORA_LIST)} 个")
            for l in FINAL_LORA_LIST:
                print(f"    - {os.path.basename(l['path'])} (权重: {l.get('weight', 1.0)})")
        else:
            print(f"  LoRA: 无")
        return
    
    if not args.style:
        parser.print_help()
        return
    
    # 加载提示词
    prompts = PromptLoader(PROMPTS_DIR)
    style = prompts.get_style(args.style)
    if not style:
        print(f"❌ 未找到风格: {args.style}")
        return
    
    # 加载模型
    if args.model:
        if not model_mgr.load(args.model, args.model_type):
            return
    else:
        # 使用 config 中的默认模型路径
        if SD_MODEL_PATH and os.path.exists(SD_MODEL_PATH):
            if not model_mgr._load_from_path(SD_MODEL_PATH):
                return
        else:
            models = model_mgr.list_models(args.model_type)
            if not models:
                print("❌ 未找到任何模型")
                return
            if not model_mgr.load(models[0]['name']):
                return
    
    # 加载 LoRA
    lora_specs = []
    if args.no_lora:
        print("🔗 LoRA 已禁用")
    elif args.lora:
        for spec in args.lora:
            name, weight = parse_lora_spec(spec)
            lora_specs.append((name, weight))
    elif FINAL_LORA_LIST and not args.no_lora:
        # 使用 config 中的默认 LoRA
        print(f"🔗 使用默认 LoRA: {len(FINAL_LORA_LIST)} 个")
        for lora in FINAL_LORA_LIST:
            lora_name = os.path.basename(lora['path'])
            lora_specs.append((lora_name, lora.get('weight', 1.0)))
    
    for name, weight in lora_specs:
        if lora_mgr.load_by_name(model_mgr.get_pipeline(), name, weight,
                                 model_mgr.get_model_type()):
            print(f"🔗 加载 LoRA: {name} (权重: {weight})")
    
    # 生成
    engine = GenerationEngine(model_mgr.get_pipeline())
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for i in range(args.count):
        prompt = prompts.get_prompt(args.style, i)
        if not prompt:
            break
        print(f"\n🎨 [{i+1}/{args.count}] {prompt[:60]}...")
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
            filepath = os.path.join(OUTPUT_DIR, filename)
            image.save(filepath)
            print(f"   ✅ {filepath}")
        except Exception as e:
            print(f"   ❌ {e}")
    
    print(f"\n✅ 完成")


if __name__ == "__main__":
    main()