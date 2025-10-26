import requests
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.base import BaseParser, BaseLogger, VideoInfo, Comment
from ..core.config import config
from ..utils.helpers import extract_video_id


class VKParser(BaseParser):
    """Парсер комментариев ВКонтакте"""
    
    def __init__(self):
        self.logger = BaseLogger("VKParser")
        self.access_token = config.VK_ACCESS_TOKEN
        self.api_version = config.VK_API_VERSION
        self.base_url = "https://api.vk.com/method"
        
    def parse_video_info(self, video_url: str) -> Optional[VideoInfo]:
        """Получить информацию о видео по URL"""
        try:
            # Извлекаем video_id из URL
            video_id = extract_video_id(video_url)
            self.logger.debug(f"Извлеченный video_id: {video_id}")
            
            if not video_id:
                self.logger.error("Не удалось извлечь video_id из URL")
                return None
            
            if not self.access_token:
                self.logger.error("Отсутствует VK access token")
                return None
            
            # Используем полный video_id в параметре videos
            params = {
                'videos': video_id,
                'access_token': self.access_token,
                'v': self.api_version
            }
            
            self.logger.debug(f"Запрос к VK API: video.get с параметрами {params}")
            response = requests.get(f"{self.base_url}/video.get", params=params)
            data = response.json()
            
            self.logger.debug(f"Ответ VK API: {data}")
            
            if 'response' in data and data['response']['items']:
                video_data = data['response']['items'][0]
                
                # Создаем объект VideoInfo
                video_info = VideoInfo(
                    video_id=video_id,
                    title=video_data.get('title', 'Без названия'),
                    description=video_data.get('description', ''),
                    views=video_data.get('views', 0),
                    likes=video_data.get('likes', {}).get('count', 0),
                    comments_count=video_data.get('comments', 0),
                    duration=video_data.get('duration', 0),
                    date=datetime.fromtimestamp(video_data.get('date', 0)),
                    owner_id=video_data.get('owner_id', 0),
                    url=video_url
                )
                
                self.logger.success(f"Видео найдено: {video_info.title}")
                return video_info
            
            if 'error' in data:
                self.logger.error(f"Ошибка VK API: {data['error']}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о видео: {e}")
            return None
    
    def parse_comments(self, video_id: str, count: int) -> List[Comment]:
        """Получить комментарии к видео"""
        all_comments = []
        offset = 0
        max_per_request = config.MAX_COMMENTS_PER_REQUEST
        
        try:
            # Разбираем video_id на owner_id и video_id для API
            if '_' in video_id:
                owner_id, vid_id = video_id.split('_', 1)
            else:
                owner_id = None
                vid_id = video_id
            
            while len(all_comments) < count:
                remaining = count - len(all_comments)
                current_count = min(max_per_request, remaining)
                
                params = {
                    'owner_id': owner_id,
                    'video_id': int(vid_id),
                    'count': current_count,
                    'offset': offset,
                    'sort': 'desc',  # Новые комментарии сначала
                    'access_token': self.access_token,
                    'v': self.api_version
                }
                
                response = requests.get(f"{self.base_url}/video.getComments", params=params)
                data = response.json()
                
                if 'response' not in data:
                    self.logger.error(f"Ошибка API: {data}")
                    break
                
                comments_data = data['response'].get('items', [])
                if not comments_data:
                    break
                
                # Преобразуем данные комментариев в объекты Comment
                for comment_data in comments_data:
                    comment = Comment(
                        comment_id=str(comment_data.get('id', '')),
                        text=comment_data.get('text', ''),
                        author_id=str(comment_data.get('from_id', '')),
                        date=datetime.fromtimestamp(comment_data.get('date', 0)),
                        likes_count=comment_data.get('likes', {}).get('count', 0),
                        video_id=video_id
                    )
                    all_comments.append(comment)
                
                offset += len(comments_data)
                
                # Небольшая задержка между запросами
                time.sleep(0.5)
                
                self.logger.info(f"Получено комментариев: {len(all_comments)}")
            
            self.logger.success(f"Успешно получено {len(all_comments)} комментариев")
            return all_comments[:count]
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении комментариев: {e}")
            return all_comments
