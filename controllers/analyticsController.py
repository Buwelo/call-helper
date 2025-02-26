from collections import defaultdict
import logging
from flask import render_template
from sqlalchemy import func
from config.extensions import db
from models.transcript import UserTranscript
from models.user import User


def analyze():
    top_scores = db.session.query(
        func.concat(User.first_name, ' ', User.last_name).label('full_name'),
        UserTranscript.overall_score,
        UserTranscript.testing_id,
        User.id.label('user_id'),
        UserTranscript.created_at  # Add created_at to the query
    ).join(User, User.id == UserTranscript.user_id
    ).order_by(UserTranscript.overall_score.desc()
    ).all()

    # Aggregate scores for the same testing_id
    aggregated_scores = defaultdict(lambda: {'name': '', 'score': 0, 'count': 0, 'user_id': None, 'created_at': None})
    for name, score, testing_id, user_id, created_at in top_scores:
        if testing_id is not None:
            entry = aggregated_scores[testing_id]
            if entry['score'] < (score or 0):  # Update only if this score is higher
                entry['name'] = name
                entry['user_id'] = user_id
                entry['created_at'] = created_at
            entry['score'] += score if score is not None else 0
            entry['count'] += 1
        else:
            # For records without testing_id, treat them individually
            aggregated_scores[f'individual_{name}_{score}'] = {
                'name': name, 
                'score': score if score is not None else 0, 
                'count': 1,
                'user_id': user_id,
                'created_at': created_at
            }

    # Calculate average scores and format the result
    top_scores_list = [
        {
            "name": data['name'],
            "score": round(data['score'] / data['count'], 2),
            "testing_id": testing_id if not testing_id.startswith('individual_') else None,
            "user_id": data['user_id'],
            "created_at": data['created_at']  # Include created_at in the result
        }
        for testing_id, data in aggregated_scores.items()
    ]

    # Sort the aggregated scores
    top_scores_list.sort(key=lambda x: x['score'], reverse=True)

    logging.info(f'Top scores: {top_scores_list}')
    return {
            'top_scores': top_scores_list,
        }

# get number of tests taken
# get highest scores per user (top 10)
# tests taken over time
# export scores
