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