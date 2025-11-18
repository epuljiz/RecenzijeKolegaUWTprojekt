from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from bson import ObjectId
from datetime import datetime
import bleach
from . import reviews_bp
from ..extensions import mongo
from ..models import User

admin_permission = Permission(RoleNeed('admin'))

@reviews_bp.route('/reviews')
def reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    skip = (page - 1) * per_page

    # Filtri
    rating_filter = request.args.get('rating', type=int)
    project_filter = request.args.get('project_type', '')

    query = {}
    if rating_filter:
        query['rating'] = {'$gte': rating_filter}
    if project_filter:
        query['project_type'] = project_filter

    # Dohvati recenzije s paginacijom
    all_reviews = list(mongo.db.reviews.find(query)
                       .sort('date_created', -1)
                       .skip(skip)
                       .limit(per_page))

    total_reviews = mongo.db.reviews.count_documents(query)
    total_pages = (total_reviews + per_page - 1) // per_page

    # Pripremi podatke za prikaz
    for review in all_reviews:
        reviewer = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
        reviewed_user = mongo.db.users.find_one(
            {'_id': review['reviewed_user_id']})

        review['reviewer_name'] = reviewer['name'] if reviewer else 'Nepoznat korisnik'
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime(
            '%d.%m.%Y. %H:%M')

    return render_template('reviews/reviews.html',
                           reviews=all_reviews,
                           page=page,
                           total_pages=total_pages,
                           rating_filter=rating_filter,
                           project_filter=project_filter)


@reviews_bp.route('/add_review', methods=['GET', 'POST'])
@login_required
def add_review():
    form = ReviewForm()

    if form.validate_on_submit():
        reviewed_user_email = form.reviewed_user_email.data
        rating = form.rating.data
        comment = bleach.clean(form.comment.data)  # Sanitizacija HTML-a
        project_type = form.project_type.data

        # Pronađi korisnika koji se recenzira
        reviewed_user = mongo.db.users.find_one({'email': reviewed_user_email})
        if not reviewed_user:
            flash('Korisnik s ovom email adresom ne postoji.', 'danger')
            return render_template('reviews/add_review.html', form=form)

        # Provjeri da li je korisnik pokušao ocijeniti samog sebe
        if reviewed_user['_id'] == ObjectId(current_user.id):
            flash('Ne možete ocijeniti samog sebe.', 'danger')
            return render_template('reviews/add_review.html', form=form)

        # Provjeri da li je već ocijenio ovog korisnika
        existing_review = mongo.db.reviews.find_one({
            'reviewer_user_id': ObjectId(current_user.id),
            'reviewed_user_id': reviewed_user['_id']
        })

        if existing_review:
            flash('Već ste ocijenili ovog korisnika.', 'warning')
            return render_template('reviews/add_review.html', form=form)

        # Spremi recenziju
        review_data = {
            'reviewer_user_id': ObjectId(current_user.id),
            'reviewed_user_id': reviewed_user['_id'],
            'rating': rating,
            'comment': comment,
            'project_type': project_type,
            'date_created': datetime.utcnow(),
            'last_updated': datetime.utcnow()
        }

        mongo.db.reviews.insert_one(review_data)
        flash('Recenzija uspješno dodana!', 'success')
        return redirect(url_for('reviews.reviews'))

    return render_template('reviews/add_review.html', form=form)


@reviews_bp.route('/my_reviews')
@login_required
def my_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page

    # Dohvati recenzije koje je korisnik napisao
    my_reviews_list = list(mongo.db.reviews.find({'reviewer_user_id': ObjectId(current_user.id)})
                           .sort('date_created', -1)
                           .skip(skip)
                           .limit(per_page))

    total_reviews = mongo.db.reviews.count_documents(
        {'reviewer_user_id': ObjectId(current_user.id)})
    total_pages = (total_reviews + per_page - 1) // per_page

    # Pripremi podatke za prikaz
    for review in my_reviews_list:
        reviewed_user = mongo.db.users.find_one(
            {'_id': review['reviewed_user_id']})
        review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
        review['formatted_date'] = review['date_created'].strftime(
            '%d.%m.%Y. %H:%M')

    return render_template('reviews/my_reviews.html',
                           reviews=my_reviews_list,
                           page=page,
                           total_pages=total_pages)


@reviews_bp.route('/edit_review/<review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = mongo.db.reviews.find_one({'_id': ObjectId(review_id)})

    if not review:
        abort(404)

    # Provjeri permisije
    if review['reviewer_user_id'] != ObjectId(current_user.id) and not admin_permission.can():
        abort(403)

    form = EditReviewForm()

    if form.validate_on_submit():
        # Ažuriraj recenziju
        update_data = {
            'rating': form.rating.data,
            'comment': bleach.clean(form.comment.data),
            'project_type': form.project_type.data,
            'last_updated': datetime.utcnow()
        }

        mongo.db.reviews.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': update_data}
        )

        flash('Recenzija uspješno ažurirana!', 'success')
        return redirect(url_for('reviews.my_reviews'))

    # Popuni formu s postojećim podacima
    if request.method == 'GET':
        form.rating.data = review['rating']
        form.comment.data = review['comment']
        form.project_type.data = review.get('project_type', '')

    # Dohvati ime recenziranog korisnika za prikaz
    reviewed_user = mongo.db.users.find_one(
        {'_id': review['reviewed_user_id']})
    reviewed_user_name = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'

    return render_template('reviews/edit_review.html',
                           form=form,
                           review=review,
                           reviewed_user_name=reviewed_user_name)


@reviews_bp.route('/delete_review/<review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = mongo.db.reviews.find_one({'_id': ObjectId(review_id)})

    if not review:
        abort(404)

    # Provjeri permisije
    if review['reviewer_user_id'] != ObjectId(current_user.id) and not admin_permission.can():
        abort(403)

    mongo.db.reviews.delete_one({'_id': ObjectId(review_id)})
    flash('Recenzija uspješno obrisana!', 'success')

    return redirect(url_for('reviews.my_reviews'))


@reviews_bp.route('/review/<review_id>')
def review_detail(review_id):
    review = mongo.db.reviews.find_one({'_id': ObjectId(review_id)})

    if not review:
        abort(404)

    # Dohvati podatke o korisnicima
    reviewer = mongo.db.users.find_one({'_id': review['reviewer_user_id']})
    reviewed_user = mongo.db.users.find_one(
        {'_id': review['reviewed_user_id']})

    review['reviewer_name'] = reviewer['name'] if reviewer else 'Nepoznat korisnik'
    review['reviewed_user_name'] = reviewed_user['name'] if reviewed_user else 'Nepoznat korisnik'
    review['reviewer_faculty'] = reviewer.get(
        'faculty', '') if reviewer else ''
    review['reviewed_user_faculty'] = reviewed_user.get(
        'faculty', '') if reviewed_user else ''
    review['formatted_date'] = review['date_created'].strftime(
        '%d. %B %Y. u %H:%M')

    return render_template('reviews/review_detail.html', review=review)


@reviews_bp.route('/api/users/search')
def search_users():
    query = request.args.get('q', '')
    if query:
        users = list(mongo.db.users.find({
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}}
            ]
        }).limit(10))

        users_data = [{
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'faculty': user.get('faculty', ''),
            'department': user.get('department', '')
        } for user in users]

        return jsonify(users_data)

    return jsonify([])
