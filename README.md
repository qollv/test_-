# 贪吃蛇 Snake（Python + pygame）

一个结构清晰、核心逻辑可单元测试的贪吃蛇小游戏。

![游戏预览](docs/preview.png)

## 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 启动

```bash
python main.py
```

## 操作说明

| 按键 | 作用 |
| --- | --- |
| ↑ ↓ ← → / W A S D | 转向（开局、禁止 180° 掉头） |
| 空格 / P | 暂停 / 继续 |
| R | 重新开始 |
| Esc / 关闭窗口 | 退出 |

## 目录结构

```
main.py          程序入口与主循环
game/            核心逻辑（不依赖 pygame，可无头测试）
  config.py      全局常量
  direction.py   Direction / Action 枚举
  snake.py       蛇身数据结构与行为
  food.py        食物生成
  core.py        状态机与单步推进
ui/              表现层（唯一使用 pygame 的地方）
  renderer.py    渲染
  input_handler.py  输入处理
tests/           unittest 单元测试（含无头冒烟测试 test_smoke.py）
scripts/         辅助脚本（生成预览图）
docs/            项目计划与代码审查文档
```

## 运行测试

```bash
python -m unittest discover -s tests -v      # 全部用例（含表现层无头冒烟）
python -m coverage run --source=game,ui,main -m unittest discover -s tests
python -m coverage report -m                 # 覆盖率报告
```

`tests/test_smoke.py` 通过 SDL `dummy` 驱动在无头环境下真实跑一遍
「输入 → 状态机 → 渲染」，因此表现层与 `main.py` 的主循环逻辑同样被覆盖，
不需要图形界面即可回归。

详细设计见 [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)，
v0.1 审查记录见 [docs/CODE_REVIEW_v0.1.md](docs/CODE_REVIEW_v0.1.md)。
