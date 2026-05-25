from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, Blueprint, render_template, url_for, send_file, request, flash, redirect, session, abort, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, login_required, current_user, UserMixin, LoginManager, logout_user
from werkzeug.exceptions import HTTPException
import json
from markdown import markdown
import os
import sys
import secrets
from functools import wraps
from hmac import compare_digest
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

sys.modules.setdefault('main', sys.modules[__name__])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_JSON_DIR = os.path.join(BASE_DIR, 'static', 'json', 'knowledge_json')
MUTATING_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')


class Base(DeclarativeBase):
    pass

app = Flask(__name__, static_folder='static')
secret_key = os.environ.get('SECRET_KEY')
is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') == 'true'
if is_production and not secret_key:
    raise RuntimeError('SECRET_KEY must be set in production')

app.config['SECRET_KEY'] = secret_key or secrets.token_hex(32)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///dnd.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Налаштування cookie-сесій для окремого логіну кожного користувача
app.config['SESSION_COOKIE_NAME'] = 'dnd_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SECURE'] = is_production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_SAVE_DIR'] = os.path.join(BASE_DIR, 'session_saves')

# Створюємо планувальник
scheduler = BackgroundScheduler()

# Функція для запуску скрипта create_knowledge_json
def run_create_knowledge_json():
    script_path = os.path.join(BASE_DIR, 'scripts', 'create_knowledge_json.py')
    subprocess.run(['python', script_path], check=True)

# Додаємо завдання до планувальника (щосереди о 21:00)
scheduler.add_job(
    func=run_create_knowledge_json,
    trigger=CronTrigger(day_of_week='wed', hour=21, minute=0),
    id='create_knowledge_json_job',
    name='Create Knowledge JSON',
    replace_existing=True
)

# Start scheduled jobs only for the process that explicitly owns background work.
if os.environ.get('ENABLE_SCHEDULER') == '1':
    scheduler.start()


def get_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': get_csrf_token}


@app.before_request
def protect_against_csrf():
    if request.method not in MUTATING_METHODS:
        return

    expected_token = session.get('_csrf_token')
    provided_token = (
        request.headers.get('X-CSRFToken')
        or request.headers.get('X-CSRF-TOKEN')
        or request.form.get('_csrf_token')
    )

    if not expected_token or not provided_token or not compare_digest(expected_token, provided_token):
        abort(400, description='Invalid CSRF token')


@app.after_request
def add_csrf_helper(response):
    content_type = response.headers.get('Content-Type', '')
    if response.direct_passthrough or 'text/html' not in content_type.lower():
        return response

    html = response.get_data(as_text=True)
    if '</head>' not in html:
        return response

    token = get_csrf_token()
    csrf_markup = f'''
    <meta name="csrf-token" content="{token}">
    <script>
    (function() {{
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!token) return;

        const mutatingMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
        const originalFetch = window.fetch;
        window.fetch = function(resource, options) {{
            options = options || {{}};
            const method = (options.method || 'GET').toUpperCase();
            const url = typeof resource === 'string' ? resource : resource.url;
            const sameOrigin = !url || url.startsWith('/') || url.startsWith(window.location.origin);

            if (sameOrigin && mutatingMethods.has(method)) {{
                const headers = new Headers(options.headers || {{}});
                headers.set('X-CSRFToken', token);
                options.headers = headers;
            }}

            return originalFetch.call(this, resource, options);
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('form').forEach(function(form) {{
                const method = (form.getAttribute('method') || 'GET').toUpperCase();
                if (!mutatingMethods.has(method) || form.querySelector('input[name="_csrf_token"]')) return;

                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = '_csrf_token';
                input.value = token;
                form.appendChild(input);
            }});
        }});
    }})();
    </script>
    '''
    response.set_data(html.replace('</head>', csrf_markup + '\n</head>', 1))
    return response

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    characters = db.relationship('Character', backref='user', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id_user)

