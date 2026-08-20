# core/prompts.py
"""提示词加载 - 支持扁平/分层两种格式"""

import os
import glob
import random
from typing import Dict, List, Optional, Union
import requests  # 别忘了在文件顶部导入

class PromptLoader:
    """提示词加载器 - 支持扁平/分层两种格式"""
    
    def __init__(self, prompts_dir: str):
        # 如果是相对路径，转为绝对路径
        if not os.path.isabs(prompts_dir):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.prompts_dir = os.path.normpath(os.path.join(base, prompts_dir))
        else:
            self.prompts_dir = prompts_dir
        
        self.styles: Dict = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有风格"""
        if not os.path.exists(self.prompts_dir):
            return
        
        for filepath in glob.glob(os.path.join(self.prompts_dir, "**", "*.py"), recursive=True):
            if os.path.basename(filepath).startswith("_"):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                ns = {}
                exec(code, {}, ns)
                if 'STYLE' in ns:
                    self.styles.update(ns['STYLE'])
            except Exception as e:
                print(f"⚠️ 加载失败: {filepath} - {e}")
    
    def list_styles(self) -> List[str]:
        return list(self.styles.keys())
    
    def get_style(self, name: str) -> Dict:
        return self.styles.get(name, {})
    
    def is_hierarchical(self, style: Dict) -> bool:
        """判断是否为分层格式（包含 styles 和 moods）"""
        return "styles" in style and "moods" in style
    
    def get_prompt(self, style: str, index: int = 0) -> Optional[str]:
        """获取指定索引的提示词（支持扁平/分层）"""
        style_data = self.styles.get(style, {})
        if not style_data:
            return None
        
        # 分层格式
        if self.is_hierarchical(style_data):
            subjects = style_data.get("subjects", [])
            styles = style_data.get("styles", [])
            moods = style_data.get("moods", [])
            
            if not subjects or not styles or not moods:
                return None
            
            # 使用索引循环选择
            subject = subjects[index % len(subjects)]
            style_item = styles[(index // len(subjects)) % len(styles)]
            mood = moods[(index // (len(subjects) * len(styles))) % len(moods)]
            
            # 如果有 content_texts，随机选一句添加
            content_texts = style_data.get("content_texts", [])
            if content_texts:
                text = random.choice(content_texts)
                return f"{subject}, {style_item}, {mood}, featuring Chinese characters '{text}' in flowing calligraphy"
            
            return f"{subject}, {style_item}, {mood}"
        
        # 扁平格式
        subjects = style_data.get("subjects", [])
        if not subjects:
            return None
        return subjects[index % len(subjects)]
    
    def get_random_prompt(self, style: str) -> Optional[str]:
        """随机获取提示词（支持扁平/分层）"""
        style_data = self.styles.get(style, {})
        if not style_data:
            return None
        
        # 分层格式
        if self.is_hierarchical(style_data):
            subjects = style_data.get("subjects", [])
            styles = style_data.get("styles", [])
            moods = style_data.get("moods", [])
            
            if not subjects or not styles or not moods:
                return None
            
            subject = random.choice(subjects)
            style_item = random.choice(styles)
            mood = random.choice(moods)
            
            content_texts = style_data.get("content_texts", [])
            if content_texts:
                text = random.choice(content_texts)
                return f"{subject}, {style_item}, {mood}, featuring Chinese characters '{text}' in flowing calligraphy"
            
            return f"{subject}, {style_item}, {mood}"
        
        # 扁平格式
        subjects = style_data.get("subjects", [])
        return random.choice(subjects) if subjects else None
    
    def get_prompt_count(self, style: str) -> int:
        """获取风格可用的提示词组合总数"""
        style_data = self.styles.get(style, {})
        if not style_data:
            return 0
        
        if self.is_hierarchical(style_data):
            subjects = style_data.get("subjects", [])
            styles = style_data.get("styles", [])
            moods = style_data.get("moods", [])
            return len(subjects) * len(styles) * len(moods)
        
        return len(style_data.get("subjects", []))
    
    def get_style_info(self, style: str) -> Dict:
        """获取风格详细信息"""
        style_data = self.styles.get(style, {})
        if not style_data:
            return {}
        
        info = {
            "name": style,
            "folder": style_data.get("folder", ""),
            "type": "hierarchical" if self.is_hierarchical(style_data) else "flat",
            "total_combinations": self.get_prompt_count(style),
        }
        
        if self.is_hierarchical(style_data):
            info["subjects"] = len(style_data.get("subjects", []))
            info["styles"] = len(style_data.get("styles", []))
            info["moods"] = len(style_data.get("moods", []))
            info["has_content_texts"] = bool(style_data.get("content_texts", []))
        else:
            info["subjects"] = len(style_data.get("subjects", []))
        
        return info

    def generate_prompt_with_ollama(self, user_desc: str) -> str:
        """使用当前配置的 Ollama 模型生成提示词"""
        try:
            # 读取当前配置的模型
            from config.app import OLLAMA_MODEL
            
            # 构建系统提示词（这个比鉴赏提示词更偏向“指令性”）
            system_prompt = (
                "你是一个Stable Diffusion提示词专家。请将用户的描述转换为一段高质量的英文AI绘画提示词。"
                "要求：包含主体、环境、光影、画质修饰词，以逗号分隔。只输出提示词，不要解释。"
            )
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"{system_prompt}\n用户描述：{user_desc}",
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return "cat, masterpiece, best quality, 8k"  # 备用
        except Exception as e:
            print(f"⚠️ Ollama 提示词生成失败: {e}")
            return "cat, masterpiece, best quality, 8k"
            