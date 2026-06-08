from flask import Blueprint

from main import *


bp = Blueprint('characters', __name__)


@bp.route('/charlist.html')
@login_required
def charlist():
    characters = Character.query.filter_by(
        id_user=current_user.id_user).order_by(Character.id_character.desc()).all()
    requested_character_id = request.args.get('character', type=int)
    character_ids = {character.id_character for character in characters}
    selected_character_id = requested_character_id if requested_character_id in character_ids else None
    if selected_character_id is None and characters:
        selected_character_id = characters[0].id_character

    class_icons = {
        'Варвар': 'tw-dnd/class/barbarian.svg',
        'Бард': 'tw-dnd/class/bard.svg',
        'Друїд': 'tw-dnd/class/druid.svg',
        'Рейнджер': 'tw-dnd/class/ranger.svg',
        'Чаклун': 'tw-dnd/class/wizard.svg',
        'Монах': 'tw-dnd/class/monk.svg',
        'Паладін': 'tw-dnd/class/paladin.svg',
        'Розбійник': 'tw-dnd/class/rogue.svg',
        'Клірик': 'tw-dnd/class/cleric.svg',
        'Заклинатель': 'tw-dnd/class/sorcerer.svg',
        'Воїн': 'tw-dnd/class/fighter.svg',
        'Чорнокнижник': 'tw-dnd/class/warlock.svg',
    }

    characters_data = []
    for character_obj in characters:
        proficiencies = CharacterProficiency.query.filter_by(
            id_character=character_obj.id_character
        ).all()
        equipments = CharacterEquipment.query.filter_by(
            id_character=character_obj.id_character
        ).all()

        class_name = character_obj.class_name.class_name if character_obj.class_name else ''
        racial_group = character_obj.racial_group.racial_group if character_obj.racial_group else ''
        clean_note = character_obj.note or ''
        attack_entries = character_attack_entries(character_obj)
        primary_attack_entry = attack_entries[0] if attack_entries else {'name': '', 'bonus': '', 'damage': ''}

        characters_data.append({
            'id': character_obj.id_character,
            'name': character_obj.name,
            'level': character_obj.level,
            'class_name': class_name,
            'racial_group': racial_group,
            'icon': class_icons.get(class_name, 'character-logo.png'),
            'strength': character_obj.strength,
            'dexterity': character_obj.dexterity,
            'constitution': character_obj.constitution,
            'intelligence': character_obj.intelligence,
            'wisdom': character_obj.wisdom,
            'charisma': character_obj.charisma,
            'armor_class': character_obj.armor_class,
            'speed': character_obj.speed,
            'initiative': character_obj.initiative,
            'health_current': character_obj.health_current,
            'health_max': character_obj.health_max,
            'proficiency_bonus': character_obj.proficiency_bonus,
            'inspiration': character_obj.inspiration,
            'attack_name': primary_attack_entry['name'],
            'attack_bonus': primary_attack_entry['bonus'],
            'attack_damage': primary_attack_entry['damage'],
            'attack_entries': attack_entries,
            'note': clean_note,
            'equipments': [
                character_equipment.equipment.equipment
                for character_equipment in equipments
                if character_equipment.checker
            ],
            'proficiencies': [
                {
                    'name': proficiency.proficiency.proficiency,
                    'value': proficiency.value,
                }
                for proficiency in proficiencies
                if proficiency.checker
            ],
        })

    return render_template(
        'charlist.html',
        name=current_user.username,
        characters=characters_data,
        selected_character_id=selected_character_id,
    )


@bp.route('/delete_character/<int:character_id>', methods=['POST'])
@login_required
def delete_character(character_id):
    character_obj = Character.query.get_or_404(character_id)

    if character_obj.id_user != current_user.id_user:
        abort(403)

    CharacterProficiency.query.filter_by(id_character=character_id).delete()
    CharacterEquipment.query.filter_by(id_character=character_id).delete()
    CampaignCharacter.query.filter_by(id_character=character_id).delete()

    db.session.delete(character_obj)
    db.session.commit()

    flash('Персонажа видалено.', 'success')
    return redirect(url_for('charlist'))


