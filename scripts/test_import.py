# scripts/test_import.py
# 放在 scripts/ 目录内

import sys
import os

# 添加当前目录到 Python 路径（用于找 model_index.py）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# 添加 tools 目录到 Python 路径（用于找 config.py）
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # v8_universal_generator/
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

print(f"📁 当前目录: {CURRENT_DIR}")
print(f"📁 tools 目录: {TOOLS_DIR}")
print("=" * 60)

try:
    from config import (
        SD_MODEL_PATH, 
        AVAILABLE_MODELS, 
        MODEL_SELECTION_MODE,
        AVAILABLE_LORAS,
        FINAL_LORA_LIST,
        LORA_ACTIVE_INDICES,
        USE_OPENVINO_MODEL,
        LORA_INDEX,  # ← 添加这个导入
        MODEL_INDEX  # ← 可选，用于模型默认推荐
    )
    
    print("✅ 成功导入 config.py")
    print("=" * 60)
    
    # ==================== 模型信息 ====================
    print(f"\n📦 SD 模型信息:")
    print(f"  选择模式: {MODEL_SELECTION_MODE}")
    print(f"  模型路径: {SD_MODEL_PATH}")
    print(f"  模型名称: {os.path.basename(SD_MODEL_PATH)}")
    print(f"  OpenVINO: {USE_OPENVINO_MODEL}")
    print(f"  可用模型总数: {len(AVAILABLE_MODELS)} 个")
    
    # 显示当前模型信息
    current_model = None
    for m in AVAILABLE_MODELS:
        if m.get("path") == SD_MODEL_PATH or m.get("absolute_path") == SD_MODEL_PATH:
            current_model = m
            break
    
    if current_model:
        print(f"\n📊 当前模型详情:")
        print(f"  名称: {current_model['name']}")
        print(f"  大小: {current_model['size_gb']} GB")
        print(f"  标签: {', '.join(current_model['tags'])}")
        print(f"  评分: {current_model['score']}")
        print(f"  OpenVINO可用: {current_model['is_ov']}")
        print(f"  相对路径: {current_model.get('path', 'N/A')}")
    else:
        print(f"\n⚠️ 当前模型未在索引中找到（可能是 legacy 模式）")
        print(f"   使用路径: {SD_MODEL_PATH}")
    
    # ==================== LoRA 信息 ====================
    print(f"\n🎯 LoRA 信息:")
    print(f"  LoRA 总数: {len(AVAILABLE_LORAS)} 个")
    print(f"  激活索引: {LORA_ACTIVE_INDICES}")
    print(f"  激活数量: {len(FINAL_LORA_LIST)} 个")
    
    if FINAL_LORA_LIST:
        print(f"\n📋 当前激活的 LoRA:")
        for i, lora in enumerate(FINAL_LORA_LIST):
            lora_name = os.path.basename(lora["path"])
            lora_weight = lora["weight"]
            
            # 从索引中查找 LoRA 详情
            lora_info = None
            for l in AVAILABLE_LORAS:
                if l.get("filename") == lora_name or l.get("name") in lora_name:
                    lora_info = l
                    break
            
            print(f"  [{i+1}] {lora_name}")
            print(f"      权重: {lora_weight}")
            if lora_info:
                print(f"      标签: {', '.join(lora_info.get('tags', ['无']))}")
                print(f"      大小: {lora_info.get('size_mb', 0)} MB")
                print(f"      评分: {lora_info.get('score', 0)}")
    else:
        print(f"  ⚠️ 没有激活任何 LoRA")
    
    # ==================== Top 5 推荐模型 ====================
    print(f"\n⭐ Top 5 推荐 SD 模型:")
    for i, m in enumerate(AVAILABLE_MODELS[:5]):
        stars = "⭐" * (m["score"] // 20)
        default_tag = " 👑" if m["name"] == MODEL_INDEX.get("default") else ""
        print(f"   {i+1}. {m['name'][:40]:40s} {m['size_gb']:.1f}GB {stars}{default_tag}")
    
    # ==================== Top 5 推荐 LoRA ====================
    if AVAILABLE_LORAS:
        print(f"\n⭐ Top 5 推荐 LoRA:")
        for i, l in enumerate(AVAILABLE_LORAS[:5]):
            stars = "⭐" * (l["score"] // 20)
            default_tag = " 👑" if l["name"] == LORA_INDEX.get("default") else ""
            print(f"   {i+1}. {l['name'][:40]:40s} {l['size_mb']:.1f}MB {stars}{default_tag}")
    
    print("\n" + "=" * 60)
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"\n💡 请检查:")
    print(f"   1. tools/config.py 是否存在")
    print(f"   2. scripts/lora_index.json 是否存在")
    print(f"   3. 当前工作目录: {os.getcwd()}")
    
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()