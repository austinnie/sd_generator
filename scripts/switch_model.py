# scripts/switch_model.py
# ==================== 🔄 模型切换工具（支持 SD1.5 + SDXL） ====================
"""
用法:
    python switch_model.py --list                    # 列出所有模型
    python switch_model.py --list --type sdxl       # 只列出 SDXL 模型
    python switch_model.py --set <名称>             # 切换智能推荐模型
    python switch_model.py --type sd15|sdxl         # 切换模型类型
    python switch_model.py --mode <模式>            # 切换选择模式
    python switch_model.py --legacy <编号>          # 切换到旧版编号模式
    python switch_model.py --ov                     # 启用 OpenVINO
    python switch_model.py --no-ov                  # 禁用 OpenVINO
    python switch_model.py --refresh                # 重新生成索引
    python switch_model.py --status                 # 显示状态
"""

import os
import sys
import json
import argparse
import subprocess
import re

# ==================== 路径配置 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # sd_generator/

CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "app.py")
INDEX_FILE = os.path.join(CURRENT_DIR, "models_index.json")

MODEL_TYPES = {
    "sd15": {"name": "SD1.5", "icon": "🟢"},
    "sdxl": {"name": "SDXL", "icon": "🔵"},
}


def get_index():
    if not os.path.exists(INDEX_FILE):
        print("⚠️ 模型索引不存在，正在生成...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py")])
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ 索引文件损坏 ({e})，正在重建...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py"), "--refresh"])
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def get_models_by_type(data, model_type):
    return [m for m in data.get("models", []) if m.get("model_type") == model_type]


def set_config_value(key, value):
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config/app.py 文件: {CONFIG_FILE}")
        return False
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        pattern = rf'{key} = .*?\n'
        if re.search(pattern, content):
            content = re.sub(pattern, f'{key} = {value}\n', content)
        else:
            content += f'\n{key} = {value}\n'
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ 写入 config/app.py 失败: {e}")
        return False


def switch_model_type(model_type, auto_fallback=True):
    data = get_index()
    models = get_models_by_type(data, model_type)
    
    if not models:
        config = MODEL_TYPES.get(model_type, {})
        fallback_type = config.get("fallback_type")
        
        if auto_fallback and fallback_type:
            fallback_models = get_models_by_type(data, fallback_type)
            if fallback_models:
                fallback_name = MODEL_TYPES.get(fallback_type, {}).get("name", fallback_type)
                print(f"⚠️ {config.get('name', model_type)} 无可用模型，自动降级到 {fallback_name}")
                return switch_model_type(fallback_type, auto_fallback=False)
            else:
                print(f"❌ {config.get('name', model_type)} 和 {fallback_type} 都无可用模型")
                return False, None
        else:
            print(f"❌ {config.get('name', model_type)} 无可用模型")
            return False, None
    
    default_name = data.get("default")
    selected_model = None
    
    if default_name:
        for m in models:
            if m["name"] == default_name:
                selected_model = m
                break
    
    if not selected_model:
        selected_model = models[0]
    
    if set_config_value("MODEL_TYPE", f'"{model_type}"'):
        type_name = MODEL_TYPES.get(model_type, {}).get("name", model_type)
        print(f"✅ 已切换到 {type_name}")
        print(f"   📁 模型: {selected_model['name']}")
        return True, selected_model
    else:
        return False, None


