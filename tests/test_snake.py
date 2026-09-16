"""Snake 模块的单元测试（标准库 unittest）。

覆盖构造函数、前进、转向、生长、自撞判定（含贴尾边界）与 occupies。
"""

import unittest

from game.config import INITIAL_SNAKE_LENGTH
from game.direction import Direction
from game.snake import Snake


class TestSnake(unittest.TestCase):
    def test_initial_length_default(self):
        # 默认初始长度取自 config，body[0] 为蛇头
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertEqual(len(snake.body), INITIAL_SNAKE_LENGTH)
        self.assertEqual(snake.body[0], (5, 5))
        self.assertEqual(snake.body, [(5, 5), (4, 5), (3, 5)])
        self.assertEqual(snake.direction, Direction.RIGHT)
        self.assertEqual(snake.pending_grow, 0)

    def test_initial_length_custom(self):
        # 自定义初始长度 1 只含蛇头；长度为 4 时反向排开
        single = Snake((2, 2), Direction.UP, initial_length=1)
        self.assertEqual(single.body, [(2, 2)])

        quad = Snake((10, 10), Direction.LEFT, initial_length=4)
        self.assertEqual(quad.body, [(10, 10), (11, 10), (12, 10), (13, 10)])

    def test_step_keeps_length_and_moves(self):
        # 正常前进一步：长度不变，蛇头前进一格，蛇尾让出
        snake = Snake((5, 5), Direction.RIGHT)
        snake.step()
        self.assertEqual(len(snake.body), INITIAL_SNAKE_LENGTH)
        self.assertEqual(snake.body[0], (6, 5))
        self.assertEqual(snake.body, [(6, 5), (5, 5), (4, 5)])

    def test_turn_reverse_rejected(self):
        # 反向 180° 掉头必须被拒绝
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertFalse(snake.turn(Direction.LEFT))
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_turn_same_direction_rejected(self):
        # 与当前方向相同也返回 False（不应改变方向）
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertFalse(snake.turn(Direction.RIGHT))
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_turn_legal_accepted(self):
        # 合法转向接受，且可连续两次同向/合法转向
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertTrue(snake.turn(Direction.DOWN))
        self.assertEqual(snake.direction, Direction.DOWN)
        # 重复设置同一合法方向：与当前方向相同，应返回 False
        self.assertFalse(snake.turn(Direction.DOWN))
        self.assertTrue(snake.turn(Direction.LEFT))
        self.assertEqual(snake.direction, Direction.LEFT)

    def test_grow_on_food(self):
        # 吃到食物：pending_grow +1，step 后长度 +1 且蛇尾保留
        snake = Snake((5, 5), Direction.RIGHT)
        snake.pending_grow += 1
        self.assertEqual(snake.pending_grow, 1)
        snake.step()
        self.assertEqual(len(snake.body), INITIAL_SNAKE_LENGTH + 1)
        self.assertEqual(snake.body[0], (6, 5))
        self.assertEqual(snake.body, [(6, 5), (5, 5), (4, 5), (3, 5)])
        self.assertEqual(snake.pending_grow, 0)

    def test_will_hit_self_true(self):
        # 横向蛇身向右走，撞到身体中段算自撞
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertTrue(snake.will_hit_self((4, 5)))

    def test_will_hit_self_tail_edge_when_not_growing(self):
        # 贴着尾巴走：pending_grow==0 时蛇尾本帧让位，不算撞
        snake = Snake((5, 5), Direction.RIGHT)
        tail = snake.body[-1]  # (3, 5)
        self.assertFalse(snake.will_hit_self(tail))
        # 但撞到非蛇尾的身体段仍算自撞
        self.assertTrue(snake.will_hit_self((4, 5)))

    def test_will_hit_self_tail_when_growing(self):
        # pending_grow>0 时蛇尾不动，撞到蛇尾也算自撞
        snake = Snake((5, 5), Direction.RIGHT)
        snake.pending_grow += 1
        tail = snake.body[-1]  # (3, 5)
        self.assertTrue(snake.will_hit_self(tail))

    def test_occupies(self):
        snake = Snake((5, 5), Direction.RIGHT)
        self.assertTrue(snake.occupies((5, 5)))
        self.assertTrue(snake.occupies((4, 5)))
        self.assertTrue(snake.occupies((3, 5)))
        self.assertFalse(snake.occupies((6, 5)))
        self.assertFalse(snake.occupies((5, 6)))


if __name__ == "__main__":
    unittest.main()
