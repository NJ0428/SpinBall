import pygame
import math
import random
from constants import *
from language import get_text, set_language, get_current_language, language_manager
from database import db_manager
from shop import Shop
import datetime
import json
import time
import os


class ReplayManager:
    def __init__(self):
        self.recording = False
        self.playing = False
        self.actions = []
        self.current_action_index = 0
        self.start_time = 0
        
    def start_recording(self):
        """리플레이 기록 시작"""
        self.recording = True
        self.actions = []
        self.start_time = time.time()
        
    def stop_recording(self):
        """리플레이 기록 중지"""
        self.recording = False
        
    def record_action(self, action_type, data, timestamp=None):
        """액션 기록"""
        if not self.recording or len(self.actions) >= MAX_REPLAY_ACTIONS:
            return
            
        if timestamp is None:
            timestamp = time.time() - self.start_time
            
        self.actions.append({
            'type': action_type,
            'data': data,
            'timestamp': timestamp
        })
    
    def save_replay(self, filename, score, round_num):
        """리플레이 파일 저장"""
        if not self.actions:
            return False
        
        # replays 폴더 생성
        if not os.path.exists('replays'):
            os.makedirs('replays')
            
        replay_data = {
            'version': '1.0',
            'score': score,
            'round': round_num,
            'duration': time.time() - self.start_time,
            'actions': self.actions,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            with open(f"replays/{filename}.json", 'w') as f:
                json.dump(replay_data, f)
            return True
        except:
            return False
    
    def load_replay(self, filename):
        """리플레이 파일 로드"""
        try:
            with open(f"replays/{filename}.json", 'r') as f:
                replay_data = json.load(f)
            self.actions = replay_data['actions']
            self.current_action_index = 0
            return replay_data
        except:
            return None
    
    def start_playback(self):
        """리플레이 재생 시작"""
        self.playing = True
        self.current_action_index = 0
        self.start_time = time.time()
    
    def stop_playback(self):
        """리플레이 재생 중지"""
        self.playing = False
        
    def get_next_action(self):
        """다음 액션 가져오기"""
        if not self.playing or self.current_action_index >= len(self.actions):
            return None
            
        current_time = time.time() - self.start_time
        action = self.actions[self.current_action_index]
        
        if current_time >= action['timestamp']:
            self.current_action_index += 1
            return action
        return None


class StatisticsManager:
    def __init__(self):
        self.stats = {
            'total_play_time': 0,
            'games_played': 0,
            'total_score': 0,
            'highest_score': 0,
            'highest_round': 0,
            'blocks_destroyed': {
                'normal': 0,
                'bomb': 0,
                'shield': 0,
                'ghost': 0
            },
            'total_blocks_destroyed': 0,
            'combos_achieved': 0,
            'highest_combo': 0,
            'powerups_used': 0,
            'bonus_balls_collected': 0
        }
        self.session_start_time = time.time()
        self.load_stats()
    
    def load_stats(self):
        """통계 파일 로드"""
        try:
            with open('stats.json', 'r') as f:
                saved_stats = json.load(f)
                self.stats.update(saved_stats)
        except:
            pass  # 파일이 없으면 기본값 사용
    
    def save_stats(self):
        """통계 파일 저장"""
        try:
            with open('stats.json', 'w') as f:
                json.dump(self.stats, f)
        except:
            pass
    
    def update_game_end(self, score, round_num, blocks_destroyed_by_type, combos, highest_combo, powerups_used, bonus_collected):
        """게임 종료 시 통계 업데이트"""
        self.stats['games_played'] += 1
        self.stats['total_score'] += score
        self.stats['highest_score'] = max(self.stats['highest_score'], score)
        self.stats['highest_round'] = max(self.stats['highest_round'], round_num)
        
        # 블록 파괴 통계
        for block_type, count in blocks_destroyed_by_type.items():
            if block_type in self.stats['blocks_destroyed']:
                self.stats['blocks_destroyed'][block_type] += count
                self.stats['total_blocks_destroyed'] += count
        
        # 콤보 통계
        self.stats['combos_achieved'] += combos
        self.stats['highest_combo'] = max(self.stats['highest_combo'], highest_combo)
        
        # 기타 통계
        self.stats['powerups_used'] += powerups_used
        self.stats['bonus_balls_collected'] += bonus_collected
        
        self.save_stats()
    
    def update_play_time(self):
        """플레이 시간 업데이트"""
        current_time = time.time()
        self.stats['total_play_time'] += current_time - self.session_start_time
        self.session_start_time = current_time
    
    def get_average_score(self):
        """평균 점수 계산"""
        if self.stats['games_played'] == 0:
            return 0
        return self.stats['total_score'] // self.stats['games_played']
    
    def get_play_time_formatted(self):
        """플레이 시간을 시:분:초 형식으로 반환"""
        total_seconds = int(self.stats['total_play_time'])
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class AchievementManager:
    def __init__(self):
        self.achievements = {
            'block_destroyer': {
                'id': 'block_destroyer',
                'name': '💥 Block Destroyer',
                'description': 'Destroy 10 blocks in a single shot',
                'unlocked': False,
                'progress': 0,
                'target': 10,
                'icon': '💥'
            },
            'centurion': {
                'id': 'centurion',
                'name': '💯 Centurion',
                'description': 'Reach round 100',
                'unlocked': False,
                'progress': 0,
                'target': 100,
                'icon': '💯'
            },
            'perfect_angle_45': {
                'id': 'perfect_angle_45',
                'name': '📐 Perfect 45°',
                'description': 'Complete a round using only 45° angles',
                'unlocked': False,
                'progress': 0,
                'target': 1,
                'icon': '📐'
            },
            'perfect_angle_90': {
                'id': 'perfect_angle_90',
                'name': '⬆️ Straight Shooter',
                'description': 'Complete a round using only 90° angles',
                'unlocked': False,
                'progress': 0,
                'target': 1,
                'icon': '⬆️'
            },
            'perfect_angle_135': {
                'id': 'perfect_angle_135',
                'name': '↗️ Perfect 135°',
                'description': 'Complete a round using only 135° angles',
                'unlocked': False,
                'progress': 0,
                'target': 1,
                'icon': '↗️'
            },
            'combo_master': {
                'id': 'combo_master',
                'name': '🔥 Combo Master',
                'description': 'Achieve a 20x combo',
                'unlocked': False,
                'progress': 0,
                'target': 20,
                'icon': '🔥'
            },
            'speed_demon': {
                'id': 'speed_demon',
                'name': '⚡ Speed Demon',
                'description': 'Survive 50 rounds in Survival mode',
                'unlocked': False,
                'progress': 0,
                'target': 50,
                'icon': '⚡'
            },
            'puzzle_solver': {
                'id': 'puzzle_solver',
                'name': '🧩 Puzzle Solver',
                'description': 'Complete 10 puzzle levels',
                'unlocked': False,
                'progress': 0,
                'target': 10,
                'icon': '🧩'
            },
            'time_master': {
                'id': 'time_master',
                'name': '⏰ Time Master',
                'description': 'Score 5000+ in Time Attack mode',
                'unlocked': False,
                'progress': 0,
                'target': 5000,
                'icon': '⏰'
            },
            'special_destroyer': {
                'id': 'special_destroyer',
                'name': '🎯 Special Destroyer',
                'description': 'Destroy 100 special blocks',
                'unlocked': False,
                'progress': 0,
                'target': 100,
                'icon': '🎯'
            }
        }
        self.notifications = []  # 업적 알림 큐
        self.load_achievements()
        
        # 각도 추적 변수들
        self.current_round_angles = []
        self.round_started = False
    
    def load_achievements(self):
        """업적 파일 로드"""
        try:
            with open('achievements.json', 'r') as f:
                saved_achievements = json.load(f)
                for achievement_id, data in saved_achievements.items():
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id].update(data)
        except:
            pass  # 파일이 없으면 기본값 사용
    
    def save_achievements(self):
        """업적 파일 저장"""
        try:
            with open('achievements.json', 'w') as f:
                json.dump(self.achievements, f)
        except:
            pass
    
    def check_achievement(self, achievement_id, value=1):
        """업적 진행도 체크 및 업데이트"""
        if achievement_id not in self.achievements:
            return False
            
        achievement = self.achievements[achievement_id]
        if achievement['unlocked']:
            return False
        
        # 진행도 업데이트
        if achievement_id in ['combo_master', 'centurion', 'time_master']:
            # 최대값 기록 방식
            achievement['progress'] = max(achievement['progress'], value)
        else:
            # 누적 방식
            achievement['progress'] += value
        
        # 업적 달성 체크
        if achievement['progress'] >= achievement['target']:
            achievement['unlocked'] = True
            self.add_notification(achievement)
            self.save_achievements()
            return True
        
        self.save_achievements()
        return False
    
    def add_notification(self, achievement):
        """업적 달성 알림 추가"""
        notification = {
            'achievement': achievement,
            'timestamp': pygame.time.get_ticks(),
            'duration': ACHIEVEMENT_NOTIFICATION_DURATION
        }
        self.notifications.append(notification)
    
    def update_notifications(self):
        """알림 업데이트 (만료된 알림 제거)"""
        current_time = pygame.time.get_ticks()
        self.notifications = [
            notif for notif in self.notifications 
            if current_time - notif['timestamp'] < notif['duration']
        ]
    
    def track_angle(self, angle):
        """발사 각도 추적"""
        if self.round_started:
            self.current_round_angles.append(angle)
    
    def start_round(self):
        """라운드 시작 시 각도 추적 초기화"""
        self.round_started = True
        self.current_round_angles = []
    
    def end_round(self):
        """라운드 종료 시 완벽한 각도 업적 체크"""
        if not self.round_started or not self.current_round_angles:
            return
        
        # 각 완벽한 각도에 대해 체크
        for perfect_angle in PERFECT_ANGLES:
            achievement_id = f'perfect_angle_{perfect_angle}'
            if achievement_id in self.achievements:
                # 모든 발사가 해당 각도 범위 내인지 체크
                all_perfect = all(
                    abs(angle - perfect_angle) <= PERFECT_ANGLE_TOLERANCE 
                    for angle in self.current_round_angles
                )
                if all_perfect and len(self.current_round_angles) > 0:
                    self.check_achievement(achievement_id, 1)
        
        self.round_started = False
        self.current_round_angles = []
    
    def get_unlocked_count(self):
        """달성한 업적 수 반환"""
        return sum(1 for achievement in self.achievements.values() if achievement['unlocked'])
    
    def get_total_count(self):
        """전체 업적 수 반환"""
        return len(self.achievements)
    
    def get_completion_percentage(self):
        """업적 달성률 반환"""
        if self.get_total_count() == 0:
            return 0
        return (self.get_unlocked_count() / self.get_total_count()) * 100


