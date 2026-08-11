# SD Generator

基于 Stable Diffusion 的命令行图片生成工具 —— 精简、模块化、开箱即用。

---

## 简介

`sd_generator` 是从 `v8_universal_generator` 项目中独立出来的命令行图片生成工具，专门替代 `tools/generate.py` 的功能。

它保留了核心生成能力，同时提供了更清晰的模块化结构，方便二次开发和定制。

### 核心能力

- 文生图 — 输入提示词，生成图片
- 图生图 — 基于参考图生成新图片
- 多模型支持 — 自动识别 SD 1.5 / SDXL
- LoRA 加载 — 支持加载 LoRA 权重
- 提示词库 — 内置 4 个分类的风格提示词
- 轻量简洁 — 纯命令行，无 GUI 依赖

---

## 安装

```bash
git clone https://github.com/austinnie/sd_generator.git
cd sd_generator

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

---

## 快速开始

### 1. 配置模型路径

编辑 `config/app.py`：

```python
# 模型路径
sd15_model_dir: str = "../models/sd-v1-5"      # SD 1.5 模型
sdxl_model_dir: str = "../models/sdxl"         # SDXL 模型

# LoRA 路径
sd15_lora_dir: str = "../models/sd15-lora"     # SD 1.5 LoRA
sdxl_lora_dir: str = "../models/sdxl-lora"     # SDXL LoRA
```

### 2. 生成图片

```bash
# 文生图（自动选择模型）
python cli.py pure_serene -n 2

# 指定模型类型
python cli.py pure_serene -n 1 --model-type sdxl

# 指定具体模型
python cli.py gallery_elegant -n 1 --model perfectionAsianILXL_v10.safetensors

# 图生图
python cli.py mecha_blueprint -n 1 --img2img --input photo.jpg

# 带 LoRA
python cli.py gallery_elegant -n 1 --lora busty_slider --lora-weight 0.8
```

### 3. 交互模式

```bash
python main.py
```

---

## CLI 命令参考

```bash
python cli.py <风格名> [选项]
```

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-n, --count` | 生成数量 | 1 |
| `--steps` | 迭代步数 | 25 |
| `--cfg` | CFG 值 | 7.5 |
| `--width` | 图片宽度 | 512 |
| `--height` | 图片高度 | 768 |
| `--seed` | 随机种子 | -1 |
| `--model` | 指定模型名称 | 自动选择 |
| `--model-type` | 模型类型 (sd15/sdxl) | 自动 |
| `--lora` | LoRA 名称 | 无 |
| `--lora-weight` | LoRA 权重 | 1.0 |
| `--img2img` | 图生图模式 | 否 |
| `--input` | 图生图输入图片 | 无 |

---

## 内置风格

| 风格名 | 分类 | 说明 |
|--------|------|------|
| `pure_serene` | base | 清纯风格 |
| `gallery_elegant` | gallery | 画廊优雅 |
| `mecha_blueprint` | mecha | 白模机甲 |
| `tiger_sketch` | sketch | 猛虎线稿 |

添加新风格：在 `prompts/` 目录下创建 `*.py` 文件，按照 `STYLE` 格式定义即可。

---

## 目录结构

```
sd_generator/
├── cli.py
├── main.py
├── requirements.txt
│
├── config/
│   └── app.py
│
├── core/
│   ├── engine.py
│   ├── model.py
│   ├── lora.py
│   └── prompts.py
│
├── prompts/
│   ├── base/
│   ├── gallery/
│   ├── mecha/
│   └── sketch/
│
└── output/
```

---

## 模块说明

### core/engine.py

- 封装 StableDiffusionPipeline
- 支持文生图 / 图生图
- 自动尺寸对齐（64 的倍数）

### core/model.py

- 自动扫描 SD 1.5 / SDXL 目录
- 自动识别模型类型
- 模型加载 / 卸载

### core/lora.py

- 扫描 SD 1.5 / SDXL LoRA
- 加载 / 卸载 LoRA

### core/prompts.py

- 扫描 prompts/ 目录
- 支持 STYLE 字典格式
- 随机 / 索引获取提示词

---

## License

MIT License