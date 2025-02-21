from flask import Blueprint, render_template
from flask_login import login_required
from controllers.analyticsController import analyze

analytics = Blueprint('analytics', __name__)

@analytics.route('/stats',methods=['GET'])
@login_required
def stats():
    # TODO: Implement analytics stats
    analyze()  # Call the analyze function to get the stats data
    # Use the stats data to render the stats.html template with the necessary data for visualization and analysis.
    return render_template('stats.html')