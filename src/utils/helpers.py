import re
import json
from typing import Dict, Any, Optional


def extract_video_id(video_url: str) -> Optional[str]:
    """Извлечение video_id из URL ВК"""
    try:
        # Примеры URL:
        # https://vk.com/video123456_789
        # https://vk.com/video-123456_789
        # https://m.vk.com/video123456_789
        # https://vkvideo.ru/video-190452322_456239102
        
        if 'vk.com/video' in video_url:
            # Для стандартных URL vk.com
            video_part = video_url.split('video')[1]
            video_id = video_part.split('?')[0].split('&')[0]
            return video_id.strip('/')
        
        elif 'vkvideo.ru/video' in video_url:
            # Для URL vkvideo.ru - извлекаем после '/video'
            video_part = video_url.split('/video')[1]
            video_id = video_part.split('?')[0].split('&')[0]
            return video_id.strip('/')
        
        return None
        
    except Exception:
        return None


def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Извлечение JSON из текста с markdown разметкой"""
    try:
        # Ищем JSON блок между ```json и ```
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(1).strip()
        else:
            # Если нет markdown разметки, используем весь текст
            clean_text = text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]  # Убираем ```json
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]  # Убираем ```
        
        # Убираем комментарии (строки с //)
        lines = clean_text.split('\n')
        clean_lines = []
        for line in lines:
            if '//' in line:
                line = line[:line.index('//')]
            clean_lines.append(line.strip())
        
        clean_text = '\n'.join(clean_lines)
        
        return json.loads(clean_text)
        
    except (json.JSONDecodeError, AttributeError):
        return None


def parse_text_response(text: str) -> Dict[str, Any]:
    """Парсинг текстового ответа, если JSON не удался"""
    result = {
        'positive_count': 0,
        'negative_count': 0,
        'neutral_count': 0,
        'strong_points': [],
        'weak_points': [],
        'overall_sentiment_score': 5,
        'recommendations': []
    }
    
    # Ищем упоминания позитивных комментариев
    positive_match = re.search(r'позитивн[а-я]*\s*комментари[а-я]*[:\s]*(\d+)', text, re.IGNORECASE)
    if positive_match:
        result['positive_count'] = int(positive_match.group(1))
    
    # Ищем упоминания негативных комментариев
    negative_match = re.search(r'негативн[а-я]*\s*комментари[а-я]*[:\s]*(\d+)', text, re.IGNORECASE)
    if negative_match:
        result['negative_count'] = int(negative_match.group(1))
    
    # Ищем упоминания нейтральных комментариев
    neutral_match = re.search(r'нейтральн[а-я]*\s*комментари[а-я]*[:\s]*(\d+)', text, re.IGNORECASE)
    if neutral_match:
        result['neutral_count'] = int(neutral_match.group(1))
    
    # Ищем оценку настроения
    score_match = re.search(r'оценк[а-я]*\s*настроени[а-я]*[:\s]*(\d+)', text, re.IGNORECASE)
    if score_match:
        result['overall_sentiment_score'] = int(score_match.group(1))
    
    return result


def format_analysis_report(result: Dict[str, Any], video_info: Dict[str, Any]) -> str:
    """Форматирование отчета по анализу"""
    report = []
    report.append("=" * 60)
    report.append("📊 ОТЧЕТ ПО АНАЛИЗУ КОММЕНТАРИЕВ")
    report.append("=" * 60)
    
    report.append(f"\n🎥 Видео: {video_info.get('title', 'Без названия')}")
    report.append(f"👀 Просмотры: {video_info.get('views', 'Неизвестно')}")
    report.append(f"👍 Лайки: {video_info.get('likes', {}).get('count', 0)}")
    report.append(f"💬 Всего комментариев: {result.get('comments_count', 0)}")
    
    report.append(f"\n📈 АНАЛИЗ НАСТРОЕНИЯ:")
    report.append(f"😊 Позитивных: {result.get('positive_count', 0)}")
    report.append(f"😞 Негативных: {result.get('negative_count', 0)}")
    report.append(f"😐 Нейтральных: {result.get('neutral_count', 0)}")
    report.append(f"⭐ Общая оценка: {result.get('overall_sentiment_score', 0)}/10")
    
    strong_points = result.get('strong_points', [])
    if strong_points:
        report.append(f"\n💪 СИЛЬНЫЕ СТОРОНЫ:")
        for i, point in enumerate(strong_points, 1):
            report.append(f"  {i}. {point}")
    
    weak_points = result.get('weak_points', [])
    if weak_points:
        report.append(f"\n⚠️  СЛАБЫЕ СТОРОНЫ:")
        for i, point in enumerate(weak_points, 1):
            report.append(f"  {i}. {point}")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        report.append(f"\n💡 РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"  {i}. {rec}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)
