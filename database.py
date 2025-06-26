#!/usr/bin/env python3
"""
데이터베이스 모듈
SQLite를 사용한 점수 랭킹 시스템
"""

import sqlite3
import os
import datetime
from typing import List, Tuple, Optional


class DatabaseManager:
    def __init__(self, db_path: str = "spinball_scores.db"):
        """데이터베이스 매니저 초기화"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 점수 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        round_reached INTEGER NOT NULL,
                        balls_count INTEGER NOT NULL,
                        play_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성 (성능 향상)
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_score 
                    ON scores(score DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_date 
                    ON scores(play_date DESC)
                ''')
                
                conn.commit()
                print("데이터베이스가 성공적으로 초기화되었습니다.")
                
        except sqlite3.Error as e:
            print(f"데이터베이스 초기화 오류: {e}")
    
    def save_score(self, player_name: str, score: int, round_reached: int, balls_count: int) -> bool:
        """점수 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO scores (player_name, score, round_reached, balls_count)
                    VALUES (?, ?, ?, ?)
                ''', (player_name, score, round_reached, balls_count))
                
                conn.commit()
                print(f"점수 저장 완료: {player_name} - {score}점")
                return True
                
        except sqlite3.Error as e:
            print(f"점수 저장 오류: {e}")
            return False
    
    def get_top_scores(self, limit: int = 10) -> List[Tuple[str, int, int, int, str]]:
        """상위 점수 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT player_name, score, round_reached, balls_count, 
                           datetime(play_date, 'localtime') as formatted_date
                    FROM scores 
                    ORDER BY score DESC, round_reached DESC, play_date DESC
                    LIMIT ?
                ''', (limit,))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            print(f"점수 조회 오류: {e}")
            return []
    
    def get_player_best_score(self, player_name: str) -> Optional[Tuple[int, int, int, str]]:
        """특정 플레이어의 최고 점수 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT score, round_reached, balls_count, 
                           datetime(play_date, 'localtime') as formatted_date
                    FROM scores 
                    WHERE player_name = ?
                    ORDER BY score DESC, round_reached DESC, play_date DESC
                    LIMIT 1
                ''', (player_name,))
                
                result = cursor.fetchone()
                return result if result else None
                
        except sqlite3.Error as e:
            print(f"플레이어 점수 조회 오류: {e}")
            return None
    
    def get_total_games_played(self) -> int:
        """총 게임 플레이 횟수 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM scores')
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            print(f"게임 횟수 조회 오류: {e}")
            return 0
    
    def clear_all_scores(self) -> bool:
        """모든 점수 데이터 삭제 (관리자 기능)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM scores')
                conn.commit()
                print("모든 점수 데이터가 삭제되었습니다.")
                return True
                
        except sqlite3.Error as e:
            print(f"데이터 삭제 오류: {e}")
            return False
    
    def get_database_stats(self) -> dict:
        """데이터베이스 통계 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 총 게임 수
                cursor.execute('SELECT COUNT(*) FROM scores')
                total_games = cursor.fetchone()[0]
                
                # 최고 점수
                cursor.execute('SELECT MAX(score) FROM scores')
                highest_score = cursor.fetchone()[0] or 0
                
                # 평균 점수
                cursor.execute('SELECT AVG(score) FROM scores')
                avg_score = cursor.fetchone()[0] or 0
                
                # 최고 라운드
                cursor.execute('SELECT MAX(round_reached) FROM scores')
                highest_round = cursor.fetchone()[0] or 0
                
                # 플레이어 수
                cursor.execute('SELECT COUNT(DISTINCT player_name) FROM scores')
                unique_players = cursor.fetchone()[0]
                
                return {
                    'total_games': total_games,
                    'highest_score': highest_score,
                    'average_score': round(avg_score, 1),
                    'highest_round': highest_round,
                    'unique_players': unique_players
                }
                
        except sqlite3.Error as e:
            print(f"통계 조회 오류: {e}")
            return {
                'total_games': 0,
                'highest_score': 0,
                'average_score': 0,
                'highest_round': 0,
                'unique_players': 0
            }


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager() 