# scripts/model_index.py
# ==================== 📚 模型索引生成器 ====================
"""
用法:
    python model_index.py              # 生成索引文件
    python model_index.py --refresh    # 强制刷新
    python model_index.py --list       # 列出所有模型
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

# 模型目录候选
MODELS_DIR_CANDIDATES = [
    os.path.join(SD_ROOT, "models", "sd-v1-5"),           # E:\SD_OpenVINO\models\sd-v1-5
    os.path.join(PROJECT_ROOT, "models", "sd-v1-5"),      # E:\SD_OpenVINO\v8_universal_generator\models\sd-v1-5
]

# 找到实际存在的模型目录
MODELS_DIR = None
for candidate in MODELS_DIR_CANDIDATES:
    candidate = os.path.normpath(candidate)
    if os.path.exists(candidate):
        MODELS_DIR = candidate
        break

INDEX_FILE = os.path.join(CURRENT_DIR, "models_index.json")

# ==================== 模型标签映射 ====================
MODEL_TAGS = {
    "realistic": ["realistic", "photo", "real", "henmix", "anytime", "nextphoto", "shm", "zemihr"],
    "anime": ["anime", "mix", "dreamshaper", "fantastic", "ultimix", "girl", "charactermix"],
    "artistic": ["sketch", "oil", "painting", "watercolor", "art", "style"],
    "east_asian": ["asian", "china", "east", "realisticEastAsian", "nexblend", "evalidennia"],
    "portrait": ["portrait", "face", "detail"],
    "landscape": ["landscape", "scenery", "view", "outdoor"],
    "fantasy": ["fantastic", "dream", "shaper", "ultimix"],
    "tiny": ["tiny", "inpainting"],
}

# 模型推荐分数（社区口碑）
MODEL_SCORES = {
    "anytimeRealistic": 95,
    "henmixreal": 92,
    "aiiiii01": 90,
    "nextphoto": 88,
    "realisticmix": 85,
    "DreamShaper": 82,
    "asianrealistic": 80,
    "evalidenniaRealisticEastAsian": 78,
    "zemihr": 75,
    "girlMix": 70,
    "nexblendmix": 68,
    "ultimixFantastic": 65,
    "shmRealistic": 85,
    "real_asia": 80,
    "t3_sdVer3": 75,
}


def get_relative_path(abs_path):
    """将绝对路径转换为相对于项目根目录的路径"""
    abs_path = os.path.normpath(abs_path)
    rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
    # 使用正斜杠统一路径格式（跨平台兼容）
    return rel_path.replace('\\', '/')


def scan_models():
    """扫描模型目录，返回模型信息列表"""
    if not MODELS_DIR:
        print(f"❌ 找不到模型目录！")
        print(f"   请检查以下位置:")
        for c in MODELS_DIR_CANDIDATES:
            print(f"   - {c}")
        print(f"\n   提示: 请确认模型文件在 'models/sd-v1-5/' 目录下")
        return []
    
    models = []
    models_path = Path(MODELS_DIR)
    
    print(f"📁 扫描目录: {MODELS_DIR}")
    
    for ext in [".safetensors", ".ckpt", ".pt"]:
        for f in models_path.glob(f"*{ext}"):
            name = f.stem
            size_gb = f.stat().st_size / (1024**3)
            
            # 自动检测标签
            tags = []
            name_lower = name.lower()
            for tag, keywords in MODEL_TAGS.items():
                if any(kw in name_lower for kw in keywords):
                    tags.append(tag)
            
            # 计算推荐分数
            score = 50
            for key, val in MODEL_SCORES.items():
                if key.lower() in name_lower:
                    score = val
                    break
            
            # 检查是否已转换 OpenVINO
            ov_path = models_path / f"{name}_ov"
            is_ov = ov_path.exists() and ov_path.is_dir()
            
            # 提取模型版本
            version_match = re.search(r'[vV](\d+\.?\d*)', name)
            version = version_match.group(1) if version_match else None
            
            # 使用相对路径
            rel_path = get_relative_path(str(f.absolute()))
            rel_ov_path = get_relative_path(str(ov_path.absolute())) if is_ov else None
            
            models.append({
                "name": name,
                "filename": f.name,
                "path": rel_path,  # 相对路径
                "absolute_path": str(f.absolute()),  # 保留绝对路径作为备用
                "size_gb": round(size_gb, 2),
                "tags": tags,
                "score": score,
                "is_ov": is_ov,
                "ov_path": rel_ov_path,  # 相对路径
                "ov_absolute_path": str(ov_path.absolute()) if is_ov else None,
                "version": version,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    
    # 按推荐分数排序
    models.sort(key=lambda x: x["score"], reverse=True)
    return models


def generate_index(refresh=False):
    """生成索引 JSON 文件"""
    print("🔍 正在扫描模型目录...")
    models = scan_models()
    
    if not models:
        print("❌ 没有找到任何模型文件！")
        print(f"\n💡 请检查:")
        print(f"   1. 模型文件是否在 '{MODELS_DIR}' 目录下")
        print(f"   2. 文件扩展名是否为 .safetensors, .ckpt, 或 .pt")
        return False
    
    # 按分类组织
    categories = {}
    for tag in MODEL_TAGS.keys():
        categories[tag] = [m["name"] for m in models if tag in m["tags"]]
    
    # 项目根目录的相对路径
    rel_models_dir = get_relative_path(MODELS_DIR)
    
    index_data = {
        "generated": datetime.now().isoformat(),
        "project_root": PROJECT_ROOT,  # 项目根目录（用于解析相对路径）
        "models_dir": MODELS_DIR,       # 绝对路径（兼容旧代码）
        "models_dir_relative": rel_models_dir,  # 相对路径
        "total_models": len(models),
        "models": models,
        "default": models[0]["name"] if models else None,
        "categories": categories,
        "legacy_mapping": {
            0: "aiiiii01_v10.safetensors",
            1: "anytimeRealistic_v10.safetensors", 
            2: "henmixrealV10_henmixrealV10.safetensors",
            3: "sd-v1-5-tiny.safetensors",
        }
    }
    
    # 写入 JSON 文件
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 索引已生成: {INDEX_FILE}")
    print(f"📊 共找到 {len(models)} 个模型")
    print(f"🏆 默认推荐: {index_data['default']}")
    print(f"📁 模型目录: {rel_models_dir}")
    
    # 显示分类统计
    print("\n📁 分类统计:")
    for tag, names in categories.items():
        if names:
            print(f"   {tag}: {len(names)} 个")
    
    # 显示前5个推荐模型
    print("\n⭐ Top 5 推荐模型:")
    for i, m in enumerate(models[:5]):
        stars = "⭐" * (m["score"] // 20)
        print(f"   {i+1}. {m['name'][:50]} ({m['size_gb']:.1f}GB) {stars}")
    
    return True


def list_models():
    """列出所有模型（从索引文件读取）"""
    if not os.path.exists(INDEX_FILE):
        print("❌ 索引文件不存在，请先运行: python model_index.py")
        return
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"\n📚 可用模型列表 (共 {data['total_models']} 个):")
    print("=" * 80)
    for i, m in enumerate(data["models"]):
        stars = "⭐" * (m["score"] // 20)
        ov_tag = " [OV]" if m["is_ov"] else ""
        default_tag = " 👑" if m["name"] == data["default"] else ""
        # 显示相对路径
        path_display = m.get("path", m.get("absolute_path", ""))
        print(f"  [{i:2d}] {m['name'][:45]:45s} {m['size_gb']:4.1f}GB  {stars}{ov_tag}{default_tag}")
        if m["tags"]:
            print(f"        标签: {', '.join(m['tags'])}")
            print(f"        路径: {path_display}")
    
    print(f"\n🏆 默认推荐: {data['default']}")
    print(f"📅 索引生成时间: {data['generated']}")
    print(f"📁 模型目录: {data.get('models_dir_relative', data['models_dir'])}")


def main():
    parser = argparse.ArgumentParser(description="SD 模型索引管理器")
    parser.add_argument("--refresh", action="store_true", help="强制重新扫描生成索引")
    parser.add_argument("--list", action="store_true", help="列出所有模型")
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
    elif args.refresh or not os.path.exists(INDEX_FILE):
        generate_index(refresh=args.refresh)
    else:
        print("📋 索引文件已存在，使用 --refresh 强制重新生成")
        list_models()


if __name__ == "__main__":
    main()