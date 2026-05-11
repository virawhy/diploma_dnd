import requests
import json
import os
from googletrans import Translator

# Ініціалізуємо перекладач
translator = Translator()

# Словник спеціальних термінів для перекладу
SPECIAL_TERMS = {
    # Класи
    "Warlock": "Чаклун",
    "Wizard": "Чарівник",
    "Cleric": "Жрець",
    "Fighter": "Воїн",
    "Rogue": "Розбійник",
    "Paladin": "Паладин",
    "Ranger": "Слідопит",
    "Sorcerer": "Чародій",
    "Monk": "Монах",
    "Barbarian": "Варвар",
    "Druid": "Друїд",
    "Bard": "Бард",
    
    # Заклинання
    "Forcecage": "Силова клітка",
    "Evocation": "Втілення",
    "Divination": "Віщування",
    "Conjuration": "Виклик",
    "Abjuration": "Обереги",
    "Transmutation": "Перетворення",
    "Enchantment": "Зачарування",
    "Illusion": "Ілюзія",
    "Necromancy": "Некромантія",
    
    # Інші терміни
    "Touch": "Дотик",
    "Self": "На себе",
    "Concentration": "Концентрація",
    "Instantaneous": "Миттєво",
    "Permanent": "Постійно",
    "Special": "Особливо",
    "Action": "Дія",
    "Bonus Action": "Бонусна дія",
    "Reaction": "Реакція",
    "Minute": "Хвилина",
    "Hour": "Година",
    "Day": "День",
    "Round": "Раунд",
    "Feet": "Футів",
    "Miles": "Миль"
}

BASE_URL = "https://www.dnd5eapi.co/api/2014"
KNOWLEDGE_JSON_DIR = "static/json/knowledge_json"

# Словник для зберігання детальних описів правил, які не повинні оновлюватися
STATIC_RULE_DESCRIPTIONS = {
    # Базові правила
    "": "# Пригоди — це основа гри Dungeons & Dragons. Вони являють собою серії подій, які розгортаються у вигаданому світі та створюють сюжет, у якому беруть участь гравці. Кожна пригода — це унікальна історія, у якій гравці досліджують території, взаємодіють з іншими персонажами, борються з ворогами, шукають скарби та вирішують завдання. Майстер Підземель (Dungeon Master, або скорочено DM) — це ведучий гри, який створює світ, описує події та контролює всіх персонажів і істот, що не належать гравцям. Саме він вирішує, що відбувається у грі та реагує на дії гравців, спираючись на правила та здоровий глузд. Для створення цікавої пригоди Майстер повинен продумати такі складові: Сюжет — загальна ідея або конфлікт (наприклад, село потерпає від нападів гоблінів, і гравці мають розслідувати, звідки вони беруться). Локації — місця, які відвідають персонажі: підземелля, міста, ліси, руїни тощо. Виклики — ситуації, які потребують розв'язання: бої, пастки, моральні дилеми, загадки. NPC (неігрові персонажі) — жителі світу, з якими гравці можуть говорити, торгувати, дружити чи воювати. Гравці впливають на хід пригоди своїми рішеннями, і сюжет може змінюватися залежно від їхніх дій. Це робить кожну пригоду унікальною, живою та непередбачуваною.",
    
    # Ігрові механіки
    "": "# Бойовий\n\nБій у D&D відбувається покроково, де кожен учасник діє по черзі. Порядок ходів визначається ініціативою - кидком d20 + модифікатор спритності.\n\nПід час свого ходу персонаж може:  \n- Виконати одну дію (атака, використання заклинання, ривок, тощо)  \n- Виконати одну бонусну дію (якщо доступна)  \n- Використати свій рух (зазвичай рівний швидкості персонажа)  \n- Виконати одну безкоштовну дію (коротка фраза, кинути предмет)  \n\nПерсонажі також можуть використовувати реакцію - спеціальну дію, яку можна виконати не у свій хід у відповідь на певний тригер.\n\nАтаки виконуються шляхом кидка d20 + бонус атаки проти класу броні (AC) цілі. При успіху атакуючий кидає кістки пошкодження, визначені зброєю або заклинанням.\n\nКритичний успіх (20 на d20) подвоює кількість кісток пошкодження, а критичний провал (1 на d20) автоматично промахується, незалежно від бонусів."
}

