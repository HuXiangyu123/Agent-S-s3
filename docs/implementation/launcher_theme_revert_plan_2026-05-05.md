# Launcher Theme Revert Plan (2026-05-05)

## Goal

将 `launcher.py` 的启动器视觉主题从当前深色方案回退到此前较清新的浅色方案，恢复更接近旧版 `ae9dba1` 的观感，同时不影响现有主模型/定位模型/连通性测试等功能逻辑。

## Problem Summary

当前启动器主题在 `ec895ea` 被整体切换为深色：

- `bg`: `#0b1220`
- `panel`: `#121b2d`
- `panel_alt`: `#182338`
- `text`: `#edf4ff`
- `log_bg`: `#08111d`

用户反馈当前视觉效果过重、过暗，和之前的清新风格相比明显退化。

经对比 Git 历史：

- `ae9dba1`: 使用浅色清新主题
- `ec895ea`: 切换到当前深色主题

因此本次应基于 `ae9dba1` 的主题值做回退，而不是重新发明一套新主题。

## Source Of Truth

1. `AGENTS.md`
2. `launcher.py`
3. `git show ae9dba1:launcher.py`
4. `git diff ae9dba1..ec895ea -- launcher.py`

## Scope

### In Scope

- `launcher.py` 中 `self.colors` 的主题色回退
- `ttk.Style()` 里与颜色直接相关的样式回退
- `status_badge` 的浅色状态色回退
- 日志标签颜色与输入框背景的浅色适配

### Out Of Scope

- 启动器布局结构
- Provider 路由
- Doubao / OpenAI 配置逻辑
- 运行时 CLI 参数
- SOP 功能逻辑

## Module Boundary

本次是纯视觉层修复，原则是：

1. 不修改事件流程
2. 不修改配置存储结构
3. 不修改模型调用参数
4. 只恢复主题常量和样式映射

## Target Files

- `launcher.py`

## Reference Palette

计划以 `ae9dba1` 为准，恢复以下主色：

- `bg`: `#f5f5f7`
- `panel`: `#ffffff`
- `panel_alt`: `#f0f0f2`
- `border`: `#e0e0e4`
- `text`: `#1d1d1f`
- `muted`: `#86868b`
- `accent`: `#4a6cf7`
- `accent_alt`: `#34c759`
- `warn`: `#ff9f0a`
- `danger`: `#ff3b30`
- `success`: `#34c759`
- `log_bg`: `#fafafa`

同时恢复浅色状态 badge：

- `idle`: `#e5e5ea`
- `starting`: `#d6e0fd`
- `running`: `#d1f0dd`
- `ready`: `#c8f0d4`
- `saved`: `#fdf0d1`
- `stopped`: `#fddddd`

## Implementation Plan

1. 将 `self.colors` 从深色主题回退到 `ae9dba1` 的浅色主题。
2. 回退 `TEntry` / `TCombobox` 到浅色输入框表现，不保留当前深色输入底。
3. 回退 `Primary.TButton` / `Subtle.TButton` / `Danger.TButton` 的前景色，使其适配浅底。
4. 回退 `status_badge` 默认背景和 `_set_status()` 状态色映射。
5. 保留 `ec895ea` 引入的非视觉逻辑改动，不做整文件回滚。

## TODO

1. 提取 `ae9dba1` 的主题常量并映射到当前 `launcher.py`
2. 只改视觉相关代码，避免误伤后续功能改动
3. 本地做语法检查
4. 运行启动器做人工目视确认

## Verification

自动验证：

- `python -m compileall launcher.py`

人工验证：

1. 启动 launcher
2. 检查 hero、card、tab、输入框、按钮、日志框是否恢复浅色清新风格
3. 检查状态 badge 在 idle / starting / ready 等状态下是否可读
4. 检查 Combobox 下拉列表文字与背景对比是否正常

## Risks

1. 当前代码在深色主题下新增了 `button_text`、`input_bg`、`input_text` 等字段，回退时若处理不干净，可能出现文字颜色不匹配。
2. 如果只回退部分颜色，不回退状态色和输入框色，会出现“浅底深控件”混搭。
3. Windows 下 `ttk` 主题在不同机器可能略有差异，需要至少人工看一遍。

## Rollback

若本次回退视觉效果仍不理想：

1. 保留本次计划文档
2. 回退 `launcher.py` 中主题相关改动
3. 重新基于旧版浅色主题做二次微调，而不是恢复深色方案
