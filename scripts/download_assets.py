import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin

def download_dungeon_scrawl_assets():
    # URL сайту
    url = "https://app.dungeonscrawl.com"
    
    # Створюємо папку для зображень, якщо вона не існує
    save_path = os.path.join('static', 'sprites', 'dungeon_scrawl')
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    try:
        # Отримуємо HTML-контент сторінки
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Знаходимо всі div з класом css-kpnz4m
        asset_divs = soup.find_all('div', class_='css-kpnz4m')
        
        for div in asset_divs:
            # Знаходимо зображення
            img = div.find('img')
            if img and img.get('src'):
                # Отримуємо назву з input
                name_input = div.find('input', class_='css-1cpmr3p')
                asset_name = name_input.get('value') if name_input else 'unnamed_asset'
                
                # Формуємо повний URL зображення
                img_url = urljoin(url, img['src'])
                
                # Завантажуємо зображення
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                
                # Зберігаємо зображення
                file_path = os.path.join(save_path, f"{asset_name}.png")
                with open(file_path, 'wb') as f:
                    f.write(img_response.content)
                
                print(f"Завантажено: {asset_name}")
                
    except Exception as e:
        print(f"Помилка при завантаженні: {str(e)}")

if __name__ == "__main__":
    download_dungeon_scrawl_assets()