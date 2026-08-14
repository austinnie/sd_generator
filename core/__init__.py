# core/__init__.py
from .engine import GenerationEngine
from .model import ModelManager
from .prompts import PromptLoader
from .lora import LoraManager
from .appraiser import Appraiser          # 🆕
from .postprocessor import remove_ai_traces  # 🆕

__all__ = [
    'GenerationEngine', 
    'ModelManager', 
    'PromptLoader', 
    'LoraManager',
    'Appraiser',           # 🆕
    'remove_ai_traces',    # 🆕
]