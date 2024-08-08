from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import numpy as np
from flask import Flask, jsonify, abort
import logging
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_from_env(key):
    return os.getenv(key)

app = Flask(__name__)
client = MongoClient(get_from_env("MONGO_URI"))
db = client["main"]
videos_collection = db["videos"]
users_collection = db["users"]

logging.basicConfig(level=logging.INFO)

def prepare_feature_vector(video):
    """Prepare the feature vector for a video."""
    duration_parts = video.get('meta', {}).get('duration', '00:00:00').split(":")
    duration = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
    
    feature_vector = [
        len(video.get('meta', {}).get('tags', [])),
        video.get('views', 0),
        video.get('likes', 0),
        video.get('dislikes', 0),
        int(video.get('meta', {}).get('width', 0)),
        int(video.get('meta', {}).get('height', 0)),
        duration,
        int(video.get('meta', {}).get('file_size', 0)),
        video.get('meta', {}).get('is_made_for_adults', False)
    ]
    
    return feature_vector

def prepare_training_data(user_id):
    """Prepare the training data for a given user."""
    user_data = get_user_data(user_id)
    if user_data is None:
        raise ValueError(f"User with ID {user_id} not found.")
    
    all_videos = list(videos_collection.find())
    if not all_videos:
        raise ValueError("No videos found in the collection.")
    
    X = []
    y = []
    for video in all_videos:
        video_id = video['id']
        liked = video_id in user_data.get('liked_videos', [])
        disliked = video_id in user_data.get('disliked_videos', [])
        
        feature_vector = prepare_feature_vector(video)
        X.append(feature_vector)
        y.append(liked * 1 + disliked * -1)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(np.array(X))
    
    return X_scaled, np.array(y), scaler

def train_model(user_id, n_neighbors=5):
    """Train the k-NN model for a specific user."""
    X, y, scaler = prepare_training_data(user_id)
    if X.shape[0] < n_neighbors:
        logging.warning(f"Not enough samples to train the model with {n_neighbors} neighbors. Training with fewer neighbors.")
        n_neighbors = X.shape[0]
    
    model = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
    model.fit(X)
    
    return model, scaler

def recommend_videos_ml(user_id):
    """Generate video recommendations using the trained k-NN model."""
    user_data = get_user_data(user_id)
    if user_data is None:
        raise ValueError(f"User with ID {user_id} not found.")
    
    model, scaler = train_model(user_id)
    watched_videos = set(user_data.get('watch_history', []))
    
    all_videos = list(videos_collection.find())
    if not all_videos:
        raise ValueError("No videos found in the collection.")
    
    recommendations = []
    
    for video in all_videos:
        video_id = video['id']
        if video_id in watched_videos:
            continue
        
        feature_vector = prepare_feature_vector(video)
        feature_vector_scaled = scaler.transform([feature_vector])
        
        distances, indices = model.kneighbors(feature_vector_scaled)
        for i, distance in zip(indices[0], distances[0]):
            recommendations.append((all_videos[i]['id'], distance))
    
    recommendations.sort(key=lambda x: x[1])
    
    return [rec[0] for rec in recommendations]

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations_ml(user_id):
    try:
        recommendations = recommend_videos_ml(user_id)
        return jsonify(recommendations)
    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        abort(404, description=str(ve))
    except Exception as e:
        logging.error(f"Error in generating ML recommendations: {e}")
        abort(500, description="Internal Server Error")

def get_user_data(user_id):
    """Retrieve user data from the database."""
    user_data = users_collection.find_one({"id": user_id})
    if user_data is None:
        logging.error(f"No user found with ID: {user_id}")
        return None
    return user_data

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
