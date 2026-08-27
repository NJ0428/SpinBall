"""
SpinBall 절차적 사운드 시스템
외부 음원 파일 없이 numpy로 모든 효과음과 BGM을 실시간 합성합니다.
"""

import math
import random

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class SoundManager:
    """절차적 오디오 합성 기반 사운드 매니저"""

    SAMPLE_RATE = 44100

    def __init__(self):
        self.enabled = True
        self.available = False
        self.sounds = {}
        self.bgm_sound = None
        self.bgm_channel = None
        self.current_bgm_tier = -1

        if not NUMPY_AVAILABLE or not PYGAME_AVAILABLE:
            print("사운드 시스템: numpy 또는 pygame 없음 - 무음 모드")
            return

        self._init_mixer()
        if self.available:
            self._pregenerate_sounds()

    # ──────────────────────────────────────────
    # 초기화
    # ──────────────────────────────────────────

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self.SAMPLE_RATE,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            pygame.mixer.set_num_channels(16)
            self.available = True
        except Exception as e:
            print(f"사운드 믹서 초기화 실패: {e}")
            self.available = False

    # ──────────────────────────────────────────
    # 내부 파형 도구
    # ──────────────────────────────────────────

    def _to_sound(self, samples: "np.ndarray") -> "pygame.mixer.Sound":
        """float64 mono → pygame.Sound (stereo int16)"""
        peak = np.max(np.abs(samples))
        if peak > 0:
            samples = samples / peak * 0.85
        stereo = np.column_stack([samples, samples])
        stereo = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
        return pygame.sndarray.make_sound(stereo)

    def _t(self, duration: float) -> "np.ndarray":
        return np.linspace(0, duration, int(self.SAMPLE_RATE * duration), endpoint=False)

    def _sin(self, freq: float, t: "np.ndarray", vol: float = 1.0) -> "np.ndarray":
        return vol * np.sin(2 * math.pi * freq * t)

    def _sweep(self, f0: float, f1: float, t: "np.ndarray", vol: float = 1.0) -> "np.ndarray":
        """주파수 스윕 (선형)"""
        freqs = np.linspace(f0, f1, len(t))
        phase = np.cumsum(freqs) / self.SAMPLE_RATE
        return vol * np.sin(2 * math.pi * phase)

    def _noise(self, n: int, vol: float = 1.0) -> "np.ndarray":
        return vol * (np.random.random(n) * 2 - 1)

    def _exp_env(self, t: "np.ndarray", decay: float) -> "np.ndarray":
        return np.exp(-decay * t)

    def _adsr(self, n: int, atk: float = 0.02, dec: float = 0.1, sus: float = 0.7, rel: float = 0.2) -> "np.ndarray":
        env = np.ones(n)
        a = max(1, int(atk * n)); d = max(1, int(dec * n))
        s = max(1, int(sus * n)); r = max(1, n - a - d - s)
        env[:a] = np.linspace(0, 1, a)
        env[a:a+d] = np.linspace(1, 0.7, d)
        env[a+d:a+d+s] = 0.7
        env[a+d+s:a+d+s+r] = np.linspace(0.7, 0, r)
        return env

    # ──────────────────────────────────────────
    # 효과음 생성기
    # ──────────────────────────────────────────

    def _sfx_wall_bounce(self) -> "np.ndarray":
        """벽 반사 - 짧고 부드러운 핑"""
        t = self._t(0.09)
        w = self._sweep(350, 180, t, 0.45)
        return w * self._exp_env(t, 35)

    def _sfx_block_hit(self) -> "np.ndarray":
        """블록 타격(미파괴) - 둔탁한 틱"""
        t = self._t(0.10)
        w = self._sin(480, t, 0.35) + self._noise(len(t), 0.08)
        return w * self._exp_env(t, 30)

    def _sfx_destroy_normal(self) -> "np.ndarray":
        """일반 블록 파괴 - 경쾌한 팝"""
        t = self._t(0.18)
        w = self._sweep(900, 220, t, 0.55)
        w += self._noise(len(t), 0.06)
        return w * self._exp_env(t, 18)

    def _sfx_destroy_bomb(self) -> "np.ndarray":
        """폭탄 블록 - 저주파 폭발"""
        t = self._t(0.45)
        # 저주파 붐 + 노이즈
        w = self._sweep(90, 30, t, 0.7) + self._noise(len(t), 0.5)
        env = self._exp_env(t, 7)
        # 초반 충격 강조
        env[:int(0.03 * self.SAMPLE_RATE)] *= 1.8
        return w * env

    def _sfx_destroy_shield(self) -> "np.ndarray":
        """방어막 블록 - 금속 쇳소리"""
        t = self._t(0.35)
        w = (self._sin(160, t, 0.30)
             + self._sin(320, t, 0.20)
             + self._sin(480, t, 0.12)
             + self._noise(len(t), 0.18))
        return w * self._exp_env(t, 10)

    def _sfx_destroy_ghost(self) -> "np.ndarray":
        """유령 블록 - 신비로운 글리산도"""
        t = self._t(0.55)
        w = self._sweep(1400, 350, t, 0.40)
        # 두 번째 레이어 (약간 다른 속도)
        w += self._sweep(1100, 550, t, 0.20)
        return w * self._exp_env(t, 5)

    def _sfx_combo(self, level: int) -> "np.ndarray":
        """콤보 - 레벨마다 반음씩 올라가는 벨 톤"""
        dur = 0.18
        t = self._t(dur)
        base = 440.0
        semitones = min(level - 2, 14)
        freq = base * (2 ** (semitones / 12.0))
        w = (self._sin(freq, t, 0.40)
             + self._sin(freq * 2, t, 0.15)
             + self._sin(freq * 3, t, 0.07))
        return w * self._exp_env(t, 18)

    def _sfx_launch(self) -> "np.ndarray":
        """공 발사 - 상승 스윕"""
        t = self._t(0.18)
        w = self._sweep(180, 900, t, 0.38)
        w += self._noise(len(t), 0.06)
        return w * self._exp_env(t, 14)

    def _sfx_round_complete(self) -> "np.ndarray":
        """라운드 완료 - 상승 4음 팡파레"""
        notes = [523, 659, 784, 1047]  # C4 E4 G4 C5
        step = 0.10
        total = int(self.SAMPLE_RATE * (step * len(notes) + 0.35))
        w = np.zeros(total)
        for i, f in enumerate(notes):
            s = int(i * step * self.SAMPLE_RATE)
            n = int(step * self.SAMPLE_RATE)
            t = np.linspace(0, step, n)
            nw = (self._sin(f, t, 0.45) + self._sin(f * 2, t, 0.15))
            nw *= self._exp_env(t, 6)
            w[s:s + n] += nw
        return w

    def _sfx_game_over(self) -> "np.ndarray":
        """게임 오버 - 하강 4음"""
        notes = [392, 330, 262, 196]  # G4 E4 C4 G3
        step = 0.22
        total = int(self.SAMPLE_RATE * (step * len(notes) + 0.40))
        w = np.zeros(total)
        for i, f in enumerate(notes):
            s = int(i * step * self.SAMPLE_RATE)
            n = int(step * self.SAMPLE_RATE)
            t = np.linspace(0, step, n)
            nw = (self._sin(f, t, 0.40)
                  + self._sin(f * 0.5, t, 0.12))  # 서브 배음으로 묵직하게
            nw *= self._exp_env(t, 3.5)
            w[s:s + n] += nw
        return w

    def _sfx_bonus_collect(self) -> "np.ndarray":
        """보너스 수집 - 밝은 화음"""
        t = self._t(0.28)
        w = (self._sin(880, t, 0.38)
             + self._sin(1100, t, 0.20)
             + self._sin(1760, t, 0.10))
        return w * self._exp_env(t, 11)

    def _sfx_menu_select(self) -> "np.ndarray":
        """메뉴 이동 - 짧은 클릭"""
        t = self._t(0.06)
        w = self._sin(600, t, 0.28)
        return w * self._exp_env(t, 55)

    def _sfx_achievement(self) -> "np.ndarray":
        """업적 달성 - 5음 승리 팡파레"""
        notes = [523, 659, 784, 659, 1047]  # C E G E C5
        step = 0.09
        total = int(self.SAMPLE_RATE * (step * len(notes) + 0.45))
        w = np.zeros(total)
        for i, f in enumerate(notes):
            s = int(i * step * self.SAMPLE_RATE)
            n = int(step * self.SAMPLE_RATE)
            t = np.linspace(0, step, n)
            nw = (self._sin(f, t, 0.42) + self._sin(f * 2, t, 0.15))
            nw *= self._exp_env(t, 8)
            w[s:s + n] += nw
        return w

    # ──────────────────────────────────────────
    # 사전 생성
    # ──────────────────────────────────────────

    def _pregenerate_sounds(self):
        generators = {
            'wall_bounce':    self._sfx_wall_bounce,
            'block_hit':      self._sfx_block_hit,
            'destroy_normal': self._sfx_destroy_normal,
            'destroy_bomb':   self._sfx_destroy_bomb,
            'destroy_shield': self._sfx_destroy_shield,
            'destroy_ghost':  self._sfx_destroy_ghost,
            'launch':         self._sfx_launch,
            'round_complete': self._sfx_round_complete,
            'game_over':      self._sfx_game_over,
            'bonus_collect':  self._sfx_bonus_collect,
            'menu_select':    self._sfx_menu_select,
            'achievement':    self._sfx_achievement,
        }
        for lvl in range(2, 15):
            generators[f'combo_{lvl}'] = lambda l=lvl: self._sfx_combo(l)

        for name, fn in generators.items():
            try:
                self.sounds[name] = self._to_sound(fn())
            except Exception as e:
                print(f"[Sound] '{name}' 생성 실패: {e}")

        print(f"[Sound] {len(self.sounds)}개 효과음 준비 완료")

    # ──────────────────────────────────────────
    # 재생 API
    # ──────────────────────────────────────────

    def play(self, name: str, volume: float = 1.0):
        if not self.enabled or not self.available:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                ch = pygame.mixer.find_channel()
                if ch:
                    ch.set_volume(volume)
                    ch.play(snd)
            except Exception:
                pass

    def play_combo(self, combo_count: int):
        level = min(combo_count, 14)
        self.play(f'combo_{level}', volume=0.85)

    def play_block_destroy(self, block_type: int):
        """block_type 상수에 따라 알맞은 파괴음 재생"""
        mapping = {
            0: 'destroy_normal',
            1: 'destroy_bomb',
            2: 'destroy_shield',
            3: 'destroy_ghost',
        }
        self.play(mapping.get(block_type, 'destroy_normal'))

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.stop_bgm()

    # ──────────────────────────────────────────
    # BGM 시스템
    # ──────────────────────────────────────────

    _BGM_TIERS = [
        # tier 0: 평화로운 (1~4라운드)
        {
            'bpm': 82,
            'scale': [261, 294, 330, 349, 392, 440, 494],  # C장조
            'melody': [0, 2, 4, 2, 0, 4, 2, 4],
            'bass_pattern': [0, 4, 3, 4],
            'kick': [0, 2], 'snare': [1, 3],
            'hihat_density': 0,
            'melody_vol': 0.18, 'bass_vol': 0.20, 'drum_vol': 0.18,
        },
        # tier 1: 활기 (5~9라운드)
        {
            'bpm': 105,
            'scale': [293, 330, 370, 392, 440, 494, 554],  # D장조
            'melody': [0, 4, 2, 6, 1, 5, 3, 6],
            'bass_pattern': [0, 4, 0, 5],
            'kick': [0, 2], 'snare': [1, 3],
            'hihat_density': 4,
            'melody_vol': 0.20, 'bass_vol': 0.22, 'drum_vol': 0.20,
        },
        # tier 2: 긴박 (10~19라운드)
        {
            'bpm': 128,
            'scale': [220, 247, 262, 294, 330, 370, 415],  # A단조
            'melody': [0, 5, 3, 6, 4, 2, 5, 1],
            'bass_pattern': [0, 3, 4, 3],
            'kick': [0, 1, 2, 3], 'snare': [1, 3],
            'hihat_density': 8,
            'melody_vol': 0.22, 'bass_vol': 0.24, 'drum_vol': 0.22,
        },
        # tier 3: 극한 긴박 (20라운드+)
        {
            'bpm': 158,
            'scale': [196, 220, 247, 262, 294, 311, 370],  # G단조
            'melody': [6, 5, 4, 6, 3, 5, 2, 4],
            'bass_pattern': [0, 5, 0, 6],
            'kick': [0, 1, 2, 3], 'snare': [0, 1, 2, 3],
            'hihat_density': 16,
            'melody_vol': 0.22, 'bass_vol': 0.24, 'drum_vol': 0.22,
        },
    ]

    def _get_tier(self, round_num: int) -> int:
        if round_num < 5:   return 0
        if round_num < 10:  return 1
        if round_num < 20:  return 2
        return 3

    def _build_bgm(self, tier_idx: int) -> "np.ndarray":
        cfg = self._BGM_TIERS[tier_idx]
        bpm = cfg['bpm']
        beat = 60.0 / bpm
        bar = beat * 4
        bar_n = int(self.SAMPLE_RATE * bar)
        wave = np.zeros(bar_n)

        scale = cfg['scale']
        note_dur = beat / 2  # 8분음표
        note_n = int(self.SAMPLE_RATE * note_dur)

        # ── 멜로디
        for i, idx in enumerate(cfg['melody']):
            s = int(i * note_n)
            e = min(s + note_n, bar_n)
            if s >= bar_n:
                break
            n = e - s
            t = np.linspace(0, note_dur, n)
            f = scale[idx % len(scale)]
            nw = (self._sin(f, t, cfg['melody_vol'])
                  + self._sin(f * 2, t, cfg['melody_vol'] * 0.35))
            env = np.ones(n)
            a = min(int(0.01 * self.SAMPLE_RATE), n // 4)
            r = min(int(0.06 * self.SAMPLE_RATE), n // 4)
            env[:a] = np.linspace(0, 1, a)
            env[-r:] = np.linspace(1, 0, r)
            wave[s:e] += nw * env

        # ── 베이스
        bass_pat = cfg['bass_pattern']
        for i, idx in enumerate(bass_pat):
            s = int(i * beat * self.SAMPLE_RATE)
            dur = beat * 0.8
            n = min(int(dur * self.SAMPLE_RATE), bar_n - s)
            if n <= 0:
                break
            t = np.linspace(0, dur, n)
            f = scale[idx % len(scale)] / 2.0  # 옥타브 아래
            bw = self._sin(f, t, cfg['bass_vol'])
            bw *= self._exp_env(t, 4)
            wave[s:s + n] += bw

        # ── 킥 드럼
        kick_vol = cfg['drum_vol']
        for beat_i in cfg['kick']:
            s = int(beat_i * beat * self.SAMPLE_RATE)
            dur = 0.12
            n = min(int(dur * self.SAMPLE_RATE), bar_n - s)
            if n <= 0:
                continue
            t = np.linspace(0, dur, n)
            kw = self._sweep(80, 35, t, kick_vol * 1.3)
            kw += self._noise(n, kick_vol * 0.15)
            kw *= self._exp_env(t, 28)
            wave[s:s + n] += kw

        # ── 스네어
        snare_vol = cfg['drum_vol'] * 0.7
        for beat_i in cfg['snare']:
            s = int(beat_i * beat * self.SAMPLE_RATE)
            dur = 0.09
            n = min(int(dur * self.SAMPLE_RATE), bar_n - s)
            if n <= 0:
                continue
            sw = self._noise(n, snare_vol)
            t = np.linspace(0, dur, n)
            sw += self._sin(220, t, snare_vol * 0.4)
            sw *= self._exp_env(t, 38)
            wave[s:s + n] += sw

        # ── 하이햇
        density = cfg['hihat_density']
        if density > 0:
            for j in range(density):
                s = int(j * bar_n / density)
                n = min(int(0.025 * self.SAMPLE_RATE), bar_n - s)
                if n <= 0:
                    break
                hw = self._noise(n, 0.07)
                t = np.linspace(0, 0.025, n)
                hw *= self._exp_env(t, 90)
                wave[s:s + n] += hw

        # 클리핑 방지
        peak = np.max(np.abs(wave))
        if peak > 0:
            wave = wave / peak * 0.58
        return wave

    def start_bgm(self, round_num: int = 1):
        """게임 BGM 시작 (같은 티어면 유지)"""
        if not self.enabled or not self.available:
            return
        tier = self._get_tier(round_num)
        if tier == self.current_bgm_tier:
            return  # 티어 동일 → 유지

        self.stop_bgm()
        self.current_bgm_tier = tier

        try:
            chunk = self._build_bgm(tier)
            self.bgm_sound = self._to_sound(chunk)
            self.bgm_sound.set_volume(0.28)
            self.bgm_channel = pygame.mixer.Channel(0)
            self.bgm_channel.play(self.bgm_sound, loops=-1)
        except Exception as e:
            print(f"[BGM] 재생 오류: {e}")

    def stop_bgm(self):
        """BGM 정지"""
        if self.bgm_channel:
            try:
                self.bgm_channel.stop()
            except Exception:
                pass
        self.bgm_channel = None
        self.bgm_sound = None
        self.current_bgm_tier = -1

    def update_bgm(self, round_num: int):
        """라운드 변경 시 BGM 티어 업데이트"""
        self.start_bgm(round_num)


# 전역 싱글톤
sound_manager = SoundManager()
