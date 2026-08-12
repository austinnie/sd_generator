SD Generator

基于 Stable Diffusion 的命令行图片生成工具 —— 精简、模块化、开箱即用。

## 一、简介

sd_generator 是从 v8_universal_generator 项目中独立出来的命令行图片生成工具，专门替代 tools/generate.py 的功能。

它保留了核心生成能力，同时提供了更清晰的模块化结构，方便二次开发和定制。

**核心能力**：

- 文生图 — 输入提示词，生成图片
- 图生图 — 基于参考图生成新图片
- **多模型支持** — 自动识别 SD 1.5 / SDXL，支持无缝切换
- **LoRA 自动适配** — 根据模型类型自动加载对应的 LoRA
- 提示词库 — 内置 4 个分类的风格提示词
- 轻量简洁 — 纯命令行，无 GUI 依赖
- 模型/LoRA 索引管理 — 自动扫描、分类、推荐
- 智能模型选择 — 支持 smart/legacy/manual 三种模式

## 二、安装

```bash
git clone https://github.com/austinnie/sd_generator.git
cd sd_generator

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

## 三、快速开始

### 生成索引（首次使用必需）

扫描并索引所有模型（自动扫描 SD1.5 和 SDXL）：
```bash
python scripts/model_index.py --refresh
```

扫描并索引所有 LoRA（自动扫描 SD1.5 和 SDXL LoRA）：
```bash
python scripts/lora_index.py --refresh
```

### 配置模型路径

编辑 `config/app.py`：

```python
# 模型类型: "sd15" | "sdxl"
MODEL_TYPE = "sd15"  # 默认 SD1.5

# 模型路径（在 scripts/model_index.py 中配置）
# sd15: ../models/sd-v1-5/
# sdxl: ../models/sdxl/

# LoRA 路径（在 scripts/lora_index.py 中配置）
# sd15: ../models/sd15-lora/
# sdxl: ../models/sdxl-lora/
```

### 切换模型和 LoRA

**切换模型类型**：
```bash
# 切换到 SDXL
python scripts/switch_model.py --type sdxl

# 切换回 SD1.5
python scripts/switch_model.py --type sd15

# 查看当前模型状态
python scripts/switch_model.py --status
```

**切换 LoRA 类型**（自动跟随模型类型）：
```bash
# 切换到 SDXL LoRA（同时更新模型类型）
python scripts/switch_lora.py --type sdxl

# 切换回 SD1.5 LoRA
python scripts/switch_lora.py --type sd15

# 查看当前 LoRA 状态（含各类型 Top 5 推荐）
python scripts/switch_lora.py --status
```

**激活指定 LoRA**：
```bash
# 激活 SDXL 索引 0（aesthetic_anime）
python scripts/switch_lora.py --active 0 --type sdxl

# 激活 SD1.5 索引 0（MechaGirlFigure_v1）
python scripts/switch_lora.py --active 0 --type sd15

# 查看 SDXL LoRA 列表
python scripts/switch_lora.py --list --type sdxl
```

### 生成图片

```bash
# 使用当前模型生成
python cli.py bird_sketch -n 1

# 指定步数
python cli.py bird_sketch -n 1 --steps 20

# 指定模型
python cli.py bird_sketch -n 1 --model anytimeRealistic