@bp.route("/create-char.html", methods=("POST", "GET"))
@login_required
def create_char():
    if request.method == "POST":
        id_user = current_user.id_user
        name_ch = request.form.get('name_ch')
        racial_group = request.form.get('race')
        result = RacialGroup.query.filter_by(racial_group=racial_group).first()
        id_racial_group = result.id_racial_group
        class_name = request.form.get('class')
        result2 = Class.query.filter_by(class_name=class_name).first()
        id_class = result2.id_class
        level = request.form.get('level')
        strength = request.form.get('strength')
        dexterity = request.form.get('dexterity')
        constitution = request.form.get('constitution')
        intelect = request.form.get('intelect')
        wisdom = request.form.get('wisdom')
        charisma = request.form.get('charisma')
        attack_names = [value.strip() for value in request.form.getlist('attack_name')]
        attack_bonuses = [value.strip() for value in request.form.getlist('attack_bonus')]
        damage_types = [value.strip() for value in request.form.getlist('damage_type')]
        note_text = request.form.get('note', '').strip()
        answers = request.form.getlist('answer1')
        equipments = request.form.getlist('answer2')
        custom_equipment = request.form.get('custom_equipment', '')
        health_max = 7 + int(constitution) * 3

        attack_entries = []
        max_attacks = max(len(attack_names), len(attack_bonuses), len(damage_types))
        for index in range(max_attacks):
            attack_name = attack_names[index] if index < len(attack_names) else ''
            attack_bonus = attack_bonuses[index] if index < len(attack_bonuses) and attack_bonuses[index] else '1'
            damage_type = damage_types[index] if index < len(damage_types) else ''
            if attack_name or damage_type:
                attack_entries.append({
                    'name': attack_name,
                    'bonus': attack_bonus,
                    'damage': damage_type,
                })

        new_character = Character(name=name_ch, level=level, strength=strength, dexterity=dexterity, constitution=constitution,
                                  intelligence=intelect, wisdom=wisdom, charisma=charisma, armor_class=10, speed=30,
                                  initiative=dexterity, health_current=health_max, health_max=health_max,
                                  proficiency_bonus=0, inspiration=0, note=note_text, id_class=id_class,
                                  id_racial_group=id_racial_group, id_user=current_user.id_user)
        db.session.add(new_character)
        db.session.flush()


        id_character = new_character.id_character
        replace_character_attacks(new_character, attack_entries)
        # Отримуємо всі профіцієнції з бази даних
        all_proficiencies = Proficiency.query.all()
        
        # Створюємо записи для всіх профіцієнцій
        for prof in all_proficiencies:
            # Перевіряємо, чи була обрана ця профіцієнція в формі
            prof_name = prof.proficiency
            # Перевіряємо, чи є профіцієнція в списку обраних навичок
            is_selected = prof_name in answers
            
            # Отримуємо значення підхарактеристики
            prof_value = request.form.get(prof_name + '_value')
            # Якщо значення не передано або порожнє, встановлюємо 0
            if not prof_value or not prof_value.strip():
                prof_value = '0'
            # Конвертуємо в число, якщо не вдається - встановлюємо 0
            try:
                prof_value = int(prof_value)
            except (ValueError, TypeError):
                prof_value = 0
            
            new_ch_proficiency = CharacterProficiency(
                checker=is_selected,
                value=prof_value,
                id_proficiency=prof.id_proficiency,
                id_character=id_character
            )
            db.session.add(new_ch_proficiency)
            db.session.flush()

        sync_character_equipments(id_character, equipments, custom_equipment)
        
        db.session.commit()
        return redirect(url_for("charlist"))
    return render_template("create-char.html", name=current_user.username)


@bp.route("/dice.html")
def dice():
    return render_template("dice.html", name=current_username())


ATTACKS_NOTE_HEADING = 'Атаки та чари:'


def attack_entry_dict(attack):
    return {
        'name': attack.name,
        'bonus': attack.attack_bonus,
        'damage': attack.damage_type,
        'type': attack.action_type,
    }


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def character_attack_entries(character_obj):
    return [attack_entry_dict(attack) for attack in character_obj.attacks]


def replace_character_attacks(character_obj, attack_entries):
    for attack in list(character_obj.attacks):
        db.session.delete(attack)

    db.session.flush()
    for index, entry in enumerate(attack_entries):
        character_obj.attacks.append(Attack(
            name=entry['name'] or 'Без назви',
            attack_bonus=safe_int(entry['bonus'], 0),
            damage_type=entry['damage'],
            action_type=entry.get('type') or 'attack',
            sort_order=index,
        ))