class Character(db.Model):
    __tablename__ = 'character'
    __table_args__ = (
        CheckConstraint('level BETWEEN 1 AND 20', name='ck_character_level_range'),
        CheckConstraint('health_current >= 0', name='ck_character_health_current_nonnegative'),
        CheckConstraint('health_max >= 1', name='ck_character_health_max_positive'),
        CheckConstraint('armor_class >= 0', name='ck_character_armor_class_nonnegative'),
        Index('ix_character_user', 'id_user'),
    )

    id_character = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    armor_class = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    initiative = db.Column(db.Integer, nullable=False)
    health_current = db.Column(db.Integer, nullable=False)
    health_max = db.Column(db.Integer, nullable=False)
    proficiency_bonus = db.Column(db.Integer, nullable=False)
    inspiration = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text, nullable=False, default='')
    id_class = db.Column(db.Integer, db.ForeignKey('class.id_class'), nullable=False)
    id_racial_group = db.Column(db.Integer, db.ForeignKey('racial_group.id_racial_group'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    attacks = db.relationship('Attack', backref='character', lazy=True, cascade='all, delete-orphan', order_by='Attack.sort_order')

class Attack(db.Model):
    __tablename__ = 'attack'
    __table_args__ = (
        CheckConstraint('attack_bonus >= 0', name='ck_attack_bonus_nonnegative'),
        Index('ix_attack_character', 'id_character'),
    )

    id_attack = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    attack_bonus = db.Column(db.Integer, nullable=False)
    damage_type = db.Column(db.String(255), nullable=False, default='')
    action_type = db.Column(db.String(20), nullable=False, default='attack')
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    id_character = db.Column(db.Integer, db.ForeignKey('character.id_character'), nullable=False)

class Class(db.Model):
    __tablename__ = 'class'
    id_class = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(80), unique=True, nullable=False)
    characters = db.relationship('Character', backref='class_name', lazy=True)

class RacialGroup(db.Model):
    __tablename__ = 'racial_group'
    id_racial_group = db.Column(db.Integer, primary_key=True)
    racial_group = db.Column(db.String(80), unique=True, nullable=False)
    characters = db.relationship('Character', backref='racial_group', lazy=True)

class Proficiency(db.Model):
    __tablename__ = 'proficiency'
    id_proficiency = db.Column(db.Integer, primary_key=True)
    proficiency = db.Column(db.String(80), unique=True, nullable=False)
    character_proficiencies = db.relationship('CharacterProficiency', backref='proficiency', lazy=True)

class CharacterProficiency(db.Model):
    __tablename__ = 'character_proficiency'
    __table_args__ = (
        UniqueConstraint('id_character', 'id_proficiency', name='uq_character_proficiency'),
        Index('ix_character_proficiency_character', 'id_character'),
        Index('ix_character_proficiency_proficiency', 'id_proficiency'),
    )

    id_character_proficiency = db.Column(db.Integer, primary_key=True)
    checker = db.Column(db.Boolean, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    id_proficiency = db.Column(db.Integer, db.ForeignKey('proficiency.id_proficiency'), nullable=False)
    id_character = db.Column(db.Integer, db.ForeignKey('character.id_character'), nullable=False)

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id_equipment = db.Column(db.Integer, primary_key=True)
    equipment = db.Column(db.String(80), unique=True, nullable=False)
    character_equipments = db.relationship('CharacterEquipment', backref='equipment', lazy=True)

class CharacterEquipment(db.Model):
    __tablename__ = 'character_equipment'
    __table_args__ = (
        UniqueConstraint('id_character', 'id_equipment', name='uq_character_equipment'),
        Index('ix_character_equipment_character', 'id_character'),
        Index('ix_character_equipment_equipment', 'id_equipment'),
    )

    id_character_equipment = db.Column(db.Integer, primary_key=True)
    checker = db.Column(db.Boolean, nullable=False)
    id_equipment = db.Column(db.Integer, db.ForeignKey('equipment.id_equipment'), nullable=False)
    id_character = db.Column(db.Integer, db.ForeignKey('character.id_character'), nullable=False)

class Campaign(db.Model):
    __tablename__ = 'campaign'
    __table_args__ = (
        Index('ix_campaign_owner', 'id_user'),
    )

    id_campaign = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    owner = db.relationship('User', backref='campaigns', lazy=True)
    members = db.relationship('CampaignMember', backref='campaign', lazy=True, cascade='all, delete-orphan')

class CampaignMember(db.Model):
    __tablename__ = 'campaign_member'
    __table_args__ = (
        UniqueConstraint('id_campaign', 'id_user', name='uq_campaign_member_user'),
        CheckConstraint("status IN ('invited', 'member')", name='ck_campaign_member_status'),
        Index('ix_campaign_member_campaign', 'id_campaign'),
        Index('ix_campaign_member_user', 'id_user'),
    )

    id_campaign_member = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)  # 'invited' або 'member'
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    user = db.relationship('User', backref='campaign_memberships', lazy=True)

class NPC(db.Model):
    __tablename__ = 'npc'
    __table_args__ = (Index('ix_npc_campaign', 'id_campaign'),)

    id_npc = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    campaign = db.relationship('Campaign', backref='npcs', lazy=True)

class Event(db.Model):
    __tablename__ = 'event'
    __table_args__ = (Index('ix_event_campaign', 'id_campaign'),)

    id_event = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    campaign = db.relationship('Campaign', backref='events', lazy=True)

class Location(db.Model):
    __tablename__ = 'location'
    __table_args__ = (Index('ix_location_campaign', 'id_campaign'),)

    id_location = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    campaign = db.relationship('Campaign', backref='locations', lazy=True)

class CampaignCharacter(db.Model):
    __tablename__ = 'campaign_character'
    __table_args__ = (
        UniqueConstraint('id_campaign', 'id_character', name='uq_campaign_character'),
        Index('ix_campaign_character_campaign', 'id_campaign'),
        Index('ix_campaign_character_character', 'id_character'),
    )

    id_campaign_character = db.Column(db.Integer, primary_key=True)
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    id_character = db.Column(db.Integer, db.ForeignKey('character.id_character'), nullable=False)
    campaign = db.relationship('Campaign', backref='campaign_characters', lazy=True)
    character = db.relationship('Character', backref='campaign_characters', lazy=True)

class GameSession(db.Model):
    __tablename__ = 'game_session'
    __table_args__ = (
        Index('ix_game_session_campaign', 'id_campaign'),
        Index('ix_game_session_user', 'id_user'),
    )

    id_session = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    session_data = db.Column(db.JSON, nullable=True)  # JSON для збереження стану сесії
    id_campaign = db.Column(db.Integer, db.ForeignKey('campaign.id_campaign'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    campaign = db.relationship('Campaign', backref='game_sessions', lazy=True)
    user = db.relationship('User', backref='game_sessions', lazy=True)

login_manager = LoginManager()
login_manager.login_view = 'auth'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))


def current_username():
    return current_user.username if current_user.is_authenticated else None


def configured_admin_emails():
    return {
        email.strip().lower()
        for email in os.environ.get('ADMIN_EMAILS', '').split(',')
        if email.strip()
    }


def configured_admin_usernames():
    return {
        username.strip().lower()
        for username in os.environ.get('ADMIN_USERNAMES', '').split(',')
        if username.strip()
    }


def current_user_is_admin():
    if not current_user.is_authenticated:
        return False

    admin_emails = configured_admin_emails()
    admin_usernames = configured_admin_usernames()

    return (
        current_user.email.lower() in admin_emails
        or current_user.username.lower() in admin_usernames
    )


@app.context_processor
def inject_admin_status():
    return {'is_admin': current_user_is_admin}


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user_is_admin():
            abort(403)
        return view_func(*args, **kwargs)

    return login_required(wrapped_view)


def delete_character_record(character_id):
    character_obj = Character.query.get_or_404(character_id)
    CharacterProficiency.query.filter_by(id_character=character_id).delete()
    CharacterEquipment.query.filter_by(id_character=character_id).delete()
    CampaignCharacter.query.filter_by(id_character=character_id).delete()
    db.session.delete(character_obj)


def delete_campaign_record(campaign_id):
    GameSession.query.filter_by(id_campaign=campaign_id).delete()
    CampaignCharacter.query.filter_by(id_campaign=campaign_id).delete()
    NPC.query.filter_by(id_campaign=campaign_id).delete()
    Event.query.filter_by(id_campaign=campaign_id).delete()
    Location.query.filter_by(id_campaign=campaign_id).delete()
    CampaignMember.query.filter_by(id_campaign=campaign_id).delete()

    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)


