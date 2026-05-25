from flask import Blueprint

from main import *


bp = Blueprint('sessions', __name__)


@bp.route("/sessions")
@login_required
def sessions():
    # Отримуємо всі сесії користувача
    user_sessions = GameSession.query.filter_by(id_user=current_user.id_user).all()
    # Отримуємо всі кампанії користувача для створення нової сесії
    user_campaigns = Campaign.query.filter_by(id_user=current_user.id_user).all()
    return render_template("sessions.html", sessions=user_sessions, campaigns=user_campaigns)

@bp.route("/create_session", methods=["POST"])
@login_required
def create_session():
    name = request.form.get('session_name')
    description = request.form.get('session_description')
    campaign_id = request.form.get('campaign_id')
    
    if name and description and campaign_id:
        # Перевіряємо чи кампанія належить користувачу
        campaign = Campaign.query.filter_by(id_campaign=campaign_id, id_user=current_user.id_user).first()
        if campaign:
            new_session = GameSession(
                name=name,
                description=description,
                id_campaign=campaign_id,
                id_user=current_user.id_user
            )
            db.session.add(new_session)
            db.session.commit()
            flash('Сесію успішно створено!', 'success')
        else:
            flash('Помилка: кампанія не знайдена!', 'error')
    else:
        flash('Помилка: заповніть всі поля!', 'error')
    
    return redirect('/sessions')

@bp.route("/session/<int:session_id>")
@login_required
def session_detail(session_id):
    game_session = get_owned_game_session_or_404(session_id)
    return render_template("encounters.html", session=game_session)

@bp.route("/encounters.html")
@login_required
def encounters():
    return render_template("encounters.html")

@bp.route("/api/grid", methods=["GET"])
@login_required
def get_grid_data():
    # Отримуємо список файлів з папок для спрайтів
    tokens = os.listdir(os.path.join(app.static_folder, 'sprites/tokens'))
    objects = os.listdir(os.path.join(app.static_folder, 'sprites/objects'))
    environment = os.listdir(os.path.join(app.static_folder, 'sprites/environment'))
    
    # Фільтруємо тільки PNG файли
    tokens = [f for f in tokens if f.lower().endswith('.png')]
    objects = [f for f in objects if f.lower().endswith('.png')]
    environment = [f for f in environment if f.lower().endswith('.png')]
    
    return jsonify({
        'tokens': tokens,
        'objects': objects,
        'environment': environment
    })

# API для роботи з сіткою
@bp.route("/api/grid", methods=["POST"])
@login_required
def update_grid():
    try:
        data = request.get_json()
        # Тут буде логіка збереження стану сітки
        return jsonify({"status": "success"})
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API для роботи з токенами
@bp.route("/api/tokens", methods=["POST", "PUT", "DELETE"])
@login_required
def manage_tokens():
    try:
        if request.method == "POST":
            data = request.get_json()
            # Логіка додавання нового токена
            return jsonify({"status": "success", "token_id": "new_id"})
        elif request.method == "PUT":
            data = request.get_json()
            # Логіка оновлення позиції токена
            return jsonify({"status": "success"})
        else:
            # Логіка видалення токена
            return jsonify({"status": "success"})
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API для роботи з ініціативою
@bp.route("/api/initiative", methods=["POST", "GET"])
@login_required
def manage_initiative():
    try:
        if request.method == "POST":
            data = request.get_json()
            # Логіка оновлення порядку ініціативи
            return jsonify({"status": "success"})
        else:
            # Логіка отримання поточного порядку ініціативи
            return jsonify({"initiative_order": []})
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API для збереження сесії
@bp.route("/api/session/<int:session_id>/save", methods=["POST"])
@login_required
def save_session(session_id):
    try:
        game_session = get_owned_game_session_or_404(session_id)
        data = request.get_json()
        
        # Створюємо структуру для збереження
        save_data = {
            "session_id": game_session.id_session,
            "grid_width": data.get("grid_width"),
            "grid_height": data.get("grid_height"),
            "tokens": data.get("tokens", []),
            "initiative_list": data.get("initiative_list", []),
            "saved_at": datetime.now().isoformat()
        }
        
        # Зберігаємо у JSON файл
        os.makedirs(app.config['SESSION_SAVE_DIR'], exist_ok=True)
        save_path = session_save_path(session_id)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"status": "success", "message": "Сесію збережено"})
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API для завантаження сесії
@bp.route("/api/session/<int:session_id>/load", methods=["GET"])
@login_required
def load_session(session_id):
    try:
        get_owned_game_session_or_404(session_id)
        save_path = session_save_path(session_id)
        
        if not os.path.exists(save_path):
            return jsonify({"has_save": False})
        
        with open(save_path, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
            
        return jsonify({
            "has_save": True,
            "data": save_data
        })
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API для отримання інформації про сесію
@bp.route("/api/session/<int:session_id>/info", methods=["GET"])
@login_required
def get_session_info(session_id):
    try:
        game_session = get_owned_game_session_or_404(session_id)
        session_info = {
            "id": game_session.id_session,
            "name": game_session.name,
            "description": game_session.description,
            "created_date": game_session.created_date.isoformat(),
            "campaign_id": game_session.id_campaign,
            "user_id": game_session.id_user
        }
        
        return jsonify(session_info)
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/delete_session/<int:session_id>", methods=["POST"])
@login_required
def delete_session(session_id):
    game_session = get_owned_game_session_or_404(session_id)
    
    # Видаляємо файл збереження сесії, якщо він існує
    save_path = session_save_path(session_id)
    if os.path.exists(save_path):
        os.remove(save_path)
    
    # Видаляємо сесію з бази даних
    db.session.delete(game_session)
    db.session.commit()
    
    flash('Сесію успішно видалено!', 'success')
