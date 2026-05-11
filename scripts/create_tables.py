from main import db, Class, RacialGroup, Equipment

# Список класів з create-char.html
classes = [
    'Воїн',
    'Паладін',
    'Чаклун',
    'Варвар',
    'Клірик',
    'Чорнокнижник',
    'Розбійник',
    'Заклинатель',
    'Монах',
    'Рейнджер',
    'Друїд',
    'Бард'
]

# Список рас з create-char.html
racial_groups = [
    'Дракононароджений',
    'Дварф',
    'Ельф',
    'Гном',
    'Напівельф',
    'Напіворк',
    'Напіврослик',
    'Людина',
    'Тифлінг',
    'Орк'
]

# Додавання класів
for class_name in classes:
    if not Class.query.filter_by(class_name=class_name).first():
        new_class = Class(class_name=class_name)
        db.session.add(new_class)

# Додавання рас
for racial_group in racial_groups:
    if not RacialGroup.query.filter_by(racial_group=racial_group).first():
        new_racial_group = RacialGroup(racial_group=racial_group)
        db.session.add(new_racial_group)

# Створення базових профіцієнцій
proficiencies = [
    # Рятівні кидки
    'Рятівні кидки Сила',
    'Рятівні кидки Спритність',
    'Рятівні кидки Статура',
    'Рятівні кидки Інтелект',
    'Рятівні кидки Мудрість',
    'Рятівні кидки Харизма',
    # Навички
    'Акробатика',
    'Атлетика',
    'Виживання',
    'Артистизм',
    'Залякування',
    'Історія',
    'Медицина',
    'Обман',
    'Переконання',
    'Природа',
    'Проникливість',
    'Релігія',
    'Спритність рук',
    'Скритність',
    'Магія',
    'Приборкання',
    'Розслідування',
    'Уважність'
]

# Додавання профіцієнцій
from main import Proficiency
for prof_name in proficiencies:
    if not Proficiency.query.filter_by(proficiency=prof_name).first():
        new_prof = Proficiency(proficiency=prof_name)
        db.session.add(new_prof)

# Створення базового обладнання
equipments = [
    'Спис',
    'Лук',
    'Полуторний меч',
    'Проста зброя',
    'Лускатий обладунок (17)',
    'Кольчужний обладунок (16)',
    'Клепаний шкіряний обладунок (14)',
    'Шкіряний обладунок (12)',
    'Молитовник',
    'Святий символ',
    'Набір дослідника',
    'Ремісничі інструменти'
]

# Додавання обладнання
for equipment_name in equipments:
    if not Equipment.query.filter_by(equipment=equipment_name).first():
        new_equipment = Equipment(equipment=equipment_name)
        db.session.add(new_equipment)

# Збереження змін
db.session.commit()
print('Класи, раси, профіцієнції та обладнання успішно додані до бази даних!')