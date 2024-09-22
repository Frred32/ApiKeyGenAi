import asyncio
import logging
from asyncio import WindowsSelectorEventLoopPolicy
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets
from g4f.client import Client

# Set the event loop policy
asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_key', methods=['POST'])
def generate_key():
    api_key = secrets.token_hex(16)  # Generate a secure random API key
    new_key = APIKey(key=api_key)
    db.session.add(new_key)
    db.session.commit()
    return jsonify({'api_key': api_key})

@app.route('/chat', methods=['POST'])
async def chat():
    data = request.get_json()
    api_key = data.get('api_key')
    message = data.get('message')

    # Validate the API key
    if not APIKey.query.filter_by(key=api_key).first():
        return jsonify({'error': 'Invalid API key'}), 403

    # Create a ChatGPT client instance
    client = Client()

    try:
        # Generate a response using ChatGPT
        response = client.chat.completions.create(  # Removed 'await'
            model="gpt-4",  # Use GPT-4 model
            messages=[{"role": "user", "content": message}]
        )
        
        # Check if choices exist in the response
        if response and hasattr(response, 'choices') and response.choices:
            bot_response = response.choices[0].message.content
            return jsonify({'response': bot_response})
        else:
            logging.error("No choices in response")
            return jsonify({'error': 'No response from ChatGPT.'}), 500
            
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")  # Log the error
        return jsonify({'error': 'An error occurred while generating a response.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
