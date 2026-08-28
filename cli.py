#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行入口
用法: python cli.py <风格名> [-n 数量] [--model 模型名] [--lora LoRA名]
"""

import sys
import os

# ✅ 修复：路径不要有空格
os.environ["HF_HOME"] = r"E:\hf_cache\.cache"
os.environ["TRANSFORMERS_CACHE"] = r"E:\hf_cache\.cache\hub"
os.environ["HF_HUB_CACHE"] = r"E:\hf_cache\.cache\hub"
os.environ["HUGGINGFACE_HUB_CACHE"] = r"E:\hf_cache\.cache\hub"

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
from core.appraiser import Appraiser
from config.app import (
    config, 
    load_user_config, 
    save_user_config, 
    SD_MODEL_PATH, 
    FINAL_LORA_LIST,
    AI_APPRECIATION_ENGINE,
    REMOVE_AI_TRACES,
    SKETCH_KEYWORDS,
    OLLAMA_MODEL, 
    # API 配置
    IMAGE_API_PROVIDER,
    TONGYI_API_KEY,
    TONGYI_MODEL,
    YIGE_API_KEY,
    YIGE_SECRET_KEY,
    HUNYUAN_SECRET_ID,
    HUNYUAN_SECRET_KEY,
    HF_API_TOKEN,
    HF_MODEL,
)
from core.pipeline import setup_pipeline

# ✅ 添加 API 引擎导入
from core.api_engines import create_api_engine


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

    # ✅ 在函数内导入 ModelManager 和 LoraManager
    from core.model import ModelManager
    from core.lora import LoraManager
    
    parser = argparse.ArgumentParser(description="SD Generator")
    parser.add_argument("style", nargs="?", help="风格名称")
    parser.add_argument("-n", "--count", type=int, default=None, help="生成数量")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG")
    parser.add_argument("--width", type=int, default=512, help="宽度")
    parser.add_argument("--height", type=int, default=768, help="高度")
    parser.add_argument("--seed", type=int, default=-1, help="种子")

    # 动态提示词专用参数    
    parser.add_argument("--prompt", type=str, help="动态提示词模式：直接指定画面描述")
    parser.add_argument("--style-hint", choices=["general", "anime", "realistic", "sketch", "mecha"], 
                        default="general", help="动态提示词风格提示")

                        
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
    
    # ✅ 添加 API 相关参数
    parser.add_argument("--api", choices=["tongyi", "yige", "hunyuan", "huggingface"], 
                        help="使用 API 生成图片 (覆盖配置)")
    parser.add_argument("--list-apis", action="store_true", help="列出可用的 API 提供商")

                    
                    
    # ===== 👕 去衣服功能 =====
    parser.add_argument("--remove-clothes", action="store_true", 
                        help="去除图片中的衣服（保留姿态和脸部）")
    parser.add_argument("--clothes-method", choices=["integrated", "script"], default="integrated",
                        help="去衣服方式: integrated=集成模块(默认), script=独立脚本")
    parser.add_argument("--clothes-strength", type=float, default=0.7,
                        help="去衣服强度 (0.3-1.0, 仅集成模式有效)")
                        
    args = parser.parse_args()
    
    # ✅ 列出可用 API
    if args.list_apis:
        print("\n📚 可用的 API 提供商:")
        print("=" * 50)
        print("  tongyi      通义万相（阿里云）")
        print("  yige        文心一格（百度）")
        print("  hunyuan     腾讯混元")
        print("  huggingface HuggingFace Inference API")
        print("\n💡 使用 --api <名称> 切换到指定 API")
        print("   或在 config/app.py 中设置 IMAGE_API_PROVIDER")
        return
    
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
        print(f"  图像生成: {args.api or IMAGE_API_PROVIDER}")
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
    
    # ===== 确定使用的 API 提供商 =====
    api_provider = args.api or IMAGE_API_PROVIDER
    use_api = api_provider != "local"
    
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
            total_count = min(total_combinations, 20)
            print(f"📊 分层模式：将生成 {total_count} 张（全部组合）")
        else:
            total_count = style_info.get('subjects', 1)
            print(f"📊 扁平模式：将生成 {total_count} 张（全部提示词）")
    else:
        total_count = args.count
        if total_count > total_combinations:
            print(f"⚠️ 指定数量 {total_count} 超过组合数 {total_combinations}，实际生成 {total_combinations}")
            total_count = total_combinations
    
    # ===== 2. 创建生成引擎 =====
    engine = None
    api_engine = None
    
    if use_api:
        # ✅ 使用 API 引擎
        print(f"🌐 使用 API 图像生成: {api_provider}")
        
        # 构建 API 配置
        api_config = {
            "TONGYI_API_KEY": TONGYI_API_KEY,
            "TONGYI_MODEL": TONGYI_MODEL,
            "YIGE_API_KEY": YIGE_API_KEY,
            "YIGE_SECRET_KEY": YIGE_SECRET_KEY,
            "HUNYUAN_SECRET_ID": HUNYUAN_SECRET_ID,
            "HUNYUAN_SECRET_KEY": HUNYUAN_SECRET_KEY,
            "HF_API_TOKEN": HF_API_TOKEN,
            "HF_MODEL": HF_MODEL,
        }
        
        # 检查 API Key
        if api_provider == "tongyi" and not TONGYI_API_KEY:
            print(f"❌ 请设置 TONGYI_API_KEY")
            return
        if api_provider == "yige" and not (YIGE_API_KEY and YIGE_SECRET_KEY):
            print(f"❌ 请设置 YIGE_API_KEY 和 YIGE_SECRET_KEY")
            return
        if api_provider == "hunyuan" and not (HUNYUAN_SECRET_ID and HUNYUAN_SECRET_KEY):
            print(f"❌ 请设置 HUNYUAN_SECRET_ID 和 HUNYUAN_SECRET_KEY")
            return
        if api_provider == "huggingface" and not HF_API_TOKEN:
            print(f"❌ 请设置 HF_API_TOKEN")
            return
        
        try:
            api_engine = create_api_engine(api_provider, api_config)
            print(f"✅ API 引擎初始化成功: {api_provider}")
        except Exception as e:
            print(f"❌ API 引擎初始化失败: {e}")
            return
    
    else:
        # ✅ 使用本地 SD 引擎
        print(f"🖥️ 使用本地 SD 图像生成")
        
        if args.model:
            if not model_mgr.load(args.model, args.model_type):
                return
        else:
            pipe = setup_pipeline()
            model_mgr.pipeline = pipe
            model_mgr.current = os.path.basename(SD_MODEL_PATH)
            model_mgr.model_type = pipe.__class__.__name__.lower().replace('pipeline', '').replace('stablefusion', '').replace('x', 'xl')
        
        # ===== LoRA 状态 =====
        if args.no_lora:
            print(f"🔗 LoRA 已禁用（--no-lora）")
        else:
            if FINAL_LORA_LIST:
                print(f"🔗 已配置 {len(FINAL_LORA_LIST)} 个 LoRA（已在模型加载时自动加载）")
            else:
                print(f"🔗 未配置 LoRA")
        
        engine = GenerationEngine(model_mgr.get_pipeline())
    
    # ===== 3. 生成 =====
    print(f"\n🎨 开始生成 {total_count} 张...")
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

    # ============================================================
    # ✅ 动态 OLLAMA 提示词生成（循环外，只执行一次）
    # ============================================================
    dynamic_prompt_text = None  # 用于存储动态生成的提示词

    if args.style == "dynamic_prompt":
        import requests
        
        # ============================================================
        # 🚀 非交互模式：直接使用 --prompt 参数
        # ============================================================
        if args.prompt:
            print(f"\n🤖 非交互模式：动态生成提示词")
            print(f"   📝 描述: {args.prompt}")
            print(f"   🎨 风格: {args.style_hint}")
            
            # 检查 Ollama 是否可用
            ollama_available = False
            try:
                resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
                ollama_available = resp.status_code == 200
            except:
                pass
            
            if not ollama_available:
                print("\n⚠️ 无法连接到 Ollama 服务")
                print("💡 请确保 Ollama 正在运行: ollama serve")
                return
            
            print(f"\n⏳ 正在用 '{OLLAMA_MODEL}' 生成提示词...")
            dynamic_prompt_text = prompts.generate_prompt_with_ollama(
                args.prompt,
                style_hint=args.style_hint,
                retry=2
            )
            
            print(f"\n✅ 生成的提示词:")
            print(f"   ─────────────────────────────────────────────")
            print(f"   {dynamic_prompt_text}")
            print(f"   ─────────────────────────────────────────────")
            
            # 动态模式默认生成 1 张
            if args.count is None:
                total_count = 1
                print("   📌 动态模式默认生成 1 张")
            else:
                total_count = min(args.count, 1)
                if args.count > 1:
                    print(f"   📌 动态模式最多生成 1 张，已从 {args.count} 调整为 1")
            
            # 跳过交互，直接进入生成循环
            # 使用标志跳过后续的交互代码
            skip_interactive = True
        else:
            skip_interactive = False
        
        # ============================================================
        # 🎯 交互模式（仅在未提供 --prompt 时执行）
        # ============================================================
        if not skip_interactive:
            # 检查 Ollama 是否可用
            ollama_available = False
            try:
                resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
                ollama_available = resp.status_code == 200
            except:
                pass
            
            if not ollama_available:
                print("\n⚠️ 无法连接到 Ollama 服务")
                print("💡 请确保 Ollama 正在运行: ollama serve")
                print("💡 或使用已有风格: python cli.py --list-styles")
                return
            
            print("\n" + "=" * 55)
            print("   🤖 Ollama 动态提示词生成模式")
            print("=" * 55)
            print("\n💡 风格提示:")
            style_options = {
                "general": "通用 - 适合大多数场景",
                "anime": "动漫 - 日系插画风格",
                "realistic": "写实 - 摄影风格",
                "sketch": "素描 - 线稿/白描风格",
                "mecha": "机甲 - 科幻机械风格"
            }
            for key, desc in style_options.items():
                print(f"   [{key:9s}] {desc}")
            print("=" * 55)
            
            # 选择风格
            while True:
                style_hint = input("\n请选择风格提示 (回车默认 general): ").strip().lower() or "general"
                if style_hint in style_options:
                    break
                print(f"   ⚠️ 无效选项，请选择: {', '.join(style_options.keys())}")
            
            # 获取可用 Ollama 模型列表
            try:
                resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
                if resp.status_code == 200:
                    installed_models = [m["name"] for m in resp.json().get("models", [])]
                else:
                    installed_models = []
            except:
                installed_models = []
            
            # 选择模型
            if installed_models:
                print(f"\n📦 已安装: {', '.join(installed_models)}")
                default_model = OLLAMA_MODEL if OLLAMA_MODEL in installed_models else installed_models[0]
                model_input = input(f"使用哪个模型 (回车默认 {default_model}): ").strip()
                model = model_input or default_model
                if model not in installed_models:
                    print(f"   ⚠️ 切换至可用模型: {default_model}")
                    model = default_model
            else:
                print(f"\n⚠️ 未检测到已安装的模型，使用默认: {OLLAMA_MODEL}")
                print(f"   💡 安装: ollama pull qwen2.5:1.5b")
                model = OLLAMA_MODEL
            
            # 输入描述
            print("\n💬 请输入画面描述 (支持中英文):")
            user_desc = input("> ").strip()
            if not user_desc:
                print("❌ 描述不能为空")
                return
            
            # 生成提示词
            print(f"\n⏳ 正在用 '{model}' 生成提示词...")
            dynamic_prompt_text = prompts.generate_prompt_with_ollama(
                user_desc,
                model=model,
                style_hint=style_hint,
                retry=2
            )
            
            print(f"\n✅ 生成的提示词:")
            print(f"   ─────────────────────────────────────────────")
            print(f"   {dynamic_prompt_text}")
            print(f"   ─────────────────────────────────────────────")
            
            # 确认生成
            confirm = input("\n是否使用此提示词生成? (y=生成 / n=重新描述 / q=取消): ").strip().lower()
            if confirm == 'q':
                print("已取消生成")
                return
            elif confirm == 'n':
                print("请重新运行: python cli.py dynamic_prompt")
                return
            else:
                print("\n✅ 开始生成...")
            
            # 动态模式默认生成 1 张
            if args.count is None:
                total_count = 1
                print("   📌 动态模式默认生成 1 张")
            else:
                total_count = min(args.count, 1)
                if args.count > 1:
                    print(f"   📌 动态模式最多生成 1 张，已从 {args.count} 调整为 1")
    # ============================================================
    # ✅ 生成循环
    # ============================================================
    for i in range(total_count):
        # 获取提示词
        if args.style == "dynamic_prompt" and dynamic_prompt_text:
            # 使用动态生成的提示词（所有图片共用同一个）
            prompt = dynamic_prompt_text
            # 如果生成多张，可以略微变化（如添加不同的质量词）
            if total_count > 1:
                variations = ["", "high quality", "detailed", "intricate"]
                if i > 0 and i < len(variations):
                    prompt = f"{dynamic_prompt_text}, {variations[i]}"
        else:
            # 普通风格：从提示词库获取
            prompt = prompts.get_prompt(args.style, i)
        
        if not prompt:
            print(f"❌ 提示词不足（只有 {total_combinations} 个组合）")
            break
        
        print(f"\n🎨 [{i+1}/{total_count}]")
        print(f"   📝 {prompt[:80]}...")
        prompts_used.append(prompt)
        
        try:
            # ✅ 根据引擎类型生成图片
            if use_api:
                # 使用 API 引擎
                image = api_engine.generate_single(
                    prompt=prompt,
                    negative=config.default_negative,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    seed=args.seed if args.seed != -1 else None,
                )
            else:
                # 使用本地引擎
                image = engine.generate_single(
                    prompt=prompt,
                    negative=config.default_negative,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
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

    # ==================== 👕 去衣服处理 ====================
    if args.remove_clothes and generated_files:
        clothes_removed_files = []
        method_used = None
        
        # ===== 方式1: 优先尝试独立脚本 =====
        script_path = os.path.join(os.path.dirname(__file__), "scripts", "remove_clothes.py")
        
        if os.path.exists(script_path):
            print(f"\n👕 尝试脚本模式...")
            script_success = True
            
            for idx, filepath in enumerate(generated_files):
                print(f"\n   [{idx+1}/{len(generated_files)}] 处理: {os.path.basename(filepath)}")
                try:
                    base, ext = os.path.splitext(filepath)
                    output_path = f"{base}_nude{ext}"
                    
                    result = subprocess.run([
                        sys.executable, script_path,
                        filepath,
                        "-o", output_path,
                        "--method", "auto"
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        clothes_removed_files.append(output_path)
                        print(f"   ✅ 完成: {os.path.basename(output_path)}")
                    else:
                        print(f"   ❌ 脚本失败: {result.stderr}")
                        script_success = False
                        clothes_removed_files.append(filepath)
                        break  # 失败则跳出，尝试集成模式
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ 超时")
                    script_success = False
                    clothes_removed_files.append(filepath)
                    break
                except Exception as e:
                    print(f"   ❌ 错误: {e}")
                    script_success = False
                    clothes_removed_files.append(filepath)
                    break
            
            if script_success and len(clothes_removed_files) == len(generated_files):
                generated_files = clothes_removed_files
                method_used = "脚本模式"
                print(f"\n✅ 去衣服完成 (脚本模式)，共 {len(generated_files)} 张")
        
        # ===== 方式2: 脚本失败或不存在，回退到集成模式 =====
        if method_used is None:
            print(f"\n👕 脚本模式不可用，回退到集成模式...")
            try:
                from core.clothes_remover import ClothesRemover
                remover = ClothesRemover()
                
                # 如果之前脚本部分失败了，clothes_removed_files 可能部分有值
                # 重新从 generated_files 开始
                if len(clothes_removed_files) != len(generated_files):
                    clothes_removed_files = []
                
                start_idx = len(clothes_removed_files)
                if start_idx > 0:
                    print(f"   📌 从第 {start_idx + 1} 张继续...")
                
                for idx, filepath in enumerate(generated_files[start_idx:], start=start_idx):
                    print(f"\n   [{idx+1}/{len(generated_files)}] 处理: {os.path.basename(filepath)}")
                    try:
                        output = remover.remove_clothes(
                            filepath,
                            strength=args.clothes_strength if hasattr(args, 'clothes_strength') else 0.7,
                            steps=20
                        )
                        clothes_removed_files.append(output)
                    except Exception as e:
                        print(f"   ❌ 失败: {e}")
                        clothes_removed_files.append(filepath)  # 保留原图
                
                generated_files = clothes_removed_files
                method_used = "集成模式"
                print(f"\n✅ 去衣服完成 (集成模式)，共 {len(generated_files)} 张")
                
            except ImportError as e:
                print(f"⚠️ 集成模式缺少依赖: {e}")
                print(f"💡 安装: pip install ultralytics opencv-python")
            except Exception as e:
                print(f"⚠️ 集成模式失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果两种模式都失败了，至少保留原图
        if method_used is None:
            print(f"⚠️ 去衣服失败，保留原图")
            
    # ==================== ✅ 生成 Word 文档 ====================
    if appraisals and generated_files:
        try:
            from utils.doc_generator import generate_word_doc, generate_text_summary
            
            print(f"\n📄 正在生成 Word 文档...")
            
            output_dir = os.path.dirname(generated_files[0])
            
            doc_success = generate_word_doc(output_dir, args.style, appraisals)
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
    if use_api:
        print(f"🌐 API 提供商: {api_provider}")


if __name__ == "__main__":
    main()
