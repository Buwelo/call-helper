import logging
from flask import render_template
from sqlalchemy import func
from config.extensions import db
from models.transcript import UserTranscript


def analyze():
    # Query for number of tests taken per month
    tests_per_month = db.session.query(
        func.date_trunc('month', UserTranscript.created_at).label('month'),
        func.count(UserTranscript.id).label('test_count')
    ).group_by(func.date_trunc('month', UserTranscript.created_at)
               ).order_by('month').all()

    # Convert the result to a dictionary for easier use in the template
    tests_per_month_dict = {
        str(result.month.date()): result.test_count for result in tests_per_month}  
    logging.info(f'Tests per month: {tests_per_month}')
    
    all_transcripts = db.session.query(UserTranscript).all()
    logging.info(f'All transcripts: {all_transcripts}')

    render_template('stats.html', tests_per_month=tests_per_month_dict)

# get number of tests taken
# get highest scores per user (top 10)
# tests taken over time
# export scores
