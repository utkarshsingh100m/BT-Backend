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
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
# Explicitly allow all origins for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# DynamoDB setup
DYNAMODB_TABLE = "Contacts"
dynamodb = None
table = None

def init_dynamodb():
    """Initialize DynamoDB connection and table"""
    global dynamodb, table
    try:
        if dynamodb is None:
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-north-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        
        if table is None:
            table = dynamodb.Table(DYNAMODB_TABLE)
            try:
                table.load()
                print(f"DynamoDB table {DYNAMODB_TABLE} found")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"Creating DynamoDB table {DYNAMODB_TABLE}...")
                    table = dynamodb.create_table(
                        TableName=DYNAMODB_TABLE,
                        KeySchema=[
                            {'AttributeName': 'email', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'email', 'AttributeType': 'S'},
                            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                        ],
                        ProvisionedThroughput={
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    )
                    table.wait_until_exists()
                    print(f"DynamoDB table {DYNAMODB_TABLE} created successfully")
                else:
                    raise e
                    
    except Exception as e:
        print(f"DynamoDB initialization error: {e}")

# Initialize DynamoDB on startup
init_dynamodb()

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

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_stream():
    """Streaming chat endpoint with GPT-4o"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

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
                    model="openai/gpt-oss-20b:free",
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

@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def save_contact():
    """Save contact form submission to database"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not all([name, email, message]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
            
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        
        init_dynamodb()
        if table:
            table.put_item(
                Item={
                    'name': name,
                    'email': email,
                    'message': message,
                    'timestamp': timestamp
                }
            )
        else:
             raise Exception("DynamoDB table not initialized")
        
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
        init_dynamodb()
        if table:
            # Lightweight check
            table.load()
            db_status = 'Connected'
        else:
            db_status = 'Not Initialized'
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
            '/api/health',
            '/api/track-visit',
            '/api/analytics'
        ]
    })

@app.route('/api/track-visit', methods=['POST', 'OPTIONS'])
def track_visit():
    """Track a page visit"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        init_dynamodb()
        if table is None:
            raise Exception("DynamoDB table not initialized")

        # Atomic counter update
        table.update_item(
            Key={
                'email': 'analytics',
                'timestamp': 'total_visits'
            },
            UpdateExpression='ADD visit_count :inc',
            ExpressionAttributeValues={
                ':inc': 1
            }
        )
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Tracking Error: {e}")
        # If item doesn't exist, create it
        try:
            table.put_item(
                Item={
                    'email': 'analytics',
                    'timestamp': 'total_visits',
                    'visit_count': 1
                }
            )
            return jsonify({'success': True})
        except Exception as inner_e:
            return jsonify({'success': False, 'error': str(inner_e)}), 500

@app.route('/api/analytics', methods=['GET', 'OPTIONS'])
def get_analytics():
    """Get analytics data"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        init_dynamodb()
        if table is None:
            raise Exception("DynamoDB table not initialized")
        
        response = table.get_item(
            Key={
                'email': 'analytics',
                'timestamp': 'total_visits'
            }
        )
        
        visit_count = 0
        if 'Item' in response:
            visit_count = int(response['Item'].get('visit_count', 0))
            
        return jsonify({
            'success': True,
            'data': {
                'total_visits': visit_count
            }
        })
    except Exception as e:
        print(f"Analytics Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Chat API running on port {port}")
    print(f"OpenRouter API Key: {'Configured' if os.getenv('OPENROUTER_API_KEY') else 'Missing'}")
    app.run(host='0.0.0.0', port=port, debug=True)
