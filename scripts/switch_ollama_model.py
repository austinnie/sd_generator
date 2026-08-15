# scripts/switch_ollama_model.py
"""切换 Ollama 模型工具"""

import os
import sys
import json
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "app.py")


def set_ollama_model(model_name: str):
    """修改 config/app.py 中的 OLLAMA_MODEL"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 找不到 config/app.py: {CONFIG_FILE}")
        return False
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换 OLLAMA_MODEL
    pattern = r'OLLAMA_MODEL = ".*?"'
    if re.search(pattern, content):
        content = re.sub(pattern, f'OLLAMA_MODEL = "{model_name}"', content)
    else:
        # 如果不存在，在 AI_APPRECIATION_ENGINE 后面插入
        insert_pos = content.find('AI_APPRECIATION_ENGINE')
        if insert_pos != -1:
            insert_pos = content.find('\n', insert_pos) + 1
            content = content[:insert_pos] + f'OLLAMA_MODEL = "{model_name}"\n' + content[insert_pos:]
        else:
            content += f'\nOLLAMA_MODEL = "{model_name}"\n'
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 已切换到 Ollama 模型: {model_name}")
    return True


def show_status():
    """显示当前配置"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    model_match = re.search(r'OLLAMA_MODEL = "(.*?)"', content)
    engine_match = re.search(r'AI_APPRECIATION_ENGINE = "(.*?)"', content)
    
    print("\n📊 Ollama 配置状态:")
    print("=" * 50)
    print(f"  鉴赏引擎: {engine_match.group(1) if engine_match else '未配置'}")
    print(f"  当前模型: {model_match.group(1) if model_match else '未配置'}")
    
    # 获取可用模型
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            print(f"\n📦 已安装的 Ollama 模型:")
            for m in models:
                mark = " 👈" if m == (model_match.group(1) if model_match else "") else ""
                print(f"  - {m}{mark}")
    except:
        print(f"\n⚠️ 无法连接到 Ollama，请确保 Ollama 正在运行")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="切换 Ollama 模型")
    parser.add_argument("--set", type=str, help="设置使用的模型名称")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    parser.add_argument("--list", action="store_true", help="列出可用模型")
    
    args = parser.parse_args()
    
    if args.status or (not any(vars(args).values())):
        show_status()
    elif args.set:
        set_ollama_model(args.set)
    elif args.list:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                print("\n📦 已安装的 Ollama 模型:")
                for m in data.get("models", []):
                    print(f"  - {m['name']} ({m.get('size', 'unknown')})")
            else:
                print("❌ 无法获取模型列表")
        except:
            print("❌ 无法连接到 Ollama")