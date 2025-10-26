"""
Анализатор комментариев через GigaChat
"""

import requests
import json
import time
import uuid
import base64
from typing import Dict, Any, List

from ..core.base import BaseAnalyzer, BaseLogger
from ..core.config import config
from ..utils.helpers import parse_json_from_text, parse_text_response

# Подавляем SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GigaChatAnalyzer(BaseAnalyzer):
    """Анализатор комментариев через GigaChat"""
    
    def __init__(self):
        self.logger = BaseLogger("GigaChatAnalyzer")
        self.client_id = config.GIGACHAT_CLIENT_ID
        self.client_secret = config.GIGACHAT_CLIENT_SECRET
        self.scope = config.GIGACHAT_SCOPE
        self.access_token = None
        self.token_expires_at = 0
        
    def _get_access_token(self) -> str:
        """Получение токена доступа для GigaChat API"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            # Шаг 1: Получение access token
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            # Генерируем уникальный RqUID
            rquid = str(uuid.uuid4())
            
            # Кодируем credentials для Basic Auth
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            
            payload = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': rquid,
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            self.logger.debug(f"Запрос токена GigaChat с RqUID: {rquid}")
            self.logger.debug(f"Кодируем credentials: {self.client_id[:10]}...:{self.client_secret[:10]}...")
            
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)
            
            self.logger.debug(f"Ответ GigaChat OAuth: {response.status_code}")
            if response.text:
                self.logger.debug(f"Тело ответа: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' in token_data:
                    self.access_token = token_data['access_token']
                    # Токен действует обычно 30 минут
                    self.token_expires_at = time.time() + 1800
                    self.logger.success("Токен GigaChat получен успешно")
                    return self.access_token
                else:
                    self.logger.error(f"Токен не найден в ответе: {token_data}")
                    return None
            else:
                self.logger.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении токена доступа: {e}")
            return None
    
    def analyze_comments(self, comments: List[str]) -> Dict[str, Any]:
        """Анализ комментариев с помощью GigaChat"""
        if not comments:
            return {}
        
        # Получаем токен доступа
        token = self._get_access_token()
        if not token:
            self.logger.error("Не удалось получить токен доступа для GigaChat")
            return {}
        
        try:
            # Шаг 2: Запрос к LLM через новый API
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            
            # Подготавливаем комментарии для анализа
            comments_text = "\n".join([f"{i+1}. {comment}" for i, comment in enumerate(comments)])
            
            # Формируем промпт
            prompt = config.ANALYSIS_PROMPT.format(comments=comments_text)
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            payload = {
                "model": "GigaChat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": config.ANALYSIS_TEMPERATURE,
                "top_p": 0.9,
                "n": 1,
                "stream": False,
                "max_tokens": config.ANALYSIS_MAX_TOKENS
            }
            
            self.logger.info("Отправляем запрос на анализ комментариев в GigaChat...")
            self.logger.debug(f"URL: {url}")
            self.logger.debug(f"Используем токен: {token[:20]}...")
            
            response = requests.request("POST", url, headers=headers, json=payload, verify=False)
            
            self.logger.debug(f"Ответ GigaChat API: {response.status_code}")
            if response.text:
                self.logger.debug(f"Тело ответа: {response.text[:500]}...")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'choices' in result and result['choices']:
                    choice = result['choices'][0]
                    analysis_text = choice['message']['content']
                    
                    # Проверяем, не заблокирован ли запрос
                    if choice.get('finish_reason') == 'blacklist':
                        self.logger.warning("GigaChat заблокировал анализ этого контента")
                        self.logger.info("Попробуем использовать упрощенный анализ...")
                        return self._simple_sentiment_analysis(comments)
                    
                    # Пытаемся распарсить JSON ответ
                    analysis_data = parse_json_from_text(analysis_text)
                    if analysis_data:
                        self.logger.success("Анализ комментариев завершен успешно")
                        return analysis_data
                    else:
                        self.logger.warning("Ошибка парсинга JSON ответа от GigaChat")
                        self.logger.debug(f"Ответ: {analysis_text}")
                        return parse_text_response(analysis_text)
                else:
                    self.logger.error("Неожиданный формат ответа от GigaChat")
                    return {}
            else:
                self.logger.error(f"Ошибка API GigaChat: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Ошибка при анализе комментариев: {e}")
            return {}
    
    def _simple_sentiment_analysis(self, comments: List[str]) -> Dict[str, Any]:
        """Упрощенный анализ настроения на основе ключевых слов"""
        positive_keywords = [
            'классный', 'отличный', 'супер', 'крутой', 'замечательный', 'прекрасный',
            'хороший', 'великолепный', 'потрясающий', 'восхитительный', 'блестящий',
            'люблю', 'нравится', 'обожаю', 'рекомендую', 'браво', 'ура', 'вау'
        ]
        
        negative_keywords = [
            'плохой', 'ужасный', 'отвратительный', 'говно', 'позорище', 'гадость',
            'не нравится', 'не люблю', 'ненавижу', 'отвратительно', 'мерзость',
            'скучный', 'тупой', 'глупый', 'бесполезный', 'разочарование'
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        strong_points = []
        weak_points = []
        
        for comment in comments:
            comment_lower = comment.lower()
            
            # Проверяем позитивные ключевые слова
            has_positive = any(keyword in comment_lower for keyword in positive_keywords)
            has_negative = any(keyword in comment_lower for keyword in negative_keywords)
            
            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Определяем сильные и слабые стороны
        if positive_count > negative_count:
            strong_points.append("положительные отзывы преобладают")
        if negative_count > positive_count:
            weak_points.append("отрицательные отзывы преобладают")
        
        # Рассчитываем общую оценку
        total = positive_count + negative_count + neutral_count
        if total > 0:
            sentiment_ratio = (positive_count - negative_count) / total
            overall_score = max(1, min(10, int(5 + sentiment_ratio * 5)))
        else:
            overall_score = 5
        
        result = {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'strong_points': strong_points,
            'weak_points': weak_points,
            'overall_sentiment_score': overall_score,
            'recommendations': [
                "анализ выполнен на основе ключевых слов",
                "для более точного анализа рекомендуется использовать полный анализ GigaChat"
            ]
        }
        
        self.logger.info("Выполнен упрощенный анализ на основе ключевых слов")
        return result
