# core/appraiser.py
"""AI 鉴赏系统"""

import os
import sys
import requests
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 从 config 导入模型配置
from config.app import AI_APPRECIATION_ENGINE, OLLAMA_MODEL, OLLAMA_HOST, OLLAMA_TEMPERATURE, OLLAMA_MAX_TOKENS


class Appraiser:
    """AI 鉴赏器"""
    
    def __init__(self, ollama_model: str = None):
        """
        初始化鉴赏器
        参数:
            ollama_model: Ollama 模型名称，默认使用 config 中的配置
        """
        self._blip_processor = None
        self._blip_model = None
        self._blip_loaded = False
        # ✅ 使用传入的模型或配置中的默认模型
        self.ollama_model = ollama_model or OLLAMA_MODEL
        self.ollama_host = OLLAMA_HOST
    
    def appraise(self, image_path: str, prompt: str) -> str:
        """对图片进行鉴赏，返回鉴赏文字"""
        engine = AI_APPRECIATION_ENGINE
        
        if engine == "prompt":
            print(f"   📝 鉴赏引擎: 仅使用提示词")
            return prompt
        
        self._ensure_blip_loaded()
        caption = self._get_blip_caption(image_path)
        if not caption:
            caption = prompt
        
        if engine == "llm" and self._llm_available():
            enhanced = self._enhance_with_llm(caption)
            if enhanced:
                return enhanced
        
        return caption
    
    def _ensure_blip_loaded(self):
        if self._blip_loaded:
            return
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            base_blip_path = r"E:\hf_cache\.cache\hub\models--Salesforce--blip-image-captioning-large"
            snapshots_path = os.path.join(base_blip_path, "snapshots")
            if os.path.exists(snapshots_path):
                subfolders = [f for f in os.listdir(snapshots_path) 
                             if os.path.isdir(os.path.join(snapshots_path, f))]
                if subfolders:
                    cached_dir = os.path.join(snapshots_path, subfolders[0])
                    print(f"   📦 加载 BLIP 模型 ({cached_dir})...")
                    self._blip_processor = BlipProcessor.from_pretrained(cached_dir)
                    self._blip_model = BlipForConditionalGeneration.from_pretrained(cached_dir)
                    self._blip_loaded = True
                    print(f"   ✅ BLIP 模型加载完成")
                    return
            print(f"   ⚠️ 本地 BLIP 加载失败")
            self._blip_loaded = False
        except Exception as e:
            print(f"   ⚠️ BLIP 加载失败: {e}")
            self._blip_loaded = False

    def _llm_available(self) -> bool:
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _get_blip_caption(self, image_path: str) -> str:
        if not self._blip_loaded or self._blip_model is None:
            return None
        try:
            image = Image.open(image_path).convert('RGB')
            inputs = self._blip_processor(image, return_tensors="pt")
            out = self._blip_model.generate(
                **inputs, 
                max_length=80, 
                num_beams=3, 
                repetition_penalty=1.1,
                forced_bos_token_id=self._blip_processor.tokenizer.convert_tokens_to_ids("zh")
            )
            caption = self._blip_processor.decode(out[0], skip_special_tokens=True)
            print(f"   📝 BLIP 原始描述: {caption[:60]}...")
            return caption
        except Exception as e:
            print(f"   ⚠️ BLIP 推理失败: {e}")
            return None
    
    def _enhance_with_llm(self, caption: str) -> str:
        """使用 Ollama 增强描述"""
        try:
            # ✅ 根据不同的模型使用不同的 prompt 风格
            model_lower = self.ollama_model.lower()
            
            if "qwen" in model_lower:
                # Qwen 系列：中文能力强
                system_prompt = "你是一位资深的高端手办模型收藏家和艺术评论家。"
                language = "zh"
            elif "phi" in model_lower:
                # Phi 系列：推理能力强，英文好
                system_prompt = "You are an expert art critic and collector of high-end figurines."
                language = "en"
            elif "tinyllama" in model_lower:
                # TinyLlama：轻量级，简单回复
                system_prompt = "你是一位艺术爱好者。"
                language = "zh"
            else:
                system_prompt = "你是一位专业的艺术评论家。"
                language = "zh"
            
            # ✅ 根据语言构建不同的 prompt
            if language == "zh":
                llm_prompt = f"""
{system_prompt}

请根据以下对这张图片的简短基础描述，写一段40字左右的摄影点评/文案。

要求：
1. 不要复述图片里有什么（不要堆砌名词）
2. 重点描写细节质感、光影氛围或整体意境
3. 语气要像专业人士，不要太像AI
4. 直接给出点评内容，不要有前缀

图片简述：{caption}
"""
            else:
                llm_prompt = f"""
{system_prompt}

Based on the following brief description of an image, write a short 30-40 word photography review/caption.

Requirements:
1. Don't just list what's in the image
2. Focus on texture, lighting, atmosphere, or overall artistic impression
3. Sound like a professional, not like an AI
4. Output only the review, no prefixes

Image description: {caption}
"""
            
            print(f"   ⏳ 正在请求 Ollama ({self.ollama_model}) 深度分析...")
            
            # ✅ 使用配置的模型
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": llm_prompt,
                    "stream": False,
                    "temperature": OLLAMA_TEMPERATURE,
                    "max_tokens": OLLAMA_MAX_TOKENS
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json().get("response", caption).strip()
                # 清理可能的重复内容
                if len(result) > 200:
                    result = result[:200] + "..."
                print(f"   ✅ {self.ollama_model} 深度解析完成！")
                if len(result) < 5:
                    return caption
                return result
            else:
                print(f"   ⚠️ Ollama 请求失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Ollama 请求超时 (45秒)")
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ 无法连接到 Ollama，请确保 Ollama 正在运行")
            print(f"   💡 运行: ollama serve")
        except Exception as e:
            print(f"   ⚠️ Ollama 分析失败: {e}")
        return None

    def set_model(self, model_name: str):
        """切换使用的 Ollama 模型"""
        self.ollama_model = model_name
        print(f"   🔄 已切换到 Ollama 模型: {model_name}")
    
    def list_available_models(self) -> list:
        """列出 Ollama 中可用的模型"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []


# ✅ 创建全局实例，从配置读取模型名称
appraiser = Appraiser(ollama_model=OLLAMA_MODEL)