class GameModeManager:
    def __init__(self):
        self.current_mode = GAME_MODE_CLASSIC
        self.mode_data = {}
        
    def set_mode(self, mode):
        """게임 모드 설정"""
        self.current_mode = mode
        self.mode_data = {}
        
        if mode == GAME_MODE_TIME_ATTACK:
            self.mode_data = {
                'time_left': TIME_ATTACK_DURATION,
                'start_time': time.time()
            }
        elif mode == GAME_MODE_PUZZLE:
            self.mode_data = {
                'balls_left': PUZZLE_MODE_BALLS,
                'total_balls': PUZZLE_MODE_BALLS
            }
        elif mode == GAME_MODE_SURVIVAL:
            self.mode_data = {
                'speed_multiplier': 1.0,
                'rounds_survived': 0
            }
    
    def update(self, game):
        """모드별 업데이트 로직"""
        if self.current_mode == GAME_MODE_TIME_ATTACK:
            # 시간 제한 모드: 시간 감소
            current_time = time.time()
            elapsed = current_time - self.mode_data['start_time']
            self.mode_data['time_left'] = max(0, TIME_ATTACK_DURATION - elapsed)
            
            if self.mode_data['time_left'] <= 0:
                game.game_over = True
                
        elif self.current_mode == GAME_MODE_PUZZLE:
            # 퍼즐 모드: 공 개수 체크
            # 라운드가 끝날 때마다 남은 공 개수 업데이트
            if hasattr(game, 'round_in_progress') and not game.round_in_progress:
                # 현재 라운드에서 사용한 공 개수만큼 차감
                if 'balls_used_this_round' not in self.mode_data:
                    self.mode_data['balls_used_this_round'] = 0
                
                # 라운드 완료 시 공 개수 차감
                if game.balls_launched > self.mode_data['balls_used_this_round']:
                    used_balls = game.balls_launched - self.mode_data['balls_used_this_round']
                    self.mode_data['balls_left'] = max(0, self.mode_data['balls_left'] - used_balls)
                    self.mode_data['balls_used_this_round'] = game.balls_launched
                
                # 공이 부족하고 블록이 남아있으면 게임 오버
                if self.mode_data['balls_left'] <= 0 and len([b for b in game.blocks if b.active]) > 0:
                    game.game_over = True
                    
        elif self.current_mode == GAME_MODE_SURVIVAL:
            # 생존 모드: 속도 증가
            self.mode_data['rounds_survived'] = game.round_num
            self.mode_data['speed_multiplier'] = 1.0 + (game.round_num - 1) * SURVIVAL_SPEED_INCREASE
    
    def get_mode_name(self):
        """모드 이름 반환"""
        mode_names = {
            GAME_MODE_CLASSIC: "Classic",
            GAME_MODE_TIME_ATTACK: "Time Attack",
            GAME_MODE_SURVIVAL: "Survival",
            GAME_MODE_PUZZLE: "Puzzle"
        }
        return mode_names.get(self.current_mode, "Unknown")
    
    def get_mode_description(self):
        """모드 설명 반환"""
        descriptions = {
            GAME_MODE_CLASSIC: "Standard game mode with unlimited time",
            GAME_MODE_TIME_ATTACK: f"Clear as many blocks as possible in {TIME_ATTACK_DURATION} seconds",
            GAME_MODE_SURVIVAL: "Survive as long as possible with increasing difficulty",
            GAME_MODE_PUZZLE: f"Clear all blocks with only {PUZZLE_MODE_BALLS} balls"
        }
        return descriptions.get(self.current_mode, "")
    
    def is_game_complete(self, game):
        """게임 완료 조건 체크"""
        if self.current_mode == GAME_MODE_PUZZLE:
            # 퍼즐 모드: 모든 블록 파괴 시 성공
            return len([b for b in game.blocks if b.active]) == 0
        return False


class ThemeManager:
    def __init__(self):
        self.current_theme = THEME_DARK
        self.manual_theme = None  # 수동으로 설정된 테마
        
    def get_seasonal_theme(self):
        """현재 날짜에 따른 계절 테마 반환"""
        now = datetime.datetime.now()
        month = now.month
        day = now.day
        
        # 크리스마스 시즌 (12월 1일 ~ 1월 7일)
        if month == 12 or (month == 1 and day <= 7):
            return THEME_CHRISTMAS
        # 할로윈 시즌 (10월)
        elif month == 10:
            return THEME_HALLOWEEN
        # 봄 (3월 ~ 5월)
        elif 3 <= month <= 5:
            return THEME_SPRING
        # 여름 (6월 ~ 8월)
        elif 6 <= month <= 8:
            return THEME_SUMMER
        # 기본 다크 테마
        else:
            return THEME_DARK
    
    def get_round_theme(self, round_num):
        """라운드에 따른 테마 반환"""
        # 수동 테마가 설정되어 있으면 우선 적용
        if self.manual_theme:
            return self.manual_theme
            
        # 라운드별 테마 변화
        for threshold in sorted(ROUND_THEME_CHANGES.keys(), reverse=True):
            if round_num >= threshold:
                return ROUND_THEME_CHANGES[threshold]
        
        # 기본적으로 계절 테마 적용
        return self.get_seasonal_theme()
    
    def set_manual_theme(self, theme):
        """수동으로 테마 설정"""
        self.manual_theme = theme
    
    def clear_manual_theme(self):
        """수동 테마 설정 해제"""
        self.manual_theme = None
    
    def get_theme_colors(self, theme):
        """테마에 따른 색상 팔레트 반환"""
        if theme == THEME_LIGHT:
            return {
                'background': LIGHT_BLACK,
                'surface': LIGHT_SURFACE,
                'darker_surface': LIGHT_DARKER_SURFACE,
                'text': LIGHT_TEXT,
                'text_secondary': LIGHT_TEXT_SECONDARY,
                'accent': (0, 123, 255),
                'ball_color': (0, 123, 255),
                'ball_trail': (0, 123, 255)
            }
        elif theme == THEME_CHRISTMAS:
            return {
                'background': CHRISTMAS_DARK,
                'surface': (40, 40, 50),
                'darker_surface': (30, 30, 40),
                'text': CHRISTMAS_WHITE,
                'text_secondary': (200, 200, 200),
                'accent': CHRISTMAS_RED,
                'ball_color': CHRISTMAS_GOLD,
                'ball_trail': CHRISTMAS_GOLD
            }
        elif theme == THEME_HALLOWEEN:
            return {
                'background': HALLOWEEN_BLACK,
                'surface': (40, 20, 40),
                'darker_surface': (30, 15, 30),
                'text': HALLOWEEN_ORANGE,
                'text_secondary': HALLOWEEN_GRAY,
                'accent': HALLOWEEN_PURPLE,
                'ball_color': HALLOWEEN_ORANGE,
                'ball_trail': HALLOWEEN_ORANGE
            }
        elif theme == THEME_SPRING:
            return {
                'background': SPRING_WHITE,
                'surface': (240, 248, 240),
                'darker_surface': (230, 240, 230),
                'text': (60, 120, 60),
                'text_secondary': (100, 150, 100),
                'accent': SPRING_PINK,
                'ball_color': SPRING_GREEN,
                'ball_trail': SPRING_GREEN
            }
        elif theme == THEME_SUMMER:
            return {
                'background': (240, 248, 255),
                'surface': (230, 240, 250),
                'darker_surface': (220, 230, 240),
                'text': (30, 60, 120),
                'text_secondary': (70, 100, 150),
                'accent': SUMMER_BLUE,
                'ball_color': SUMMER_CYAN,
                'ball_trail': SUMMER_CYAN
            }
        else:  # THEME_DARK (기본)
            return {
                'background': BLACK,
                'surface': DARK_SURFACE,
                'darker_surface': DARKER_SURFACE,
                'text': WHITE,
                'text_secondary': TEXT_SECONDARY,
                'accent': NEON_CYAN,
                'ball_color': NEON_CYAN,
                'ball_trail': NEON_CYAN
            }


