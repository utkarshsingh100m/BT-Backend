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
            
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        
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
    # Check DB connection
    db_status = 'Error'
    try:
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

@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    """Track a page visit"""
    try:
        # Initialize table if needed
        init_dynamodb()
        
        # We'll use a simple counter for total visits
        # Partition Key: 'analytics'
        # Sort Key: 'total_visits'
        
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

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    try:
        init_dynamodb()
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Chat API running on port {port}")
    print(f"OpenRouter API Key: {'Configured' if os.getenv('OPENROUTER_API_KEY') else 'Missing'}")
    app.run(host='0.0.0.0', port=port, debug=True)
