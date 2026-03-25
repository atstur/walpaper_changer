import os
import random
import platform
import ctypes
from datetime import datetime, time, timedelta
import threading
import glob

# Конфигурация папок с обоями
DAY_WALLPAPERS_DIR = r"C:\walpaperchanger\daywalpaper"    # Папка с дневными обоями
NIGHT_WALLPAPERS_DIR = r"C:\walpaperchanger\nightwalpaper" # Папка с ночными обоями

# Ручное расписание по месяцам: [время_утра, время_вечера]
SCHEDULE = {
    1: (time(9, 0), time(17, 0)),   # Январь
    2: (time(8, 0), time(17, 30)), # Февраль
    3: (time(6, 30), time(18, 30)), # Март
    4: (time(5, 30), time(20, 0)), # Апрель
    5: (time(4, 30), time(21, 0)),   # Май
    6: (time(3, 30), time(21, 0)),   # Июнь
    7: (time(4, 0), time(21, 0)),   # Июль
    8: (time(4, 30), time(20, 30)), # Август
    9: (time(6, 0), time(19, 30)), # Сентябрь
    10: (time(7, 0), time(18, 0)),  # Октябрь
    11: (time(7, 30), time(17, 0)), # Ноябрь
    12: (time(8, 0), time(16, 30)), # Декабрь
}

def get_random_wallpaper(folder_path):
    """Возвращает случайный файл обоев из указанной папки"""
    # Получаем все PNG файлы в папке и подпапках
    wallpapers = glob.glob(os.path.join(folder_path, "**", "*.png"), recursive=True)
    
    if not wallpapers:
        raise FileNotFoundError(f"В папке {folder_path} не найдены PNG файлы")
    
    return random.choice(wallpapers)

def set_wallpaper(file_path):
    """Устанавливает обои в Windows 10"""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Файл обоев не найден: {file_path}")
    
    # Устанавливаем обои через WinAPI
    ctypes.windll.user32.SystemParametersInfoW(20, 0, file_path, 0)
    print(f"Установлены обои: {file_path}")

def get_day_night_times():
    """Возвращает время смены для текущего месяца"""
    now = datetime.now()
    month = now.month
    return SCHEDULE.get(month, (time(6, 0), time(18, 0)))  # По умолчанию 6:00 и 18:00

def should_use_day_wallpaper(now):
    """Определяет, какие обои использовать сейчас"""
    morning_time, evening_time = get_day_night_times()
    now_time = now.time()
    
    # Если утро раньше вечера (обычный случай)
    if morning_time < evening_time:
        return morning_time <= now_time < evening_time
    
    # Если утро позже вечера (например, ночь с 21:00 до 4:00)
    return now_time >= morning_time or now_time < evening_time

def schedule_next_change():
    """Планирует следующую смену обоев"""
    now = datetime.now()
    morning_time, evening_time = get_day_night_times()
    
    # Определяем следующее событие
    if should_use_day_wallpaper(now):
        next_event_time = datetime.combine(now.date(), evening_time)
        wallpaper_type = "night"
    else:
        next_event_time = datetime.combine(now.date(), morning_time)
        wallpaper_type = "day"
        # Если событие уже прошло сегодня, планируем на завтра
        if next_event_time < now:
            next_event_time += timedelta(days=1)
    
    # Рассчитываем задержку в секундах
    delay = (next_event_time - now).total_seconds()
    
    # Планируем смену
    if delay > 0:
        threading.Timer(delay, lambda: change_wallpaper_and_reschedule(wallpaper_type)).start()
    
    print(f"Следующая смена в {next_event_time} на {wallpaper_type} обои")

def change_wallpaper_and_reschedule(wallpaper_type):
    """Меняет обои и планирует следующую смену"""
    try:
        # Выбираем случайные обои в зависимости от типа
        if wallpaper_type == "day":
            wallpaper_path = get_random_wallpaper(DAY_WALLPAPERS_DIR)
        else:
            wallpaper_path = get_random_wallpaper(NIGHT_WALLPAPERS_DIR)
        
        set_wallpaper(wallpaper_path)
    except Exception as e:
        print(f"Ошибка при смене обоев: {e}")
    
    # Планируем следующую смену
    schedule_next_change()

def main():
    """Основная функция"""
    # Установка обоев при запуске
    try:
        wallpaper_type = "day" if should_use_day_wallpaper(datetime.now()) else "night"
        change_wallpaper_and_reschedule(wallpaper_type)
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
    
    # Держим скрипт активным
    threading.Event().wait()

if __name__ == "__main__":
    main()
