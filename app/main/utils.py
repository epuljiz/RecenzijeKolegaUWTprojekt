from datetime import datetime


def format_date(value, format='%d.%m.%Y.'):
    """Formatiraj datum za prikaz u templateovima"""
    if isinstance(value, datetime):
        return value.strftime(format)
    return value


def get_user_stats(user_id):
    """Dohvati statistiku korisnika"""
    from ..extensions import mongo
    from bson import ObjectId

    # Broj recenzija koje je korisnik dobio
    reviews_received = mongo.db.reviews.count_documents({
        'reviewed_user_id': ObjectId(user_id)
    })

    # Prosječna ocjena
    pipeline = [
        {'$match': {'reviewed_user_id': ObjectId(user_id)}},
        {'$group': {'_id': None, 'avg_rating': {'$avg': '$rating'}}}
    ]

    result = list(mongo.db.reviews.aggregate(pipeline))
    avg_rating = result[0]['avg_rating'] if result else 0

    return {
        'reviews_received': reviews_received,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0
    }
