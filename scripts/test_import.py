# scripts/test_import.py
# 放在 scripts/ 目录内

import sys
import os

# 添加项目根目录到 Python 路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # sd_generator/
sys.path.insert(0, PROJECT_ROOT)

print(f"📁 当前目录: {CURRENT_DIR}")
print(f"📁 项目根目录: {PROJECT_ROOT}")
print("=" * 60)

try:
    # ✅ 修正：从 config.app 导入，而不是 config
    from config.app import (
        SD_MODEL_PATH, 
        AVAILABLE_MODELS, 
        MODEL_SELECTION_MODE,
        AVAILABLE_LORAS,
        FINAL_LORA_LIST,
        LORA_ACTIVE_INDICES,
        USE_OPENVINO_MODEL,
        LORA_INDEX,
        MODEL_INDEX,
        MODEL_TYPE,  # ✅ 添加这个
    )
    
    print("✅ 成功导入 config.app")
    print("=" * 60)
    
    # ==================== 基本信息 ====================
    print(f"\n📊 基本信息:")
    print(f"  模型类型: {MODEL_TYPE}")
    print(f"  选择模式: {MODEL_SELECTION_MODE}")
    print(f"  OpenVINO: {USE_OPENVINO_MODEL}")
    
    # ==================== 模型信息 ====================
    print(f"\n📦 SD 模型信息:")
    print(f"  可用模型总数: {len(AVAILABLE_MODELS)} 个")
    print(f"  模型路径: {SD_MODEL_PATH}")
    print(f"  模型名称: {os.path.basename(SD_MODEL_PATH) if SD_MODEL_PATH else '未设置'}")
    
    if AVAILABLE_MODELS:
        print(f"\n⭐ Top 5 推荐模型:")
        for i, m in enumerate(AVAILABLE_MODELS[:5]):
            stars = "⭐" * (m.get("score", 0) // 20)
            default_tag = " 👑" if m.get("name") == MODEL_INDEX.get("default") else ""
            print(f"   {i+1}. {m.get('name', 'unknown')[:40]:40s} {m.get('size_gb', 0):.1f}GB {stars}{default_tag}")
    
    # ==================== LoRA 信息 ====================
    print(f"\n🎯 LoRA 信息:")
    print(f"  LoRA 总数: {len(AVAILABLE_LORAS)} 个")
    print(f"  激活索引: {LORA_ACTIVE_INDICES}")
    print(f"  当前类型: {MODEL_TYPE}")
    
    if AVAILABLE_LORAS:
        # 统计各类型数量
        type_counts = {}
        for l in AVAILABLE_LORAS:
            lora_type = l.get('lora_type', 'unknown')
            type_counts[lora_type] = type_counts.get(lora_type, 0) + 1
        
        print(f"\n  📊 LoRA 类型统计:")
        for lora_type, count in type_counts.items():
            print(f"     {lora_type}: {count} 个")
        
        # 显示当前类型的 LoRA
        type_loras = [l for l in AVAILABLE_LORAS if l.get('lora_type') == MODEL_TYPE]
        print(f"\n  📋 {MODEL_TYPE} 类型的 LoRA: {len(type_loras)} 个")
        
        if type_loras:
            print(f"\n  ⭐ Top 5 推荐 {MODEL_TYPE} LoRA:")
            for i, l in enumerate(type_loras[:5]):
                stars = "⭐" * (l.get("score", 0) // 20)
                default_tag = " 👑" if l.get("name") == LORA_INDEX.get("default") else ""
                print(f"     {i+1}. {l.get('name', 'unknown')[:40]:40s} {l.get('size_mb', 0):.1f}MB {stars}{default_tag}")
        
        # 检查激活的 LoRA
        if LORA_ACTIVE_INDICES and type_loras:
            print(f"\n  🔗 当前激活的 LoRA 索引: {LORA_ACTIVE_INDICES}")
            for idx in LORA_ACTIVE_INDICES:
                if idx < len(type_loras):
                    l = type_loras[idx]
                    print(f"     [{idx}] {l.get('name', 'unknown')}")
                    print(f"         路径: {l.get('path', 'N/A')}")
                    print(f"         存在: {'✅' if os.path.exists(l.get('absolute_path', '')) else '❌'}")
                else:
                    print(f"     ⚠️ 索引 {idx} 超出范围（共 {len(type_loras)} 个）")
    
    # ==================== 最终 LoRA 列表 ====================
    print(f"\n📦 FINAL_LORA_LIST:")
    if FINAL_LORA_LIST:
        print(f"  共 {len(FINAL_LORA_LIST)} 个 LoRA 将被加载:")
        for i, lora in enumerate(FINAL_LORA_LIST):
            print(f"    [{i+1}] {lora.get('name', 'unknown')}")
            print(f"        权重: {lora.get('weight', 1.0)}")
            print(f"        路径: {lora.get('path', 'N/A')}")
            print(f"        存在: {'✅' if os.path.exists(lora.get('path', '')) else '❌'}")
    else:
        print(f"  ⚠️ FINAL_LORA_LIST 为空")
        print(f"  可能原因:")
        print(f"    1. AVAILABLE_LORAS 为空")
        print(f"    2. 没有 {MODEL_TYPE} 类型的 LoRA")
        print(f"    3. LORA_ACTIVE_INDICES 索引超出范围")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"\n💡 请检查:")
    print(f"   1. config/app.py 是否存在")
    print(f"   2. 当前工作目录: {os.getcwd()}")
    print(f"   3. Python 路径: {sys.path}")
    
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()