# 飞书 Tools/Skills 架构指导意见

## 1. 当前项目基线

在给出架构之前，先明确当前项目已具备的能力和能力边界：

### 已就绪

| 模块 | 位置 | 能力 |
|------|------|------|
| S3 通用 GUI 执行内核 | `gui_agents/s3/` | 截图→落地→反思→规划→执行的闭环主链 |
| 落地模型 (Doubao) | `gui_agents/s3/agents/grounding.py` | 视觉定位，0-1000 归一化坐标 |
| GPT 推理 (reasoning_effort) | `gui_agents/s3/agents/reasoning_strategy.py` | medium/high/xhigh 自动切换 |
| 启动器 GUI | `launcher.py` | 模型配置、指令历史、SOP 快捷操作页 |
| 环境检测 | `launcher.py` | 平台/DPI/屏幕分辨率/落地分辨率自动检测 |
| SOP 执行框架 | `sop_executor.py` + `sops/` | JSON 驱动的参数化脚本执行 |
| 配置持久化 | `config.json` + `command_history.json` | 首次启动自动配置，后续复用 |

### 当前瓶颈

1. **SOP 只有脚本执行，没有视觉锚点**：当前 sop_executor 是纯 API/脚本路径，不涉及 GUI 定位
2. **Feishu 页面无结构化描述**：LLM 每次从截图"重新发现"页面，没有先验知识加速
3. **SOP 无截图参考**：维护者不知道当前 SOP 依赖的 UI 长什么样，飞书改版后 SOP 会静默失效
4. **SOP 无维护接口**：没有版本标记、截图刷新、回归验证机制

---

## 2. 核心设计思想：Tools/Skills + SOP + Visual Anchor

### 2.1 你的核心出发点（逐条对应）

> 把飞书的常见页面固化下来，做成 tools/skills，提供一个先验知识

→ **Page Registry**：为每个飞书页面建立结构化描述（页面类型、关键 UI 区域、视觉锚点坐标区间）

> tools 可以调用脚本和预先设定的 SOP

→ **Skill = Page Knowledge + SOP Reference + Action Mapping**，每个 skill 知道自己属于哪个页面、该页面有哪些稳定操作

> SOP 可以包括结构化的操作步骤以及页面的截图

→ SOP JSON 扩展 `visual_anchors` 字段，存储关键 UI 元素的截图 crop 和坐标描述

> 截图和 SOP 需要维护，飞书相关 UI 会更新

→ 每个 SOP 携带 `ui_version_tag`，提供截图刷新脚本和维护入口

> 执行 workflow 的时候可以调用，提高速度和加强定位精度

→ Worker 在执行前先查询 Page Registry 获取当前页面的先验知识，落地模型利用视觉锚点缩小搜索空间

### 2.2 架构全景

```
                         ┌─────────────────────┐
                         │   自然语言任务输入     │
                         └─────────┬───────────┘
                                   │
                         ┌─────────▼───────────┐
                         │    TaskRouter        │  ← 路由：纯API / GUI / Hybrid
                         └─────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼───────┐  ┌────────▼───────┐  ┌────────▼───────┐
     │  API Executor   │  │  GUI Executor   │  │  Code Agent    │
     │  (飞书开放平台)   │  │  (S3 + Feishu)  │  │  (内容生成)     │
     └────────────────┘  └────────┬───────┘  └────────────────┘
                                  │
                     ┌────────────┼────────────┐
                     │            │            │
            ┌────────▼───┐ ┌─────▼──────┐ ┌───▼──────────┐
            │ Page        │ │ Skill /    │ │ Visual       │
            │ Registry    │ │ SOP Engine │ │ Anchor Store │
            │ (页面先验)   │ │ (执行编排)  │ │ (截图+坐标)   │
            └────────────┘ └────────────┘ └──────────────┘
                                  │
                     ┌────────────┼────────────┐
                     │            │            │
            ┌────────▼───┐ ┌─────▼──────┐ ┌───▼──────────┐
            │ Grounding   │ │ Verifier   │ │ Maintenance  │
            │ (落地定位)   │ │ (完成验证)  │ │ Console      │
            └────────────┘ └────────────┘ └──────────────┘
```

---

## 3. 三个核心新模块

### 3.1 Page Registry（页面注册表）

**目的**：让 agent 知道"当前是什么页面、这个页面有什么稳定特征"。

**数据结构**：

