import os
import random
import ctypes
from datetime import datetime, time, timedelta
import threading
import glob
import sys
import time as ttime
import urllib.request
import json

# Конфигурация
DAY_WALLPAPERS_DIR = r"C:\walpaperchanger\daywalpaper"
NIGHT_WALLPAPERS_DIR = r"C:\walpaperchanger\nightwalpaper"
lat = "56.109426"  # широта
lng = "47.185906"  # долгота
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".wallpaper_sun_times.json")

def get_sun_times():
    """Получает время восхода и заката через API используя urllib"""
    try:
        url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={lng}&date=today"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data['status'] != 'OK':
                raise Exception("API request failed")
            
            # Сохраняем данные в кэш
            with open(CACHE_FILE, 'w') as f:
                json.dump(data['results'], f)
                
            return data['results']['sunrise'], data['results']['sunset']
    except Exception as e:
        print(f"API error: {e}, using cached data")
        # Используем кэшированные данные при ошибке API
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cached_data = json.load(f)
                return cached_data['sunrise'], cached_data['sunset']
        # Fallback на дефолтные значения
        return "6:00:00 AM", "6:00:00 PM"

def parse_sun_time(time_str):
    """Преобразует время из строки в объект time"""
    try:
        return datetime.strptime(time_str, '%I:%M:%S %p').time()
    except:
        # Fallback на дефолтное время
        return time(6, 0)

def get_random_wallpaper(folder_path):
    """Возвращает случайный файл обоев из указанной папки"""
    wallpapers = glob.glob(os.path.join(folder_path, "**", "*.png"), recursive=True)
    
    if not wallpapers:
        raise FileNotFoundError(f"No PNG files found in {folder_path}")
    
    return random.choice(wallpapers)

def set_wallpaper(file_path):
    """Устанавливает обои в Windows"""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Wallpaper file not found: {file_path}")
    
    ctypes.windll.user32.SystemParametersInfoW(20, 0, file_path, 0)
    print(f"Wallpaper set: {file_path}")

def should_use_day_wallpaper(now):
    """Определяет, какие обои использовать сейчас"""
    sunrise_str, sunset_str = get_sun_times()
    sunrise_time = parse_sun_time(sunrise_str)
    sunset_time = parse_sun_time(sunset_str)
    
    now_time = now.time()
    
    # Если утро раньше вечера (обычный случай)
    if sunrise_time < sunset_time:
        return sunrise_time <= now_time < sunset_time
    
    # Если утро позже вечера (например, ночь с 21:00 до 4:00)
    return now_time >= sunrise_time or now_time < sunset_time

def schedule_next_change():
    """Планирует следующую смену обоев"""
    now = datetime.now()
    sunrise_str, sunset_str = get_sun_times()
    sunrise_time = parse_sun_time(sunrise_str)
    sunset_time = parse_sun_time(sunset_str)
    
    # Определяем следующее событие
    if should_use_day_wallpaper(now):
        next_event_time = datetime.combine(now.date(), sunset_time)
        wallpaper_type = "night"
    else:
        next_event_time = datetime.combine(now.date(), sunrise_time)
        wallpaper_type = "day"
        # Если событие уже прошло сегодня, планируем на завтра
        if next_event_time < now:
            next_event_time += timedelta(days=1)
    
    # Рассчитываем задержку в секундах
    delay = (next_event_time - now).total_seconds()
    
    # Планируем смену
    if delay > 0:
        threading.Timer(delay, lambda: change_wallpaper_and_reschedule(wallpaper_type)).start()
    
    print(f"Next change at {next_event_time} to {wallpaper_type} wallpaper")

def change_wallpaper_and_reschedule(wallpaper_type):
    """Меняет обои и планирует следующую смену"""
    try:
        if wallpaper_type == "day":
            wallpaper_path = get_random_wallpaper(DAY_WALLPAPERS_DIR)
        else:
            wallpaper_path = get_random_wallpaper(NIGHT_WALLPAPERS_DIR)
        
        set_wallpaper(wallpaper_path)
    except Exception as e:
        print(f"Error changing wallpaper: {e}")
    
    # Планируем следующую смену
    schedule_next_change()

def main():
    """Основная функция"""
    try:
        # Ожидаем 10 секунд перед установкой
        ttime.sleep(3)
        
        # Установка правильных обоев при запуске
        now = datetime.now()
        if should_use_day_wallpaper(now):
            wallpaper_path = get_random_wallpaper(DAY_WALLPAPERS_DIR)
            wallpaper_type = "day"
        else:
            wallpaper_path = get_random_wallpaper(NIGHT_WALLPAPERS_DIR)
            wallpaper_type = "night"
        
        set_wallpaper(wallpaper_path)
        print(f"Set {wallpaper_type} wallpaper at startup")
        
        # Планируем следующую смену
        schedule_next_change()
    except Exception as e:
        print(f"Startup error: {e}")
    
    # Держим скрипт активным
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