def translate_text(text):
    """
    Перекладає текст з англійської на українську
    """
    if not text:
        return ""
    
    # Якщо текст є списком, перекладаємо кожен елемент
    if isinstance(text, list):
        return [translate_text(item) for item in text]
    
    # Перевіряємо, чи є текст у словнику спеціальних термінів
    if text in SPECIAL_TERMS:
        print(f"Використовую спеціальний переклад для: {text} -> {SPECIAL_TERMS[text]}")
        return SPECIAL_TERMS[text]
    
    # Перевіряємо, чи містить текст спеціальні терміни
    for term, translation in SPECIAL_TERMS.items():
        if term in text and len(term) > 3:  # Перевіряємо тільки терміни довші за 3 символи
            # Замінюємо термін на переклад
            text = text.replace(term, f"___{translation}___")
            print(f"Замінено термін у тексті: {term} -> {translation}")
    
    try:
        # Логуємо оригінальний текст
        print(f"Перекладаю: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # Перекладаємо текст
        result = translator.translate(text, src='en', dest='uk')
        translated_text = result.text
        
        # Відновлюємо спеціальні терміни після перекладу
        for term, translation in SPECIAL_TERMS.items():
            if f"___{translation}___" in translated_text:
                translated_text = translated_text.replace(f"___{translation}___", translation)
        
        # Логуємо результат перекладу
        print(f"Результат: {translated_text[:50]}{'...' if len(translated_text) > 50 else ''}")
        
        return translated_text
    except Exception as e:
        print(f"Помилка перекладу: {e} для тексту: {text[:100]}{'...' if len(text) > 100 else ''}")
        return text  # Повертаємо оригінальний текст у випадку помилки

def ensure_dir_exists():
    if not os.path.exists(KNOWLEDGE_JSON_DIR):
        os.makedirs(KNOWLEDGE_JSON_DIR)

def fetch_data(endpoint):
    if endpoint.startswith('/api/2014'):
        url = f"https://www.dnd5eapi.co{endpoint}"
    else:
        url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {url}: {response.status_code}")
        return None

def create_rules_json():
    # Перевіряємо, чи існує файл rules.json
    rules_file_path = f"{KNOWLEDGE_JSON_DIR}/rules.json"
    existing_rules = {}
    
    if os.path.exists(rules_file_path):
        try:
            with open(rules_file_path, "r", encoding="utf-8") as f:
                existing_rules = json.load(f)
                print("Завантажено існуючий файл rules.json")
        except Exception as e:
            print(f"Помилка при завантаженні існуючого файлу rules.json: {e}")
    
    rules_data = fetch_data("/rules")
    if not rules_data:
        return
    
    formatted_rules = {
        "basic_rules": [],
        "game_mechanics": []
    }
    
    # Отримуємо детальну інформацію про кожне правило
    for rule in rules_data.get("results", []):
        rule_details = fetch_data(rule["url"])
        if rule_details:
            # Перекладаємо назву правила
            translated_name = translate_text(rule_details["name"])
            
            # Перевіряємо, чи є це правило в списку статичних описів
            if translated_name in STATIC_RULE_DESCRIPTIONS:
                # Використовуємо статичний опис
                rule_desc = STATIC_RULE_DESCRIPTIONS[translated_name]
                print(f"Використовую статичний опис для правила: {translated_name}")
            else:
                # Перекладаємо опис правила
                rule_desc = translate_text(rule_details["desc"])
            
            # Розділяємо правила на базові та механіки
            if "combat" in rule["index"] or "ability" in rule["index"]:
                formatted_rules["game_mechanics"].append({
                    "name": translated_name,
                    "desc": rule_desc
                })
            else:
                formatted_rules["basic_rules"].append({
                    "name": translated_name,
                    "desc": rule_desc
                })
    
    # Зберігаємо у файл
    with open(rules_file_path, "w", encoding="utf-8") as f:
        json.dump(formatted_rules, f, ensure_ascii=False, indent=4)
    
    print("Rules JSON created successfully with Ukrainian translation and static descriptions")

def create_character_basics_json():
    character_basics = {
        "ability_scores": [],
        "conditions": [],
        "damage_types": [],
        "proficiencies": []
    }

    # Отримуємо очки здібностей
    ability_scores = fetch_data("/ability-scores")
    if ability_scores:
        for score in ability_scores.get("results", []):
            details = fetch_data(score["url"])
            if details:
                character_basics["ability_scores"].append({
                    "name": translate_text(details["full_name"]),
                    "short_name": translate_text(details["name"]),
                    "desc": translate_text(details["desc"]),
                    "skills": [translate_text(skill["name"]) for skill in details.get("skills", [])]
                })

    # Отримуємо стани
    conditions = fetch_data("/conditions")
    if conditions:
        for condition in conditions.get("results", []):
            details = fetch_data(condition["url"])
            if details:
                character_basics["conditions"].append({
                    "name": translate_text(details["name"]),
                    "desc": translate_text(details["desc"])
                })

    # Отримуємо типи шкоди
    damage_types = fetch_data("/damage-types")
    if damage_types:
        for damage in damage_types.get("results", []):
            details = fetch_data(damage["url"])
            if details:
                character_basics["damage_types"].append({
                    "name": translate_text(details["name"]),
                    "desc": translate_text(details["desc"])
                })

    # Отримуємо proficiencies
    proficiencies = fetch_data("/proficiencies")
    if proficiencies:
        for prof in proficiencies.get("results", []):
            if any(category in prof["index"] for category in ["skill", "saving-throw", "armor", "weapon"]):
                details = fetch_data(prof["url"])
                if details:
                    character_basics["proficiencies"].append({
                        "name": translate_text(details["name"]),
                        "type": translate_text(details.get("type", ""))
                    })

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/character_basics.json", "w", encoding="utf-8") as f:
        json.dump(character_basics, f, ensure_ascii=False, indent=4)
    
    print("Character basics JSON created successfully with Ukrainian translation")

def main():
    ensure_dir_exists()
    create_rules_json()
    # Інші функції створення JSON файлів...

if __name__ == "__main__":
    main()