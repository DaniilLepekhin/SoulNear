"""
WebApp API v2 - Based on soul_bot ChatCompletion API

Provides REST API endpoints for webapp_v2 frontend using the same
ChatCompletion approach as the main soul_bot.

Key features:
- ChatCompletion API instead of Assistants API
- User profiles with personalization
- Thread-based chat history
- Mood tracking
- Quiz integration
"""
from quart import Quart, request, jsonify
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
import asyncio

# Add soul_bot to path to import shared code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'soul_bot'))

from database.database import DatabaseManager
from database.repository import conversation_history, user_profile
import database.repository.user as db_user
import database.repository.media as db_media
import database.repository.media_category as db_media_category

# Import OpenAI service from soul_bot
from bot.services.openai_service import get_chat_completion

# Load environment variables
load_dotenv()

app = Quart(__name__)

# CORS headers for all responses
@app.after_request
async def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database configuration (same as bot)
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'soul_bot')


@app.before_serving
async def startup():
    """Initialize database connection"""
    logger.info("🚀 Starting WebApp API v2...")
    db_manager = DatabaseManager()
    await db_manager.ensure_ready()
    logger.info("✅ Database connection established")


@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webapp_api_v2',
        'timestamp': datetime.now().isoformat()
    })


# ==========================================
# 💬 CHAT ENDPOINTS
# ==========================================

