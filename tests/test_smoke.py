"""表现层与主循环的集成冒烟测试。

为什么需要这个文件：
`scripts/` 下的裸 assert 脚本无法被 `unittest discover` 收集，导致
ui/ 与 main.py 长期处于「实际跑过但统计为 0% 覆盖」的盲区。这里用
unittest.TestCase 重写，借助 SDL 的 dummy 驱动在无头环境下真实走一遍
「输入 → 状态机 → 渲染」的完整链路。

无头原理：设置 SDL_VIVEODRIVER=dummy 后，pygame 不需要真实的显示设备，
窗口绘制与事件队列依然可用，因此 CI / 服务器上也能跑。
"""

import os

# 必须在 pygame 初始化显示之前指定无头驱动
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest
from unittest import mock

try:
    import pygame
except ImportError:  # pragma: no cover - 环境缺少 pygame 时跳过
    pygame = None

from game import config
from game.core import GameCore, GameState
from game.direction import Action, Direction
from ui.input_handler import InputHandler
from ui.renderer import Renderer
from main import main

# 虚拟每帧耗时（毫秒），约等于 60FPS；用虚拟时间避免测试真的等上几秒
FRAME_MS = 16

# 方向名 → 屏幕坐标下的反向按键，用于验证 180° 掉头防护
OPPOSITE_KEY = {
    Direction.UP: pygame.K_DOWN if pygame else None,
    Direction.DOWN: pygame.K_UP if pygame else None,
    Direction.LEFT: pygame.K_RIGHT if pygame else None,
    Direction.RIGHT: pygame.K_LEFT if pygame else None,
}


@unittest.skipIf(pygame is None, "未安装 pygame，跳过表现层冒烟测试")
class SmokeTest(unittest.TestCase):
    """用真实的 pygame 事件与渲染管线跑通整条链路。"""

    screen = None

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        pygame.event.clear()  # 隔离用例之间的残留事件
        self.game = GameCore()
        self.renderer = Renderer(self.screen, config)
        self.handler = InputHandler()

    # ------------------------------------------------------------ 工具方法
    def press(self, key: int) -> None:
        """投递一个按键事件，等价于玩家敲一下键盘。"""
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

    def pump(self, frames: int) -> None:
        """跑 frames 帧完整循环：输入 → 计时步进 → 渲染（与 main.py 一致）。"""
        elapsed = 0
        for _ in range(frames):
            for action in self.handler.poll_actions():
                self.game.handle(action)
            if self.game.state is GameState.RUNNING:
                elapsed += FRAME_MS
                while elapsed >= config.MOVE_INTERVAL_MS:
                    elapsed -= config.MOVE_INTERVAL_MS
                    self.game.update()
            else:
                elapsed = 0
            self.renderer.draw(self.game)

    # ------------------------------------------------------------ 测试用例
    def test_renderer_draws_every_state(self) -> None:
        """四种状态的整帧绘制都不能抛异常。"""
        for state in GameState:
            self.game.state = state
            self.renderer.draw(self.game)

    def test_direction_key_starts_game(self) -> None:
        self.press(pygame.K_UP)
        self.pump(1)
        self.assertIs(self.game.state, GameState.RUNNING)
        self.assertIs(self.game.snake.direction, Direction.UP)

    def test_reverse_key_in_ready_does_not_start(self) -> None:
        """P1-1 回归：初始朝右时按 ←，不能开局也不能转向。"""
        self.press(pygame.K_LEFT)
        self.pump(1)
        self.assertIs(self.game.state, GameState.READY)
        self.assertIs(self.game.snake.direction, Direction.RIGHT)

    def test_snake_hits_wall(self) -> None:
        self.press(pygame.K_UP)
        self.pump(150)  # 起点在网格中部，向上十余步必然撞顶
        self.assertIs(self.game.state, GameState.GAME_OVER)

    def test_pause_freezes_and_resumes(self) -> None:
        self.press(pygame.K_UP)
        self.pump(1)
        self.press(pygame.K_SPACE)
        self.pump(1)
        self.assertIs(self.game.state, GameState.PAUSED)

        head = self.game.snake.body[0]
        self.pump(30)
        self.assertEqual(self.game.snake.body[0], head, "暂停时蛇仍在移动")

        self.press(pygame.K_SPACE)
        self.pump(20)
        self.assertNotEqual(self.game.snake.body[0], head, "恢复后蛇没有移动")

    def test_restart_after_game_over(self) -> None:
        self.press(pygame.K_UP)
        self.pump(150)
        self.assertIs(self.game.state, GameState.GAME_OVER)

        self.press(pygame.K_r)
        self.pump(1)
        self.assertIs(self.game.state, GameState.RUNNING)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(len(self.game.snake.body), config.INITIAL_SNAKE_LENGTH)

    def test_eating_food_scores_and_grows(self) -> None:
        self.press(pygame.K_RIGHT)
        self.pump(1)
        self.game.food.position = self.game.snake.next_head()  # 食物摆在正前方

        length_before = len(self.game.snake.body)
        self.pump(10)
        self.assertEqual(self.game.score, config.SCORE_PER_FOOD)
        self.assertEqual(len(self.game.snake.body), length_before + 1)

    def test_reverse_turn_is_rejected(self) -> None:
        self.press(pygame.K_UP)
        self.pump(1)
        direction = self.game.snake.direction
        self.press(OPPOSITE_KEY[direction])
        self.pump(20)
        self.assertIs(self.game.snake.direction, direction, "出现了 180° 掉头")
        self.assertIs(self.game.state, GameState.RUNNING)

    def test_double_turn_cannot_reverse(self) -> None:
        """同一格内连按 ↑←↓ 也不能绕过反向检查。"""
        self.press(pygame.K_UP)
        self.pump(1)
        self.game.snake.direction = Direction.UP  # 固定初始朝向，保证可复现
        self.press(pygame.K_LEFT)
        self.press(pygame.K_DOWN)
        self.pump(20)
        self.assertIs(self.game.snake.direction, Direction.UP)

    def test_escape_and_window_close_both_quit(self) -> None:
        self.press(pygame.K_ESCAPE)
        self.assertIn(Action.QUIT, self.handler.poll_actions())

        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertIn(Action.QUIT, self.handler.poll_actions())

    def test_quit_action_sets_flag(self) -> None:
        self.game.handle(Action.QUIT)
        self.assertTrue(self.game.quit_requested)


