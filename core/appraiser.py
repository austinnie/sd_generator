# core/appraiser.py
"""AI 鉴赏系统"""

import os
import sys
import requests

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ✅ 修改：从 config.app 导入
from config.app import AI_APPRECIATION_ENGINE


class Appraiser:
    """AI 鉴赏器"""
    
    def __init__(self):
        self._blip_processor = None
        self._blip_model = None
        self._blip_loaded = False
    
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
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _get_blip_caption(self, image_path: str) -> str:
        if not self._blip_loaded or self._blip_model is None:
            return None
        try:
            from PIL import Image
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
        try:
            llm_prompt = f"""
你是一位资深的高端手办模型收藏家。请根据以下对这张图片的简短基础描述，写一段40字左右的摄影点评/文案。
要求：
1. 不要去复述图片里有什么（不要堆砌名词）。
2. 重点描写"金属装甲的光泽度"、"机械关节的结构感"或者"整体的精密拼装感"。
3. 语气要像一个懂行的人，不要太像AI。
4. 直接给出点评内容，不要有"描述如下"之类的前缀。

图片简述：{caption}
"""
            print(f"   ⏳ 正在请求 Ollama (qwen2.5:1.5b) 深度分析...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen2.5:1.5b", "prompt": llm_prompt, "stream": False, "temperature": 0.7},
                timeout=45
            )
            if response.status_code == 200:
                result = response.json().get("response", caption).strip()
                print(f"   ✅ LLM 深度解析完成！")
                if len(result) < 5:
                    return caption
                return result
        except Exception as e:
            print(f"   ⚠️ Ollama 连接失败: {e}")
        return None

appraiser = Appraiser()