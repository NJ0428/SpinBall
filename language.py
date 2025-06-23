# -*- coding: utf-8 -*-
"""
SpinBall 게임 언어 설정 파일
Language Settings for SpinBall Game
"""

# 지원하는 언어 목록
SUPPORTED_LANGUAGES = ['ko', 'en']
DEFAULT_LANGUAGE = 'ko'

# 언어별 텍스트 사전
TEXTS = {
    'ko': {
        # 타이틀 화면
        'game_title': 'SpinBall',
        'menu_start': '게임시작',
        'menu_settings': '게임 설정',
        'menu_ranking': '랭킹',
        'menu_quit': '게임 종료',
        
        # 게임 플레이
        'score': '점수',
        'round': '라운드',
        'balls': '공',
        'game_over': '게임 오버',
        'restart_hint': 'R키: 재시작, ESC: 타이틀',
        
        # 설정 화면
        'settings_title': '게임 설정',
        'ball_speed': '공 속도',
        'sound': '사운드',
        'difficulty': '난이도',
        'language': '언어',
        'sound_on': '켜짐',
        'sound_off': '꺼짐',
        'back_to_title': 'ESC: 타이틀로 돌아가기',
        'korean': '한국어',
        'english': 'English',
        
        # 랭킹 화면
        'ranking_title': '랭킹',
        
        # 게임 조작법
        'controls_title': '조작법',
        'control_aim': '마우스로 발사 각도를 조정하세요',
        'control_shoot': '마우스 클릭으로 공을 발사하세요',
        'control_blocks': '블록의 숫자만큼 공이 맞아야 블록이 사라집니다',
        'control_gameover': '블록이 바닥에 닿으면 게임 오버!',
        'control_rounds': '라운드가 지날수록 공의 개수가 늘어납니다',
        
        # 기타
        'easy': '쉬움',
        'normal': '보통',
        'hard': '어려움',
    },
    
    'en': {
        # 타이틀 화면
        'game_title': 'SpinBall',
        'menu_start': 'Start Game',
        'menu_settings': 'Settings',
        'menu_ranking': 'Ranking',
        'menu_quit': 'Quit Game',
        
        # 게임 플레이
        'score': 'Score',
        'round': 'Round',
        'balls': 'Balls',
        'game_over': 'Game Over',
        'restart_hint': 'R: Restart, ESC: Title',
        
        # 설정 화면
        'settings_title': 'Game Settings',
        'ball_speed': 'Ball Speed',
        'sound': 'Sound',
        'difficulty': 'Difficulty',
        'language': 'Language',
        'sound_on': 'On',
        'sound_off': 'Off',
        'back_to_title': 'ESC: Back to Title',
        'korean': '한국어',
        'english': 'English',
        
        # 랭킹 화면
        'ranking_title': 'Ranking',
        
        # 게임 조작법
        'controls_title': 'Controls',
        'control_aim': 'Move mouse to aim',
        'control_shoot': 'Click to shoot balls',
        'control_blocks': 'Hit blocks equal to their number to destroy',
        'control_gameover': 'Game over if blocks reach bottom!',
        'control_rounds': 'More balls each round',
        
        # 기타
        'easy': 'Easy',
        'normal': 'Normal',
        'hard': 'Hard',
    }
}

class LanguageManager:
    """언어 관리 클래스"""
    
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.current_language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    
    def get_text(self, key):
        """키에 해당하는 현재 언어의 텍스트를 반환"""
        try:
            return TEXTS[self.current_language][key]
        except KeyError:
            # 키가 없으면 기본 언어(한국어)에서 찾기
            try:
                return TEXTS[DEFAULT_LANGUAGE][key]
            except KeyError:
                return f"[{key}]"  # 키를 찾을 수 없으면 키 이름 반환
    
    def set_language(self, language):
        """언어 설정"""
        if language in SUPPORTED_LANGUAGES:
            self.current_language = language
            return True
        return False
    
    def get_current_language(self):
        """현재 언어 반환"""
        return self.current_language
    
    def get_language_name(self, lang_code=None):
        """언어 코드에 해당하는 언어 이름 반환"""
        if lang_code is None:
            lang_code = self.current_language
        
        if lang_code == 'ko':
            return self.get_text('korean')
        elif lang_code == 'en':
            return self.get_text('english')
        else:
            return lang_code
    
    def get_supported_languages(self):
        """지원하는 언어 목록 반환"""
        return SUPPORTED_LANGUAGES.copy()

# 전역 언어 관리자 인스턴스
language_manager = LanguageManager()

def get_text(key):
    """편의 함수: 현재 언어의 텍스트 반환"""
    return language_manager.get_text(key)

def set_language(language):
    """편의 함수: 언어 설정"""
    return language_manager.set_language(language)

def get_current_language():
    """편의 함수: 현재 언어 반환"""
    return language_manager.get_current_language() 