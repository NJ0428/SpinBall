import pygame
import math
import random
from constants import *


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
            # 더 선명한 공 색상
            pygame.draw.circle(screen, CYAN, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)


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
        
        self.reset_game()
        
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
        self.round_in_progress = False  # 현재 라운드가 진행 중인지
        self.bonus_balls_collected = 0  # 이번 라운드에서 수집한 보너스 볼 개수
        self.last_ball_x = SCREEN_WIDTH // 2  # 마지막 공이 떨어진 X 위치
        
        # 첫 번째 라운드의 블록 생성
        self.generate_blocks()
        
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
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
            elif event.type == pygame.MOUSEMOTION:
                if not self.game_over:
                    # 마우스 위치로 발사각도 계산
                    mouse_x, mouse_y = event.pos
                    if mouse_y < SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                        dx = mouse_x - self.launch_x
                        dy = (SCREEN_HEIGHT - BOTTOM_UI_HEIGHT) - mouse_y
                        if dy > 0:
                            angle = math.degrees(math.atan2(dy, dx))
                            self.launch_angle = max(MIN_LAUNCH_ANGLE, min(MAX_LAUNCH_ANGLE, angle))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.game_over and not self.round_in_progress:
                    self.start_launch()
                    
        return True
        
    def start_launch(self):
        # 라운드가 진행 중이 아닐 때만 새 라운드 시작
        if not self.round_in_progress:
            # 새 라운드 시작
            self.round_in_progress = True
            self.launching = True
            self.launch_start_time = pygame.time.get_ticks()
            self.balls_launched = 0
            
            # 첫 번째 공 즉시 발사
            angle_rad = math.radians(self.launch_angle)
            dx = BALL_SPEED * math.cos(angle_rad)
            dy = -BALL_SPEED * math.sin(angle_rad)
            
            # 공 발사 (바닥보다 조금 위에서 발사)  
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            ball = Ball(self.launch_x, launch_y, dx, dy)
            self.balls.append(ball)
            self.balls_launched += 1
        
    def update(self):
        if self.game_over:
            return
            
        current_time = pygame.time.get_ticks()
        
        # 자동 공 연속 발사 (연속 클릭하지 않아도 됨)
        if (self.launching and 
            self.balls_launched < self.ball_count and 
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
                        self.score += 1
                        
            # 보너스 볼 수집
            for bonus in self.bonus_balls:
                if ball.collect_bonus(bonus):
                    bonus.active = False
                    self.bonus_balls_collected += 1  # 라운드 종료 후 적용
                    
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
        
        # 모든 공이 바닥에 떨어졌는지 확인 (라운드 완료)
        if self.round_in_progress and self.balls_launched >= self.ball_count and len(self.balls) == 0:
            # 수집한 보너스 볼을 다음 라운드에 적용
            self.ball_count += self.bonus_balls_collected
            self.bonus_balls_collected = 0
            
            self.launching = False
            self.round_in_progress = False
            self.next_round()
            
        # 게임 오버 체크 (블록이나 보너스 볼이 바닥에 닿음)
        for block in self.blocks:
            if block.active and block.y + BLOCK_SIZE >= SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                break
                
        for bonus in self.bonus_balls:
            if bonus.active and bonus.y + bonus.radius >= SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                break
                
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
            angle_rad = math.radians(self.launch_angle)
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            end_x = self.launch_x + AIM_LINE_LENGTH * math.cos(angle_rad)
            end_y = launch_y - AIM_LINE_LENGTH * math.sin(angle_rad)
            
            # 조준선 (점선 효과)
            for i in range(0, int(AIM_LINE_LENGTH), 10):
                start_x = self.launch_x + i * math.cos(angle_rad)
                start_y = launch_y - i * math.sin(angle_rad)
                end_x_segment = start_x + 5 * math.cos(angle_rad)
                end_y_segment = start_y - 5 * math.sin(angle_rad)
                
                pygame.draw.line(self.screen, LIGHT_GRAY, 
                               (start_x, start_y), (end_x_segment, end_y_segment), 3)
            
            # 발사점 표시
            launch_y = SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - BALL_RADIUS - 2
            pygame.draw.circle(self.screen, CYAN, 
                             (self.launch_x, launch_y), 8)
            pygame.draw.circle(self.screen, WHITE, 
                             (self.launch_x, launch_y), 8, 2)
        
    def draw_ui(self):
        # 상단 UI 배경
        pygame.draw.rect(self.screen, UI_BG_COLOR, (0, 0, SCREEN_WIDTH, TOP_UI_HEIGHT))
        pygame.draw.line(self.screen, GRAY, (0, TOP_UI_HEIGHT), (SCREEN_WIDTH, TOP_UI_HEIGHT), 2)
        
        # 점수 표시
        score_text = self.small_font.render(f"현재점수: {self.score}", True, UI_TEXT_COLOR)
        high_score_text = self.small_font.render(f"최고기록: {self.high_score}", True, UI_TEXT_COLOR)
        
        self.screen.blit(high_score_text, (20, 15))
        self.screen.blit(score_text, (20, 40))
        
        # 라운드 표시
        round_text = self.small_font.render(f"라운드: {self.round_num}", True, UI_TEXT_COLOR)
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
        
    def draw(self):
        self.screen.fill(WHITE)
        
        # UI 그리기
        self.draw_ui()
        
        # 블록 그리기
        for block in self.blocks:
            block.draw(self.screen)
            
        # 보너스 볼 그리기
        for bonus in self.bonus_balls:
            bonus.draw(self.screen)
            
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
            
            game_over_text = self.large_font.render("게임 오버!", True, WHITE)
            score_text = self.font.render(f"점수: {self.score}", True, WHITE)
            restart_text = self.small_font.render("R키를 눌러 재시작", True, LIGHT_GRAY)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(score_text, score_rect)
            self.screen.blit(restart_text, restart_rect)
        
        # 조작법 (첫 라운드에만 표시)
        elif self.round_num == 1 and not self.round_in_progress:
            help_text = self.small_font.render("마우스로 조준, 클릭으로 발사", True, GRAY)
            help_rect = help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(help_text, help_rect)
            
        pygame.display.flip()
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit() 