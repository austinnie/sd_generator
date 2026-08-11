# config/app.py
"""应用配置"""

from dataclasses import dataclass
import os


@dataclass
class Config:
    # ===== 模型路径 =====
    sd15_model_dir: str = "../models/sd-v1-5"        # SD 1.5 模型
    sdxl_model_dir: str = "../models/sdxl"           # SDXL 模型
    
    # ===== LoRA 路径 =====
    sd15_lora_dir: str = "../models/sd15-lora"       # SD 1.5 LoRA
    sdxl_lora_dir: str = "../models/sdxl-lora"       # SDXL LoRA
    
    # ===== 输出和提示词 =====
    output_dir: str = "./output"
    prompts_dir: str = "./prompts"
    
    # ===== 默认生成参数 =====
    default_steps: int = 25
    default_cfg: float = 7.5
    default_width: int = 512
    default_height: int = 768
    
    # ===== 负面提示词 =====
    default_negative: str = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"


config = Config()


# ===== 路径工具函数 =====
def get_project_root() -> str:
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(relative_path: str) -> str:
    """将相对路径转为绝对路径"""
    if os.path.isabs(relative_path):
        return relative_path
    return os.path.normpath(os.path.join(get_project_root(), relative_path))


def get_sd15_model_dir() -> str:
    return resolve_path(config.sd15_model_dir)


def get_sdxl_model_dir() -> str:
    return resolve_path(config.sdxl_model_dir)


def get_sd15_lora_dir() -> str:
    return resolve_path(config.sd15_lora_dir)


def get_sdxl_lora_dir() -> str:
    return resolve_path(config.sdxl_lora_dir)


def get_output_dir() -> str:
    return resolve_path(config.output_dir)


def get_prompts_dir() -> str:
    return resolve_path(config.prompts_dir)