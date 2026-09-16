"""表现层输入处理器（InputHandler）。

职责：从 pygame 事件队列拉取玩家输入，翻译成 game.direction.Action。
本模块是「唯一允许 import pygame」的表现层之一，契约要求：
- poll_actions() 拉取并清空事件队列，按事件原始顺序返回 Action 列表；
- 必须处理 pygame.QUIT（点窗口关闭按钮），否则窗口关不掉；
- 所有键位映射固定如下，且只产出 Action，不触碰游戏状态。

键位映射：
    ↑↓←→ 与 W A S D → 转向 Action
    空格 / P            → Action.PAUSE
    R                  → Action.RESTART
    Esc / pygame.QUIT  → Action.QUIT
"""

import pygame

from game.direction import Action

# 键盘按键（pygame 常量）到 Action 的映射表
_KEY_TO_ACTION: dict[int, Action] = {
    pygame.K_UP: Action.TURN_UP,
    pygame.K_DOWN: Action.TURN_DOWN,
    pygame.K_LEFT: Action.TURN_LEFT,
    pygame.K_RIGHT: Action.TURN_RIGHT,
    pygame.K_w: Action.TURN_UP,
    pygame.K_a: Action.TURN_LEFT,
    pygame.K_s: Action.TURN_DOWN,
    pygame.K_d: Action.TURN_RIGHT,
    pygame.K_SPACE: Action.PAUSE,
    pygame.K_p: Action.PAUSE,
    pygame.K_r: Action.RESTART,
    pygame.K_ESCAPE: Action.QUIT,
}


class InputHandler:
    """把 pygame 事件流转换为 Action 列表。

    构造时不依赖任何参数，调用 poll_actions() 时才去读事件队列。
    """

    def poll_actions(self) -> list[Action]:
        """拉取并清空 pygame 事件队列，按原始顺序返回 Action 列表。

        返回：
            本次循环中玩家触发的 Action；无输入则返回空列表。
        """
        actions: list[Action] = []
        # 处理全部待处理事件（读后队列即清空）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 点窗口关闭按钮：始终视为退出
                actions.append(Action.QUIT)
            elif event.type == pygame.KEYDOWN:
                action = _KEY_TO_ACTION.get(event.key)
                if action is not None:
                    actions.append(action)
        return actions
