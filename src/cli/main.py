"""
CLI интерфейс для парсера комментариев ВК
"""

import argparse
import sys
from typing import Optional

from ..core.manager import CommentAnalyzer


class CLI:
    """Командная строка интерфейс"""
    
    def __init__(self):
        self.analyzer = CommentAnalyzer()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Создать парсер аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Парсер комментариев ВК с анализом через GigaChat',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  %(prog)s "https://vkvideo.ru/video-190452322_456239102"
  %(prog)s "https://vk.com/video123456_789" --max-comments 500
  %(prog)s --stats
  %(prog)s --history
            """
        )
        
        # Основная команда
        parser.add_argument(
            'video_url',
            nargs='?',
            help='URL видео ВК для анализа'
        )
        
        # Опции
        parser.add_argument(
            '--max-comments',
            type=int,
            default=None,
            help='Максимальное количество комментариев для анализа'
        )
        
        parser.add_argument(
            '--no-report',
            action='store_true',
            help='Не выводить отчет по анализу'
        )
        
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показать статистику по сохраненным видео'
        )
        
        parser.add_argument(
            '--history',
            action='store_true',
            help='Показать историю анализов'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Запуск CLI"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Инициализация
            if not self.analyzer.initialize():
                return 1
            
            # Обработка команд
            if parsed_args.stats:
                self.analyzer.get_video_statistics()
                return 0
            
            if parsed_args.history:
                self.analyzer.get_analysis_history()
                return 0
            
            if not parsed_args.video_url:
                parser.print_help()
                return 1
            
            # Анализ видео
            result = self.analyzer.analyze_video_comments(
                parsed_args.video_url,
                parsed_args.max_comments
            )
            
            if result.get('status') == 'success':
                if not parsed_args.no_report:
                    self.analyzer.print_analysis_report(result)
                
                print(f"\n🎉 Анализ завершен! Результаты сохранены в базе данных.")
                return 0
            else:
                print(f"\n❌ Ошибка при выполнении анализа: {result.get('error', 'Неизвестная ошибка')}")
                return 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Анализ прерван пользователем")
            return 1
        except Exception as e:
            print(f"\n❌ Неожиданная ошибка: {e}")
            return 1
        finally:
            self.analyzer.cleanup()


def main():
    """Точка входа для CLI"""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
