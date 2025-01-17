# Create a new user
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{"username": "john", "interests": ["cricket", "football"]}'

# Get a fresh question (with username header)
curl "http://localhost:8000/questions/fresh/" \
     -H "username: john"

# Get question history (with username header)
curl "http://localhost:8000/questions/history/" \
     -H "username: john"

# Get questions by interest (with username header)
curl "http://localhost:8000/questions/history/?interest=cricket" \
     -H "username: john"

# Get pending resolutions (with username header)
curl "http://localhost:8000/questions/pending/" \
     -H "username: john"

# Resolve a question (with username header)
curl -X POST "http://localhost:8000/questions/1/resolve/" \
     -H "Content-Type: application/json" \
     -H "username: john" \
     -d '{"result": "yes", "note": "Team won the match"}'

# Install dependencies
pip install -r requirements.txt

# Run the API for local development
python run_api.py

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env  # Copy example env file and update with your values

# Run the API for local development
uvicorn prediction_app.api.main:app --reload