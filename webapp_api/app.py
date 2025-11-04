from quart import Quart, request, jsonify
from quart_cors import cors
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import Optional
from contextlib import asynccontextmanager

from asyncpg import DuplicateDatabaseError, InvalidCatalogNameError
from sqlalchemy import URL, select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import VARCHAR, DateTime, Integer, Boolean, TEXT
from datetime import datetime as dt
import uuid

# Load environment variables
load_dotenv()

app = Quart(__name__)
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
POSTGRES_DB = os.getenv('POSTGRES_DB', 'soul_bot')


def _build_engine(database_name: str) -> AsyncEngine:
    return create_async_engine(
        URL(
            drivername='postgresql+asyncpg',
            username=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=database_name,
            query={},
        ),
        future=True,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


_engine: AsyncEngine = _build_engine(POSTGRES_DB)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


class DatabaseManager:
    """Self-healing database engine for the Quart API."""

    def __init__(self, engine_obj: AsyncEngine, session_factory: async_sessionmaker) -> None:
        self._engine = engine_obj
        self._session_factory = session_factory
        self._lock = asyncio.Lock()

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def ensure_ready(self) -> None:
        async with self._lock:
            retries = 0
            while True:
                try:
                    async with self._engine.connect() as conn:
                        await conn.execute(text('SELECT 1'))
                    return
                except InvalidCatalogNameError:
                    logger.warning("WebApp DB '%s' missing, creating...", POSTGRES_DB)
                    await self._create_database()
                    await self._reset_engine()
                except OperationalError as exc:
                    if not self._is_missing_database(exc):
                        raise
                    logger.warning("WebApp DB '%s' missing (OperationalError), creating...", POSTGRES_DB)
                    await self._create_database()
                    await self._reset_engine()

                retries += 1
                if retries > 3:
                    raise RuntimeError(f"Unable to prepare database '{POSTGRES_DB}' for WebApp")

    def _is_missing_database(self, exc: OperationalError) -> bool:
        origin = getattr(exc, 'orig', None)
        if isinstance(origin, InvalidCatalogNameError):
            return True
        message = str(exc).lower()
        return POSTGRES_DB.lower() in message and 'does not exist' in message

    async def _create_database(self) -> None:
        admin_engine = _build_engine('postgres')
        try:
            async with admin_engine.begin() as conn:
                await conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
                logger.info("Created WebApp database '%s'", POSTGRES_DB)
        except DuplicateDatabaseError:
            logger.info("WebApp database '%s' already exists", POSTGRES_DB)
        finally:
            await admin_engine.dispose()

    async def _reset_engine(self) -> None:
        global _engine, _session_factory

        await self._engine.dispose()
        self._engine = _build_engine(POSTGRES_DB)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)
        _engine = self._engine
        _session_factory = self._session_factory

    @asynccontextmanager
    async def _session_context(self):
        await self.ensure_ready()
        async with self._session_factory() as session:
            yield session

    @asynccontextmanager
    async def _begin_context(self):
        await self.ensure_ready()
        async with self._session_factory().begin() as session:
            yield session

    def __call__(self):
        return self._session_context()

    def begin(self):
        return self._begin_context()


AsyncSessionLocal = DatabaseManager(_engine, _session_factory)

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

class MediaCategory(Base):
    __tablename__ = 'media_categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(VARCHAR(length=32))
    text: Mapped[str] = mapped_column(VARCHAR(length=2048))
    category: Mapped[str] = mapped_column(VARCHAR(length=32))
    media_type: Mapped[str] = mapped_column(VARCHAR(length=8), nullable=True)
    media_id: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
    destination: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)

