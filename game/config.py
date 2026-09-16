"""全局配置常量。

设计原则：
1. 所有可调参数集中在本文件，业务代码（game/ 与 ui/）中禁止出现裸数字；
2. 常量名使用全大写，按「网格 / 节奏 / 玩法 / 颜色 / 文字」分区组织；
3. 纯数据模块，不依赖 pygame，便于核心逻辑在无图形环境下做单元测试。
"""

# ---------------------------------------------------------------- 网格与窗口
GRID_WIDTH = 30  # 横向格子数
GRID_HEIGHT = 20  # 纵向格子数
CELL_SIZE = 24  # 每个格子的像素边长

# 顶部信息栏高度：用于显示分数，不参与游戏网格
HUD_HEIGHT = 40

# 窗口尺寸由网格与格子大小推算，避免各处硬编码
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + HUD_HEIGHT
WINDOW_TITLE = "贪吃蛇 Snake"

# ---------------------------------------------------------------- 运行节奏
FPS = 60  # 渲染帧率
MOVE_INTERVAL_MS = 120  # 蛇每前进一格的间隔（毫秒），与帧率解耦

# ---------------------------------------------------------------- 玩法参数
INITIAL_SNAKE_LENGTH = 3  # 初始蛇身长度（含蛇头）
SCORE_PER_FOOD = 10  # 每吃一个食物的得分
START_POSITION = (GRID_WIDTH // 2, GRID_HEIGHT // 2)  # 蛇头初始坐标
START_DIRECTION = "RIGHT"  # 初始方向，由 direction.Direction 解析使用

# ---------------------------------------------------------------- 颜色（RGB）
COLOR_BACKGROUND = (18, 22, 30)
COLOR_GRID_LINE = (30, 36, 48)
COLOR_SNAKE_HEAD = (94, 234, 143)
COLOR_SNAKE_BODY = (52, 168, 96)
COLOR_FOOD = (232, 88, 88)
COLOR_TEXT = (236, 240, 247)
COLOR_HUD_BACKGROUND = (12, 15, 21)
COLOR_OVERLAY = (0, 0, 0)
OVERLAY_ALPHA = 170  # 结束/暂停遮罩透明度（0~255）

# ---------------------------------------------------------------- 文字与字体
# 中文需要 CJK 字体，按优先级逐个尝试，全部不可用时回退到 pygame 默认字体
FONT_CANDIDATES = (
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "WenQuanYi Zen Hei",
    "Heiti SC",
)
# 部分 Linux 环境下 fontconfig 不可用（fc-list 超时），此时按文件名直接加载
FONT_FILE_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)
FONT_SIZE_LARGE = 32
FONT_SIZE_SMALL = 20

TEXT_READY = "按方向键开始"
TEXT_PAUSED = "已暂停（空格继续）"
TEXT_GAME_OVER = "游戏结束"
TEXT_RESTART_HINT = "按 R 重开"
TEXT_SCORE_LABEL = "得分："
