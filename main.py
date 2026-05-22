from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, Blueprint, render_template, url_for, send_file, request, flash, redirect, session, abort, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, login_required, current_user, UserMixin, LoginManager, logout_user
from werkzeug.exceptions import HTTPException
import json
from markdown import markdown
import os
import secrets
from functools import wraps
from hmac import compare_digest
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dnd.db')
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


def all_monsters():
    file_path = os.path.join(BASE_DIR, 'static', 'json', 'monsters.json')
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)
    monsters = {}
    for i in data.get('results'):
        monsters[i['name']] = [i['url'][13:], i['index']]
    return monsters


monsters1 = all_monsters()


@app.route("/bestiary/<monsters_name>")
def detail_bestiary(monsters_name):
    for_api_key = ''
    monster_properties = {}
    for key, value in monsters1.items():
        if (monsters_name.lower() == value[1].lower()):
            for_api_key = value[1]
            f = open(
                f"./static/json/all_types_details/monsters/{for_api_key}.json")
            data = json.load(f)
            monster_properties = {}
            try:
                monster_properties["name"] = data["name"]
            except (IndexError, KeyError):
                monster_properties["name"] = "-"
            try:
                monster_properties["type"] = data["type"]
            except (IndexError, KeyError):
                monster_properties["type"] = "-"
            try:
                monster_properties["armor_class"] = data["armor_class"][0]["value"]
            except (IndexError, KeyError):
                monster_properties["armor_class"] = "-"
            try:
                monster_properties["speed_walk"] = data["speed"]["walk"]
            except (IndexError, KeyError):
                monster_properties["speed_walk"] = "-"
            try:
                monster_properties["speed_swim"] = data["speed"]["swim"]
            except (IndexError, KeyError):
                monster_properties["speed_swim"] = "-"
            try:
                monster_properties["strength"] = data["strength"]
            except (IndexError, KeyError):
                monster_properties["strength"] = "-"
            try:
                monster_properties["dexterity"] = data["dexterity"]
            except (IndexError, KeyError):
                monster_properties["dexterity"] = "-"
            try:
                monster_properties["constitution"] = data["constitution"]
            except (IndexError, KeyError):
                monster_properties["constitution"] = "-"
            try:
                monster_properties["intelligence"] = data["intelligence"]
            except (IndexError, KeyError):
                monster_properties["intelligence"] = "-"
            try:
                monster_properties["wisdom"] = data["wisdom"]
            except (IndexError, KeyError):
                monster_properties["wisdom"] = "-"
            try:
                monster_properties["charisma"] = data["charisma"]
            except (IndexError, KeyError):
                monster_properties["charisma"] = "-"
            try:
                monster_properties["damage_vulnerabilities"] = data["damage_vulnerabilities"]
            except (IndexError, KeyError):
                monster_properties["damage_vulnerabilities"] = []
            try:
                monster_properties["damage_resistances"] = data["damage_resistances"]
            except (IndexError, KeyError):
                monster_properties["damage_resistances"] = []
            try:
                monster_properties["damage_immunities"] = data["damage_immunities"]
            except (IndexError, KeyError):
                monster_properties["damage_immunities"] = []
            try:
                monster_properties["challenge_rating"] = data["challenge_rating"]
            except (IndexError, KeyError):
                monster_properties["challenge_rating"] = "-"
            try:
                monster_properties["hit_points"] = data["hit_points"]
            except (IndexError, KeyError):
                monster_properties["hit_points"] = "-"
            try:
                monster_properties["special_abilities_name"] = data["special_abilities"][0]["name"]
            except (IndexError, KeyError):
                monster_properties["special_abilities_name"] = "-"
            try:
                monster_properties["special_abilities_desc"] = data["special_abilities"][0]["desc"]
            except (IndexError, KeyError):
                monster_properties["special_abilities_desc"] = "-"
            try:
                monster_properties["action_name"] = data["actions"][0]["name"]
            except (IndexError, KeyError):
                monster_properties["action_name"] = "-"
            try:
                monster_properties["action_desc"] = data["actions"][0]["desc"]
            except (IndexError, KeyError):
                monster_properties["action_desc"] = "-"
            try:
                monster_properties["attack_bonus"] = data["actions"][0]["attack_bonus"]
            except (IndexError, KeyError):
                monster_properties["attack_bonus"] = "-"
            try:
                monster_properties["damage_type"] = data["actions"][0]["damage"][0]["damage_type"]["index"]
            except (IndexError, KeyError):
                monster_properties["damage_type"] = "-"
            try:
                monster_properties["image"] = data["image"]
            except (IndexError, KeyError):
                monster_properties["image"] = ""
    return render_template("bestiary.html", dict_monster_prop=monster_properties, monsters=monsters1, name=current_username())



@app.route("/", methods=("POST", "GET"))
def index():
    return render_template('index.html', name=current_username())