def get_owned_game_session_or_404(session_id):
    game_session = GameSession.query.get_or_404(session_id)
    if game_session.id_user != current_user.id_user:
        abort(403)
    return game_session


def session_save_path(session_id):
    return os.path.join(app.config['SESSION_SAVE_DIR'], f"session_{session_id}.json")


def current_user_owns_campaign(campaign):
    return campaign.id_user == current_user.id_user


def current_user_is_campaign_member(campaign):
    return any(member.id_user == current_user.id_user and member.status == 'member' for member in campaign.members)


def current_user_can_view_campaign(campaign):
    return current_user_owns_campaign(campaign) or current_user_is_campaign_member(campaign)


EQUIPMENT_GROUPS = [
    {
        'title': 'Оберіть зброю',
        'items': ['Спис', 'Лук', 'Полуторний меч', 'Проста зброя'],
    },
    {
        'title': 'Оберіть обладунок',
        'items': [
            'Лускатий обладунок (17)',
            'Кольчужний обладунок (16)',
            'Клепаний шкіряний обладунок (14)',
            'Шкіряний обладунок (12)',
        ],
    },
    {
        'title': 'Оберіть спорядження',
        'items': ['Молитовник', 'Святий символ', 'Набір дослідника', 'Ремісничі інструменти'],
    },
]