class Particle:
    def __init__(self, x, y, dx, dy, color, life, size=2):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.active = True
        
    def update(self):
        if not self.active:
            return
            
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        
        # 중력 효과 (폭발 파티클용)
        self.dy += 0.2
        
        # 공기 저항
        self.dx *= 0.98
        self.dy *= 0.98
        
        if self.life <= 0:
            self.active = False
    
    def draw(self, screen):
        if not self.active:
            return
            
        # 생명력에 따른 알파값 계산
        alpha = int(255 * (self.life / self.max_life))
        if alpha <= 0:
            return
            
        # 파티클 크기도 생명력에 따라 변화
        current_size = max(1, int(self.size * (self.life / self.max_life)))
        
        # 반투명 파티클 그리기
        particle_surface = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        particle_color = (*self.color, alpha)
        pygame.draw.circle(particle_surface, particle_color, (current_size, current_size), current_size)
        screen.blit(particle_surface, (int(self.x - current_size), int(self.y - current_size)))


class TrailPoint:
    def __init__(self, x, y, alpha=255):
        self.x = x
        self.y = y
        self.alpha = alpha
        self.active = True
    
    def update(self):
        self.alpha -= TRAIL_FADE_SPEED
        if self.alpha <= 0:
            self.active = False
    
    def draw(self, screen, color, radius):
        if not self.active or self.alpha <= 0:
            return
            
        trail_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        trail_color = (*color, max(0, self.alpha))
        pygame.draw.circle(trail_surface, trail_color, (radius, radius), radius)
        screen.blit(trail_surface, (int(self.x - radius), int(self.y - radius)))


