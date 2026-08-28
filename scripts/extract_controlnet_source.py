# scripts/extract_controlnet_source.py
"""提取 ControlNet 源码为文本格式，方便查看和集成"""

import os
import sys
from pathlib import Path

# 两套 ControlNet 路径
CONTROLNET_PATHS = {
    "full": r"E:\SD_OPENVINO\CONTROLNET",
    "markflow": r"E:\SD_OPENVINO\MARKFLOW_4IMAGE\SKILLS\CONTROLNET",
}

# 要提取的文件扩展名
PYTHON_EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.md', '.txt', '.sh', '.bat'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}

def extract_source_code(root_path: str, output_file: str, max_files: int = None):
    """提取目录下所有源码文件到单个文本文件"""
    
    root = Path(root_path)
    if not root.exists():
        print(f"❌ 目录不存在: {root_path}")
        return
    
    print(f"\n📁 扫描目录: {root_path}")
    
    # 收集所有文件
    all_files = []
    for ext in PYTHON_EXTENSIONS:
        all_files.extend(list(root.rglob(f"*{ext}")))
    
    # 过滤掉 __pycache__ 和隐藏文件
    all_files = [f for f in all_files if '__pycache__' not in str(f) and not f.name.startswith('.')]
    
    if max_files:
        all_files = all_files[:max_files]
    
    print(f"📊 找到 {len(all_files)} 个源码文件")
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("=" * 80 + "\n")
        out.write(f"ControlNet 源码提取\n")
        out.write(f"源目录: {root_path}\n")
        out.write(f"文件总数: {len(all_files)}\n")
        out.write("=" * 80 + "\n\n")
        
        for i, filepath in enumerate(all_files, 1):
            rel_path = filepath.relative_to(root)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                out.write("=" * 80 + "\n")
                out.write(f"文件: {rel_path}\n")
                out.write(f"路径: {filepath}\n")
                out.write(f"大小: {filepath.stat().st_size} bytes\n")
                out.write("=" * 80 + "\n\n")
                out.write(content)
                out.write("\n\n")
                
                print(f"  [{i}/{len(all_files)}] ✓ {rel_path}")
                
            except Exception as e:
                out.write(f"⚠️ 读取失败: {e}\n\n")
                print(f"  [{i}/{len(all_files)}] ✗ {rel_path} - {e}")
    
    print(f"\n✅ 源码已保存到: {output_file}")

def compare_versions():
    """比较两套 ControlNet 的架构差异"""
    
    print("=" * 80)
    print("📊 ControlNet 版本对比")
    print("=" * 80)
    
    # 分析 full 版本
    full_root = Path(CONTROLNET_PATHS["full"])
    if full_root.exists():
        full_py = list(full_root.rglob("*.py"))
        full_py = [f for f in full_py if '__pycache__' not in str(f)]
        print(f"\n📁 Full 版本: {CONTROLNET_PATHS['full']}")
        print(f"   Python 文件: {len(full_py)} 个")
        print(f"   主要文件: {', '.join([f.name for f in full_py[:5]])}")
        
        # 检查关键文件
        has_cldm = any('cldm' in str(f).lower() for f in full_py)
        has_ldm = any('ldm' in str(f).lower() for f in full_py)
        has_gradio = any('gradio' in str(f).lower() for f in full_py)
        print(f"   包含 CLDM: {'✅' if has_cldm else '❌'}")
        print(f"   包含 LDM: {'✅' if has_ldm else '❌'}")
        print(f"   包含 Gradio: {'✅' if has_gradio else '❌'}")
    
    # 分析 markflow 版本
    markflow_root = Path(CONTROLNET_PATHS["markflow"])
    if markflow_root.exists():
        markflow_py = list(markflow_root.rglob("*.py"))
        markflow_py = [f for f in markflow_py if '__pycache__' not in str(f)]
        print(f"\n📁 Markflow 版本: {CONTROLNET_PATHS['markflow']}")
        print(f"   Python 文件: {len(markflow_py)} 个")
        print(f"   主要文件: {', '.join([f.name for f in markflow_py])}")
        
        # 检查 skill.py
        skill_file = markflow_root / "skill.py"
        if skill_file.exists():
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
                has_controlnet = 'controlnet' in content.lower()
                has_diffusers = 'diffusers' in content.lower()
                print(f"   skill.py 包含 ControlNet: {'✅' if has_controlnet else '❌'}")
                print(f"   skill.py 包含 Diffusers: {'✅' if has_diffusers else '❌'}")
    
    print("\n" + "=" * 80)
    print("💡 推荐集成: Markflow 版本")
    print("   原因: 轻量、封装好、易集成")
    print("=" * 80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="提取 ControlNet 源码")
    parser.add_argument("--version", choices=["full", "markflow", "both"], 
                        default="both", help="选择版本")
    parser.add_argument("--output", "-o", default="controlnet_source.txt", 
                        help="输出文件")
    parser.add_argument("--max-files", type=int, default=None, 
                        help="最大文件数")
    parser.add_argument("--compare", action="store_true", 
                        help="比较两个版本")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_versions()
        return
    
    if args.version in ["full", "both"]:
        extract_source_code(
            CONTROLNET_PATHS["full"], 
            f"full_{args.output}",
            args.max_files
        )
    
    if args.version in ["markflow", "both"]:
        extract_source_code(
            CONTROLNET_PATHS["markflow"], 
            f"markflow_{args.output}",
            args.max_files
        )

if __name__ == "__main__":
    main()