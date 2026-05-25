from flask import Blueprint

from main import *


bp = Blueprint('knowledge', __name__)


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

@bp.app_template_filter('markdown')
def markdown_filter(text):
    if isinstance(text, str):
        return markdown(text)
    return text

@bp.route("/knowledge/rules")
def knowledge_rules():
    rules = load_json_data('rules.json')
    return render_template('knowledge_rules.html', rules=rules, name=current_username())

@bp.route("/knowledge/character")
def knowledge_character():
    character = load_json_data('character_basics.json')
    return render_template('knowledge_character.html', character=character, name=current_username())

@bp.route("/knowledge/races")
def knowledge_races():
    races = load_json_data('races.json')
    return render_template('knowledge_races.html', races=races, name=current_username())

@bp.route("/knowledge/classes")
def knowledge_classes():
    classes = load_json_data('classes.json')
    return render_template('knowledge_classes.html', classes=classes, name=current_username())


@bp.route("/knowledge/bestiary")
def knowledge_bestiary():
    bestiary = load_json_data('monsters.json')
    return render_template('knowledge_bestiary.html', bestiary=bestiary, name=current_username())
