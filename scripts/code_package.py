# scripts/code_package.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目打包脚本 - 自动打包整个项目
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path

# ============================================================
# 配置
# ============================================================

# 要排除的目录
EXCLUDE_DIRS = [
    "__pycache__",
    "venv",
    "env",
    ".git",
    "output",
    "outputs",
    "logs",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    "*.egg-info",
]

# 要排除的文件扩展名
EXCLUDE_EXTENSIONS = [
    ".pyc", ".pyo", ".pyd",
    ".db", ".sqlite3",
    ".log", ".zip", ".rar", ".7z",
    ".exe", ".dll", ".so", ".pkl",
]

# 要打包的根目录文件扩展名
ROOT_FILE_EXTS = ['.py', '.json', '.txt', '.md', '.yml', '.yaml']


def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent


def should_exclude(name: str, is_dir: bool = False) -> bool:
    """判断是否应该排除"""
    if is_dir:
        for pattern in EXCLUDE_DIRS:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
    else:
        ext = os.path.splitext(name)[1].lower()
        if ext in EXCLUDE_EXTENSIONS:
            return True
    return False


def get_project_name() -> str:
    """获取项目文件夹名"""
    return os.path.basename(get_project_root())


def pack_project(output_dir: str = None):
    """打包整个项目"""
    project_root = get_project_root()
    project_name = get_project_name()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{project_name}_{timestamp}.zip"
    
    if output_dir:
        zip_path = os.path.join(output_dir, zip_filename)
        os.makedirs(output_dir, exist_ok=True)
    else:
        zip_path = os.path.join(project_root, zip_filename)
    
    print("=" * 70)
    print(f"📦 打包项目: {project_name}")
    print(f"📁 项目目录: {project_root}")
    print(f"📄 输出文件: {zip_path}")
    print("=" * 70)
    
    file_count = 0
    added_files = set()
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 处理根目录下的文件
        print("\n📄 根目录文件:")
        for file in os.listdir(project_root):
            if os.path.isfile(os.path.join(project_root, file)):
                if should_exclude(file, is_dir=False):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in ROOT_FILE_EXTS:
                    zipf.write(os.path.join(project_root, file), file)
                    added_files.add(file)
                    file_count += 1
                    print(f"   ✅ {file}")
        
        # 处理子目录
        print("\n📁 子目录:")
        for root, dirs, files in os.walk(project_root):
            if root == str(project_root):
                dirs[:] = [d for d in dirs if not should_exclude(d, is_dir=True)]
                continue
            
            dir_name = os.path.basename(root)
            if should_exclude(dir_name, is_dir=True):
                dirs[:] = []
                continue
            
            for file in files:
                if should_exclude(file, is_dir=False):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, str(project_root))
                
                if arcname in added_files:
                    continue
                
                zipf.write(file_path, arcname)
                added_files.add(arcname)
                file_count += 1
        
        # 统计目录数
        dir_count = len(set([os.path.dirname(f) for f in added_files if '/' in f or '\\' in f]))
        
        print(f"\n📊 打包完成!")
        print(f"   📦 文件: {zip_filename}")
        print(f"   📊 大小: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
        print(f"   📁 目录: {dir_count} 个")
        print(f"   📄 文件: {file_count} 个")
        print("=" * 70)
    
    return zip_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目打包脚本")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("-n", "--name", help="输出文件名（不含扩展名）")
    
    args = parser.parse_args()
    
    try:
        pack_project(args.output)
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消")
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()