from flask import Blueprint, render_template
from flask_login import login_required
from controllers.analyticsController import analyze

analytics = Blueprint('analytics', __name__)

@analytics.route('/stats', methods=['GET'])
@login_required
def stats():
    data = analyze()
    print("Data being passed to template:", data)  # Debug print
    return render_template('stats.html', **data)

@analytics.route('/stats/user/<int:user_id>', methods=['GET'])
@login_required
def user_stats(user_id):
    return render_template('user_stats.html', user_id=user_id)