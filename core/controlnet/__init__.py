# core/controlnet/__init__.py
"""
ControlNet 集成模块 - 提供姿态检测和 ControlNet 控制能力
"""

from .skill import Controlnet, CONTROLNET_TYPES

__all__ = ['Controlnet', 'CONTROLNET_TYPES']