def split_attack_note_section(note_text):
    normalized_note = (note_text or '').replace('\r\n', '\n').strip()
    if not normalized_note:
        return '', []

    note_blocks = []
    attack_entries = []
    for block in normalized_note.split('\n\n'):
        stripped_block = block.strip()
        if not stripped_block:
            continue

        if stripped_block.startswith(ATTACKS_NOTE_HEADING):
            for line in stripped_block.split('\n')[1:]:
                line = line.strip()
                if not line.startswith('- '):
                    continue

                parts = [part.strip() for part in line[2:].split('|')]
                name = parts[0] if parts else ''
                bonus = '1'
                damage = ''
                if len(parts) > 1:
                    bonus = parts[1].replace('бонус', '', 1).strip() or '1'
                if len(parts) > 2:
                    damage = '' if parts[2] == 'без опису' else parts[2]

                attack_entries.append({
                    'name': name if name != 'Без назви' else '',
                    'bonus': bonus,
                    'damage': damage,
                })
        else:
            note_blocks.append(stripped_block)

    return '\n\n'.join(note_blocks), attack_entries


def build_attack_entries(form):
    attack_names = [value.strip() for value in form.getlist('attack_name')]
    attack_bonuses = [value.strip() for value in form.getlist('attack_bonus')]
    damage_types = [value.strip() for value in form.getlist('damage_type')]

    attack_entries = []
    max_attacks = max(len(attack_names), len(attack_bonuses), len(damage_types))
    for index in range(max_attacks):
        attack_name = attack_names[index] if index < len(attack_names) else ''
        attack_bonus = attack_bonuses[index] if index < len(attack_bonuses) and attack_bonuses[index] else '1'
        damage_type = damage_types[index] if index < len(damage_types) else ''
        if attack_name or damage_type:
            attack_entries.append({
                'name': attack_name,
                'bonus': attack_bonus,
                'damage': damage_type,
            })

    return attack_entries


def compose_note_with_attacks(note_text, attack_entries):
    clean_note, _ = split_attack_note_section(note_text)
    note_parts = []

    if attack_entries:
        note_parts.append(
            ATTACKS_NOTE_HEADING + '\n' +
            '\n'.join(
                f"- {entry['name'] or 'Без назви'} | бонус {entry['bonus']} | {entry['damage'] or 'без опису'}"
                for entry in attack_entries
            )
        )
    if clean_note:
        note_parts.append(clean_note)

    return '\n\n'.join(note_parts)


