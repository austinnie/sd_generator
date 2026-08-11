SD Generator

基于 Stable Diffusion 的命令行图片生成工具 —— 精简、模块化、开箱即用。

一、简介

sd_generator 是从 v8_universal_generator 项目中独立出来的命令行图片生成工具，专门替代 tools/generate.py 的功能。

它保留了核心生成能力，同时提供了更清晰的模块化结构，方便二次开发和定制。

核心能力：

文生图 — 输入提示词，生成图片

图生图 — 基于参考图生成新图片

多模型支持 — 自动识别 SD 1.5 / SDXL

LoRA 加载 — 支持加载 LoRA 权重

提示词库 — 内置 4 个分类的风格提示词

轻量简洁 — 纯命令行，无 GUI 依赖

模型/LoRA 索引管理 — 自动扫描、分类、推荐

智能模型选择 — 支持 smart/legacy/manual 三种模式

二、安装

git clone https://github.com/austinnie/sd_generator.git
cd sd_generator

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

三、快速开始

生成索引（首次使用必需）

扫描并索引所有模型
python scripts/model_index.py --refresh

扫描并索引所有 LoRA
python scripts/lora_index.py --refresh

配置模型路径

编辑 config/app.py：

模型路径
sd15_model_dir: str = "../models/sd-v1-5" # SD 1.5 模型
sdxl_model_dir: str = "../models/sdxl" # SDXL 模型

LoRA 路径
sd15_lora_dir: str = "../models/sd15-lora" # SD 1.5 LoRA
sdxl_lora_dir: str = "../models/sdxl-lora" # SDXL LoRA

生成图片

使用智能推荐的模型生成
python cli.py pure_serene -n 2

指定模型
python cli.py pure_serene -n 1 --model anytimeRealistic

使用 LoRA
python cli.py gallery_elegant -n 1 --lora busty_slider --lora-weight 0.8

交互模式

python main.py

四、工具脚本说明

scripts/model_index.py - 模型索引生成器

自动扫描模型目录，生成索引 JSON 文件，供其他工具使用。

用法：
python scripts/model_index.py # 基本用法
python scripts/model_index.py --refresh # 强制重新扫描
python scripts/model_index.py --list # 列出所有已索引的模型

输出文件：scripts/models_index.json

包含内容：

模型名称、路径、大小

自动识别的标签（realistic/anime/east_asian 等）

推荐评分（0-100）

OpenVINO 转换状态

按分类组织的索引

scripts/lora_index.py - LoRA 索引生成器

自动扫描 LoRA 目录，生成索引 JSON 文件。

用法：
python scripts/lora_index.py # 基本用法
python scripts/lora_index.py --refresh # 强制重新扫描
python scripts/lora_index.py --list # 列出所有已索引的 LoRA

输出文件：scripts/lora_index.json

包含内容：

LoRA 名称、路径、大小

自动识别的标签（mecha/character/clothing 等）

推荐评分（0-100）

版本信息

按分类组织的索引

scripts/switch_model.py - 模型切换工具

切换和管理 Stable Diffusion 模型，支持三种模式。

用法：
python scripts/switch_model.py --status # 显示当前状态
python scripts/switch_model.py --list # 列出所有可用模型
python scripts/switch_model.py --mode smart # 智能模式
python scripts/switch_model.py --mode manual # 手动模式
python scripts/switch_model.py --manual anytimeRealistic # 指定模型
python scripts/switch_model.py --mode legacy # 旧版模式
python scripts/switch_model.py --legacy 1 # 使用编号
python scripts/switch_model.py --set DreamShaper # 设置默认模型
python scripts/switch_model.py --ov # 启用 OpenVINO
python scripts/switch_model.py --no-ov # 禁用 OpenVINO
python scripts/switch_model.py --refresh # 重新生成索引

三种模式说明：

模式 说明 适用场景
smart 使用索引推荐的模型（默认） 大多数情况，自动选择最佳模型
manual 手动指定模型名称 需要精确控制模型时
legacy 使用编号 0-3 选择 兼容旧代码的编号方式

scripts/switch_lora.py - LoRA 切换工具

切换和管理 LoRA 权重。