```python
# gui_agents/feishu/pages/registry.py

@dataclass
class PageDescriptor:
    page_id: str                    # "feishu:im:chat_detail"
    page_type: str                  # "chat_detail" / "doc_editor" / "calendar_view"
    display_name: str               # "飞书 IM - 会话详情页"

    # 视觉特征（供落地模型缩小搜索空间）
    layout_hints: dict              # {"top_bar": (0, 0, w, 60), "chat_area": (0, 60, w, h-120), ...}

    # 稳定文本锚点（OCR 快速定位用）
    text_anchors: list[str]         # ["会话", "消息", "文件", "搜索"]

    # 关键 UI 元素模板坐标（相对坐标 0-1）
    key_regions: dict               # {"message_input": (0.15, 0.92, 0.85, 0.97),
                                    #  "send_button": (0.88, 0.93, 0.95, 0.96),
                                    #  "chat_title": (0.05, 0.02, 0.40, 0.06)}

    # 该页面支持的 skills
    supported_skills: list[str]     # ["send_message", "search_in_chat", "reply_thread"]

    # 维护信息
    ui_version_tag: str             # "feishu-desktop-7.32.5-win"
    last_verified: str              # "2026-05-04"
```

**注册表目录结构**：

```text
gui_agents/feishu/pages/
  __init__.py
  registry.py              ← PageDescriptor 定义 + PageRegistry 查询类
  feishu_im/
    chat_list.py            ← PageDescriptor: 会话列表页
    chat_detail.py          ← PageDescriptor: 会话详情页
    search_result.py        ← PageDescriptor: 搜索结果页
  feishu_docs/
    doc_list.py             ← PageDescriptor: 文档列表页
    doc_editor.py           ← PageDescriptor: 文档编辑页
  feishu_calendar/
    calendar_main.py        ← PageDescriptor: 日历主页
    event_create.py         ← PageDescriptor: 创建日程弹窗
```

**关键设计决策**：

- PageDescriptor 不包含像素级截图（截图在 Visual Anchor Store），只包含结构化坐标区间
- 坐标区间使用**相对坐标**（0-1），与屏幕分辨率解耦
- `ui_version_tag` 使得可以检测 SOP 是否匹配当前飞书版本

### 3.2 Skill / SOP Engine（技能与 SOP 引擎）

**目的**：将高频飞书任务固化为可调用的结构化 SOP，执行时利用 Page Registry 的先验知识加速定位。

**Skill 定义**：

```python
# gui_agents/feishu/skills/send_message.py

SEND_MESSAGE_SKILL = {
    "skill_id": "feishu:im:send_message",
    "display_name": "发送消息",
    "description": "打开指定群聊并发送文本消息",

    # 所需页面（入口状态）
    "entry_page": "feishu:im:chat_detail",

    # 执行阶段
    "stages": [
        {
            "stage_id": "open_chat",
            "name": "打开目标群聊",
            "actions": [
                {"type": "semantic", "action": "open_chat", "params": {"chat_name": "{{chat_name}}"}},
            ],
            "success_gate": {"type": "visual_anchor", "anchor_id": "chat_title", "expected": "{{chat_name}}"},
            "fallback": {"type": "retry_with", "strategy": "search", "max_retries": 2},
        },
        {
            "stage_id": "focus_input",
            "name": "定位消息输入框",
            "actions": [
                {"type": "semantic", "action": "focus_message_input", "params": {}},
                {"type": "semantic", "action": "clear_message_input", "params": {}},
            ],
            "success_gate": {"type": "visual_anchor", "anchor_id": "message_input_active"},
            "fallback": {"type": "click_region", "region": "message_input"},
        },
        {
            "stage_id": "type_message",
            "name": "输入消息内容",
            "actions": [
                {"type": "semantic", "action": "type_message", "params": {"text": "{{message}}"}},
            ],
            "success_gate": {"type": "text_verify", "field": "message_input", "expected": "{{message}}"},
            "fallback": {"type": "retry_with", "strategy": "refocus", "max_retries": 1},
        },
        {
            "stage_id": "send",
            "name": "发送消息",
            "actions": [
                {"type": "semantic", "action": "send_message", "params": {}},
            ],
            "success_gate": {"type": "visual_anchor", "anchor_id": "message_input_empty"},
            "fallback": {"type": "retry_with", "strategy": "hotkey_enter", "max_retries": 1},
        },
        {
            "stage_id": "verify",
            "name": "验证发送成功",
            "actions": [],
            "success_gate": {"type": "unique_token", "token": "{{unique_token}}"},
            "fallback": {"type": "screenshot", "save_to": "artifacts/verify_fail/"},
        },
    ],

    # 该 SOP 依赖的视觉锚点（指向 Visual Anchor Store）
    "required_anchors": [
        "chat_title",
        "message_input_bounds",
        "message_input_active",
        "message_input_empty",
        "send_button",
    ],

    # 维护信息
    "ui_version_tag": "feishu-desktop-7.32.5-win",
    "last_validated": "2026-05-04",
    "validation_screenshot": "anchors/feishu/7.32.5/chat_detail/send_flow.png",
}
```

