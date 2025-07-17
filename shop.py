import pygame
from constants import SHOP_ITEMS

class Shop:
    def __init__(self, font, player_score):
        self.font = font
        self.items = SHOP_ITEMS
        self.open = False
        self.selected_item = None
        self.owned_items = []  # 이번 라운드에 구매한 아이템
        self.player_score = player_score

    def draw(self, surface):
        # 반투명 배경
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 상점 타이틀
        title = self.font.render("상점", True, (255, 255, 0))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 80))

        # 아이템 목록
        start_y = 150
        for idx, item in enumerate(self.items):
            y = start_y + idx * 70
            name = f"{item['name']} ({item['price']}점)"
            desc = item['desc']
            color = (200, 200, 200)
            if self.player_score < item['price']:
                color = (120, 120, 120)  # 잔액 부족
            name_surf = self.font.render(name, True, color)
            desc_surf = self.font.render(desc, True, color)
            surface.blit(name_surf, (120, y))
            surface.blit(desc_surf, (400, y))
            # 버튼
            btn_rect = pygame.Rect(700, y, 80, 40)
            pygame.draw.rect(surface, color, btn_rect, border_radius=8)
            btn_text = self.font.render("구매", True, (0, 0, 0))
            surface.blit(btn_text, (btn_rect.x + 10, btn_rect.y + 5))
            item['btn_rect'] = btn_rect  # 클릭 판정용

        # 닫기 버튼
        close_rect = pygame.Rect(surface.get_width()//2 - 50, 500, 100, 40)
        pygame.draw.rect(surface, (180, 180, 180), close_rect, border_radius=8)
        close_text = self.font.render("닫기", True, (0, 0, 0))
        surface.blit(close_text, (close_rect.x + 20, close_rect.y + 5))
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