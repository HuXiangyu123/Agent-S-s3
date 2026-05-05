# 接口兼容性指南

最后更新：2026-05-05

## 1. 当前默认入口

当前默认 CLI 入口仍是：

```python
from gui_agents.s3.agents.grounding import OSWorldACI
```

对应文件：

- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/agents/grounding.py`

这意味着当前默认主线是 `vision-first`，调用方只应假设通用动作可用，例如：

- `agent.open(...)`
- `agent.click(...)`
- `agent.type(...)`
- `agent.hotkey(...)`
- `agent.wait(...)`

补充说明：

- `classic_s3` 仍走上述默认入口
- `feishu_agent` 现在不再走独立 `feishu_worker` runtime，而是走 `AgentS3 + WindowsFeishuACI + 动态 Feishu tool guidance`
- 因此，“飞书增强模式”与“默认通用模式”共享同一套 `AgentS3 -> Worker` 执行主链，只是 grounding agent 和运行时 guidance 不同

## 2. Feishu / Windows 专用扩展的当前状态

仓库中仍保留以下 Feishu / Windows 专用实现：

- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/agents/_feishu_exec.py`

其中定义了额外 helper，例如：

- `feishu_focus()`
- `feishu_click(...)`
- `feishu_type(...)`
- `feishu_doc_click(...)`
- `feishu_doc_type(...)`

这些 helper 仍然不是 `classic_s3` 的默认入口契约。只有在入口显式切到：

```python
from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI as OSWorldACI
```

时，才可以把上述方法当成可用能力。

当前仓库内这个显式切换已经存在于 `feishu_agent` 执行模式中。

## 3. 兼容性口径

### CLI 参数

当前默认入口仍需要显式传入 grounding 配置：

```bash
python gui_agents/s3/cli_app.py \
  --provider openai \
  --model <main_model_id> \
  --model_url <main_model_url> \
  --model_api_key <main_model_key> \
  --ground_provider <ground_provider> \
  --ground_url <ground_model_url> \
  --ground_api_key <ground_model_key> \
  --ground_model <ground_model_id> \
  --grounding_width 1000 \
  --grounding_height 1000
```

说明：

- `--grounding_width` / `--grounding_height` 仍是当前入口要求的必填参数
- `--budget` 当前默认值以 `cli_app.py` 为准，不应再沿用旧文档里的历史数值
- 若某个 launcher 对这些参数做了包装或覆写，应以 launcher 实际实现为准

### Python API

默认主线写法：

```python
from gui_agents.s3.agents.grounding import OSWorldACI

agent = OSWorldACI(...)
agent.click("发送按钮")
agent.type("hello")
```

可选扩展写法：

```python
from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI as OSWorldACI

agent = OSWorldACI(...)
agent.feishu_click("飞书按钮")
```

约束：

- 不要把可选扩展写成默认兼容事实
- 如果某段文档或 prompt 使用了 `feishu_*` 方法，必须先确认当前入口是否真的接入 `WindowsFeishuACI`
- 现在 `feishu_agent` 模式已经满足这个前提，但 `classic_s3` 仍不满足

## 4. 浏览器态与桌面态的使用边界

若后续重新启用 Feishu / Windows 专用 helper，推荐口径如下：

1. 飞书桌面端原生控件：`feishu_click` / `feishu_type`
2. 浏览器云文档顶部工具栏：`feishu_doc_click`
3. 浏览器正文和页面内容：`agent.click` / `agent.type`
4. 浏览器分享弹窗已自动聚焦输入框：`feishu_doc_type`

在默认入口未接线前，上述规则只能视为历史/可选路线，不能当成当前主线承诺。

## 5. 迁移检查清单

- [ ] 若文档写了“`cli_app.py` 已自动切到 `WindowsFeishuACI`”，请删除或改正
- [ ] 若调用方直接使用 `agent.feishu_click(...)`，先确认入口是否已切到 `grounding_feishu.py`
- [ ] 若需求只是恢复当前可跑基线，优先使用默认 `OSWorldACI` 主线，不要先碰 UIA / Accessibility
- [ ] 若要恢复 UIA 路线，先更新 `spec`、`interfaces`、freeze 记录，再改入口
- [ ] 若要增强飞书桌面端能力，优先沿 `feishu_agent -> AgentS3 + WindowsFeishuACI + tool guidance` 路线扩展，不要再新增平行 runtime

## 6. 历史说明

旧版兼容性文档里关于以下表述已不再代表当前默认主线：

- “`cli_app.py` 自动处理了切换”
- “用户代码默认应改为 `WindowsFeishuACI`”
- “Feishu UIA helper 已在默认入口生效”

这些内容如需保留，应按历史决策或历史迁移说明处理，不应继续作为当前实现事实。
