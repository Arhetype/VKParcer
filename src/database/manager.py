"""
Менеджер базы данных
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base import BaseDatabase, VideoInfo, Comment, AnalysisResult, BaseLogger
from ..core.config import config


class DatabaseManager(BaseDatabase):
    """Менеджер базы данных SQLite"""
    
    def __init__(self):
        self.logger = BaseLogger("DatabaseManager")
        self.db_path = config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица для хранения информации о видео
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    duration INTEGER DEFAULT 0,
                    date_created TIMESTAMP,
                    owner_id INTEGER,
                    url TEXT,
                    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица для хранения комментариев
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    comment_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    author_id TEXT,
                    date_created TIMESTAMP,
                    likes_count INTEGER DEFAULT 0,
                    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(video_id, comment_id),
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Таблица для хранения результатов анализа
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    positive_count INTEGER,
                    negative_count INTEGER,
                    neutral_count INTEGER,
                    strong_points TEXT,  -- JSON array
                    weak_points TEXT,    -- JSON array
                    overall_sentiment_score REAL,
                    recommendations TEXT, -- JSON array
                    raw_analysis TEXT,   -- Полный ответ от GigaChat
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.success("База данных инициализирована успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации базы данных: {e}")
    
    def save_video_info(self, video_info: VideoInfo) -> None:
        """Сохранить информацию о видео"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (video_id, title, description, views, likes, comments_count, 
                 duration, date_created, owner_id, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_info.video_id,
                video_info.title,
                video_info.description,
                video_info.views,
                video_info.likes,
                video_info.comments_count,
                video_info.duration,
                video_info.date,
                video_info.owner_id,
                video_info.url
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Информация о видео сохранена: {video_info.title}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении информации о видео: {e}")
    
    def save_comments(self, comments: List[Comment]) -> None:
        """Сохранить комментарии"""
        if not comments:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for comment in comments:
                cursor.execute('''
                    INSERT OR REPLACE INTO comments 
                    (video_id, comment_id, text, author_id, date_created, likes_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    comment.video_id,
                    comment.comment_id,
                    comment.text,
                    comment.author_id,
                    comment.date,
                    comment.likes_count
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Сохранено {len(comments)} комментариев")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении комментариев: {e}")
    
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """Сохранить результат анализа"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_results 
                (video_id, positive_count, negative_count, neutral_count, 
                 strong_points, weak_points, overall_sentiment_score, 
                 recommendations, raw_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.video_id,
                result.positive_count,
                result.negative_count,
                result.neutral_count,
                json.dumps(result.strong_points, ensure_ascii=False),
                json.dumps(result.weak_points, ensure_ascii=False),
                result.overall_sentiment_score,
                json.dumps(result.recommendations, ensure_ascii=False),
                json.dumps(result.raw_analysis, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.success("Результат анализа сохранен")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата анализа: {e}")
    
    def get_comments_for_analysis(self, video_id: str) -> List[str]:
        """Получить комментарии для анализа"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT text FROM comments 
                WHERE video_id = ? AND text != ''
                ORDER BY parsed_at DESC
            ''', (video_id,))
            
            comments = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"Получено {len(comments)} комментариев для анализа")
            return comments
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении комментариев: {e}")
            return []
    
    def get_latest_analysis(self, video_id: str) -> Optional[AnalysisResult]:
        """Получить последний анализ для видео"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM analysis_results 
                WHERE video_id = ? 
                ORDER BY analysis_date DESC 
                LIMIT 1
            ''', (video_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                analysis_result = AnalysisResult(
                    video_id=result[1],
                    positive_count=result[3],
                    negative_count=result[4],
                    neutral_count=result[5],
                    strong_points=json.loads(result[6]) if result[6] else [],
                    weak_points=json.loads(result[7]) if result[7] else [],
                    overall_sentiment_score=result[8],
                    recommendations=json.loads(result[9]) if result[9] else [],
                    analysis_date=result[2],
                    raw_analysis=json.loads(result[10]) if result[10] else {}
                )
                
                self.logger.info(f"Найден анализ для видео {video_id}")
                return analysis_result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении анализа: {e}")
            return None
    
    def get_video_statistics(self) -> List[Dict[str, Any]]:
        """Получить статистику по видео"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT video_id, COUNT(*) as comment_count, 
                       MIN(parsed_at) as first_parsed,
                       MAX(parsed_at) as last_parsed
                FROM comments 
                GROUP BY video_id 
                ORDER BY comment_count DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            statistics = []
            for video_id, count, first, last in results:
                statistics.append({
                    'video_id': video_id,
                    'comment_count': count,
                    'first_parsed': first,
                    'last_parsed': last
                })
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики: {e}")
            return []
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Получить историю анализов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT video_id, analysis_date, positive_count, negative_count, 
                       neutral_count, overall_sentiment_score
                FROM analysis_results 
                ORDER BY analysis_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            history = []
            for result in results:
                history.append({
                    'video_id': result[0],
                    'analysis_date': result[1],
                    'positive_count': result[2],
                    'negative_count': result[3],
                    'neutral_count': result[4],
                    'overall_sentiment_score': result[5]
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении истории: {e}")
            return []