**SOP 引擎职责**：

```python
class SOPEngine:
    """编排 SOP 阶段执行，注入 Page Registry 先验知识。"""

    def execute(self, skill: dict, params: dict, observation: dict) -> SOPResult:
        # 1. 从 Page Registry 加载当前页面描述符
        page = self.registry.lookup(skill["entry_page"])

        # 2. 将 page.layout_hints / key_regions 注入 grounding agent 上下文
        #    落地模型不再从全图搜索，而是在指定区域内定位
        self.grounding.set_page_context(page)

        # 3. 逐阶段执行，每阶段：
        for stage in skill["stages"]:
            # a. 读取该阶段的 visual_anchor
            # b. 调落地模型在 anchor 区域内定位
            # c. 执行语义动作
            # d. 调 success_gate 验证
            # e. 失败则走 fallback 链
            pass

        # 4. 返回结构化结果
        return SOPResult(...)
```

**关键设计决策**：

- Skill 定义与执行引擎分离：Skill JSON 是数据，SOPEngine 是解释器
- 每个阶段有 `success_gate`（成功判定）和 `fallback`（失败恢复），不再依赖 LLM "自己判断"
- `visual_anchor` 机制：不在全图搜，而是在已知区域内搜，定位速度提升 3-5x

### 3.3 Visual Anchor Store（视觉锚点库）

**目的**：存储飞书各页面关键 UI 元素的截图 crop，供落地模型参考和维护者对比。

**目录结构**：

```text
gui_agents/feishu/anchors/
  feishu-desktop-7.32.5-win/          ← 按飞书版本组织
    chat_detail/
      overview.png                     ← 全页面截图
      chat_title.png                   ← 群聊标题区域 crop
      message_input.png                ← 消息输入框 crop
      message_input_active.png         ← 输入框激活态 crop
      send_button.png                  ← 发送按钮 crop
      left_sidebar.png                 ← 左侧会话列表 crop
      anchors.json                     ← 锚点坐标元数据
    chat_list/
      overview.png
      search_box.png
      chat_item_template.png
    doc_editor/
      ...
  feishu-desktop-7.35.0-win/          ← 新版飞书的锚点
    ...
```

**anchors.json 结构**：

```json
{
  "ui_version": "feishu-desktop-7.32.5-win",
  "screen_ref": "3840x2160@150%",
  "page_type": "chat_detail",
  "anchors": {
    "chat_title": {
      "relative_bounds": [0.05, 0.02, 0.40, 0.06],
      "crop_file": "chat_title.png",
      "stable_text": ["群聊名称区域"],
      "grounding_hint": "群聊标题文本，位于窗口顶部中央偏左"
    },
    "message_input": {
      "relative_bounds": [0.15, 0.92, 0.85, 0.97],
      "crop_file": "message_input.png",
      "stable_features": ["灰色背景输入框", "placeholder文本"],
      "grounding_hint": "底部大面积灰色输入框区域"
    },
    "send_button": {
      "relative_bounds": [0.88, 0.93, 0.95, 0.96],
      "crop_file": "send_button.png",
      "stable_features": ["蓝色发送按钮", "纸飞机图标"],
      "grounding_hint": "输入框右侧的蓝色发送按钮，hover时高亮"
    }
  }
}
```

**关键设计决策**：

- 按飞书版本隔离：`feishu-desktop-7.32.5-win/` 目录，版本升级时新锚点不覆盖旧锚点
- 相对坐标：`relative_bounds` 使用 0-1 归一化坐标，与屏幕分辨率解耦
- `grounding_hint`：自然语言描述给落地模型，比纯坐标更鲁棒（UI 微调时仍然有效）
- 每个 anchor 携带 `stable_features`：用于版本变更检测（如果新版截图与旧版特征不匹配，触发刷新提醒）

---

## 4. 维护接口设计

这是对「飞书 UI 会更新」问题的直接回应。

### 4.1 Anchor Validator（锚点校验器）

