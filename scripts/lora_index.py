# scripts/lora_index.py
# ==================== 📚 LoRA 索引生成器（支持 SD1.5 + SDXL） ====================
"""
用法:
    python lora_index.py              # 生成索引文件
    python lora_index.py --refresh    # 强制刷新
    python lora_index.py --list       # 列出所有 LoRA
    python lora_index.py --list --type sdxl  # 只列出 SDXL LoRA
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ==================== 配置 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # sd_generator/
SD_ROOT = os.path.dirname(PROJECT_ROOT)                   # SD_OpenVINO/

# 🆕 多类型 LoRA 目录配置
LORA_TYPES = {
    "sd15": {
        "name": "SD1.5",
        "icon": "🟢",
        "dirs": [
            os.path.join(SD_ROOT, "models", "sd15-lora"),
            os.path.join(PROJECT_ROOT, "models", "sd15-lora"),
        ],
    },
    "sdxl": {
        "name": "SDXL",
        "icon": "🔵",
        "dirs": [
            os.path.join(SD_ROOT, "models", "sdxl-lora"),
            os.path.join(PROJECT_ROOT, "models", "sdxl-lora"),
        ],
    },
}

def find_lora_dirs():
    """查找所有存在的 LoRA 目录"""
    found = {}
    for lora_type, config in LORA_TYPES.items():
        for candidate in config["dirs"]:
            candidate = os.path.normpath(candidate)
            if os.path.exists(candidate):
                found[lora_type] = candidate
                break
    return found

LORA_DIRS_FOUND = find_lora_dirs()
INDEX_FILE = os.path.join(CURRENT_DIR, "lora_index.json")

# ==================== LoRA 标签映射 ====================
LORA_TAGS = {
    "mecha": ["mecha", "gundam", "robot", "mechagirl", "AMecha", "MechaGirl"],
    "character": ["chunli", "eula", "tifa", "sirius", "yor", "leifang", "kandisi"],
    "clothing": ["qipao", "kimono", "swim", "dress", "lace", "stocking", "maid", "sailor"],
    "style": ["realistic", "anime", "sketch", "gongbi", "oil", "watercolor"],
    "body": ["busty", "cleavage", "preggo"],
    "cosplay": ["cos", "cosplay"],
    "asian": ["china", "hanfu", "guqinghan", "linghan"],
    "fantasy": ["dragon", "elf", "monster", "fantasy"],
}

# LoRA 推荐分数
LORA_SCORES = {
    # SD1.5
    "MechaGirlFigure": 95,
    "AMechaSSS": 92,
    "mecha_offset": 90,
    "Mechav2": 88,
    "MechaGirl": 85,
    "mecha_girl": 82,
    "eula": 80,
    "chunli": 78,
    "tifa": 75,
    "yor": 73,
    "asian_beauty": 70,
    "hanfu_transparent": 68,
    "qipao": 65,
    "busty_slider": 60,
    # SDXL
    "aesthetic_anime": 85,
    "anmi_sdxl": 82,
    "xlAsianRealisticMix": 80,
}


def get_relative_path(abs_path):
    """将绝对路径转换为相对于项目根目录的路径"""
    abs_path = os.path.normpath(abs_path)
    rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
    return rel_path.replace('\\', '/')


def scan_loras():
    """扫描所有 LoRA 目录，返回 LoRA 信息列表"""
    if not LORA_DIRS_FOUND:
        print(f"❌ 找不到任何 LoRA 目录！")
        print(f"   请检查以下位置:")
        for lora_type, config in LORA_TYPES.items():
            for c in config["dirs"]:
                print(f"   - {c}")
        return []
    
    loras = []
    
    for lora_type, lora_dir in LORA_DIRS_FOUND.items():
        config = LORA_TYPES[lora_type]
        print(f"{config['icon']} 扫描目录 [{config['name']}]: {lora_dir}")
        
        lora_path = Path(lora_dir)
        
        for ext in [".safetensors", ".ckpt", ".pt"]:
            for f in lora_path.glob(f"*{ext}"):
                name = f.stem
                size_mb = f.stat().st_size / (1024**2)
                
                tags = []
                name_lower = name.lower()
                for tag, keywords in LORA_TAGS.items():
                    if any(kw.lower() in name_lower for kw in keywords):
                        tags.append(tag)
                
                if not tags:
                    tags.append("uncategorized")
                
                score = 50
                for key, val in LORA_SCORES.items():
                    if key.lower() in name_lower:
                        score = val
                        break
                
                version_match = re.search(r'[vV](\d+\.?\d*)', name)
                version = version_match.group(1) if version_match else None
                
                rel_path = get_relative_path(str(f.absolute()))
                
                loras.append({
                    "name": name,
                    "filename": f.name,
                    "lora_type": lora_type,
                    "lora_type_name": config["name"],
                    "lora_type_icon": config["icon"],
                    "path": rel_path,
                    "absolute_path": str(f.absolute()),
                    "size_mb": round(size_mb, 2),
                    "tags": tags,
                    "score": score,
                    "version": version,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
    
    loras.sort(key=lambda x: (0 if x["lora_type"] == "sd15" else 1, -x["score"]))
    return loras


def generate_index(refresh=False):
    """生成 LoRA 索引 JSON 文件"""
    print("🔍 正在扫描 LoRA 目录...")
    loras = scan_loras()
    
    if not loras:
        print("❌ 没有找到任何 LoRA 文件！")
        return False
    
    categories = {}
    for tag in LORA_TAGS.keys():
        categories[tag] = [l["name"] for l in loras if tag in l["tags"]]
    categories["uncategorized"] = [l["name"] for l in loras if "uncategorized" in l["tags"]]
    
    type_groups = {}
    for lora_type, config in LORA_TYPES.items():
        type_loras = [l for l in loras if l["lora_type"] == lora_type]
        if type_loras:
            type_groups[lora_type] = {
                "name": config["name"],
                "icon": config["icon"],
                "count": len(type_loras),
                "default": type_loras[0]["name"] if type_loras else None,
                "loras": [l["name"] for l in type_loras],
            }
    
    rel_lora_dirs = {}
    for lora_type, lora_dir in LORA_DIRS_FOUND.items():
        rel_lora_dirs[lora_type] = get_relative_path(lora_dir)
    
    index_data = {
        "generated": datetime.now().isoformat(),
        "project_root": PROJECT_ROOT,
        "lora_dirs": LORA_DIRS_FOUND,
        "lora_dirs_relative": rel_lora_dirs,
        "total_loras": len(loras),
        "loras": loras,
        "default": loras[0]["name"] if loras else None,
        "default_type": loras[0]["lora_type"] if loras else None,
        "categories": categories,
        "type_groups": type_groups,
    }
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ LoRA 索引已生成: {INDEX_FILE}")
    print(f"📊 共找到 {len(loras)} 个 LoRA")
    print(f"🏆 默认推荐: {index_data['default']} ({index_data['default_type']})")
    
    print("\n📁 LoRA 类型统计:")
    for lora_type, group in type_groups.items():
        print(f"   {group['icon']} {group['name']}: {group['count']} 个")
        if group['default']:
            print(f"      默认: {group['default']}")
    
    print("\n⭐ Top 5 推荐 LoRA:")
    for i, l in enumerate(loras[:5]):
        stars = "⭐" * (l["score"] // 20)
        icon = l.get("lora_type_icon", "📁")
        print(f"   {i+1}. {icon} {l['name'][:50]} ({l['size_mb']:.1f}MB) {stars}")
    
    return True


def list_loras(filter_type=None):
    """列出所有 LoRA（从索引文件读取）"""
    if not os.path.exists(INDEX_FILE):
        print("❌ 索引文件不存在，请先运行: python lora_index.py")
        return
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    loras = data["loras"]
    if filter_type:
        loras = [l for l in loras if l["lora_type"] == filter_type]
        if not loras:
            print(f"❌ 没有找到 {filter_type} 类型的 LoRA")
            return
    
    print(f"\n📚 可用 LoRA 列表 (共 {len(loras)} 个):")
    if filter_type:
        type_name = LORA_TYPES.get(filter_type, {}).get("name", filter_type)
        print(f"   🔍 过滤类型: {type_name}")
    print("=" * 80)
    
    for i, l in enumerate(loras):
        stars = "⭐" * (l["score"] // 20)
        default_tag = " 👑" if l["name"] == data["default"] else ""
        icon = l.get("lora_type_icon", "📁")
        type_name = l.get("lora_type_name", "")
        
        print(f"  [{i:2d}] {icon} {l['name'][:45]:45s} {l['size_mb']:6.1f}MB  {stars}{default_tag}")
        print(f"        类型: {type_name} | 标签: {', '.join(l['tags'])}")
    
    print(f"\n🏆 默认推荐: {data['default']}")
    print(f"📅 索引生成时间: {data['generated']}")


def main():
    parser = argparse.ArgumentParser(description="SD LoRA 索引管理器（支持 SD1.5 + SDXL）")
    parser.add_argument("--refresh", action="store_true", help="强制重新扫描生成索引")
    parser.add_argument("--list", action="store_true", help="列出所有 LoRA")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="只列出指定类型的 LoRA")
    
    args = parser.parse_args()
    
    if args.list:
        list_loras(filter_type=args.type)
    elif args.refresh or not os.path.exists(INDEX_FILE):
        generate_index(refresh=args.refresh)
    else:
        print("📋 索引文件已存在，使用 --refresh 强制重新生成")
        list_loras()


if __name__ == "__main__":
    main()