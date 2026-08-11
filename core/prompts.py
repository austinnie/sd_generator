# core/prompts.py
"""提示词加载"""

import os
import glob
import random
from typing import Dict, List, Optional


class PromptLoader:
    """提示词加载器"""
    
    def __init__(self, prompts_dir: str):
        # ✅ 如果是相对路径，转为绝对路径
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
    
    def get_prompt(self, style: str, index: int = 0) -> Optional[str]:
        """获取指定索引的提示词"""
        subjects = self.styles.get(style, {}).get("subjects", [])
        if not subjects:
            return None
        return subjects[index % len(subjects)]
    
    def get_random_prompt(self, style: str) -> Optional[str]:
        """随机获取提示词"""
        subjects = self.styles.get(style, {}).get("subjects", [])
        return random.choice(subjects) if subjects else None
