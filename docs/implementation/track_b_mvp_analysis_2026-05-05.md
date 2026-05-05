# Track B MVP Analysis And Implementation Plan (2026-05-05)

## Goal

为飞书 GUI Agent 建立 `Track B` 的最小可用视觉知识层，覆盖：

- `pages/`
- `detectors/`
- `locators/`

本轮目标不是接入完整运行链路，也不是恢复 UIA，而是先把 `IM send_message` 主路径所需的页面事实、状态识别和目标定位契约落成可维护代码，供后续 `workflows/`、`verifiers/`、`feishu_worker` 消费。

## Why Track B Next

`Track A` 已经完成了：

- 自然语言 -> `TestCase`
- `TestCase` -> `WorkflowPlan`

当前还缺的是把“话说清楚”接到“屏看清楚”：

- `WorkflowPlan` 已知道要做 `open_chat -> type_message -> send_message`
- 但运行时还没有稳定的 `PageDescriptor`
- 也没有结构化 `FeishuState`
- 更没有统一 `LocatorResult`

没有 `Track B`，后续 `Track C` 的 workflow 只能继续依赖 prompt 内隐知识和黑盒视觉点击，无法形成稳定的页面语义层。

## Current Implementation Status

当前仓库状态：

- `gui_agents/feishu/` 已有：
  - `contracts.py`
  - `testcases/`
  - `planner/`
- `gui_agents/feishu/pages/`、`detectors/`、`locators/` 目前不存在
- `tests/feishu/` 目前只有 `testcases/`、`planner/`
- 默认运行链路仍是：
  - `gui_agents/s3/cli_app.py`
  - `gui_agents/s3/agents/grounding.py`
  - `OSWorldACI`

这意味着：

1. `Track B` 本轮应先作为独立领域层落地，不直接改默认 runtime 主链
2. 当前默认主线只承诺 `vision-first`
3. `AccessibilityLocator` / `HybridLocator` 本轮仍只保留接口占位

## Source Of Truth

1. `AGENTS.md`
2. `docs/feishu_gui_agent_master_plan.md`
3. `docs/spec/feishu_gui_agent_technical_spec.md`
4. `docs/interfaces/feishu_gui_agent_interfaces.md`
5. `docs/process/project_state.md`
6. `gui_agents/feishu/contracts.py`
7. `gui_agents/s3/agents/grounding.py`

## MVP Scope

### In Scope

只覆盖 `IM send_message` 所需的最小视觉知识层：

- 1 个页面描述：
  - `im_chat_main`
- 1 组状态识别：
  - 当前是否在 IM 聊天页
  - 当前聊天标题
  - 输入框是否可见
  - 发送按钮是否可见
  - 搜索框是否可见
- 1 个最小定位器：
  - `message_input`
  - `send_button`
- 统一的失败返回格式：
  - `failure_type`
  - `failure_reason`
  - `page_id`

### Out Of Scope

- `Docs` / `Calendar`
- 群创建弹窗
- `@提及` 下拉
- UIA / Accessibility 实现
- 默认 `cli_app.py` 入口改线
- `FeishuWorker` / `workflows/` / `verifiers/`
- 真实自动点击执行集成

## Recommended Module Boundaries

### `pages/`

职责：

- 固化页面知识
- 定义 `PageDescriptor`
- 提供页面注册表
- 提供关键区域、文本锚点、支持 workflow 列表

不负责：

- OCR 识别
- 状态判断
- 坐标定位

### `detectors/`

职责：

- 从 `observation` 推导 `FeishuState`
- 判断当前页面是否符合某个 `PageDescriptor`
- 输出结构化状态

不负责：

- 直接返回点击坐标
- 执行动作
- 规划 workflow

### `locators/`

职责：

- 基于 `target + state + observation + page_context` 返回 `LocatorResult`
- 当前只承诺 `VisionLocator`
- 定位失败时仍返回结构化失败

不负责：

- 直接点击
- 页面状态建模
- 业务流程切换

## Proposed MVP Design

### 1. Pages

先建立单页注册：

- `page_id`: `im_chat_main`
- `page_type`: `chat_main`
- `display_name`: `Feishu IM Chat Main`
- `supported_workflows`: `["send_message"]`

建议关键区域最小化定义：

- `header`
- `chat_body`
- `message_input_area`
- `send_button_area`
- `search_area`

建议文本锚点最小化：

- `发送`
- 聊天页稳定标题区文本
- 搜索区稳定占位词或附近稳定文案

### 2. Detectors

第一版不追求聪明，只追求够用：

- 输入：`observation: dict`
- 允许 `observation` 至少支持：
  - `ocr_text`
  - `ocr_words`
  - `image_size`
  - 可选原图元信息

最小判断逻辑：

1. 是否命中 IM 聊天页锚点
2. 是否存在聊天标题候选
3. 是否存在输入框区域特征
4. 是否存在发送按钮文字或稳定区域
5. 是否存在搜索框特征

第一版建议采用：

- 规则驱动
- OCR 文本匹配
- 配合页面描述中的区域 hints

而不是：

- 直接重新调 VLM
- 黑盒页面分类 prompt

### 3. Locators

第一版 `VisionLocator` 只做最小目标集：

- `message_input`
- `send_button`

定位策略建议：

1. 先用 `page_context.page_descriptor` 缩小候选区域
2. 再用 OCR 文本或规则锚点命中目标
3. 若无法精确命中，则返回结构化失败，不做隐式猜点

返回必须符合 `LocatorResult` 契约：

