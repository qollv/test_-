"""食物生成模块（核心逻辑层）。

职责：在网格内随机挑选一个「未被占用」的格子作为食物坐标。
约束：
- 禁止 import pygame（保证无头可测）；
- 禁止直接使用全局 random 模块的函数，所有随机性都走注入的 `rng`
  （random.Random 实例），以便测试用固定种子复现。
"""

from __future__ import annotations

import random
from typing import Optional, Set, Tuple

# 类型别名：网格坐标 (x, y)
GridPos = Tuple[int, int]


class BoardFullError(Exception):
    """棋盘已被占满、没有空位可生成食物时抛出。"""


class Food:
    """网格食物。

    只在「网格内且不在 occupied 中」的格子里随机生成食物坐标。
    """

    def __init__(
        self,
        grid_width: int,
        grid_height: int,
        rng: Optional[random.Random] = None,
    ) -> None:
        """初始化食物并生成初始坐标。

        :param grid_width: 横向格子数
        :param grid_height: 纵向格子数
        :param rng: 注入的随机源；为空时内部创建一个独立实例
        """
        self._grid_width = grid_width
        self._grid_height = grid_height
        # 未注入则自建随机实例（不使用全局 random 函数）
        self._rng = rng if rng is not None else random.Random()
        # 构造后立刻生成初始位置（空棋盘上随机取一格）
        self.position: GridPos = self.respawn(set())

    def respawn(self, occupied: Set[GridPos]) -> GridPos:
        """重新生成食物坐标。

        在「网格内且不在 occupied 中」的格子里随机选取一个，
        更新并返回 self.position。无任何可用格子时抛 BoardFullError。

        :param occupied: 已被占用的坐标集合（如蛇身）
        :return: 新生成的食物坐标 (x, y)
        """
        # 直接构造候选格子集合，避免使用 rng 反复重试导致退化
        candidates: Set[GridPos] = {
            (x, y)
            for x in range(self._grid_width)
            for y in range(self._grid_height)
            if (x, y) not in occupied
        }

        if not candidates:
            raise BoardFullError("棋盘已被完全占用，无法生成食物")

        # 用注入的随机源在候选集合中随机选取
        new_pos = self._rng.choice(tuple(candidates))
        self.position = new_pos
        return new_pos
