"""表现层渲染器（Renderer）。

职责：把 GameCore 的只读快照 `snapshot()` 画到 pygame 窗口上。
本模块是「唯一允许 import pygame」的表现层之一，但严格遵守契约：
- 只读 `game.snapshot()`，绝不修改任何游戏状态；
- 所有颜色 / 尺寸 / 文字一律取自 `game.config`，禁止裸数字；
- 绘制顺序固定：背景 → 网格线 → 食物 → 蛇 → HUD 分数栏 → 状态遮罩。
"""

import pygame

from game.config import (
    COLOR_BACKGROUND,
    COLOR_FOOD,
    COLOR_GRID_LINE,
    COLOR_HUD_BACKGROUND,
    COLOR_OVERLAY,
    COLOR_SNAKE_BODY,
    COLOR_SNAKE_HEAD,
    COLOR_TEXT,
    CELL_SIZE,
    FONT_CANDIDATES,
    FONT_FILE_CANDIDATES,
    FONT_SIZE_LARGE,
    FONT_SIZE_SMALL,
    HUD_HEIGHT,
    OVERLAY_ALPHA,
    TEXT_GAME_OVER,
    TEXT_PAUSED,
    TEXT_READY,
    TEXT_RESTART_HINT,
    TEXT_SCORE_LABEL,
)
from game.core import GameState


