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

# Словник для зберігання детальних описів правил, які не повинні оновлюватися
STATIC_RULE_DESCRIPTIONS = {
    # Базові правила
    "": "# Детальний опис пригод у D&D. Ця секція містить інформацію про те, як створювати та проводити пригоди, включаючи поради для Майстра Підземель щодо створення цікавих сюжетів, локацій та викликів для гравців.\n\nПригоди в D&D можуть включати дослідження підземель, битви з монстрами, взаємодію з NPC, вирішення головоломок та багато іншого. Майстер Підземель створює світ та ситуації, а гравці вирішують, як їхні персонажі будуть реагувати та взаємодіяти з цим світом.",
    
    # Ігрові механіки
    "": "# Бій у D&D відбувається покроково, де кожен учасник діє по черзі. Порядок ходів визначається ініціативою - кидком d20 + модифікатор спритності.\n\nПід час свого ходу персонаж може:  \n- Виконати одну дію (атака, використання заклинання, ривок, тощо)  \n- Виконати одну бонусну дію (якщо доступна)  \n- Використати свій рух (зазвичай рівний швидкості персонажа)  \n- Виконати одну безкоштовну дію (коротка фраза, кинути предмет)  \n\nПерсонажі також можуть використовувати реакцію - спеціальну дію, яку можна виконати не у свій хід у відповідь на певний тригер.\n\nАтаки виконуються шляхом кидка d20 + бонус атаки проти класу броні (AC) цілі. При успіху атакуючий кидає кістки пошкодження, визначені зброєю або заклинанням.\n\nКритичний успіх (20 на d20) подвоює кількість кісток пошкодження, а критичний провал (1 на d20) автоматично промахується, незалежно від бонусів."
}

BASE_URL = "https://www.dnd5eapi.co/api/2014"
KNOWLEDGE_JSON_DIR = "static/json/knowledge_json"

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
                        "type": translate_text(details["type"])
                    })

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/character_basics.json", "w", encoding="utf-8") as f:
        json.dump(character_basics, f, ensure_ascii=False, indent=4)
    
    print("Character basics JSON created successfully with Ukrainian translation")

def create_races_json():
    races_data = {
        "races": [],
        "backgrounds": [],
        "languages": []
    }

    # Отримуємо раси
    races = fetch_data("/races")
    if races:
        for race in races.get("results", []):
            details = fetch_data(race["url"])
            if details:
                race_info = {
                    "name": translate_text(details["name"]),
                    "speed": details.get("speed", 0),
                    "ability_bonuses": [],
                    "age": translate_text(details.get("age", "")),
                    "alignment": translate_text(details.get("alignment", "")),
                    "size": translate_text(details.get("size", "")),
                    "size_description": translate_text(details.get("size_description", "")),
                    "languages": [translate_text(lang["name"]) for lang in details.get("languages", [])]
                }
                
                # Додаємо бонуси до характеристик
                for bonus in details.get("ability_bonuses", []):
                    race_info["ability_bonuses"].append({
                        "ability_score": translate_text(bonus.get("ability_score", {}).get("name", "")),
                        "bonus": bonus.get("bonus", 0)
                    })
                
                races_data["races"].append(race_info)

    # Отримуємо backgrounds
    backgrounds = fetch_data("/backgrounds")
    if backgrounds:
        for bg in backgrounds.get("results", []):
            details = fetch_data(bg["url"])
            if details:
                races_data["backgrounds"].append({
                    "name": translate_text(details["name"]),
                    "feature": {
                        "name": translate_text(details.get("feature", {}).get("name", "")),
                        "desc": translate_text(details.get("feature", {}).get("desc", []))
                    },
                    "starting_proficiencies": [translate_text(prof["name"]) for prof in details.get("starting_proficiencies", [])]
                })

    # Отримуємо мови
    languages = fetch_data("/languages")
    if languages:
        for lang in languages.get("results", []):
            details = fetch_data(lang["url"])
            if details:
                races_data["languages"].append({
                    "name": translate_text(details["name"]),
                    "type": translate_text(details.get("type", "")),
                    "script": translate_text(details.get("script", "")),
                    "typical_speakers": translate_text(details.get("typical_speakers", []))
                })

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/races.json", "w", encoding="utf-8") as f:
        json.dump(races_data, f, ensure_ascii=False, indent=4)
    
    print("Races JSON created successfully with Ukrainian translation")

