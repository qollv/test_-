"""方向与动作枚举。

Direction 描述「蛇当前朝哪儿走」，Action 描述「玩家/外部想做什么」。
两者分离的意义：输入层只认识 Action，核心逻辑只认识 Direction，
中间用 ACTION_TO_DIRECTION 做一次翻译，避免键盘细节泄漏到游戏逻辑里。
"""

from enum import Enum


class Direction(Enum):
    """四个移动方向，值为 (dx, dy) 位移向量。

    坐标系：x 向右增大，y 向下增大（与 pygame 屏幕坐标一致）。
    """

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        """返回反方向。用于禁止 180° 掉头自杀。"""
        return _OPPOSITES[self]

    def __add__(self, position: tuple[int, int]) -> tuple[int, int]:
        """方便写 `direction + head` 得到下一格坐标。"""
        dx, dy = self.value
        x, y = position
        return (x + dx, y + dy)


# 反向映射放在模块级：若写在类体内会被 Enum 误当成枚举成员
_OPPOSITES: dict["Direction", "Direction"] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


class Action(Enum):
    """外部可下达的指令。输入层负责把键盘/鼠标事件翻译成 Action。"""

    TURN_UP = "turn_up"
    TURN_DOWN = "turn_down"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    PAUSE = "pause"
    RESTART = "restart"
    QUIT = "quit"


# 转向类 Action 到 Direction 的映射（其余 Action 不在表中）
ACTION_TO_DIRECTION: dict["Action", "Direction"] = {
    Action.TURN_UP: Direction.UP,
    Action.TURN_DOWN: Direction.DOWN,
    Action.TURN_LEFT: Direction.LEFT,
    Action.TURN_RIGHT: Direction.RIGHT,
}