class _FakeClock:
    """固定步长时钟：跑满指定帧数后投递 QUIT，让 main() 确定性结束。"""

    def __init__(self, frames: int, frame_ms: int = FRAME_MS) -> None:
        self._frames = frames
        self._frame_ms = frame_ms

    def tick(self, fps: int) -> int:
        self._frames -= 1
        if self._frames <= 0:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        return self._frame_ms


@unittest.skipIf(pygame is None, "未安装 pygame，跳过主循环冒烟测试")
class MainLoopTest(unittest.TestCase):
    """真实执行 main()：验证建窗、主循环与干净退出。

    单独成类的原因：main() 结束时会调用 pygame.quit()，与 SmokeTest 的
    类级 pygame 生命周期冲突，因此这里自己管理一次 init/quit。
    """

    def setUp(self) -> None:
        # main() 结束时会 pygame.quit()，因此每个用例都要重新初始化
        pygame.init()
        pygame.event.clear()

    def tearDown(self) -> None:
        pygame.quit()

    def test_main_creates_window_and_exits_on_quit(self) -> None:
        # 先用假时钟空转若干帧（停留在 READY 态），再收到退出事件。
        # 能正常返回，即说明建窗、主循环、干净退出三步都跑通。
        with mock.patch("pygame.time.Clock", return_value=_FakeClock(frames=20)):
            main()
        # 退出后显示子系统应当已被 pygame.quit() 收尾
        self.assertFalse(pygame.display.get_init())

    def test_main_exits_on_escape_key(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        main()  # Esc 映射为 QUIT，同样应干净退出

    def test_main_steps_and_renders_while_running(self) -> None:
        """跑满若干帧再退出，覆盖主循环的「计时步进 + 渲染」分支。

        真实时钟会让测试等上数秒，这里换成固定步长的假时钟：
        帧数耗尽时自动投递 QUIT，既确定性又不依赖真实时间。
        """
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
        with mock.patch("pygame.time.Clock", return_value=_FakeClock(frames=40)):
            main()
        self.assertFalse(pygame.display.get_init())


if __name__ == "__main__":
    unittest.main()