def create_classes_json():
    classes_data = {
        "classes": [],
        "subclasses": [],
        "magic_schools": []
    }

    # Отримуємо класи
    classes = fetch_data("/classes")
    if classes:
        for class_item in classes.get("results", []):
            details = fetch_data(class_item["url"])
            if details:
                class_info = {
                    "name": translate_text(details["name"]),
                    "hit_die": details.get("hit_die", 0),
                    "proficiencies": [translate_text(prof["name"]) for prof in details.get("proficiencies", [])],
                    "saving_throws": [translate_text(save["name"]) for save in details.get("saving_throws", [])],
                    "starting_equipment": []
                }
                
                # Отримуємо стартове спорядження
                if details.get("starting_equipment", []):
                    for equipment in details["starting_equipment"]:
                        if equipment.get("equipment", {}).get("name"):
                            class_info["starting_equipment"].append({
                                "name": translate_text(equipment["equipment"]["name"]),
                                "quantity": equipment.get("quantity", 1)
                            })
                
                classes_data["classes"].append(class_info)

                # Отримуємо підкласи для кожного класу
                subclasses = fetch_data(f"/classes/{class_item['index']}/subclasses")
                if subclasses:
                    for subclass in subclasses.get("results", []):
                        subclass_details = fetch_data(subclass["url"])
                        if subclass_details:
                            classes_data["subclasses"].append({
                                "name": translate_text(subclass_details["name"]),
                                "class": translate_text(details["name"]),
                                "flavor": translate_text(subclass_details.get("subclass_flavor", "")),
                                "desc": translate_text(subclass_details.get("desc", []))
                            })

    # Отримуємо школи магії
    magic_schools = fetch_data("/magic-schools")
    if magic_schools:
        for school in magic_schools.get("results", []):
            details = fetch_data(school["url"])
            if details:
                classes_data["magic_schools"].append({
                    "name": translate_text(details["name"]),
                    "desc": translate_text(details.get("desc", ""))
                })

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/classes.json", "w", encoding="utf-8") as f:
        json.dump(classes_data, f, ensure_ascii=False, indent=4)
    
    print("Classes JSON created successfully with Ukrainian translation")

def create_equipment_json():
    equipment_data = {
        "equipment_categories": [],
        "equipment": []
    }

    # Отримуємо категорії спорядження
    categories = fetch_data("/equipment-categories")
    if categories:
        for category in categories.get("results", []):
            details = fetch_data(category["url"])
            if details:
                equipment_data["equipment_categories"].append({
                    "name": translate_text(details["name"]),
                    "equipment": [translate_text(item["name"]) for item in details.get("equipment", [])]
                })

    # Отримуємо спорядження
    equipment = fetch_data("/equipment")
    if equipment:
        for item in equipment.get("results", []):
            details = fetch_data(item["url"])
            if details:
                equipment_info = {
                    "name": translate_text(details["name"]),
                    "category": translate_text(details.get("equipment_category", {}).get("name", "")),
                    "cost": details.get("cost", {}).get("quantity", 0),
                    "weight": details.get("weight", 0),
                    "desc": translate_text(details.get("desc", []))
                }
                
                # Додаємо специфічні властивості для зброї
                if details.get("weapon_category"):
                    equipment_info["weapon_category"] = translate_text(details["weapon_category"])
                    equipment_info["weapon_range"] = translate_text(details.get("weapon_range", ""))
                    equipment_info["damage"] = {
                        "dice": details.get("damage", {}).get("damage_dice", ""),
                        "type": translate_text(details.get("damage", {}).get("damage_type", {}).get("name", ""))
                    }
                    equipment_info["properties"] = [translate_text(prop["name"]) for prop in details.get("properties", [])]
                
                # Додаємо специфічні властивості для броні
                if details.get("armor_category"):
                    equipment_info["armor_category"] = translate_text(details["armor_category"])
                    equipment_info["armor_class"] = {
                        "base": details.get("armor_class", {}).get("base", 0),
                        "dex_bonus": details.get("armor_class", {}).get("dex_bonus", False),
                        "max_bonus": details.get("armor_class", {}).get("max_bonus", 0)
                    }
                    equipment_info["str_minimum"] = details.get("str_minimum", 0)
                    equipment_info["stealth_disadvantage"] = details.get("stealth_disadvantage", False)
                
                equipment_data["equipment"].append(equipment_info)

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/equipment.json", "w", encoding="utf-8") as f:
        json.dump(equipment_data, f, ensure_ascii=False, indent=4)
    
    print("Equipment JSON created successfully with Ukrainian translation")

