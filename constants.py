class Colors:
    WHITE = (255, 255, 255)
    BLACK = (15, 15, 23)
    DARK_SURFACE = (25, 25, 35)
    DARKER_SURFACE = (18, 18, 28)
    NEON_CYAN = (0, 255, 255)
    NEON_PINK = (255, 20, 147)
    NEON_GREEN = (57, 255, 20)
    NEON_PURPLE = (138, 43, 226)
    NEON_ORANGE = (255, 140, 0)
    NEON_BLUE = (30, 144, 255)
    NEON_YELLOW = (255, 255, 0)
    RED = (220, 38, 127)
    ORANGE = (255, 140, 0)
    YELLOW = (255, 193, 7)
    GREEN = (76, 175, 80)
    BLUE = (33, 150, 243)
    PURPLE = (156, 39, 176)
    CYAN = (0, 188, 212)
    PINK = (233, 30, 99)
    GRAY = (158, 158, 158)
    LIGHT_GRAY = (189, 189, 189)
    DARK_GRAY = (97, 97, 97)
    TEXT_SECONDARY = (158, 158, 158)
    UI_BG_COLOR = DARK_SURFACE
    UI_TEXT_COLOR = WHITE
    UI_TEXT_SECONDARY = TEXT_SECONDARY
    BONUS_GREEN = NEON_GREEN
    ACCENT_COLOR = NEON_CYAN

class GameSettings:
    SCREEN_WIDTH = 400
    SCREEN_HEIGHT = 700
    FPS = 60
    INITIAL_BLOCK_HEALTH = 1
    HEALTH_INCREASE_PER_ROUND = 1

class UI:
    TOP_UI_HEIGHT = 80
    BOTTOM_UI_HEIGHT = 120
    TITLE_FONT_SIZE = 48
    MENU_FONT_SIZE = 32
    MENU_ITEM_HEIGHT = 60
    MENU_START_Y = 300

class Ball:
    RADIUS = 8
    SPEED = 11
    COUNT_START = 1
    LAUNCH_DELAY = 80

class Block:
    SIZE = 56
    MARGIN = 1
    ROWS_MAX = 10
    START_Y = 120
    MOVE_DOWN_DISTANCE = SIZE + MARGIN
    TYPE_NORMAL = 0
    TYPE_BOMB = 1
    TYPE_SHIELD = 2
    TYPE_GHOST = 3
    BOMB_COLOR = (255, 69, 0)
    SHIELD_COLOR = (70, 130, 180)
    GHOST_COLOR = (147, 112, 219)
    BOMB_CHANCE = 0.08
    SHIELD_CHANCE = 0.06
    GHOST_CHANCE = 0.05
    GHOST_PASS_CHANCE = 0.4

class Bonus:
    BALL_RADIUS = 10
    BALL_SPAWN_CHANCE = 0.8

class Paddle:
    WIDTH = 100
    HEIGHT = 15
    SPEED = 8
    Y = GameSettings.SCREEN_HEIGHT - 50

class Brick:
    WIDTH = 75
    HEIGHT = 30
    ROWS = 5
    COLS = 10
    PADDING = 5
    OFFSET_TOP = 60
    POINTS = 10

class Game:
    STATE_TITLE = 0
    STATE_GAME = 1
    STATE_SETTINGS = 2
    STATE_RANKING = 3
    STATE_PAUSED = 4
    STATE_STATISTICS = 5
    STATE_REPLAY = 6
    STATE_MODE_SELECT = 7
    STATE_ACHIEVEMENTS = 8
    MODE_CLASSIC = 0
    MODE_TIME_ATTACK = 1
    MODE_SURVIVAL = 2
    MODE_PUZZLE = 3

class Combo:
    TIME_WINDOW = 2000
    MULTIPLIER_BASE = 1.5
    MULTIPLIER_INCREMENT = 0.5
    MAX_MULTIPLIER = 5.0
    MIN_COUNT = 2
    TEXT_COLOR = Colors.NEON_YELLOW
    GLOW_COLOR = (255, 255, 0, 100)

