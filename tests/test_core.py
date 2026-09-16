"""GameCore 状态机的单元测试。

覆盖：撞墙、撞自己、吃食物加分变长、暂停不推进、重开归零、
READY 转向即开局、snapshot 内容与只读解耦。
"""

import random
import unittest

from game import config
from game.core import GameCore, GameState
from game.direction import Action, Direction


class CoreTestBase(unittest.TestCase):
    """公共夹具：注入固定种子，保证食物生成可复现。"""

    def setUp(self) -> None:
        self.game = GameCore(rng=random.Random(20260916))

    def start_game(self, action: Action = Action.TURN_UP) -> None:
        """从 READY 进入 RUNNING。"""
        self.game.handle(action)


class TestInitialState(CoreTestBase):
    """初始状态与开局行为。"""

    def test_initial_state_is_ready(self) -> None:
        self.assertIs(self.game.state, GameState.READY)
        self.assertEqual(self.game.score, 0)

    def test_turn_in_ready_starts_game(self) -> None:
        # 初始方向为 RIGHT，按 ↑ 应同时完成「转向 + 开局」
        self.start_game(Action.TURN_UP)
        self.assertIs(self.game.state, GameState.RUNNING)
        self.assertIs(self.game.snake.direction, Direction.UP)

    def test_update_does_nothing_in_ready(self) -> None:
        head_before = self.game.snake.body[0]
        self.game.update()
        self.assertEqual(self.game.snake.body[0], head_before)
        self.assertIs(self.game.state, GameState.READY)


class TestCollision(CoreTestBase):
    """撞墙与撞自己都进入 GAME_OVER。"""

    def test_hit_wall_ends_game(self) -> None:
        # 蛇朝右一路前进，必然撞到右墙；步数给足余量
        self.start_game(Action.TURN_RIGHT)
        for _ in range(config.GRID_WIDTH + 5):
            self.game.update()
        self.assertIs(self.game.state, GameState.GAME_OVER)

    def test_hit_self_ends_game(self) -> None:
        # 蛇身绕成一个圈，蛇头 (5,5) 向下走进身体 (5,6) —— 该格不是蛇尾
        game = self.game
        game.snake.body = [(5, 5), (5, 6), (4, 6), (4, 5)]
        game.snake.direction = Direction.DOWN
        game.state = GameState.RUNNING

        game.update()
        self.assertIs(game.state, GameState.GAME_OVER)

    def test_following_tail_is_not_self_hit(self) -> None:
        # 边界：蛇尾当帧会让位，贴着尾巴走不算自撞
        game = self.game
        game.snake.body = [(5, 5), (5, 6), (4, 6), (4, 5)]
        # (4,5) 是蛇尾，可进入；(5,6) 是身体，不可进入
        self.assertFalse(game.snake.will_hit_self((4, 5)))
        self.assertTrue(game.snake.will_hit_self((5, 6)))


class TestTurnQueue(CoreTestBase):
    """转向排队：一个步进间隔内的多次按键不能组合出 180° 掉头。"""

    def setUp(self) -> None:
        super().setUp()
        self.game.snake.body = [(5, 5), (5, 6), (5, 7)]  # 一条朝上的蛇
        self.game.snake.direction = Direction.UP
        self.game.state = GameState.RUNNING

    def test_turn_applied_on_next_update(self) -> None:
        self.game.handle(Action.TURN_RIGHT)
        self.assertIs(self.game.snake.direction, Direction.UP)  # 尚未生效
        self.game.update()
        self.assertIs(self.game.snake.direction, Direction.RIGHT)
        self.assertEqual(self.game.snake.body[0], (6, 5))

    def test_double_turn_cannot_reverse(self) -> None:
        # ↑ 状态下快速连按 ← 与 ↓：最终结果相对 UP 是反向，必须被拒绝
        self.game.handle(Action.TURN_LEFT)
        self.game.handle(Action.TURN_DOWN)
        self.game.update()
        self.assertIs(self.game.snake.direction, Direction.UP)
        self.assertIs(self.game.state, GameState.RUNNING)

    def test_legal_double_turn_keeps_last(self) -> None:
        self.game.handle(Action.TURN_LEFT)
        self.game.handle(Action.TURN_UP)  # 与当前方向相同，最终保持 UP
        self.game.update()
        self.assertIs(self.game.snake.direction, Direction.UP)
        self.assertEqual(self.game.snake.body[0], (5, 4))


class TestEating(CoreTestBase):
    """吃食物的计分与生长。"""

    def test_eat_food_increases_score_and_length(self) -> None:
        game = self.game
        game.snake.body = [(5, 5), (4, 5), (3, 5)]
        game.snake.direction = Direction.RIGHT
        game.state = GameState.RUNNING
        # 把食物放到蛇头正前方，制造一次确定的进食
        game.food.position = (6, 5)

        length_before = len(game.snake.body)
        game.update()

        self.assertEqual(game.score, config.SCORE_PER_FOOD)
        self.assertEqual(len(game.snake.body), length_before + 1)
        self.assertEqual(game.snake.body[0], (6, 5))
        # 食物必须重生，且不能落在蛇身上
        self.assertNotIn(game.food.position, game.snake.body)

    def test_food_never_spawns_on_snake(self) -> None:
        game = self.game
        self.start_game(Action.TURN_RIGHT)
        for _ in range(50):
            self.assertNotIn(game.food.position, set(game.snake.body))
            game.update()
            if game.state is GameState.GAME_OVER:
                game.reset()
                game.state = GameState.RUNNING


class TestPauseAndReset(CoreTestBase):
    """暂停与重开。"""

    def test_pause_toggle_and_no_progress(self) -> None:
        self.start_game()
        self.game.handle(Action.PAUSE)
        self.assertIs(self.game.state, GameState.PAUSED)

        head_before = self.game.snake.body[0]
        self.game.update()
        self.assertEqual(self.game.snake.body[0], head_before)

        self.game.handle(Action.PAUSE)
        self.assertIs(self.game.state, GameState.RUNNING)

    def test_restart_resets_score_and_state(self) -> None:
        self.start_game()
        self.game.score = 100
        self.game.state = GameState.GAME_OVER
        self.game.handle(Action.RESTART)

        self.assertEqual(self.game.score, 0)
        self.assertIs(self.game.state, GameState.RUNNING)
        self.assertEqual(len(self.game.snake.body), config.INITIAL_SNAKE_LENGTH)

    def test_quit_is_accepted_in_any_state(self) -> None:
        self.game.handle(Action.QUIT)
        self.assertTrue(self.game.quit_requested)


class TestSnapshot(CoreTestBase):
    """快照是渲染层的唯一数据来源。"""

    def test_snapshot_content(self) -> None:
        snap = self.game.snapshot()
        self.assertEqual(snap["snake"], self.game.snake.body)
        self.assertEqual(snap["food"], self.game.food.position)
        self.assertEqual(snap["score"], self.game.score)
        self.assertIs(snap["state"], self.game.state)
        self.assertEqual(snap["grid_width"], config.GRID_WIDTH)
        self.assertEqual(snap["grid_height"], config.GRID_HEIGHT)

    def test_snapshot_is_readonly_copy(self) -> None:
        snap = self.game.snapshot()
        snap["snake"].append((-1, -1))  # 修改快照不应影响真实状态
        self.assertNotIn((-1, -1), self.game.snake.body)


if __name__ == "__main__":
    unittest.main()
