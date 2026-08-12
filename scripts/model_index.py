# scripts/model_index.py
# ==================== 📚 模型索引生成器（支持 SD1.5 + SDXL） ====================
"""
用法:
    python model_index.py              # 生成索引文件
    python model_index.py --refresh    # 强制刷新
    python model_index.py --list       # 列出所有模型
    python model_index.py --list --type sdxl  # 只列出 SDXL 模型
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

# 🆕 多模型类型配置
MODEL_TYPES = {
    "sd15": {
        "name": "SD1.5",
        "icon": "🟢",
        "dirs": [
            os.path.join(SD_ROOT, "models", "sd-v1-5"),
            os.path.join(PROJECT_ROOT, "models", "sd-v1-5"),
        ],
        "pipeline": "StableDiffusionPipeline",
        "max_resolution": 768,
        "default_steps": 25,
        "fallback_type": None,
    },
    "sdxl": {
        "name": "SDXL",
        "icon": "🔵",
        "dirs": [
            os.path.join(SD_ROOT, "models", "sdxl"),
            os.path.join(PROJECT_ROOT, "models", "sdxl"),
        ],
        "pipeline": "StableDiffusionXLPipeline",
        "max_resolution": 1024,
        "default_steps": 20,
        "fallback_type": "sd15",
    },
}

def find_model_dirs():
    """查找所有存在的模型目录"""
    found = {}
    for model_type, config in MODEL_TYPES.items():
        for candidate in config["dirs"]:
            candidate = os.path.normpath(candidate)
            if os.path.exists(candidate):
                found[model_type] = candidate
                break
    return found

MODEL_DIRS_FOUND = find_model_dirs()
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

MODEL_SCORES = {
    # SD1.5
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
    # SDXL
    "xlAsianRealisticMix": 90,
    "perfectionAsianILXL": 88,
    "sdxl_lightning": 85,
}


def get_relative_path(abs_path):
    """将绝对路径转换为相对于项目根目录的路径"""
    abs_path = os.path.normpath(abs_path)
    rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
    return rel_path.replace('\\', '/')


def scan_models():
    """扫描所有模型目录，返回模型信息列表"""
    if not MODEL_DIRS_FOUND:
        print(f"❌ 找不到任何模型目录！")
        print(f"   请检查以下位置:")
        for model_type, config in MODEL_TYPES.items():
            for c in config["dirs"]:
                print(f"   - {c}")
        return []
    
    models = []
    
    for model_type, models_dir in MODEL_DIRS_FOUND.items():
        config = MODEL_TYPES[model_type]
        print(f"{config['icon']} 扫描目录 [{config['name']}]: {models_dir}")
        
        models_path = Path(models_dir)
        
        for ext in [".safetensors", ".ckpt", ".pt"]:
            for f in models_path.glob(f"*{ext}"):
                name = f.stem
                size_gb = f.stat().st_size / (1024**3)
                
                tags = []
                name_lower = name.lower()
                for tag, keywords in MODEL_TAGS.items():
                    if any(kw in name_lower for kw in keywords):
                        tags.append(tag)
                
                if not tags:
                    tags.append("uncategorized")
                
                score = 50
                for key, val in MODEL_SCORES.items():
                    if key.lower() in name_lower:
                        score = val
                        break
                
                ov_path = models_path / f"{name}_ov"
                is_ov = ov_path.exists() and ov_path.is_dir()
                
                version_match = re.search(r'[vV](\d+\.?\d*)', name)
                version = version_match.group(1) if version_match else None
                
                rel_path = get_relative_path(str(f.absolute()))
                rel_ov_path = get_relative_path(str(ov_path.absolute())) if is_ov else None
                
                models.append({
                    "name": name,
                    "filename": f.name,
                    "model_type": model_type,
                    "model_type_name": config["name"],
                    "model_type_icon": config["icon"],
                    "pipeline": config["pipeline"],
                    "max_resolution": config["max_resolution"],
                    "default_steps": config["default_steps"],
                    "path": rel_path,
                    "absolute_path": str(f.absolute()),
                    "size_gb": round(size_gb, 2),
                    "tags": tags,
                    "score": score,
                    "is_ov": is_ov,
                    "ov_path": rel_ov_path,
                    "ov_absolute_path": str(ov_path.absolute()) if is_ov else None,
                    "version": version,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
    
    models.sort(key=lambda x: (0 if x["model_type"] == "sd15" else 1, -x["score"]))
    return models


def generate_index(refresh=False):
    """生成索引 JSON 文件"""
    print("🔍 正在扫描模型目录...")
    models = scan_models()
    
    if not models:
        print("❌ 没有找到任何模型文件！")
        print(f"\n💡 请检查:")
        print(f"   1. 模型文件是否在正确的目录下")
        print(f"   2. 文件扩展名是否为 .safetensors, .ckpt, 或 .pt")
        return False
    
    categories = {}
    for tag in MODEL_TAGS.keys():
        categories[tag] = [m["name"] for m in models if tag in m["tags"]]
    categories["uncategorized"] = [m["name"] for m in models if "uncategorized" in m["tags"]]
    
    type_groups = {}
    for model_type, config in MODEL_TYPES.items():
        type_models = [m for m in models if m["model_type"] == model_type]
        if type_models:
            type_groups[model_type] = {
                "name": config["name"],
                "icon": config["icon"],
                "count": len(type_models),
                "default": type_models[0]["name"] if type_models else None,
                "models": [m["name"] for m in type_models],
            }
    
    rel_models_dir = {}
    for model_type, models_dir in MODEL_DIRS_FOUND.items():
        rel_models_dir[model_type] = get_relative_path(models_dir)
    
    index_data = {
        "generated": datetime.now().isoformat(),
        "project_root": PROJECT_ROOT,
        "model_dirs": MODEL_DIRS_FOUND,
        "model_dirs_relative": rel_models_dir,
        "total_models": len(models),
        "models": models,
        "default": models[0]["name"] if models else None,
        "default_type": models[0]["model_type"] if models else None,
        "categories": categories,
        "type_groups": type_groups,
        "legacy_mapping": {
            "sd15": {
                0: "aiiiii01_v10.safetensors",
                1: "anytimeRealistic_v10.safetensors", 
                2: "henmixrealV10_henmixrealV10.safetensors",
                3: "sd-v1-5-tiny.safetensors",
            },
            "sdxl": {
                0: "xlAsianRealisticMixNhiPNhChU_v10.safetensors",
                1: "perfectionAsianILXL_v10.safetensors",
                2: "sdxl_lightning_4step.safetensors",
            }
        }
    }
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 索引已生成: {INDEX_FILE}")
    print(f"📊 共找到 {len(models)} 个模型")
    print(f"🏆 默认推荐: {index_data['default']} ({index_data['default_type']})")
    
    print("\n📁 模型类型统计:")
    for model_type, group in type_groups.items():
        print(f"   {group['icon']} {group['name']}: {group['count']} 个")
        if group['default']:
            print(f"      默认: {group['default']}")
    
    print("\n⭐ Top 5 推荐模型:")
    for i, m in enumerate(models[:5]):
        stars = "⭐" * (m["score"] // 20)
        icon = m.get("model_type_icon", "📁")
        print(f"   {i+1}. {icon} {m['name'][:50]} ({m['size_gb']:.1f}GB) {stars}")
    
    return True


def list_models(filter_type=None):
    """列出所有模型（从索引文件读取）"""
    if not os.path.exists(INDEX_FILE):
        print("❌ 索引文件不存在，请先运行: python model_index.py")
        return
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    models = data["models"]
    if filter_type:
        models = [m for m in models if m["model_type"] == filter_type]
        if not models:
            print(f"❌ 没有找到 {filter_type} 类型的模型")
            return
    
    print(f"\n📚 可用模型列表 (共 {len(models)} 个):")
    if filter_type:
        print(f"   🔍 过滤类型: {filter_type}")
    print("=" * 80)
    
    for i, m in enumerate(models):
        stars = "⭐" * (m["score"] // 20)
        ov_tag = " [OV]" if m["is_ov"] else ""
        default_tag = " 👑" if m["name"] == data["default"] else ""
        icon = m.get("model_type_icon", "📁")
        type_name = m.get("model_type_name", "")
        
        print(f"  [{i:2d}] {icon} {m['name'][:45]:45s} {m['size_gb']:4.1f}GB  {stars}{ov_tag}{default_tag}")
        print(f"        类型: {type_name} | 标签: {', '.join(m['tags'])}")
        print(f"        路径: {m.get('path', '')}")
    
    print(f"\n🏆 默认推荐: {data['default']}")
    print(f"📅 索引生成时间: {data['generated']}")


def main():
    parser = argparse.ArgumentParser(description="SD 模型索引管理器（支持 SD1.5 + SDXL）")
    parser.add_argument("--refresh", action="store_true", help="强制重新扫描生成索引")
    parser.add_argument("--list", action="store_true", help="列出所有模型")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="只列出指定类型的模型")
    
    args = parser.parse_args()
    
    if args.list:
        list_models(filter_type=args.type)
    elif args.refresh or not os.path.exists(INDEX_FILE):
        generate_index(refresh=args.refresh)
    else:
        print("📋 索引文件已存在，使用 --refresh 强制重新生成")
        list_models()


if __name__ == "__main__":
    main()