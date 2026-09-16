"""生成三态预览图（READY / RUNNING / GAME_OVER），用于文档与验收展示。"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game import config
from game.core import GameCore, GameState
from game.direction import Direction
from ui.renderer import Renderer

W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
OUT = "/home/qhr/WorkBuddy/2026-09-16-11-59-46/docs/preview.png"

pygame.init()
pygame.display.set_mode((W, H))
sheet = pygame.Surface((W, H * 3))

game = GameCore()
# 造一条有辨识度的蛇与一个食物，便于展示
game.snake.body = [(8, 10), (7, 10), (6, 10), (6, 11), (6, 12), (5, 12)]
game.snake.direction = Direction.RIGHT
game.food.position = (12, 10)

for index, state in enumerate(
    (GameState.READY, GameState.RUNNING, GameState.GAME_OVER)
):
    game.state = state
    game.score = 30 if state is not GameState.READY else 0
    sub = sheet.subsurface(pygame.Rect(0, index * H, W, H))
    Renderer(sub, config).draw(game)

pygame.image.save(sheet, OUT)
pygame.quit()
print("preview saved:", OUT)
