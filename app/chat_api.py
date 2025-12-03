"""
Buddy Tools Backend - Chat API Module
Refactored for Vercel deployment
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_cors import CORS
import requests
import os
import json
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database setup
DB_NAME = os.path.join(os.path.dirname(__file__), "contact.db")

def init_db():
    """Initialize the database with contact table"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database {DB_NAME} initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Initialize DB on startup
init_db()

# Initialize OpenAI client with OpenRouter
# Using requests directly for better control
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# System message for the assistant
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful AI assistant for students. You help with homework, assignments, explanations, and academic questions. Be concise, clear, and educational in your responses."
}

@app.route('/api/chat', methods=['POST'])
def chat_stream():
    """Chat endpoint with GPT-4o via OpenRouter (Non-streaming)"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        conversation_history = data.get('conversationHistory', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Build messages array
        messages = [SYSTEM_MESSAGE] + conversation_history + [
            {"role": "user", "content": message}
        ]
        
        import requests
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://buddy-tools.vercel.app",
            "X-Title": "Buddy Tools"
        }
        
        # Step 1: First API call with reasoning
        payload_1 = {
            "model": "openai/gpt-oss-20b:free",
            "messages": messages,
            "reasoning": {"enabled": True}
        }
        
        response_1 = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload_1
        )
        
        if response_1.status_code != 200:
            return jsonify({'success': False, 'error': f"OpenRouter API Error (Step 1): {response_1.status_code} - {response_1.text}"}), 500

        resp_json_1 = response_1.json()
        if 'choices' not in resp_json_1 or not resp_json_1['choices']:
            return jsonify({'success': False, 'error': 'No response from AI'}), 500
            
        msg_1 = resp_json_1['choices'][0]['message']
        
        # Step 2: Second API call - "Are you sure? Think carefully."
        messages_2 = messages + [
            {
                "role": "assistant",
                "content": msg_1.get('content'),
                "reasoning_details": msg_1.get('reasoning_details')
            },
            {"role": "user", "content": "Are you sure? Think carefully."}
        ]
        
        payload_2 = {
            "model": "openai/gpt-oss-20b:free",
            "messages": messages_2,
            "reasoning": {"enabled": True}
        }
        
        response_2 = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload_2
        )
        
        if response_2.status_code != 200:
            return jsonify({'success': False, 'error': f"OpenRouter API Error (Step 2): {response_2.status_code} - {response_2.text}"}), 500

        resp_json_2 = response_2.json()
        if 'choices' not in resp_json_2 or not resp_json_2['choices']:
            return jsonify({'success': False, 'error': 'No response from AI (Step 2)'}), 500
            
        final_content = resp_json_2['choices'][0]['message']['content']
        
        return jsonify({
            'success': True, 
            'message': final_content
        })
        
    except Exception as e:
        print(f"Chat API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    except Exception as e:
        print(f"Chat API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def save_contact():
    """Save contact form submission to database"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not all([name, email, message]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)',
                 (name, email, message))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        print(f"Contact API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    api_key_status = 'Configured' if os.getenv('OPENROUTER_API_KEY') else 'Missing'
    
    # Check DB connection
    db_status = 'Error'
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.close()
        db_status = 'Connected'
    except:
        pass
        
    return jsonify({
        'status': 'OK',
        'message': 'Chat API is running',
        'api_key': api_key_status,
        'database': db_status
    })

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'name': 'Buddy Tools API',
        'version': '2.0',
        'endpoints': [
            '/api/chat',
            '/api/contact',
            '/api/health'
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Chat API running on port {port}")
    print(f"OpenRouter API Key: {'Configured' if os.getenv('OPENROUTER_API_KEY') else 'Missing'}")
    app.run(host='0.0.0.0', port=port, debug=True)
