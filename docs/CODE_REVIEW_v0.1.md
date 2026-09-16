# 贪吃蛇项目 v0.1 · 代码审查报告

- 审查对象：https://github.com/qollv/test_-.git （main 分支，tag v0.1，2 次提交）
- 代码规模：Python 1346 行（game/ 174、ui/ 294、main.py 60、tests/ 364、scripts/ 166）
- 审查方式：静态通读 + 动态验证（隔离 venv，pygame 2.6.1，SDL dummy 无头驱动）
- 总体结论：**通过**，但存在 2 个需修复项与 4 个待办项

## 一、核验通过项

| 核验点 | 结果 |
| --- | --- |
| 单元测试 | 32 个全部通过 |
| 核心逻辑覆盖率（game/） | 97.7%，满足计划文档 ≥80% 要求 |
| 冒烟测试 | 通过（开局/撞墙/重开/暂停/进食/掉头防护/退出） |
| main.main() 真实执行 | 投喂按键后干净退出，无异常 |
| 分层架构约束 | game/ 零 pygame 依赖；renderer 只读 snapshot，不回写状态 |
| 180° 掉头防护 | 有效，含「同一格内连按 ↑←↓」绕过尝试 |
| 棋盘填满通关路径 | 正确：score +10、蛇长 600、GAME_OVER |
| 中文字体渲染 | 正常（Noto Sans CJK SC 命中，实测可出字形） |
| 渲染性能 | 1.0 ms/帧，占 60FPS 预算 6% |
| 版本标记 | v0.1 tag 已存在 |

## 二、需修复（P1）

### P1-1 READY 态按反向键：游戏开始但方向不变

`game/core.py` handle() 119-123 行：初始方向为 RIGHT，玩家在 READY 态按 ←，
`snake.turn()` 因反向被拒绝返回 False，但代码仍无条件将状态置为 RUNNING。

实测：蛇身 `[(15,10),(14,10),(13,10)]`，按 ← 后状态 RUNNING、方向仍为 RIGHT，
推进后蛇头变为 `(16,10)` —— 玩家按左，蛇向右跑。

建议：`turn()` 返回 False 时不开始游戏，保持 READY。

### P1-2 表现层与主入口零单元测试覆盖

README 给出的 `python -m unittest discover -s tests -v` 仅覆盖 58%：
`ui/renderer.py` 105 行、`ui/input_handler.py` 14 行、`main.py` 60 行全部为 0%。

根因：`scripts/smoke_test.py` 虽覆盖了这些代码，但是裸 assert 脚本，
不在 tests/ 目录下，无法被 unittest discover 收集 —— 测试看上去很全，实则有盲区。

建议：将 smoke_test 改写为 `tests/test_smoke.py`（unittest.TestCase），
纳入 discover；renderer 可借 dummy 驱动做绘制冒烟。

## 三、待办（P2）

1. **死代码**：`game/snake.py` `will_hit_self` 的 `pending_grow` 分支不可达 —— 实测 update
   调用前 pending_grow 恒为 0（食物不生成在蛇身，故无「吃食物同时撞尾」场景）。
   注释描述的场景不成立，会误导后续维护者。
2. **验收清单未勾选**：`docs/PROJECT_PLAN.md` 第六节 9 项全部仍为 `- [ ]`，实际均已完成。
3. **仓库污染**：`.Trash-0/info/.coverage.trashinfo`（系统回收站残留）被提交，
   `.gitignore` 未排除该目录。
4. **可优化**：`renderer._draw_overlay` 每帧新建 720×520 Surface，可缓存复用（当前非瓶颈）。

## 四、修复记录（v0.1.1，2026-09-16）

| 编号 | 处理 | 说明 |
| --- | --- | --- |
| P1-1 | 已修复 | `core.handle()` 在 READY 态先判断反向键：与当前方向相反时直接忽略，不开始游戏。<br>**与建议略有出入**：仅在「反向」时不开始；按与初始方向相同的键（如初始朝右按 →）仍然开局，否则玩家按第一个方向键会毫无反应。 |
| P1-2 | 已修复 | 新增 `tests/test_smoke.py`（unittest，dummy 无头驱动），覆盖 ui/ 与主循环；`scripts/smoke_test.py` 已删除。 |
| P2-1 | 已澄清 | 保留 `will_hit_self` 的 pending_grow 分支，但在 docstring 中写明「本作流程中不可达、保留是为了模块语义自洽」，避免误导。 |
| P2-2 | 已完成 | 第六节 9 项验收清单全部勾选。 |
| P2-3 | 已清理 | `.Trash-0/` 移出版本库并加入 `.gitignore`（连带补 `.workbuddy/`）。 |
| P2-4 | 已优化 | 遮罩 Surface 改为构造时创建、每帧复用。 |

补充：新增 `MainLoopTest` 真实调用 `main()`（含用假时钟跑满多帧的用例），
使 `main.py` 覆盖率从 0% 提升到 97%；整体覆盖率 96%。

## 五、复现环境

- 隔离 venv：`/home/qhr/.workbuddy/binaries/python/envs/default`（pygame 2.6.1、coverage）
- 无头运行：`SDL_VIDEODRIVER=dummy`
- 注：`fc-list timed-out` 仅为告警，字体经 `match_font` 仍正常命中，不影响中文显示。
