from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseManager, BaseLogger
from ..core.config import config
from ..parsers.vk_parser import VKParser
from ..analyzers.gigachat_analyzer import GigaChatAnalyzer
from ..database.manager import DatabaseManager
from ..utils.helpers import format_analysis_report


class CommentAnalyzer(BaseManager):
    """Основной менеджер для анализа комментариев"""
    
    def __init__(self):
        super().__init__(BaseLogger("CommentAnalyzer"))
        self.vk_parser = None
        self.giga_analyzer = None
        self.db_manager = None
    
    def initialize(self) -> bool:
        """Инициализация менеджера"""
        try:
            # Проверяем конфигурацию
            if not config.validate_config():
                return False
            
            # Инициализируем компоненты
            self.vk_parser = VKParser()
            self.giga_analyzer = GigaChatAnalyzer()
            self.db_manager = DatabaseManager()
            
            self.logger.success("Менеджер инициализирован успешно")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации менеджера: {e}")
            return False
    
    def analyze_video_comments(self, video_url: str, max_comments: int = None) -> Dict[str, Any]:
        """Полный анализ комментариев к видео"""
        if max_comments is None:
            max_comments = config.MAX_COMMENTS_TOTAL
        
        self.logger.info(f"Начинаем анализ видео: {video_url}")
        self.logger.info(f"Максимальное количество комментариев: {max_comments}")
        
        try:
            # Шаг 1: Парсинг информации о видео
            self.logger.info("Шаг 1: Получение информации о видео...")
            video_info = self.vk_parser.parse_video_info(video_url)
            
            if not video_info:
                self.logger.error("Не удалось получить информацию о видео")
                return {}
            
            # Шаг 2: Парсинг комментариев
            self.logger.info("Шаг 2: Парсинг комментариев...")
            comments = self.vk_parser.parse_comments(video_info.video_id, max_comments)
            
            if not comments:
                self.logger.error("Комментарии не найдены")
                return {}
            
            # Шаг 3: Сохранение данных в БД
            self.logger.info("Шаг 3: Сохранение данных в базу...")
            self.db_manager.save_video_info(video_info)
            self.db_manager.save_comments(comments)
            
            # Шаг 4: Подготовка комментариев для анализа
            self.logger.info("Шаг 4: Подготовка комментариев для анализа...")
            comments_texts = [comment.text for comment in comments if comment.text.strip()]
            
            if not comments_texts:
                self.logger.error("Нет текстовых комментариев для анализа")
                return {
                    'video_info': video_info,
                    'video_id': video_info.video_id,
                    'comments_count': len(comments),
                    'status': 'no_text_comments'
                }
            
            self.logger.info(f"Готово к анализу: {len(comments_texts)} комментариев")
            
            # Шаг 5: Анализ через GigaChat
            self.logger.info("Шаг 5: Анализ комментариев через GigaChat...")
            analysis_data = self.giga_analyzer.analyze_comments(comments_texts)
            
            if not analysis_data:
                self.logger.error("Не удалось получить анализ от GigaChat")
                return {
                    'video_info': video_info,
                    'video_id': video_info.video_id,
                    'comments_count': len(comments),
                    'status': 'analysis_failed'
                }
            
            # Шаг 6: Сохранение результатов анализа
            self.logger.info("Шаг 6: Сохранение результатов анализа...")
            from ..core.base import AnalysisResult
            
            analysis_result = AnalysisResult(
                video_id=video_info.video_id,
                positive_count=analysis_data.get('positive_count', 0),
                negative_count=analysis_data.get('negative_count', 0),
                neutral_count=analysis_data.get('neutral_count', 0),
                strong_points=analysis_data.get('strong_points', []),
                weak_points=analysis_data.get('weak_points', []),
                overall_sentiment_score=analysis_data.get('overall_sentiment_score', 0),
                recommendations=analysis_data.get('recommendations', []),
                analysis_date=datetime.now(),
                raw_analysis=analysis_data
            )
            
            self.db_manager.save_analysis_result(analysis_result)
            
            # Формируем итоговый результат
            result = {
                'video_info': video_info,
                'video_id': video_info.video_id,
                'comments_count': len(comments),
                'analysis': analysis_data,
                'status': 'success'
            }
            
            self.logger.success("Анализ завершен успешно!")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении анализа: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def print_analysis_report(self, result: Dict[str, Any]) -> None:
        """Вывод отчета по анализу"""
        if not result or result.get('status') != 'success':
            self.logger.error("Нет данных для отчета")
            return
        
        video_info = result['video_info']
        analysis = result['analysis']
        
        # Формируем данные для отчета
        report_data = {
            'comments_count': result['comments_count'],
            'positive_count': analysis.get('positive_count', 0),
            'negative_count': analysis.get('negative_count', 0),
            'neutral_count': analysis.get('neutral_count', 0),
            'overall_sentiment_score': analysis.get('overall_sentiment_score', 0),
            'strong_points': analysis.get('strong_points', []),
            'weak_points': analysis.get('weak_points', []),
            'recommendations': analysis.get('recommendations', [])
        }
        
        video_data = {
            'title': video_info.title,
            'views': video_info.views,
            'likes': {'count': video_info.likes}
        }
        
        report = format_analysis_report(report_data, video_data)
        print(report)
    
    def get_video_statistics(self) -> None:
        """Получить статистику по видео"""
        statistics = self.db_manager.get_video_statistics()
        
        if not statistics:
            self.logger.info("Нет сохраненных данных")
            return
        
        print("💬 КОЛИЧЕСТВО КОММЕНТАРИЕВ ПО ВИДЕО")
        print("=" * 60)
        
        for stat in statistics:
            print(f"\n🎥 Видео ID: {stat['video_id']}")
            print(f"   💬 Комментариев: {stat['comment_count']}")
            print(f"   📅 Первый парсинг: {stat['first_parsed']}")
            print(f"   📅 Последний парсинг: {stat['last_parsed']}")
    
    def get_analysis_history(self) -> None:
        """Получить историю анализов"""
        history = self.db_manager.get_analysis_history()
        
        if not history:
            self.logger.info("Нет сохраненных анализов")
            return
        
        print("📊 ИСТОРИЯ АНАЛИЗОВ")
        print("=" * 80)
        
        for i, analysis in enumerate(history, 1):
            video_id = analysis['video_id']
            analysis_date = analysis['analysis_date']
            pos = analysis['positive_count']
            neg = analysis['negative_count']
            neutral = analysis['neutral_count']
            score = analysis['overall_sentiment_score']
            total = pos + neg + neutral
            
            print(f"\n{i}. Видео ID: {video_id}")
            print(f"   📅 Дата анализа: {analysis_date}")
            print(f"   📈 Настроение: 😊{pos} 😞{neg} 😐{neutral} (всего: {total})")
            print(f"   ⭐ Общая оценка: {score}/10")
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.logger.info("Очистка ресурсов...")
        # Здесь можно добавить логику очистки, если необходимо