用法：
python scripts/switch_lora.py --status # 显示当前状态
python scripts/switch_lora.py --list # 列出所有可用 LoRA
python scripts/switch_lora.py --active 0 # 激活指定索引
python scripts/switch_lora.py --set MechaGirlFigure_v1 # 设置默认
python scripts/switch_lora.py --refresh # 重新生成索引

常用 LoRA 索引参考：

索引 名称 分类 说明
0 MechaGirlFigure_v1 mecha 机甲少女（推荐）
1 AMechaSSS mecha 机甲风格
6 eula character 角色 Eula
10 chunli character 角色春丽
17 busty_slider body 身材调整

scripts/organize_output.py - 输出整理工具

将 output 目录中的图片按每 5 张一组整理到子文件夹中。

用法：
python scripts/organize_output.py

功能：

自动检测图片和对应的 .txt 说明文件

每 5 张图片 + 5 个说明文件为一组

移动到 0001/、0002/ 等子文件夹

跳过已整理的文件夹（防止重复）

scripts/test_import.py - 配置测试工具

测试导入配置是否正确，显示当前配置状态。

用法：
python scripts/test_import.py

输出信息：

当前模型路径和名称

可用模型数量

当前激活的 LoRA

Top 5 推荐模型和 LoRA

五、CLI 命令参考

python cli.py <风格名> [选项]

基本选项：

选项 说明 默认值
-n, --count 生成数量 1
--steps 迭代步数 25
--cfg CFG 值 7.5
--width 图片宽度 512
--height 图片高度 768
--seed 随机种子 -1

模型选择选项：

选项 说明
--model, -m 指定模型名称（支持部分匹配）
--model-type 模型类型过滤 (sd15/sdxl)
--list-models 列出所有可用模型

LoRA 选择选项：

选项 说明
--lora, -l LoRA 名称（可多次使用，格式: name@weight）
--list-loras 列出所有可用 LoRA
--no-lora 禁用所有 LoRA

配置管理选项：

选项 说明
--save 保存当前选择为默认配置
--clear 清除默认配置
--show-config 显示当前配置

六、内置风格

风格名 分类 说明
pure_serene base 清纯风格
gallery_elegant gallery 画廊优雅
mecha_blueprint mecha 白模机甲
tiger_sketch sketch 猛虎线稿

添加新风格：在 prompts/ 目录下创建 .py 文件，按照 STYLE 格式定义即可。

七、目录结构

sd_generator/
├── cli.py # 命令行入口
├── main.py # 交互式入口
├── requirements.txt
├── README.md
│
├── config/
│ └── app.py # 配置中心（含智能模型选择）
│
├── core/
│ ├── engine.py # 生成引擎
│ ├── model.py # 模型管理（使用索引）
│ ├── lora.py # LoRA 管理（使用索引）
│ └── prompts.py # 提示词加载
│
├── prompts/ # 提示词库
│ ├── base/
│ ├── gallery/
│ ├── mecha/
│ └── sketch/
│
├── scripts/ # 工具脚本
│ ├── model_index.py # 模型索引生成器
│ ├── lora_index.py # LoRA 索引生成器
│ ├── switch_model.py # 模型切换工具
│ ├── switch_lora.py # LoRA 切换工具
│ ├── organize_output.py # 输出整理工具
│ ├── test_import.py # 配置测试工具
│ ├── models_index.json # 模型索引数据（自动生成）
│ └── lora_index.json # LoRA 索引数据（自动生成）
│
└── output/ # 生成图片输出目录

八、完整工作流示例

1. 首次使用：生成索引
python scripts/model_index.py --refresh
python scripts/lora_index.py --refresh

2. 查看可用资源
python cli.py --list-models
python cli.py --list-loras

3. 配置默认模型和 LoRA
python scripts/switch_model.py --set anytimeRealistic
python scripts/switch_lora.py --active 0

4. 生成图片
python cli.py pure_serene -n 2

5. 临时指定不同配置
python cli.py mecha_blueprint -n 1 --model DreamShaper --lora MechaGirlFigure_v1@0.8

6. 使用多个 LoRA
python cli.py gallery_elegant -n 1 -l eula_v2@0.6 -l busty_slider@0.5

7. 保存当前配置为默认
python cli.py pure_serene --model anytimeRealistic --lora busty_slider@0.7 --save

8. 查看当前配置
python cli.py --show-config

9. 清除默认配置
python cli.py --clear

九、License

MIT License