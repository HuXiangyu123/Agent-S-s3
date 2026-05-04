# Agent-S3 for Feishu

基于 [Agent-S (Simular AI)](https://github.com/simular-ai/Agent-S) 的飞书桌面端 CUA（Computer-Use Agent）二次开发项目。在原版 S3 通用 GUI Agent 基础上，针对飞书场景增加了图形化启动器、环境自动检测、指令历史复用、推理强度自动切换等功能。

当前项目主路线是飞书桌面端 GUI 自动化。这里提到的“命令行启动”仅指本地 Agent 进程的启动方式，不是飞书开放平台 CLI，也不是 bot 驱动路线。

---

## 快速上手（Windows）

### 第一步：环境准备

- 安装 [Python 3.10–3.12](https://www.python.org/downloads/)
- （可选）创建 conda 环境：`conda create -n agent-s python=3.12 && conda activate agent-s`
- 右键 `install.ps1` → **用 PowerShell 运行**

### 第二步：配置 API Key

复制 `env.txt.example` 为 `env.txt`，填入实际 API Key：

```bash
cp env.txt.example env.txt
```

| 用途 | 平台 | 说明 |
|------|------|------|
| 主模型（推理规划） | OpenAI GPT / 火山引擎豆包 | 支持 reasoning_effort 控制 |
| 落地模型（视觉定位） | 火山引擎豆包 Vision | doubao-seed-1-6-vision，坐标空间 0-1000 |

> `env.txt` 已在 `.gitignore` 中，不会被提交到仓库。

### 第三步：启动

```bash
python launcher.py
```

在图形界面中：
1. 选择主模型（OpenAI GPT / 火山引擎豆包）和落地服务
2. 填写 API Key
3. 系统自动检测屏幕分辨率和 DPI 缩放
4. 点击「保存配置」→「启动 Agent」
5. 出现 **✅ Agent 就绪** 后，输入任务指令或从下拉框选择历史指令

### 候选指令

- `打开消息中的测试群聊，在消息发送框输入 hello，并在聊天框点击右侧的表情图标，随机选择一个表情后发送`
- `打开云文档页面，点击新建按钮，创建空白文档`

---

## 命令行启动

```bash
python gui_agents/s3/cli_app.py \
    --provider openai \
    --model gpt-5.4 \
    --model_url https://right.codes/codex/v1 \
    --model_api_key sk-xxx \
    --ground_provider openai \
    --ground_url https://ark.cn-beijing.volces.com/api/v3 \
    --ground_api_key ark-xxx \
    --ground_model doubao-seed-1-6-vision-250815 \
    --grounding_width 2000 \
    --grounding_height 1125 \
    --ground_coord_scale 1000 \
    --reasoning_effort medium \
    --reflection_mode on_failure
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--provider` | 否 | `openai` | 主模型 provider |
| `--model` | 否 | `gpt-5-2025-08-07` | 主模型名称 |
| `--model_url` | 否 | — | 主模型 API 端点 |
| `--model_api_key` | 否 | — | 主模型 API Key |
| `--ground_provider` | **是** | — | 落地模型 provider |
| `--ground_url` | **是** | — | 落地模型 API 端点 |
| `--ground_model` | **是** | — | 落地模型名称 |
| `--ground_api_key` | 否 | — | 落地模型 API Key |
| `--grounding_width` | **是** | — | 落地图片宽度 |
| `--grounding_height` | **是** | — | 落地图片高度 |
| `--ground_coord_scale` | 否 | — | 落地坐标空间（Doubao 用 1000） |
| `--reasoning_effort` | 否 | `medium` | GPT 推理强度：`low` / `medium` / `high` / `xhigh` |
| `--reflection_mode` | 否 | `on_failure` | 反射频率：`full` / `reduced` / `on_failure` / `off` |
| `--enable_reflection` | 否 | `True` | 启用反射代理 |
| `--max_trajectory_length` | 否 | `8` | 最多保留的图像轮数 |

---

## SDK 使用

```python
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

engine_params = {
    "engine_type": "openai",
    "model": "gpt-5.4",
    "base_url": "https://right.codes/codex/v1",
    "api_key": "sk-xxx",
    "reasoning_effort": "medium",
    "reflection_mode": "on_failure",
}

engine_params_for_grounding = {
    "engine_type": "openai",
    "model": "doubao-seed-1-6-vision-250815",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "ark-xxx",
    "grounding_width": 2000,
    "grounding_height": 1125,
    "ground_coord_scale": 1000,  # Doubao 坐标空间 0-1000
}

grounding_agent = OSWorldACI(
    platform="windows",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_for_grounding,
    width=3840,   # 屏幕宽度（pyautogui.size()）
    height=2160,  # 屏幕高度
)

agent = AgentS3(
    engine_params,
    grounding_agent,
    platform="windows",
    max_trajectory_length=8,
    enable_reflection=True,
)

# 执行
info, actions = agent.predict(instruction="在飞书中发送消息", observation=obs)
exec(actions[0])
```

---

## 项目特性

### 推理强度自动切换

GPT/o-series 模型根据任务复杂度自动调整 `reasoning_effort`：

| 场景 | 推理强度 |
|------|----------|
| 普通操作（点击、输入、等待） | `medium` |
| 复杂操作（跨窗口、应用切换、跨模块） | `xhigh` |
| 步骤失败重试 | `xhigh` |

策略定义在 `gui_agents/s3/agents/reasoning_strategy.py`，可通过 `env.txt` 的 `model_reasoning_effort` 覆盖默认值。

### 反射频率控制

| 模式 | 行为 | 说明 |
|------|------|------|
| `full` | 每步反射 | 最稳定，最慢（多 ~15-25s/步） |
| `reduced` | 每隔一步反射 | 节省 ~50% 反射调用 |
| `on_failure` | 仅失败时反射 | 默认，节省 ~90% 反射调用 |
| `off` | 不反射 | 最快，精度可能下降 |

### 环境自动检测

首次启动时自动检测：
- 操作系统 & 版本
- 屏幕分辨率（虚拟 + 物理）
- DPI 缩放比例
- 推荐落地分辨率（按 provider）

检测结果持久化到 `config.json`，后续启动直接复用。支持手动「重新检测环境」。

### 指令历史复用

输入过的指令自动保存到 `command_history.json`（去重，上限 50 条），通过下拉框复用。

---

## 项目结构

```text
gui_agents/s3/               ← S3 通用 GUI 执行内核
  agents/
    agent_s.py                ← AgentS3 主入口
    worker.py                 ← Worker（规划 + 落地 + 反射）
    grounding.py              ← OSWorldACI 落地代理
    reasoning_strategy.py     ← reasoning_effort 自动切换
    code_agent.py             ← Code Agent（混合执行）
  memory/
    procedural_memory.py      ← 过程记忆 & prompt
  core/
    engine.py                 ← LLM 引擎（OpenAI/Anthropic/Gemini）
    module.py                 ← BaseModule

launcher.py                   ← 图形化启动器
test_models.py                ← 模型连通性测试
sop_executor.py               ← SOP 脚本执行引擎
sops/                         ← SOP JSON 配置文件
docs/
  README.md                              ← 文档索引与协作入口
  feishu_gui_agent_master_plan.md      ← 飞书 GUI Agent 主方案
  product/
    feishu_gui_agent_prd.md            ← 产品需求文档
  spec/
    feishu_gui_agent_technical_spec.md ← 技术规格文档
  interfaces/
    feishu_gui_agent_interfaces.md     ← 模块接口文档
  archive/
    feishu_secondary_dev_guide.md      ← 归档：飞书二开方案
    feishu_tools_skills_architecture.md← 归档：Tools/Skills 架构指导
  openai_api_parameters.md             ← OpenAI API 参数参考
  项目需求.md                          ← 项目需求
```

---

## 测试

```bash
# 模型连通性测试
python test_models.py          # 终端输出
python test_models.py --json   # 机器可读
python test_models.py -v       # 显示原始响应
```

---

## 注意事项

- 仅支持**单显示器**
- Agent 会直接控制鼠标和键盘，执行过程中请勿操作电脑
- 每步约 30–60 秒（含 1 次生成器 + 1 次落地 + 可选反射调用）
- 反射模式默认 `on_failure`，如需更稳定可改为 `full`

---

## 致谢

本项目基于 [Agent-S (Simular AI)](https://github.com/simular-ai/Agent-S) 的 S3 内核构建，在原版通用 GUI Agent 能力之上增加了飞书场景适配和工程化改进。

## 引用

```bibtex
@misc{Agent-S2,
    title={Agent S2: A Compositional Generalist-Specialist Framework for Computer Use Agents},
    author={Saaket Agashe and Kyle Wong and Vincent Tu and Jiachen Yang and Ang Li and Xin Eric Wang},
    year={2025},
    eprint={2504.00906},
    archivePrefix={arXiv},
    primaryClass={cs.AI},
}

@inproceedings{Agent-S,
    title={{Agent S: An Open Agentic Framework that Uses Computers Like a Human}},
    author={Saaket Agashe and Jiuzhou Han and Shuyu Gan and Jiachen Yang and Ang Li and Xin Eric Wang},
    booktitle={International Conference on Learning Representations (ICLR)},
    year={2025},
    url={https://arxiv.org/abs/2410.08164},
}
```
