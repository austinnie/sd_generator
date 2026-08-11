# scripts/code_collect.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
收集项目目录下所有文件内容
用于分享给 AI 诊断问题
"""

import os
import sys
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

# 要收集的文件扩展名
INCLUDE_EXTENSIONS = [".py", ".json", ".txt", ".md", ".yaml", ".yml"]

# 要排除的文件名模式
EXCLUDE_FILES = [
    "code_collect.py",
    "code_package.py",
    "*.pyc",
    "*.pyo",
    "*.log",
]

# ============================================================
# 核心函数
# ============================================================

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent


def should_exclude_dir(dirpath: str) -> bool:
    """判断是否排除该目录"""
    dirname = os.path.basename(dirpath)
    for pattern in EXCLUDE_DIRS:
        if pattern.startswith("*"):
            if dirname.endswith(pattern[1:]):
                return True
        elif dirname == pattern:
            return True
    return False


def should_include_file(filepath: str) -> bool:
    """判断是否包含该文件"""
    filename = os.path.basename(filepath)
    
    # 排除特定文件
    for pattern in EXCLUDE_FILES:
        if pattern.endswith("*"):
            if filename.startswith(pattern[:-1]):
                return False
        elif pattern.startswith("*") and filename.endswith(pattern[1:]):
            return False
        elif filename == pattern:
            return False
    
    # 检查扩展名
    ext = os.path.splitext(filename)[1].lower()
    return ext in INCLUDE_EXTENSIONS


def collect_files(directory: str) -> list:
    """收集目录下所有文件"""
    files = []
    
    for root, dirs, filenames in os.walk(directory):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if not should_exclude_dir(os.path.join(root, d))]
        
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if should_include_file(filepath):
                files.append(filepath)
    
    return sorted(files)


def read_file_content(filepath: str) -> str:
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read()
        except Exception as e:
            return f"[无法读取: {e}]"
    except Exception as e:
        return f"[读取错误: {e}]"


def generate_report(output_file: str = None) -> str:
    """生成收集报告"""
    project_root = get_project_root()
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"project_snapshot_{timestamp}.txt"
    
    print(f"📂 项目目录: {project_root}")
    print(f"📄 输出文件: {output_file}")
    print("=" * 70)
    
    files = collect_files(str(project_root))
    print(f"✅ 找到 {len(files)} 个文件")
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # 头部
        out.write("=" * 80 + "\n")
        out.write("Project Snapshot - 项目快照\n")
        out.write(f"收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"项目目录: {project_root}\n")
        out.write(f"文件总数: {len(files)}\n")
        out.write("=" * 80 + "\n\n")
        
        # 目录结构
        out.write("📁 目录结构:\n")
        out.write("-" * 40 + "\n")
        
        for root, dirs, filenames in os.walk(str(project_root)):
            dirs[:] = [d for d in dirs if not should_exclude_dir(os.path.join(root, d))]
            
            level = root.replace(str(project_root), '').count(os.sep)
            indent = '│   ' * level
            if level > 0:
                out.write(f"{indent}├── {os.path.basename(root)}/\n")
            
            sub_indent = '│   ' * (level + 1)
            valid_files = [f for f in filenames if should_include_file(os.path.join(root, f))]
            for i, filename in enumerate(sorted(valid_files)):
                is_last = (i == len(valid_files) - 1)
                prefix = "└── " if is_last else "├── "
                out.write(f"{sub_indent}{prefix}{filename}\n")
        
        out.write("\n" + "=" * 80 + "\n")
        out.write("📄 文件内容:\n")
        out.write("=" * 80 + "\n\n")
        
        # 每个文件的内容
        for filepath in files:
            rel_path = os.path.relpath(filepath, str(project_root))
            content = read_file_content(filepath)
            
            out.write("\n" + "=" * 80 + "\n")
            out.write(f"📄 文件: {rel_path}\n")
            out.write(f"路径: {filepath}\n")
            out.write("=" * 80 + "\n\n")
            out.write(content)
            out.write("\n\n")
    
    print(f"\n✅ 报告已生成: {output_file}")
    
    # 统计
    py_files = [f for f in files if f.endswith('.py')]
    print(f"\n📊 统计: 总 {len(files)} 个文件, Python {len(py_files)} 个")
    
    return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="收集项目目录下所有文件")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-d", "--dir", help="要收集的目录（默认自动检测）")
    
    args = parser.parse_args()
    
    if args.dir:
        os.chdir(args.dir)
    
    generate_report(args.output)


if __name__ == "__main__":
    main()