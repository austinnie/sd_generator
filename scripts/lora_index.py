# scripts/lora_index.py
# ==================== 📚 LoRA 索引生成器 ====================
"""
用法:
    python lora_index.py              # 生成索引文件
    python lora_index.py --refresh    # 强制刷新
    python lora_index.py --list       # 列出所有 LoRA
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ==================== 配置 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # v8_universal_generator/
SD_ROOT = os.path.dirname(PROJECT_ROOT)                   # SD_OpenVINO/

# LoRA 目录候选
LORA_DIR_CANDIDATES = [
    os.path.join(SD_ROOT, "models", "sd15-lora"),         # E:\SD_OpenVINO\models\sd15-lora
    os.path.join(PROJECT_ROOT, "models", "sd15-lora"),    # E:\SD_OpenVINO\v8_universal_generator\models\sd15-lora
]

# 找到实际存在的 LoRA 目录
LORA_DIR = None
for candidate in LORA_DIR_CANDIDATES:
    candidate = os.path.normpath(candidate)
    if os.path.exists(candidate):
        LORA_DIR = candidate
        break

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
}


def get_relative_path(abs_path):
    """将绝对路径转换为相对于项目根目录的路径"""
    abs_path = os.path.normpath(abs_path)
    rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
    return rel_path.replace('\\', '/')


def scan_loras():
    """扫描 LoRA 目录，返回 LoRA 信息列表"""
    if not LORA_DIR:
        print(f"❌ 找不到 LoRA 目录！")
        print(f"   请检查以下位置:")
        for c in LORA_DIR_CANDIDATES:
            print(f"   - {c}")
        print(f"\n   提示: 请确认 LoRA 文件在 'models/sd15-lora/' 目录下")
        return []
    
    loras = []
    lora_path = Path(LORA_DIR)
    
    print(f"📁 扫描目录: {LORA_DIR}")
    
    for ext in [".safetensors", ".ckpt", ".pt"]:
        for f in lora_path.glob(f"*{ext}"):
            name = f.stem
            size_mb = f.stat().st_size / (1024**2)
            
            # 自动检测标签
            tags = []
            name_lower = name.lower()
            for tag, keywords in LORA_TAGS.items():
                if any(kw.lower() in name_lower for kw in keywords):
                    tags.append(tag)
            
            # 如果没有标签，添加 "uncategorized"
            if not tags:
                tags.append("uncategorized")
            
            # 计算推荐分数
            score = 50
            for key, val in LORA_SCORES.items():
                if key.lower() in name_lower:
                    score = val
                    break
            
            # 提取版本
            version_match = re.search(r'[vV](\d+\.?\d*)', name)
            version = version_match.group(1) if version_match else None
            
            # 使用相对路径
            rel_path = get_relative_path(str(f.absolute()))
            
            loras.append({
                "name": name,
                "filename": f.name,
                "path": rel_path,
                "absolute_path": str(f.absolute()),
                "size_mb": round(size_mb, 2),
                "tags": tags,
                "score": score,
                "version": version,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    
    # 按推荐分数排序
    loras.sort(key=lambda x: x["score"], reverse=True)
    return loras


def generate_index(refresh=False):
    """生成 LoRA 索引 JSON 文件"""
    print("🔍 正在扫描 LoRA 目录...")
    loras = scan_loras()
    
    if not loras:
        print("❌ 没有找到任何 LoRA 文件！")
        print(f"\n💡 请检查:")
        print(f"   1. LoRA 文件是否在 '{LORA_DIR}' 目录下")
        print(f"   2. 文件扩展名是否为 .safetensors, .ckpt, 或 .pt")
        return False
    
    # 按分类组织
    categories = {}
    for tag in LORA_TAGS.keys():
        categories[tag] = [l["name"] for l in loras if tag in l["tags"]]
    categories["uncategorized"] = [l["name"] for l in loras if "uncategorized" in l["tags"]]
    
    # 项目根目录的相对路径
    rel_lora_dir = get_relative_path(LORA_DIR)
    
    index_data = {
        "generated": datetime.now().isoformat(),
        "project_root": PROJECT_ROOT,
        "lora_dir": LORA_DIR,
        "lora_dir_relative": rel_lora_dir,
        "total_loras": len(loras),
        "loras": loras,
        "default": loras[0]["name"] if loras else None,
        "categories": categories,
    }
    
    # 写入 JSON 文件
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ LoRA 索引已生成: {INDEX_FILE}")
    print(f"📊 共找到 {len(loras)} 个 LoRA")
    print(f"🏆 默认推荐: {index_data['default']}")
    print(f"📁 LoRA 目录: {rel_lora_dir}")
    
    # 显示分类统计
    print("\n📁 分类统计:")
    for tag, names in categories.items():
        if names:
            print(f"   {tag}: {len(names)} 个")
    
    # 显示前5个推荐 LoRA
    print("\n⭐ Top 5 推荐 LoRA:")
    for i, l in enumerate(loras[:5]):
        stars = "⭐" * (l["score"] // 20)
        print(f"   {i+1}. {l['name'][:50]} ({l['size_mb']:.1f}MB) {stars}")
    
    return True


def list_loras():
    """列出所有 LoRA（从索引文件读取）"""
    if not os.path.exists(INDEX_FILE):
        print("❌ 索引文件不存在，请先运行: python lora_index.py")
        return
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"\n📚 可用 LoRA 列表 (共 {data['total_loras']} 个):")
    print("=" * 80)
    for i, l in enumerate(data["loras"]):
        stars = "⭐" * (l["score"] // 20)
        default_tag = " 👑" if l["name"] == data["default"] else ""
        print(f"  [{i:2d}] {l['name'][:45]:45s} {l['size_mb']:6.1f}MB  {stars}{default_tag}")
        if l["tags"]:
            print(f"        标签: {', '.join(l['tags'])}")
    
    print(f"\n🏆 默认推荐: {data['default']}")
    print(f"📅 索引生成时间: {data['generated']}")
    print(f"📁 LoRA 目录: {data.get('lora_dir_relative', data['lora_dir'])}")


def main():
    parser = argparse.ArgumentParser(description="SD LoRA 索引管理器")
    parser.add_argument("--refresh", action="store_true", help="强制重新扫描生成索引")
    parser.add_argument("--list", action="store_true", help="列出所有 LoRA")
    
    args = parser.parse_args()
    
    if args.list:
        list_loras()
    elif args.refresh or not os.path.exists(INDEX_FILE):
        generate_index(refresh=args.refresh)
    else:
        print("📋 索引文件已存在，使用 --refresh 强制重新生成")
        list_loras()


if __name__ == "__main__":
    main()