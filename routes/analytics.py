from flask import Blueprint, render_template
from flask_login import login_required

analytics = Blueprint('analytics', __name__)

@analytics.route('/stats',methods=['GET'])
@login_required
def stats():
    # TODO: Implement analytics stats
    return render_template('stats.html')