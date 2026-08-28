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

### 配置 API Key（可选）
创建 .env 文件（不要提交到 Git）：
```
env
# ==================== 图像生成 API 配置 ====================
# 默认提供商: local | tongyi | yige | hunyuan | huggingface
IMAGE_API_PROVIDER=local

# ==================== 通义万相（阿里云） ====================
# 注册: https://dashscope.console.aliyun.com/
# 免费额度: 2000 张
TONGYI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TONGYI_MODEL=wan2.1-t2i-plus
# 可选模型: wan2.1-t2i-plus, qwen-image3.0-pro, qwen-image-max, wan2.1-t2i-turbo

# ==================== 文心一格（百度） ====================
# 注册: https://console.bce.baidu.com/ai/#/ai/yige/app/list
# 免费额度: 200 张/月
YIGE_API_KEY=xxxxxxxxxxxxxxxx
YIGE_SECRET_KEY=xxxxxxxxxxxxxxxx

# ==================== 腾讯混元 ====================
# 注册: https://cloud.tencent.com/product/hunyuan
# 免费额度: 50 张
HUNYUAN_SECRET_ID=xxxxxxxxxxxxxxxx
HUNYUAN_SECRET_KEY=xxxxxxxxxxxxxxxx

# ==================== HuggingFace（完全免费） ====================
# 注册: https://huggingface.co/
# 获取 Token: https://huggingface.co/settings/tokens
# 免费额度: 无限（限速）
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HF_MODEL=sdxl
# 可选: sdxl, sd3, flux, sd15
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

## 三.五、🤖 动态提示词生成（AI 辅助创作）

`dynamic_prompt` 风格可以与 Ollama 配合，根据您的自然语言描述自动生成高质量的 SD 提示词。

### 使用场景
- 不知道怎么写提示词？用中文描述画面即可
- 想快速尝试不同风格？一句话生成多种变体
- 灵感枯竭时？让 AI 帮你扩展创意

### 使用方法

```bash
# 进入动态提示词模式
python cli.py dynamic_prompt
```

### 交互流程示例：
```text
🤖 Ollama 动态提示词生成模式
==================================================
💡 可选的风格提示:
   [general]  通用 - 适合大多数场景
   [anime]    动漫 - 日系插画风格
   [realistic]写实 - 摄影风格
   [sketch]   素描 - 线稿/白描风格
   [mecha]    机甲 - 科幻机械风格
==================================================
请选择风格提示 (回车默认 general): realistic

使用哪个 Ollama 模型 (回车默认 qwen2.5:1.5b): 

💬 请输入画面描述: 一个穿着白色连衣裙的女孩，站在向日葵花田里，夕阳照在她脸上

⏳ 正在用 qwen2.5:1.5b 生成提示词...

✅ 生成的提示词:
   📝 a young woman in a flowing white dress, standing in a sunflower field, golden sunset light illuminating her face, warm orange and yellow tones, soft bokeh background, photorealistic, highly detailed, sharp focus, 8k, professional photography

是否使用此提示词生成? (y/n，回车=y): y

🎨 开始生成...
```

### 一键生成（非交互模式）

```bash
# 直接指定描述和风格，一步生成
python cli.py dynamic_prompt --prompt "赛博朋克风格的机甲少女" --style-hint mecha -n 1
```
注意：动态提示词模式需要 Ollama 在后台运行 (ollama serve)。如果 Ollama 不可用，会自动降级为备用提示词。


### 可选的风格提示参数

| 参数值 | 说明 | 适用场景 |
|--------|------|----------|
| `general` | 通用风格 | 大多数场景（默认） |
| `anime` | 动漫风格 | 日系插画、二次元 |
| `realistic` | 写实风格 | 摄影、写实人像 |
| `sketch` | 素描风格 | 线稿、白描、铅笔素描 |
| `mecha` | 机甲风格 | 科幻、机械、赛博朋克 |


### 命令速查

| 模式 | 命令 | 说明 |
|------|------|------|
| 交互模式 | `python cli.py dynamic_prompt` | 完整对话体验，适合探索 |
| 非交互模式 | `python cli.py dynamic_prompt --prompt "描述"` | 直接生成，默认 general 风格 |
| 指定风格 | `python cli.py dynamic_prompt --prompt "描述" --style-hint mecha` | 指定动漫/写实/素描/机甲风格 |
| 完整参数 | `python cli.py dynamic_prompt --prompt "描述" --style-hint anime --steps 30 -n 1` | 同时指定步数和数量 |

**示例**：

```bash
# 交互模式 - 完整对话体验
python cli.py dynamic_prompt

# 非交互模式 - 直接生成
python cli.py dynamic_prompt --prompt "穿着白色连衣裙的女孩在向日葵花田里"

# 指定风格
python cli.py dynamic_prompt --prompt "机甲少女在赛博朋克城市" --style-hint mecha