# 使用 LoRA
python cli.py gallery_elegant -n 1 --lora eula_v2@0.6 --lora busty_slider@0.5
```

### 交互模式

```bash
python main.py
```

## 四、双模型支持说明

| 特性 | SD1.5 | SDXL |
|------|-------|------|
| 模型目录 | `../models/sd-v1-5/` | `../models/sdxl/` |
| LoRA 目录 | `../models/sd15-lora/` | `../models/sdxl-lora/` |
| Pipeline | `StableDiffusionPipeline` | `StableDiffusionXLPipeline` |
| 推荐步数 | 25 | 20 |
| 最大分辨率 | 768 | 1024 |

**LoRA 自动适配**：当切换模型类型时，LoRA 会自动跟随，确保 SD1.5 的 LoRA 不会加载到 SDXL 上。

## 五、工具脚本说明

### scripts/model_index.py - 模型索引生成器

自动扫描 **SD1.5** 和 **SDXL** 模型目录，生成索引 JSON 文件。

用法：
```bash
python scripts/model_index.py              # 基本用法
python scripts/model_index.py --refresh    # 强制重新扫描
python scripts/model_index.py --list       # 列出所有已索引的模型
python scripts/model_index.py --list --type sdxl  # 只列出 SDXL 模型
```

输出文件：`scripts/models_index.json`

### scripts/lora_index.py - LoRA 索引生成器

自动扫描 **SD1.5** 和 **SDXL** LoRA 目录，生成索引 JSON 文件。

用法：
```bash
python scripts/lora_index.py              # 基本用法
python scripts/lora_index.py --refresh    # 强制重新扫描
python scripts/lora_index.py --list       # 列出所有已索引的 LoRA
python scripts/lora_index.py --list --type sdxl  # 只列出 SDXL LoRA
```

输出文件：`scripts/lora_index.json`

### scripts/switch_model.py - 模型切换工具

切换和管理 Stable Diffusion 模型，支持三种模式。

用法：
```bash
python scripts/switch_model.py --status           # 显示当前状态
python scripts/switch_model.py --list             # 列出所有可用模型
python scripts/switch_model.py --list --type sdxl # 只列出 SDXL 模型
python scripts/switch_model.py --type sdxl        # 切换到 SDXL
python scripts/switch_model.py --type sd15        # 切换到 SD1.5
python scripts/switch_model.py --mode smart       # 智能模式
python scripts/switch_model.py --mode manual      # 手动模式
python scripts/switch_model.py --manual anytimeRealistic  # 指定模型
python scripts/switch_model.py --mode legacy      # 旧版模式
python scripts/switch_model.py --legacy 1         # 使用编号
python scripts/switch_model.py --set DreamShaper  # 设置默认模型
python scripts/switch_model.py --ov               # 启用 OpenVINO
python scripts/switch_model.py --no-ov            # 禁用 OpenVINO
python scripts/switch_model.py --refresh          # 重新生成索引
```

**三种模式说明**：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| smart | 使用索引推荐的模型（默认） | 大多数情况，自动选择最佳模型 |
| manual | 手动指定模型名称 | 需要精确控制模型时 |
| legacy | 使用编号 0-3 选择 | 兼容旧代码的编号方式 |

### scripts/switch_lora.py - LoRA 切换工具

切换和管理 LoRA 权重，**自动匹配模型类型**。

用法：
```bash
python scripts/switch_lora.py --status           # 显示当前状态（含各类型 Top 5）
python scripts/switch_lora.py --list             # 列出所有可用 LoRA
python scripts/switch_lora.py --list --type sdxl # 只列出 SDXL LoRA
python scripts/switch_lora.py --type sdxl        # 切换到 SDXL LoRA
python scripts/switch_lora.py --type sd15        # 切换到 SD1.5 LoRA
python scripts/switch_lora.py --active 0         # 激活指定索引的 LoRA
python scripts/switch_lora.py --active 0 --type sdxl  # 激活 SDXL 索引 0
python scripts/switch_lora.py --set MechaGirlFigure_v1  # 设置默认
python scripts/switch_lora.py --refresh          # 重新生成索引
```

**常用 SD1.5 LoRA 索引参考**：

| 索引 | 名称 | 分类 | 说明 |
|------|------|------|------|
| 0 | MechaGirlFigure_v1 | mecha | 机甲少女（推荐） |
| 1 | AMechaSSS | mecha | 机甲风格 |
| 6 | eula | character | 角色 Eula |
| 10 | chunli | character | 角色春丽 |
| 17 | busty_slider | body | 身材调整 |

**常用 SDXL LoRA 索引参考**：

| 索引 | 名称 | 分类 | 说明 |
|------|------|------|------|
| 0 | aesthetic_anime | style | 动漫美学风格 |
| 1 | anmi_sdxl | style | Anmi 画风 |
| 2 | qipao_sdxl | clothing | 旗袍风格 |

### scripts/organize_output.py - 输出整理工具

将 output 目录中的图片按每 5 张一组整理到子文件夹中。

用法：
```bash
python scripts/organize_output.py
```

### scripts/test_import.py - 配置测试工具

测试导入配置是否正确，显示当前配置状态。

用法：
```bash
python scripts/test_import.py
```

## 六、CLI 命令参考

```bash
python cli.py <风格名> [选项]
```

**基本选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-n, --count` | 生成数量 | 1 |
| `--steps` | 迭代步数 | 25 |
| `--cfg` | CFG 值 | 7.5 |
| `--width` | 图片宽度 | 512 |
| `--height` | 图片高度 | 768 |
| `--seed` | 随机种子 | -1 |

