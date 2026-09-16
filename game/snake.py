"""蛇身数据结构与行为。

本模块是核心逻辑层的一部分，禁止 import pygame，也不使用随机数，
以便在没有图形界面的环境下做纯单元测试。

蛇身用有序列表 `body` 表示：`body[0]` 是蛇头，`body[-1]` 是蛇尾。
坐标系与 direction.py 保持一致：x 向右增大，y 向下增大。
"""

from game.config import INITIAL_SNAKE_LENGTH
from game.direction import Direction


class Snake:
    """贪吃蛇的蛇身与基础行为。

    构造函数会从起始坐标沿「初始方向的反方向」依次排开，共生成
    ``initial_length`` 节蛇身。例如初始长度 3、方向 RIGHT、起始 (5,5) 时，
    body = [(5,5), (4,5), (3,5)]（蛇头在最前）。
    """

    def __init__(
        self,
        start_pos: tuple[int, int],
        start_direction: Direction = Direction.RIGHT,
        initial_length: int = INITIAL_SNAKE_LENGTH,
    ) -> None:
        if initial_length < 1:
            raise ValueError("initial_length 必须 ≥ 1")
        self.direction: Direction = start_direction
        # 还需增长几格；GameCore 吃到食物时会 +1，step 时消耗
        self.pending_grow: int = 0
        # 构造蛇身：蛇头在 start_pos，其余节沿初始方向的反方向排开
        self.body: list[tuple[int, int]] = [start_pos]
        for _ in range(initial_length - 1):
            self.body.append(start_direction.opposite + self.body[-1])

    def turn(self, new_direction: Direction) -> bool:
        """尝试转向。

        与当前方向相反（180° 掉头）或相同方向都拒绝，返回 False；
        其余合法转向接受并返回 True。
        """
        if new_direction == self.direction or new_direction == self.direction.opposite:
            return False
        self.direction = new_direction
        return True

    def next_head(self) -> tuple[int, int]:
        """只计算下一格坐标，不修改任何状态。"""
        return self.direction + self.body[0]

    def step(self) -> None:
        """前进一步：插入新头。

        若 pending_grow > 0，则消耗一格增长并保留蛇尾（蛇变长）；
        否则弹出蛇尾（蛇长不变）。
        """
        self.body.insert(0, self.next_head())
        if self.pending_grow > 0:
            self.pending_grow -= 1
        else:
            self.body.pop()

    def occupies(self, pos: tuple[int, int]) -> bool:
        """该坐标是否被当前蛇身覆盖。"""
        return pos in self.body

    def will_hit_self(self, pos: tuple[int, int]) -> bool:
        """移动到 pos 是否会撞到自己。

        边界处理：蛇尾在本帧会让位——当 pending_grow == 0 时，下一帧蛇尾
        会被弹出，因此「贴着尾巴走」（pos 恰好等于当前蛇尾）不算自撞，返回
        False；当 pending_grow > 0 时蛇尾不动，撞到蛇尾算自撞，返回 True。
        蛇头自身也会移动，但 next_head 计算出的 pos 永远与当前蛇头不重合，
        故无需单独排除蛇头。

        关于 pending_grow > 0 分支的可达性：在当前 GameCore.update() 的
        顺序里（先判碰撞 → 再加 pending_grow → 再 step），每次判定前
        pending_grow 恒为 0，因此该分支在完整对局中不会被触发。这里保留它，
        是为了让 Snake 作为独立模块时语义自洽（调用方可以先 pending_grow = n
        再连续 step），并由 tests/test_snake.py 直接覆盖。请勿据此假设
        「吃食物的同时撞到蛇尾」存在——该场景在本作中不会发生。
        """
        if pos == self.body[-1] and self.pending_grow == 0:
            return False
        return pos in self.body
