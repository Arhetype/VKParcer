"""
Интерактивный интерфейс для парсера комментариев ВК
"""

import os
from typing import Optional

from ..core.manager import CommentAnalyzer


class InteractiveCLI:
    """Интерактивный интерфейс"""
    
    def __init__(self):
        self.analyzer = CommentAnalyzer()
    
    def run(self) -> None:
        """Запуск интерактивного режима"""
        print("🚀 Парсер комментариев ВК с анализом через GigaChat")
        print("=" * 50)
        
        # Проверяем наличие .env файла
        if not os.path.exists('.env'):
            print("❌ Файл .env не найден!")
            print("Создайте файл .env на основе env_example.txt и заполните его данными:")
            print("- VK_ACCESS_TOKEN")
            print("- GIGACHAT_CLIENT_ID") 
            print("- GIGACHAT_CLIENT_SECRET")
            return
        
        # Инициализация
        if not self.analyzer.initialize():
            print("❌ Ошибка инициализации. Проверьте конфигурацию.")
            return
        
        while True:
            try:
                self.show_menu()
                choice = input("\nВыберите действие (1-5): ").strip()
                
                if choice == '1':
                    self.analyze_video()
                elif choice == '2':
                    self.show_statistics()
                elif choice == '3':
                    self.show_history()
                elif choice == '4':
                    self.show_help()
                elif choice == '5':
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                    
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        self.analyzer.cleanup()
    
    def show_menu(self) -> None:
        """Показать главное меню"""
        print("\n" + "=" * 30)
        print("📋 ГЛАВНОЕ МЕНЮ")
        print("=" * 30)
        print("1. 🔍 Анализ видео")
        print("2. 📊 Статистика")
        print("3. 📈 История анализов")
        print("4. ❓ Помощь")
        print("5. 🚪 Выход")
    
    def analyze_video(self) -> None:
        """Анализ видео"""
        print("\n" + "=" * 30)
        print("🔍 АНАЛИЗ ВИДЕО")
        print("=" * 30)
        
        # Запрашиваем URL видео
        video_url = input("📹 Введите URL видео ВК: ").strip()
        if not video_url:
            print("❌ URL не может быть пустым")
            return
        
        # Запрашиваем количество комментариев
        try:
            max_comments_input = input("📊 Максимальное количество комментариев (Enter для значения по умолчанию): ").strip()
            max_comments = int(max_comments_input) if max_comments_input else None
        except ValueError:
            max_comments = None
            print("⚠️  Используется значение по умолчанию")
        
        print(f"\n🎯 Начинаем анализ:")
        print(f"   URL: {video_url}")
        print(f"   Максимум комментариев: {max_comments or 'по умолчанию'}")
        
        # Подтверждение
        confirm = input("\n❓ Продолжить? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', 'да', 'д']:
            print("⏹️  Операция отменена")
            return
        
        # Запускаем анализ
        result = self.analyzer.analyze_video_comments(video_url, max_comments)
        
        if result.get('status') == 'success':
            self.analyzer.print_analysis_report(result)
            print(f"\n🎉 Анализ завершен! Результаты сохранены в базе данных.")
        else:
            print(f"\n❌ Ошибка при анализе: {result.get('error', 'Неизвестная ошибка')}")
    
    def show_statistics(self) -> None:
        """Показать статистику"""
        print("\n" + "=" * 30)
        print("📊 СТАТИСТИКА")
        print("=" * 30)
        
        self.analyzer.get_video_statistics()
    
    def show_history(self) -> None:
        """Показать историю анализов"""
        print("\n" + "=" * 30)
        print("📈 ИСТОРИЯ АНАЛИЗОВ")
        print("=" * 30)
        
        self.analyzer.get_analysis_history()
    
    def show_help(self) -> None:
        """Показать справку"""
        print("\n" + "=" * 30)
        print("❓ СПРАВКА")
        print("=" * 30)
        
        help_text = """
🔍 АНАЛИЗ ВИДЕО:
   - Введите URL видео ВК (поддерживаются форматы vk.com и vkvideo.ru)
   - Укажите количество комментариев для анализа
   - Получите детальный анализ настроения аудитории

📊 СТАТИСТИКА:
   - Показывает количество комментариев по каждому видео
   - Даты первого и последнего парсинга

📈 ИСТОРИЯ АНАЛИЗОВ:
   - Список всех проведенных анализов
   - Результаты анализа настроения
   - Даты проведения анализов

⚙️ НАСТРОЙКА:
   - Создайте файл .env с вашими токенами
   - VK_ACCESS_TOKEN - токен доступа к ВК API
   - GIGACHAT_CLIENT_ID и GIGACHAT_CLIENT_SECRET - данные GigaChat

📝 ПОДДЕРЖИВАЕМЫЕ URL:
   - https://vk.com/video123456_789
   - https://vkvideo.ru/video-190452322_456239102
   - https://m.vk.com/video123456_789
        """
        
        print(help_text)


def main():
    """Точка входа для интерактивного режима"""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
