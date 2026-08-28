# core/prompts.py
"""提示词加载 - 支持扁平/分层两种格式"""

import os
import glob
import random
import time
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

    # core/prompts.py

    def generate_prompt_with_ollama(
        self, 
        user_desc: str, 
        model: str = None,
        style_hint: str = "general",
        retry: int = 2
    ) -> str:
        """
        使用 Ollama 生成高质量 SD 提示词
        
        参数:
            user_desc: 用户描述（中文/英文）
            model: 指定模型，默认使用 OLLAMA_MODEL
            style_hint: 风格提示 (general/anime/realistic/sketch/mecha)
            retry: 失败重试次数
        
        返回:
            生成的提示词
        """
        from config.app import OLLAMA_MODEL, OLLAMA_HOST
        
        if model is None:
            model = OLLAMA_MODEL
        
        # ===== 风格特定的系统提示词 =====
        SYSTEM_PROMPTS = {
            "general": "你是一个Stable Diffusion提示词专家。将用户描述转换为英文AI绘画提示词。要求：包含主体、环境、光影、画质修饰词，以逗号分隔。只输出提示词，不要解释。",
            "anime": "你是一个动漫风格提示词专家。将用户描述转换为精美的日系动漫绘画提示词。包含角色特征、服装、背景、色彩氛围。只输出英文提示词。",
            "realistic": "你是一个写实摄影提示词专家。将用户描述转换为真实感摄影提示词。包含相机参数、光线、构图、细节质感。只输出英文提示词。",
            "sketch": "你是一个素描/线稿提示词专家。将用户描述转换为铅笔素描或白描风格的提示词。强调线条、留白、黑白对比。只输出英文提示词。",
            "mecha": "你是一个机甲/科幻提示词专家。将用户描述转换为机甲机械风格的提示词。包含机械细节、材质、科技感。只输出英文提示词。",
        }
        
        system_prompt = SYSTEM_PROMPTS.get(style_hint, SYSTEM_PROMPTS["general"])
        
        # ===== 附加质量修饰词（自动追加） =====
        QUALITY_TAGS = {
            "general": "masterpiece, best quality, 8k",
            "anime": "anime style, masterpiece, high quality, vibrant colors, detailed",
            "realistic": "photorealistic, highly detailed, sharp focus, 8k, professional photography",
            "sketch": "pencil sketch, black and white, fine linework, white background, raw art",
            "mecha": "sci-fi, mechanical, intricate details, hyper-detailed, concept art",
        }
        
        quality_tag = QUALITY_TAGS.get(style_hint, QUALITY_TAGS["general"])
        
        # ===== 用户描述增强：如果用户输入太短，自动扩展 =====
        if len(user_desc.strip()) < 5:
            user_desc = f"a beautiful scene with {user_desc}"
        
        # ===== 构建完整 Prompt =====
        full_prompt = f"""{system_prompt}

    用户描述：{user_desc}

    要求：
    1. 提示词用英文，逗号分隔
    2. 包含：主体描述 + 环境/背景 + 光影氛围 + 画质修饰词
    3. 长度控制在 30-80 词之间
    4. 只输出提示词，不要有其他内容

    自动追加质量词：{quality_tag}
    """
        
        # ===== 调用 Ollama =====
        for attempt in range(retry + 1):
            try:
                response = requests.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "temperature": 0.7,
                        "max_tokens": 200,
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    result = response.json().get("response", "").strip()
                    
                    # 清理结果
                    result = result.replace("提示词：", "").replace("Prompt:", "").strip()
                    # 确保有质量词
                    if quality_tag not in result:
                        result = f"{result}, {quality_tag}"
                    
                    # 缓存结果（可选）
                    self._prompt_cache[user_desc] = result
                    
                    return result
                    
            except requests.exceptions.Timeout:
                print(f"   ⚠️ Ollama 超时 (尝试 {attempt+1}/{retry+1})")
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️ 无法连接 Ollama (尝试 {attempt+1}/{retry+1})")
                if attempt == 0:
                    print("   💡 请确保 Ollama 正在运行: ollama serve")
            except Exception as e:
                print(f"   ⚠️ Ollama 错误: {e}")
            
            if attempt < retry:
                time.sleep(2)
        
        # ===== 所有重试失败，返回备用提示词 =====
        fallback = f"{user_desc}, {quality_tag}"
        print(f"   ⚠️ Ollama 不可用，使用备用提示词")
        return fallback