def create_spells_json():
    spells_data = {
        "spells": []
    }

    # Отримуємо заклинання
    spells = fetch_data("/spells")
    if spells:
        for spell in spells.get("results", []):
            details = fetch_data(spell["url"])
            if details:
                spell_info = {
                    "name": translate_text(details["name"]),
                    "level": details.get("level", 0),
                    "school": translate_text(details.get("school", {}).get("name", "")),
                    "casting_time": translate_text(details.get("casting_time", "")),
                    "range": translate_text(details.get("range", "")),
                    "components": details.get("components", []),
                    "duration": translate_text(details.get("duration", "")),
                    "desc": translate_text(details.get("desc", [])),
                    "higher_level": translate_text(details.get("higher_level", [])),
                    "classes": [translate_text(class_item["name"]) for class_item in details.get("classes", [])]
                }
                
                # Додаємо матеріальні компоненти, якщо вони є
                if details.get("material"):
                    spell_info["material"] = translate_text(details["material"])
                
                spells_data["spells"].append(spell_info)

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/spells.json", "w", encoding="utf-8") as f:
        json.dump(spells_data, f, ensure_ascii=False, indent=4)
    
    print("Spells JSON created successfully with Ukrainian translation")

def create_monsters_json():
    monsters_data = {
        "monsters": []
    }

    # Отримуємо монстрів
    monsters = fetch_data("/monsters")
    if monsters:
        for monster in monsters.get("results", []):
            details = fetch_data(monster["url"])
            if details:
                monster_info = {
                    "name": translate_text(details["name"]),
                    "size": translate_text(details.get("size", "")),
                    "type": translate_text(details.get("type", "")),
                    "alignment": translate_text(details.get("alignment", "")),
                    "armor_class": details.get("armor_class", 0),
                    "hit_points": details.get("hit_points", 0),
                    "hit_dice": details.get("hit_dice", ""),
                    "speed": {k: v for k, v in details.get("speed", {}).items()},
                    "strength": details.get("strength", 10),
                    "dexterity": details.get("dexterity", 10),
                    "constitution": details.get("constitution", 10),
                    "intelligence": details.get("intelligence", 10),
                    "wisdom": details.get("wisdom", 10),
                    "charisma": details.get("charisma", 10),
                    "challenge_rating": details.get("challenge_rating", 0),
                    "xp": details.get("xp", 0),
                    "desc": translate_text(details.get("desc", ""))
                }
                
                # Додаємо спеціальні здібності
                if details.get("special_abilities"):
                    monster_info["special_abilities"] = [
                        {
                            "name": translate_text(ability.get("name", "")),
                            "desc": translate_text(ability.get("desc", ""))
                        } for ability in details["special_abilities"]
                    ]
                
                # Додаємо дії
                if details.get("actions"):
                    monster_info["actions"] = [
                        {
                            "name": translate_text(action.get("name", "")),
                            "desc": translate_text(action.get("desc", ""))
                        } for action in details["actions"]
                    ]
                
                # Додаємо легендарні дії
                if details.get("legendary_actions"):
                    monster_info["legendary_actions"] = [
                        {
                            "name": translate_text(action.get("name", "")),
                            "desc": translate_text(action.get("desc", ""))
                        } for action in details["legendary_actions"]
                    ]
                
                monsters_data["monsters"].append(monster_info)

    # Зберігаємо у файл
    with open(f"{KNOWLEDGE_JSON_DIR}/monsters.json", "w", encoding="utf-8") as f:
        json.dump(monsters_data, f, ensure_ascii=False, indent=4)
    
    print("Monsters JSON created successfully with Ukrainian translation")

def main():
    ensure_dir_exists()
    create_rules_json()
    create_character_basics_json()
    create_races_json()
    create_classes_json()
    create_equipment_json()
    create_spells_json()
    create_monsters_json()

if __name__ == "__main__":
    main()