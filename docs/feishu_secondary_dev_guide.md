# 面向飞书 App 的二开方案

## 1. 先说结论

只扩充 memory 不够，而且会越来越不合理。

原因不是 memory 没用，而是它解决的是“先验经验”问题，不解决下面 4 个核心问题：

1. 没有飞书语义动作。
2. 没有飞书页面状态识别。
3. 没有任务完成验证。
4. 没有 API 和 GUI 的混合执行路由。

如果只扩 memory，最终效果通常是：

- 每个操作都要手搓 few-shot 轨迹
- UI 一改版，历史记忆立即贬值
- LLM 仍然只能在通用 `click/type/hotkey` 上硬猜
- 长流程会越来越脆

所以你的判断是对的：只靠扩 memory，会把系统做成“样例驱动的脆弱自动化”，不是可持续的业务 agent。

## 2. 用这个仓库做飞书，应该从哪方面入手

建议按优先级从高到低看：

### 2.1 先做“飞书语义动作层”

当前 S3 暴露给 LLM 的动作基本是通用 GUI 原语，定义在 `gui_agents/s3/agents/grounding.py`，例如：

- `click(...)`
- `open(...)`
- `type(...)`
- `hotkey(...)`
- `scroll(...)`
- `call_code_agent(...)`

这对通用桌面足够，但对飞书不够。你需要补一层业务动作，把“飞书里的稳定任务语义”提出来。

建议新增一个领域层，例如：

```text
gui_agents/feishu/
  agents/
    grounding.py
    worker.py
  memory/
    procedural_memory.py
  detectors.py
  workflows.py
  api_client.py
```

建议的高层动作示例：

- `open_feishu()`
- `switch_workspace(workspace_name)`
- `open_chat(chat_name)`
- `search_contact(name)`
- `send_message(text)`
- `send_file(path)`
- `reply_last_message(text)`
- `open_doc(doc_name)`
- `create_doc(title)`
- `search_message(keyword)`

这样 LLM 不再每次都手写一串底层 click/type，而是优先调用飞书领域动作。

### 2.2 再做“页面状态识别层”

飞书不是单一页面，而是多工作区、多入口、多模态界面：

- 会话列表
- 会话详情
- 线程回复
- 文档
- 表格
- 日历
- 审批
- 搜索结果
- 弹窗/通知/登录框

如果没有状态识别层，agent 会一直靠 screenshot 自己猜当前页面，非常不稳定。

建议单独做一个 `FeishuStateDetector`，至少输出：

- `page_type`
- `workspace`
- `chat_name`
- `has_modal`
- `input_box_visible`
- `send_button_visible`
- `unread_badge_count`

实现方式可以组合：

- screenshot + OCR
- 少量模板匹配
- 条件允许时叠加 accessibility 信息

注意这里的重点不是“更聪明”，而是“把不确定性前移成显式状态”。

### 2.3 再做“workflow / 状态机层”

飞书常见任务不是单步动作，而是半结构化流程。例如：

- 打开某群并发送消息
- 找到某人并发文件
- 打开某文档并填写指定内容
- 在某线程下回复并 @ 指定人

这些任务如果完全交给 LLM 在线现编，会有两个问题：

- 每次路径都不同，稳定性差
- 失败恢复没有显式策略

建议把高频任务抽成 workflow：

- `SendMessageWorkflow`
- `SendFileWorkflow`
- `ReplyInThreadWorkflow`
- `OpenDocAndEditWorkflow`

每个 workflow 要有：

- 前置条件
- 关键步骤
- 成功判定
- 失败恢复
- 超时/重试策略

这层才是真正降低“每个操作都要手搓”的关键。

### 2.4 再做“API + GUI 混合执行”

这是飞书场景里最值得投入的一层。

很多飞书动作其实更适合 API，不适合纯 GUI：

- 发消息
- 取用户/群信息
- 创建文档
- 读写多维表格/表格数据
- 日历事件
- 审批流信息

建议加一个 `TaskRouter`：

```text
用户任务
  -> TaskRouter
    -> API path
    -> GUI path
    -> API + GUI hybrid path
```

路由规则建议：

- 能 API 完成的，优先 API
- 必须依赖桌面态上下文的，用 GUI
- 登录、扫码、复杂富文本编辑、未知页面回退，走 GUI
- 数据处理、批量消息、文档生成，优先 API 或 code agent

这一步会直接把系统从“视觉点点点”升级成“业务 agent”。

### 2.5 最后才是 memory

memory 仍然有价值，但位置应该靠后。

适合记的内容：

