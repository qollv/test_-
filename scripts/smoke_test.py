"""无头冒烟测试：模拟真实主循环与按键，跑通开局→移动→暂停→重开→退出。

不写入项目目录，仅用于验收。
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import pygame

from game import config
from game.core import GameCore, GameState
from game.direction import Action, Direction
from ui.input_handler import InputHandler
from ui.renderer import Renderer

FRAME_MS = 16  # 虚拟每帧耗时（约 60FPS）

pygame.init()
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
renderer = Renderer(screen, config)
handler = InputHandler()
game = GameCore()


def press(key):
    """投递一个按键事件，等价于玩家敲了一下键盘。"""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def pump(frames):
    """跑 frames 帧完整循环：输入 → 计时步进 → 渲染。"""
    acc = 0
    for _ in range(frames):
        for action in handler.poll_actions():
            game.handle(action)
        if game.state is GameState.RUNNING:
            acc += FRAME_MS
            while acc >= config.MOVE_INTERVAL_MS:
                acc -= config.MOVE_INTERVAL_MS
                game.update()
        else:
            acc = 0
        renderer.draw(game)


# 1) READY 画面可渲染
renderer.draw(game)
assert game.state is GameState.READY

# 2) 按 ↑ 开局
press(pygame.K_UP)
pump(1)
assert game.state is GameState.RUNNING, game.state
assert game.snake.direction.name == "UP"

# 3) 一直跑：必然撞到上墙（起点在网格中部，向上约 10 步到顶）
pump(150)
assert game.state is GameState.GAME_OVER, f"未进入结束状态：{game.state}"
renderer.draw(game)  # 结束遮罩可渲染

# 4) 按 R 重开
press(pygame.K_r)
pump(1)
assert game.state is GameState.RUNNING, game.state
assert game.score == 0

# 5) 空格暂停后不再推进
press(pygame.K_SPACE)
pump(1)
assert game.state is GameState.PAUSED, game.state
head_before = game.snake.body[0]
pump(30)
assert game.snake.body[0] == head_before, "暂停时蛇仍在移动"
renderer.draw(game)

# 6) 再按空格继续
press(pygame.K_SPACE)
pump(20)
assert game.snake.body[0] != head_before, "恢复后蛇没有移动"

# 7) 吃食物：把食物放到蛇头正前方
score_before = game.score
length_before = len(game.snake.body)
game.food.position = game.snake.next_head()
pump(10)
assert game.score == score_before + config.SCORE_PER_FOOD, game.score
assert len(game.snake.body) == length_before + 1

# 8) 禁止 180° 掉头：按当前方向的反向键，方向必须保持不变
opposite_key = {
    "UP": pygame.K_DOWN,
    "DOWN": pygame.K_UP,
    "LEFT": pygame.K_RIGHT,
    "RIGHT": pygame.K_LEFT,
}
direction_before = game.snake.direction
press(opposite_key[direction_before.name])
pump(20)
assert game.snake.direction is direction_before, "出现了 180° 掉头"
assert game.state is GameState.RUNNING, game.state

# 8b) 同一格内连按两次（↑ 后 ← 再 ↓）也不能绕过反向检查
game.snake.direction = Direction.UP
press(pygame.K_LEFT)
press(pygame.K_DOWN)
pump(20)
assert game.snake.direction.name == "UP", f"连按绕过了反向检查：{game.snake.direction}"

# 9) Esc 退出
press(pygame.K_ESCAPE)
actions = handler.poll_actions()
assert Action.QUIT in actions, actions
game.handle(Action.QUIT)
assert game.quit_requested

# 10) 点关闭按钮也必须能退出
pygame.event.post(pygame.event.Event(pygame.QUIT))
assert Action.QUIT in handler.poll_actions()

pygame.quit()
print("SMOKE_OK: 开局/移动/撞墙/重开/暂停/恢复/吃食物/禁止掉头/退出 全部通过")
