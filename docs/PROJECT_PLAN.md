# 贪吃蛇小游戏 · 项目计划 v0.1

## 一、目标与范围

用 Python + pygame 实现一个可玩、可测、可维护的贪吃蛇。

- **可玩**：窗口正常、转向/暂停/重开/退出齐全、速度稳定。
- **可测**：核心逻辑（蛇、食物、状态机）不依赖 pygame，纯 `unittest` 覆盖。
- **可维护**：常量集中、类型注解齐全、中文注释、模块职责单一。

范围外（v0.1 不做）：排行榜、音效、难度递增、穿墙模式、联网对战。

## 二、目录结构

```
.
├── main.py                 # 程序入口：创建窗口、主循环、退出
├── game/                   # 核心逻辑层（禁止 import pygame）
│   ├── config.py           # 全局常量
│   ├── direction.py        # Direction / Action 枚举
│   ├── snake.py            # 蛇身数据结构与行为
│   ├── food.py             # 食物生成
│   └── core.py             # 游戏状态机与单步推进
├── ui/                     # 表现层（唯一允许 import pygame 的地方）
│   ├── renderer.py         # 渲染
│   └── input_handler.py    # 输入处理
├── tests/                  # 单元测试（unittest）
│   ├── test_snake.py
│   ├── test_food.py
│   └── test_core.py
└── docs/PROJECT_PLAN.md    # 本文档
```

## 三、接口契约

### 3.1 Direction / Action（`game/direction.py`）

```python
class Direction(Enum):
    UP = (0, -1); DOWN = (0, 1); LEFT = (-1, 0); RIGHT = (1, 0)
    # .opposite -> Direction       反向，用于禁止 180° 掉头
    # direction + (x, y) -> (x+dx, y+dy)

class Action(Enum):
    TURN_UP / TURN_DOWN / TURN_LEFT / TURN_RIGHT / PAUSE / RESTART / QUIT

ACTION_TO_DIRECTION: dict[Action, Direction]  # 仅含四个转向动作
```

### 3.2 Snake（`game/snake.py`）

```python
Snake(start_pos, start_direction=Direction.RIGHT, initial_length=3)
# 属性
body: list[tuple[int, int]]   # body[0] 为蛇头
direction: Direction
pending_grow: int             # 待增长格数，由 GameCore 吃到食物时 +1
# 方法
turn(new_direction) -> bool   # 反向时拒绝并返回 False，否则 True
next_head() -> tuple[int, int]# 不修改状态地返回下一格坐标
step() -> None                # 插入新头；pending_grow>0 时消耗并保留蛇尾，否则弹尾
occupies(pos) -> bool
will_hit_self(pos) -> bool    # 蛇尾当帧会让位，贴着尾巴走不算撞
```

约束：禁止 `import pygame`；禁止随机数。

### 3.3 Food（`game/food.py`）

```python
Food(grid_width, grid_height, rng: random.Random | None = None)
position: tuple[int, int]
respawn(occupied: set[tuple[int, int]]) -> tuple[int, int]
```

- 只在未占用的格子中生成；棋盘已满时抛出 `BoardFullError`。
- 约束：禁止 `import pygame`；禁用全局 `random`，统一使用注入的 `rng`。

### 3.4 GameCore（`game/core.py`）

```python
class GameState(Enum): READY / RUNNING / PAUSED / GAME_OVER

GameCore(config=None, rng=None)
# 属性：snake / food / score / state
handle(action) -> None    # RUNNING 才响应转向；READY 下转向即开局；RESTART 重开；QUIT 置 state
                          # 注意：RUNNING 下的转向只记入待办，由下一次 update 统一应用，
                          # 防止一个步进间隔内连按两次组合出 180° 掉头
update() -> None          # 非 RUNNING 直接返回；否则 移动 → 撞墙/撞身 → 吃食物 → 计分(+10)
reset() -> None           # 重置局面与分数，回到 READY，随机种子不变
snapshot() -> dict        # {"snake": [...], "food": (x, y), "score": int,
                          #  "state": GameState, "grid_width": int, "grid_height": int}
```

`snapshot()` 是渲染层唯一的数据来源，保证表现层只读、不修改游戏状态。

### 3.5 Renderer（`ui/renderer.py`）

```python
Renderer(screen: pygame.Surface, config)
draw(game: GameCore) -> None
```

绘制顺序：背景 → 网格 → 食物 → 蛇 → HUD(分数) → 状态遮罩。
READY 显示「按方向键开始」，PAUSED 显示「已暂停」，GAME_OVER 半透明遮罩 + 最终得分 + 「按 R 重开」。
所有颜色取自 `config.py`。

### 3.6 InputHandler（`ui/input_handler.py`）

```python
poll_actions() -> list[Action]
```

键位：方向键与 WASD → 转向；空格 / P → 暂停；R → 重开；Esc / 窗口关闭 → 退出。
必须处理 `pygame.QUIT`，否则窗口关不掉。返回顺序与事件原始顺序一致。

## 四、开发顺序与并行策略

| 编号 | 模块 | 依赖 | 可并行 |
| --- | --- | --- | --- |
| A | 地基（目录/config/direction/git） | - | 先行 |
| B | Snake + 单测 | A | 与 C/F 并行 |
| C | Food + 单测 | A | 与 B/F 并行 |
| D | GameCore + 单测 | B、C（可按契约先行） | B/C 之后 |
| E | Renderer | A、D 的 snapshot 契约 | 按契约并行 |
| F | InputHandler | A 的 Action | 按契约并行 |
| G | main.py 主循环 | D、E、F | 最后集成 |
| H | 验收与发布 | A~G | 收尾 |

模块间只依赖「契约」而非「实现」，因此 B/C/E/F 可由不同开发者（或子 agent）同时开工。

## 五、编码规范

1. 常量全部收进 `game/config.py`，业务代码禁止裸数字。
2. 公开函数/方法带类型注解，模块与关键函数写中文 docstring/注释。
3. 核心逻辑层（game/）不得 import pygame，保证可无头测试。
4. 测试使用标准库 `unittest`，运行方式：`python -m unittest discover -s tests -v`。
5. 随机性一律通过注入 `random.Random` 实例，测试可复现。

## 六、验收清单（v0.1 完成的定义）

> 状态：v0.1 全部达成（2026-09-16 验收，详见 docs/CODE_REVIEW_v0.1.md）。

- [x] `python main.py` 可直接运行，窗口正常，无报错
- [x] 方向键转向，禁止 180° 掉头自杀（含「同一格内连按两次」绕过尝试）
- [x] 吃食物蛇身 +1、分数 +10，食物重生且不落在蛇身上
- [x] 撞墙 / 撞自己 → GAME_OVER 并显示最终得分
- [x] 空格暂停、R 重开、Esc 退出
- [x] `python -m unittest discover tests` 全部通过，核心逻辑覆盖率 ≥ 80%（实测 96%+）
- [x] README 补全：安装依赖、启动方式、操作说明、目录结构
- [x] 代码检查：注释齐全、无裸数字、统一代码风格
- [x] 打 v0.1 tag 并推送 https://github.com/qollv/test_-.git

## 七、运行方式

```bash
pip install -r requirements.txt     # 安装依赖
python main.py                      # 启动游戏
python -m unittest discover -s tests -v   # 跑测试
```
