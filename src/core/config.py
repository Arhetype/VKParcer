import os
from dotenv import load_dotenv
from .base import BaseConfig, BaseLogger


class Config(BaseConfig):
    """Конфигурация приложения"""
    
    def __init__(self):
        self.logger = BaseLogger("Config")
        super().__init__()
    
    def load_config(self) -> None:
        """Загрузить конфигурацию из переменных окружения"""
        load_dotenv()
        
        # VK API настройки
        self.VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN')
        self.VK_API_VERSION = os.getenv('VK_API_VERSION', '5.131')
        
        # GigaChat API настройки
        self.GIGACHAT_CLIENT_ID = os.getenv('GIGACHAT_CLIENT_ID')
        self.GIGACHAT_CLIENT_SECRET = os.getenv('GIGACHAT_CLIENT_SECRET')
        self.GIGACHAT_SCOPE = os.getenv('GIGACHAT_SCOPE', 'GIGACHAT_API_PERS')
        
        # База данных
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'vk_comments_analysis.db')
        
        # Настройки парсинга
        self.MAX_COMMENTS_PER_REQUEST = int(os.getenv('MAX_COMMENTS_PER_REQUEST', '100'))
        self.MAX_COMMENTS_TOTAL = int(os.getenv('MAX_COMMENTS_TOTAL', '1000'))
        
        # Настройки анализа
        self.ANALYSIS_TEMPERATURE = float(os.getenv('ANALYSIS_TEMPERATURE', '0.7'))
        self.ANALYSIS_MAX_TOKENS = int(os.getenv('ANALYSIS_MAX_TOKENS', '2000'))
        
        # Промпт для анализа
        self.ANALYSIS_PROMPT = """
        Проанализируй следующие комментарии к видео и определи:
        
        1. Количество позитивных комментариев
        2. Количество негативных комментариев  
        3. Количество нейтральных комментариев
        4. Основные сильные стороны видео (по комментариям)
        5. Основные слабые стороны видео (по комментариям)
        6. Общую оценку настроения аудитории (от 1 до 10)
        7. Рекомендации по улучшению контента
        
        Комментарии:
        {comments}
        
        Ответ предоставь в формате JSON:
        {{
            "positive_count": число,
            "negative_count": число,
            "neutral_count": число,
            "strong_points": ["пункт1", "пункт2", ...],
            "weak_points": ["пункт1", "пункт2", ...],
            "overall_sentiment_score": число от 1 до 10,
            "recommendations": ["рекомендация1", "рекомендация2", ...]
        }}
        """
    
    def validate_config(self) -> bool:
        """Проверить корректность конфигурации"""
        errors = []
        
        if not self.VK_ACCESS_TOKEN:
            errors.append("VK_ACCESS_TOKEN не установлен")
        
        if not self.GIGACHAT_CLIENT_ID:
            errors.append("GIGACHAT_CLIENT_ID не установлен")
        
        if not self.GIGACHAT_CLIENT_SECRET:
            errors.append("GIGACHAT_CLIENT_SECRET не установлен")
        
        if errors:
            self.logger.error("Ошибки конфигурации:")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
        
        self.logger.success("Конфигурация загружена успешно")
        return True
    
    def debug_config(self) -> None:
        """Вывести отладочную информацию о конфигурации"""
        self.logger.info(f"VK_ACCESS_TOKEN загружен: {'Да' if self.VK_ACCESS_TOKEN else 'Нет'}")
        if self.VK_ACCESS_TOKEN:
            self.logger.info(f"Токен начинается с: {self.VK_ACCESS_TOKEN[:20]}...")
        
        self.logger.info(f"GIGACHAT_CLIENT_ID: {self.GIGACHAT_CLIENT_ID[:10] if self.GIGACHAT_CLIENT_ID else 'Не установлен'}...")
        self.logger.info(f"База данных: {self.DATABASE_PATH}")
        self.logger.info(f"Максимум комментариев: {self.MAX_COMMENTS_TOTAL}")


# Глобальный экземпляр конфигурации
config = Config()
