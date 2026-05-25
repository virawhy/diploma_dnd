from flask import Blueprint

from main import *


bp = Blueprint('campaigns', __name__)


@bp.route("/campaign/<int:campaign_id>")
@login_required
def campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Перевірка чи користувач має доступ до кампанії
    if not current_user_can_view_campaign(campaign):
        abort(403)
    
    # Отримуємо персонажів гравців
    characters = Character.query.join(CampaignCharacter, CampaignCharacter.id_character == Character.id_character)\
                         .filter(CampaignCharacter.id_campaign == campaign_id).all()
    
    # Отримуємо запрошення для поточного користувача
    invites = CampaignMember.query.filter_by(
        id_user=current_user.id_user,
        status='invited'
    ).all()
    
    # Визначаємо, чи є поточний користувач власником кампанії
    is_owner = campaign.id_user == current_user.id_user
    
    return render_template('campaign.html',
                          campaign=campaign,
                          npcs=campaign.npcs,
                          events=campaign.events,
                          locations=campaign.locations,
                          characters=characters,
                          invites=invites,
                          is_owner=is_owner)

@bp.route('/api/invites')
@login_required
def get_invites():
    app.logger.info(f'Отримання списку запрошень для користувача {current_user.id_user}')
    try:
        invites = CampaignMember.query.filter_by(
            id_user=current_user.id_user,
            status='invited'
        ).all()
        
        invites_data = [{
            'id': invite.id_campaign_member,
            'campaign_name': invite.campaign.name,
            'status': invite.status
        } for invite in invites]
        
        return jsonify(invites_data)
    except Exception as e:
        app.logger.error(f'Помилка при отриманні списку запрошень: {str(e)}')
        return {'error': 'Помилка при отриманні списку запрошень'}, 500

# API для НПС
@bp.route('/api/campaign/<int:campaign_id>/npc', methods=['POST'])
@login_required
def create_npc(campaign_id):
    app.logger.info(f'Створення NPC для кампанії {campaign_id}')
    try:
        campaign = Campaign.query.get_or_404(campaign_id)
        if not current_user_owns_campaign(campaign):
            app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
            abort(403)
        
        data = request.get_json()
        app.logger.debug(f'Отримані дані: {data}')
        
        npc = NPC(name=data['name'],
                  description=data['description'],
                  id_campaign=campaign_id)
        
        db.session.add(npc)
        db.session.commit()
        app.logger.info(f'NPC успішно створено з id {npc.id_npc}')
        return {'id': npc.id_npc, 'name': npc.name, 'description': npc.description}
    except HTTPException:
        raise
    except Exception as e:
        app.logger.error(f'Помилка при створенні NPC: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при створенні NPC'}, 500

