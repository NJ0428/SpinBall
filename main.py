#!/usr/bin/env python3
"""
볼즈 게임 (Ballz Style)
Python과 Pygame을 사용한 숫자 블록 브레이커 게임

조작법:
- 마우스 움직임: 발사 각도 조정
- 마우스 클릭: 공 발사
- R 키: 게임 재시작 (게임 오버 시)
"""

import pygame
import os
from game_objects import Game

def main():
    print("볼즈 게임을 시작합니다!")
    print("조작법:")
    print("- 마우스로 발사 각도를 조정하세요")
    print("- 마우스 클릭으로 공을 발사하세요")
    print("- 블록의 숫자만큼 공이 맞아야 블록이 사라집니다")
    print("- 블록이 바닥에 닿으면 게임 오버!")
    print("- 라운드가 지날수록 공의 개수가 늘어납니다")
    
    # pygame 초기화
    pygame.init()
    
    # 게임 아이콘 설정
    try:
        icon_path = "images/spinball_icon.png"
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
            print("게임 아이콘이 적용되었습니다.")
    except Exception as e:
        print(f"아이콘 로딩 실패: {e}")
    
    game = Game()
    game.run()

if __name__ == "__main__":
    main() 