# Маршрут для відображення та оновлення інформації про персонажа
@bp.route("/character/<id_class_f>", methods=("POST", "GET"))
@login_required  # Декоратор, що вимагає авторизації користувача
def character(id_class_f):
    # Отримуємо об'єкт персонажа з бази даних за його ID
    character_obj = Character.query.filter_by(id_character=id_class_f).first()

    # Якщо персонаж не знайдений, повертаємо помилку 404
    if character_obj is None:
        abort(404)
        
    # Перевіряємо, чи поточний користувач є власником персонажа
    is_owner = character_obj.id_user == current_user.id_user
    if not is_owner:
        abort(403)

    clean_note = character_obj.note or ''
    attack_entries = character_attack_entries(character_obj)
    primary_attack_entry = attack_entries[0] if attack_entries else {'name': '', 'bonus': 1, 'damage': ''}
    attack_form_entries = attack_entries or [primary_attack_entry]
    equipment_names = [
        character_equipment.equipment.equipment
        for character_equipment in CharacterEquipment.query.filter_by(id_character=id_class_f).all()
        if character_equipment.checker
    ]
    standard_equipment = set(standard_equipment_names())
    custom_equipment_text = '\n'.join(
        equipment_name for equipment_name in equipment_names
        if equipment_name not in standard_equipment
    )

    # Створюємо словник з основними характеристиками персонажа
    character_dict = {
        'name': character_obj.name,  # Ім'я персонажа
        'level': character_obj.level,  # Рівень персонажа
        'class_name': character_obj.class_name.class_name,  # Назва класу
        'racial_group': character_obj.racial_group.racial_group,  # Расова група
        'strength': character_obj.strength,  # Сила
        'dexterity': character_obj.dexterity,  # Спритність
        'constitution': character_obj.constitution,  # Статура
        'intelligence': character_obj.intelligence,  # Інтелект
        'wisdom': character_obj.wisdom,  # Мудрість
        'charisma': character_obj.charisma,  # Харизма
        'armor_class': character_obj.armor_class,  # Клас броні
        'speed': character_obj.speed,  # Швидкість
        'initiative': character_obj.initiative,  # Ініціатива
        'health_current': character_obj.health_current,  # Поточне здоров'я
        'health_max': character_obj.health_max,  # Максимальне здоров'я
        'proficiency_bonus': character_obj.proficiency_bonus,  # Бонус майстерності
        'inspiration': character_obj.inspiration,  # Натхнення
        'attack_name': primary_attack_entry['name'],  # Назва атаки
        'attack_bonus': primary_attack_entry['bonus'],  # Бонус атаки
        'attack_damage': primary_attack_entry['damage'],  # Тип пошкодження
        'attack_entries': attack_form_entries,
        'note': clean_note,  # Нотатки
        'equipments': equipment_names,
        'custom_equipment': custom_equipment_text,
    }

    # Отримуємо всі підхарактеристики персонажа
    proficiency_ch_obj = CharacterProficiency.query.filter_by(id_character=id_class_f).all()
    # Створюємо список активних підхарактеристик
    proficiencies_list = [cp.proficiency.proficiency for cp in proficiency_ch_obj if cp.checker]

    
    # Створюємо словник значень підхарактеристик
    proficiency_values = {}
    for cp in proficiency_ch_obj:
        proficiency_values[cp.proficiency.proficiency] = cp.value 
    
    # Отримуємо об'єкт персонажа для оновлення
    char_to_update = Character.query.get_or_404(id_class_f)
    if request.method == "POST":
        # Перевіряємо, чи користувач є власником персонажа
        if not is_owner:
            flash("Ви не можете редагувати персонажа іншого користувача", "error")
            return redirect(url_for("character", id_class_f=id_class_f))
        # Виводимо отримані дані форми для відладки
        # Оновлюємо основні характеристики персонажа
        char_to_update.name = request.form.get('name_ch')
        char_to_update.level = request.form.get('level')
        char_to_update.armor_class = int(request.form.get('armor_class', 0))
        char_to_update.speed = int(request.form.get('speed', 0))
        char_to_update.initiative = int(request.form.get('initiative', 0))
        char_to_update.health_current = int(request.form.get('health_current', 0))
        char_to_update.health_max = int(request.form.get('health_max', 0))
        char_to_update.proficiency_bonus = int(request.form.get('proficiency_bonus', 0))
        char_to_update.inspiration = int(request.form.get('inspiration', 0))
        char_to_update.strength = request.form.get('strength')
        char_to_update.dexterity = request.form.get('dexterity')
        char_to_update.constitution = request.form.get('constitution')
        char_to_update.intelligence = request.form.get('intelligence')
        char_to_update.wisdom = request.form.get('wisdom')
        char_to_update.charisma = request.form.get('charisma')
        attack_entries = build_attack_entries(request.form)
        primary_attack_entry = attack_entries[0] if attack_entries else {'name': '', 'bonus': '1', 'damage': ''}
        replace_character_attacks(char_to_update, attack_entries)
        selected_equipments = request.form.getlist('answer2')
        custom_equipment_text = request.form.get('custom_equipment', '').strip()
        sync_character_equipments(id_class_f, selected_equipments, custom_equipment_text)
        equipment_names = [*selected_equipments, *[
            item.strip()
            for item in custom_equipment_text.replace('\r\n', '\n').split('\n')
            if item.strip()
        ]]
        char_to_update.note = request.form.get('note', '').strip()
        
        # Зберігаємо зміни в базі даних
        db.session.commit()
        
        # Оновлюємо словник character_dict після збереження змін
        character_dict.update({
            'name': char_to_update.name,
            'level': char_to_update.level,
            'armor_class': char_to_update.armor_class,
            'speed': char_to_update.speed,
            'initiative': char_to_update.initiative,
            'health_current': char_to_update.health_current,
            'health_max': char_to_update.health_max,
            'proficiency_bonus': char_to_update.proficiency_bonus,
            'inspiration': char_to_update.inspiration,
            'strength': char_to_update.strength,
            'dexterity': char_to_update.dexterity,
            'constitution': char_to_update.constitution,
            'intelligence': char_to_update.intelligence,
            'wisdom': char_to_update.wisdom,
            'charisma': char_to_update.charisma,
            'attack_name': primary_attack_entry['name'],
            'attack_bonus': primary_attack_entry['bonus'],
            'attack_damage': primary_attack_entry['damage'],
            'attack_entries': attack_entries or [primary_attack_entry],
            'note': char_to_update.note,
            'equipments': equipment_names,
            'custom_equipment': custom_equipment_text
        })
        
        # Отримуємо всі поточні підхарактеристики персонажа
        current_proficiencies = CharacterProficiency.query.filter_by(id_character=id_class_f).all()


        
        # Створюємо словник для швидкого пошуку підхарактеристик
        current_prof_dict = {}
        for cp in current_proficiencies:
            current_prof_dict[cp.proficiency.proficiency] = cp
        
        # Обробляємо всі підхарактеристики
        all_proficiencies = Proficiency.query.all()
        for prof in all_proficiencies:
            prof_name = prof.proficiency
            # Перевіряємо стан чекбоксу
            form_value = request.form.getlist(prof_name)
            is_checked = len(form_value) > 0
            
            # Отримуємо значення підхарактеристики
            prof_value_key = prof_name + '_value'
            prof_value = request.form.get(prof_value_key, '0')
            # Встановлюємо значення 0, якщо порожнє
            # Конвертуємо в число
            try:
                prof_value = int(prof_value)
            except (ValueError, TypeError):
                prof_value = 0
                
            # Оновлюємо або створюємо запис підхарактеристики
            if prof_name in current_prof_dict:
                cp = current_prof_dict[prof_name]
                cp.checker = is_checked
                cp.value = prof_value
                db.session.add(cp)
                # Оновлюємо значення в словнику
                proficiency_values[prof_name] = prof_value
                if is_checked and prof_name not in proficiencies_list:
                    proficiencies_list.append(prof_name)
                elif not is_checked and prof_name in proficiencies_list:
                    proficiencies_list.remove(prof_name)
            else:
                new_ch_proficiency = CharacterProficiency(
                    checker=is_checked,
                    value=prof_value,
                    id_proficiency=prof.id_proficiency,
                    id_character=id_class_f
                )
                db.session.add(new_ch_proficiency)
                # Додаємо значення в словник
                proficiency_values[prof_name] = prof_value
                if is_checked:
                    proficiencies_list.append(prof_name)
                        
        # Зберігаємо зміни в базі даних
        try:
            db.session.commit()
            # Оновлюємо значення після збереження
            proficiency_ch_obj = CharacterProficiency.query.filter_by(id_character=id_class_f).all()
            proficiency_values = {}
            proficiencies_list = []
            for cp in proficiency_ch_obj:
                proficiency_values[cp.proficiency.proficiency] = cp.value
                if cp.checker:
                    proficiencies_list.append(cp.proficiency.proficiency)
            # Оновлюємо значення в character_dict після збереження
            character_dict.update({
                'strength': char_to_update.strength,
                'dexterity': char_to_update.dexterity,
                'constitution': char_to_update.constitution,
                'intelligence': char_to_update.intelligence,
                'wisdom': char_to_update.wisdom,
                'charisma': char_to_update.charisma,
                'attack_name': primary_attack_entry['name'],
                'attack_bonus': primary_attack_entry['bonus'],
                'attack_damage': primary_attack_entry['damage'],
                'attack_entries': attack_entries or [primary_attack_entry],
                'note': char_to_update.note,
                'equipments': equipment_names,
                'custom_equipment': custom_equipment_text
            })
            return render_template("character.html", character=character_dict, name=current_user.username, proficiencies_list=proficiencies_list, proficiency_values=proficiency_values, is_owner=is_owner, equipment_groups=EQUIPMENT_GROUPS)
        except Exception as e:
            # Відкатуємо зміни у випадку помилки
            db.session.rollback()
            app.logger.error("Character update failed: %s", e)
        
    # Виводимо список активних підхарактеристик
    
    # Відображаємо сторінку персонажа
    return render_template("character.html", character=character_dict, name=current_user.username, proficiencies_list=proficiencies_list, proficiency_values=proficiency_values, is_owner=is_owner, equipment_groups=EQUIPMENT_GROUPS)