class Particle:
    EXPLOSION_COUNT = 15
    EXPLOSION_SPEED = 8
    EXPLOSION_LIFE = 30
    TRAIL_LENGTH = 8
    TRAIL_FADE_SPEED = 20
    SPARKLE_COUNT = 8
    SPARKLE_SPEED = 4
    SPARKLE_LIFE = 20

class Theme:
    DARK = "dark"
    LIGHT = "light"
    CHRISTMAS = "christmas"
    HALLOWEEN = "halloween"
    SPRING = "spring"
    SUMMER = "summer"
    LIGHT_WHITE = (255, 255, 255)
    LIGHT_BLACK = (240, 240, 245)
    LIGHT_SURFACE = (250, 250, 255)
    LIGHT_DARKER_SURFACE = (235, 235, 245)
    LIGHT_TEXT = (50, 50, 70)
    LIGHT_TEXT_SECONDARY = (120, 120, 140)
    CHRISTMAS_RED = (220, 20, 60)
    CHRISTMAS_GREEN = (34, 139, 34)
    CHRISTMAS_GOLD = (255, 215, 0)
    CHRISTMAS_WHITE = (255, 250, 250)
    CHRISTMAS_DARK = (25, 25, 35)
    HALLOWEEN_ORANGE = (255, 140, 0)
    HALLOWEEN_PURPLE = (128, 0, 128)
    HALLOWEEN_BLACK = (20, 20, 20)
    HALLOWEEN_GREEN = (50, 205, 50)
    HALLOWEEN_GRAY = (105, 105, 105)
    SPRING_PINK = (255, 182, 193)
    SPRING_GREEN = (144, 238, 144)
    SPRING_YELLOW = (255, 255, 224)
    SPRING_BLUE = (173, 216, 230)
    SPRING_WHITE = (248, 248, 255)
    SUMMER_BLUE = (0, 191, 255)
    SUMMER_YELLOW = (255, 215, 0)
    SUMMER_ORANGE = (255, 165, 0)
    SUMMER_CYAN = (0, 255, 255)
    SUMMER_WHITE = (255, 255, 255)
    BACKGROUNDS = {
        DARK: [(15, 15, 23), (25, 25, 35), (35, 35, 45)],
        LIGHT: [(240, 240, 245), (250, 250, 255), (255, 255, 255)],
        CHRISTMAS: [(25, 25, 35), (139, 0, 0), (0, 100, 0)],
        HALLOWEEN: [(20, 20, 20), (75, 0, 130), (255, 140, 0)],
        SPRING: [(248, 248, 255), (255, 182, 193), (144, 238, 144)],
        SUMMER: [(135, 206, 235), (255, 215, 0), (0, 191, 255)]
    }
    ROUND_CHANGES = {
        1: DARK,
        5: SPRING,
        10: SUMMER,
        15: HALLOWEEN,
        20: CHRISTMAS,
        25: LIGHT
    }

class Replay:
    MAX_ACTIONS = 10000
    SAVE_THRESHOLD = 1000

class Stats:
    UPDATE_INTERVAL = 1000

class Achievement:
    NOTIFICATION_DURATION = 3000
    PERFECT_ANGLE_TOLERANCE = 2
    PERFECT_ANGLES = [45, 90, 135]

class Shop:
    ITEMS = [
        {"name": "파워볼", "price": 100, "desc": "벽돌을 2배로 깸", "key": 1},
        {"name": "스피드볼", "price": 150, "desc": "공 속도 2배", "key": 2},
        {"name": "매그넘볼", "price": 200, "desc": "공 1개 남으면 모든 블록 제거", "key": 3},
        {"name": "블록 삭제", "price": 300, "desc": "모든 블록 즉시 삭제", "key": None},
    ]