# 指定步数等其他参数
python cli.py dynamic_prompt --prompt "夕阳下的武士" --style-hint anime --steps 30 -n 1
```

### 推荐的 Ollama 模型

| 模型 | 推荐度 | 说明 |
|------|--------|------|
| `qwen2.5:1.5b` | ⭐⭐⭐⭐⭐ | 轻量快速，中文理解最佳 |
| `qwen2.5:7b` | ⭐⭐⭐⭐ | 质量更高，需更多资源 |
| `deepseek-r1:7b` | ⭐⭐⭐⭐ | 推理能力强，适合复杂描述 |
| `phi` | ⭐⭐⭐ | 英文能力强 |
| `tinyllama` | ⭐⭐ | 最轻量，速度最快 |

### 目录结构

```text
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
│ ├── model.py # 模型管理（支持 SD1.5/SDXL）
│ ├── lora.py # LoRA 管理（自动匹配类型）
│ ├── prompts.py # 提示词加载
│ ├── appraiser.py # AI 图像鉴赏（Ollama）
│ ├── postprocessor.py # 消除 AI 痕迹
│ ├── pipeline.py # Pipeline 管理
│ └── api_engines/ # API 图像生成引擎
│ ├── tongyi.py # 通义万相
│ ├── yige.py # 文心一格
│ ├── hunyuan.py # 腾讯混元
│ └── huggingface.py # HuggingFace
│
├── prompts/ # 提示词库
│ ├── base/ # 基础风格
│ ├── gallery/ # 画廊/展示风格
│ ├── mecha/ # 机甲/科幻风格
│ ├── portrait/ # 人像/摄影风格
│ ├── sketch/ # 素描/线稿风格
│ ├── anime/ # 动漫风格
│ ├── chinese/ # 国风/水墨风格
│ ├── animals/ # 动物/生肖风格
│ ├── zodiac/ # 十二生肖
│ └── dynamic_prompt.py # 🤖 触发 Ollama 动态生成模式
│
├── scripts/ # 工具脚本
│ ├── model_index.py # 模型索引生成器（双模型）
│ ├── lora_index.py # LoRA 索引生成器（双模型）
│ ├── switch_model.py # 模型切换工具（双模型）
│ ├── switch_lora.py # LoRA 切换工具（双模型）
│ ├── switch_ollama_model.py # Ollama 模型切换工具
│ ├── organize_output.py # 输出整理工具
│ ├── test_import.py # 配置测试工具
│ ├── remove_clothes.py # 衣服移除独立脚本
│ ├── models_index.json # 模型索引数据（自动生成）
│ └── lora_index.json # LoRA 索引数据（自动生成）
│
├── utils/ # 工具模块
│ ├── doc_generator.py # Word 文档生成
│ ├── exif_injector.py # EXIF 注入
│ ├── imagemeta_cleaner.py # 元数据清理
│ ├── logger.py # 日志
│ ├── photo_realistic.py # 照片真实化
│ └── watermark.py # 水印处理
│
├── output/ # 生成图片输出目录
└── .env # API Key 配置（不提交到 Git）
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


##五、云端 API 图像生成
支持 4 种云端图像生成 API，可与本地 SD 无缝切换。

### API 提供商对比

| API | 免费额度 | 速度 | 中文支持 | 注册难度 |
|---|---|---|---|---|
| 通义万相（阿里云） | 2000 张 | 快 | ⭐⭐⭐⭐⭐ | 需实名认证 |
| 文心一格（百度） | 200 张/月 | 快 | ⭐⭐⭐⭐⭐ | 需实名认证 |
| 腾讯混元 | 50 张 | 快 | ⭐⭐⭐⭐⭐ | 需申请 |
| HuggingFace | 无限（限速） | 慢 | ⭐⭐ | 简单 |


### API 命令
```bash
# 通义万相（阿里云）
python cli.py mecha_glow -n 1 --api tongyi --steps 20

# 文心一格（百度）
python cli.py mecha_glow -n 1 --api yige --steps 20

# 腾讯混元
python cli.py mecha_glow -n 1 --api hunyuan --steps 20

# HuggingFace（完全免费）
python cli.py mecha_glow -n 1 --api huggingface --steps 20

# 切换回本地 SD
python cli.py mecha_glow -n 1 --api local --steps 20

# 查看所有可用 API
python cli.py --list-apis

# 查看当前配置
python cli.py --show-config
```

### 通义万相模型选择

| 模型 | 价格（元/张） | 质量 | 推荐场景 |
|---|---|---|---|
| `wan2.1-t2i-turbo` | ¥0.04-0.06 | ⭐⭐⭐ | 快速测试 |
| `wan2.1-t2i-plus` | ¥0.06-0.10 | ⭐⭐⭐⭐ | 日常使用（推荐） |
| `qwen-image-plus` | ¥0.08-0.12 | ⭐⭐⭐⭐ | 平衡选择 |
| `qwen-image3.0-pro` | ¥0.10-0.16 | ⭐⭐⭐⭐⭐ | 高质量需求 |
| `qwen-image-max` | ¥0.12-0.20 | ⭐⭐⭐⭐⭐ | 最高质量 |