```python
# gui_agents/feishu/maintenance/anchor_validator.py

class AnchorValidator:
    """验证当前飞书 UI 是否与已存储的锚点匹配。"""

    def validate_page(self, page_id: str, screenshot: bytes) -> ValidationReport:
        """
        1. 加载该页面的所有 anchors
        2. 对每个 anchor 区域 crop 截图
        3. 与存储的 reference crop 做像素级相似度比对
        4. 标记状态: VALID / DRIFTED / BROKEN
        """
        pass

    def suggest_refresh(self, page_id: str) -> list[str]:
        """返回需要刷新的 anchor ID 列表。"""
        pass
```

### 4.2 Screenshot Recorder（截图录制器）

```python
# gui_agents/feishu/maintenance/screenshot_recorder.py

class ScreenshotRecorder:
    """针对指定飞书页面，自动截取并保存锚点截图。"""

    def record_page(self, page_id: str) -> None:
        """
        1. 打开指定飞书页面
        2. 截全页面 overview
        3. 按 PageDescriptor.key_regions 逐个 crop
        4. 写入 anchors/{ui_version}/{page_type}/
        5. 更新 anchors.json
        """
        pass
```

### 4.3 Drift Monitor（漂移监控）

```python
# gui_agents/feishu/maintenance/drift_monitor.py

class DriftMonitor:
    """定期检查飞书 UI 是否发生了变更。"""

    def check_all(self) -> DriftReport:
        """
        对注册表中的所有页面：
        - 打开页面 → 截图
        - 调用 AnchorValidator.validate_page()
        - 汇总 DRIFTED / BROKEN 的锚点
        - 生成维护报告
        """
        pass
```

### 4.4 启动器集成

在 `launcher.py` 的 SOP 快捷操作页增加维护入口：

```
┌─────────────────────────────────────────┐
│  快捷操作                                │
│  ┌─────────────────────────────────┐    │
│  │ 🔄 刷新列表    🛠 锚点维护       │    │  ← 新增按钮
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ 📋 发送消息 (send_message)       │    │
│  │   版本: 7.32.5  ✅ 已验证        │    │  ← 显示锚点状态
│  │   [▶ 立即执行] [📸 刷新截图]     │    │  ← 新增刷新按钮
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ 📋 创建文档 (create_doc)         │    │
│  │   版本: 7.32.5  ⚠ 已漂移        │    │  ← 警告状态
│  │   [▶ 立即执行] [📸 刷新截图]     │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## 5. 与现有系统的集成路径

### 5.1 S3 Worker 的改造（最小侵入）

当前 `Worker.generate_next_action()` 负责拼上下文 → 调 LLM → 解析动作。改造方向：在执行前注入 Page Registry 先验。

```python
# 在 Worker.generate_next_action() 中增加：

# Step 0: 查询当前页面的先验知识
if hasattr(self, 'page_registry'):
    page = self.page_registry.match(obs["screenshot"])
    if page:
        # 将页面结构注入 grounding agent 的搜索空间
        self.grounding_agent.set_page_hints(page.layout_hints, page.key_regions)

        # 将页面描述注入 LLM 上下文（减少 LLM "猜页面" 的开销）
        generator_message += f"\nCURRENT PAGE: {page.page_type} ({page.display_name})\n"
        generator_message += f"KEY REGIONS: {json.dumps(page.key_regions)}\n"
```

### 5.2 Grounding 的锚点加速

```python
# 在 grounding agent 中：

class FeishuGrounding(OSWorldACI):
    def set_page_hints(self, layout_hints, key_regions):
        """缩小落地模型的搜索范围到已知区域。"""
        self._layout_hints = layout_hints
        self._key_regions = key_regions

    def generate_coords(self, ref_expr, obs):
        # 如果 ref_expr 命中了某个 key_region
        # 则只在该区域内做精细定位，而非全图搜索
        matched_region = self._match_region(ref_expr)
        if matched_region:
            crop = self._crop_to_region(obs, matched_region)
            # 传 crop 而非全图给落地模型
            coords = self._ground_in_region(crop, ref_expr)
            # 将 crop 内坐标映射回全图坐标
            return self._map_back(coords, matched_region)
        else:
            # fallback：全图落地
            return super().generate_coords(ref_expr, obs)