- 某类任务成功轨迹摘要
- 某页面的稳定视觉锚点
- 某类异常的恢复策略
- 某组织的命名习惯、常用群名、文档路径

不适合让 memory 单独承担的内容：

- 新动作定义
- 页面解析逻辑
- 任务验证逻辑
- 跨系统执行策略

## 3. 基于现有仓库，推荐怎么改

### 3.1 以 S3 为底座，不建议直接在 S2 上硬改

建议基线：

- 执行核心用 S3
- 长期记忆能力按需借 S2
- 不建议把 S2 的 Manager/DAG 全量搬回来

原因：

- S3 的执行主链路短，见 `gui_agents/s3/cli_app.py:155` 和 `gui_agents/s3/agents/worker.py:180`
- S3 已经自带 `code agent` 分支，便于做 GUI/API/Code 混合
- S2 的 DAG 更偏 benchmark 规划，不一定适合 IM/协同办公这种高频中断、状态变化快的任务

### 3.2 推荐的改造落点

#### A. 新增飞书 ACI，而不是直接污染通用 OSWorldACI

推荐方式：

- 新建 `FeishuACI(OSWorldACI)`
- 把飞书特有动作写进这个子类
- 在 procedural memory 里只暴露飞书需要的高层动作

建议改造点：

- 基类参考：`gui_agents/s3/agents/grounding.py:179`
- 动作入口：`gui_agents/s3/agents/grounding.py:346-664`
- Prompt 暴露：`gui_agents/s3/memory/procedural_memory.py:15`

#### B. Worker 增加领域路由，而不是只改 prompt

当前 S3 的 `Worker.generate_next_action()` 负责拼上下文并产出动作，见 `gui_agents/s3/agents/worker.py:180`。

建议这里增加：

- `task_router`
- `state_detector`
- `verifier`
- `domain_memory`

一个更合适的结构是：

```text
FeishuWorker
  -> StateDetector
  -> TaskRouter
  -> LLM Planner
  -> FeishuACI
  -> Verifier
```

#### C. 复用 S2 的 KB，但不要复用整套 S2 调度

可以借的部分：

- `gui_agents/s2/core/knowledge.py:83` `formulate_query`
- `gui_agents/s2/core/knowledge.py:161` `retrieve_narrative_experience`
- `gui_agents/s2/core/knowledge.py:198` `retrieve_episodic_experience`
- `gui_agents/s2/core/knowledge.py:235` `knowledge_fusion`

可行做法：

- 让 FeishuWorker 在任务开始前检索“类似飞书任务”
- 让 workflow 在失败时检索“恢复策略”
- 不要让 S2 的 DAG 抢走 S3 的主执行链

## 4. 飞书场景下，什么能力最值得优先做

建议按这个顺序推进：

### 第一阶段：做最小闭环

目标只做 3 类操作：

1. 搜索并打开会话
2. 发送文本消息
3. 上传文件

要求：

- 单 OS 先跑通
- 有成功验证
- 失败可重试

### 第二阶段：做状态识别和验证

优先做：

- 是否进入正确会话
- 输入框是否可用
- 消息是否发出成功
- 文件是否上传成功

没有 verifier，任何自动化都会停留在“看起来点了”，而不是“确实完成了”。

### 第三阶段：接 API 路由

一旦最小闭环稳定，就接入：

- 消息 API
- 文档 API
- 表格/多维表格 API
- 通讯录/群信息 API

这一步的收益通常最大。

### 第四阶段：再强化 memory

这时 memory 才会真正有复利，因为它服务的是：

- 已经稳定存在的动作层
- 已经存在的状态识别器
- 已经定义好的 workflow

## 5. 一个更合理的目标架构

推荐你把这个项目往下面的结构推：

```text
User Task
  -> Domain Router
    -> Feishu API Executor
    -> GUI Executor (Agent-S / FeishuACI)
    -> Code Executor
  -> State Store
  -> Workflow Engine
  -> Verifier
  -> Domain Memory
```

对应到当前仓库，建议落点：

- `gui_agents/s3/agents/worker.py`
  - 加 router / verifier / domain context
- `gui_agents/s3/agents/grounding.py`
  - 不直接硬改，抽子类
- `gui_agents/s3/memory/procedural_memory.py`
  - 替换成飞书领域 prompt
- `gui_agents/s2/core/knowledge.py`
  - 选择性复用检索记忆

## 6. 关于多端适配，飞书怎么处理更现实

仓库本身有桌面 OS 多端能力，但飞书业务适配建议不要一开始就三端全做。

