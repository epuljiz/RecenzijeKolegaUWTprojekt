import os
from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'production'))

# Test MongoDB connection on startup
@app.before_request
def test_mongo_connection():
    try:
        from app.extensions import mongo
        mongo.db.command('ping')
        print("✅ MongoDB Atlas connection successful!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

if __name__ == '__main__':
    app.run()