import os
from app import app
from routes import create_test_user
import json

# Obținem calea către directorul curent
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construim calea către fișierul JSON
json_path = os.path.join(current_dir, 'responses.json')

# Încărcăm dataset-ul
with open(json_path, 'r', encoding='utf-8') as f:
    responses = json.load(f)

if __name__ == "__main__":
    # The GROQ_API_KEY is already set in the environment, no need to set it here
    
    with app.app_context():
        create_test_user()
    app.run(host="0.0.0.0", port=5000)
