# scripts/switch_lora.py
# ==================== 🔄 LoRA 切换工具（支持 SD1.5 + SDXL） ====================
"""
用法:
    python switch_lora.py --list                    # 列出所有 LoRA
    python switch_lora.py --list --type sdxl       # 只列出 SDXL LoRA
    python switch_lora.py --type sd15|sdxl         # 切换 LoRA 类型
    python switch_lora.py --set <名称>             # 设置默认 LoRA
    python switch_lora.py --active <索引>          # 设置激活的 LoRA 索引
    python switch_lora.py --refresh                # 重新生成索引
    python switch_lora.py --status                 # 显示状态
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
INDEX_FILE = os.path.join(CURRENT_DIR, "lora_index.json")

LORA_TYPES = {
    "sd15": {"name": "SD1.5", "icon": "🟢"},
    "sdxl": {"name": "SDXL", "icon": "🔵"},
}


def get_index():
    if not os.path.exists(INDEX_FILE):
        print("⚠️ LoRA 索引不存在，正在生成...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "lora_index.py")])
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ 索引文件损坏 ({e})，正在重建...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "lora_index.py"), "--refresh"])
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def get_loras_by_type(data, lora_type):
    return [l for l in data.get("loras", []) if l.get("lora_type") == lora_type]


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


def switch_lora_type(lora_type):
    """切换 LoRA 类型（同时更新 MODEL_TYPE）"""
    data = get_index()
    
    loras = get_loras_by_type(data, lora_type)
    if not loras:
        print(f"❌ 没有找到 {lora_type} 类型的 LoRA")
        type_name = LORA_TYPES.get(lora_type, {}).get("name", lora_type)
        print(f"   请先下载 {type_name} LoRA 或运行: python lora_index.py --refresh")
        return False
    
    if set_config_value("MODEL_TYPE", f'"{lora_type}"'):
        type_name = LORA_TYPES.get(lora_type, {}).get("name", lora_type)
        print(f"✅ 已切换到 {type_name} 模型和 LoRA")
        print(f"   📊 可用 LoRA: {len(loras)} 个")
        
        default_name = data.get("default")
        if default_name:
            for l in loras:
                if l["name"] == default_name:
                    print(f"   🏆 默认推荐: {default_name}")
                    break
        
        # 显示该类型 Top 5
        print(f"\n   ⭐ {type_name} Top 5:")
        for i, l in enumerate(loras[:5], 1):
            stars = "⭐" * (l.get("score", 0) // 20)
            size = l.get("size_mb", 0)
            default_mark = " 👑" if l["name"] == data.get("default") else ""
            print(f"      [{i}] {l['name'][:40]:40s} {size:6.1f}MB  {stars}{default_mark}")
        
        return True
    else:
        return False


def list_loras(filter_type=None):
    data = get_index()
    loras = data.get("loras", [])
    
    if filter_type:
        loras = [l for l in loras if l.get("lora_type") == filter_type]
        if not loras:
            print(f"❌ 没有找到 {filter_type} 类型的 LoRA")
            return
    
    if not loras:
        print("❌ 没有找到任何 LoRA")
        return
    
    print(f"\n📚 可用 LoRA 列表 (共 {len(loras)} 个):")
    if filter_type:
        type_name = LORA_TYPES.get(filter_type, {}).get("name", filter_type)
        print(f"   🔍 过滤类型: {type_name}")
    print("=" * 80)
    
    for i, l in enumerate(loras):
        default = " 👑" if l["name"] == data.get("default") else ""
        stars = "⭐" * (l.get("score", 0) // 20)
        icon = l.get("lora_type_icon", "📁")
        type_name = l.get("lora_type_name", "")
        size = l.get("size_mb", 0)
        
        print(f"  [{i:2d}] {icon} {l['name'][:45]:45s} {size:6.1f}MB  {stars}{default}")
        print(f"        类型: {type_name} | 标签: {', '.join(l.get('tags', []))}")
    
    type_groups = data.get("type_groups", {})
    print("\n📊 LoRA 类型统计:")
    for lora_type, group in type_groups.items():
        print(f"   {group['icon']} {group['name']}: {group['count']} 个")
        if group.get('default'):
            print(f"      默认: {group['default']}")
    
    print(f"\n🏆 全局默认: {data.get('default', '无')}")
    print(f"📅 索引更新: {data.get('generated', '未知')}")


def set_default_lora(lora_name, lora_type=None):
    data = get_index()
    loras = data.get("loras", [])
    
    if lora_type:
        loras = [l for l in loras if l.get("lora_type") == lora_type]
    
    found = None
    for l in loras:
        if lora_name.lower() in l["name"].lower():
            found = l
            break
    
    if not found:
        print(f"❌ 未找到包含 '{lora_name}' 的 LoRA")
        print("提示: 使用 --list 查看所有 LoRA")
        return
    
    data["default"] = found["name"]
    data["default_type"] = found.get("lora_type", "sd15")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    lora_type = found.get("lora_type", "sd15")
    set_config_value("MODEL_TYPE", f'"{lora_type}"')
    
    print(f"✅ 默认 LoRA 已切换: {found['name']}")
    print(f"   📁 {found['path']}")
    print(f"   🏷️  标签: {', '.join(found['tags'])}")
    print(f"   📊 类型: {found.get('lora_type_name', found.get('lora_type', 'unknown'))}")


def set_active_lora(index, lora_type=None):
    data = get_index()
    loras = data.get("loras", [])
    
    if lora_type:
        loras = [l for l in loras if l.get("lora_type") == lora_type]
        if not loras:
            print(f"❌ 没有找到 {lora_type} 类型的 LoRA")
            return
        if index < 0 or index >= len(loras):
            print(f"❌ 无效索引: {index}，可用范围 0-{len(loras)-1}")
            return
        lora = loras[index]
        global_index = None
        for i, l in enumerate(data["loras"]):
            if l["name"] == lora["name"]:
                global_index = i
                break
        if global_index is None:
            print(f"❌ 找不到 LoRA: {lora['name']}")
            return
        index = global_index
    else:
        if index < 0 or index >= len(loras):
            print(f"❌ 无效索引: {index}，可用范围 0-{len(loras)-1}")
            return
        lora = loras[index]
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config/app.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if 'LORA_ACTIVE_INDICES' in content:
        content = re.sub(r'LORA_ACTIVE_INDICES = \[.*?\]', f'LORA_ACTIVE_INDICES = [{index}]', content)
    else:
        content += f'\nLORA_ACTIVE_INDICES = [{index}]\n'
    
    lora_type = lora.get("lora_type", "sd15")
    if 'MODEL_TYPE' in content:
        content = re.sub(r'MODEL_TYPE = ".*?"', f'MODEL_TYPE = "{lora_type}"', content)
    else:
        content += f'MODEL_TYPE = "{lora_type}"\n'
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 已激活 LoRA: {lora['name']} (索引 {index})")
    print(f"   📁 {lora['path']}")
    print(f"   🏷️  标签: {', '.join(lora['tags'])}")
    print(f"   📊 类型: {lora.get('lora_type_name', lora.get('lora_type', 'unknown'))}")


def show_status():
    data = get_index() if os.path.exists(INDEX_FILE) else None
    
    print("\n📊 LoRA 当前状态:")
    print("=" * 60)
    
    if data:
        loras = data.get("loras", [])
        print(f"  索引文件: {INDEX_FILE}")
        print(f"  LoRA 总数: {len(loras)}")
        print(f"  全局默认: {data.get('default', '无')}")
        print(f"  默认类型: {data.get('default_type', '无')}")
        
        type_groups = data.get("type_groups", {})
        if type_groups:
            print(f"\n  📁 LoRA 类型:")
            for lora_type, group in type_groups.items():
                print(f"     {group['icon']} {group['name']}: {group['count']} 个")
                if group.get('default'):
                    print(f"        默认: {group['default']}")
            
            print(f"\n  ⭐ 各类型 Top 5 推荐 LoRA:")
            for lora_type, group in type_groups.items():
                icon = group['icon']
                name = group['name']
                type_loras = [l for l in loras if l.get("lora_type") == lora_type]
                top5 = type_loras[:5]
                
                print(f"\n     {icon} {name}:")
                for i, l in enumerate(top5, 1):
                    stars = "⭐" * (l.get("score", 0) // 20)
                    size = l.get("size_mb", 0)
                    default_mark = " 👑" if l["name"] == group.get('default') else ""
                    print(f"        [{i}] {l['name'][:40]:40s} {size:6.1f}MB  {stars}{default_mark}")
    else:
        print(f"  ⚠️ 找不到索引文件: {INDEX_FILE}")
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        model_type_match = re.search(r'MODEL_TYPE = "(.*?)"', content)
        active_match = re.search(r'LORA_ACTIVE_INDICES = \[(.*?)\]', content)
        
        print(f"\n  📄 配置文件: {CONFIG_FILE}")
        if model_type_match:
            model_type = model_type_match.group(1)
            type_name = LORA_TYPES.get(model_type, {}).get("name", model_type)
            print(f"  模型/LoRA 类型: {type_name}")
        else:
            print(f"  模型/LoRA 类型: 未设置")
        
        if active_match:
            indices = active_match.group(1)
            print(f"  激活索引: [{indices}]")
    
    print(f"\n💡 设置命令:")
    print(f"  --type sd15|sdxl         切换模型/LoRA 类型")
    print(f"  --set <名称>             设置默认 LoRA")
    print(f"  --set <名称> --type sdxl 设置 SDXL 的默认 LoRA")
    print(f"  --active <索引>          激活指定索引的 LoRA")
    print(f"  --refresh               重新生成索引")
    print(f"  --list                   列出所有 LoRA")
    print(f"  --list --type sdxl       只列出 SDXL LoRA")


def main():
    parser = argparse.ArgumentParser(description="SD LoRA 切换工具（支持 SD1.5 + SDXL）")
    parser.add_argument("--list", action="store_true", help="列出所有 LoRA")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="切换或过滤 LoRA 类型")
    parser.add_argument("--set", type=str, help="设置默认 LoRA")
    parser.add_argument("--active", type=int, help="激活指定索引的 LoRA")
    parser.add_argument("--refresh", action="store_true", help="重新生成索引")
    parser.add_argument("--status", action="store_true", help="显示状态")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    
    elif args.list:
        list_loras(filter_type=args.type)
    
    elif args.type and not args.list:
        switch_lora_type(args.type)
    
    elif args.set:
        set_default_lora(args.set, lora_type=args.type)
    
    elif args.active is not None:
        set_active_lora(args.active, lora_type=args.type)
    
    elif args.refresh:
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "lora_index.py"), "--refresh"])
        show_status()


if __name__ == "__main__":
    main()