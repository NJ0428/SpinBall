import pygame

def safe_render_text(font, text, color, fallback_font=None):
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