建议顺序：

1. 先选一个主目标 OS。
2. 先选飞书桌面客户端或飞书 Web 二选一。
3. 跑通最小闭环后，再抽象 OS 差异。

原因：

- 通用 `platform` 分支只能解决热键和启动方式，不解决飞书页面差异
- 同一个飞书任务在不同 OS、不同客户端版本上，视觉锚点可能不同
- 太早追求“三端统一”，会把复杂度提前

如果你的业务允许，优先级一般是：

- 企业内部 Windows 桌面端最多，就先做 Windows
- 如果更重 API/网页编辑，优先考虑飞书 Web 版本

## 7. 一句话建议

把 S3 当成“通用 GUI 执行内核”，把 S2 当成“可拆用的记忆模块”，然后在它们之上新增一层飞书领域动作、页面状态识别、workflow 和 API 路由。

这条路比“继续往 memory 里堆样例”更像一个可维护的产品架构。

## 8. 按阶段落地的详细步骤

下面这部分不是概念图，而是建议你实际照着推进的顺序。目标是先做出一个能稳定发消息的飞书桌面端 agent，再往文档、表格、线程回复扩。

### 8.1 第 0 步：先把运行基线稳定住

先不要上来就重构架构。先把当前仓库的执行底盘收敛到一个你能持续回归的状态。

建议先固定 3 件事：

1. grounding 默认复用 `MAIN_*` 配置，确保 `run_agent.py` 和原生 S3 CLI 都能直接跑。
2. 保留真实回归脚本，每次改完都能对当前飞书页面执行一次标准任务。
3. 固化产物目录，把每一步截图、动作、最终状态写到 `artifacts/live_tests/.../summary.json`。

第 0 步的退出条件：

- 你能稳定执行一条固定任务，例如“当前已在某群聊中，清空输入框并发送指定文本”
- 每次回归都能看到 step 截图
- 失败时能从 summary 里定位是“识别错”“点偏了”“输入错地方”“发送未完成”

这一步不 glamorous，但它决定后面是不是在盲改。

### 8.2 第 1 步：先只做一个最小业务闭环

不要同时做消息、文档、表格、审批。先只做一个闭环：

- 打开目标群聊
- 找到输入框
- 输入文本
- 发送
- 验证消息确实发出

建议把这个闭环单独命名为 `SendMessageWorkflow`，后面所有设计都围着它长出来。

这个阶段不要追求：

- 全客户端覆盖
- 全 OS 覆盖
- 所有飞书入口覆盖
- 通用自然语言无约束执行

这个阶段只追求：

- 指定任务稳定完成
- 明确失败分类
- 明确恢复动作

### 8.3 第 2 步：新建飞书专用目录，不要污染通用 S3

建议直接新建下面这套骨架：

```text
gui_agents/feishu/
  __init__.py
  agents/
    __init__.py
    feishu_aci.py
    feishu_worker.py
  detectors/
    __init__.py
    state_detector.py
  workflows/
    __init__.py
    base.py
    send_message.py
  verifiers/
    __init__.py
    completion_gate.py
  router/
    __init__.py
    task_router.py
  memory/
    __init__.py
    procedural_memory.py
```

这样拆的原因很直接：

- `agents/` 放执行与规划
- `detectors/` 放“当前飞书页面是什么”
- `workflows/` 放“这个任务该分几段做”
- `verifiers/` 放“任务到底算不算成功”
- `router/` 放 API / GUI / code 的决策
- `memory/` 放飞书领域提示词和经验检索

如果一开始就把这些逻辑塞回 `gui_agents/s3/agents/worker.py`，几轮之后你就很难分辨一个 bug 是出在通用 agent 还是飞书专用逻辑。

## 9. 第一阶段建议直接实现的文件

### 9.1 `feishu_aci.py`

第一版不要贪多，只做最小动作集：

- `open_chat(chat_name)`
- `focus_message_input()`
- `clear_message_input()`
- `type_message(text)`
- `send_message()`
- `ensure_in_chat(chat_name)`

其中 `open_chat(chat_name)` 不要只封装一个 `click`。它应该允许内部自己走多个策略：

- 直接点击左侧会话列表
- `Ctrl+K` 或客户端搜索
- 搜索结果点击
- 如果已在当前群聊则直接返回

也就是说，`FeishuACI` 应该暴露“语义动作”，而不是“换个名字的 pyautogui 动作”。

### 9.2 `state_detector.py`

建议先定义一个结构化状态对象，例如：