def standard_equipment_names():
    return [item for group in EQUIPMENT_GROUPS for item in group['items']]


def sync_character_equipments(character_id, selected_equipments, custom_equipment_text=''):
    custom_equipments = [
        item.strip()
        for item in (custom_equipment_text or '').replace('\r\n', '\n').split('\n')
        if item.strip()
    ]

    equipment_names = []
    seen_names = set()
    for equipment_name in [*selected_equipments, *custom_equipments]:
        if equipment_name in seen_names:
            continue
        seen_names.add(equipment_name)
        equipment_names.append(equipment_name)

    CharacterEquipment.query.filter_by(id_character=character_id).delete()

    for equipment_name in equipment_names:
        equipment = Equipment.query.filter_by(equipment=equipment_name).first()
        if equipment is None:
            equipment = Equipment(equipment=equipment_name)
            db.session.add(equipment)
            db.session.flush()

        db.session.add(CharacterEquipment(
            checker=True,
            id_equipment=equipment.id_equipment,
            id_character=character_id,
        ))




def register_routes():
    from blueprints import register_blueprints

    register_blueprints(app)


register_routes()

def create_tables():
    # Список класів
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

    # Список рас
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

    # Створення базових профіцієнцій
    proficiencies = [
        'Акробатика',
        'Атлетика',
        'Виживання',
        'Виступ',
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
        'Догляд за тваринами'
    ]

    # Створення базового обладнання
    equipments = [
        'Короткий меч',
        'Довгий меч',
        'Кинджал',
        'Бойовий молот',
        'Легкий арбалет',
        'Важкий арбалет',
        'Лук',
        'Спис',
        'Полуторний меч',
        'Проста зброя',
        'Щит',
        'Шкіряна броня',
        'Кольчуга',
        'Латна броня',
        'Лускатий обладунок (17)',
        'Кольчужний обладунок (16)',
        'Клепаний шкіряний обладунок (14)',
        'Шкіряний обладунок (12)',
        'Молитовник',
        'Святий символ',
        'Набір дослідника',
        'Ремісничі інструменти'
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

    # Додавання профіцієнцій
    for prof_name in proficiencies:
        if not Proficiency.query.filter_by(proficiency=prof_name).first():
            new_prof = Proficiency(proficiency=prof_name)
            db.session.add(new_prof)

    # Додавання обладнання
    for equipment_name in equipments:
        if not Equipment.query.filter_by(equipment=equipment_name).first():
            new_equipment = Equipment(equipment=equipment_name)
            db.session.add(new_equipment)

    # Збереження змін
    db.session.commit()
    print('Seed data added to database.')


def initialize_database():
    if os.environ.get('SKIP_DB_INIT') == '1':
        return

    with app.app_context():
        db.create_all()
        create_tables()


initialize_database()


if __name__ == '__main__':
    app.run(
        debug=os.environ.get('FLASK_DEBUG') == '1',
        port=int(os.environ.get('PORT', 5000)),
    )
