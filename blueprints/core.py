from flask import Blueprint

from main import *


bp = Blueprint('core', __name__)


@bp.route("/", methods=("POST", "GET"))
def index():
    return render_template('index.html', name=current_username())


@bp.route("/profile")
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
