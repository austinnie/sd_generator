import os
import shutil
from pathlib import Path

# ==================== 核心配置 ====================
# 明确指定要整理的 output 目录位置
# 相对于 scripts 文件夹所在的项目根目录
TARGET_OUTPUT_RELATIVE = os.path.join("tools", "output")


def organize_output(output_root):
    """
    整理输出目录：
    1. 遍历 output_root 下所有的文件夹和子文件夹。
    2. 找到所有的图片文件 (.png, .jpg, .jpeg) 和对应的 .txt 文件。
    3. 按每 5 张图片 + 5 个对应 txt 为一组，移动到新的子文件夹中。
    4. 如果是已经分组 (0001, 0002) 的文件夹，则跳过，防止重复整理。
    """
    
    # 支持的图片扩展名
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    
    if not os.path.exists(output_root):
        print(f"❌ 错误：找不到目录 {output_root}")
        print(f"💡 请确认 E:\\SD_OpenVINO\\v8_universal_generator\\tools\\output 是否存在。")
        return

    print(f"\n📁 开始整理: {output_root}")

    # 遍历 output 目录下的所有根任务文件夹（如 "运动人像_女子棒球_20260806_003938"）
    for folder_name in os.listdir(output_root):
        task_folder = os.path.join(output_root, folder_name)
        
        if not os.path.isdir(task_folder):
            continue

        # 如果里面已经有 0001, 0002 等文件夹，说明已经整理过了，跳过
        already_organized = any(
            p.is_dir() and p.name.isdigit() 
            for p in Path(task_folder).iterdir()
        )
        if already_organized:
            print(f"⏭️ 跳过已整理的任务: {folder_name}")
            continue

        print(f"\n📂 正在处理任务: {folder_name}")

        # 1. 扫描任务文件夹下的所有文件
        all_files = {}
        for root, dirs, files in os.walk(task_folder):
            for file in files:
                file_path = os.path.join(root, file)
                base_name, ext = os.path.splitext(file)

                # 判断是否为图片
                if ext.lower() in IMAGE_EXTENSIONS:
                    # 将图片路径存入字典，键为文件名（不含扩展名）
                    all_files[base_name] = {
                        'img': file_path,
                        'txt': None
                    }
                # 判断是否为对应的 txt 文件
                elif ext.lower() == '.txt':
                    # 尝试匹配对应的图片（如果之前已经扫描到了这张图的 base_name）
                    if base_name in all_files:
                        all_files[base_name]['txt'] = file_path

        # 提取所有有效配对（至少有图片，TXT可有可无）
        valid_pairs = [v for k, v in all_files.items() if v['img']]
        
        # 按图片名称排序（保证顺序一致）
        valid_pairs.sort(key=lambda x: os.path.basename(x['img']))

        if not valid_pairs:
            print(f"   ⚠️ 未找到图片文件，跳过。")
            continue

        total_images = len(valid_pairs)
        print(f"   ✅ 找到 {total_images} 张图片及对应的说明文件。")

        # 2. 开始分组：每 5 个一组
        BATCH_SIZE = 5
        for i in range(0, total_images, BATCH_SIZE):
            batch = valid_pairs[i : i + BATCH_SIZE]
            batch_index = (i // BATCH_SIZE) + 1
            subfolder_name = f"{batch_index:04d}" # 例如 0001, 0002
            subfolder_path = os.path.join(task_folder, subfolder_name)

            # 创建目标子文件夹
            os.makedirs(subfolder_path, exist_ok=True)

            # 移动文件
            for item in batch:
                # 移动图片
                src_img = item['img']
                dst_img = os.path.join(subfolder_path, os.path.basename(src_img))
                shutil.move(src_img, dst_img)
                
                # 移动对应的 txt（如果存在）
                if item['txt'] and os.path.exists(item['txt']):
                    src_txt = item['txt']
                    dst_txt = os.path.join(subfolder_path, os.path.basename(src_txt))
                    shutil.move(src_txt, dst_txt)

            print(f"   📁 已创建子文件夹 {subfolder_name}，放入 {len(batch)} 组图文。")

    print(f"\n✅ 所有历史文件夹整理完成！")


if __name__ == "__main__":
    print("=== 🔄 图文分组整理工具 ===")
    
    # 🛡️ 定位脚本所在的目录 (scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 根据脚本目录推断项目根目录 (因为 scripts 在项目根目录下)
    project_root = os.path.dirname(script_dir)
    
    # 拼接出 tools/output 的绝对路径
    OUTPUT_ROOT = os.path.join(project_root, TARGET_OUTPUT_RELATIVE)
        
    print(f"📁 目标输出目录: {OUTPUT_ROOT}")
    print("="*50)
    
    organize_output(OUTPUT_ROOT)