from bson import ObjectId
from ..extensions import mongo


def get_user_reviews_stats(user_id):
    """Dohvati statistiku recenzija za korisnika"""
    # Recenzije koje je korisnik dobio
    reviews_received = list(mongo.db.reviews.find({
        'reviewed_user_id': ObjectId(user_id)
    }))

    # Recenzije koje je korisnik napisao
    reviews_written = mongo.db.reviews.count_documents({
        'reviewer_user_id': ObjectId(user_id)
    })

    # Prosječna ocjena
    total_rating = sum(review['rating'] for review in reviews_received)
    avg_rating = total_rating / \
        len(reviews_received) if reviews_received else 0

    # Raspodjela ocjena
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews_received:
        rating_distribution[review['rating']] += 1

    return {
        'reviews_received': len(reviews_received),
        'reviews_written': reviews_written,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution
    }


def can_user_review(reviewer_id, reviewed_user_id):
    """Provjeri može li korisnik ocijeniti drugog korisnika"""
    # Ne može ocijeniti samog sebe
    if reviewer_id == reviewed_user_id:
        return False, "Ne možete ocijeniti samog sebe."

    # Provjeri je li već ocijenio
    existing_review = mongo.db.reviews.find_one({
        'reviewer_user_id': ObjectId(reviewer_id),
        'reviewed_user_id': ObjectId(reviewed_user_id)
    })

    if existing_review:
        return False, "Već ste ocijenili ovog korisnika."

    return True, ""
