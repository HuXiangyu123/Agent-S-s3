# 飞书 Tools / Skills 架构说明

## 1. 当前基线

当前仓库已经具备这些能力：

- `gui_agents/s3/`：通用 GUI 执行内核
- `launcher.py`：图形化启动器
- `sop_executor.py` + `sops/`：脚本化快捷执行
- `reasoning_effort` 自动切换
- 基础日志、配置持久化、环境检测

当前仓库还不具备这些飞书专用能力：

- 页面先验知识
- 视觉锚点维护
- 飞书语义动作层
- 显式 workflow / verifier
- 稳定回归链

另外，当前阶段不把飞书 CLI、bot、开放平台 API 当主架构基础。

## 2. 当前架构原则

当前推荐的原则不是 `API / GUI / Hybrid` 优先，而是：

```text
GUI-first
  + Page Knowledge
  + Visual Anchor
  + Workflow
  + Verifier
  + Maintenance
```

原因：

1. 当前目标是飞书桌面端真实 GUI 自动化。
2. 个人用户场景下，开放平台能力不完整，也不等价于真实桌面用户操作。
3. 当前最需要解决的是稳定性、状态识别、回归与维护，不是接口调用。

## 3. 当前推荐的总览架构

```text
自然语言任务
  -> Workflow Selector
  -> GUI Workflow Engine
  -> FeishuACI
  -> S3 Grounding / Execution
  -> Verifier
  -> Regression Artifacts

辅助能力：
  - Page Registry
  - Visual Anchor Store
  - Screenshot Recorder
  - Anchor Validator
  - optional Code Agent
```

这里的 `Workflow Selector` 当前只需要在两类路径间做判断：

- 进入某个已注册 workflow
- 交给 `code agent` 做内容整理或文本生成

当前不需要默认第三条 `API path`。

## 4. 三个核心模块

### 4.1 Page Registry

目的：让系统知道“当前可能是什么页面，以及关键区域在哪里”。

示例：

```python
from dataclasses import dataclass


@dataclass
class PageDescriptor:
    page_id: str
    page_type: str
    display_name: str
    layout_hints: dict
    key_regions: dict
    text_anchors: list[str]
    supported_workflows: list[str]
    ui_version_tag: str
```

建议目录：

```text
gui_agents/feishu/pages/
  __init__.py
  registry.py
  feishu_im/
    chat_list.py
    chat_detail.py
  feishu_docs/
    doc_editor.py
```

### 4.2 Workflow / Skill Engine

目的：把高频任务固化成稳定的阶段机，而不是每次让模型重想一遍。

第一阶段建议 workflow 比 skill 更直接。后续如果数量变多，再向可配置 skill/SOP 演进。

最小示例：

```python
SEND_MESSAGE_WORKFLOW = {
    "workflow_id": "feishu:im:send_message",
    "entry_page": "feishu:im:chat_detail",
    "stages": [
        "ensure_chat_open",
        "ensure_input_ready",
        "type_message",
        "send_message",
        "verify_sent",
    ],
}
```

每一阶段都必须有：

- success gate
- fallback
- retry policy

### 4.3 Visual Anchor Store

目的：把页面截图、局部 crop、稳定区域和版本信息管理起来，解决 UI 漂移问题。

建议目录：

```text
gui_agents/feishu/anchors/
  feishu-desktop-<version>-win/
    chat_detail/
      overview.png
      chat_title.png
      message_input.png
      send_button.png
      anchors.json
```

建议 `anchors.json` 至少包含：

- `ui_version`
- `page_type`
- `relative_bounds`
- `crop_file`
- `grounding_hint`
- `stable_text` 或 `stable_features`

## 5. 当前不建议放进主架构的模块

以下模块不是不能做，而是不该作为当前主链的默认前提：

- `FeishuAPIExecutor`
- `API + GUI hybrid router`
- bot / CLI 优先的任务分发
- 依赖开放平台能力的 workflow

如果未来业务场景变化，需要开放平台支持，建议隔离在：

```text
gui_agents/feishu/integrations/
  open_platform/
    executor.py
    adapters.py
```

并通过显式开关启用。

## 6. 与当前 S3 的集成方式

建议最小侵入接入，不重写主链。

### 6.1 Worker 层

在 `gui_agents/s3/agents/worker.py` 里只增加少量注入点：

- page context
- workflow result
- verifier result

不要直接把飞书专用逻辑全部塞回 `Worker`。

### 6.2 Grounding 层

建议通过 `FeishuACI(OSWorldACI)` 或专用封装做语义动作扩展：

- `open_chat`
- `focus_message_input`
- `clear_message_input`
- `type_message`
- `send_message`

不要为了飞书逻辑破坏 `OSWorldACI` 的通用定位职责。

### 6.3 启动器和 SOP 页

`launcher.py` 当前可以继续保留：

- 模型配置
- 环境检测
- 历史任务
- SOP 快捷入口

但后续应增加：

- workflow 回归入口
- 锚点状态显示
- 截图刷新入口

## 7. 维护链为什么是一等公民

如果没有维护链：

- SOP 会变成一次性产物
- 页面一改版，定位 silently drift
- 团队无法判断问题来自模型、页面还是锚点

所以建议尽早准备：

- `ScreenshotRecorder`
- `AnchorValidator`
- `DriftMonitor`
- regression artifacts

## 8. 推荐里程碑

### M1：最小闭环

- 建 `gui_agents/feishu/` 骨架
- 实现 `FeishuStateDetector`
- 实现 `FeishuACI`
- 实现 `SendMessageWorkflow`
- 实现 `CompletionGate`

验收：

- 固定目标会话消息发送可以稳定回归

### M2：页面先验与锚点

- `PageRegistry`
- `anchors/`
- `ScreenshotRecorder`
- `AnchorValidator`

验收：

- 已注册页面可以发现 UI 漂移

### M3：第二个 workflow 与恢复

- `SendFileWorkflow` 或 `ReplyInThreadWorkflow`
- modal / wrong-page recovery
- 更细的 verifier

验收：

- 至少 2 个 workflow 有明确成功标准

### M4：回归与评审

- regression 脚本
- artifacts 归档
- review checklist

验收：

- 每次改动后都能做同一组回归，不再只看“跑起来了没有”

## 9. 与旧版 dev guide 的差异

当前版本与旧思路的最大差异是：

1. 不再把 `API / GUI / Hybrid` 作为当前默认结构。
2. 不再把 `FeishuAPIExecutor` 当 MVP 必选项。
3. 把“桌面 GUI 主路径 + 可维护的页面/锚点/回归链”提升为当前第一优先级。

未来如果业务目标变化，再把开放平台能力补成可选扩展，而不是现在提前侵入主架构。

## 10. 一句话原则

当前只追求：

“注册过的飞书页面和 workflow 稳定跑通，并且能验证、能回归、能维护。”

不追求：

“先把所有潜在 API / bot / CLI 路径都设计进去。”