def list_models(filter_type=None):
    data = get_index()
    models = data.get("models", [])
    
    if filter_type:
        models = [m for m in models if m.get("model_type") == filter_type]
        if not models:
            print(f"❌ 没有找到 {filter_type} 类型的模型")
            return
    
    if not models:
        print("❌ 没有找到任何模型")
        return
    
    print(f"\n📚 可用模型列表 (共 {len(models)} 个):")
    if filter_type:
        type_name = MODEL_TYPES.get(filter_type, {}).get("name", filter_type)
        print(f"   🔍 过滤类型: {type_name}")
    print("=" * 80)
    
    for i, m in enumerate(models):
        default = " 👑" if m["name"] == data.get("default") else ""
        ov = " [OV]" if m.get("is_ov") else ""
        stars = "⭐" * (m.get("score", 0) // 20)
        icon = m.get("model_type_icon", "📁")
        type_name = m.get("model_type_name", "")
        size = m.get("size_gb", 0)
        
        print(f"  [{i:2d}] {icon} {m['name'][:45]:45s} {size:4.1f}GB  {stars}{ov}{default}")
        print(f"        类型: {type_name} | 标签: {', '.join(m.get('tags', []))}")
    
    type_groups = data.get("type_groups", {})
    print("\n📊 模型类型统计:")
    for model_type, group in type_groups.items():
        print(f"   {group['icon']} {group['name']}: {group['count']} 个")
        if group.get('default'):
            print(f"      默认: {group['default']}")
    
    print(f"\n🏆 全局默认: {data.get('default', '无')}")
    print(f"📅 索引更新: {data.get('generated', '未知')}")


def set_mode(mode):
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config/app.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if mode in ["legacy", "smart", "manual"]:
        if 'MODEL_SELECTION_MODE' in content:
            content = re.sub(r'MODEL_SELECTION_MODE = ".*?"', f'MODEL_SELECTION_MODE = "{mode}"', content)
        else:
            content += f'\nMODEL_SELECTION_MODE = "{mode}"\n'
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ 已切换到 {mode} 模式")
    else:
        print(f"❌ 无效模式: {mode}，可选: legacy, smart, manual")


def set_smart_default(model_name):
    data = get_index()
    
    found = None
    for m in data["models"]:
        if model_name.lower() in m["name"].lower():
            found = m
            break
    
    if not found:
        print(f"❌ 未找到包含 '{model_name}' 的模型")
        print("提示: 使用 --list 查看所有模型")
        return
    
    data["default"] = found["name"]
    data["default_type"] = found.get("model_type", "sd15")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    set_config_value("MODEL_TYPE", f'"{found["model_type"]}"')
    set_mode("smart")
    
    print(f"✅ 智能模式默认模型已切换: {found['name']}")
    print(f"   📊 类型: {found.get('model_type_name', found.get('model_type', 'unknown'))}")


def set_legacy_model(index, model_type=None):
    data = get_index()
    legacy_mapping = data.get("legacy_mapping", {})
    
    if not model_type:
        model_type = data.get("default_type", "sd15")
    
    if model_type not in legacy_mapping:
        print(f"❌ 没有 {model_type} 的 legacy 映射")
        return
    
    mapping = legacy_mapping[model_type]
    if str(index) not in mapping:
        print(f"❌ 无效编号: {index}，可用: {list(mapping.keys())}")
        return
    
    filename = mapping[str(index)]
    
    set_config_value("MODEL_TYPE", f'"{model_type}"')
    set_config_value("ACTIVE_MODEL", str(index))
    set_mode("legacy")
    
    type_name = MODEL_TYPES.get(model_type, {}).get("name", model_type)
    print(f"✅ 已切换到 legacy 模式")
    print(f"   📊 模型类型: {type_name}")
    print(f"   📁 编号 {index}: {filename}")


def toggle_ov(enable=True):
    set_config_value("USE_OPENVINO_MODEL", "True" if enable else "False")
    print(f"✅ {'已启用' if enable else '已关闭'} OpenVINO 模式")


def show_status():
    data = get_index() if os.path.exists(INDEX_FILE) else None
    
    print("\n📊 当前配置状态:")
    print("=" * 60)
    
    if data:
        print(f"  索引文件: {INDEX_FILE}")
        print(f"  模型总数: {data.get('total_models', 0)}")
        print(f"  全局默认: {data.get('default', '无')}")
        print(f"  默认类型: {data.get('default_type', '无')}")
        
        type_groups = data.get("type_groups", {})
        if type_groups:
            print(f"\n  📁 模型类型:")
            for model_type, group in type_groups.items():
                print(f"     {group['icon']} {group['name']}: {group['count']} 个")
                if group.get('default'):
                    print(f"        默认: {group['default']}")
    else:
        print(f"  ⚠️ 找不到索引文件: {INDEX_FILE}")
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        model_type_match = re.search(r'MODEL_TYPE = "(.*?)"', content)
        mode_match = re.search(r'MODEL_SELECTION_MODE = "(.*?)"', content)
        ov_match = re.search(r'USE_OPENVINO_MODEL = (True|False)', content)
        active_match = re.search(r'ACTIVE_MODEL = (\d+)', content)
        
        print(f"\n  📄 配置文件: {CONFIG_FILE}")
        print(f"  模型类型: {model_type_match.group(1) if model_type_match else '未设置'}")
        print(f"  选择模式: {mode_match.group(1) if mode_match else '未设置'}")
        print(f"  OpenVINO: {ov_match.group(1) if ov_match else 'False'}")
        if active_match:
            print(f"  Legacy 编号: {active_match.group(1)}")
    
    print(f"\n💡 可用命令:")
    print(f"  --list                   列出所有模型")
    print(f"  --list --type sdxl       只列出 SDXL 模型")
    print(f"  --set <名称>             设置智能推荐模型")
    print(f"  --type sd15|sdxl         切换模型类型")
    print(f"  --mode <模式>            切换模式 (legacy/smart/manual)")
    print(f"  --legacy <编号>          切换到旧版编号")
    print(f"  --ov                    启用 OpenVINO")
    print(f"  --no-ov                 禁用 OpenVINO")
    print(f"  --refresh               重新生成索引")


def main():
    parser = argparse.ArgumentParser(description="SD 模型切换工具（支持 SD1.5 + SDXL）")
    parser.add_argument("--list", action="store_true", help="列出所有模型")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="切换或过滤模型类型")
    parser.add_argument("--set", type=str, help="设置智能模式默认模型")
    parser.add_argument("--mode", choices=["legacy", "smart", "manual"], help="切换选择模式")
    parser.add_argument("--legacy", type=int, help="切换到旧版编号模式")
    parser.add_argument("--ov", action="store_true", help="启用 OpenVINO")
    parser.add_argument("--no-ov", action="store_true", help="禁用 OpenVINO")
    parser.add_argument("--refresh", action="store_true", help="重新生成索引")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    
    elif args.list:
        list_models(filter_type=args.type)
    
    elif args.type and not args.list:
        switch_model_type(args.type)
    
    elif args.set:
        set_smart_default(args.set)
    
    elif args.mode:
        set_mode(args.mode)
    
    elif args.legacy is not None:
        set_legacy_model(args.legacy)
    
    elif args.ov:
        toggle_ov(True)
    
    elif args.no_ov:
        toggle_ov(False)
    
    elif args.refresh:
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "model_index.py"), "--refresh"])


if __name__ == "__main__":
    main()