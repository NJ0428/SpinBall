import pygame
from constants import (SHOP_ITEMS, BLACK, DARKER_SURFACE, DARK_SURFACE, 
                      NEON_PURPLE, NEON_CYAN, NEON_GREEN, WHITE, 
                      TEXT_SECONDARY, DARK_GRAY)

class Shop:
    def __init__(self, font, player_score):
        self.font = font
        self.items = SHOP_ITEMS
        self.open = False
        self.selected_item = None
        self.owned_items = []  # 이번 라운드에 구매한 아이템
        self.player_score = player_score

    def draw(self, surface):
        
        # 블러 배경
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*BLACK, 220))
        surface.blit(overlay, (0, 0))

        # 상점 메인 카드
        shop_card = pygame.Rect(20, 60, surface.get_width() - 40, surface.get_height() - 120)
        pygame.draw.rect(surface, DARKER_SURFACE, shop_card, border_radius=20)
        pygame.draw.rect(surface, NEON_PURPLE, shop_card, 3, border_radius=20)

        # 상점 타이틀 (네온 효과)
        title = self.font.render("🛒 POWER-UP SHOP", True, NEON_PURPLE)
        title_rect = title.get_rect(center=(surface.get_width() // 2, 100))
        surface.blit(title, title_rect)
        
        # 현재 점수 표시
        score_text = self.font.render(f"Credits: {self.player_score:,}", True, NEON_CYAN)
        score_rect = score_text.get_rect(center=(surface.get_width() // 2, 130))
        surface.blit(score_text, score_rect)

        # 아이템 목록 (카드 스타일)
        start_y = 170
        for idx, item in enumerate(self.items):
            y = start_y + idx * 80
            
            # 아이템 카드
            item_card = pygame.Rect(40, y, surface.get_width() - 80, 70)
            can_afford = self.player_score >= item['price']
            
            if can_afford:
                pygame.draw.rect(surface, DARK_SURFACE, item_card, border_radius=12)
                pygame.draw.rect(surface, NEON_GREEN, item_card, 2, border_radius=12)
                text_color = WHITE
                price_color = NEON_GREEN
            else:
                pygame.draw.rect(surface, DARKER_SURFACE, item_card, border_radius=12)
                pygame.draw.rect(surface, DARK_GRAY, item_card, 1, border_radius=12)
                text_color = DARK_GRAY
                price_color = DARK_GRAY
            
            # 아이템 정보
            name_text = self.font.render(item['name'], True, text_color)
            desc_text = self.font.render(item['desc'], True, TEXT_SECONDARY if can_afford else DARK_GRAY)
            price_text = self.font.render(f"{item['price']:,}", True, price_color)
            
            surface.blit(name_text, (60, y + 10))
            surface.blit(desc_text, (60, y + 35))
            surface.blit(price_text, (surface.get_width() - 150, y + 10))
            
            # 구매 버튼
            btn_rect = pygame.Rect(surface.get_width() - 120, y + 35, 80, 25)
            if can_afford:
                pygame.draw.rect(surface, NEON_GREEN, btn_rect, border_radius=6)
                btn_text = self.font.render("BUY", True, BLACK)
            else:
                pygame.draw.rect(surface, DARK_GRAY, btn_rect, border_radius=6)
                btn_text = self.font.render("BUY", True, DARKER_SURFACE)
            
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            surface.blit(btn_text, btn_text_rect)
            item['btn_rect'] = btn_rect

        # 닫기 버튼 (모던 스타일)
        close_rect = pygame.Rect(surface.get_width()//2 - 60, surface.get_height() - 80, 120, 40)
        pygame.draw.rect(surface, DARK_SURFACE, close_rect, border_radius=20)
        pygame.draw.rect(surface, NEON_CYAN, close_rect, 2, border_radius=20)
        close_text = self.font.render("CLOSE", True, NEON_CYAN)
        close_text_rect = close_text.get_rect(center=close_rect.center)
        surface.blit(close_text, close_text_rect)
        self.close_rect = close_rect

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            # 아이템 구매
            for item in self.items:
                if item['btn_rect'].collidepoint(pos):
                    self.buy(item)
            # 닫기 버튼
            if self.close_rect.collidepoint(pos):
                self.open = False

    def buy(self, item):
        if self.player_score >= item['price']:
            self.player_score -= item['price']
            if item['name'] == "블록 삭제":
                self.owned_items.append(item)  # 즉시 사용 플래그(게임에서 처리)
            else:
                self.owned_items.append(item)

    def use_item(self, key):
        # 1,2,3번 키로 아이템 사용
        for item in self.owned_items:
            if item['key'] == key:
                self.owned_items.remove(item)
                return item['name']
        return None

    def reset(self, player_score):
        self.owned_items = []
        self.player_score = player_score 