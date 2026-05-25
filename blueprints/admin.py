from flask import Blueprint

from main import *


bp = Blueprint('admin', __name__)


@bp.route("/admin")
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


@bp.route("/admin/user/<int:user_id>/delete", methods=["POST"])
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


@bp.route("/admin/campaign/<int:campaign_id>/delete", methods=["POST"])
@admin_required
def admin_delete_campaign(campaign_id):
    delete_campaign_record(campaign_id)
    db.session.commit()
    flash("Кампанію видалено.", "success")
    return redirect(url_for('admin_panel'))


@bp.route("/admin/character/<int:character_id>/delete", methods=["POST"])
@admin_required
def admin_delete_character(character_id):
    delete_character_record(character_id)
    db.session.commit()
    flash("Персонажа видалено.", "success")
    return redirect(url_for('admin_panel'))


#--------------



