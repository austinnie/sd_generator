# scripts/switch_lora.py
# ==================== 🔄 LoRA 切换工具 ====================
"""
用法:
    python switch_lora.py --list              # 列出所有 LoRA
    python switch_lora.py --set <名称>        # 切换默认 LoRA
    python switch_lora.py --active <索引>     # 设置激活的 LoRA 索引
    python switch_lora.py --refresh           # 重新生成索引
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

# config/app.py 在项目根目录的 config/ 下
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "app.py")
INDEX_FILE = os.path.join(CURRENT_DIR, "lora_index.json")


def get_index():
    """获取索引数据"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️ LoRA 索引不存在，正在生成...")
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "lora_index.py")])
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def list_loras():
    """列出所有 LoRA"""
    data = get_index()
    print(f"\n📚 可用 LoRA 列表 (共 {data['total_loras']} 个):")
    print("=" * 80)
    for i, l in enumerate(data["loras"]):
        default = " 👑" if l["name"] == data["default"] else ""
        stars = "⭐" * (l["score"] // 20)
        print(f"  [{i:2d}] {l['name'][:45]:45s} {l['size_mb']:6.1f}MB  {stars}{default}")
        if l["tags"]:
            print(f"        标签: {', '.join(l['tags'])}")
    
    print(f"\n🏆 当前默认: {data['default']}")
    print(f"📅 索引更新: {data['generated']}")


def set_default_lora(lora_name):
    """设置默认 LoRA"""
    data = get_index()
    
    found = None
    for l in data["loras"]:
        if lora_name.lower() in l["name"].lower():
            found = l
            break
    
    if not found:
        print(f"❌ 未找到包含 '{lora_name}' 的 LoRA")
        print("提示: 使用 --list 查看所有 LoRA")
        return
    
    data["default"] = found["name"]
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 默认 LoRA 已切换: {found['name']}")
    print(f"   📁 {found['path']}")
    print(f"   🏷️  标签: {', '.join(found['tags'])}")


def set_active_lora(index):
    """设置激活的 LoRA 索引（写入 config/app.py）"""
    data = get_index()
    
    if index < 0 or index >= len(data["loras"]):
        print(f"❌ 无效索引: {index}，可用范围 0-{len(data['loras'])-1}")
        return
    
    lora = data["loras"][index]
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config/app.py 文件: {CONFIG_FILE}")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 修改 LORA_ACTIVE_INDICES
    if 'LORA_ACTIVE_INDICES' in content:
        content = re.sub(r'LORA_ACTIVE_INDICES = \[.*?\]', f'LORA_ACTIVE_INDICES = [{index}]', content)
    else:
        # 在 LORA_ACTIVE_INDICES 定义位置插入
        # 找到 # ==================== LoRA 配置 ==================== 位置
        if '# ==================== LoRA 配置 ====================' in content:
            content = content.replace(
                '# ==================== LoRA 配置 ====================',
                f'# ==================== LoRA 配置 ====================\nLORA_ACTIVE_INDICES = [{index}]'
            )
        else:
            # 在文件末尾添加
            content += f'\nLORA_ACTIVE_INDICES = [{index}]\n'
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 已激活 LoRA: {lora['name']} (索引 {index})")
    print(f"   📁 {lora['path']}")
    print(f"   🏷️  标签: {', '.join(lora['tags'])}")
    
    # 提示用户需要清除缓存
    print("\n⚠️ 请清除 Python 缓存后重新运行:")
    print("   rmdir /s /q config\\__pycache__")
    print("   rmdir /s /q core\\__pycache__")


def show_status():
    """显示当前状态"""
    data = get_index() if os.path.exists(INDEX_FILE) else None
    
    print("\n📊 LoRA 当前状态:")
    
    if data:
        print(f"  LoRA 总数: {data.get('total_loras', 0)}")
        print(f"  默认推荐: {data.get('default', '无')}")
        print(f"  索引文件: {INDEX_FILE}")
    else:
        print(f"  ⚠️ 找不到索引文件: {INDEX_FILE}")
    
    # 读取 config/app.py 中的当前激活索引
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        active_match = re.search(r'LORA_ACTIVE_INDICES = \[(\d+)\]', content)
        if active_match:
            idx = int(active_match.group(1))
            print(f"  当前激活索引: {idx}")
            
            if data and idx < len(data["loras"]):
                lora = data["loras"][idx]
                print(f"  当前激活 LoRA: {lora['name']}")
        else:
            print(f"  当前激活索引: 未设置 (无 LoRA)")
    
    print(f"\n💡 可用命令:")
    print(f"  --list          列出所有 LoRA")
    print(f"  --set <名称>    设置默认推荐 LoRA")
    print(f"  --active <索引> 激活指定索引的 LoRA")
    print(f"  --refresh       重新生成索引")


def main():
    parser = argparse.ArgumentParser(description="SD LoRA 切换工具")
    parser.add_argument("--list", action="store_true", help="列出所有 LoRA")
    parser.add_argument("--set", type=str, help="设置默认推荐 LoRA")
    parser.add_argument("--active", type=int, help="激活指定索引的 LoRA")
    parser.add_argument("--refresh", action="store_true", help="重新生成索引")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    elif args.list:
        list_loras()
    elif args.set:
        set_default_lora(args.set)
    elif args.active is not None:
        set_active_lora(args.active)
    elif args.refresh:
        subprocess.run([sys.executable, os.path.join(CURRENT_DIR, "lora_index.py"), "--refresh"])


if __name__ == "__main__":
    main()