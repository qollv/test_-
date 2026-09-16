"""Food 模块的单元测试（标准库 unittest）。"""

import random
import unittest

from game.food import BoardFullError, Food
from game.config import GRID_WIDTH, GRID_HEIGHT


class TestFood(unittest.TestCase):
    """针对食物生成逻辑的各项验证。"""

    def test_reproducible_with_same_seed(self):
        """注入相同种子的 rng，两个实例的 respawn 序列应当一致。"""
        seq_a = []
        seq_b = []
        food_a = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(12345))
        food_b = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(12345))
        for _ in range(50):
            seq_a.append(food_a.respawn(set()))
            seq_b.append(food_b.respawn(set()))
        self.assertEqual(seq_a, seq_b)

    def test_position_in_bounds_and_not_occupied(self):
        """循环 200 次 + 近乎占满的 occupied，坐标始终合法且未被占用。"""
        food = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(7))
        # 构造一个几乎占满棋盘的占用集合：只给食物留一个固定空位
        reserved = (GRID_WIDTH - 1, GRID_HEIGHT - 1)
        occupied = {
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) != reserved
        }
        for _ in range(200):
            pos = food.respawn(occupied)
            x, y = pos
            self.assertTrue(0 <= x < GRID_WIDTH, f"x 越界: {x}")
            self.assertTrue(0 <= y < GRID_HEIGHT, f"y 越界: {y}")
            self.assertNotIn(pos, occupied, f"食物落在占用格: {pos}")

    def test_only_one_free_cell(self):
        """棋盘仅剩一格空位时，respawn 必定返回那一格。"""
        food = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(99))
        # 仅保留左上角 (0, 0) 为空位
        occupied = {
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) != (0, 0)
        }
        self.assertEqual(food.respawn(occupied), (0, 0))
        self.assertEqual(food.position, (0, 0))

    def test_board_full_raises(self):
        """棋盘全满时 respawn 抛出 BoardFullError。"""
        food = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(1))
        occupied = {
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
        }
        with self.assertRaises(BoardFullError):
            food.respawn(occupied)

    def test_initial_position_exists(self):
        """构造后应当已具备初始 position，且位于网格内。"""
        food = Food(GRID_WIDTH, GRID_HEIGHT, random.Random(42))
        x, y = food.position
        self.assertTrue(0 <= x < GRID_WIDTH)
        self.assertTrue(0 <= y < GRID_HEIGHT)


if __name__ == "__main__":
    unittest.main()
