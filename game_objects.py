import pygame
import math
import random
from constants import *
from language import get_text, set_language, get_current_language, language_manager
from database import db_manager


class Ball:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = BALL_RADIUS
        self.active = True
        
    def move(self):
        if not self.active:
            return
        
        self.x += self.dx
        self.y += self.dy
        
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
            color = CYAN
            outline_color = WHITE
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, outline_color, (int(self.x), int(self.y)), self.radius, 2)


class Block:
    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.active = True
        
    def hit(self):
        if self.active:
            self.health -= 1
            if self.health <= 0:
                self.active = False
                return True  # 블록이 파괴됨
        return False
    
    def get_score_value(self):
        """블록이 주는 점수 값 (체력에 비례)"""
        return self.max_health * 10
        
    def move_down(self):
        self.y += BLOCK_SIZE + BLOCK_MARGIN
        
    def get_color(self):
        # 체력에 따라 색상 결정
        if self.health >= 10:
            return RED
        elif self.health >= 7:
            return ORANGE
        elif self.health >= 4:
            return YELLOW
        elif self.health >= 2:
            return GREEN
        else:
            return BLUE
            
    def draw(self, screen):
        if self.active:
            # 블록 그리기 (둥근 모서리 효과)
            color = self.get_color()
            pygame.draw.rect(screen, color, (self.x, self.y, BLOCK_SIZE, BLOCK_SIZE), border_radius=5)
            pygame.draw.rect(screen, WHITE, (self.x, self.y, BLOCK_SIZE, BLOCK_SIZE), 2, border_radius=5)
            
            # 숫자 표시 (더 큰 폰트)
            font = pygame.font.Font(None, 28)
            text = font.render(str(self.health), True, BLACK)
            text_rect = text.get_rect(center=(self.x + BLOCK_SIZE//2, self.y + BLOCK_SIZE//2))
            screen.blit(text, text_rect)


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
            # 녹색 원 그리기
            pygame.draw.circle(screen, BONUS_GREEN, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)
            
            # "+" 표시
            font = pygame.font.Font(None, 20)
            text = font.render("+1", True, WHITE)
            text_rect = text.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(text, text_rect)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("볼즈 게임")
        self.clock = pygame.time.Clock()
        
        # 한글 폰트 설정 시도
        font_loaded = False
        font_paths = [
            "malgun.ttf",  # Windows 맑은고딕
            "C:/Windows/Fonts/malgun.ttf",
            "gulim.ttc",   # Windows 굴림
            "C:/Windows/Fonts/gulim.ttc",
            "batang.ttc",  # Windows 바탕
            "C:/Windows/Fonts/batang.ttc",
        ]
        
        for font_path in font_paths:
            try:
                self.font = pygame.font.Font(font_path, 24)
                self.small_font = pygame.font.Font(font_path, 20)
                self.large_font = pygame.font.Font(font_path, 28)
                font_loaded = True
                break
            except:
                continue
                
        if not font_loaded:
            # 시스템 기본 폰트 사용
            self.font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
            self.large_font = pygame.font.Font(None, 36)
        
        # 타이틀 화면용 한글 폰트 추가
        self.current_font_path = None
        for font_path in font_paths:
            try:
                # 각 폰트 경로를 테스트
                test_font = pygame.font.Font(font_path, 24)
                self.current_font_path = font_path
                break
            except:
                continue
                
        # 타이틀 화면용 폰트 생성
        try:
            if self.current_font_path:
                self.title_font = pygame.font.Font(self.current_font_path, TITLE_FONT_SIZE)
                self.menu_font = pygame.font.Font(self.current_font_path, MENU_FONT_SIZE)
            else:
                raise Exception("No Korean font found")
        except:
            # 한글 폰트 로딩 실패 시 기본 폰트 사용
            self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
            self.menu_font = pygame.font.Font(None, MENU_FONT_SIZE)
        
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
                self.blocks.append(Block(x, y, health))
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
            ball = Ball(self.launch_x, launch_y, dx, dy)
            self.balls.append(ball)
            self.balls_launched += 1
        
    def update(self):
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
            self.balls.append(Ball(self.launch_x, launch_y, dx, dy))
            self.balls_launched += 1
            
        # 공 이동 및 충돌 처리
        for ball in self.balls[:]:
            ball.move()
            
            # 블록과 충돌 검사
            for block in self.blocks[:]:  # 복사본을 사용하여 안전한 반복
                if ball.bounce_block(block):
                    if block.hit():
                        # 블록이 파괴되면 점수 추가
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
        
    def draw_aim_line(self):
        # 게임 오버가 아니고 라운드가 진행 중이 아닐 때만 조준선 표시
        if not self.game_over and not self.round_in_progress:
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            
            # 슈퍼볼 모드 조준선 코드 삭제
            angle_rad = math.radians(self.launch_angle)
            
            # 조준선 (점선 효과)
            for i in range(0, int(AIM_LINE_LENGTH), 10):
                start_x = self.launch_x + i * math.cos(angle_rad)
                start_y = launch_y - i * math.sin(angle_rad)
                end_x_segment = start_x + 5 * math.cos(angle_rad)
                end_y_segment = start_y - 5 * math.sin(angle_rad)
                
                pygame.draw.line(self.screen, CYAN, 
                               (start_x, start_y), (end_x_segment, end_y_segment), 2)
            
            # 발사점 표시
            pygame.draw.circle(self.screen, CYAN, 
                             (self.launch_x, launch_y), 8)
            pygame.draw.circle(self.screen, BLACK, 
                             (self.launch_x, launch_y), 8, 2)
        
    def draw_ui(self):
        # 상단 UI 배경
        pygame.draw.rect(self.screen, UI_BG_COLOR, (0, 0, SCREEN_WIDTH, TOP_UI_HEIGHT))
        pygame.draw.line(self.screen, GRAY, (0, TOP_UI_HEIGHT), (SCREEN_WIDTH, TOP_UI_HEIGHT), 2)
        
        # 점수 표시
        score_text = self.small_font.render(f"{get_text('score')}: {self.score}", True, UI_TEXT_COLOR)
        high_score_text = self.small_font.render(f"Best: {self.high_score}", True, UI_TEXT_COLOR)
        
        self.screen.blit(high_score_text, (20, 15))
        self.screen.blit(score_text, (20, 40))
        
        # 라운드 표시
        round_text = self.small_font.render(f"{get_text('round')}: {self.round_num}", True, UI_TEXT_COLOR)
        self.screen.blit(round_text, (SCREEN_WIDTH - 120, 15))
        
        # 하단 UI 배경
        pygame.draw.rect(self.screen, UI_BG_COLOR, 
                        (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT, SCREEN_WIDTH, BOTTOM_UI_HEIGHT))
        pygame.draw.line(self.screen, GRAY, 
                        (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 2)
        
        # 공 개수 표시
        ball_count_text = self.font.render(f"x{self.ball_count}", True, UI_TEXT_COLOR)
        text_rect = ball_count_text.get_rect()
        text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)
        self.screen.blit(ball_count_text, text_rect)
        
        # 수집한 보너스 볼 표시 (있을 때만)
        if self.bonus_balls_collected > 0:
            bonus_text = self.small_font.render(f"+{self.bonus_balls_collected}", True, BONUS_GREEN)
            bonus_rect = bonus_text.get_rect()
            bonus_rect.center = (SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT - 30)
            self.screen.blit(bonus_text, bonus_rect)
            
        # 슈퍼볼 관련 UI 코드 삭제
        
    def draw(self):
        self.screen.fill(WHITE)
        
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
        # 배경 그라데이션 효과
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            color = (
                int(50 + color_ratio * 100),
                int(50 + color_ratio * 150),
                int(100 + color_ratio * 100)
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # 게임 타이틀
        title_text = self.title_font.render("SpinBall", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        
        # 타이틀 그림자 효과
        shadow_text = self.title_font.render("SpinBall", True, BLACK)
        shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH//2 + 3, 153))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # 메뉴 항목들
        menu_items = self.get_menu_items()
        for i, item in enumerate(menu_items):
            y = MENU_START_Y + i * MENU_ITEM_HEIGHT
            
            # 선택된 메뉴 하이라이트
            if i == self.selected_menu:
                # 하이라이트 배경 (더 부드러운 애니메이션 효과)
                highlight_rect = pygame.Rect(40, y - 25, SCREEN_WIDTH - 80, 50)
                pygame.draw.rect(self.screen, CYAN, highlight_rect, border_radius=25)
                pygame.draw.rect(self.screen, WHITE, highlight_rect, 3, border_radius=25)
                text_color = BLACK
                font_size_add = 6
            else:
                text_color = WHITE
                font_size_add = 0
            
            # 메뉴 텍스트 (한글 지원)
            try:
                if self.current_font_path:
                    menu_font = pygame.font.Font(self.current_font_path, MENU_FONT_SIZE + font_size_add)
                else:
                    menu_font = pygame.font.Font(None, MENU_FONT_SIZE + font_size_add)
            except:
                menu_font = pygame.font.Font(None, MENU_FONT_SIZE + font_size_add)
            menu_text = menu_font.render(item, True, text_color)
            menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(menu_text, menu_rect)
        
        # 조작법 안내
        control_text = self.small_font.render("↑↓ 선택, Enter 확인 또는 마우스 클릭", True, LIGHT_GRAY)
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
        
        # 게임 오버 메시지
        if self.game_over:
            # 반투명 오버레이
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.large_font.render(get_text('game_over'), True, WHITE)
            score_text = self.font.render(f"{get_text('score')}: {self.score}", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(score_text, score_rect)
            
            # 이름 입력 또는 저장 완료 상태에 따른 메시지
            if not self.name_entered and not self.score_saved:
                name_prompt_text = self.font.render("이름을 입력하세요:", True, WHITE)
                name_prompt_rect = name_prompt_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(name_prompt_text, name_prompt_rect)
                
                # 입력 박스
                input_box = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 25, 200, 30)
                pygame.draw.rect(self.screen, WHITE, input_box)
                pygame.draw.rect(self.screen, BLACK, input_box, 2)
                
                # 입력된 텍스트 표시
                name_text = self.font.render(self.player_name, True, BLACK)
                name_text_rect = name_text.get_rect(center=input_box.center)
                self.screen.blit(name_text, name_text_rect)
                
                # 커서 표시 (깜빡임 효과)
                if self.input_active and (pygame.time.get_ticks() // 500) % 2:
                    cursor_x = name_text_rect.right + 2
                    pygame.draw.line(self.screen, BLACK, (cursor_x, input_box.y + 5), (cursor_x, input_box.bottom - 5), 2)
                
                confirm_text = self.small_font.render("Enter: 저장, ESC: 건너뛰기", True, LIGHT_GRAY)
                confirm_rect = confirm_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
                self.screen.blit(confirm_text, confirm_rect)
                
            elif self.score_saved:
                saved_text = self.font.render("점수가 저장되었습니다!", True, GREEN)
                saved_rect = saved_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(saved_text, saved_rect)
                
                restart_text = self.small_font.render(get_text('restart_hint'), True, LIGHT_GRAY)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
                self.screen.blit(restart_text, restart_rect)
            else:
                restart_text = self.small_font.render(get_text('restart_hint'), True, LIGHT_GRAY)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
                self.screen.blit(restart_text, restart_rect)
        
        # 조작법 (첫 라운드에만 표시)
        elif self.round_num == 1 and not self.round_in_progress:
            help_text = self.small_font.render("마우스로 조준, 클릭으로 발사 (ESC: 타이틀로)", True, GRAY)
            help_rect = help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(help_text, help_rect)
            
            # 슈퍼볼 도움말 삭제
            
    def draw_settings(self):
        self.screen.fill(DARK_GRAY)
        
        # 제목 (한글 지원)
        try:
            if self.current_font_path:
                title_font = pygame.font.Font(self.current_font_path, 36)
            else:
                title_font = self.large_font
        except:
            title_font = self.large_font
        title_text = title_font.render(get_text('settings_title'), True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 설정 항목들 (한글 지원)
        settings_text = [
            f"{get_text('ball_speed')}: {self.settings['ball_speed']}",
            f"{get_text('sound')}: {get_text('sound_on') if self.settings['sound_enabled'] else get_text('sound_off')}",
            f"{get_text('difficulty')}: {self.settings['difficulty']}",
            f"{get_text('language')}: {language_manager.get_language_name(self.settings['language'])}"
        ]
        
        for i, text in enumerate(settings_text):
            y = 150 + i * 60
            
            # 선택된 항목 하이라이트
            if i == self.settings_menu_selected:
                highlight_rect = pygame.Rect(50, y - 25, SCREEN_WIDTH - 100, 50)
                pygame.draw.rect(self.screen, (50, 50, 80), highlight_rect, border_radius=10)
                text_color = YELLOW
            else:
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
        
        # 조작 안내 (한글 지원)
        try:
            if self.current_font_path:
                help_font = pygame.font.Font(self.current_font_path, 18)
            else:
                help_font = self.small_font
        except:
            help_font = self.small_font
        
        help_texts = [
            "↑↓: 항목 선택, ←→: 값 변경",
            get_text('back_to_title')
        ]
        
        for i, help_text in enumerate(help_texts):
            y = SCREEN_HEIGHT - 80 + i * 25
            text_surface = help_font.render(help_text, True, LIGHT_GRAY)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text_surface, text_rect)
        
    def draw_ranking(self):
        self.screen.fill(DARK_GRAY)
        
        # 제목 (한글 지원)
        try:
            if self.current_font_path:
                title_font = pygame.font.Font(self.current_font_path, 36)
            else:
                title_font = self.large_font
        except:
            title_font = self.large_font
        title_text = title_font.render(get_text('ranking_title'), True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 데이터베이스에서 랭킹 가져오기
        rankings = self.get_rankings(10)
        
        if rankings:
            # 헤더
            try:
                if self.current_font_path:
                    header_font = pygame.font.Font(self.current_font_path, 18)
                else:
                    header_font = self.small_font
            except:
                header_font = self.small_font
            
            header_text = header_font.render("순위  플레이어    점수    라운드", True, LIGHT_GRAY)
            header_rect = header_text.get_rect(center=(SCREEN_WIDTH//2, 130))
            self.screen.blit(header_text, header_rect)
            
            # 랭킹 목록 (한글 지원)
            for i, (name, score, round_reached, balls_count, play_date) in enumerate(rankings):
                y = 160 + i * 35
                
                try:
                    if self.current_font_path:
                        rank_font = pygame.font.Font(self.current_font_path, 20)
                    else:
                        rank_font = self.small_font
                except:
                    rank_font = self.small_font
                
                # 순위별 색상
                if i == 0:
                    color = (255, 215, 0)  # 금색
                elif i == 1:
                    color = (192, 192, 192)  # 은색
                elif i == 2:
                    color = (205, 127, 50)  # 동색
                else:
                    color = WHITE
                
                rank_text = rank_font.render(f"{i+1:2d}.  {name[:8]:<8}  {score:>6}  {round_reached:>3}R", True, color)
                rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH//2, y))
                self.screen.blit(rank_text, rank_rect)
                
                # 날짜 표시 (더 작은 폰트)
                try:
                    if self.current_font_path:
                        date_font = pygame.font.Font(self.current_font_path, 14)
                    else:
                        date_font = pygame.font.Font(None, 16)
                except:
                    date_font = pygame.font.Font(None, 16)
                
                date_str = play_date.split()[0] if play_date else ""  # 날짜만 표시
                date_text = date_font.render(date_str, True, GRAY)
                date_rect = date_text.get_rect(center=(SCREEN_WIDTH//2, y + 15))
                self.screen.blit(date_text, date_rect)
        else:
            # 랭킹이 없을 때
            try:
                if self.current_font_path:
                    no_rank_font = pygame.font.Font(self.current_font_path, 24)
                else:
                    no_rank_font = self.font
            except:
                no_rank_font = self.font
            
            no_rank_text = no_rank_font.render("아직 저장된 점수가 없습니다", True, LIGHT_GRAY)
            no_rank_rect = no_rank_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(no_rank_text, no_rank_rect)
        
        # 통계 정보 표시
        stats = db_manager.get_database_stats()
        if stats['total_games'] > 0:
            try:
                if self.current_font_path:
                    stats_font = pygame.font.Font(self.current_font_path, 16)
                else:
                    stats_font = pygame.font.Font(None, 18)
            except:
                stats_font = pygame.font.Font(None, 18)
            
            stats_text = stats_font.render(
                f"총 게임: {stats['total_games']}  평균 점수: {stats['average_score']}", 
                True, LIGHT_GRAY
            )
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80))
            self.screen.blit(stats_text, stats_rect)
        
        # 돌아가기 안내 (한글 지원)
        try:
            if self.current_font_path:
                back_font = pygame.font.Font(self.current_font_path, 20)
            else:
                back_font = self.small_font
        except:
            back_font = self.small_font
        back_text = back_font.render(get_text('back_to_title'), True, LIGHT_GRAY)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(back_text, back_rect)
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit() 