@app.route('/api/chat', methods=['POST'])
async def chat():
    """
    Send message and get AI response
    Uses ChatCompletion API with personalization
    """
    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        assistant_type = data.get('assistant_type', 'helper')

        if not user_id or not message:
            return jsonify({'error': 'user_id and message are required'}), 400

        # Get AI response using soul_bot's service
        response = await get_chat_completion(
            user_id=user_id,
            message=message,
            assistant_type=assistant_type,
            model="gpt-4o-mini",
            max_history_messages=10,
            temperature=0.7
        )

        if response is None:
            return jsonify({'error': 'Failed to get AI response'}), 500

        return jsonify({
            'status': 'success',
            'response': response,
            'assistant_type': assistant_type
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/history/<int:user_id>', methods=['GET'])
async def get_chat_history(user_id: int):
    """
    Get chat history for user
    Supports filtering by assistant_type and thread_id
    """
    try:
        assistant_type = request.args.get('assistant_type', 'helper')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Get history from conversation_history table
        messages = await conversation_history.get_history(
            user_id=user_id,
            assistant_type=assistant_type,
            limit=limit,
            offset=offset
        )

        return jsonify({
            'status': 'success',
            'data': {
                'messages': messages,
                'total': len(messages)
            }
        })

    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/save', methods=['POST'])
async def save_chat_message():
    """
    Save chat message to history
    """
    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        message_id = data.get('message_id')
        role = data.get('role')
        content = data.get('content')
        assistant_type = data.get('assistant_type', 'helper')
        thread_id = data.get('thread_id', 'main')

        if not all([user_id, message_id, role, content]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Save to conversation_history
        await conversation_history.add_message(
            user_id=user_id,
            role=role,
            content=content,
            assistant_type=assistant_type
        )

        return jsonify({
            'status': 'success',
            'message': 'Message saved'
        })

    except Exception as e:
        logger.error(f"Save message error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/clear', methods=['POST'])
async def clear_chat_history():
    """
    Clear chat history for user
    """
    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        assistant_type = data.get('assistant_type', 'helper')

        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        await conversation_history.clear_history(
            user_id=user_id,
            assistant_type=assistant_type
        )

        return jsonify({
            'status': 'success',
            'message': 'History cleared'
        })

    except Exception as e:
        logger.error(f"Clear history error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==========================================
# 👤 USER & PROFILE ENDPOINTS
# ==========================================

@app.route('/api/user/<int:user_id>', methods=['GET'])
async def get_user(user_id: int):
    """Get user information"""
    try:
        user = await db_user.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'status': 'success',
            'data': {
                'user_id': user.user_id,
                'name': user.name,
                'username': user.username,
                'premium': user.premium,
                'sub_date': user.sub_date.isoformat() if user.sub_date else None
            }
        })

    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/<int:user_id>', methods=['GET'])
async def get_profile(user_id: int):
    """Get user profile with patterns, insights, and preferences"""
    try:
        profile = await user_profile.get_or_create(user_id)

        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        return jsonify({
            'status': 'success',
            'data': {
                'tone_style': profile.tone_style,
                'personality': profile.personality,
                'message_length': profile.message_length,
                'patterns': profile.patterns,
                'insights': profile.insights,
                'emotional_state': profile.emotional_state,
                'learning_preferences': profile.learning_preferences,
                'preferences': profile.preferences,
                'pattern_analysis_count': profile.pattern_analysis_count,
                'last_analysis_at': profile.last_analysis_at.isoformat() if profile.last_analysis_at else None
            }
        })

    except Exception as e:
        logger.error(f"Get profile error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/<int:user_id>/patterns', methods=['GET'])
async def get_patterns(user_id: int):
    """Get user patterns"""
    try:
        profile = await user_profile.get_or_create(user_id)

        return jsonify({
            'status': 'success',
            'data': profile.patterns
        })

    except Exception as e:
        logger.error(f"Get patterns error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/<int:user_id>/insights', methods=['GET'])
async def get_insights(user_id: int):
    """Get user insights"""
    try:
        profile = await user_profile.get_or_create(user_id)

        return jsonify({
            'status': 'success',
            'data': profile.insights
        })

    except Exception as e:
        logger.error(f"Get insights error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/<int:user_id>/emotional-state', methods=['GET'])
async def get_emotional_state(user_id: int):
    """Get user emotional state"""
    try:
        profile = await user_profile.get_or_create(user_id)

        return jsonify({
            'status': 'success',
            'data': profile.emotional_state
        })

    except Exception as e:
        logger.error(f"Get emotional state error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==========================================
# 🧘 PRACTICES ENDPOINTS
# ==========================================

@app.route('/api/practices', methods=['GET'])
async def get_practices():
    """Get all practices organized by categories"""
    try:
        # Get all categories with media
        categories = await db_media_category.get_all_with_media()

        # Transform to expected format
        practices = {}
        for category in categories:
            media_list = []
            for media in category.get('medias', []):
                media_list.append({
                    'id': media.id,
                    'name': media.name,
                    'text': media.text,
                    'media_type': media.media_type,
                    'media_id': media.media_id,
                    'file_url': media.file_url,
                    'destination': media.destination,
                    'position': media.position
                })

            practices[category['name']] = media_list

        return jsonify({
            'status': 'success',
            'data': practices
        })

    except Exception as e:
        logger.error(f"Get practices error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==========================================
# 🎯 MOOD TRACKING (for compatibility)
# ==========================================

@app.route('/api/mood/save', methods=['POST'])
async def save_mood():
    """Save user mood (stored in emotional_state in profile)"""
    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        mood = data.get('mood')

        if not user_id or not mood:
            return jsonify({'error': 'user_id and mood are required'}), 400

        # Get profile and update emotional_state
        profile = await user_profile.get_or_create(user_id)

        # Update emotional state with current mood
        emotional_state = profile.emotional_state or {}
        emotional_state['current_mood'] = mood
        emotional_state['updated_at'] = datetime.now().isoformat()

        await user_profile.update(
            user_id=user_id,
            emotional_state=emotional_state
        )

        return jsonify({
            'status': 'success',
            'message': 'Mood saved'
        })

    except Exception as e:
        logger.error(f"Save mood error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/mood/history/<int:user_id>', methods=['GET'])
async def get_mood_history(user_id: int):
    """Get mood history (from emotional_state)"""
    try:
        profile = await user_profile.get_or_create(user_id)

        emotional_state = profile.emotional_state or {}

        return jsonify({
            'status': 'success',
            'data': {
                'current_mood': emotional_state.get('current_mood'),
                'emotional_state': emotional_state
            }
        })

    except Exception as e:
        logger.error(f"Get mood history error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
