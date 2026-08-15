#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行入口
用法: python cli.py <风格名> [-n 数量] [--model 模型名] [--lora LoRA名]
"""

import sys
import os
import io

# 修复 Windows 终端编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
import argparse
from datetime import datetime
from core.postprocessor import remove_ai_traces

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import GenerationEngine
from core.model import ModelManager
from core.lora import LoraManager
from core.prompts import PromptLoader
from core.appraiser import Appraiser  # ✅ 添加这行
from config.app import (
    config, 
    load_user_config, 
    save_user_config, 
    SD_MODEL_PATH, 
    FINAL_LORA_LIST,
    AI_APPRECIATION_ENGINE,  # ✅ 添加这行
    REMOVE_AI_TRACES,        # ✅ 添加这行
    SKETCH_KEYWORDS          # ✅ 添加这行（可选，但建议加上）
)
from core.pipeline import setup_pipeline

def parse_lora_spec(spec: str) -> tuple:
    """解析 LoRA 规格: 'name' 或 'name@0.8'"""
    if '@' in spec:
        name, weight_str = spec.rsplit('@', 1)
        try:
            weight = float(weight_str)
        except:
            weight = 1.0
        return name.strip(), weight
    return spec.strip(), 1.0


def main():
    parser = argparse.ArgumentParser(description="SD Generator")
    parser.add_argument("style", nargs="?", help="风格名称")
    parser.add_argument("-n", "--count", type=int, default=None, help="生成数量")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG")
    parser.add_argument("--width", type=int, default=512, help="宽度")
    parser.add_argument("--height", type=int, default=768, help="高度")
    parser.add_argument("--seed", type=int, default=-1, help="种子")
    
    # 模型选择
    parser.add_argument("--model", "-m", help="指定模型名称")
    parser.add_argument("--model-type", choices=["sd15", "sdxl"], help="模型类型")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用模型")
    
    # LoRA 选择
    parser.add_argument("--lora", "-l", action="append", help="LoRA (name@weight)")
    parser.add_argument("--list-loras", action="store_true", help="列出所有可用 LoRA")
    parser.add_argument("--no-lora", action="store_true", help="禁用所有 LoRA")
    
    # 风格列表
    parser.add_argument("--list-styles", action="store_true", help="列出所有可用风格")
    
    # 配置管理
    parser.add_argument("--save", action="store_true", help="保存当前选择为默认")
    parser.add_argument("--clear", action="store_true", help="清除默认配置")
    parser.add_argument("--show-config", action="store_true", help="显示当前配置")
    
    args = parser.parse_args()
    
    model_mgr = ModelManager()
    lora_mgr = LoraManager()
    
    # 加载提示词（用于 --list-styles）
    prompts = PromptLoader(config.prompts_dir)
    
    # ===== 列出所有风格 =====
    if args.list_styles:
        styles = prompts.list_styles()
        print(f"\n📚 可用风格 (共 {len(styles)} 个):")
        print("=" * 70)
        for i, name in enumerate(styles):
            style_info = prompts.get_style_info(name)
            style_type = style_info.get('type', 'flat')
            combo = style_info.get('total_combinations', 0)
            folder = style_info.get('folder', '')
            print(f"  [{i:2d}] {name:30s} [{style_type}] {combo}种组合 -> {folder}")
        return
    
    # ===== 列出模型 =====
    if args.list_models:
        models = model_mgr.list_models(args.model_type)
        default = model_mgr.get_default_model()
        print(f"\n📚 可用模型 (共 {len(models)} 个):")
        print("=" * 70)
        for i, m in enumerate(models):
            default_mark = " 👑" if m['name'] == default else ""
            tags = m.get('tags', [])
            tag_str = f" [{', '.join(tags[:3])}]" if tags else ""
            print(f"  [{i:2d}] {m['name'][:45]:45s} {m.get('size_gb', 0):.1f}GB  {m.get('type', '')}{tag_str}{default_mark}")
        print(f"\n🏆 默认推荐: {default or '无'}")
        return
    
    # ===== 列出 LoRA =====
    if args.list_loras:
        loras = lora_mgr.list(args.model_type)
        default = lora_mgr.get_default_lora()
        print(f"\n📚 可用 LoRA (共 {len(loras)} 个):")
        print("=" * 70)
        for i, l in enumerate(loras):
            default_mark = " 👑" if l['name'] == default else ""
            tags = l.get('tags', [])
            tag_str = f" [{', '.join(tags[:3])}]" if tags else ""
            print(f"  [{i:2d}] {l['name'][:45]:45s} {l.get('size_mb', 0):.1f}MB  {l.get('type', '')}{tag_str}{default_mark}")
        print(f"\n🏆 默认推荐: {default or '无'}")
        return
    
    # ===== 清除配置 =====
    if args.clear:
        save_user_config({})
        print("✅ 已清除默认配置")
        return
    
    # ===== 显示配置 =====
    if args.show_config:
        user_config = load_user_config()
        print("\n📊 当前配置:")
        print(f"  模式: smart")
        print(f"  模型: {os.path.basename(SD_MODEL_PATH) if SD_MODEL_PATH else '未设置'}")
        loras = user_config.get('default_loras', [])
        if loras:
            default_lora_str = ', '.join([f"{l['name']}@{l.get('weight', 1.0)}" for l in loras])
            print(f"  默认 LoRA: {default_lora_str}")
        else:
            print(f"  默认 LoRA: 无")
        return
    
    # ===== 需要指定风格 =====
    if not args.style:
        parser.print_help()
        print("\n❌ 请指定风格名称")
        print("   提示: 使用 --list-styles 查看所有可用风格")
        return
    
    # ===== 1. 加载提示词 =====
    print("📝 加载提示词...")
    style = prompts.get_style(args.style)
    if not style:
        print(f"❌ 未找到风格: {args.style}")
        print(f"   可用: {', '.join(prompts.list_styles()[:10])}")
        return
    
    # 显示风格信息
    style_info = prompts.get_style_info(args.style)
    print(f"📋 风格: {args.style}")
    print(f"📁 分类: {style_info.get('folder', '未分类')}")
    print(f"📊 类型: {style_info.get('type', 'flat')}")
    print(f"📝 组合数: {style_info.get('total_combinations', 0)}")
    if style_info.get('type') == 'hierarchical':
        print(f"   ├─ 主体: {style_info.get('subjects', 0)} 种")
        print(f"   ├─ 风格: {style_info.get('styles', 0)} 种")
        print(f"   └─ 情绪: {style_info.get('moods', 0)} 种")
        if style_info.get('has_content_texts'):
            print(f"   └─ 内容文本: 有")
    
    # ===== 确定生成数量 =====
    total_combinations = style_info.get('total_combinations', 1)
    if args.count is None:
        if style_info.get('type') == 'hierarchical':
            total_count = min(total_combinations, 20)  # ← 这里定义了 total_count
            print(f"📊 分层模式：将生成 {total_count} 张（全部组合）")
        else:
            total_count = style_info.get('subjects', 1)  # ← 这里也定义了
            print(f"📊 扁平模式：将生成 {total_count} 张（全部提示词）")
    else:
        total_count = args.count  # ← 这里也定义了
        if total_count > total_combinations:
            print(f"⚠️ 指定数量 {total_count} 超过组合数 {total_combinations}，实际生成 {total_combinations}")
            total_count = total_combinations
    
    # ===== 2. 加载模型 =====
    if args.model:
        if not model_mgr.load(args.model, args.model_type):
            return
    else:
        # 改为：
        pipe = setup_pipeline()
        model_mgr.pipeline = pipe
        model_mgr.current = os.path.basename(SD_MODEL_PATH)
        model_mgr.model_type = pipe.__class__.__name__.lower().replace('pipeline', '').replace('stablefusion', '').replace('x', 'xl')

    # ===== 3. 加载 LoRA =====
    # LoRA 由 pipeline.py 在加载模型时自动加载
    print(f"🔗 使用配置 LoRA（已在模型加载时自动加载）")
    
    # ===== 4. 生成 =====
    print(f"\n🎨 开始生成 {total_count} 张...")
    engine = GenerationEngine(model_mgr.get_pipeline())
    os.makedirs(config.output_dir, exist_ok=True)

    # 初始化鉴赏器
    appraiser = None
    if AI_APPRECIATION_ENGINE != "prompt":
        try:
            appraiser = Appraiser()
            print(f"📝 AI 鉴赏引擎: {AI_APPRECIATION_ENGINE}")
        except Exception as e:
            print(f"⚠️ AI 鉴赏初始化失败: {e}")

    # ✅ 收集数据
    generated_files = []
    appraisals = []
    prompts_used = []

    for i in range(total_count):
        prompt = prompts.get_prompt(args.style, i)
        if not prompt:
            print(f"❌ 提示词不足（只有 {total_combinations} 个组合）")
            break
        
        print(f"\n🎨 [{i+1}/{total_count}]")
        print(f"   📝 {prompt[:80]}...")
        prompts_used.append(prompt)
        
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
            generated_files.append(filepath)
            
            # ===== 后处理 =====
            final_path = filepath
            if REMOVE_AI_TRACES:
                from core.postprocessor import remove_ai_traces, is_sketch_style
                is_sketch = is_sketch_style(args.style) or is_sketch_style(prompt)
                final_path = remove_ai_traces(filepath, is_sketch=is_sketch)
                if final_path != filepath:
                    print(f"   ✅ 后处理完成: {os.path.basename(final_path)}")
                    # ✅ 更新为最终的 JPG 路径
                    generated_files[-1] = final_path
            
            # ===== AI 鉴赏 =====
            if appraiser:
                try:
                    caption = appraiser.appraise(final_path, prompt)
                    txt_file = final_path.replace('.png', '.jpg').replace('.jpg', '.txt')
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(f"【风格】: {args.style}\n")
                        f.write(f"【提示词】: {prompt}\n")
                        f.write(f"{'='*50}\n")
                        f.write(f"【AI 鉴赏】:\n{caption}\n")
                    print(f"   📝 AI 鉴赏已保存: {os.path.basename(txt_file)}")
                    appraisals.append(caption)
                except Exception as e:
                    print(f"   ⚠️ AI 鉴赏失败: {e}")
                    appraisals.append("（AI 鉴赏生成失败）")
            
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()

    # ==================== ✅ 生成 Word 文档 ====================
    if appraisals and generated_files:
        try:
            from utils.doc_generator import generate_word_doc, generate_text_summary
            
            print(f"\n📄 正在生成 Word 文档...")
            
            # 获取实际输出目录（可能包含子文件夹）
            output_dir = os.path.dirname(generated_files[0])
            
            # 生成 Word 文档
            doc_success = generate_word_doc(output_dir, args.style, appraisals)
            
            # 生成文本摘要
            txt_success = generate_text_summary(output_dir, args.style, appraisals)
            
            if doc_success:
                print(f"   ✅ Word 文档已生成: {os.path.join(output_dir, '公众号草稿.docx')}")
            if txt_success:
                print(f"   ✅ 文本摘要已生成: {os.path.join(output_dir, '点评.txt')}")
                
        except ImportError:
            print(f"⚠️ 未安装 python-docx，跳过 Word 文档生成")
            print(f"💡 安装: pip install python-docx")
        except Exception as e:
            print(f"⚠️ Word 文档生成失败: {e}")

    print(f"\n✅ 完成，共 {total_count} 张")
    print(f"📁 输出目录: {config.output_dir}")


if __name__ == "__main__":
    main()