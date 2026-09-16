"""游戏状态机与单步推进（核心逻辑层）。

职责：把 Snake、Food 组合成一局游戏，管理状态流转与计分。
约束：
- 禁止 import pygame，保证可无头单元测试；
- 表现层只能通过 snapshot() 读取数据，不得反向修改状态；
- 随机性统一来自注入的 random.Random 实例，测试可复现。
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Any

from game import config as default_config
from game.direction import ACTION_TO_DIRECTION, Action, Direction
from game.food import BoardFullError, Food
from game.snake import Snake


class GameState(Enum):
    """一局游戏的四种状态。

    READY：等待玩家按方向键开始；
    RUNNING：正常推进；
    PAUSED：暂停，update() 不再推进；
    GAME_OVER：撞墙或撞到自己，等待玩家按 R 重开。
    """

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class GameCore:
    """一局贪吃蛇的完整状态。

    对外只暴露 snake / food / score / state 与 handle、update、reset、snapshot
    四组能力，渲染层与输入层都不直接改动内部数据。
    """

    def __init__(
        self,
        config: Any | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """初始化一局游戏。

        :param config: 配置模块，默认使用 game.config
        :param rng: 随机源，注入后 reset() 不会重置种子，便于测试复现
        """
        self._config = config if config is not None else default_config
        self._rng = rng if rng is not None else random.Random()
        self.quit_requested: bool = False
        # 构造即完成一次初始化，保证所有属性始终可用
        self.reset()

    # ------------------------------------------------------------------ 生命周期
    def reset(self) -> None:
        """重置局面：蛇回到初始位置、分数归零、状态回到 READY。

        注意：随机种子不会被重置，注入的 rng 继续推进，便于测试复现。
        """
        self.snake = Snake(
            start_pos=self._config.START_POSITION,
            start_direction=Direction[self._config.START_DIRECTION],
            initial_length=self._config.INITIAL_SNAKE_LENGTH,
        )
        self.food = Food(
            self._config.GRID_WIDTH,
            self._config.GRID_HEIGHT,
            self._rng,
        )
        # 食物不能生成在蛇身上
        self.food.respawn(set(self.snake.body))
        self.score: int = 0
        self.state: GameState = GameState.READY
        # 待应用的转向：RUNNING 下不立即转向，留给下一次 update 统一处理
        self._pending_direction: Direction | None = None

    def handle(self, action: Action) -> None:
        """处理一个外部指令，只在合法状态下生效。

        规则：
        - QUIT：任何状态下都响应，置 quit_requested（由主循环退出）；
        - RESTART：重置局面并直接进入 RUNNING；
        - PAUSE：RUNNING ↔ PAUSED 切换；
        - 转向：RUNNING 时转向；READY 时同时兼具「开始游戏」的作用。

        转向为什么不在 RUNNING 下立即生效？
        若立即生效，玩家在一个步进间隔内连按两次（如 ↑ 后马上 ← 再 ↓）时，
        第二次转向是相对「尚未移动的蛇身」判断的，可能组合出 180° 掉头并撞死。
        因此 RUNNING 下只记录待办方向，由下一次 update() 统一应用，
        这样同一格内的多次按键只会留下最后一次，且仍受反向检查约束。
        """
        if action is Action.QUIT:
            self.quit_requested = True
            return

        if action is Action.RESTART:
            self.reset()
            self.state = GameState.RUNNING
            return

        if action is Action.PAUSE:
            if self.state is GameState.RUNNING:
                self.state = GameState.PAUSED
            elif self.state is GameState.PAUSED:
                self.state = GameState.RUNNING
            return

        direction = ACTION_TO_DIRECTION.get(action)
        if direction is None:
            # 非转向类指令（本版本未定义），忽略
            return

        if self.state is GameState.READY:
            # READY 下按方向键即开局，但必须排除「反向键」：
            # 蛇初始朝右时按 ← 属于 180° 掉头，此时不能开局，
            # 否则会出现「玩家按左、蛇向右跑」的错觉。
            if direction == self.snake.direction.opposite:
                return
            # 与当前方向相同的按键 turn() 会拒绝（返回 False），
            # 但方向本来就是它，游戏照常开始。
            self.snake.turn(direction)
            self.state = GameState.RUNNING
        elif self.state is GameState.RUNNING:
            self._pending_direction = direction

    def update(self) -> None:
        """推进一格。非 RUNNING 状态直接返回。

        顺序：判定下一格 → 撞墙/撞身则 GAME_OVER → 吃食物则增长计分 → 移动。
        """
        if self.state is not GameState.RUNNING:
            return

        # 先应用待办转向（同一格内的多次按键只留最后一次，且仍受反向检查）
        if self._pending_direction is not None:
            self.snake.turn(self._pending_direction)
            self._pending_direction = None

        next_pos = self.snake.next_head()
        if self._is_out_of_grid(next_pos) or self.snake.will_hit_self(next_pos):
            self.state = GameState.GAME_OVER
            return

        # 吃到食物：先标记增长，step() 后蛇尾保留，蛇身变长
        eating = next_pos == self.food.position
        if eating:
            self.snake.pending_grow += 1

        self.snake.step()

        if eating:
            self.score += self._config.SCORE_PER_FOOD
            try:
                # 必须在 step() 之后重生，否则食物可能落在新的蛇头上
                self.food.respawn(set(self.snake.body))
            except BoardFullError:
                # 棋盘被蛇填满，已无空位生成食物，视作通关并结束本局
                self.state = GameState.GAME_OVER

    def snapshot(self) -> dict[str, Any]:
        """返回渲染层所需的只读状态快照。

        :return: 包含蛇身、食物、分数、状态与网格尺寸的字典
        """
        return {
            "snake": list(self.snake.body),
            "food": self.food.position,
            "score": self.score,
            "state": self.state,
            "grid_width": self._config.GRID_WIDTH,
            "grid_height": self._config.GRID_HEIGHT,
        }

    # ------------------------------------------------------------------ 内部工具
    def _is_out_of_grid(self, pos: tuple[int, int]) -> bool:
        """判断坐标是否越出网格边界。"""
        x, y = pos
        return not (
            0 <= x < self._config.GRID_WIDTH and 0 <= y < self._config.GRID_HEIGHT
        )
