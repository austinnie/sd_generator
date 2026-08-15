# config/app.py
# ==================== 📋 全局配置中心 ====================
import os
import sys
import json
from pathlib import Path

# ✅ 当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # config/
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)              # sd_generator/

# ==================== 📚 加载模型索引 ====================
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
INDEX_FILE = os.path.join(SCRIPTS_DIR, "models_index.json")

def load_model_index():
    """加载模型索引文件，如果不存在则自动生成"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️ 模型索引不存在，正在自动生成...")
        try:
            import subprocess
            model_index_script = os.path.join(SCRIPTS_DIR, "model_index.py")
            if os.path.exists(model_index_script):
                subprocess.run(
                    [sys.executable, model_index_script],
                    capture_output=True,
                    text=True,
                    cwd=SCRIPTS_DIR
                )
            else:
                print(f"⚠️ 找不到 model_index.py: {model_index_script}")
                return {"models": [], "default": None}
        except Exception as e:
            print(f"⚠️ 自动生成索引失败: {e}")
            return {"models": [], "default": None}
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载索引失败: {e}")
        return {"models": [], "default": None}

MODEL_INDEX = load_model_index()
AVAILABLE_MODELS = MODEL_INDEX.get("models", [])

# ==================== 🔵 模型选择配置 ====================
# 🆕 模型类型: "sd15" | "sdxl"（由 switch_lora.py / switch_model.py 自动管理）
MODEL_TYPE = "sd15"

MODEL_SELECTION_MODE = "smart"  # legacy | smart | manual
MANUAL_MODEL_NAME = None
USE_OPENVINO_MODEL = False
ACTIVE_MODEL = 0

# ==================== 🔴 智能模型选择 ====================
def resolve_model_path():
    """根据配置决定最终使用的模型路径"""
    
    # 1. manual 模式
    if MODEL_SELECTION_MODE == "manual" and MANUAL_MODEL_NAME:
        for m in AVAILABLE_MODELS:
            if MANUAL_MODEL_NAME.lower() in m["name"].lower():
                return resolve_model_path_from_index(m)
        print(f"⚠️ 未找到模型: {MANUAL_MODEL_NAME}，使用默认模型")
    
    # 2. smart 模式
    if MODEL_SELECTION_MODE == "smart":
        if AVAILABLE_MODELS:
            default_name = MODEL_INDEX.get("default")
            if default_name:
                for m in AVAILABLE_MODELS:
                    if m["name"] == default_name:
                        abs_path = resolve_model_path_from_index(m)
                        if abs_path:
                            print(f"🤖 智能推荐: {m['name']} ({m.get('size_gb', 0)}GB)")
                            return abs_path
            first_path = resolve_model_path_from_index(AVAILABLE_MODELS[0])
            if first_path:
                return first_path
    
    # 3. legacy 模式
    legacy_paths = [
        os.path.join(PROJECT_ROOT, "../models/sd-v1-5/aiiiii01_v10.safetensors"),
        os.path.join(PROJECT_ROOT, "../models/sd-v1-5/anytimeRealistic_v10.safetensors"),
        os.path.join(PROJECT_ROOT, "../models/sd-v1-5/henmixrealV10_henmixrealV10.safetensors"),
        os.path.join(PROJECT_ROOT, "../models/sd-v1-5/sd-v1-5-tiny.safetensors"),
    ]
    if 0 <= ACTIVE_MODEL < len(legacy_paths):
        return legacy_paths[ACTIVE_MODEL]
    return legacy_paths[0]

def resolve_model_path_from_index(model_entry):
    """从索引条目解析实际模型路径"""
    if "path" in model_entry and model_entry["path"]:
        abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, model_entry["path"]))
        if os.path.exists(abs_path):
            return abs_path
    if "absolute_path" in model_entry and model_entry["absolute_path"]:
        if os.path.exists(model_entry["absolute_path"]):
            return model_entry["absolute_path"]
    if "filename" in model_entry:
        models_dir = MODEL_INDEX.get("models_dir_relative", "../models/sd-v1-5")
        fallback_path = os.path.normpath(os.path.join(PROJECT_ROOT, models_dir, model_entry["filename"]))
        if os.path.exists(fallback_path):
            return fallback_path
    return None

SD_MODEL_PATH = resolve_model_path()

# ==================== 📚 加载 LoRA 索引 ====================
LORA_INDEX_FILE = os.path.join(SCRIPTS_DIR, "lora_index.json")

def load_lora_index():
    """加载 LoRA 索引文件"""
    if not os.path.exists(LORA_INDEX_FILE):
        print("⚠️ LoRA 索引不存在，正在自动生成...")
        try:
            import subprocess
            lora_index_script = os.path.join(SCRIPTS_DIR, "lora_index.py")
            if os.path.exists(lora_index_script):
                subprocess.run(
                    [sys.executable, lora_index_script],
                    capture_output=True,
                    text=True,
                    cwd=SCRIPTS_DIR
                )
            else:
                print(f"⚠️ 找不到 lora_index.py: {lora_index_script}")
                return {"loras": [], "default": None}
        except Exception as e:
            print(f"⚠️ 自动生成 LoRA 索引失败: {e}")
            return {"loras": [], "default": None}
    
    try:
        with open(LORA_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载 LoRA 索引失败: {e}")
        return {"loras": [], "default": None}

LORA_INDEX = load_lora_index()
AVAILABLE_LORAS = LORA_INDEX.get("loras", [])

# ==================== LoRA 配置 ====================
LORA_ACTIVE_INDICES = [1]  # 例如 [0] 启用第一个
FINAL_LORA_LIST = []

# 从索引中获取 LoRA 路径
def get_lora_path_by_index(idx):
    """根据索引从 LORA_INDEX 获取 LoRA 路径"""
    if not AVAILABLE_LORAS or idx >= len(AVAILABLE_LORAS):
        return None
    lora_entry = AVAILABLE_LORAS[idx]
    if "path" in lora_entry and lora_entry["path"]:
        return os.path.normpath(os.path.join(PROJECT_ROOT, lora_entry["path"]))
    if "absolute_path" in lora_entry:
        return lora_entry["absolute_path"]
    return None

if LORA_ACTIVE_INDICES:
    for idx in LORA_ACTIVE_INDICES:
        path = get_lora_path_by_index(idx)
        if path and os.path.exists(path):
            FINAL_LORA_LIST.append({
                "path": path,
                "weight": 0.8
            })

# ==================== 生成参数 ====================
STEPS = 25
MAX_LIMIT = 768
INPUT_IMAGE_NAME = "input"
DEFAULT_STRENGTH = 0.35
OUTPUT_DIR = "./output"
PROMPTS_DIR = "./prompts"

# ==================== 用户配置管理 ====================
USER_CONFIG_FILE = os.path.join(PROJECT_ROOT, ".user_config.json")


def load_user_config() -> dict:
    """加载用户配置（模型/LoRA 选择）"""
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_user_config(data: dict):
    """保存用户配置"""
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存用户配置失败: {e}")


# ==================== 🎨 AI 鉴赏配置 ====================
AI_APPRECIATION_ENGINE = "llm"  # tag / blip / llm / prompt

# ==================== 📷 消除AI痕迹配置 ====================
REMOVE_AI_TRACES = True
AI_CLEAR_METADATA = True
AI_REALISTIC = True
AI_CAMERA = "sony_a7iv"
AI_STRENGTH = "light"
AI_INJECT_EXIF = False
AI_CHROMATIC_ABERRATION = True
AI_CHROMATIC_STRENGTH = 0.05
AI_REALISTIC_NOISE = False
AI_NOISE_ISO_BASE = 100
AI_NOISE_RANDOMIZE = True
AI_MINOR_CROP = True
AI_CROP_PERCENT = 0.005
AI_FINGERPRINT_OBFUSCATION = False
AI_DISTORTION_STRENGTH = 0.0005

# ==================== 兼容旧代码的 config 对象 ====================
class Config:
    """兼容旧代码的配置对象"""
    def __init__(self):
        self.sd15_model_dir = "../models/sd-v1-5"
        self.sdxl_model_dir = "../models/sdxl"
        self.sd15_lora_dir = "../models/sd15-lora"
        self.sdxl_lora_dir = "../models/sdxl-lora"
        self.output_dir = OUTPUT_DIR
        self.prompts_dir = PROMPTS_DIR
        self.default_steps = STEPS
        self.default_cfg = 7.5
        self.default_width = 512
        self.default_height = 768
        self.default_negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"

config = Config()

# ==================== 导出 ====================
# ==================== 🎨 素描风格检测关键词 ====================
SKETCH_KEYWORDS = [
    "pencil sketch", "line art", "black and white sketch", 
    "graphite drawing", "ink outline", "charcoal portrait",
    "baimiao", "素描", "线稿", "白描", "水墨", "铅笔", "炭笔", "速写"
]

# ==================== 🎨 AI 鉴赏配置 ====================
AI_APPRECIATION_ENGINE = "llm"  # tag / blip / llm / prompt

# ==================== 📷 消除AI痕迹配置 ====================
REMOVE_AI_TRACES = True
AI_CLEAR_METADATA = True
AI_REALISTIC = True
AI_CAMERA = "sony_a7iv"
AI_STRENGTH = "light"
AI_INJECT_EXIF = False
AI_CHROMATIC_ABERRATION = True
AI_CHROMATIC_STRENGTH = 0.05
AI_REALISTIC_NOISE = False
AI_NOISE_ISO_BASE = 100
AI_NOISE_RANDOMIZE = True
AI_MINOR_CROP = True
AI_CROP_PERCENT = 0.005
AI_FINGERPRINT_OBFUSCATION = False
AI_DISTORTION_STRENGTH = 0.0005

__all__ = [
    'config',
    'SD_MODEL_PATH', 'AVAILABLE_MODELS', 'MODEL_INDEX',
    'FINAL_LORA_LIST', 'AVAILABLE_LORAS', 'LORA_INDEX',
    'STEPS', 'MAX_LIMIT', 'OUTPUT_DIR', 'PROMPTS_DIR',
    'MODEL_SELECTION_MODE', 'USE_OPENVINO_MODEL',
    'resolve_model_path', 'resolve_model_path_from_index',
    'get_lora_path_by_index',
    'load_user_config', 'save_user_config',
    'AI_APPRECIATION_ENGINE',  # 🆕
    'REMOVE_AI_TRACES',        # 🆕
    'AI_CLEAR_METADATA',       # 🆕
    'AI_REALISTIC',            # 🆕
    'AI_CAMERA',               # 🆕
    'AI_STRENGTH',             # 🆕
    'AI_INJECT_EXIF',          # 🆕
    'AI_CHROMATIC_ABERRATION', # 🆕
    'AI_CHROMATIC_STRENGTH',   # 🆕
    'AI_REALISTIC_NOISE',      # 🆕
    'AI_NOISE_ISO_BASE',       # 🆕
    'AI_NOISE_RANDOMIZE',      # 🆕
    'AI_MINOR_CROP',           # 🆕
    'AI_CROP_PERCENT',         # 🆕
    'AI_FINGERPRINT_OBFUSCATION', # 🆕
    'AI_DISTORTION_STRENGTH',  # 🆕
    'SKETCH_KEYWORDS',         # 🆕    
]