class Renderer:
    """把游戏快照渲染到给定 Surface。

    字体对象做惰性初始化并缓存，避免每帧重建（中文需 CJK 字体，
    按 config.FONT_CANDIDATES 逐个尝试，全部失败回退默认字体）。
    """

    def __init__(self, screen: pygame.Surface, config) -> None:
        """绑定画布与配置。

        参数：
            screen: pygame 主窗口 Surface。
            config: game.config 模块对象（集中所有常量）。
        """
        self._screen = screen
        self._config = config
        # 字体缓存：懒加载，先占位为 None
        self._font_large: pygame.font.Font | None = None
        self._font_small: pygame.font.Font | None = None
        # 半透明遮罩层尺寸固定，预先建好复用，避免每帧新建 Surface
        self._overlay = pygame.Surface(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        )
        self._overlay.set_alpha(OVERLAY_ALPHA)

    # ------------------------------------------------------------------ 字体
    def _get_font(self, size: int) -> pygame.font.Font:
        """按优先级惰性获取并缓存字体对象。

        参数：
            size: 字号（取自 config 的 FONT_SIZE_LARGE / FONT_SIZE_SMALL）。
        返回：
            可用的 pygame 字体对象。
        """
        # 根据字号复用对应缓存槽，避免重复创建
        if size == FONT_SIZE_LARGE and self._font_large is not None:
            return self._font_large
        if size == FONT_SIZE_SMALL and self._font_small is not None:
            return self._font_small

        font: pygame.font.Font | None = None
        # 先按字体名找（依赖 fontconfig，Windows / macOS 走这条路）。
        # 注意：SysFont 对不存在的字体名不会抛异常，而是静默回退默认字体，
        # 因此必须先用 match_font 确认字体真的存在，再加载。
        for candidate in FONT_CANDIDATES:
            path = pygame.font.match_font(candidate)
            if path is None:
                continue
            try:
                font = pygame.font.Font(path, size)
                break
            except Exception:
                continue
        if font is None:
            # 再按字体文件路径找（部分 Linux 环境 fontconfig 不可用时的兜底）
            for path in FONT_FILE_CANDIDATES:
                try:
                    font = pygame.font.Font(path, size)
                    break
                except Exception:
                    continue
        if font is None:
            # 全部失败，回退 pygame 默认字体（可能无法显示中文）
            font = pygame.font.Font(None, size)

        if size == FONT_SIZE_LARGE:
            self._font_large = font
        else:
            self._font_small = font
        return font

    # ------------------------------------------------------------------ 主入口
    def draw(self, game) -> None:
        """按契约层级绘制当前帧。

        参数：
            game: GameCore 实例；只读其 snapshot()，不修改状态。
        """
        snap = game.snapshot()
        self._draw_background()
        self._draw_grid()
        self._draw_food(snap["food"])
        self._draw_snake(snap["snake"])
        self._draw_hud(snap["score"])
        self._draw_overlay(snap["state"], snap["score"])

        # 把所有绘制内容刷到屏幕
        pygame.display.flip()

    # ------------------------------------------------------------------ 背景
    def _draw_background(self) -> None:
        """铺满整窗的纯色背景。"""
        self._screen.fill(COLOR_BACKGROUND)

    # ------------------------------------------------------------------ 网格
    def _draw_grid(self) -> None:
        """绘制网格线。

        网格区域整体下移 HUD_HEIGHT 像素，顶部留给 HUD 分数栏。
        """
        grid_w = self._config.GRID_WIDTH
        grid_h = self._config.GRID_HEIGHT
        # 纵向线：x 从 0 到 grid_w
        for col in range(grid_w + 1):
            x = col * CELL_SIZE
            top = (x, HUD_HEIGHT)
            bottom = (x, HUD_HEIGHT + grid_h * CELL_SIZE)
            pygame.draw.line(self._screen, COLOR_GRID_LINE, top, bottom)
        # 横向线：y 从 0 到 grid_h，起点整体下移 HUD_HEIGHT
        for row in range(grid_h + 1):
            y = HUD_HEIGHT + row * CELL_SIZE
            left = (0, y)
            right = (grid_w * CELL_SIZE, y)
            pygame.draw.line(self._screen, COLOR_GRID_LINE, left, right)

    # ------------------------------------------------------------------ 食物
    def _draw_food(self, food: tuple[int, int]) -> None:
        """绘制食物方块（按网格坐标换算到屏幕像素）。"""
        fx, fy = food
        px = fx * CELL_SIZE
        py = HUD_HEIGHT + fy * CELL_SIZE
        rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self._screen, COLOR_FOOD, rect)

    # ------------------------------------------------------------------ 蛇
    def _draw_snake(self, snake: list[tuple[int, int]]) -> None:
        """绘制蛇，蛇头与蛇身用不同颜色。

        参数：
            snake: 蛇身坐标列表，snake[0] 为蛇头。
        """
        for index, (sx, sy) in enumerate(snake):
            px = sx * CELL_SIZE
            py = HUD_HEIGHT + sy * CELL_SIZE
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            # 头部用醒目的头色，身体用身体色
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            pygame.draw.rect(self._screen, color, rect)

    # ------------------------------------------------------------------ HUD
    def _draw_hud(self, score: int) -> None:
        """顶部 HUD 背景条 + 得分文字。"""
        # HUD 背景条（顶部整条）
        hud_rect = pygame.Rect(0, 0, self._config.WINDOW_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self._screen, COLOR_HUD_BACKGROUND, hud_rect)

        # 得分文字：config.TEXT_SCORE_LABEL + 分数
        text = f"{TEXT_SCORE_LABEL}{score}"
        font = self._get_font(FONT_SIZE_SMALL)
        surface = font.render(text, True, COLOR_TEXT)
        # 垂直居中于 HUD 区域
        text_rect = surface.get_rect()
        text_rect.centery = HUD_HEIGHT // 2
        text_rect.left = CELL_SIZE  # 左侧留一个格子边距
        self._screen.blit(surface, text_rect)

    # ------------------------------------------------------------------ 遮罩
    def _draw_overlay(self, state: GameState, score: int) -> None:
        """按游戏状态叠加遮罩与提示文字。

        参数：
            state: 当前 GameState 枚举。
            score: 当前/最终得分（GAME_OVER 时显示）。
        """
        if state == GameState.RUNNING:
            # 运行中不叠加任何遮罩
            return

        # 半透明遮罩覆盖整个游戏区（Surface 复用，只重新填色）
        self._overlay.fill(COLOR_OVERLAY)
        self._screen.blit(self._overlay, (0, 0))

        if state == GameState.READY:
            self._draw_centered_text(TEXT_READY, FONT_SIZE_LARGE)
        elif state == GameState.PAUSED:
            self._draw_centered_text(TEXT_PAUSED, FONT_SIZE_LARGE)
        elif state == GameState.GAME_OVER:
            # 第一行：游戏结束；第二行：最终得分；第三行：重开提示
            self._draw_centered_text(
                TEXT_GAME_OVER, FONT_SIZE_LARGE, line_offset=-CELL_SIZE
            )
            self._draw_centered_text(
                f"{TEXT_SCORE_LABEL}{score}",
                FONT_SIZE_SMALL,
                line_offset=0,
            )
            self._draw_centered_text(
                TEXT_RESTART_HINT, FONT_SIZE_SMALL, line_offset=CELL_SIZE
            )

    def _draw_centered_text(
        self, text: str, size: int, line_offset: int = 0
    ) -> None:
        """在窗口中心（可纵向偏移 line_offset 像素）绘制一行文字。"""
        font = self._get_font(size)
        surface = font.render(text, True, COLOR_TEXT)
        rect = surface.get_rect()
        rect.center = (self._config.WINDOW_WIDTH // 2,
                       self._config.WINDOW_HEIGHT // 2 + line_offset)
        self._screen.blit(surface, rect)
