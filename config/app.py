# config/app.py
"""应用配置 - 使用相对路径"""

from dataclasses import dataclass
import os


@dataclass
class Config:
    # ===== 路径配置（相对路径） =====
    model_dir: str = "../models/sd-v1-5"
    lora_dir: str = "../models/sd15-lora"
    output_dir: str = "./output"
    prompts_dir: str = "./prompts"
    
    # ===== 生成参数 =====
    default_steps: int = 25
    default_cfg: float = 7.5
    default_width: int = 512
    default_height: int = 768
    
    # ===== 负面提示词 =====
    default_negative: str = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"


config = Config()


# ===== 工具函数：获取绝对路径 =====
def get_abs_path(relative_path: str) -> str:
    """将相对路径转为绝对路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(base_dir, relative_path))


# ===== 便捷函数 =====
def get_model_dir() -> str:
    return get_abs_path(config.model_dir)

def get_lora_dir() -> str:
    return get_abs_path(config.lora_dir)

def get_output_dir() -> str:
    return get_abs_path(config.output_dir)

def get_prompts_dir() -> str:
    return get_abs_path(config.prompts_dir)