@app.route("/profile")
@login_required
def profile():
    characters = Character.query.filter_by(
        id_user=current_user.id_user
    ).order_by(Character.id_character.desc()).limit(4).all()
    owned_campaigns = Campaign.query.filter_by(
        id_user=current_user.id_user
    ).order_by(Campaign.id_campaign.desc()).limit(4).all()
    campaign_memberships = CampaignMember.query.filter_by(
        id_user=current_user.id_user
    ).all()
    invited_memberships = [
        membership for membership in campaign_memberships
        if membership.status == 'invited'
    ]
    all_member_campaigns = [
        membership for membership in campaign_memberships
        if membership.status == 'member'
    ]
    sessions = GameSession.query.filter_by(
        id_user=current_user.id_user
    ).order_by(GameSession.created_date.desc()).limit(4).all()

    stats = {
        'characters': Character.query.filter_by(id_user=current_user.id_user).count(),
        'owned_campaigns': Campaign.query.filter_by(id_user=current_user.id_user).count(),
        'member_campaigns': len(all_member_campaigns),
        'sessions': GameSession.query.filter_by(id_user=current_user.id_user).count(),
        'invites': len(invited_memberships),
    }

    return render_template(
        'profile.html',
        user=current_user,
        stats=stats,
        characters=characters,
        owned_campaigns=owned_campaigns,
        member_campaigns=all_member_campaigns[:4],
        invited_memberships=invited_memberships,
        sessions=sessions,
    )


