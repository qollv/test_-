"""程序入口：创建窗口、驱动主循环、干净退出。

运行方式：
    python main.py

主循环要点：
- 输入：每帧拉取一次 Action 列表，交给 GameCore.handle；
- 步进：累加真实经过的时间，每满 MOVE_INTERVAL_MS 才推进一格，
  这样蛇的速度与渲染帧率解耦（FPS 变化不影响手感）；
- 渲染：每帧全量重绘；
- 退出：收到 QUIT 后跳出循环并调用 pygame.quit()。
"""

import pygame

from game import config
from game.core import GameCore, GameState
from ui.input_handler import InputHandler
from ui.renderer import Renderer


def main() -> None:
    """启动游戏，直到玩家退出。"""
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption(config.WINDOW_TITLE)
    clock = pygame.time.Clock()

    game = GameCore()
    renderer = Renderer(screen, config)
    input_handler = InputHandler()

    # 时间累加器：记录距离下一次移动还差多少毫秒
    elapsed_since_move = 0

    while True:
        # 1) 处理输入：逐个交给状态机，QUIT 由状态机记录
        for action in input_handler.poll_actions():
            game.handle(action)
        if game.quit_requested:
            break

        # 2) 按真实时间推进：暂停/未开局时不累加，避免恢复后瞬移
        frame_ms = clock.tick(config.FPS)
        if game.state is GameState.RUNNING:
            elapsed_since_move += frame_ms
            while elapsed_since_move >= config.MOVE_INTERVAL_MS:
                elapsed_since_move -= config.MOVE_INTERVAL_MS
                game.update()
        else:
            elapsed_since_move = 0

        # 3) 渲染当前帧
        renderer.draw(game)

    pygame.quit()


if __name__ == "__main__":
    main()
