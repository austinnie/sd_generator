# scripts/check_versions.py
"""检查本地已安装的包版本"""

import sys
import subprocess
import importlib.metadata

# 需要检查的包列表
PACKAGES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "huggingface_hub",
    "tokenizers",
    "peft",
    "pillow",
    "numpy",
    "opencv-python",
    "psutil",
    "tqdm",
    "python-docx",
    "piexif",
    "dashscope",
    "tencentcloud-sdk-python",
]

def check_version(package_name: str) -> str:
    """检查单个包的版本"""
    try:
        # 处理 opencv-python 的特殊情况
        import_name = package_name
        if package_name == "opencv-python":
            import_name = "cv2"
        
        version = importlib.metadata.version(package_name)
        return version
    except importlib.metadata.PackageNotFoundError:
        return "❌ 未安装"
    except Exception as e:
        return f"⚠️ 错误: {e}"

def main():
    print("=" * 70)
    print(f"📊 本地包版本检查")
    print(f"🐍 Python 版本: {sys.version}")
    print("=" * 70)
    print()
    
    print(f"{'包名':<25} {'版本':<20} 状态")
    print("-" * 70)
    
    for pkg in PACKAGES:
        version = check_version(pkg)
        status = "✅" if "未安装" not in version and "错误" not in version else ""
        print(f"{pkg:<25} {version:<20} {status}")
    
    print()
    print("=" * 70)
    
    # 检查 pip 版本
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        print(f"📦 pip: {result.stdout.strip()}")
    except:
        pass
    
    print("=" * 70)
    
    # 列出需要升级的包
    print()
    print("📋 检查可升级的包...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=columns"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except:
        pass

if __name__ == "__main__":
    main()