```

**收益**：
- 落地模型输入从 2000×1125 缩小到目标区域（例如 200×80 的发送按钮区域）
- API 调用延迟从 5-10s 降到 1-2s
- 定位精度显著提升（背景噪声大幅减少）

### 5.3 融入 SOP Tab

当前 `launcher.py` 已有 SOP 快捷操作页，`sop_executor.py` 负责执行。改造方向：

1. SOP JSON 增加 `visual_anchors`、`ui_version_tag`、`pages` 字段
2. `sop_executor.py` 在执行前加载对应 PageDescriptor
3. SOP 卡片显示锚点状态（VALID / DRIFTED / BROKEN）
4. SOP 卡片增加"刷新截图"按钮

---

## 6. 实施优先级

按投入产出比排序，建议分 4 个里程碑：

### M1：Page Registry + 1 个 Skill（1 周）

- [ ] 建 `gui_agents/feishu/` 目录骨架
- [ ] 实现 `PageDescriptor` 和 `PageRegistry` 基础类
- [ ] 为 **IM 会话详情页** 写第一个 PageDescriptor（手工标注坐标区间）
- [ ] 为 **发送消息** 写第一个 Skill JSON
- [ ] 在 `Worker` 中注入 Page Registry 查询（最小侵入）
- [ ] 验证：用 `send_message` skill 稳定执行 10 次，成功率 > 80%

### M2：Visual Anchor Store + 维护工具（1 周）

- [ ] 建 `anchors/` 目录结构
- [ ] 实现 `ScreenshotRecorder`：对已注册页面自动截取锚点
- [ ] 实现 `AnchorValidator`：像素级比对，检测漂移
- [ ] 为 IM 和文档页建立锚点库
- [ ] 在启动器 SOP 页增加锚点状态显示
- [ ] 验证：锚点校验器能正确区分 VALID / DRIFTED 状态

### M3：FeishuACI + 第二批 Skills（1 周）

- [ ] 实现 `FeishuACI(OSWorldACI)`——语义动作封装
    - `open_chat`, `focus_message_input`, `clear_message_input`, `send_message`
    - `open_doc`, `create_doc`
    - `search_contact`
- [ ] 实现 Grounding 锚点加速（crop 区域定位）
- [ ] 实现 `CompletionGate`（发送验证、文档创建验证）
- [ ] 新增 Skills：`create_doc`、`search_and_send`
- [ ] 验证：端到端执行 "搜索群聊并发送消息" < 60s

### M4：TaskRouter + 回归体系（1 周）

- [ ] 实现 `TaskRouter`：API/GUI/Code 路由决策
- [ ] 实现 `DriftMonitor`：自动检测所有注册页面的锚点漂移
- [ ] 建回归脚本：`scripts/regression/send_message_regression.py`
- [ ] 集成到启动器，提供"一键回归"按钮
- [ ] 验证：回归脚本能在飞书版本更新后自动标记漂移的锚点

---

## 7. 与 dev_guide 的差异说明

原 `feishu_secondary_dev_guide.md` 的核心判断仍然成立（需要语义动作层、状态检测层、workflow 层、API 混合路由）。本架构指导意见在其基础上做了以下具体化：

| 维度 | dev_guide 建议 | 本架构的具体化 |
|------|---------------|---------------|
| 语义动作层 | 建议 `FeishuACI` 子类 | 实现了 Skill JSON 格式，定义 stage/fence/fallback 三段式 |
| 状态检测 | 建议 `FeishuStateDetector` | 收敛为 `PageRegistry` 查询 + `AnchorValidator` 校验，不需要单独的 OCR 层 |
| workflow | 建议 `SendMessageWorkflow` 等 | 收敛为 `SOPEngine` 渲染 Skill JSON，而非每个 workflow 单独写类 |
| Memory | 建议放在最后 | 同建议，但明确了 memory 服务的是"类似任务找 SOP"而非"定义新动作" |
| 维护 | 未涉及 | **新增**：Visual Anchor Store、ScreenshotRecorder、AnchorValidator、DriftMonitor 完整维护链 |

核心差异：本架构把 "SOP + 截图 + 维护" 提升为一等公民，因为——没有维护机制，SOP 就是一次性产物；没有截图锚点，执行稳定性和定位精度无法保证。

---

## 8. 一条总原则

```
先验知识（Page Registry + Visual Anchor）
  → 缩小搜索空间（Grounding 只在目标区域定位，不搜全图）
  → 提速 + 提精度
  → 维护接口保证先验知识不腐化
  → 形成可持续迭代的飞书自动化基础
```

不追求"所有飞书操作都自动化"，只追求"注册过的页面和 SOP 稳定跑通，未注册的走通用 S3 路径作为兜底"。
