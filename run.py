import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient(os.getenv('MONGO_URI'))
db = client.kolegarecenzije

# Test MongoDB connection on startup
@app.before_request
def test_mongo_connection():
    try:
        client.admin.command('ping')
        print("🎉 MongoDB Atlas connection SUCCESSFUL!")
    except Exception as e:
        print(f"❌ MongoDB connection FAILED: {e}")

# Routes
@app.route('/')
def home():
    return jsonify({"message": "KolegaRecenzije API is running!"})

@app.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        courses = list(db.courses.find({}, {'_id': 0}))
        return jsonify(courses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        course_code = request.args.get('course')
        if course_code:
            reviews = list(db.reviews.find({"courseCode": course_code}, {'_id': 0}))
        else:
            reviews = list(db.reviews.find({}, {'_id': 0}))
        return jsonify(reviews)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        review_data = request.json
        result = db.reviews.insert_one(review_data)
        return jsonify({"message": "Review added successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses', methods=['POST'])
def add_course():
    try:
        course_data = request.json
        result = db.courses.insert_one(course_data)
        return jsonify({"message": "Course added successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)