import pygame
import math
import random
from constants import *
from language import get_text, set_language, get_current_language, language_manager
from database import db_manager
from shop import Shop


class Ball:
    def __init__(self, x, y, dx, dy, game=None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = BALL_RADIUS
        self.active = True
        self.game = game  # Game 인스턴스 참조
        
    def move(self):
        if not self.active:
            return
        
        # 스피드볼 효과 적용
        speed_multiplier = 2 if self.game and self.game.active_powerups.get(2, False) else 1
        self.x += self.dx * speed_multiplier
        self.y += self.dy * speed_multiplier
        
        # 좌우 벽 충돌
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.dx = -self.dx
        
        # 상단 벽 충돌
        if self.y - self.radius <= TOP_UI_HEIGHT:
            self.dy = abs(self.dy)
        
        # 바닥에 닿으면 비활성화
        if self.y + self.radius >= SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
            self.active = False
    
    def bounce_block(self, block):
        if not self.active or not block.active:
            return False
        
        # 블록과 충돌 검사
        if (self.x + self.radius >= block.x and 
            self.x - self.radius <= block.x + BLOCK_SIZE and
            self.y + self.radius >= block.y and 
            self.y - self.radius <= block.y + BLOCK_SIZE):
            
            # 투명 블록의 경우 hit 메서드에서 통과 여부를 결정
            # hit이 False를 반환하면 공이 통과한 것
            if block.block_type == BLOCK_TYPE_GHOST:
                hit_result = block.hit(self.game)
                if not hit_result:
                    return False  # 공이 통과함, 반사하지 않음
            
            # 충돌 방향 결정
            center_x = block.x + BLOCK_SIZE / 2
            center_y = block.y + BLOCK_SIZE / 2
            
            dx = self.x - center_x
            dy = self.y - center_y
            
            # 공이 블록 중심에서 멀어지는 방향으로 반사
            if abs(dx) > abs(dy):
                self.dx = abs(self.dx) if dx > 0 else -abs(self.dx)
                # 공을 블록에서 밀어내기
                if dx > 0:
                    self.x = block.x + BLOCK_SIZE + self.radius + 1
                else:
                    self.x = block.x - self.radius - 1
            else:
                self.dy = abs(self.dy) if dy > 0 else -abs(self.dy)
                # 공을 블록에서 밀어내기
                if dy > 0:
                    self.y = block.y + BLOCK_SIZE + self.radius + 1
                else:
                    self.y = block.y - self.radius - 1
            
            return True
        return False
    
    def collect_bonus(self, bonus):
        if not self.active or not bonus.active:
            return False
        
        # 보너스와 충돌 검사
        distance = math.sqrt((self.x - bonus.x)**2 + (self.y - bonus.y)**2)
        if distance <= self.radius + bonus.radius:
            return True
        return False
    
    def draw(self, screen):
        if self.active:
            # 네온 글로우 효과
            for i in range(3, 0, -1):
                glow_color = (*NEON_CYAN, 60 // i)
                glow_surface = pygame.Surface((self.radius * 2 + i * 4, self.radius * 2 + i * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, 
                                 (self.radius + i * 2, self.radius + i * 2), self.radius + i)
                screen.blit(glow_surface, (int(self.x - self.radius - i * 2), int(self.y - self.radius - i * 2)))
            
            # 메인 공 (그라데이션 효과)
            pygame.draw.circle(screen, NEON_CYAN, (int(self.x), int(self.y)), self.radius)
            
            # 하이라이트 (3D 효과)
            highlight_pos = (int(self.x - self.radius//3), int(self.y - self.radius//3))
            pygame.draw.circle(screen, WHITE, highlight_pos, self.radius//3)
            
            # 외곽선
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)


class Block:
    def __init__(self, x, y, health, block_type=BLOCK_TYPE_NORMAL):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.active = True
        self.block_type = block_type
        self.shield_hits = 0  # 방어막 블록이 맞은 횟수
        self.alpha = 255  # 투명 블록의 투명도
        
    def hit(self, game=None):
        if not self.active:
            return False
            
        # 투명 블록: 일정 확률로 공이 통과
        if self.block_type == BLOCK_TYPE_GHOST:
            if random.random() < GHOST_BLOCK_PASS_CHANCE:
                return False  # 공이 통과함 (충돌하지 않음)
        
        # 방어막 블록: 3번 맞아야 파괴
        if self.block_type == BLOCK_TYPE_SHIELD:
            self.shield_hits += 1
            if self.shield_hits < 3:
                return False  # 아직 파괴되지 않음
        
        # 파워볼 효과 적용
        damage = 2 if game and game.active_powerups.get(1, False) else 1
        self.health -= damage
        
        if self.health <= 0:
            self.active = False
            
            # 폭탄 블록: 주변 블록도 파괴
            if self.block_type == BLOCK_TYPE_BOMB and game:
                self.explode_nearby_blocks(game)
            
            return True  # 블록이 파괴됨
        return False
    
    def explode_nearby_blocks(self, game):
        """폭탄 블록 폭발 시 주변 블록들 파괴"""
        explosion_range = BLOCK_SIZE + BLOCK_MARGIN + 10  # 폭발 범위
        
        for block in game.blocks:
            if block != self and block.active:
                # 거리 계산
                dx = abs(block.x - self.x)
                dy = abs(block.y - self.y)
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 폭발 범위 내의 블록들 파괴
                if distance <= explosion_range:
                    block.active = False
                    # 폭발로 파괴된 블록도 점수 추가
                    game.add_score(block.get_score_value())
    
    def get_score_value(self):
        """블록이 주는 점수 값 (체력에 비례)"""
        base_score = self.max_health * 10
        # 특수 블록은 보너스 점수
        if self.block_type == BLOCK_TYPE_BOMB:
            return base_score * 2  # 폭탄 블록은 2배 점수
        elif self.block_type == BLOCK_TYPE_SHIELD:
            return base_score * 3  # 방어막 블록은 3배 점수
        elif self.block_type == BLOCK_TYPE_GHOST:
            return base_score * 2  # 투명 블록은 2배 점수
        return base_score
        
    def move_down(self):
        self.y += BLOCK_SIZE + BLOCK_MARGIN
        
    def get_color(self):
        # 특수 블록 색상 우선 처리
        if self.block_type == BLOCK_TYPE_BOMB:
            return BOMB_BLOCK_COLOR
        elif self.block_type == BLOCK_TYPE_SHIELD:
            return SHIELD_BLOCK_COLOR
        elif self.block_type == BLOCK_TYPE_GHOST:
            return GHOST_BLOCK_COLOR
        
        # 일반 블록: 체력에 따라 그라데이션 색상 결정
        if self.health >= 15:
            return NEON_PINK
        elif self.health >= 12:
            return RED
        elif self.health >= 9:
            return ORANGE
        elif self.health >= 6:
            return YELLOW
        elif self.health >= 4:
            return GREEN
        elif self.health >= 2:
            return BLUE
        else:
            return PURPLE
            
    def draw(self, screen):
        if self.active:
            color = self.get_color()
            
            # 메인 블록 (그라데이션 효과)
            block_rect = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
            
            # 투명 블록은 반투명 효과
            if self.block_type == BLOCK_TYPE_GHOST:
                # 투명 블록 전용 서페이스 생성
                ghost_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(ghost_surface, (*color, 150), (0, 0, BLOCK_SIZE, BLOCK_SIZE), border_radius=8)
                screen.blit(ghost_surface, (self.x, self.y))
            else:
                pygame.draw.rect(screen, color, block_rect, border_radius=8)
            
            # 내부 하이라이트 (3D 효과)
            highlight_color = tuple(min(255, c + 40) for c in color)
            highlight_rect = pygame.Rect(self.x + 2, self.y + 2, BLOCK_SIZE - 4, BLOCK_SIZE//3)
            
            if self.block_type == BLOCK_TYPE_GHOST:
                highlight_surface = pygame.Surface((BLOCK_SIZE - 4, BLOCK_SIZE//3), pygame.SRCALPHA)
                pygame.draw.rect(highlight_surface, (*highlight_color, 150), (0, 0, BLOCK_SIZE - 4, BLOCK_SIZE//3), border_radius=6)
                screen.blit(highlight_surface, (self.x + 2, self.y + 2))
            else:
                pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=6)
            
            # 특수 블록 아이콘 표시
            self.draw_special_icon(screen)
            
            # 네온 테두리
            if self.block_type == BLOCK_TYPE_GHOST:
                # 투명 블록은 점선 테두리
                for i in range(0, BLOCK_SIZE, 8):
                    pygame.draw.rect(screen, WHITE, (self.x + i, self.y, 4, 2))
                    pygame.draw.rect(screen, WHITE, (self.x + i, self.y + BLOCK_SIZE - 2, 4, 2))
                    pygame.draw.rect(screen, WHITE, (self.x, self.y + i, 2, 4))
                    pygame.draw.rect(screen, WHITE, (self.x + BLOCK_SIZE - 2, self.y + i, 2, 4))
            else:
                pygame.draw.rect(screen, WHITE, block_rect, 2, border_radius=8)
            
            # 체력 표시 (더 모던한 스타일)
            self.draw_health_text(screen)
    
    def draw_special_icon(self, screen):
        """특수 블록 아이콘 그리기"""
        center_x = self.x + BLOCK_SIZE // 2
        center_y = self.y + BLOCK_SIZE // 2
        
        if self.block_type == BLOCK_TYPE_BOMB:
            # 폭탄 아이콘 (작은 원과 심지)
            pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y + 5), 8)
            pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y + 5), 8, 2)
            # 심지
            pygame.draw.line(screen, (255, 255, 0), (center_x - 5, center_y - 3), (center_x - 8, center_y - 8), 2)
            
        elif self.block_type == BLOCK_TYPE_SHIELD:
            # 방어막 아이콘 (방패 모양)
            shield_points = [
                (center_x, center_y - 8),
                (center_x - 6, center_y - 4),
                (center_x - 6, center_y + 4),
                (center_x, center_y + 8),
                (center_x + 6, center_y + 4),
                (center_x + 6, center_y - 4)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), shield_points)
            pygame.draw.polygon(screen, (0, 0, 0), shield_points, 2)
            
            # 방어막 히트 표시 (작은 점들)
            for i in range(self.shield_hits):
                pygame.draw.circle(screen, (255, 0, 0), (center_x - 4 + i * 4, center_y), 2)
                
        elif self.block_type == BLOCK_TYPE_GHOST:
            # 투명 블록 아이콘 (유령 모양)
            ghost_points = [
                (center_x, center_y - 6),
                (center_x - 5, center_y - 3),
                (center_x - 5, center_y + 3),
                (center_x - 3, center_y + 6),
                (center_x - 1, center_y + 4),
                (center_x + 1, center_y + 6),
                (center_x + 3, center_y + 4),
                (center_x + 5, center_y + 6),
                (center_x + 5, center_y - 3)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), ghost_points)
            # 눈
            pygame.draw.circle(screen, (0, 0, 0), (center_x - 2, center_y - 2), 1)
            pygame.draw.circle(screen, (0, 0, 0), (center_x + 2, center_y - 2), 1)
    
    def draw_health_text(self, screen):
        """체력 텍스트 그리기"""
        try:
            font = pygame.font.Font(None, 24)
            text = font.render(str(self.health), True, WHITE)
            text_rect = text.get_rect(center=(self.x + BLOCK_SIZE//2, self.y + BLOCK_SIZE//2 + 5))
            
            # 텍스트 그림자
            shadow = font.render(str(self.health), True, BLACK)
            shadow_rect = shadow.get_rect(center=(self.x + BLOCK_SIZE//2 + 1, self.y + BLOCK_SIZE//2 + 6))
            screen.blit(shadow, shadow_rect)
            screen.blit(text, text_rect)
        except:
            # 폰트 렌더링 실패 시 기본 처리
            try:
                default_font = pygame.font.Font(None, 20)
                text = default_font.render(str(self.health), True, WHITE)
                text_rect = text.get_rect(center=(self.x + BLOCK_SIZE//2, self.y + BLOCK_SIZE//2))
                screen.blit(text, text_rect)
            except:
                pass  # 텍스트 렌더링 완전 실패 시 숫자 없이 표시


class BonusBall:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BONUS_BALL_RADIUS
        self.active = True
        
    def move_down(self):
        """블록과 함께 아래로 이동"""
        self.y += BLOCK_SIZE + BLOCK_MARGIN
                
    def draw(self, screen):
        if self.active:
            # 펄스 애니메이션
            current_time = pygame.time.get_ticks()
            pulse = int(2 + math.sin(current_time / 300) * 2)
            
            # 글로우 효과
            for i in range(2, 0, -1):
                glow_color = (*BONUS_GREEN, 80 // i)
                glow_surface = pygame.Surface((self.radius * 2 + i * 6, self.radius * 2 + i * 6), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, 
                                 (self.radius + i * 3, self.radius + i * 3), self.radius + i + pulse)
                screen.blit(glow_surface, (int(self.x - self.radius - i * 3), int(self.y - self.radius - i * 3)))
            
            # 메인 보너스 볼
            pygame.draw.circle(screen, BONUS_GREEN, (int(self.x), int(self.y)), self.radius + pulse)
            
            # 내부 하이라이트
            highlight_color = tuple(min(255, c + 60) for c in BONUS_GREEN)
            pygame.draw.circle(screen, highlight_color, 
                             (int(self.x - 3), int(self.y - 3)), self.radius//2)
            
            # 외곽선
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius + pulse, 2)
            
            # "+1" 텍스트 (더 눈에 띄게)
            try:
                font = pygame.font.Font(None, 18)
                text = font.render("+1", True, BLACK)
                text_rect = text.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(text, text_rect)
            except:
                # 폰트 렌더링 실패 시 기본 처리
                try:
                    default_font = pygame.font.Font(None, 16)
                    text = default_font.render("+1", True, BLACK)
                    text_rect = text.get_rect(center=(int(self.x), int(self.y)))
                    screen.blit(text, text_rect)
                except:
                    pass  # 텍스트 렌더링 완전 실패 시 텍스트 없이 표시


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("볼즈 게임")
        self.clock = pygame.time.Clock()
        
        # 한글 폰트 설정 (더 안정적인 방법)
        font_loaded = False
        self.current_font_path = None
        
        # Windows 한글 폰트 경로들 (우선순위 순)
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",      # 맑은고딕
            "C:/Windows/Fonts/malgunbd.ttf",    # 맑은고딕 Bold
            "C:/Windows/Fonts/gulim.ttc",       # 굴림
            "C:/Windows/Fonts/batang.ttc",      # 바탕
            "C:/Windows/Fonts/dotum.ttc",       # 돋움
            "C:/Windows/Fonts/gungsuh.ttc",     # 궁서
            "malgun.ttf",                       # 상대경로 시도
            "gulim.ttc",
            "batang.ttc",
        ]
        
        # 한글 폰트 로딩 시도
        for font_path in font_paths:
            try:
                # 테스트 폰트 생성
                test_font = pygame.font.Font(font_path, 24)
                # 한글 렌더링 테스트
                test_surface = test_font.render("한글테스트", True, (255, 255, 255))
                
                # 성공하면 모든 폰트 생성
                self.font = pygame.font.Font(font_path, 24)
                self.small_font = pygame.font.Font(font_path, 18)
                self.large_font = pygame.font.Font(font_path, 28)
                self.title_font = pygame.font.Font(font_path, TITLE_FONT_SIZE)
                self.menu_font = pygame.font.Font(font_path, MENU_FONT_SIZE)
                
                self.current_font_path = font_path
                font_loaded = True
                print(f"한글 폰트 로딩 성공: {font_path}")
                break
            except Exception as e:
                continue
                
        # 한글 폰트 로딩 실패 시 시스템 기본 폰트 사용
        if not font_loaded:
            print("한글 폰트 로딩 실패, 기본 폰트 사용")
            try:
                # 시스템 기본 폰트로 대체
                self.font = pygame.font.SysFont('arial', 24)
                self.small_font = pygame.font.SysFont('arial', 18)
                self.large_font = pygame.font.SysFont('arial', 28)
                self.title_font = pygame.font.SysFont('arial', TITLE_FONT_SIZE)
                self.menu_font = pygame.font.SysFont('arial', MENU_FONT_SIZE)
            except:
                # 최후의 수단: pygame 기본 폰트
                self.font = pygame.font.Font(None, 32)
                self.small_font = pygame.font.Font(None, 24)
                self.large_font = pygame.font.Font(None, 36)
                self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE + 8)
                self.menu_font = pygame.font.Font(None, MENU_FONT_SIZE + 8)
        
        # 설정 값들
        self.settings = {
            "ball_speed": 11,
            "sound_enabled": True,
            "difficulty": "보통",
            "language": "ko"
        }
        
        # 언어 설정 초기화
        set_language(self.settings["language"])
        
        # 플레이어 이름 입력 상태
        self.entering_name = False
        self.player_name = ""
        self.input_active = False
        
        # 게임 오버 후 이름 입력 관련
        self.name_entered = False
        self.score_saved = False
        
        self.reset_game()
        
        # 게임 상태 관리
        self.game_state = GAME_STATE_TITLE
        self.selected_menu = 0  # 선택된 메뉴 항목
        self.settings_menu_selected = 0  # 설정 메뉴에서 선택된 항목
        
        self.shop = Shop(self.font, self.score)
        self.active_powerups = {1: False, 2: False, 3: False}  # 파워볼, 스피드볼, 매그넘볼
        
    def safe_render_text(self, font, text, color, fallback_font=None):
        """안전한 텍스트 렌더링 (한글 깨짐 방지)"""
        try:
            return font.render(text, True, color)
        except:
            # 폰트 렌더링 실패 시 대체 폰트 사용
            if fallback_font:
                try:
                    return fallback_font.render(text, True, color)
                except:
                    pass
            # 최후의 수단: 기본 폰트
            try:
                default_font = pygame.font.Font(None, 24)
                return default_font.render(str(text), True, color)
            except:
                # 텍스트를 ASCII로 변환
                safe_text = text.encode('ascii', 'ignore').decode('ascii')
                default_font = pygame.font.Font(None, 24)
                return default_font.render(safe_text if safe_text else "Text", True, color)
        
    def get_menu_items(self):
        """현재 언어에 따른 메뉴 항목들 반환"""
        return [
            get_text('menu_start'),
            get_text('menu_settings'), 
            get_text('menu_ranking'),
            get_text('menu_quit')
        ]
        
    def change_setting(self, increase=True):
        """설정 값 변경"""
        if self.settings_menu_selected == 0:  # 공 속도
            if increase:
                self.settings["ball_speed"] = min(20, self.settings["ball_speed"] + 1)
            else:
                self.settings["ball_speed"] = max(5, self.settings["ball_speed"] - 1)
        elif self.settings_menu_selected == 1:  # 사운드
            self.settings["sound_enabled"] = not self.settings["sound_enabled"]
        elif self.settings_menu_selected == 2:  # 난이도
            difficulties = [get_text('easy'), get_text('normal'), get_text('hard')]
            current_idx = 0
            if self.settings["difficulty"] in difficulties:
                current_idx = difficulties.index(self.settings["difficulty"])
            if increase:
                current_idx = (current_idx + 1) % len(difficulties)
            else:
                current_idx = (current_idx - 1) % len(difficulties)
            self.settings["difficulty"] = difficulties[current_idx]
        elif self.settings_menu_selected == 3:  # 언어
            languages = language_manager.get_supported_languages()
            current_idx = 0
            if self.settings["language"] in languages:
                current_idx = languages.index(self.settings["language"])
            if increase:
                current_idx = (current_idx + 1) % len(languages)
            else:
                current_idx = (current_idx - 1) % len(languages)
            self.settings["language"] = languages[current_idx]
            set_language(self.settings["language"])
        
    def reset_game(self):
        self.balls = []
        self.blocks = []
        self.bonus_balls = []
        self.round_num = 1
        self.ball_count = BALL_COUNT_START
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.launching = False
        self.launch_angle = 90
        self.launch_start_time = 0
        self.balls_launched = 0
        self.launch_x = SCREEN_WIDTH // 2
        self.round_in_progress = False
        self.bonus_balls_collected = 0
        self.last_ball_x = SCREEN_WIDTH // 2
        # 슈퍼볼 관련 변수 전체 삭제
        self.entering_name = False
        self.player_name = ""
        self.input_active = False
        self.name_entered = False
        self.score_saved = False
        self.generate_blocks()
    
    def add_score(self, points):
        """점수 추가"""
        self.score += points
    
    def save_game_score(self):
        """게임 점수를 데이터베이스에 저장"""
        if self.player_name.strip() and not self.score_saved:
            success = db_manager.save_score(
                self.player_name.strip(),
                self.score,
                self.round_num,
                self.ball_count
            )
            if success:
                self.score_saved = True
                print(f"점수 저장 완료: {self.player_name} - {self.score}점")
            return success
        return False
    
    def get_rankings(self, limit=10):
        """랭킹 조회"""
        return db_manager.get_top_scores(limit)
    
    def use_super_ball(self):
        pass  # 완전 삭제(호출도 제거)
        
    def generate_blocks(self):
        # 새로운 블록 라인을 맨 위에 추가
        occupied_positions = []  # 이미 사용된 위치들
        
        for col in range(BLOCKS_PER_ROW):
            if random.random() < 0.6:  # 60% 확률로 블록 생성 (보너스 볼 공간 확보)
                # 화면을 꽉 채우도록 블록 위치 계산 (왼쪽 여백 1px)
                x = 1 + col * (BLOCK_SIZE + BLOCK_MARGIN)
                y = BLOCK_START_Y
                health = self.round_num  # 라운드 수와 같은 체력
                
                # 특수 블록 타입 결정
                block_type = BLOCK_TYPE_NORMAL
                rand = random.random()
                
                if rand < BOMB_BLOCK_CHANCE:
                    block_type = BLOCK_TYPE_BOMB
                elif rand < BOMB_BLOCK_CHANCE + SHIELD_BLOCK_CHANCE:
                    block_type = BLOCK_TYPE_SHIELD
                elif rand < BOMB_BLOCK_CHANCE + SHIELD_BLOCK_CHANCE + GHOST_BLOCK_CHANCE:
                    block_type = BLOCK_TYPE_GHOST
                
                self.blocks.append(Block(x, y, health, block_type))
                occupied_positions.append(col)
        
        # 보너스 볼 생성 - 블록이 없는 위치에만 생성
        if random.random() < BONUS_BALL_SPAWN_CHANCE and len(occupied_positions) < BLOCKS_PER_ROW:
            available_cols = [col for col in range(BLOCKS_PER_ROW) if col not in occupied_positions]
            if available_cols:
                col = random.choice(available_cols)
                # 보너스 볼 위치도 동일하게 계산
                x = 1 + col * (BLOCK_SIZE + BLOCK_MARGIN) + BLOCK_SIZE // 2
                y = BLOCK_START_Y + BLOCK_SIZE // 2
                self.bonus_balls.append(BonusBall(x, y))
                occupied_positions.append(col)  # 보너스 볼이 생성된 위치도 점유됨으로 표시
        
        # 슈퍼볼 아이템 생성 코드 완전 삭제
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == GAME_STATE_TITLE:
                    self.handle_title_input(event.key)
                elif self.game_state == GAME_STATE_GAME:
                    if self.game_over and not self.name_entered and not self.score_saved:
                        # 게임 오버 시 이름 입력 처리
                        if event.key == pygame.K_RETURN:
                            if self.player_name.strip():
                                self.save_game_score()
                                self.name_entered = True
                            else:
                                self.name_entered = True  # 빈 이름으로도 진행 가능
                        elif event.key == pygame.K_ESCAPE:
                            self.name_entered = True  # 이름 입력 건너뛰기
                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]
                        else:
                            # 일반 문자 입력 (길이 제한)
                            if len(self.player_name) < 10 and event.unicode.isprintable():
                                self.player_name += event.unicode
                        self.input_active = True
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE and not self.game_over:
                        self.game_state = GAME_STATE_TITLE
                elif self.game_state == GAME_STATE_SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
                    elif event.key == pygame.K_UP:
                        self.settings_menu_selected = (self.settings_menu_selected - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        self.settings_menu_selected = (self.settings_menu_selected + 1) % 4
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.change_setting(event.key == pygame.K_RIGHT)
                elif self.game_state == GAME_STATE_RANKING:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
            elif event.type == pygame.MOUSEMOTION:
                if self.game_state == GAME_STATE_GAME and not self.game_over:
                    # 마우스 위치로 발사각도 계산
                    mouse_x, mouse_y = event.pos
                    if mouse_y < SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                        dx = mouse_x - self.launch_x
                        dy = (SCREEN_HEIGHT - BOTTOM_UI_HEIGHT) - mouse_y
                        if dy > 0:
                            angle = math.degrees(math.atan2(dy, dx))
                            self.launch_angle = max(MIN_LAUNCH_ANGLE, min(MAX_LAUNCH_ANGLE, angle))
                elif self.game_state == GAME_STATE_TITLE:
                    # 타이틀 화면에서 마우스 위치에 따라 메뉴 선택
                    mouse_x, mouse_y = event.pos
                    menu_items = self.get_menu_items()
                    for i in range(len(menu_items)):
                        y = MENU_START_Y + i * MENU_ITEM_HEIGHT
                        if y - 20 <= mouse_y <= y + 20:
                            self.selected_menu = i
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == GAME_STATE_TITLE:
                    # 타이틀 화면에서 마우스 클릭으로 메뉴 선택
                    mouse_x, mouse_y = event.pos
                    menu_items = self.get_menu_items()
                    for i in range(len(menu_items)):
                        y = MENU_START_Y + i * MENU_ITEM_HEIGHT
                        if y - 20 <= mouse_y <= y + 20:
                            self.selected_menu = i
                            # 선택된 메뉴 실행
                            if self.selected_menu == 0:  # 게임시작
                                self.game_state = GAME_STATE_GAME
                                self.reset_game()
                            elif self.selected_menu == 1:  # 게임 설정
                                self.game_state = GAME_STATE_SETTINGS
                            elif self.selected_menu == 2:  # 랭킹
                                self.game_state = GAME_STATE_RANKING
                            elif self.selected_menu == 3:  # 게임 종료
                                return False
                            break
                elif self.game_state == GAME_STATE_GAME and not self.game_over and not self.round_in_progress:
                    self.start_launch()
                    
        if self.shop.open:
            self.shop.handle_event(pygame.event.get())
            return True
            
        return True
        
    def handle_title_input(self, key):
        menu_items = self.get_menu_items()
        if key == pygame.K_UP:
            self.selected_menu = (self.selected_menu - 1) % len(menu_items)
        elif key == pygame.K_DOWN:
            self.selected_menu = (self.selected_menu + 1) % len(menu_items)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.selected_menu == 0:  # 게임시작
                self.game_state = GAME_STATE_GAME
                self.reset_game()
            elif self.selected_menu == 1:  # 게임 설정
                self.game_state = GAME_STATE_SETTINGS
            elif self.selected_menu == 2:  # 랭킹
                self.game_state = GAME_STATE_RANKING
            elif self.selected_menu == 3:  # 게임 종료
                return False
        
    def start_launch(self):
        # 라운드가 진행 중이 아닐 때만 새 라운드 시작
        if not self.round_in_progress:
            # 새 라운드 시작
            self.round_in_progress = True
            self.launching = True
            self.launch_start_time = pygame.time.get_ticks()
            self.balls_launched = 0
            
            # 슈퍼볼 모드 관련 코드 완전 삭제
            angle_rad = math.radians(self.launch_angle)
            dx = BALL_SPEED * math.cos(angle_rad)
            dy = -BALL_SPEED * math.sin(angle_rad)
            
            # 공 발사 (바닥보다 조금 위에서 발사)  
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            ball = Ball(self.launch_x, launch_y, dx, dy, self) # Game 인스턴스 전달
            self.balls.append(ball)
            self.balls_launched += 1
        
    def update(self):
        if self.shop.open:
            return
            
        if self.game_state != GAME_STATE_GAME:
            return
            
        if self.game_over:
            return
            
        current_time = pygame.time.get_ticks()
        
        # 자동 공 연속 발사 (연속 클릭하지 않아도 됨) - 슈퍼볼 모드에서는 스킵
        if (self.launching and self.balls_launched < self.ball_count and 
            current_time - self.launch_start_time >= self.balls_launched * BALL_LAUNCH_DELAY):
            
            angle_rad = math.radians(self.launch_angle)
            dx = BALL_SPEED * math.cos(angle_rad)
            dy = -BALL_SPEED * math.sin(angle_rad)
            
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            ball = Ball(self.launch_x, launch_y, dx, dy, self) # Game 인스턴스 전달
            self.balls.append(ball)
            self.balls_launched += 1
            
        # 공 이동 및 충돌 처리
        for ball in self.balls[:]:
            ball.move()
            
            # 블록과 충돌 검사
            for block in self.blocks[:]:  # 복사본을 사용하여 안전한 반복
                if ball.bounce_block(block):
                    # 투명 블록이 아닌 경우에만 hit 처리 (투명 블록은 bounce_block에서 처리됨)
                    if block.block_type != BLOCK_TYPE_GHOST:
                        if block.hit(self): # Game 인스턴스 전달
                            # 블록이 파괴되면 점수 추가
                            self.add_score(block.get_score_value())
                    else:
                        # 투명 블록이 파괴된 경우 점수 추가 (bounce_block에서 이미 hit 처리됨)
                        if not block.active:
                            self.add_score(block.get_score_value())
                        
            # 보너스 볼 수집
            for bonus in self.bonus_balls:
                if ball.collect_bonus(bonus):
                    bonus.active = False
                    self.bonus_balls_collected += 1  # 라운드 종료 후 적용
                    
            # 슈퍼볼 아이템 수집 코드 완전 삭제
                    
        # 보너스 볼은 고정된 위치에 있으므로 이동하지 않음
            
        # 비활성화된 객체들 제거 (마지막 공의 위치 추적)
        active_balls = []
        for ball in self.balls:
            if ball.active:
                active_balls.append(ball)
            else:
                # 공이 바닥에 떨어진 위치를 기록 (가장 최근에 떨어진 공)
                self.last_ball_x = ball.x
        self.balls = active_balls
        self.blocks = [block for block in self.blocks if block.active]
        self.bonus_balls = [bonus for bonus in self.bonus_balls if bonus.active]
        # 슈퍼볼 아이템 리스트 정리 코드 삭제
        
        # 모든 공이 바닥에 떨어졌는지 확인 (라운드 완료)
        if self.round_in_progress and self.balls_launched >= self.ball_count and len(self.balls) == 0:
            # 수집한 보너스 볼을 다음 라운드에 적용
            self.ball_count += self.bonus_balls_collected
            self.bonus_balls_collected = 0
            
            # 슈퍼볼 관련 코드 삭제
            self.launching = False
            self.round_in_progress = False
            self.next_round()
            
        # 게임 오버 체크 (블록이나 보너스 볼이 바닥에 닿음)
        for block in self.blocks:
            if block.active and block.y + BLOCK_SIZE >= SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                # 게임 오버 시 이름 입력 상태 활성화
                self.input_active = True
                break
                
        for bonus in self.bonus_balls:
            if bonus.active and bonus.y + bonus.radius >= SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                # 게임 오버 시 이름 입력 상태 활성화
                self.input_active = True
                break
                
        # 슈퍼볼 아이템 바닥 충돌 코드 삭제
                
        # 매그넘볼 효과: 공이 1개 남았을 때 모든 블록 제거
        if self.active_powerups[3] and len(self.balls) == 1:
            for block in self.blocks:
                block.active = False
            self.active_powerups[3] = False
        # 파워볼/스피드볼 효과 적용은 Ball/Block 처리에서 반영 예정
        # 라운드 종료 후 상점 오픈
        if self.round_in_progress and self.balls_launched >= self.ball_count and len(self.balls) == 0:
            self.shop.open = True
            self.shop.reset(self.score)
            
        # 블록 삭제 아이템 효과: shop.owned_items에 있으면 즉시 모든 블록 제거
        for item in self.shop.owned_items[:]:
            if item['name'] == "블록 삭제":
                for block in self.blocks:
                    block.active = False
                self.shop.owned_items.remove(item)
            
    def next_round(self):
        # 기존 블록들을 아래로 이동
        for block in self.blocks:
            if block.active:
                block.move_down()
                
        # 기존 보너스 볼들도 아래로 이동
        for bonus in self.bonus_balls:
            if bonus.active:
                bonus.move_down()
                
        # 새로운 블록 생성
        self.generate_blocks()
        
        # 라운드 증가
        self.round_num += 1
        
        # 발사 위치를 마지막 공이 떨어진 위치로 설정 (화면 경계 제한)
        self.launch_x = max(20, min(SCREEN_WIDTH - 20, self.last_ball_x))
        
        # 라운드 시작 시 파워업 초기화
        self.active_powerups = {1: False, 2: False, 3: False}
        self.shop.owned_items = []
        
    def draw_aim_line(self):
        # 게임 오버가 아니고 라운드가 진행 중이 아닐 때만 조준선 표시
        if not self.game_over and not self.round_in_progress:
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            angle_rad = math.radians(self.launch_angle)
            
            # 조준선 (그라데이션 점선 효과)
            for i in range(0, int(AIM_LINE_LENGTH), 12):
                alpha = max(50, 255 - i * 2)  # 거리에 따라 투명도 감소
                start_x = self.launch_x + i * math.cos(angle_rad)
                start_y = launch_y - i * math.sin(angle_rad)
                end_x_segment = start_x + 8 * math.cos(angle_rad)
                end_y_segment = start_y - 8 * math.sin(angle_rad)
                
                # 조준선 색상 (네온 효과)
                line_color = (*NEON_CYAN, alpha)
                line_surface = pygame.Surface((abs(end_x_segment - start_x) + 4, abs(end_y_segment - start_y) + 4), pygame.SRCALPHA)
                pygame.draw.line(line_surface, line_color, 
                               (2, 2), (end_x_segment - start_x + 2, end_y_segment - start_y + 2), 3)
                self.screen.blit(line_surface, (min(start_x, end_x_segment) - 2, min(start_y, end_y_segment) - 2))
            
            # 발사점 (펄스 효과)
            current_time = pygame.time.get_ticks()
            pulse = int(2 + math.sin(current_time / 200) * 2)
            
            # 글로우 효과
            for i in range(3, 0, -1):
                glow_color = (*NEON_CYAN, 60 // i)
                glow_surface = pygame.Surface((20 + i * 4, 20 + i * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, (10 + i * 2, 10 + i * 2), 8 + i + pulse)
                self.screen.blit(glow_surface, (self.launch_x - 10 - i * 2, launch_y - 10 - i * 2))
            
            # 메인 발사점
            pygame.draw.circle(self.screen, NEON_CYAN, (self.launch_x, launch_y), 8 + pulse)
            pygame.draw.circle(self.screen, WHITE, (self.launch_x, launch_y), 8 + pulse, 2)
            
            # 중앙 하이라이트
            pygame.draw.circle(self.screen, WHITE, (self.launch_x - 2, launch_y - 2), 3)
        
    def draw_ui(self):
        # 상단 UI - 글래스모피즘 스타일
        ui_surface = pygame.Surface((SCREEN_WIDTH, TOP_UI_HEIGHT), pygame.SRCALPHA)
        ui_surface.fill((*DARK_SURFACE, 200))  # 반투명 배경
        self.screen.blit(ui_surface, (0, 0))
        
        # 상단 테두리 (네온 액센트)
        pygame.draw.line(self.screen, ACCENT_COLOR, (0, TOP_UI_HEIGHT-1), (SCREEN_WIDTH, TOP_UI_HEIGHT-1), 2)
        
        # 점수 카드 (왼쪽)
        score_card = pygame.Rect(15, 10, 150, 60)
        pygame.draw.rect(self.screen, DARKER_SURFACE, score_card, border_radius=8)
        pygame.draw.rect(self.screen, NEON_CYAN, score_card, 1, border_radius=8)
        
        # 점수 텍스트
        score_label = self.safe_render_text(self.small_font, "SCORE", TEXT_SECONDARY)
        score_value = self.safe_render_text(self.font, f"{self.score:,}", NEON_CYAN)
        self.screen.blit(score_label, (25, 20))
        self.screen.blit(score_value, (25, 40))
        
        # 베스트 스코어 (작게)
        if self.high_score > 0:
            best_text = self.safe_render_text(self.small_font, f"BEST: {self.high_score:,}", TEXT_SECONDARY)
            self.screen.blit(best_text, (180, 25))
        
        # 라운드 카드 (오른쪽)
        round_card = pygame.Rect(SCREEN_WIDTH - 100, 10, 85, 60)
        pygame.draw.rect(self.screen, DARKER_SURFACE, round_card, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PURPLE, round_card, 1, border_radius=8)
        
        round_label = self.safe_render_text(self.small_font, "ROUND", TEXT_SECONDARY)
        round_value = self.safe_render_text(self.font, f"{self.round_num}", NEON_PURPLE)
        self.screen.blit(round_label, (SCREEN_WIDTH - 90, 20))
        self.screen.blit(round_value, (SCREEN_WIDTH - 75, 40))
        
        # 하단 UI - 글래스모피즘 스타일
        bottom_surface = pygame.Surface((SCREEN_WIDTH, BOTTOM_UI_HEIGHT), pygame.SRCALPHA)
        bottom_surface.fill((*DARK_SURFACE, 200))
        self.screen.blit(bottom_surface, (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT))
        
        # 하단 테두리
        pygame.draw.line(self.screen, ACCENT_COLOR, (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 2)
        
        # 공 개수 표시 (중앙, 더 큰 스타일)
        ball_bg = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 80, 120, 50)
        pygame.draw.rect(self.screen, DARKER_SURFACE, ball_bg, border_radius=25)
        pygame.draw.rect(self.screen, NEON_GREEN, ball_bg, 2, border_radius=25)
        
        # 공 아이콘 (원형)
        pygame.draw.circle(self.screen, NEON_GREEN, (SCREEN_WIDTH//2 - 30, SCREEN_HEIGHT - 55), 8)
        pygame.draw.circle(self.screen, WHITE, (SCREEN_WIDTH//2 - 30, SCREEN_HEIGHT - 55), 8, 2)
        
        ball_count_text = self.safe_render_text(self.font, f"×{self.ball_count}", WHITE)
        text_rect = ball_count_text.get_rect()
        text_rect.center = (SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT - 55)
        self.screen.blit(ball_count_text, text_rect)
        
        # 수집한 보너스 볼 표시 (펄스 애니메이션)
        if self.bonus_balls_collected > 0:
            current_time = pygame.time.get_ticks()
            pulse = int(20 + 10 * math.sin(current_time / 200))
            
            bonus_bg = pygame.Rect(SCREEN_WIDTH//2 + 70, SCREEN_HEIGHT - 70, 60, 30)
            pygame.draw.rect(self.screen, DARKER_SURFACE, bonus_bg, border_radius=15)
            pygame.draw.rect(self.screen, BONUS_GREEN, bonus_bg, 2, border_radius=15)
            
            bonus_text = self.safe_render_text(self.small_font, f"+{self.bonus_balls_collected}", BONUS_GREEN)
            bonus_rect = bonus_text.get_rect()
            bonus_rect.center = (SCREEN_WIDTH//2 + 100, SCREEN_HEIGHT - 55)
            self.screen.blit(bonus_text, bonus_rect)
            
        # 슈퍼볼 관련 UI 코드 삭제
        
    def draw(self):
        # 다크 테마 배경
        self.screen.fill(BLACK)
        
        if self.game_state == GAME_STATE_TITLE:
            self.draw_title()
        elif self.game_state == GAME_STATE_GAME:
            self.draw_game()
        elif self.game_state == GAME_STATE_SETTINGS:
            self.draw_settings()
        elif self.game_state == GAME_STATE_RANKING:
            self.draw_ranking()
            
        pygame.display.flip()
        
    def draw_title(self):
        # 다크 그라데이션 배경
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(15 + color_ratio * 10)  # 15-25
            g = int(15 + color_ratio * 10)  # 15-25  
            b = int(23 + color_ratio * 12)  # 23-35
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 네온 파티클 효과 (배경 장식)
        current_time = pygame.time.get_ticks()
        for i in range(20):
            x = (current_time // 50 + i * 20) % (SCREEN_WIDTH + 100) - 50
            y = 50 + i * 30
            alpha = int(128 + 127 * math.sin(current_time / 1000 + i))
            color = (*NEON_CYAN[:3], alpha)
            if hasattr(pygame, 'gfxdraw'):
                pygame.gfxdraw.filled_circle(self.screen, x, y, 2, color)
        
        # 게임 타이틀 (네온 효과)
        title_text = self.safe_render_text(self.title_font, "SpinBall", NEON_CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 120))
        
        # 네온 글로우 효과
        for offset in range(8, 0, -2):
            glow_color = (*NEON_CYAN, 30)
            glow_text = self.title_font.render("SpinBall", True, NEON_CYAN)
            glow_rect = glow_text.get_rect(center=(SCREEN_WIDTH//2, 120))
            # 글로우는 여러 레이어로 구현
            
        self.screen.blit(title_text, title_rect)
        
        # 서브타이틀
        subtitle = self.safe_render_text(self.small_font, "Modern Block Breaker", TEXT_SECONDARY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 160))
        self.screen.blit(subtitle, subtitle_rect)
        
        # 메뉴 항목들 (카드 스타일)
        menu_items = self.get_menu_items()
        for i, item in enumerate(menu_items):
            y = MENU_START_Y + i * MENU_ITEM_HEIGHT
            
            # 메뉴 카드 배경
            card_rect = pygame.Rect(30, y - 20, SCREEN_WIDTH - 60, 45)
            
            if i == self.selected_menu:
                # 선택된 메뉴: 네온 테두리와 글로우
                pygame.draw.rect(self.screen, DARKER_SURFACE, card_rect, border_radius=12)
                pygame.draw.rect(self.screen, NEON_CYAN, card_rect, 2, border_radius=12)
                text_color = NEON_CYAN
                
                # 선택 인디케이터
                indicator_rect = pygame.Rect(35, y - 15, 4, 35)
                pygame.draw.rect(self.screen, NEON_CYAN, indicator_rect, border_radius=2)
            else:
                # 일반 메뉴: 서브틀한 배경
                pygame.draw.rect(self.screen, DARK_SURFACE, card_rect, border_radius=12)
                pygame.draw.rect(self.screen, DARK_GRAY, card_rect, 1, border_radius=12)
                text_color = WHITE
            
            # 메뉴 텍스트 (한글 지원)
            try:
                if self.current_font_path:
                    menu_font = pygame.font.Font(self.current_font_path, MENU_FONT_SIZE)
                else:
                    menu_font = self.menu_font
            except:
                menu_font = self.menu_font
            
            menu_text = self.safe_render_text(menu_font, item, text_color)
            menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(menu_text, menu_rect)
        
        # 조작법 안내 (모던 스타일)
        control_card = pygame.Rect(20, SCREEN_HEIGHT - 80, SCREEN_WIDTH - 40, 60)
        control_surface = pygame.Surface((SCREEN_WIDTH - 40, 60), pygame.SRCALPHA)
        control_surface.fill((*DARK_SURFACE, 150))
        self.screen.blit(control_surface, (20, SCREEN_HEIGHT - 80))
        pygame.draw.rect(self.screen, TEXT_SECONDARY, control_card, 1, border_radius=10)
        
        control_text = self.safe_render_text(self.small_font, "Navigate: ↑↓ • Select: ENTER • Mouse Click", TEXT_SECONDARY)
        control_rect = control_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
        self.screen.blit(control_text, control_rect)
        
    def draw_game(self):
        # UI 그리기
        self.draw_ui()
        
        # 블록 그리기
        for block in self.blocks:
            block.draw(self.screen)
            
        # 보너스 볼 그리기
        for bonus in self.bonus_balls:
            bonus.draw(self.screen)
            
        # 슈퍼볼 아이템 그리기 코드 삭제
            
        # 공 그리기
        for ball in self.balls:
            ball.draw(self.screen)
            
        # 조준선 그리기
        self.draw_aim_line()
        
        # 게임 오버 메시지 (모던 스타일)
        if self.game_over:
            # 블러 효과를 위한 다크 오버레이
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*BLACK, 200))
            self.screen.blit(overlay, (0, 0))
            
            # 게임 오버 카드
            card_rect = pygame.Rect(30, SCREEN_HEIGHT//2 - 150, SCREEN_WIDTH - 60, 300)
            pygame.draw.rect(self.screen, DARKER_SURFACE, card_rect, border_radius=20)
            pygame.draw.rect(self.screen, NEON_PINK, card_rect, 3, border_radius=20)
            
            # 게임 오버 타이틀 (네온 효과)
            game_over_text = self.safe_render_text(self.large_font, get_text('game_over'), NEON_PINK)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            self.screen.blit(game_over_text, game_over_rect)
            
            # 점수 표시 (하이라이트)
            score_label = self.safe_render_text(self.small_font, "FINAL SCORE", TEXT_SECONDARY)
            score_value = self.safe_render_text(self.font, f"{self.score:,}", NEON_CYAN)
            score_label_rect = score_label.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
            score_value_rect = score_value.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 35))
            self.screen.blit(score_label, score_label_rect)
            self.screen.blit(score_value, score_value_rect)
            
            # 이름 입력 또는 저장 완료 상태에 따른 메시지
            if not self.name_entered and not self.score_saved:
                name_prompt_text = self.font.render("Enter your name:", True, WHITE)
                name_prompt_rect = name_prompt_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
                self.screen.blit(name_prompt_text, name_prompt_rect)
                
                # 모던 입력 박스
                input_box = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 40, 240, 40)
                pygame.draw.rect(self.screen, DARK_SURFACE, input_box, border_radius=8)
                pygame.draw.rect(self.screen, NEON_CYAN, input_box, 2, border_radius=8)
                
                # 입력된 텍스트 표시
                name_text = self.font.render(self.player_name, True, WHITE)
                name_text_rect = name_text.get_rect(center=input_box.center)
                self.screen.blit(name_text, name_text_rect)
                
                # 네온 커서 (깜빡임 효과)
                if self.input_active and (pygame.time.get_ticks() // 400) % 2:
                    cursor_x = name_text_rect.right + 3
                    pygame.draw.line(self.screen, NEON_CYAN, 
                                   (cursor_x, input_box.y + 8), (cursor_x, input_box.bottom - 8), 2)
                
                # 안내 텍스트
                confirm_text = self.small_font.render("ENTER: Save • ESC: Skip", True, TEXT_SECONDARY)
                confirm_rect = confirm_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
                self.screen.blit(confirm_text, confirm_rect)
                
            elif self.score_saved:
                # 저장 완료 메시지
                saved_icon = "✓"
                saved_text = self.font.render(f"{saved_icon} Score Saved!", True, NEON_GREEN)
                saved_rect = saved_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
                self.screen.blit(saved_text, saved_rect)
                
                restart_text = self.small_font.render(get_text('restart_hint'), True, TEXT_SECONDARY)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
                self.screen.blit(restart_text, restart_rect)
            else:
                restart_text = self.small_font.render(get_text('restart_hint'), True, TEXT_SECONDARY)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
                self.screen.blit(restart_text, restart_rect)
        
        # 조작법 (첫 라운드에만 표시) - 모던 스타일
        elif self.round_num == 1 and not self.round_in_progress:
            # 반투명 도움말 카드
            help_card = pygame.Rect(20, SCREEN_HEIGHT//2 - 40, SCREEN_WIDTH - 40, 80)
            help_surface = pygame.Surface((SCREEN_WIDTH - 40, 80), pygame.SRCALPHA)
            help_surface.fill((*DARK_SURFACE, 180))
            self.screen.blit(help_surface, (20, SCREEN_HEIGHT//2 - 40))
            pygame.draw.rect(self.screen, ACCENT_COLOR, help_card, 2, border_radius=12)
            
            # 도움말 텍스트
            help_text1 = self.small_font.render("🎯 Mouse: Aim • Click: Shoot", True, WHITE)
            help_text2 = self.small_font.render("ESC: Back to Menu", True, TEXT_SECONDARY)
            
            help_rect1 = help_text1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
            help_rect2 = help_text2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 15))
            
            self.screen.blit(help_text1, help_rect1)
            self.screen.blit(help_text2, help_rect2)
            
            # 슈퍼볼 도움말 삭제
            
    def draw_settings(self):
        # 다크 그라데이션 배경
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(15 + color_ratio * 10)
            g = int(15 + color_ratio * 10)  
            b = int(23 + color_ratio * 12)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 설정 메인 카드
        settings_card = pygame.Rect(20, 50, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 100)
        pygame.draw.rect(self.screen, DARKER_SURFACE, settings_card, border_radius=20)
        pygame.draw.rect(self.screen, NEON_ORANGE, settings_card, 3, border_radius=20)
        
        # 제목 (네온 효과)
        try:
            if self.current_font_path:
                title_font = pygame.font.Font(self.current_font_path, 36)
            else:
                title_font = self.large_font
        except:
            title_font = self.large_font
        title_text = self.safe_render_text(title_font, "⚙️ " + get_text('settings_title'), NEON_ORANGE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 90))
        self.screen.blit(title_text, title_rect)
        
        # 설정 항목들 (카드 스타일)
        settings_text = [
            f"{get_text('ball_speed')}: {self.settings['ball_speed']}",
            f"{get_text('sound')}: {get_text('sound_on') if self.settings['sound_enabled'] else get_text('sound_off')}",
            f"{get_text('difficulty')}: {self.settings['difficulty']}",
            f"{get_text('language')}: {language_manager.get_language_name(self.settings['language'])}"
        ]
        
        for i, text in enumerate(settings_text):
            y = 160 + i * 70
            
            # 설정 항목 카드
            item_card = pygame.Rect(40, y - 25, SCREEN_WIDTH - 80, 50)
            
            if i == self.settings_menu_selected:
                # 선택된 항목: 네온 하이라이트
                pygame.draw.rect(self.screen, DARK_SURFACE, item_card, border_radius=12)
                pygame.draw.rect(self.screen, NEON_CYAN, item_card, 2, border_radius=12)
                text_color = NEON_CYAN
                
                # 선택 인디케이터
                indicator = pygame.Rect(45, y - 20, 4, 40)
                pygame.draw.rect(self.screen, NEON_CYAN, indicator, border_radius=2)
            else:
                pygame.draw.rect(self.screen, DARK_SURFACE, item_card, border_radius=12)
                pygame.draw.rect(self.screen, DARK_GRAY, item_card, 1, border_radius=12)
                text_color = WHITE
            
            try:
                if self.current_font_path:
                    setting_font = pygame.font.Font(self.current_font_path, 24)
                else:
                    setting_font = self.font
            except:
                setting_font = self.font
            setting_text = setting_font.render(text, True, text_color)
            setting_rect = setting_text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(setting_text, setting_rect)
        
        # 조작 안내 (모던 스타일)
        help_card = pygame.Rect(30, SCREEN_HEIGHT - 90, SCREEN_WIDTH - 60, 60)
        pygame.draw.rect(self.screen, DARK_SURFACE, help_card, border_radius=12)
        pygame.draw.rect(self.screen, TEXT_SECONDARY, help_card, 1, border_radius=12)
        
        try:
            if self.current_font_path:
                help_font = pygame.font.Font(self.current_font_path, 18)
            else:
                help_font = self.small_font
        except:
            help_font = self.small_font
        
        help_texts = [
            "↑↓: Select • ←→: Change",
            get_text('back_to_title')
        ]
        
        for i, help_text in enumerate(help_texts):
            y = SCREEN_HEIGHT - 75 + i * 20
            text_surface = help_font.render(help_text, True, TEXT_SECONDARY)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text_surface, text_rect)
        
    def draw_ranking(self):
        # 다크 그라데이션 배경
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(15 + color_ratio * 10)
            g = int(15 + color_ratio * 10)  
            b = int(23 + color_ratio * 12)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 랭킹 메인 카드
        ranking_card = pygame.Rect(20, 40, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 80)
        pygame.draw.rect(self.screen, DARKER_SURFACE, ranking_card, border_radius=20)
        pygame.draw.rect(self.screen, NEON_YELLOW, ranking_card, 3, border_radius=20)
        
        # 제목 (트로피 이모지와 네온 효과)
        try:
            if self.current_font_path:
                title_font = pygame.font.Font(self.current_font_path, 36)
            else:
                title_font = self.large_font
        except:
            title_font = self.large_font
        title_text = self.safe_render_text(title_font, "🏆 " + get_text('ranking_title'), NEON_YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 데이터베이스에서 랭킹 가져오기
        rankings = self.get_rankings(8)  # 화면에 맞게 8개로 제한
        
        if rankings:
            # 헤더 카드
            header_card = pygame.Rect(30, 110, SCREEN_WIDTH - 60, 30)
            pygame.draw.rect(self.screen, DARK_SURFACE, header_card, border_radius=8)
            
            try:
                if self.current_font_path:
                    header_font = pygame.font.Font(self.current_font_path, 16)
                else:
                    header_font = self.small_font
            except:
                header_font = self.small_font
            
            header_text = header_font.render("RANK  PLAYER    SCORE   ROUND", True, TEXT_SECONDARY)
            header_rect = header_text.get_rect(center=(SCREEN_WIDTH//2, 125))
            self.screen.blit(header_text, header_rect)
            
            # 랭킹 목록 (카드 스타일)
            for i, (name, score, round_reached, balls_count, play_date) in enumerate(rankings):
                y = 155 + i * 55
                
                # 랭킹 카드
                rank_card = pygame.Rect(30, y, SCREEN_WIDTH - 60, 45)
                
                # 순위별 색상과 스타일
                if i == 0:
                    pygame.draw.rect(self.screen, DARK_SURFACE, rank_card, border_radius=10)
                    pygame.draw.rect(self.screen, (255, 215, 0), rank_card, 2, border_radius=10)  # 금색
                    text_color = (255, 215, 0)
                    rank_icon = "🥇"
                elif i == 1:
                    pygame.draw.rect(self.screen, DARK_SURFACE, rank_card, border_radius=10)
                    pygame.draw.rect(self.screen, (192, 192, 192), rank_card, 2, border_radius=10)  # 은색
                    text_color = (192, 192, 192)
                    rank_icon = "🥈"
                elif i == 2:
                    pygame.draw.rect(self.screen, DARK_SURFACE, rank_card, border_radius=10)
                    pygame.draw.rect(self.screen, (205, 127, 50), rank_card, 2, border_radius=10)  # 동색
                    text_color = (205, 127, 50)
                    rank_icon = "🥉"
                else:
                    pygame.draw.rect(self.screen, DARK_SURFACE, rank_card, border_radius=10)
                    pygame.draw.rect(self.screen, DARK_GRAY, rank_card, 1, border_radius=10)
                    text_color = WHITE
                    rank_icon = f"{i+1}"
                
                try:
                    if self.current_font_path:
                        rank_font = pygame.font.Font(self.current_font_path, 18)
                    else:
                        rank_font = self.small_font
                except:
                    rank_font = self.small_font
                
                # 순위 표시
                rank_text = rank_font.render(rank_icon, True, text_color)
                self.screen.blit(rank_text, (45, y + 5))
                
                # 플레이어 이름
                name_text = rank_font.render(name[:8], True, text_color)
                self.screen.blit(name_text, (80, y + 5))
                
                # 점수 (강조)
                score_text = rank_font.render(f"{score:,}", True, NEON_CYAN)
                score_rect = score_text.get_rect()
                score_rect.right = SCREEN_WIDTH - 120
                score_rect.y = y + 5
                self.screen.blit(score_text, score_rect)
                
                # 라운드
                round_text = rank_font.render(f"R{round_reached}", True, text_color)
                round_rect = round_text.get_rect()
                round_rect.right = SCREEN_WIDTH - 50
                round_rect.y = y + 5
                self.screen.blit(round_text, round_rect)
                
                # 날짜 (작게)
                try:
                    if self.current_font_path:
                        date_font = pygame.font.Font(self.current_font_path, 12)
                    else:
                        date_font = pygame.font.Font(None, 14)
                except:
                    date_font = pygame.font.Font(None, 14)
                
                date_str = play_date.split()[0] if play_date else ""
                date_text = date_font.render(date_str, True, TEXT_SECONDARY)
                self.screen.blit(date_text, (80, y + 25))
        else:
            # 랭킹이 없을 때
            empty_card = pygame.Rect(40, SCREEN_HEIGHT//2 - 40, SCREEN_WIDTH - 80, 80)
            pygame.draw.rect(self.screen, DARK_SURFACE, empty_card, border_radius=12)
            pygame.draw.rect(self.screen, TEXT_SECONDARY, empty_card, 1, border_radius=12)
            
            try:
                if self.current_font_path:
                    no_rank_font = pygame.font.Font(self.current_font_path, 20)
                else:
                    no_rank_font = self.font
            except:
                no_rank_font = self.font
            
            no_rank_text = no_rank_font.render("No scores yet", True, TEXT_SECONDARY)
            no_rank_rect = no_rank_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(no_rank_text, no_rank_rect)
        
        # 통계 정보 (하단 카드)
        stats = db_manager.get_database_stats()
        if stats['total_games'] > 0:
            stats_card = pygame.Rect(30, SCREEN_HEIGHT - 70, SCREEN_WIDTH - 60, 40)
            pygame.draw.rect(self.screen, DARK_SURFACE, stats_card, border_radius=10)
            
            try:
                if self.current_font_path:
                    stats_font = pygame.font.Font(self.current_font_path, 14)
                else:
                    stats_font = pygame.font.Font(None, 16)
            except:
                stats_font = pygame.font.Font(None, 16)
            
            stats_text = stats_font.render(
                f"Total Games: {stats['total_games']} • Avg Score: {stats['average_score']}", 
                True, TEXT_SECONDARY
            )
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(stats_text, stats_rect)
        
        # 돌아가기 안내
        try:
            if self.current_font_path:
                back_font = pygame.font.Font(self.current_font_path, 16)
            else:
                back_font = self.small_font
        except:
            back_font = self.small_font
        back_text = back_font.render("ESC: " + get_text('back_to_title'), True, TEXT_SECONDARY)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 20))
        self.screen.blit(back_text, back_rect)
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit() 