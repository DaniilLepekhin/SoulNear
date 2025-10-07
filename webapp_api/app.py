from quart import Quart, request, jsonify
from quart_cors import cors
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy import URL, select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import VARCHAR, DateTime, Integer, Boolean
from datetime import datetime as dt

# Load environment variables
load_dotenv()

app = Quart(__name__)
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True
cors(app, allow_origin="*", allow_methods=["GET", "POST", "OPTIONS"])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
HELPER_ID = os.getenv('HELPER_ID', '')
SOULSLEEP_ID = os.getenv('SOULSLEEP_ID', '')
RELATIONSHIPS_ID = os.getenv('RELATIONSHIPS_ID', '')
MONEY_ID = os.getenv('MONEY_ID', '')
CONFIDENCE_ID = os.getenv('CONFIDENCE_ID', '')
FEARS_ID = os.getenv('FEARS_ID', '')

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Database configuration (same as bot)
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'soul_test_bot')

engine = create_async_engine(
    URL(
        drivername='postgresql+asyncpg',
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        query={},
    ), future=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Database models (copy from bot, read-only)
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(length=64))
    username: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    ref: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)

    helper_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    assistant_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    sleeper_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)

    reg_date: Mapped[DateTime] = mapped_column(DateTime, default=dt.now())
    active_date: Mapped[DateTime] = mapped_column(DateTime, default=dt.now())
    sub_date: Mapped[DateTime] = mapped_column(DateTime)
    block_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    helper_requests: Mapped[int] = mapped_column(Integer, default=10)
    assistant_requests: Mapped[int] = mapped_column(Integer, default=12)
    sleeper_requests: Mapped[int] = mapped_column(Integer, default=3)

    real_name: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[bool] = mapped_column(Boolean, nullable=True)

# Helper functions (copied from bot's ChatGPT.py)
async def get_user_from_db(user_id: int):
    """Get user from database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

async def update_user_thread(user_id: int, thread_id: str, assistant_type: str):
    """Update user thread ID in database"""
    async with AsyncSessionLocal() as session:
        if assistant_type == 'helper':
            stmt = update(User).where(User.user_id == user_id).values(helper_thread_id=thread_id)
        elif assistant_type == 'sleeper':
            stmt = update(User).where(User.user_id == user_id).values(sleeper_thread_id=thread_id)
        else:  # analysis assistants
            stmt = update(User).where(User.user_id == user_id).values(assistant_thread_id=thread_id)

        await session.execute(stmt)
        await session.commit()

async def get_assistant_response(user_id: int, prompt: str, assistant_type: str) -> str | None:
    """
    Get response from OpenAI Assistant
    Copied logic from soul_bot/bot/functions/ChatGPT.py
    """
    if not client:
        logger.error("OpenAI client not initialized")
        return None

    user = await get_user_from_db(user_id)

    # Map assistant type to assistant ID
    assistant_ids = {
        'helper': HELPER_ID,
        'sleeper': SOULSLEEP_ID,
        'relationships': RELATIONSHIPS_ID,
        'money': MONEY_ID,
        'confidence': CONFIDENCE_ID,
        'fears': FEARS_ID
    }

    assistant_id = assistant_ids.get(assistant_type, HELPER_ID)

    if not assistant_id:
        logger.error(f"Assistant ID not found for type: {assistant_type}")
        return None

    # Get or create thread
    thread_id = None
    if user:
        if assistant_type == 'helper':
            thread_id = user.helper_thread_id
        elif assistant_type == 'sleeper':
            thread_id = user.sleeper_thread_id
        else:
            thread_id = user.assistant_thread_id

    # Create new thread if needed
    if not thread_id:
        thread = await client.beta.threads.create()
        thread_id = thread.id
        await update_user_thread(user_id, thread_id, assistant_type)
        logger.info(f"Created new thread {thread_id} for user {user_id}, type {assistant_type}")

    # Add message to thread
    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[{"type": "text", "text": prompt}]
    )

    try:
        # Run assistant
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model='gpt-4-turbo-preview'
        )

        # Handle failed runs
        max_attempts = 5
        attempt = 0
        while run.status != 'completed' and attempt < max_attempts:
            if run.status == 'failed':
                await client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=[{"type": "text", "text": prompt}]
                )
                run = await client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    model='gpt-4-turbo-preview'
                )
                attempt += 1
                if attempt >= max_attempts:
                    logger.error(f"Max attempts reached for user {user_id}")
                    return None
                continue

            run = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status != 'completed':
            logger.error(f"Run not completed for user {user_id}: {run.status}")
            return None

        # Get messages
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']

        if not assistant_messages:
            logger.error(f"No assistant messages for user {user_id}")
            return None

        last_message = assistant_messages[0]
        response_text = last_message.content[0].text.value if isinstance(last_message.content, list) else ""

        # Clean response (like in bot)
        response_text = response_text.replace('*', '').replace('#', '').strip()

        logger.info(f"Response generated for user {user_id}, length: {len(response_text)}")
        return response_text

    except Exception as e:
        logger.error(f"Error in get_assistant_response: {e}", exc_info=True)
        return None

# Routes for serving webapp files
@app.route('/')
async def index():
    """Serve the main webapp page"""
    try:
        with open('/home/soulnear_webapp/index.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return 'WebApp not found', 404

@app.route('/styles.css')
async def styles():
    """Serve CSS styles"""
    try:
        with open('/home/soulnear_webapp/styles.css', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/css; charset=utf-8'}
    except FileNotFoundError:
        return 'CSS not found', 404

@app.route('/app.js')
async def webapp_js():
    """Serve JavaScript file"""
    try:
        with open('/home/soulnear_webapp/app.js', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript; charset=utf-8'}
    except FileNotFoundError:
        return 'JavaScript not found', 404

@app.route('/<path:filename>')
async def serve_static(filename):
    """Serve static files (images, etc.)"""
    try:
        file_path = f'/home/soulnear_webapp/{filename}'
        with open(file_path, 'rb') as f:
            content = f.read()

        # Determine content type
        if filename.endswith('.png'):
            content_type = 'image/png'
        elif filename.endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif filename.endswith('.svg'):
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'

        return content, 200, {'Content-Type': content_type}
    except FileNotFoundError:
        return 'File not found', 404

# API endpoints
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
async def chat():
    """Main chat endpoint"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        message = data.get('message', '')
        assistant_type = data.get('assistant_type', 'helper')

        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        if not message:
            return jsonify({'error': 'message required'}), 400

        logger.info(f"Chat request: user={user_id}, type={assistant_type}, msg_len={len(message)}")

        # Get response from OpenAI
        response = await get_assistant_response(user_id, message, assistant_type)

        if response is None:
            return jsonify({'error': 'Failed to get response from assistant'}), 500

        return jsonify({
            'status': 'success',
            'response': response
        }), 200

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST', 'OPTIONS'])
async def reset_context():
    """Reset chat context (create new thread)"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        assistant_type = data.get('assistant_type', 'helper')

        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        # Create new thread
        thread = await client.beta.threads.create()
        thread_id = thread.id

        # Update in database
        await update_user_thread(user_id, thread_id, assistant_type)

        logger.info(f"Reset context for user {user_id}, type {assistant_type}")

        return jsonify({
            'status': 'success',
            'message': 'Context reset successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error in reset endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
async def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'openai_configured': client is not None,
        'database_configured': POSTGRES_PASSWORD != ''
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)
