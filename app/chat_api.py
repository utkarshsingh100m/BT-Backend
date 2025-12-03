"""
Buddy Tools Backend - Chat API Module
Refactored for Vercel deployment
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
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
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# System message for the assistant
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful AI assistant for students. You help with homework, assignments, explanations, and academic questions. Be concise, clear, and educational in your responses."
}

@app.route('/api/chat', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint with GPT-4o"""
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
        
        def generate():
            try:
                # Stream the response with GPT-4o
                stream = client.chat.completions.create(
                    model="openai/gpt-4o",
                    messages=messages,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                
            except Exception as e:
                print(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
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