- `matched`
- `strategy`
- `x`
- `y`
- `confidence`
- `bbox`
- `page_id`
- 可选 `failure_type`
- 可选 `failure_reason`

## Observation Contract For Track B

为了让 `detectors/locators` 先可测试，建议本轮定义一个**最小 observation 约定**，不改共享 contracts，只在模块内部约定：

```python
{
    "ocr_text": str,
    "ocr_words": [
        {
            "text": str,
            "bbox": [x1, y1, x2, y2],
        }
    ],
    "image_width": int,
    "image_height": int,
}
```

理由：

- 这样可以先用人工构造 fixture 跑单元测试
- 不必本轮就把截图 OCR 管线正式接入 `Track B`
- 后续再由 runtime 侧适配真实 observation

## Target Files

### Code

- `gui_agents/feishu/pages/__init__.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/pages/im_chat_main.py`
- `gui_agents/feishu/detectors/__init__.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/locators/__init__.py`
- `gui_agents/feishu/locators/vision_locator.py`

### Tests

- `tests/feishu/pages/__init__.py`
- `tests/feishu/pages/test_registry.py`
- `tests/feishu/detectors/__init__.py`
- `tests/feishu/detectors/test_im_state_detector.py`
- `tests/feishu/locators/__init__.py`
- `tests/feishu/locators/test_vision_locator.py`

### Fixtures

建议准备：

- `tests/fixtures/feishu/im_chat_main/`

本轮如果截图还没准备好，可先用纯结构化 mock fixture 起步。

## TODO List

1. 先定义 `im_chat_main` 的 `PageDescriptor`
2. 建立 `PageRegistry`，把 `Track B` 页面知识从 prompt 中抽离
3. 定义 `IMStateDetector` 的最小 observation 消费协议
4. 先实现规则驱动的 `FeishuState` 识别，不引入额外 VLM 调用
5. 先实现 `VisionLocator` 的最小目标集：`message_input`、`send_button`
6. 对定位失败、页面识别失败分别返回结构化失败
7. 先用 mock OCR fixture 建自动化测试
8. 截图到位后，再补真实页面事实校准与 fixture 升级

## Depends On

- 已冻结共享 contracts：
  - `PageDescriptor`
  - `FeishuState`
  - `LocatorResult`
  - `FailureType`
  - `TargetId`
- `Track A` 已提供的 `WorkflowPlan`
- 当前 `vision-first` runtime 仍作为后续接线背景，不是本轮直接修改对象

## Outputs

本轮应产出：

1. 可导入的 `pages/`、`detectors/`、`locators/` 包
2. 单页 `IM chat main` 页面描述
3. 最小 `FeishuState` 检测器
4. 最小 `VisionLocator`
5. 对应模块测试
6. 对“需要真实截图”的缺口有清单，而不是边写边猜

## Verification Plan

自动化验证：

1. `PageRegistry` 能按 `page_id` 正确返回 `PageDescriptor`
2. `IMStateDetector` 能从 mock observation 正确输出：
   - `page_type`
   - `product`
   - `chat_name`
   - `message_input_visible`
   - `send_button_visible`
   - `search_box_visible`
3. `VisionLocator` 对 `message_input` / `send_button` 返回正确 `LocatorResult`
4. 定位失败时返回：
   - `matched=False`
   - `failure_type="location"`
5. 页面识别不成立时返回：
   - `page_id=None`
   - `failure_type="recognition"` 或等价结构化失败

计划执行的命令：

- `python -m unittest discover -s tests/feishu/pages -t . -v`
- `python -m unittest discover -s tests/feishu/detectors -t . -v`
- `python -m unittest discover -s tests/feishu/locators -t . -v`
- `python -m unittest discover -s tests/feishu -t . -v`
- `python -m compileall gui_agents/feishu tests/feishu`

## Risks

1. 没有真实截图时，页面锚点容易写成想象中的 UI，而不是真实 UI。
2. 如果 observation 协议现在定义得太随意，后续接 runtime 时会产生适配层返工。
3. 如果 detector 过早塞入太多业务判断，会与 `workflow` 职责冲突。
4. 如果 locator 为了“勉强点到”而做隐式猜点，后续失败原因会重新变黑盒。

## Rollback

如果本轮方案被证明边界不合理：

1. 保留 `pages/` 的结构与测试
2. 回滚 detector/locator 的具体规则
3. 保留 observation fixture 作为后续契约证据

## Screenshot / Local Knowledge Needed From User

如果进入编码并做真实页面校准，最小建议你补这些本地截图：

1. 飞书 IM 聊天主页全图
2. 已打开目标群聊时的标题栏区域
3. 输入框空状态
4. 输入框已聚焦状态
5. 发送按钮可点状态
6. 搜索框可见状态
7. 如果方便，再补一个“异常态”：
   - 弹窗遮挡
   - 错页
   - 搜索结果列表展开

建议命名示例：

- `im_chat_main_full.png`
- `im_chat_title.png`
- `im_message_input_idle.png`
- `im_message_input_focused.png`
- `im_send_button_enabled.png`
- `im_search_box_visible.png`

## Recommendation

建议按两小步推进 Track B：

### B1. 无截图先行

- 先建 `pages/registry`
- 先建 detector / locator 接口与 mock fixture 测试
- 固化 observation 消费协议

### B2. 截图校准

- 你补本地截图
- 我再把 `PageDescriptor`、区域 hints、定位规则校准到真实页面

这样可以避免现在就被截图资产阻塞，同时保证后续不是拍脑袋接页面事实。