```python
from dataclasses import dataclass


@dataclass
class FeishuState:
    page_type: str
    workspace_name: str | None
    chat_name: str | None
    left_nav_visible: bool
    search_box_visible: bool
    message_input_visible: bool
    send_button_visible: bool
    modal_type: str | None
    last_error_banner: str | None
```

第一版检测不要追求太“智能”，而要追求字段够用。`SendMessageWorkflow` 最少只需要判断：

- 当前是不是聊天页
- 当前群聊标题是不是目标群名
- 输入框是不是可见
- 弹窗有没有挡住

### 9.3 `send_message.py`

建议把 workflow 写成显式阶段机，而不是一段 prompt 文本：

```text
INIT
  -> ENSURE_CHAT_OPEN
  -> ENSURE_INPUT_READY
  -> TYPE_MESSAGE
  -> SEND_MESSAGE
  -> VERIFY_SENT
  -> DONE
```

每个阶段都定义：

- 进入条件
- 执行动作
- 成功判定
- 失败后的 fallback

例如：

- `ENSURE_CHAT_OPEN` 失败 2 次后，不再继续点左侧列表，而是强制切换到搜索策略
- `VERIFY_SENT` 失败时，先检查输入框里是否仍有文本，再决定是重发还是重新定位输入框

### 9.4 `completion_gate.py`

这层是飞书二开里最值钱的部分之一。第一版建议只做这 3 个判断：

1. 会话标题是目标群聊。
2. 底部输入框已清空或失焦，说明发送动作完成。
3. 聊天记录底部或左侧预览出现本次唯一消息 token。

这里非常建议每次真实回归都发唯一消息，比如：

- `hello-codex-1706`
- `smoke-feishu-20260502-1`

这样 verifier 不需要猜“最后一条 hello 是不是刚刚发的”，只要找唯一 token。

### 9.5 `task_router.py`

第一版 router 不需要很复杂，只需要先做显式路由：

- 包含“发消息/回复消息/打开群聊”的任务 -> GUI workflow
- 包含“生成一段内容/整理文本”的任务 -> code agent
- 包含“读写飞书开放平台数据”的任务 -> API path

后面再做 LLM router。不要一开始就把 router 也做成黑盒 prompt。

## 10. 发送消息闭环的具体实现顺序

这一段是更细的“先写什么，再写什么”。

### 10.1 先接 `FeishuStateDetector`

第一版可以直接复用现有截图与 OCR，不要先引入额外基础设施。

建议做法：

1. 从当前 observation 读取 screenshot。
2. 调现有 OCR 提取文本块。
3. 用规则识别群聊标题、输入框、发送按钮、搜索框。
4. 输出 `FeishuState`。

这里的关键不是 100% 准，而是要把状态显式暴露给 workflow。哪怕第一版只是基于 OCR 关键字判断，也比让 LLM 每一步重新猜稳定。

### 10.2 再写 `FeishuACI`

第一版 `FeishuACI` 不需要脱离现有 `OSWorldACI`，建议先继承它：

```python
class FeishuACI(OSWorldACI):
    def open_chat(self, chat_name: str): ...
    def focus_message_input(self): ...
    def clear_message_input(self): ...
    def type_message(self, text: str): ...
    def send_message(self): ...
```

然后内部复用现有底层动作：

- `click(...)`
- `type(...)`
- `hotkey(...)`
- `wait(...)`

你真正要改的是“策略编排”，不是把所有桌面操作重写一遍。

### 10.3 再写 `SendMessageWorkflow`

第一版不要让 worker 自由规划。建议 workflow 先显式调用：

1. `state = detector.detect(observation)`
2. `workflow.next_step(state, task_context)`
3. `aci.<semantic_action>(...)`
4. `verifier.check(...)`

也就是说，第一版甚至可以先少用一点 LLM，而多用显式状态机。原因很简单：你现在的主要问题不是语言理解，而是飞书页面操作稳定性。

### 10.4 最后才把它挂回 `FeishuWorker`

等 `FeishuStateDetector + FeishuACI + SendMessageWorkflow + CompletionGate` 都能单独跑通，再做 `FeishuWorker` 包装：

```text
FeishuWorker
  -> parse task
  -> choose workflow
  -> run workflow loop
  -> ask LLM only when strategy分支不明确
```

这样 LLM 的角色从“每一步都决定怎么点哪里”降成“选择阶段策略和恢复策略”，系统会稳定很多。

## 11. 你现在最该优先做的 6 个能力

如果按投入产出比排序，我建议是下面这 6 个：