class Media(Base):
    __tablename__ = 'medias'

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(VARCHAR(length=64))
    text: Mapped[str] = mapped_column(VARCHAR(length=2048), nullable=True)
    media_type: Mapped[str] = mapped_column(VARCHAR(length=8), nullable=True)
    media_id: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
    destination: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(TEXT(), nullable=True)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    thread_id: Mapped[str] = mapped_column(VARCHAR(length=64), nullable=False, default='main')
    message_id: Mapped[str] = mapped_column(VARCHAR(length=64), nullable=False)
    role: Mapped[str] = mapped_column(VARCHAR(length=16), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(TEXT(), nullable=False)
    assistant_type: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=False, default='helper')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=dt.now)

class ChatThread(Base):
    __tablename__ = 'chat_threads'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(VARCHAR(length=64), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(VARCHAR(length=256), nullable=True)
    assistant_type: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=False, default='helper')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=dt.now)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=dt.now)

class Mood(Base):
    __tablename__ = 'moods'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    mood_value: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 (😂🤩😐😔🤯)
    emoji: Mapped[str] = mapped_column(VARCHAR(length=16), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=dt.now)

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

# Ханг музыка из sounds.py
HANG_MUSIC = [
    {"name": "Macadamia", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Macadamia.mp3", "duration": "3:47"},
    {"name": "New Horizons", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_New_Horizons.mp3", "duration": "2:21"},
    {"name": "Sunny Way", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Sunny_Way.mp3", "duration": "5:23"},
    {"name": "Seven Wonders", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Seven_Wonders.mp3", "duration": "3:05"},
    {"name": "The Flow", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_The_Flow.mp3", "duration": "5:18"},
    {"name": "Immersion", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Immersion.mp3", "duration": "3:46"},
    {"name": "Spring", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Spring.mp3", "duration": "3:32"},
    {"name": "Rainbow", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Rainbow.mp3", "duration": "4:33"},
    {"name": "Blissful", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Blissful.mp3", "duration": "5:14"},
    {"name": "Ocean Inside", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Ocean_Inside.mp3", "duration": "2:32"},
    {"name": "Gravity", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Gravity.mp3", "duration": "3:06"},
    {"name": "Cappadocia", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Cappadocia.mp3", "duration": "4:06"},
    {"name": "Reggae", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Reggae.mp3", "duration": "3:12"},
    {"name": "Macadamia Remix", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Macadamia_Remix.mp3", "duration": "4:31"},
    {"name": "Sunny Way Remix", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Sunny_Way_Remix.mp3", "duration": "5:12"},
    {"name": "Breath of Spring Remix", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Breath_of_Spring_Remix.mp3", "duration": "3:31"},
    {"name": "Ocean Inside Remix", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_Ocean_Inside_Remix.mp3", "duration": "5:11"},
    {"name": "J. Remix", "url": "https://storage.daniillepekhin.com/soulnear/audio/hang_J_Remix.mp3", "duration": "3:46"},
]

@app.route('/api/practices', methods=['GET', 'OPTIONS'])
async def get_practices():
    """Get all practices from database"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        async with AsyncSessionLocal() as session:
            # Get all media categories
            categories_result = await session.execute(
                select(MediaCategory).order_by(MediaCategory.position)
            )
            categories = categories_result.scalars().all()

            logger.info(f"Found {len(categories)} categories")

            # Get all media items
            media_result = await session.execute(
                select(Media).order_by(Media.category_id, Media.position)
            )
            media_items = media_result.scalars().all()

            logger.info(f"Found {len(media_items)} media items")

            # Organize data by category type
            practices_data = {
                'practices': [],  # Медитации
                'videos': [],     # Йога и видео
                'music': []       # Ханг музыка
            }

            # Group by category
            for category in categories:
                logger.info(f"Processing category: {category.name} ({category.category})")
                category_media = [m for m in media_items if m.category_id == category.id]

                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'text': category.text,
                    'category': category.category,
                    'media_type': category.media_type,
                    'media_id': category.media_id,
                    'items': []
                }

                for media in category_media:
                    media_dict = {
                        'id': media.id,
                        'name': media.name,
                        'text': media.text,
                        'media_type': media.media_type,
                        'media_id': media.media_id,
                        'position': media.position
                    }
                    # Add file_url if available (from S3)
                    if hasattr(media, 'file_url') and media.file_url:
                        media_dict['url'] = media.file_url
                    category_data['items'].append(media_dict)

                # Add to appropriate section
                if category.category == 'practices':
                    practices_data['practices'].append(category_data)
                elif category.category == 'videos':
                    practices_data['videos'].append(category_data)

            # Add Hang music
            for track in HANG_MUSIC:
                practices_data['music'].append({
                    'name': track['name'],
                    'url': track['url'],
                    'duration': track['duration'],
                    'media_type': 'audio'
                })

            return jsonify({
                'status': 'success',
                'data': practices_data
            }), 200

    except Exception as e:
        logger.error(f"Error in get_practices: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<file_id>', methods=['GET', 'OPTIONS'])
async def get_audio_url(file_id):
    """Get audio file URL from Telegram file_id"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        import httpx

        # Получаем информацию о файле от Telegram Bot API
        bot_token = os.getenv('BOT_TOKEN', '')
        if not bot_token:
            return jsonify({'status': 'error', 'error': 'Bot token not configured'}), 500

        async with httpx.AsyncClient() as client:
            # Получаем file_path
            response = await client.get(
                f'https://api.telegram.org/bot{bot_token}/getFile',
                params={'file_id': file_id}
            )
            data = response.json()

            if data.get('ok') and data.get('result'):
                file_path = data['result']['file_path']
                # Формируем прямую ссылку на файл
                file_url = f'https://api.telegram.org/file/bot{bot_token}/{file_path}'

                logger.info(f"Got audio URL for {file_id}: {file_url}")

                return jsonify({
                    'status': 'success',
                    'url': file_url
                }), 200
            else:
                logger.error(f"Failed to get file info: {data}")
                return jsonify({'status': 'error', 'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Error getting audio URL: {e}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/user/<int:user_id>', methods=['GET', 'OPTIONS'])
async def get_user_info(user_id):
    """Get user information including subscription status"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found'
                }), 404

            # Check subscription status
            now = datetime.now()
            is_subscribed = user.sub_date and user.sub_date > now

            # Format dates
            sub_date_str = user.sub_date.strftime('%d.%m.%Y') if user.sub_date else None
            reg_date_str = user.reg_date.strftime('%d.%m.%Y') if user.reg_date else None

            return jsonify({
                'status': 'success',
                'data': {
                    'user_id': user.user_id,
                    'name': user.name,
                    'username': user.username,
                    'is_subscribed': is_subscribed,
                    'subscription_end_date': sub_date_str,
                    'subscription_end_timestamp': int(user.sub_date.timestamp()) if user.sub_date else None,
                    'helper_requests': user.helper_requests,
                    'assistant_requests': user.assistant_requests,
                    'sleeper_requests': user.sleeper_requests,
                    'registration_date': reg_date_str,
                    'is_blocked': user.block_date is not None
                }
            }), 200

    except Exception as e:
        logger.error(f"Error getting user info: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
async def process_voice():
    """Process voice message - transcribe using OpenAI Whisper and get AI response"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # Check if OpenAI client is configured
        if not client:
            return jsonify({
                'status': 'error',
                'message': 'OpenAI client not configured'
            }), 500

        # Get uploaded audio file
        files = await request.files
        audio_file = files.get('audio')

        if not audio_file:
            return jsonify({
                'status': 'error',
                'message': 'No audio file provided'
            }), 400

        # Get user_id from form data
        form = await request.form
        user_id = form.get('user_id')

        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'No user_id provided'
            }), 400

        user_id = int(user_id)

        # Save audio file temporarily
        filename = str(uuid.uuid4())
        voice_dir = '/tmp/voice'
        os.makedirs(voice_dir, exist_ok=True)

        file_path = os.path.join(voice_dir, f"{filename}.webm")

        # Save uploaded file
        await audio_file.save(file_path)
        logger.info(f"Saved audio file: {file_path}")

        # Transcribe using OpenAI Whisper API
        try:
            with open(file_path, 'rb') as audio:
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="ru"
                )
            transcription_text = transcription.text
            logger.info(f"Whisper transcribed: {transcription_text}")
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            # Clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'status': 'error',
                'message': f'Transcription failed: {str(e)}'
            }), 500

        # Clean up audio file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file: {e}")

        # Get or create thread for user
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found'
                }), 404

            thread_id = user.helper_thread_id

            if not thread_id:
                thread = await client.beta.threads.create()
                thread_id = thread.id
                await session.execute(
                    update(User).where(User.user_id == user_id).values(helper_thread_id=thread_id)
                )
                await session.commit()

        # Send message to thread
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=transcription_text
        )

        # Run assistant
        run = await client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=HELPER_ID
        )

        # Wait for completion
        max_iterations = 60  # 30 seconds max
        iteration = 0
        while iteration < max_iterations:
            run_status = await client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                logger.error(f"Run failed with status: {run_status.status}")
                return jsonify({
                    'status': 'error',
                    'message': f'AI processing failed: {run_status.status}'
                }), 500
            await asyncio.sleep(0.5)
            iteration += 1

        if iteration >= max_iterations:
            return jsonify({
                'status': 'error',
                'message': 'AI processing timeout'
            }), 500

        # Get response
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        ai_response = messages.data[0].content[0].text.value

        logger.info(f"Voice response - transcription: {transcription_text}, message: {ai_response[:100]}")

        return jsonify({
            'status': 'success',
            'data': {
                'transcription': transcription_text,
                'message': ai_response
            }
        }), 200

    except Exception as e:
        logger.error(f"Error processing voice: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/chat/save', methods=['POST', 'OPTIONS'])
async def save_chat_message():
    """Save chat message to database"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        thread_id = data.get('thread_id', 'main')
        message_id = data.get('message_id')
        role = data.get('role')
        content = data.get('content')
        assistant_type = data.get('assistant_type', 'helper')

        if not all([user_id, message_id, role, content]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        async with AsyncSessionLocal() as session:
            message = ChatMessage(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                role=role,
                content=content,
                assistant_type=assistant_type
            )
            session.add(message)

            # Update thread updated_at
            from sqlalchemy import update as sql_update
            await session.execute(
                sql_update(ChatThread)
                .where(ChatThread.thread_id == thread_id)
                .values(updated_at=dt.now())
            )
            await session.commit()

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error saving chat message: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat/history/<int:user_id>', methods=['GET', 'OPTIONS'])
async def get_chat_history(user_id):
    """Get chat history for user"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        assistant_type = request.args.get('assistant_type', 'helper')
        thread_id = request.args.get('thread_id', 'main')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        async with AsyncSessionLocal() as session:
            from sqlalchemy import desc
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == user_id)
                .where(ChatMessage.thread_id == thread_id)
                .where(ChatMessage.assistant_type == assistant_type)
                .order_by(desc(ChatMessage.created_at))
                .limit(limit)
                .offset(offset)
            )
            messages = result.scalars().all()

            # Reverse to get chronological order
            messages = list(reversed(messages))

            messages_data = [{
                'id': msg.id,
                'message_id': msg.message_id,
                'role': msg.role,
                'content': msg.content,
                'thread_id': msg.thread_id,
                'assistant_type': msg.assistant_type,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            } for msg in messages]

        return jsonify({'status': 'success', 'messages': messages_data}), 200
    except Exception as e:
        logger.error(f"Error loading chat history: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat/threads/<int:user_id>', methods=['GET', 'OPTIONS'])
async def get_chat_threads(user_id):
    """Get list of chat threads for user"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        assistant_type = request.args.get('assistant_type', 'helper')

        async with AsyncSessionLocal() as session:
            from sqlalchemy import desc, func
            # Get threads with last message preview
            result = await session.execute(
                select(ChatThread)
                .where(ChatThread.user_id == user_id)
                .where(ChatThread.assistant_type == assistant_type)
                .order_by(desc(ChatThread.updated_at))
            )
            threads = result.scalars().all()

            threads_data = []
            for thread in threads:
                # Get first user message for title
                first_msg_result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.thread_id == thread.thread_id)
                    .where(ChatMessage.role == 'user')
                    .order_by(ChatMessage.created_at)
                    .limit(1)
                )
                first_message = first_msg_result.scalar_one_or_none()

                # Get last message for preview
                last_msg_result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.thread_id == thread.thread_id)
                    .order_by(desc(ChatMessage.created_at))
                    .limit(1)
                )
                last_message = last_msg_result.scalar_one_or_none()

                threads_data.append({
                    'thread_id': thread.thread_id,
                    'title': thread.title,
                    'assistant_type': thread.assistant_type,
                    'created_at': thread.created_at.isoformat() if thread.created_at else None,
                    'updated_at': thread.updated_at.isoformat() if thread.updated_at else None,
                    'first_message': first_message.content if first_message else None,
                    'last_message': last_message.content if last_message else None
                })

        return jsonify({'status': 'success', 'threads': threads_data}), 200
    except Exception as e:
        logger.error(f"Error loading chat threads: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat/thread/create', methods=['POST', 'OPTIONS'])
async def create_chat_thread():
    """Create new chat thread"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        thread_id = data.get('thread_id') or str(uuid.uuid4())
        title = data.get('title')
        assistant_type = data.get('assistant_type', 'helper')

        if not user_id:
            return jsonify({'status': 'error', 'message': 'Missing user_id'}), 400

        async with AsyncSessionLocal() as session:
            thread = ChatThread(
                thread_id=thread_id,
                user_id=user_id,
                title=title,
                assistant_type=assistant_type
            )
            session.add(thread)
            await session.commit()

        return jsonify({'status': 'success', 'thread_id': thread_id}), 200
    except Exception as e:
        logger.error(f"Error creating chat thread: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/mood/save', methods=['POST', 'OPTIONS'])
async def save_mood():
    """Save user mood for a specific date"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = await request.get_json()
        user_id = data.get('user_id')
        date_str = data.get('date')  # Format: YYYY-MM-DD
        mood_value = data.get('mood_value')  # 1-5
        emoji = data.get('emoji')

        if not all([user_id, date_str, mood_value, emoji]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        # Parse date
        mood_date = datetime.strptime(date_str, '%Y-%m-%d')

        async with AsyncSessionLocal() as session:
            from sqlalchemy import delete
            # Delete existing mood for this date if exists
            await session.execute(
                delete(Mood).where(
                    Mood.user_id == user_id,
                    Mood.date == mood_date
                )
            )

            # Create new mood entry
            mood = Mood(
                user_id=user_id,
                date=mood_date,
                mood_value=mood_value,
                emoji=emoji
            )
            session.add(mood)
            await session.commit()

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error saving mood: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/mood/history/<int:user_id>', methods=['GET', 'OPTIONS'])
async def get_mood_history(user_id):
    """Get mood history for user"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        days = int(request.args.get('days', 30))  # Last N days

        async with AsyncSessionLocal() as session:
            from sqlalchemy import desc
            from datetime import timedelta

            # Get moods from last N days
            start_date = datetime.now() - timedelta(days=days)
            result = await session.execute(
                select(Mood)
                .where(Mood.user_id == user_id)
                .where(Mood.date >= start_date)
                .order_by(Mood.date)
            )
            moods = result.scalars().all()

            moods_data = [{
                'date': mood.date.strftime('%Y-%m-%d'),
                'mood_value': mood.mood_value,
                'emoji': mood.emoji
            } for mood in moods]

        return jsonify({'status': 'success', 'moods': moods_data}), 200
    except Exception as e:
        logger.error(f"Error getting mood history: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
