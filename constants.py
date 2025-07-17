# 게임 설정 상수
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
FPS = 60

# 색상 (이미지 스타일에 맞게 조정)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
BLUE = (80, 80, 255)
YELLOW = (255, 255, 80)
ORANGE = (255, 165, 80)
PURPLE = (200, 80, 255)
CYAN = (80, 255, 255)
PINK = (255, 80, 200)
GRAY = (128, 128, 128)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (64, 64, 64)

# UI 색상
UI_BG_COLOR = (240, 240, 240)
UI_TEXT_COLOR = (60, 60, 60)
BONUS_GREEN = (100, 255, 100)

# 공 설정
BALL_RADIUS = 8
BALL_SPEED = 11  # 기존 6에서 1.8배 증가 (6 * 1.8 = 10.8)
BALL_COUNT_START = 1
BALL_LAUNCH_DELAY = 80  # 밀리세컨드

# 블록 설정 (7칸으로 변경)  
BLOCK_SIZE = 56  # 화면을 꽉 채우도록 크기 최적화 (7*56 + 6*1 + 2 = 400)
BLOCK_MARGIN = 1  # 최소 간격으로 설정
BLOCKS_PER_ROW = 7
BLOCK_ROWS_MAX = 10
BLOCK_START_Y = 120

# 보너스 아이템 설정
BONUS_BALL_RADIUS = 10
BONUS_BALL_SPAWN_CHANCE = 0.8  # 80% 확률

# 슈퍼볼 아이템 설정
# SUPER_BALL_RADIUS = 12
# SUPER_BALL_SPAWN_CHANCE = 0.05  # 5% 확률
# SUPER_BALL_COLOR = (255, 255, 0)  # 노랑색

# 발사 설정
LAUNCH_AREA_HEIGHT = 100
AIM_LINE_LENGTH = 200
MIN_LAUNCH_ANGLE = 10  # 최소 발사각도 (도)
MAX_LAUNCH_ANGLE = 170  # 최대 발사각도 (도)

# UI 설정
TOP_UI_HEIGHT = 80
BOTTOM_UI_HEIGHT = 120

# 게임 설정
INITIAL_BLOCK_HEALTH = 1
HEALTH_INCREASE_PER_ROUND = 1
BLOCKS_MOVE_DOWN_DISTANCE = BLOCK_SIZE + BLOCK_MARGIN

# 패들 설정
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
PADDLE_SPEED = 8
PADDLE_Y = SCREEN_HEIGHT - 50

# 벽돌 설정
BRICK_WIDTH = 75
BRICK_HEIGHT = 30
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_PADDING = 5
BRICK_OFFSET_TOP = 60

# 점수
BRICK_POINTS = 10 

# 게임 상태
GAME_STATE_TITLE = 0
GAME_STATE_GAME = 1
GAME_STATE_SETTINGS = 2
GAME_STATE_RANKING = 3

# 타이틀 화면 설정
TITLE_FONT_SIZE = 48
MENU_FONT_SIZE = 32
MENU_ITEM_HEIGHT = 60
MENU_START_Y = 300

# 상점 아이템 목록
SHOP_ITEMS = [
    {"name": "파워볼", "price": 100, "desc": "벽돌을 2배로 깸", "key": 1},
    {"name": "스피드볼", "price": 150, "desc": "공 속도 2배", "key": 2},
    {"name": "매그넘볼", "price": 200, "desc": "공 1개 남으면 모든 블록 제거", "key": 3},
    {"name": "블록 삭제", "price": 300, "desc": "모든 블록 즉시 삭제", "key": None},
]