1. `ensure_in_chat(chat_name)`：验证当前是否真的进入目标群聊。
2. `focus_message_input()`：稳定找到真正的消息输入框，而不是搜索框。
3. `clear_message_input()`：统一清空旧内容，避免脏输入。
4. `send_message()`：统一发送逻辑，兼容按钮点击和回车发送。
5. `verify_message_sent(unique_token)`：用唯一 token 做完成判定。
6. `recover_from_modal_or_wrong_page()`：遇到弹窗、错误会话、搜索页时能回正。

这 6 个能力一旦稳定，飞书里的很多任务都能拼出来。

## 12. memory 到底怎么接才合理

这部分单独展开，因为你的原始问题就卡在这里。

memory 应该服务于下面几类内容：

- 某类群聊/联系人在你组织里的常见命名模式
- 某版本飞书里稳定可复用的视觉锚点描述
- 某类失败后的恢复策略摘要
- 某个 workflow 的高成功率路径

memory 不应该负责：

- 决定当前页面是什么
- 决定输入框到底在哪
- 决定消息有没有真的发出去
- 定义新的飞书动作

更具体一点：

- `state_detector` 负责“看见什么”
- `workflow` 负责“接下来做什么”
- `verifier` 负责“这步到底成没成”
- `memory` 负责“以前类似情况怎么更快成功”

如果把这四层混在一起，系统会很快退化成“喂更多样例，期待模型自己学会一切”。

## 13. API + GUI 混合路线该怎么落

虽然你现在暂时不考虑飞书 CLI，但 API 路线仍然应该保留，只是不是 bot/CLI 主路径。

建议保留一个本地 `FeishuAPIExecutor`，只做“确实适合 API 的动作”：

- 查询用户/群基础信息
- 查询消息历史
- 创建文档
- 读写表格数据
- 批量生成富文本内容

然后由 `TaskRouter` 明确决定：

- 当前任务必须在真实用户桌面态里完成 -> GUI
- 当前任务更像数据操作 -> API
- 当前任务需要先 GUI 定位上下文，再 API 批量处理 -> hybrid

一个典型 hybrid 例子：

1. GUI 打开某群聊，确认上下文正确。
2. API 拉取最近消息或成员信息。
3. code agent 生成回复内容。
4. GUI 把回复发回当前会话。

这比“全 GUI 硬点”更稳，也比“全 API 假装等价于用户操作”更贴近你的目标。

## 14. 接不接回 UI-TARS，应该怎么判断

你现在决定先不用本地 UI-TARS 模型，这个判断是合理的。当前阶段更重要的是先把飞书专用状态机、验证器和语义动作做出来。

更现实的策略是：

- 第一阶段：主模型兼任 planning + grounding，先跑通最小闭环
- 第二阶段：如果点击精度或小目标识别明显不够，再单独换回专用 grounding
- 第三阶段：如果要做更复杂的视觉子目标执行，再把 UI-TARS SDK 作为下层执行器接回来

也就是说，UI-TARS 不应该是你现在所有工作的前置条件。它应该是后续替换底层执行器的一个增强件。

## 15. 建议的两周推进节奏

如果按两周算，一个比较务实的节奏是：

### 第 1 周

1. 把飞书目录骨架建出来。
2. 实现 `FeishuStateDetector` 第一版。
3. 实现 `FeishuACI` 的最小消息动作集。
4. 实现 `SendMessageWorkflow`。
5. 跑通“当前已在目标群聊中，发送唯一 token 消息”。

### 第 2 周

1. 加 `ensure_in_chat(chat_name)`。
2. 加 `CompletionGate` 的消息唯一 token 验证。
3. 加错误恢复逻辑：误进搜索框、误进其他群聊、弹窗遮挡。
4. 把 `FeishuWorker` 接回自然语言任务入口。
5. 增加第二个 workflow：`ReplyInThreadWorkflow` 或 `OpenChatAndSendWorkflow`。

两周结束时，合理目标不是“飞书全能 agent”，而是：

- 至少 1 个 workflow 高成功率
- 至少 1 个 workflow 有明确 verifier
- 至少 1 套真实回归脚本固定可跑

## 16. 一条更实用的总原则

先把飞书任务拆成“状态 + 语义动作 + verifier + fallback”，再考虑 memory 和专用视觉模型。

因为真正决定你能不能做成二开产品的，不是模型名字，而是：

- 任务是不是被拆成了稳定阶段
- 每个阶段有没有明确完成判定
- 失败时系统会不会退回到可恢复状态

这三件事做好了，后面无论你继续用共享主模型、换回 UI-TARS、还是混入 API，改造成本都会低很多。