### 配置文件 `.env` 说明

| 变量 | 说明 | 示例 |
|---|---|---|
| `IMAGE_API_PROVIDER` | 默认提供商 | `local` / `tongyi` / `yige` / `hunyuan` / `huggingface` |
| `TONGYI_API_KEY` | 通义万相 API Key | `sk-xxx...` |
| `TONGYI_MODEL` | 通义万相模型 | `wan2.1-t2i-plus` |
| `YIGE_API_KEY` | 文心一格 API Key | `xxx...` |
| `YIGE_SECRET_KEY` | 文心一格 Secret Key | `xxx...` |
| `HUNYUAN_SECRET_ID` | 腾讯混元 Secret ID | `xxx...` |
| `HUNYUAN_SECRET_KEY` | 腾讯混元 Secret Key | `xxx...` |
| `HF_API_TOKEN` | HuggingFace Token | `hf_xxx...` |
| `HF_MODEL` | HuggingFace 模型 | `sdxl` / `sd3` / `flux` / `sd15` |

## 六、工具脚本说明

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

切换和管理 LoRA 权重，自动匹配模型类型。

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


### scripts/switch_ollama_model.py - Ollama 模型切换工具

切换 AI 鉴赏使用的 Ollama 模型。

用法：
```bash
python scripts/switch_ollama_model.py --status    # 显示当前状态
python scripts/switch_ollama_model.py --list      # 列出已安装的模型
python scripts/switch_ollama_model.py --set qwen2.5:7b  # 切换到指定模型
python scripts/switch_ollama_model.py --recommended  # 显示推荐模型
```

### 推荐的 Ollama 模型

| 模型 | 说明 | 下载命令 |
|---|---|---|
| `qwen2.5:1.5b` | 轻量，速度快 | `ollama pull qwen2.5:1.5b` |
| `qwen2.5:7b` | 中文理解最佳（推荐） | `ollama pull qwen2.5:7b` |
| `deepseek-r1:7b` | 推理能力强 | `ollama pull deepseek-r1:7b` |
| `phi:latest` | 英文能力强 | `ollama pull phi` |
| `tinyllama:latest` | 最轻量 | `ollama pull tinyllama` |

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

## 七、CLI 命令参考

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

**API 选择选项**：

| 选项 | 说明 | 
|------|------|
| `--api`	| 使用云端 API 生成 (tongyi/yige/hunyuan/huggingface)| 
| `-list-apis`	| 列出所有可用的 API 提供商| 

**配置管理选项**：

| 选项 | 说明 |
|------|------|
| `--save` | 保存当前选择为默认配置 |
| `--clear` | 清除默认配置 |
| `--show-config` | 显示当前配置 |

## 八、内置风格

| 风格名 | 分类 | 说明 |
|--------|------|------|
| pure_serene | base | 清纯风格 |
| gallery_elegant | gallery | 画廊优雅 |
| mecha_blueprint | mecha | 白模机甲 |
| tiger_sketch | sketch | 猛虎线稿 |

添加新风格：在 `prompts/` 目录下创建 `.py` 文件，按照 STYLE 格式定义即可。

## 九、完整工作流示例

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

# 8. 使用云端 API 生成
python cli.py mecha_glow -n 1 --api tongyi --steps 20

# 9. 临时指定不同配置
python cli.py mecha_blueprint -n 1 --model DreamShaper --lora MechaGirlFigure_v1@0.8

# 10. 使用多个 LoRA
python cli.py gallery_elegant -n 1 -l eula_v2@0.6 -l busty_slider@0.5

# 11. 查看当前配置
python cli.py --show-config
```

## 十、目录结构

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
│   ├── prompts.py        # 提示词加载
│   ├── appraiser.py      # AI 图像鉴赏（Ollama）
│   ├── postprocessor.py  # 消除 AI 痕迹
│   ├── pipeline.py       # Pipeline 管理
│   └── api_engines/      # API 图像生成引擎
│       ├── tongyi.py     # 通义万相
│       ├── yige.py       # 文心一格
│       ├── hunyuan.py    # 腾讯混元
│       └── huggingface.py # HuggingFace
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
│   ├── switch_ollama_model.py # Ollama 模型切换工具
│   ├── organize_output.py # 输出整理工具
│   ├── test_import.py    # 配置测试工具
│   ├── models_index.json # 模型索引数据（自动生成）
│   └── lora_index.json   # LoRA 索引数据（自动生成）
│
├── utils/                # 工具模块
│   ├── doc_generator.py  # Word 文档生成
│   ├── exif_injector.py  # EXIF 注入
│   ├── imagemeta_cleaner.py # 元数据清理
│   ├── logger.py         # 日志
│   ├── photo_realistic.py # 照片真实化
│   └── watermark.py      # 水印处理
│
├── output/               # 生成图片输出目录
└── .env                  # API Key 配置（不提交到 Git）
```

## 十一、License

MIT License
