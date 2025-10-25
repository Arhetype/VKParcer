"""
Базовые классы и интерфейсы для парсера комментариев ВК
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VideoInfo:
    """Информация о видео"""
    video_id: str
    title: str
    description: str
    views: int
    likes: int
    comments_count: int
    duration: int
    date: datetime
    owner_id: int
    url: str


@dataclass
class Comment:
    """Комментарий к видео"""
    comment_id: str
    text: str
    author_id: str
    date: datetime
    likes_count: int
    video_id: str


@dataclass
class AnalysisResult:
    """Результат анализа комментариев"""
    video_id: str
    positive_count: int
    negative_count: int
    neutral_count: int
    strong_points: List[str]
    weak_points: List[str]
    overall_sentiment_score: float
    recommendations: List[str]
    analysis_date: datetime
    raw_analysis: Dict[str, Any]


class BaseParser(ABC):
    """Базовый класс для парсеров"""
    
    @abstractmethod
    def parse_video_info(self, video_url: str) -> Optional[VideoInfo]:
        """Получить информацию о видео"""
        pass
    
    @abstractmethod
    def parse_comments(self, video_id: str, count: int) -> List[Comment]:
        """Получить комментарии к видео"""
        pass


class BaseAnalyzer(ABC):
    """Базовый класс для анализаторов"""
    
    @abstractmethod
    def analyze_comments(self, comments: List[str]) -> Dict[str, Any]:
        """Анализировать комментарии"""
        pass


class BaseDatabase(ABC):
    """Базовый класс для работы с базой данных"""
    
    @abstractmethod
    def save_video_info(self, video_info: VideoInfo) -> None:
        """Сохранить информацию о видео"""
        pass
    
    @abstractmethod
    def save_comments(self, comments: List[Comment]) -> None:
        """Сохранить комментарии"""
        pass
    
    @abstractmethod
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """Сохранить результат анализа"""
        pass
    
    @abstractmethod
    def get_comments_for_analysis(self, video_id: str) -> List[str]:
        """Получить комментарии для анализа"""
        pass
    
    @abstractmethod
    def get_latest_analysis(self, video_id: str) -> Optional[AnalysisResult]:
        """Получить последний анализ"""
        pass


class BaseConfig:
    """Базовый класс конфигурации"""
    
    def __init__(self):
        self.load_config()
    
    @abstractmethod
    def load_config(self) -> None:
        """Загрузить конфигурацию"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Проверить корректность конфигурации"""
        pass


class BaseLogger:
    """Базовый класс для логирования"""
    
    def __init__(self, name: str):
        self.name = name
    
    def info(self, message: str) -> None:
        """Информационное сообщение"""
        print(f"ℹ️  [{self.name}] {message}")
    
    def success(self, message: str) -> None:
        """Сообщение об успехе"""
        print(f"✅ [{self.name}] {message}")
    
    def warning(self, message: str) -> None:
        """Предупреждение"""
        print(f"⚠️  [{self.name}] {message}")
    
    def error(self, message: str) -> None:
        """Ошибка"""
        print(f"❌ [{self.name}] {message}")
    
    def debug(self, message: str) -> None:
        """Отладочное сообщение"""
        print(f"🔍 [{self.name}] {message}")


class BaseManager:
    """Базовый класс для менеджеров"""
    
    def __init__(self, logger: BaseLogger):
        self.logger = logger
    
    def initialize(self) -> bool:
        """Инициализация менеджера"""
        return True
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        pass