class Ball:
    def __init__(self, x, y, dx, dy, game=None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = BALL_RADIUS
        self.active = True
        self.game = game  # Game 인스턴스 참조
        self.trail_points = []  # 궤적 포인트들
        
    def move(self):
        if not self.active:
            return
        
        # 현재 위치를 트레일에 추가
        self.trail_points.append(TrailPoint(self.x, self.y))
        
        # 트레일 길이 제한 (메모리 효율성)
        if len(self.trail_points) > TRAIL_LENGTH:
            self.trail_points = self.trail_points[-TRAIL_LENGTH:]
        
        # 스피드볼 효과 적용
        speed_multiplier = 2 if self.game and self.game.active_powerups.get(2, False) else 1
        
        # 생존 모드 속도 증가 적용
        if self.game and self.game.mode_manager.current_mode == GAME_MODE_SURVIVAL:
            speed_multiplier *= self.game.mode_manager.mode_data.get('speed_multiplier', 1.0)
        
        self.x += self.dx * speed_multiplier
        self.y += self.dy * speed_multiplier
        
        # 트레일 포인트들 업데이트
        self.trail_points = [point for point in self.trail_points if point.active]
        for point in self.trail_points:
            point.update()
        
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
            # 테마에 따른 공 색상 가져오기
            theme_colors = self.game.theme_manager.get_theme_colors(self.game.current_theme) if self.game else None
            ball_color = theme_colors['ball_color'] if theme_colors else NEON_CYAN
            trail_color = theme_colors['ball_trail'] if theme_colors else NEON_CYAN
            
            # 트레일 그리기 (공보다 먼저 그려서 뒤에 표시)
            for i, point in enumerate(self.trail_points):
                trail_radius = max(1, int(self.radius * 0.3 * (i + 1) / len(self.trail_points)))
                point.draw(screen, trail_color, trail_radius)
            
            # 네온 글로우 효과
            for i in range(3, 0, -1):
                glow_color = (*ball_color, 60 // i)
                glow_surface = pygame.Surface((self.radius * 2 + i * 4, self.radius * 2 + i * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, 
                                 (self.radius + i * 2, self.radius + i * 2), self.radius + i)
                screen.blit(glow_surface, (int(self.x - self.radius - i * 2), int(self.y - self.radius - i * 2)))
            
            # 메인 공 (그라데이션 효과)
            pygame.draw.circle(screen, ball_color, (int(self.x), int(self.y)), self.radius)
            
            # 하이라이트 (3D 효과)
            highlight_color = theme_colors['text'] if theme_colors else WHITE
            highlight_pos = (int(self.x - self.radius//3), int(self.y - self.radius//3))
            pygame.draw.circle(screen, highlight_color, highlight_pos, self.radius//3)
            
            # 외곽선
            pygame.draw.circle(screen, highlight_color, (int(self.x), int(self.y)), self.radius, 2)


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
            
            # 블록 파괴 시 폭발 파티클 생성
            if game:
                self.create_explosion_particles(game)
            
            # 폭탄 블록: 주변 블록도 파괴
            if self.block_type == BLOCK_TYPE_BOMB and game:
                self.explode_nearby_blocks(game)
            
            return True  # 블록이 파괴됨
        return False
    
    def create_explosion_particles(self, game):
        """블록 파괴 시 폭발 파티클 생성"""
        center_x = self.x + BLOCK_SIZE // 2
        center_y = self.y + BLOCK_SIZE // 2
        block_color = self.get_color()
        
        # 블록 타입별 통계 업데이트
        if self.block_type == BLOCK_TYPE_BOMB:
            game.blocks_destroyed_by_type['bomb'] += 1
        elif self.block_type == BLOCK_TYPE_SHIELD:
            game.blocks_destroyed_by_type['shield'] += 1
        elif self.block_type == BLOCK_TYPE_GHOST:
            game.blocks_destroyed_by_type['ghost'] += 1
        else:
            game.blocks_destroyed_by_type['normal'] += 1
        
        # 업적: 블록 파괴 카운트
        game.blocks_destroyed_this_shot += 1
        
        # 업적: 특수 블록 파괴
        if self.block_type != BLOCK_TYPE_NORMAL:
            game.achievement_manager.check_achievement('special_destroyer', 1)
        
        for _ in range(EXPLOSION_PARTICLE_COUNT):
            # 랜덤한 방향과 속도
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, EXPLOSION_PARTICLE_SPEED)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            # 파티클 크기와 수명 랜덤화
            size = random.randint(2, 4)
            life = random.randint(EXPLOSION_PARTICLE_LIFE // 2, EXPLOSION_PARTICLE_LIFE)
            
            particle = Particle(center_x, center_y, dx, dy, block_color, life, size)
            game.particles.append(particle)
    
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
                    # 폭발로 파괴된 블록도 콤보 시스템과 함께 점수 추가
                    block_color = block.get_color()
                    game.add_score(block.get_score_value(), block_color)
    
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
        self.collected = False  # 수집 상태 플래그
    
    def create_sparkle_particles(self, game):
        """보너스 볼 수집 시 반짝임 파티클 생성"""
        for _ in range(SPARKLE_PARTICLE_COUNT):
            # 랜덤한 방향과 속도
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, SPARKLE_PARTICLE_SPEED)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - 2  # 위쪽으로 약간 편향
            
            # 반짝임 색상 (노란색, 흰색, 초록색 중 랜덤)
            colors = [NEON_YELLOW, WHITE, NEON_GREEN]
            color = random.choice(colors)
            
            # 파티클 크기와 수명
            size = random.randint(1, 3)
            life = random.randint(SPARKLE_PARTICLE_LIFE // 2, SPARKLE_PARTICLE_LIFE)
            
            particle = Particle(self.x, self.y, dx, dy, color, life, size)
            game.particles.append(particle)
        
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
            "language": "ko",
            "theme": "auto"  # auto, dark, light, christmas, halloween, spring, summer
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
        
        # 게임 상태 관리
        self.game_state = GAME_STATE_TITLE
        self.selected_menu = 0  # 선택된 메뉴 항목
        self.settings_menu_selected = 0  # 설정 메뉴에서 선택된 항목
        
        # 콤보 시스템
        self.combo_count = 0
        self.combo_multiplier = 1.0
        self.last_block_color = None
        self.last_combo_time = 0
        self.combo_display_time = 0
        self.combo_score_gained = 0
        
        # 파티클 시스템
        self.particles = []
        
        # 테마 시스템
        self.theme_manager = ThemeManager()
        self.current_theme = self.theme_manager.get_seasonal_theme()
        
        # 일시정지 시스템
        self.paused = False
        self.pause_menu_selected = 0
        
        # 리플레이 시스템
        self.replay_manager = ReplayManager()
        
        # 통계 시스템
        self.stats_manager = StatisticsManager()
        self.blocks_destroyed_by_type = {'normal': 0, 'bomb': 0, 'shield': 0, 'ghost': 0}
        self.combos_this_game = 0
        self.highest_combo_this_game = 0
        self.powerups_used_this_game = 0
        
        # 게임 모드 시스템
        self.mode_manager = GameModeManager()
        self.mode_select_index = 0
        
        # 업적 시스템
        self.achievement_manager = AchievementManager()
        self.blocks_destroyed_this_shot = 0
        
        self.reset_game()
        
        self.shop = Shop(self.font, self.score)
        self.active_powerups = {1: False, 2: False, 3: False}  # 파워볼, 스피드볼, 매그넘볼
        
    def safe_render_text(self, font, text, color, fallback_font=None):
        """안전한 텍스트 렌더링 (한글 깨짐 방지)"""
        try:
            # 텍스트가 None이거나 빈 문자열인 경우 처리
            if text is None:
                text = ""
            text = str(text)
            return font.render(text, True, color)
        except Exception as e:
            # 폰트 렌더링 실패 시 대체 폰트 사용
            if fallback_font:
                try:
                    return fallback_font.render(str(text), True, color)
                except:
                    pass
            # 최후의 수단: 기본 폰트
            try:
                default_font = pygame.font.Font(None, 24)
                return default_font.render(str(text), True, color)
            except:
                # 텍스트를 ASCII로 변환
                try:
                    safe_text = str(text).encode('ascii', 'ignore').decode('ascii')
                    default_font = pygame.font.Font(None, 24)
                    return default_font.render(safe_text if safe_text else "Text", True, color)
                except:
                    # 최종 대안: 빈 서피스 반환
                    surface = pygame.Surface((50, 20), pygame.SRCALPHA)
                    surface.fill((0, 0, 0, 0))
                    return surface
        
    def get_menu_items(self):
        """현재 언어에 따른 메뉴 항목들 반환"""
        return [
            get_text('menu_start'),
            "Challenge Modes",
            get_text('menu_settings'), 
            get_text('menu_ranking'),
            "Statistics",
            "Achievements",
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
        elif self.settings_menu_selected == 4:  # 테마
            themes = ["auto", "dark", "light", "christmas", "halloween", "spring", "summer"]
            current_idx = 0
            if self.settings["theme"] in themes:
                current_idx = themes.index(self.settings["theme"])
            if increase:
                current_idx = (current_idx + 1) % len(themes)
            else:
                current_idx = (current_idx - 1) % len(themes)
            self.settings["theme"] = themes[current_idx]
            
            # 테마 적용
            if self.settings["theme"] == "auto":
                self.theme_manager.clear_manual_theme()
                self.current_theme = self.theme_manager.get_round_theme(self.round_num)
            else:
                theme_map = {
                    "dark": THEME_DARK,
                    "light": THEME_LIGHT,
                    "christmas": THEME_CHRISTMAS,
                    "halloween": THEME_HALLOWEEN,
                    "spring": THEME_SPRING,
                    "summer": THEME_SUMMER
                }
                self.theme_manager.set_manual_theme(theme_map[self.settings["theme"]])
                self.current_theme = theme_map[self.settings["theme"]]
        
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
        
        # 콤보 시스템 초기화
        self.combo_count = 0
        self.combo_multiplier = 1.0
        self.last_block_color = None
        self.last_combo_time = 0
        self.combo_display_time = 0
        self.combo_score_gained = 0
        
        # 파티클 시스템 초기화
        self.particles = []
        
        # 테마 초기화
        self.current_theme = self.theme_manager.get_seasonal_theme()
        
        # 통계 초기화
        self.blocks_destroyed_by_type = {'normal': 0, 'bomb': 0, 'shield': 0, 'ghost': 0}
        self.combos_this_game = 0
        self.highest_combo_this_game = 0
        self.powerups_used_this_game = 0
        
        # 리플레이 기록 시작
        if not self.replay_manager.playing:
            self.replay_manager.start_recording()
        
        # 업적 시스템 초기화
        self.blocks_destroyed_this_shot = 0
        
        # 상점 초기화
        if hasattr(self, 'shop'):
            self.shop.open = False
            self.shop.owned_items = []
            self.shop.player_score = self.score
        
        self.generate_blocks()
    
    def add_score(self, points, block_color=None):
        """점수 추가 (콤보 시스템 포함)"""
        current_time = pygame.time.get_ticks()
        
        # 콤보 시스템 처리
        if block_color:
            # 같은 색깔 블록이고 시간 제한 내인 경우
            if (self.last_block_color == block_color and 
                current_time - self.last_combo_time <= COMBO_TIME_WINDOW):
                self.combo_count += 1
            else:
                # 새로운 콤보 시작 또는 콤보 끊김
                if self.last_block_color == block_color:
                    self.combo_count = 2  # 같은 색깔 2개부터 콤보 시작
                else:
                    self.combo_count = 1  # 다른 색깔이면 콤보 리셋
            
            # 콤보 배율 계산
            if self.combo_count >= MIN_COMBO_COUNT:
                self.combo_multiplier = min(
                    COMBO_MULTIPLIER_BASE + (self.combo_count - MIN_COMBO_COUNT) * COMBO_MULTIPLIER_INCREMENT,
                    MAX_COMBO_MULTIPLIER
                )
                # 콤보 통계 업데이트
                if self.combo_count > self.highest_combo_this_game:
                    self.highest_combo_this_game = self.combo_count
                if self.combo_count == MIN_COMBO_COUNT:
                    self.combos_this_game += 1
                
                # 업적: 콤보 마스터
                self.achievement_manager.check_achievement('combo_master', self.combo_count)
            else:
                self.combo_multiplier = 1.0
            
            # 콤보 정보 업데이트
            self.last_block_color = block_color
            self.last_combo_time = current_time
            self.combo_display_time = current_time + 2000  # 2초간 콤보 표시
        
        # 콤보 적용된 점수 계산
        final_points = int(points * self.combo_multiplier)
        self.combo_score_gained = final_points - points  # 콤보로 얻은 추가 점수
        
        self.score += final_points
        
        # 상점 점수 동기화
        if hasattr(self, 'shop'):
            self.shop.update_score(self.score)
    
    def save_game_score(self):
        """게임 점수를 데이터베이스에 저장"""
        if self.player_name.strip() and not self.score_saved:
            try:
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
            except Exception as e:
                print(f"점수 저장 중 오류 발생: {e}")
                return False
        return False
    
    def get_rankings(self, limit=10):
        """랭킹 조회"""
        try:
            return db_manager.get_top_scores(limit)
        except Exception as e:
            print(f"랭킹 조회 중 오류 발생: {e}")
            return []
    
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
                    if event.key == pygame.K_ESCAPE and not self.game_over:
                        # 일시정지 토글
                        if self.paused:
                            self.paused = False
                        else:
                            self.paused = True
                            self.pause_menu_selected = 0
                    elif self.game_over and not self.name_entered and not self.score_saved:
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
                        # 게임 종료 시 통계 업데이트
                        self.stats_manager.update_game_end(
                            self.score, self.round_num, self.blocks_destroyed_by_type,
                            self.combos_this_game, self.highest_combo_this_game,
                            self.powerups_used_this_game, self.bonus_balls_collected
                        )
                        
                        # 모드별 업적 체크
                        if self.mode_manager.current_mode == GAME_MODE_TIME_ATTACK:
                            self.achievement_manager.check_achievement('time_master', self.score)
                        elif self.mode_manager.current_mode == GAME_MODE_PUZZLE and self.mode_manager.is_game_complete(self):
                            self.achievement_manager.check_achievement('puzzle_solver', 1)
                        
                        # 높은 점수 시 리플레이 저장
                        if self.score >= REPLAY_SAVE_THRESHOLD:
                            self.replay_manager.save_replay(f"replay_{int(time.time())}", self.score, self.round_num)
                        self.reset_game()
                    elif self.paused:
                        # 일시정지 메뉴 처리
                        if event.key == pygame.K_UP:
                            self.pause_menu_selected = (self.pause_menu_selected - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            self.pause_menu_selected = (self.pause_menu_selected + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            if self.pause_menu_selected == 0:  # 계속하기
                                self.paused = False
                            elif self.pause_menu_selected == 1:  # 설정
                                self.game_state = GAME_STATE_SETTINGS
                                self.paused = False
                            elif self.pause_menu_selected == 2:  # 메인 메뉴
                                self.game_state = GAME_STATE_TITLE
                                self.paused = False
                elif self.game_state == GAME_STATE_SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
                    elif event.key == pygame.K_UP:
                        self.settings_menu_selected = (self.settings_menu_selected - 1) % 5
                    elif event.key == pygame.K_DOWN:
                        self.settings_menu_selected = (self.settings_menu_selected + 1) % 5
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.change_setting(event.key == pygame.K_RIGHT)
                elif self.game_state == GAME_STATE_RANKING:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
                elif self.game_state == GAME_STATE_STATISTICS:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
                elif self.game_state == GAME_STATE_MODE_SELECT:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = GAME_STATE_TITLE
                    elif event.key == pygame.K_UP:
                        self.mode_select_index = (self.mode_select_index - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        self.mode_select_index = (self.mode_select_index + 1) % 4
                    elif event.key == pygame.K_RETURN:
                        self.mode_manager.set_mode(self.mode_select_index)
                        self.game_state = GAME_STATE_GAME
                        self.reset_game()
                elif self.game_state == GAME_STATE_ACHIEVEMENTS:
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
                            if self.selected_menu == 0:  # 게임시작 (클래식 모드)
                                self.mode_manager.set_mode(GAME_MODE_CLASSIC)
                                self.game_state = GAME_STATE_GAME
                                self.reset_game()
                            elif self.selected_menu == 1:  # 도전 모드
                                self.game_state = GAME_STATE_MODE_SELECT
                            elif self.selected_menu == 2:  # 게임 설정
                                self.game_state = GAME_STATE_SETTINGS
                            elif self.selected_menu == 3:  # 랭킹
                                self.game_state = GAME_STATE_RANKING
                            elif self.selected_menu == 4:  # 통계
                                self.game_state = GAME_STATE_STATISTICS
                            elif self.selected_menu == 5:  # 업적
                                self.game_state = GAME_STATE_ACHIEVEMENTS
                            elif self.selected_menu == 6:  # 게임 종료
                                return False
                            break
                elif self.game_state == GAME_STATE_GAME and not self.game_over and not self.round_in_progress:
                    self.start_launch()
                    
        # 상점이 열려있을 때는 상점 이벤트만 처리
        if self.shop.open:
            shop_events = pygame.event.get()
            for shop_event in shop_events:
                if shop_event.type == pygame.MOUSEBUTTONDOWN:
                    pos = shop_event.pos
                    # 아이템 구매
                    for item in self.shop.items:
                        if 'btn_rect' in item and item['btn_rect'].collidepoint(pos):
                            if self.shop.buy(item):
                                # 게임의 점수도 업데이트
                                self.score = self.shop.player_score
                    # 닫기 버튼
                    if hasattr(self.shop, 'close_rect') and self.shop.close_rect.collidepoint(pos):
                        self.shop.open = False
                elif shop_event.type == pygame.KEYDOWN:
                    if shop_event.key == pygame.K_ESCAPE:
                        self.shop.open = False
            return True
            
        return True
        
    def handle_title_input(self, key):
        menu_items = self.get_menu_items()
        if key == pygame.K_UP:
            self.selected_menu = (self.selected_menu - 1) % len(menu_items)
        elif key == pygame.K_DOWN:
            self.selected_menu = (self.selected_menu + 1) % len(menu_items)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.selected_menu == 0:  # 게임시작 (클래식 모드)
                self.mode_manager.set_mode(GAME_MODE_CLASSIC)
                self.game_state = GAME_STATE_GAME
                self.reset_game()
            elif self.selected_menu == 1:  # 도전 모드
                self.game_state = GAME_STATE_MODE_SELECT
            elif self.selected_menu == 2:  # 게임 설정
                self.game_state = GAME_STATE_SETTINGS
            elif self.selected_menu == 3:  # 랭킹
                self.game_state = GAME_STATE_RANKING
            elif self.selected_menu == 4:  # 통계
                self.game_state = GAME_STATE_STATISTICS
            elif self.selected_menu == 5:  # 업적
                self.game_state = GAME_STATE_ACHIEVEMENTS
            elif self.selected_menu == 6:  # 게임 종료
                return False
        
    def start_launch(self):
        # 라운드가 진행 중이 아닐 때만 새 라운드 시작
        if not self.round_in_progress:
            # 퍼즐 모드에서 공이 부족한 경우 발사 불가
            if (self.mode_manager.current_mode == GAME_MODE_PUZZLE and 
                self.mode_manager.mode_data.get('balls_left', 0) <= 0):
                return
                
            # 새 라운드 시작
            self.round_in_progress = True
            self.launching = True
            self.launch_start_time = pygame.time.get_ticks()
            self.balls_launched = 0
            self.blocks_destroyed_this_shot = 0
            
            # 업적: 각도 추적 시작
            if self.balls_launched == 0:  # 첫 번째 공 발사 시에만
                self.achievement_manager.start_round()
                self.achievement_manager.track_angle(self.launch_angle)
            
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
            
        if self.game_over or self.paused:
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
                            # 블록이 파괴되면 콤보 시스템과 함께 점수 추가
                            block_color = block.get_color()
                            self.add_score(block.get_score_value(), block_color)
                    else:
                        # 투명 블록이 파괴된 경우 점수 추가 (bounce_block에서 이미 hit 처리됨)
                        if not block.active:
                            block_color = block.get_color()
                            self.add_score(block.get_score_value(), block_color)
                        
            # 보너스 볼 수집
            for bonus in self.bonus_balls:
                if ball.collect_bonus(bonus):
                    if not bonus.collected:  # 중복 수집 방지
                        bonus.collected = True
                        bonus.create_sparkle_particles(self)  # 반짝임 효과 생성
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
        if self.round_in_progress and self.balls_launched >= self.ball_count and len(self.balls) == 0 and not self.game_over:
            # 수집한 보너스 볼을 다음 라운드에 적용
            self.ball_count += self.bonus_balls_collected
            self.bonus_balls_collected = 0
            
            self.launching = False
            self.round_in_progress = False
            
            # 업적 체크
            # 한 번에 10개 블록 파괴
            if self.blocks_destroyed_this_shot >= 10:
                self.achievement_manager.check_achievement('block_destroyer', 1)
            
            # 라운드 종료 시 각도 업적 체크
            self.achievement_manager.end_round()
            
            # 라운드 종료 후 상점 오픈 (게임 오버가 아닐 때만)
            if not self.game_over:
                self.shop.open = True
                self.shop.reset(self.score)
            
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
        
        # 콤보 시스템 업데이트
        self.update_combo_system()
        
        # 파티클 시스템 업데이트 (메모리 누수 방지)
        self.update_particles()
        
        # 게임 모드별 업데이트
        self.mode_manager.update(self)
        
        # 퍼즐 모드 완료 체크
        if self.mode_manager.is_game_complete(self):
            self.game_over = True
        
        # 업적 알림 업데이트
        self.achievement_manager.update_notifications()
        
        # 메모리 정리 (파티클이 너무 많이 쌓이는 것 방지)
        if len(self.particles) > 500:
            self.particles = self.particles[-300:]
        # 상점 아이템 효과 처리
        for item in self.shop.owned_items[:]:
            if item['name'] == "파워볼":
                self.active_powerups[1] = True
                self.shop.owned_items.remove(item)
                self.powerups_used_this_game += 1
            elif item['name'] == "스피드볼":
                self.active_powerups[2] = True
                self.shop.owned_items.remove(item)
                self.powerups_used_this_game += 1
            elif item['name'] == "매그넘볼":
                self.active_powerups[3] = True
                self.shop.owned_items.remove(item)
                self.powerups_used_this_game += 1
            elif item['name'] == "블록 삭제":
                for block in self.blocks:
                    block.active = False
                self.shop.owned_items.remove(item)
                self.powerups_used_this_game += 1
            
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
        
        # 업적: 100라운드 달성
        self.achievement_manager.check_achievement('centurion', self.round_num)
        
        # 생존 모드 업적
        if self.mode_manager.current_mode == GAME_MODE_SURVIVAL:
            self.achievement_manager.check_achievement('speed_demon', self.round_num)
        
        # 테마 업데이트 (라운드에 따라)
        self.current_theme = self.theme_manager.get_round_theme(self.round_num)
        
        # 발사 위치를 마지막 공이 떨어진 위치로 설정 (화면 경계 제한)
        self.launch_x = max(20, min(SCREEN_WIDTH - 20, self.last_ball_x))
        
        # 라운드 시작 시 파워업 초기화
        self.active_powerups = {1: False, 2: False, 3: False}
        self.shop.owned_items = []
    
    def update_combo_system(self):
        """콤보 시스템 업데이트"""
        current_time = pygame.time.get_ticks()
        
        # 콤보 시간 초과 시 리셋
        if current_time - self.last_combo_time > COMBO_TIME_WINDOW:
            if self.combo_count >= MIN_COMBO_COUNT:
                # 콤보가 끊어질 때 잠시 표시
                self.combo_display_time = current_time + 1000
            self.combo_count = 0
            self.combo_multiplier = 1.0
            self.last_block_color = None
    
    def update_particles(self):
        """파티클 시스템 업데이트"""
        # 파티클들 업데이트
        for particle in self.particles:
            particle.update()
        
        # 비활성화된 파티클들 제거
        self.particles = [particle for particle in self.particles if particle.active]
        
        # 파티클 수 제한 (메모리 누수 방지)
        if len(self.particles) > 200:
            self.particles = self.particles[-150:]
    
    def draw_themed_background(self, screen):
        """테마에 따른 배경 그리기"""
        if self.current_theme in THEME_BACKGROUNDS:
            colors = THEME_BACKGROUNDS[self.current_theme]
            
            # 그라데이션 배경
            for y in range(SCREEN_HEIGHT):
                # 높이에 따른 색상 보간
                ratio = y / SCREEN_HEIGHT
                
                if ratio < 0.5:
                    # 상단 절반: 첫 번째와 두 번째 색상 보간
                    t = ratio * 2
                    color = [
                        int(colors[0][i] * (1 - t) + colors[1][i] * t)
                        for i in range(3)
                    ]
                else:
                    # 하단 절반: 두 번째와 세 번째 색상 보간
                    t = (ratio - 0.5) * 2
                    color = [
                        int(colors[1][i] * (1 - t) + colors[2][i] * t)
                        for i in range(3)
                    ]
                
                pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
        else:
            # 기본 다크 배경
            screen.fill(BLACK)
        
        # 테마별 추가 장식 효과
        self.draw_theme_decorations(screen)
    
    def draw_theme_decorations(self, screen):
        """테마별 장식 효과"""
        current_time = pygame.time.get_ticks()
        
        if self.current_theme == THEME_CHRISTMAS:
            # 눈송이 효과
            for i in range(20):
                x = (current_time // 50 + i * 37) % (SCREEN_WIDTH + 20) - 10
                y = (current_time // 30 + i * 23) % (SCREEN_HEIGHT + 20) - 10
                size = 2 + (i % 3)
                alpha = 100 + (i % 100)
                
                snowflake_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(snowflake_surface, (*CHRISTMAS_WHITE, alpha), (size, size), size)
                screen.blit(snowflake_surface, (x, y))
        
        elif self.current_theme == THEME_HALLOWEEN:
            # 박쥐 실루엣 효과
            for i in range(5):
                x = (current_time // 100 + i * 80) % (SCREEN_WIDTH + 40) - 20
                y = 50 + math.sin((current_time + i * 1000) / 1000) * 30
                
                # 간단한 박쥐 모양
                bat_points = [
                    (x, y), (x-8, y-4), (x-4, y-8), (x, y-4),
                    (x+4, y-8), (x+8, y-4), (x, y)
                ]
                bat_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.polygon(bat_surface, (*HALLOWEEN_BLACK, 150), 
                                  [(p[0]-x+10, p[1]-y+10) for p in bat_points])
                screen.blit(bat_surface, (x-10, y-10))
        
        elif self.current_theme == THEME_SPRING:
            # 꽃잎 효과
            for i in range(15):
                x = (current_time // 80 + i * 45) % (SCREEN_WIDTH + 30) - 15
                y = (current_time // 60 + i * 67) % (SCREEN_HEIGHT + 30) - 15
                
                petal_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                color = SPRING_PINK if i % 2 == 0 else SPRING_YELLOW
                pygame.draw.circle(petal_surface, (*color, 120), (3, 3), 3)
                screen.blit(petal_surface, (x, y))
        
        elif self.current_theme == THEME_SUMMER:
            # 태양 광선 효과
            sun_x, sun_y = SCREEN_WIDTH - 60, 60
            for i in range(8):
                angle = (current_time / 1000 + i * math.pi / 4) % (2 * math.pi)
                end_x = sun_x + math.cos(angle) * 40
                end_y = sun_y + math.sin(angle) * 40
                
                ray_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(ray_surface, (*SUMMER_YELLOW, 50), 
                               (sun_x, sun_y), (end_x, end_y), 2)
                screen.blit(ray_surface, (0, 0))
    
    def draw_combo_ui(self, screen):
        """콤보 UI 표시"""
        current_time = pygame.time.get_ticks()
        
        # 콤보가 활성화되어 있거나 표시 시간이 남아있는 경우
        if (self.combo_count >= MIN_COMBO_COUNT or 
            current_time < self.combo_display_time):
            
            # 콤보 텍스트 위치 (화면 중앙 상단)
            combo_x = SCREEN_WIDTH // 2
            combo_y = 150
            
            # 콤보 카운트 표시
            if self.combo_count >= MIN_COMBO_COUNT:
                combo_text = f"{self.combo_count}x COMBO!"
                multiplier_text = f"x{self.combo_multiplier:.1f}"
                
                # 글로우 효과
                for i in range(3, 0, -1):
                    glow_surface = pygame.Surface((200, 60), pygame.SRCALPHA)
                    glow_color = (*COMBO_GLOW_COLOR[:3], COMBO_GLOW_COLOR[3] // i)
                    pygame.draw.rect(glow_surface, glow_color, (0, 0, 200, 60), border_radius=15)
                    screen.blit(glow_surface, (combo_x - 100, combo_y - 30))
                
                # 콤보 텍스트
                combo_surface = self.safe_render_text(self.large_font, combo_text, COMBO_TEXT_COLOR)
                combo_rect = combo_surface.get_rect(center=(combo_x, combo_y - 10))
                screen.blit(combo_surface, combo_rect)
                
                # 배율 텍스트
                multiplier_surface = self.safe_render_text(self.font, multiplier_text, NEON_GREEN)
                multiplier_rect = multiplier_surface.get_rect(center=(combo_x, combo_y + 15))
                screen.blit(multiplier_surface, multiplier_rect)
                
                # 추가 점수 표시
                if self.combo_score_gained > 0:
                    bonus_text = f"+{self.combo_score_gained}"
                    bonus_surface = self.safe_render_text(self.small_font, bonus_text, NEON_CYAN)
                    bonus_rect = bonus_surface.get_rect(center=(combo_x + 80, combo_y))
                    screen.blit(bonus_surface, bonus_rect)
        
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
        # 테마 색상 가져오기
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        
        # 상단 UI - 글래스모피즘 스타일
        ui_surface = pygame.Surface((SCREEN_WIDTH, TOP_UI_HEIGHT), pygame.SRCALPHA)
        ui_surface.fill((*theme_colors['surface'], 200))  # 반투명 배경
        self.screen.blit(ui_surface, (0, 0))
        
        # 상단 테두리 (테마 액센트)
        pygame.draw.line(self.screen, theme_colors['accent'], (0, TOP_UI_HEIGHT-1), (SCREEN_WIDTH, TOP_UI_HEIGHT-1), 2)
        
        # 점수 카드 (왼쪽)
        score_card = pygame.Rect(15, 10, 150, 60)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], score_card, border_radius=8)
        pygame.draw.rect(self.screen, theme_colors['ball_color'], score_card, 1, border_radius=8)
        
        # 점수 텍스트
        score_label = self.safe_render_text(self.small_font, "SCORE", theme_colors['text_secondary'])
        score_value = self.safe_render_text(self.font, f"{self.score:,}", theme_colors['ball_color'])
        self.screen.blit(score_label, (25, 20))
        self.screen.blit(score_value, (25, 40))
        
        # 베스트 스코어 (작게)
        if self.high_score > 0:
            best_text = self.safe_render_text(self.small_font, f"BEST: {self.high_score:,}", theme_colors['text_secondary'])
            self.screen.blit(best_text, (180, 25))
        
        # 라운드/모드 정보 카드 (오른쪽)
        info_card = pygame.Rect(SCREEN_WIDTH - 100, 10, 85, 60)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], info_card, border_radius=8)
        pygame.draw.rect(self.screen, theme_colors['accent'], info_card, 1, border_radius=8)
        
        # 모드별 정보 표시
        if self.mode_manager.current_mode == GAME_MODE_TIME_ATTACK:
            time_left = self.mode_manager.mode_data.get('time_left', 0)
            info_label = self.safe_render_text(self.small_font, "TIME", theme_colors['text_secondary'])
            info_value = self.safe_render_text(self.font, f"{int(time_left)}", theme_colors['accent'])
        elif self.mode_manager.current_mode == GAME_MODE_PUZZLE:
            balls_left = self.mode_manager.mode_data.get('balls_left', 0)
            info_label = self.safe_render_text(self.small_font, "BALLS", theme_colors['text_secondary'])
            info_value = self.safe_render_text(self.font, f"{balls_left}", theme_colors['accent'])
        elif self.mode_manager.current_mode == GAME_MODE_SURVIVAL:
            speed = self.mode_manager.mode_data.get('speed_multiplier', 1.0)
            info_label = self.safe_render_text(self.small_font, "SPEED", theme_colors['text_secondary'])
            info_value = self.safe_render_text(self.font, f"{speed:.1f}x", theme_colors['accent'])
        else:  # 클래식 모드
            info_label = self.safe_render_text(self.small_font, "ROUND", theme_colors['text_secondary'])
            info_value = self.safe_render_text(self.font, f"{self.round_num}", theme_colors['accent'])
        
        self.screen.blit(info_label, (SCREEN_WIDTH - 90, 20))
        self.screen.blit(info_value, (SCREEN_WIDTH - 75, 40))
        
        # 하단 UI - 글래스모피즘 스타일
        bottom_surface = pygame.Surface((SCREEN_WIDTH, BOTTOM_UI_HEIGHT), pygame.SRCALPHA)
        bottom_surface.fill((*theme_colors['surface'], 200))
        self.screen.blit(bottom_surface, (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT))
        
        # 하단 테두리
        pygame.draw.line(self.screen, theme_colors['accent'], (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT), 2)
        
        # 공 개수 표시 (중앙, 더 큰 스타일)
        ball_bg = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 80, 120, 50)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], ball_bg, border_radius=25)
        pygame.draw.rect(self.screen, theme_colors['ball_color'], ball_bg, 2, border_radius=25)
        
        # 공 아이콘 (원형)
        pygame.draw.circle(self.screen, theme_colors['ball_color'], (SCREEN_WIDTH//2 - 30, SCREEN_HEIGHT - 55), 8)
        pygame.draw.circle(self.screen, theme_colors['text'], (SCREEN_WIDTH//2 - 30, SCREEN_HEIGHT - 55), 8, 2)
        
        ball_count_text = self.safe_render_text(self.font, f"×{self.ball_count}", theme_colors['text'])
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
        # 테마에 따른 배경
        self.draw_themed_background(self.screen)
        
        if self.game_state == GAME_STATE_TITLE:
            self.draw_title()
        elif self.game_state == GAME_STATE_GAME:
            self.draw_game()
        elif self.game_state == GAME_STATE_SETTINGS:
            self.draw_settings()
        elif self.game_state == GAME_STATE_RANKING:
            self.draw_ranking()
        elif self.game_state == GAME_STATE_STATISTICS:
            self.draw_statistics()
        elif self.game_state == GAME_STATE_MODE_SELECT:
            self.draw_mode_select()
        elif self.game_state == GAME_STATE_ACHIEVEMENTS:
            self.draw_achievements()
            
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
        
        # 파티클 그리기
        for particle in self.particles:
            particle.draw(self.screen)
            
        # 조준선 그리기
        self.draw_aim_line()
        
        # 콤보 UI 그리기
        self.draw_combo_ui(self.screen)
        
        # 업적 알림 그리기
        self.draw_achievement_notifications()
        
        # 상점 그리기
        if self.shop.open:
            self.shop.draw(self.screen)
        
        # 일시정지 화면
        if self.paused:
            self.draw_pause_menu()
        
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
            
            # 게임 오버 타이틀 (모드별 메시지)
            if self.mode_manager.current_mode == GAME_MODE_PUZZLE and self.mode_manager.is_game_complete(self):
                game_over_text = self.safe_render_text(self.large_font, "🎉 PUZZLE SOLVED!", NEON_GREEN)
            elif self.mode_manager.current_mode == GAME_MODE_TIME_ATTACK:
                game_over_text = self.safe_render_text(self.large_font, "⏰ TIME UP!", NEON_ORANGE)
            else:
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
        theme_names = {
            "auto": "Auto",
            "dark": "Dark",
            "light": "Light", 
            "christmas": "Christmas",
            "halloween": "Halloween",
            "spring": "Spring",
            "summer": "Summer"
        }
        
        settings_text = [
            f"{get_text('ball_speed')}: {self.settings['ball_speed']}",
            f"{get_text('sound')}: {get_text('sound_on') if self.settings['sound_enabled'] else get_text('sound_off')}",
            f"{get_text('difficulty')}: {self.settings['difficulty']}",
            f"{get_text('language')}: {language_manager.get_language_name(self.settings['language'])}",
            f"Theme: {theme_names.get(self.settings['theme'], self.settings['theme'])}"
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
    
    def draw_pause_menu(self):
        """일시정지 메뉴 그리기"""
        # 블러 배경
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*BLACK, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 일시정지 카드
        pause_card = pygame.Rect(50, SCREEN_HEIGHT//2 - 120, SCREEN_WIDTH - 100, 240)
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], pause_card, border_radius=20)
        pygame.draw.rect(self.screen, theme_colors['accent'], pause_card, 3, border_radius=20)
        
        # 일시정지 타이틀
        pause_title = self.safe_render_text(self.large_font, "⏸️ PAUSED", theme_colors['accent'])
        pause_rect = pause_title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
        self.screen.blit(pause_title, pause_rect)
        
        # 메뉴 옵션들
        menu_options = ["Continue", "Settings", "Main Menu"]
        
        for i, option in enumerate(menu_options):
            y = SCREEN_HEIGHT//2 - 30 + i * 40
            
            if i == self.pause_menu_selected:
                # 선택된 옵션
                option_surface = self.safe_render_text(self.font, f"▶ {option}", theme_colors['accent'])
            else:
                option_surface = self.safe_render_text(self.font, option, theme_colors['text'])
            
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(option_surface, option_rect)
        
        # 조작 안내
        help_text = self.safe_render_text(self.small_font, "↑↓: Select • ENTER: Confirm • ESC: Resume", theme_colors['text_secondary'])
        help_rect = help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90))
        self.screen.blit(help_text, help_rect)
    
    def draw_statistics(self):
        """통계 화면 그리기"""
        # 테마 배경
        self.draw_themed_background(self.screen)
        
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        
        # 통계 메인 카드
        stats_card = pygame.Rect(20, 50, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 100)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], stats_card, border_radius=20)
        pygame.draw.rect(self.screen, theme_colors['accent'], stats_card, 3, border_radius=20)
        
        # 제목
        title_text = self.safe_render_text(self.large_font, "📊 STATISTICS", theme_colors['accent'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 90))
        self.screen.blit(title_text, title_rect)
        
        # 통계 데이터
        stats_data = [
            ("Play Time", self.stats_manager.get_play_time_formatted()),
            ("Games Played", str(self.stats_manager.stats['games_played'])),
            ("Highest Score", f"{self.stats_manager.stats['highest_score']:,}"),
            ("Average Score", f"{self.stats_manager.get_average_score():,}"),
            ("Highest Round", str(self.stats_manager.stats['highest_round'])),
            ("Blocks Destroyed", str(self.stats_manager.stats['total_blocks_destroyed'])),
            ("Highest Combo", str(self.stats_manager.stats['highest_combo'])),
            ("Combos Achieved", str(self.stats_manager.stats['combos_achieved'])),
            ("Powerups Used", str(self.stats_manager.stats['powerups_used'])),
            ("Bonus Balls", str(self.stats_manager.stats['bonus_balls_collected']))
        ]
        
        # 통계 항목들 (2열로 배치)
        for i, (label, value) in enumerate(stats_data):
            col = i % 2
            row = i // 2
            x = 60 + col * 140
            y = 140 + row * 35
            
            # 라벨
            label_surface = self.safe_render_text(self.small_font, label + ":", theme_colors['text_secondary'])
            self.screen.blit(label_surface, (x, y))
            
            # 값
            value_surface = self.safe_render_text(self.font, value, theme_colors['text'])
            self.screen.blit(value_surface, (x, y + 15))
        
        # 블록별 파괴 통계
        block_stats_y = 480
        block_title = self.safe_render_text(self.font, "Blocks Destroyed by Type:", theme_colors['text'])
        self.screen.blit(block_title, (40, block_stats_y))
        
        block_types = [
            ("Normal", self.stats_manager.stats['blocks_destroyed']['normal'], theme_colors['text']),
            ("Bomb", self.stats_manager.stats['blocks_destroyed']['bomb'], (255, 69, 0)),
            ("Shield", self.stats_manager.stats['blocks_destroyed']['shield'], (70, 130, 180)),
            ("Ghost", self.stats_manager.stats['blocks_destroyed']['ghost'], (147, 112, 219))
        ]
        
        for i, (block_type, count, color) in enumerate(block_types):
            x = 40 + i * 80
            y = block_stats_y + 30
            
            # 블록 타입 아이콘 (작은 사각형)
            block_rect = pygame.Rect(x, y, 20, 20)
            pygame.draw.rect(self.screen, color, block_rect, border_radius=4)
            pygame.draw.rect(self.screen, theme_colors['text'], block_rect, 1, border_radius=4)
            
            # 타입명과 개수
            type_text = self.safe_render_text(self.small_font, block_type, theme_colors['text_secondary'])
            count_text = self.safe_render_text(self.small_font, str(count), theme_colors['text'])
            
            self.screen.blit(type_text, (x + 25, y))
            self.screen.blit(count_text, (x + 25, y + 12))
        
        # 뒤로가기 안내
        back_text = self.safe_render_text(self.small_font, "ESC: Back to Menu", theme_colors['text_secondary'])
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(back_text, back_rect)
    
    def draw_mode_select(self):
        """모드 선택 화면 그리기"""
        # 테마 배경
        self.draw_themed_background(self.screen)
        
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        
        # 모드 선택 메인 카드
        mode_card = pygame.Rect(20, 50, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 100)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], mode_card, border_radius=20)
        pygame.draw.rect(self.screen, theme_colors['accent'], mode_card, 3, border_radius=20)
        
        # 제목
        title_text = self.safe_render_text(self.large_font, "🎯 CHALLENGE MODES", theme_colors['accent'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 90))
        self.screen.blit(title_text, title_rect)
        
        # 모드 목록
        modes = [
            ("Classic", "Standard game mode with unlimited time"),
            ("Time Attack", f"Clear blocks in {TIME_ATTACK_DURATION} seconds"),
            ("Survival", "Survive with increasing ball speed"),
            ("Puzzle", f"Clear all blocks with {PUZZLE_MODE_BALLS} balls")
        ]
        
        for i, (mode_name, description) in enumerate(modes):
            y = 150 + i * 100
            
            # 모드 카드
            mode_item_card = pygame.Rect(40, y - 35, SCREEN_WIDTH - 80, 80)
            
            if i == self.mode_select_index:
                # 선택된 모드
                pygame.draw.rect(self.screen, theme_colors['surface'], mode_item_card, border_radius=12)
                pygame.draw.rect(self.screen, theme_colors['accent'], mode_item_card, 2, border_radius=12)
                name_color = theme_colors['accent']
                desc_color = theme_colors['text']
                
                # 선택 인디케이터
                indicator = pygame.Rect(45, y - 30, 4, 70)
                pygame.draw.rect(self.screen, theme_colors['accent'], indicator, border_radius=2)
            else:
                pygame.draw.rect(self.screen, theme_colors['darker_surface'], mode_item_card, border_radius=12)
                pygame.draw.rect(self.screen, theme_colors['text_secondary'], mode_item_card, 1, border_radius=12)
                name_color = theme_colors['text']
                desc_color = theme_colors['text_secondary']
            
            # 모드 이름
            name_surface = self.safe_render_text(self.font, mode_name, name_color)
            name_rect = name_surface.get_rect(center=(SCREEN_WIDTH//2, y - 10))
            self.screen.blit(name_surface, name_rect)
            
            # 모드 설명
            desc_surface = self.safe_render_text(self.small_font, description, desc_color)
            desc_rect = desc_surface.get_rect(center=(SCREEN_WIDTH//2, y + 15))
            self.screen.blit(desc_surface, desc_rect)
        
        # 조작 안내
        help_text = self.safe_render_text(self.small_font, "↑↓: Select • ENTER: Start • ESC: Back", theme_colors['text_secondary'])
        help_rect = help_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(help_text, help_rect)
    
    def draw_achievements(self):
        """업적 화면 그리기"""
        # 테마 배경
        self.draw_themed_background(self.screen)
        
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        
        # 업적 메인 카드
        achievement_card = pygame.Rect(20, 50, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 100)
        pygame.draw.rect(self.screen, theme_colors['darker_surface'], achievement_card, border_radius=20)
        pygame.draw.rect(self.screen, theme_colors['accent'], achievement_card, 3, border_radius=20)
        
        # 제목과 진행률
        title_text = self.safe_render_text(self.large_font, "🏆 ACHIEVEMENTS", theme_colors['accent'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 진행률 표시
        completion = self.achievement_manager.get_completion_percentage()
        progress_text = f"{self.achievement_manager.get_unlocked_count()}/{self.achievement_manager.get_total_count()} ({completion:.0f}%)"
        progress_surface = self.safe_render_text(self.small_font, progress_text, theme_colors['text_secondary'])
        progress_rect = progress_surface.get_rect(center=(SCREEN_WIDTH//2, 105))
        self.screen.blit(progress_surface, progress_rect)
        
        # 업적 목록 (스크롤 가능하도록 일부만 표시)
        start_y = 130
        achievement_height = 45
        visible_achievements = 10
        
        achievements_list = list(self.achievement_manager.achievements.values())
        
        for i, achievement in enumerate(achievements_list[:visible_achievements]):
            y = start_y + i * achievement_height
            
            # 업적 카드
            achievement_item_rect = pygame.Rect(30, y, SCREEN_WIDTH - 60, achievement_height - 5)
            
            if achievement['unlocked']:
                # 달성된 업적
                pygame.draw.rect(self.screen, theme_colors['surface'], achievement_item_rect, border_radius=8)
                pygame.draw.rect(self.screen, NEON_GREEN, achievement_item_rect, 2, border_radius=8)
                name_color = NEON_GREEN
                desc_color = theme_colors['text']
                progress_color = NEON_GREEN
            else:
                # 미달성 업적
                pygame.draw.rect(self.screen, theme_colors['darker_surface'], achievement_item_rect, border_radius=8)
                pygame.draw.rect(self.screen, theme_colors['text_secondary'], achievement_item_rect, 1, border_radius=8)
                name_color = theme_colors['text_secondary']
                desc_color = theme_colors['text_secondary']
                progress_color = theme_colors['text_secondary']
            
            # 업적 아이콘과 이름
            icon_name = f"{achievement['icon']} {achievement['name']}"
            name_surface = self.safe_render_text(self.small_font, icon_name, name_color)
            self.screen.blit(name_surface, (40, y + 5))
            
            # 업적 설명
            desc_surface = self.safe_render_text(self.small_font, achievement['description'], desc_color)
            self.screen.blit(desc_surface, (40, y + 22))
            
            # 진행도 표시
            if not achievement['unlocked'] and achievement['target'] > 1:
                progress_text = f"{achievement['progress']}/{achievement['target']}"
                progress_surface = self.safe_render_text(self.small_font, progress_text, progress_color)
                progress_rect = progress_surface.get_rect()
                progress_rect.right = SCREEN_WIDTH - 40
                progress_rect.centery = y + achievement_height // 2
                self.screen.blit(progress_surface, progress_rect)
        
        # 뒤로가기 안내
        back_text = self.safe_render_text(self.small_font, "ESC: Back to Menu", theme_colors['text_secondary'])
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(back_text, back_rect)
    
    def draw_achievement_notifications(self):
        """업적 달성 알림 그리기"""
        if not self.achievement_manager.notifications:
            return
        
        theme_colors = self.theme_manager.get_theme_colors(self.current_theme)
        current_time = pygame.time.get_ticks()
        
        for i, notification in enumerate(self.achievement_manager.notifications):
            achievement = notification['achievement']
            elapsed = current_time - notification['timestamp']
            
            # 페이드 인/아웃 효과
            if elapsed < 500:  # 페이드 인
                alpha = int(255 * (elapsed / 500))
            elif elapsed > notification['duration'] - 500:  # 페이드 아웃
                alpha = int(255 * ((notification['duration'] - elapsed) / 500))
            else:
                alpha = 255
            
            # 알림 위치 (여러 개일 경우 위로 쌓임)
            y = 200 + i * 80
            
            # 알림 카드
            notification_rect = pygame.Rect(20, y, SCREEN_WIDTH - 40, 70)
            notification_surface = pygame.Surface((SCREEN_WIDTH - 40, 70), pygame.SRCALPHA)
            green_color = (NEON_GREEN[0], NEON_GREEN[1], NEON_GREEN[2], min(alpha, 200))
            notification_surface.fill(green_color)
            self.screen.blit(notification_surface, (20, y))
            
            pygame.draw.rect(self.screen, NEON_GREEN, notification_rect, 2, border_radius=10)
            
            # "Achievement Unlocked!" 텍스트
            unlock_text = self.safe_render_text(self.small_font, "🎉 ACHIEVEMENT UNLOCKED!", WHITE)
            unlock_rect = unlock_text.get_rect(center=(SCREEN_WIDTH//2, y + 15))
            self.screen.blit(unlock_text, unlock_rect)
            
            # 업적 이름
            achievement_text = f"{achievement['icon']} {achievement['name']}"
            achievement_surface = self.safe_render_text(self.font, achievement_text, WHITE)
            achievement_rect = achievement_surface.get_rect(center=(SCREEN_WIDTH//2, y + 35))
            self.screen.blit(achievement_surface, achievement_rect)
            
            # 업적 설명
            desc_surface = self.safe_render_text(self.small_font, achievement['description'], WHITE)
            desc_rect = desc_surface.get_rect(center=(SCREEN_WIDTH//2, y + 55))
            self.screen.blit(desc_surface, desc_rect)
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()