@bp.route('/api/npc/<int:npc_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_npc(npc_id):
    npc = NPC.query.get_or_404(npc_id)
    if not current_user_owns_campaign(npc.campaign):
        abort(403)
    
    if request.method == 'DELETE':
        db.session.delete(npc)
        db.session.commit()
        return '', 204
    
    data = request.get_json()
    npc.name = data['name']
    npc.description = data['description']
    db.session.commit()
    return {'id': npc.id_npc, 'name': npc.name, 'description': npc.description}

# API для подій
@bp.route('/api/campaign/<int:campaign_id>/event', methods=['POST'])
@login_required
def create_event(campaign_id):
    app.logger.info(f'Створення події для кампанії {campaign_id}')
    try:
        campaign = Campaign.query.get_or_404(campaign_id)
        if not current_user_owns_campaign(campaign):
            app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
            abort(403)
        
        data = request.get_json()
        app.logger.debug(f'Отримані дані: {data}')
        
        # Конвертуємо дату з рядка в об'єкт datetime.date
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        event = Event(name=data['name'],
                      description=data['description'],
                      date=date_obj,
                      id_campaign=campaign_id)
        
        db.session.add(event)
        db.session.commit()
        app.logger.info(f'Подію успішно створено з id {event.id_event}')
        return {'id': event.id_event, 'name': event.name, 'description': event.description, 'date': event.date}
    except HTTPException:
        raise
    except Exception as e:
        app.logger.error(f'Помилка при створенні події: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при створенні події'}, 500

@bp.route('/api/event/<int:event_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user_owns_campaign(event.campaign):
        abort(403)
    
    if request.method == 'DELETE':
        db.session.delete(event)
        db.session.commit()
        return '', 204
    
    data = request.get_json()
    date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
    event.name = data['name']
    event.description = data['description']
    event.date = date_obj
    db.session.commit()
    return {'id': event.id_event, 'name': event.name, 'description': event.description, 'date': event.date}

# API для локацій
@bp.route('/api/campaign/<int:campaign_id>/location', methods=['POST'])
@login_required
def create_location(campaign_id):
    app.logger.info(f'Створення локації для кампанії {campaign_id}')
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not current_user_owns_campaign(campaign):
        app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
        abort(403)
    
    try:
        data = request.get_json()
    except Exception as e:
        app.logger.error(f'Error parsing JSON data: {str(e)}')
        return {'error': 'Invalid JSON data'}, 400
    
    app.logger.debug(f'Отримані дані: {data}')
    
    try:
        location = Location(name=data['name'],
                          description=data['description'],
                          id_campaign=campaign_id)
        
        db.session.add(location)
        db.session.commit()
        app.logger.info(f'Локацію успішно створено з id {location.id_location}')
        return {'id': location.id_location, 'name': location.name, 'description': location.description}
    except Exception as e:
        app.logger.error(f'Помилка при створенні локації: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при створенні локації'}, 500

@bp.route('/api/location/<int:location_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_location(location_id):
    location = Location.query.get_or_404(location_id)
    if not current_user_owns_campaign(location.campaign):
        abort(403)
    
    if request.method == 'DELETE':
        db.session.delete(location)
        db.session.commit()
        return '', 204
    
    data = request.get_json()
    location.name = data['name']
    location.description = data['description']
    db.session.commit()
    return {'id': location.id_location, 'name': location.name, 'description': location.description}

@bp.route('/api/campaign/<int:campaign_id>/invite', methods=['POST'])
@login_required
def invite_to_campaign(campaign_id):
    app.logger.info(f'Спроба надіслати запрошення до кампанії {campaign_id}')
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not current_user_owns_campaign(campaign):
        app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
        abort(403)
    
    try:
        data = request.get_json()
        invited_username = data.get('username')
        if not invited_username:
            return {'error': 'Не вказано імʼя користувача'}, 400
            
        invited_user = User.query.filter_by(username=invited_username).first()
        if not invited_user:
            return {'error': 'Користувача не знайдено'}, 404
            
        if invited_user.id_user == current_user.id_user:
            return {'error': 'Ви не можете запросити самого себе'}, 400
            
        existing_member = CampaignMember.query.filter_by(
            id_campaign=campaign_id,
            id_user=invited_user.id_user
        ).first()
        
        if existing_member:
            if existing_member.status == 'invited':
                return {'error': 'Запрошення вже надіслано'}, 400
            elif existing_member.status == 'member':
                return {'error': 'Користувач вже є учасником кампанії'}, 400
        
        member = CampaignMember(id_campaign=campaign_id,
                               id_user=invited_user.id_user,
                               status='invited')
        db.session.add(member)
        db.session.commit()
        
        app.logger.info(f'Запрошення успішно надіслано користувачу {invited_username}')
        return {'message': 'Запрошення надіслано успішно'}, 200
        
    except Exception as e:
        app.logger.error(f'Помилка при надсиланні запрошення: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при надсиланні запрошення'}, 500

@bp.route('/api/campaign/<int:campaign_id>/invite/accept', methods=['POST'])
@login_required
def accept_campaign_invite(campaign_id):
    app.logger.info(f'Спроба прийняти запрошення до кампанії {campaign_id}')
    
    member = CampaignMember.query.filter_by(
        id_campaign=campaign_id,
        id_user=current_user.id_user,
        status='invited'
    ).first_or_404()
    
    try:
        member.status = 'member'
        db.session.commit()
        app.logger.info(f'Запрошення до кампанії {campaign_id} прийнято')
        return {'message': 'Запрошення прийнято'}, 200
    except Exception as e:
        app.logger.error(f'Помилка при прийнятті запрошення: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при прийнятті запрошення'}, 500

@bp.route('/api/campaign/<int:campaign_id>/invite/reject', methods=['POST'])
@login_required
def reject_campaign_invite(campaign_id):
    app.logger.info(f'Спроба відхилити запрошення до кампанії {campaign_id}')
    
    member = CampaignMember.query.filter_by(
        id_campaign=campaign_id,
        id_user=current_user.id_user,
        status='invited'
    ).first_or_404()
    
    try:
        db.session.delete(member)
        db.session.commit()
        app.logger.info(f'Запрошення до кампанії {campaign_id} відхилено')
        return {'message': 'Запрошення відхилено'}, 200
    except Exception as e:
        app.logger.error(f'Помилка при відхиленні запрошення: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при відхиленні запрошення'}, 500

@bp.route('/api/campaign/<int:campaign_id>/invite/decline', methods=['POST'])
@login_required
def decline_campaign_invite(campaign_id):
    app.logger.info(f'Спроба відхилити запрошення до кампанії {campaign_id}')
    
    member = CampaignMember.query.filter_by(
        id_campaign=campaign_id,
        id_user=current_user.id_user,
        status='invited'
    ).first_or_404()
    
    try:
        db.session.delete(member)
        db.session.commit()
        app.logger.info(f'Запрошення до кампанії {campaign_id} відхилено')
        return {'message': 'Запрошення відхилено'}, 200
    except Exception as e:
        app.logger.error(f'Помилка при відхиленні запрошення: {str(e)}')
        db.session.rollback()
        return {'error': 'Помилка при відхиленні запрошення'}, 500

@bp.route('/api/campaign/<int:campaign_id>/members')
@login_required
def get_campaign_members(campaign_id):
    app.logger.info(f'Отримання списку учасників кампанії {campaign_id}')
    
    # Перевіряємо доступ до кампанії
    campaign = Campaign.query.get_or_404(campaign_id)
    if not current_user_can_view_campaign(campaign):
        app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
        abort(403)
    
    # Отримуємо список учасників кампанії
    members_list = []
    for member in campaign.members:
        if member.status == 'member':
            user = User.query.get(member.id_user)
            if user:
                members_list.append({
                    'id': user.id_user,
                    'username': user.username,
                    'email': user.email
                })
    
    # Додаємо власника кампанії
    owner = User.query.get(campaign.id_user)
    if owner and not any(m['id'] == owner.id_user for m in members_list):
        members_list.append({
            'id': owner.id_user,
            'username': owner.username,
            'email': owner.email
        })
    
    return jsonify(members_list)

@bp.route('/api/campaign/<int:campaign_id>/user/<username>/characters')
@login_required
def get_user_characters(campaign_id, username):
    app.logger.info(f'Отримання списку персонажів для користувача {username} в кампанії {campaign_id}')
    
    # Перевіряємо доступ до кампанії
    campaign = Campaign.query.get_or_404(campaign_id)
    if not current_user_can_view_campaign(campaign):
        app.logger.warning(f'Спроба несанкціонованого доступу до кампанії {campaign_id}')
        abort(403)
    
    # Знаходимо користувача за username
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    app.logger.debug(f'Знайдено користувача: {user.username} (id: {user.id_user})')
    
    # Отримуємо список персонажів користувача
    characters = Character.query.filter_by(id_user=user.id_user).all()
    app.logger.debug(f'Знайдено {len(characters)} персонажів')
    
    # Формуємо список персонажів для відповіді
    characters_list = []
    for char in characters:
        app.logger.debug(f'Обробка персонажа: {char.name} (id: {char.id_character})')
        try:
            character_data = {
                'id': char.id_character,
                'id_character': char.id_character,
                'name': char.name,
                'level': char.level,
                'class': char.class_name.class_name if char.class_name else None,
                'race': char.racial_group.racial_group if char.racial_group else None,
                'strength': char.strength,
                'dexterity': char.dexterity,
                'constitution': char.constitution,
                'intelligence': char.intelligence,
                'wisdom': char.wisdom,
                'charisma': char.charisma,
                'health_current': char.health_current,
                'health_max': char.health_max,
                'armor_class': char.armor_class,
                'initiative': char.initiative
            }
            characters_list.append(character_data)
            app.logger.debug(f'Дані персонажа успішно додано: {character_data}')
        except Exception as e:
            app.logger.error(f'Помилка при обробці персонажа {char.name}: {str(e)}')
    
    app.logger.debug(f'Підготовлено список персонажів: {characters_list}')
    return jsonify(characters_list)

@bp.route('/api/campaign/<int:campaign_id>/character/<int:character_id>', methods=['POST', 'DELETE'])
@login_required
def manage_campaign_character(campaign_id, character_id):
    app.logger.info(f'Спроба {request.method} персонажа {character_id} в кампанії {campaign_id}')
    
    campaign = Campaign.query.get_or_404(campaign_id)
    character = Character.query.get_or_404(character_id)
    
    # Перевіряємо чи користувач є власником кампанії
    is_campaign_owner = current_user_owns_campaign(campaign)
    
    # Перевіряємо чи користувач є учасником кампанії
    is_campaign_member = current_user_is_campaign_member(campaign)
    is_character_owner = character.id_user == current_user.id_user
    
    # Перевіряємо чи користувач має право керувати персонажем
    if not is_campaign_owner and not is_campaign_member:
        app.logger.warning(f'Користувач {current_user.username} не має доступу до кампанії {campaign_id}')
        abort(403)
    
    if request.method == 'DELETE':
        if not is_campaign_owner and not is_character_owner:
            abort(403)

        # Видаляємо персонажа з кампанії
        campaign_character = CampaignCharacter.query.filter_by(
            id_campaign=campaign_id,
            id_character=character_id
        ).first_or_404()
        
        try:
            db.session.delete(campaign_character)
            db.session.commit()
            return jsonify({'message': 'Character removed from campaign successfully'}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Помилка при видаленні персонажа з кампанії: {str(e)}')
            return jsonify({'message': 'Error removing character from campaign'}), 500
    
    # Додавання персонажа до кампанії (POST метод)
    if not is_campaign_owner and not is_character_owner:
        abort(403)

    # Перевіряємо чи персонаж вже не є учасником іншої кампанії
    # Перевіряємо чи персонаж вже не доданий до цієї кампанії
    existing = CampaignCharacter.query.filter_by(
        id_campaign=campaign_id,
        id_character=character_id
    ).first()
    
    if existing:
        return jsonify({'message': 'Character is already in this campaign'}), 400
    
    # Додаємо персонажа до кампанії
    campaign_character = CampaignCharacter(
        id_campaign=campaign_id,
        id_character=character_id
    )
    
    campaign_member = CampaignMember.query.filter_by(
        id_campaign=campaign_id,
        id_user=character.id_user
    ).first()

    if campaign_member:
        campaign_member.status = 'member'
    else:
        campaign_member = CampaignMember(
            id_campaign=campaign_id,
            id_user=character.id_user,
            status='member'
        )
        db.session.add(campaign_member)
    
    try:
        db.session.add(campaign_character)
        db.session.commit()
        return jsonify({'message': 'Character added to campaign successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Помилка при додаванні персонажа до кампанії: {str(e)}')
        return jsonify({'message': 'Error adding character to campaign'}), 500

@bp.route("/campaigns")
@login_required
def campaigns():
    # Отримуємо власні кампанії користувача
    owned_campaigns = Campaign.query.filter_by(id_user=current_user.id_user).all()
    
    # Отримуємо кампанії, в яких користувач є учасником або запрошений
    campaign_memberships = CampaignMember.query.filter_by(id_user=current_user.id_user).all()
    
    return render_template('campaigns.html',
                           name=current_user.username,
                           owned_campaigns=owned_campaigns,
                           campaign_memberships=campaign_memberships)

@bp.route('/create_campaign', methods=['POST'])
@login_required
def create_campaign():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name or not description:
        return 'Не всі поля заповнені', 400
    
    new_campaign = Campaign(name=name,
                           description=description,
                           id_user=current_user.id_user)
    
    db.session.add(new_campaign)
    db.session.commit()
    
    return 'OK', 200

@bp.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not current_user_owns_campaign(campaign):
        abort(403)
    
    # Видаляємо всі пов'язані записи
    CampaignMember.query.filter_by(id_campaign=campaign_id).delete()
    CampaignCharacter.query.filter_by(id_campaign=campaign_id).delete()
    Event.query.filter_by(id_campaign=campaign_id).delete()
    NPC.query.filter_by(id_campaign=campaign_id).delete()
    Location.query.filter_by(id_campaign=campaign_id).delete()
    
    db.session.delete(campaign)
    db.session.commit()
    
    return 'OK', 200

@bp.route('/accept_invitation/<int:membership_id>', methods=['POST'])
@login_required
def accept_invitation(membership_id):
    membership = CampaignMember.query.get_or_404(membership_id)
    
    if membership.id_user != current_user.id_user:
        abort(403)
    
    membership.status = 'member'
    db.session.commit()
    
    return 'OK', 200

@bp.route('/decline_invitation/<int:membership_id>', methods=['POST'])
@login_required
def decline_invitation(membership_id):
    membership = CampaignMember.query.get_or_404(membership_id)
    
    if membership.id_user != current_user.id_user:
        abort(403)
    
    db.session.delete(membership)
    db.session.commit()
    
    return 'OK', 200