@app.route("/admin")
@admin_required
def admin_panel():
    users = User.query.order_by(User.id_user.desc()).all()
    characters = Character.query.order_by(Character.id_character.desc()).limit(30).all()
    campaigns = Campaign.query.order_by(Campaign.id_campaign.desc()).limit(30).all()
    sessions_list = GameSession.query.order_by(GameSession.created_date.desc()).limit(30).all()

    stats = {
        'users': User.query.count(),
        'characters': Character.query.count(),
        'campaigns': Campaign.query.count(),
        'sessions': GameSession.query.count(),
    }

    return render_template(
        'admin.html',
        stats=stats,
        users=users,
        characters=characters,
        campaigns=campaigns,
        sessions=sessions_list,
    )


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id_user == current_user.id_user:
        flash("Не можна видалити власний акаунт з адмін-панелі.", "error")
        return redirect(url_for('admin_panel'))

    for campaign in Campaign.query.filter_by(id_user=user_id).all():
        delete_campaign_record(campaign.id_campaign)
    for character_obj in Character.query.filter_by(id_user=user_id).all():
        delete_character_record(character_obj.id_character)
    GameSession.query.filter_by(id_user=user_id).delete()
    CampaignMember.query.filter_by(id_user=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    flash("Користувача видалено.", "success")
    return redirect(url_for('admin_panel'))


@app.route("/admin/campaign/<int:campaign_id>/delete", methods=["POST"])
@admin_required
def admin_delete_campaign(campaign_id):
    delete_campaign_record(campaign_id)
    db.session.commit()
    flash("Кампанію видалено.", "success")
    return redirect(url_for('admin_panel'))


@app.route("/admin/character/<int:character_id>/delete", methods=["POST"])
@admin_required
def admin_delete_character(character_id):
    delete_character_record(character_id)
    db.session.commit()
    flash("Персонажа видалено.", "success")
    return redirect(url_for('admin_panel'))


#--------------



#---------------

@app.route("/sessions")
@login_required
def sessions():
    # Отримуємо всі сесії користувача
    user_sessions = GameSession.query.filter_by(id_user=current_user.id_user).all()
    # Отримуємо всі кампанії користувача для створення нової сесії
    user_campaigns = Campaign.query.filter_by(id_user=current_user.id_user).all()
    return render_template("sessions.html", sessions=user_sessions, campaigns=user_campaigns)

@app.route("/create_session", methods=["POST"])
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

@app.route("/session/<int:session_id>")
@login_required
def session_detail(session_id):
    game_session = get_owned_game_session_or_404(session_id)
    return render_template("encounters.html", session=game_session)

@app.route("/encounters.html")
@login_required
def encounters():
    return render_template("encounters.html")

@app.route("/api/grid", methods=["GET"])
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
@app.route("/api/grid", methods=["POST"])
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
@app.route("/api/tokens", methods=["POST", "PUT", "DELETE"])
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
@app.route("/api/initiative", methods=["POST", "GET"])
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
@app.route("/api/session/<int:session_id>/save", methods=["POST"])
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
@app.route("/api/session/<int:session_id>/load", methods=["GET"])
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
@app.route("/api/session/<int:session_id>/info", methods=["GET"])
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

@app.route("/delete_session/<int:session_id>", methods=["POST"])
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
    return 'OK', 200

@app.route("/campaign/<int:campaign_id>")
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

@app.route('/api/invites')
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
@app.route('/api/campaign/<int:campaign_id>/npc', methods=['POST'])
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

@app.route('/api/npc/<int:npc_id>', methods=['PUT', 'DELETE'])
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
@app.route('/api/campaign/<int:campaign_id>/event', methods=['POST'])
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

@app.route('/api/event/<int:event_id>', methods=['PUT', 'DELETE'])
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
@app.route('/api/campaign/<int:campaign_id>/location', methods=['POST'])
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

@app.route('/api/location/<int:location_id>', methods=['PUT', 'DELETE'])
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

@app.route('/api/campaign/<int:campaign_id>/invite', methods=['POST'])
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

@app.route('/api/campaign/<int:campaign_id>/invite/accept', methods=['POST'])
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

@app.route('/api/campaign/<int:campaign_id>/invite/reject', methods=['POST'])
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

@app.route('/api/campaign/<int:campaign_id>/invite/decline', methods=['POST'])
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

@app.route('/api/campaign/<int:campaign_id>/members')
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

@app.route('/api/campaign/<int:campaign_id>/user/<username>/characters')
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

@app.route('/api/campaign/<int:campaign_id>/character/<int:character_id>', methods=['POST', 'DELETE'])
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

@app.route("/campaigns")
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

@app.route('/create_campaign', methods=['POST'])
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

@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
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

@app.route('/accept_invitation/<int:membership_id>', methods=['POST'])
@login_required
def accept_invitation(membership_id):
    membership = CampaignMember.query.get_or_404(membership_id)
    
    if membership.id_user != current_user.id_user:
        abort(403)
    
    membership.status = 'member'
    db.session.commit()
    
    return 'OK', 200

@app.route('/decline_invitation/<int:membership_id>', methods=['POST'])
@login_required
def decline_invitation(membership_id):
    membership = CampaignMember.query.get_or_404(membership_id)
    
    if membership.id_user != current_user.id_user:
        abort(403)
    
    db.session.delete(membership)
    db.session.commit()
    
    return 'OK', 200


@app.route('/charlist.html')
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


@app.route('/delete_character/<int:character_id>', methods=['POST'])
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


@app.route("/create-char.html", methods=("POST", "GET"))
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


@app.route("/dice.html")
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
@app.route("/character/<id_class_f>", methods=("POST", "GET"))
@login_required  # Декоратор, що вимагає авторизації користувача
def character(id_class_f):
    # Отримуємо об'єкт персонажа з бази даних за його ID
    character_obj = Character.query.filter_by(id_character=id_class_f).first()

    # Якщо персонаж не знайдений, повертаємо помилку 404
    if character_obj is None:
        abort(404)
        
    # Перевіряємо, чи поточний користувач є власником персонажа
    is_owner = character_obj.id_user == current_user.id_user
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



@app.route('/auth.html', methods=("POST", "GET"))
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Акаунт із такою e-mail адресою не знайдено. Перевірте адресу або зареєструйтесь.', 'account_missing')
            return redirect(url_for('auth'))

        if not check_password_hash(user.password, password):
            flash('Пароль введено невірно.', 'error')
            return redirect(url_for('auth'))
        login_user(user)
        return redirect(url_for("profile"))

    return render_template('auth.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))


@app.route("/registration.html", methods=("POST", "GET"))
def registration():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Паролі не збігаються", "error")
            return redirect(url_for("registration"))
        if User.query.filter_by(username=username).first():
            flash("Профіль із таким нікнеймом вже існує. Оберіть інший нікнейм.", "username_taken")
            return redirect(url_for("registration"))
        else:
            try:
                hash = generate_password_hash(password)
                new_user = User(username=username, email=request.form['email'],
                                password=hash)
                db.session.add(new_user)
                db.session.flush()
                db.session.commit()
                return redirect(url_for("auth"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception("Error adding user to database: %s", e)
                flash("Не вдалося створити акаунт", "error")
    return render_template("registration.html")


#------------Бот--------------------------

def load_json_data(filename):
    file_path = os.path.join(KNOWLEDGE_JSON_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        current_app.logger.warning("Knowledge JSON not found: %s", file_path)
        return None
    except json.JSONDecodeError:
        current_app.logger.exception("Knowledge JSON is invalid: %s", file_path)
        return None
    except Exception as e:
        current_app.logger.exception("Error loading knowledge JSON %s: %s", filename, e)
        return None

@app.template_filter('markdown')
def markdown_filter(text):
    if isinstance(text, str):
        return markdown(text)
    return text

@app.route("/knowledge/rules")
def knowledge_rules():
    rules = load_json_data('rules.json')
    return render_template('knowledge_rules.html', rules=rules, name=current_username())

@app.route("/knowledge/character")
def knowledge_character():
    character = load_json_data('character_basics.json')
    return render_template('knowledge_character.html', character=character, name=current_username())

@app.route("/knowledge/races")
def knowledge_races():
    races = load_json_data('races.json')
    return render_template('knowledge_races.html', races=races, name=current_username())

@app.route("/knowledge/classes")
def knowledge_classes():
    classes = load_json_data('classes.json')
    return render_template('knowledge_classes.html', classes=classes, name=current_username())


@app.route("/knowledge/bestiary")
def knowledge_bestiary():
    bestiary = load_json_data('monsters.json')
    return render_template('knowledge_bestiary.html', bestiary=bestiary, name=current_username())


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