**模型选择选项**：

| 选项 | 说明 |
|------|------|
| `--model, -m` | 指定模型名称（支持部分匹配） |
| `--model-type` | 模型类型过滤 (sd15/sdxl) |
| `--list-models` | 列出所有可用模型 |

**LoRA 选择选项**：

| 选项 | 说明 |
|------|------|
| `--lora, -l` | LoRA 名称（可多次使用，格式: name@weight） |
| `--list-loras` | 列出所有可用 LoRA |
| `--no-lora` | 禁用所有 LoRA |

**配置管理选项**：

| 选项 | 说明 |
|------|------|
| `--save` | 保存当前选择为默认配置 |
| `--clear` | 清除默认配置 |
| `--show-config` | 显示当前配置 |

## 七、内置风格

| 风格名 | 分类 | 说明 |
|--------|------|------|
| pure_serene | base | 清纯风格 |
| gallery_elegant | gallery | 画廊优雅 |
| mecha_blueprint | mecha | 白模机甲 |
| tiger_sketch | sketch | 猛虎线稿 |

添加新风格：在 `prompts/` 目录下创建 `.py` 文件，按照 STYLE 格式定义即可。

## 八、完整工作流示例

```bash
# 1. 首次使用：生成索引
python scripts/model_index.py --refresh
python scripts/lora_index.py --refresh

# 2. 查看可用资源
python scripts/switch_model.py --list
python scripts/switch_lora.py --status

# 3. 切换到 SDXL
python scripts/switch_model.py --type sdxl
python scripts/switch_lora.py --type sdxl

# 4. 激活 SDXL LoRA（查看列表后选择）
python scripts/switch_lora.py --list --type sdxl
python scripts/switch_lora.py --active 0 --type sdxl

# 5. 生成图片
python cli.py bird_sketch -n 1

# 6. 切换回 SD1.5
python scripts/switch_model.py --type sd15
python scripts/switch_lora.py --type sd15
python scripts/switch_lora.py --active 0 --type sd15

# 7. 生成图片
python cli.py bird_sketch -n 1

# 8. 临时指定不同配置
python cli.py mecha_blueprint -n 1 --model DreamShaper --lora MechaGirlFigure_v1@0.8

# 9. 使用多个 LoRA
python cli.py gallery_elegant -n 1 -l eula_v2@0.6 -l busty_slider@0.5

# 10. 查看当前配置
python cli.py --show-config
```

## 九、目录结构

```
sd_generator/
├── cli.py                 # 命令行入口
├── main.py                # 交互式入口
├── requirements.txt
├── README.md
│
├── config/
│   └── app.py            # 配置中心（含智能模型选择）
│
├── core/
│   ├── engine.py         # 生成引擎
│   ├── model.py          # 模型管理（支持 SD1.5/SDXL）
│   ├── lora.py           # LoRA 管理（自动匹配类型）
│   └── prompts.py        # 提示词加载
│
├── prompts/              # 提示词库
│   ├── base/
│   ├── gallery/
│   ├── mecha/
│   └── sketch/
│
├── scripts/              # 工具脚本
│   ├── model_index.py    # 模型索引生成器（双模型）
│   ├── lora_index.py     # LoRA 索引生成器（双模型）
│   ├── switch_model.py   # 模型切换工具（双模型）
│   ├── switch_lora.py    # LoRA 切换工具（双模型）
│   ├── organize_output.py # 输出整理工具
│   ├── test_import.py    # 配置测试工具
│   ├── models_index.json # 模型索引数据（自动生成）
│   └── lora_index.json   # LoRA 索引数据（自动生成）
│
└── output/               # 生成图片输出目录
```

## 十、License

MIT License