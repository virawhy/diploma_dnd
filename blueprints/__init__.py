from .admin import bp as admin_bp
from .auth import bp as auth_bp
from .bestiary import bp as bestiary_bp
from .campaigns import bp as campaigns_bp
from .characters import bp as characters_bp
from .core import bp as core_bp
from .knowledge import bp as knowledge_bp
from .sessions import bp as sessions_bp


BLUEPRINTS = (
    bestiary_bp,
    core_bp,
    admin_bp,
    sessions_bp,
    campaigns_bp,
    characters_bp,
    auth_bp,
    knowledge_bp,
)


def register_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    add_legacy_endpoint_aliases(app)


def add_legacy_endpoint_aliases(app):
    existing_endpoints = set(app.view_functions)
    blueprint_rules = [
        rule
        for rule in app.url_map.iter_rules()
        if '.' in rule.endpoint and not rule.endpoint.startswith('static')
    ]

    for rule in blueprint_rules:
        legacy_endpoint = rule.endpoint.rsplit('.', 1)[1]
        if legacy_endpoint in existing_endpoints:
            continue

        app.add_url_rule(
            rule.rule,
            endpoint=legacy_endpoint,
            defaults=rule.defaults,
            subdomain=rule.subdomain,
            methods=rule.methods,
            build_only=True,
        )
        existing_endpoints.add(legacy_endpoint)
