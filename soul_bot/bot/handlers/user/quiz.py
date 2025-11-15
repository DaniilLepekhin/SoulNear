"""
🧠 Quiz Handlers (Stage 4)

Handlers для динамических квизов

Flow:
1. Пользователь → /quiz или кнопка "Пройти квиз"
2. Выбирает категорию (relationships/money/purpose)
3. Проходит 8–12 вопросов диалогового квиза (FSM state: waiting_for_answer)
4. Получает результаты + обновление профиля
"""
import html
import logging
import os
import uuid
from pathlib import Path
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from types import SimpleNamespace

from bot.loader import dp
from bot.states.states import QuizStates
from bot.services.quiz_service import generator, analyzer
from bot.services.quiz.adaptive_quiz_service import AdaptiveQuizService
from bot.services.ai.gpt_service import GPTService
from bot.functions.speech import convert_voice, transcribe_audio
import database.repository.quiz_session as db_quiz_session
import database.repository.user_profile as db_user_profile
from bot.keyboards.start import menu as main_menu_keyboard, start
from config import is_feature_enabled
import bot.text as texts
from bot.services.quiz_ui import (
    build_quiz_menu_keyboard,
)
from bot.functions.other import check_user_info
import database.repository.user as db_user

# Initialize adaptive quiz service
gpt_service = GPTService()
adaptive_quiz = AdaptiveQuizService(gpt_service)


# ==========================================
# 🚀 СТАРТ КВИЗА
# ==========================================

@dp.message(Command('quiz'))
async def quiz_command(message: Message):
    """
    Команда /quiz - показать категории квизов
    """
    if not is_feature_enabled('ENABLE_DYNAMIC_QUIZ'):
        await message.answer("⚠️ Квизы временно недоступны")
        return
    
    # Проверяем есть ли активный квиз
    active_session = await db_quiz_session.get_active(message.from_user.id)
    if active_session:
        # Resume
        await message.answer(
            "📝 У вас есть незавершённый квиз!\n\n"
            f"Категория: {active_session.category}\n"
            f"Прогресс: {active_session.current_question_index}/{active_session.total_questions}\n\n"
            "Хотите продолжить или начать новый?",
            reply_markup=_resume_or_new_keyboard()
        )
        return
    
    # Показываем категории
    await message.answer(
        "🧠 <b>Психологические квизы</b>\n\n"
        "Выберите категорию для прохождения квиза:\n\n"
        "Квиз поможет выявить ваши поведенческие паттерны и даст персональные рекомендации.",
        reply_markup=_categories_keyboard(),
        parse_mode='HTML'
    )


async def _safe_set_text(message: Message, text: str, **kwargs) -> Message:
    """
    Edit message text when possible, otherwise send a new message.
    Returns message that contains the requested text.
    """
    if message.text:
        try:
            await message.edit_text(text, **kwargs)
            return message
        except TelegramBadRequest as exc:  # noqa: BLE001
            error = str(exc).lower()
            if "message is not modified" in error:
                return message
            if "there is no text in the message to edit" not in error and "message can't be edited" not in error:
                raise

    new_message = await message.answer(text, **kwargs)

    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    return new_message


@dp.callback_query(F.data == 'quiz_start')
async def quiz_start_callback(call: CallbackQuery):
    """
    Кнопка "🧠 Психологический квиз" из главного меню
    """
    if not is_feature_enabled('ENABLE_DYNAMIC_QUIZ'):
        await _safe_set_text(call.message, "⚠️ Квизы временно недоступны")
        await call.answer()
        return
    
    # Проверяем есть ли активный квиз
    active_session = await db_quiz_session.get_active(call.from_user.id)
    if active_session:
        # Resume
        await _safe_set_text(
            call.message,
            "📝 У вас есть незавершённый квиз!\n\n"
            f"Категория: {active_session.category}\n"
            f"Прогресс: {active_session.current_question_index}/{active_session.total_questions}\n\n"
            "Хотите продолжить или начать новый?",
            reply_markup=_resume_or_new_keyboard()
        )
        await call.answer()
        return
    
    # Показываем категории
    await _safe_set_text(
        call.message,
        "🧠 <b>Психологические квизы</b>\n\n"
        "Выберите категорию для прохождения квиза:\n\n"
        "Квиз поможет выявить ваши поведенческие паттерны и даст персональные рекомендации.",
        reply_markup=_categories_keyboard(),
        parse_mode='HTML'
    )
    await call.answer()


@dp.callback_query(F.data.startswith('quiz_category_'))
async def start_quiz_callback(call: CallbackQuery, state: FSMContext):
    """
    Начать квиз по выбранной категории
    """
    category = call.data.replace('quiz_category_', '')
    await _start_quiz_for_category(call, state, category)


@dp.callback_query(F.data == 'quiz_go_menu')
async def quiz_go_menu_callback(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get('quiz_session_id')
    if session_id:
        await db_quiz_session.cancel(session_id)

    await state.clear()

    try:
        await call.message.delete()
    except Exception:
        pass

    if not await check_user_info(message=call.message, state=state):
        await call.answer()
        return

    user = await db_user.get(call.from_user.id)

    if user and user.real_name:
        await call.message.answer(
            texts.menu,
            reply_markup=main_menu_keyboard,
            disable_web_page_preview=True,
            parse_mode='HTML'
        )
    else:
        await call.message.answer(
            texts.greet,
            reply_markup=start,
            disable_web_page_preview=True,
            parse_mode='HTML'
        )

    await call.answer()


async def _start_quiz_for_category(call: CallbackQuery, state: FSMContext, category: str):
    user_id = call.from_user.id

    try:
        profile = await db_user_profile.get_or_create(user_id)
        profile_data = {
            "patterns": profile.patterns.get('patterns', [])
        }

        questions = await generator.generate_questions(
            category=category,
            count=3,
            user_profile=profile_data
        )

        quiz_session = await db_quiz_session.create(
            user_id=user_id,
            category=category,
            questions=questions,
            total_questions=generator.TARGET_QUESTION_COUNT,
        )

        await state.update_data(
            selected_quiz_category=None,
            pending_quiz_category=None,
            quiz_session_id=quiz_session.id,
            last_question_message_id=None
        )
        await state.set_state(QuizStates.waiting_for_answer)

        await _show_current_question(call.message, quiz_session, state)

    except Exception as e:
        error_text = html.escape(str(e))
        await _safe_set_text(
            call.message,
            f"⚠️ Ошибка при создании квиза.\n\n"
            f"<code>{error_text}</code>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode='HTML'
        )
        await state.update_data(selected_quiz_category=None)


async def launch_quiz_for_category_from_message(
    message: Message,
    state: FSMContext,
    category: str,
) -> int | None:
    """
    Запускает квиз по категории, используя обычное сообщение вместо callback.
    Возвращает идентификатор созданной quiz-сессии или None.
    """
    proxy_call = SimpleNamespace(
        message=message,
        from_user=SimpleNamespace(id=message.chat.id),
    )
    await _start_quiz_for_category(proxy_call, state, category)
    data = await state.get_data()
    return data.get('quiz_session_id')


# ==========================================
# 📝 ПРОХОЖДЕНИЕ КВИЗА
# ==========================================

@dp.callback_query(QuizStates.waiting_for_answer, F.data.startswith('quiz_answer_'))
async def handle_quiz_answer(call: CallbackQuery, state: FSMContext):
    """
    Обработка ответа на вопрос
    """
    # Получаем session_id из FSM
    data = await state.get_data()
    session_id = data.get('quiz_session_id')
    
    if not session_id:
        await call.answer("⚠️ Сессия потеряна", show_alert=True)
        await state.clear()
        return
    
    # Получаем сессию
    quiz_session = await db_quiz_session.get(session_id)
    
    if not quiz_session:
        await call.answer("⚠️ Квиз не найден", show_alert=True)
        await state.clear()
        return
    
    # Текущий вопрос
    current_idx = quiz_session.current_question_index
    current_question = quiz_session.questions[current_idx]
    
    # Получаем текст ответа по индексу (callback_data теперь содержит индекс, а не полный текст)
    answer_idx = int(call.data.replace('quiz_answer_', ''))
    answer_value = current_question['options'][answer_idx]
    
    # Сохраняем ответ
    quiz_session = await db_quiz_session.update_answer(
        session_id=session_id,
        question_id=current_question['id'],
        answer_value=answer_value
    )
    
    await call.answer("✅ Ответ сохранён")

    # Отключаем старую клавиатуру, чтобы нельзя было повторно жать варианты
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    quiz_session, status_msg = await _ensure_next_question(call.message, quiz_session)
    await _maybe_send_mid_insight(call.message, quiz_session, state)
    
    # 🔥 ADAPTIVE BRANCHING: проверяем нужно ли добавить follow-up вопросы
    if is_feature_enabled('ENABLE_ADAPTIVE_QUIZ') and await adaptive_quiz.should_branch(quiz_session):
        try:
            followup_questions = await adaptive_quiz.get_adaptive_questions(quiz_session)
            
            if followup_questions:
                normalized = generator._normalize_question_list(followup_questions, quiz_session.category)
                quiz_session.questions.extend(normalized)
                quiz_session.total_questions += len(normalized)
                
                # Сохраняем обновленную сессию
                quiz_session = await db_quiz_session.update(quiz_session)
                logging.info(
                    f"[quiz] Adaptive branching added {len(normalized)} questions: "
                    f"total_questions={quiz_session.total_questions}, "
                    f"questions_len={len(quiz_session.questions or [])}"
                )
                
                # Уведомляем пользователя
                await call.message.answer(
                    "💡 Поймал интересный паттерн — докину пару уточняющих вопросов.",
                    parse_mode='HTML'
                )
        except Exception as e:
            logging.error(f"Adaptive branching failed: {e}", exc_info=True)
    
    # Проверяем завершён ли квиз
    logging.info(
        f"[quiz] After adaptive branch: index={quiz_session.current_question_index}, "
        f"total={quiz_session.total_questions}, questions_len={len(quiz_session.questions or [])}"
    )
    if quiz_session.current_question_index >= quiz_session.total_questions:
        # Квиз завершён!
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await _finish_quiz(call.message, quiz_session, state)
    else:
        # Генерируем и показываем следующий вопрос
        await _show_current_question(call.message, quiz_session, state, status_msg)


@dp.message(QuizStates.waiting_for_answer, F.text)
async def handle_text_answer(message: Message, state: FSMContext):
    """
    Обработка текстового ответа (для type=text вопросов)
    """
    answer_value = (message.text or "").strip()

    if answer_value.startswith("/"):
        command = answer_value.split()[0].lower()

        await state.clear()

        from bot.handlers.user.start import start_message, menu_message  # local import to avoid circular deps

        if command in {"/start", "/restart"}:
            await start_message(message, state)
        elif command in {"/menu", "/main", "/me"}:
            await menu_message(message, state)
        else:
            await message.answer("⚠️ Эта команда недоступна во время квиза. Используй /menu или /start.")
        return
    
    # Получаем session_id
    data = await state.get_data()
    session_id = data.get('quiz_session_id')
    
    if not session_id:
        await message.answer("⚠️ Сессия потеряна")
        await state.clear()
        return
    
    # Получаем сессию
    quiz_session = await db_quiz_session.get(session_id)
    
    if not quiz_session:
        await message.answer("⚠️ Квиз не найден")
        await state.clear()
        return
    
    # Текущий вопрос
    current_idx = quiz_session.current_question_index
    current_question = quiz_session.questions[current_idx]
    
    # Проверяем что это текстовый вопрос
    if current_question.get('type') != 'text':
        await message.answer("⚠️ Выберите ответ из предложенных вариантов")
        return
    
    # Сохраняем ответ
    quiz_session = await db_quiz_session.update_answer(
        session_id=session_id,
        question_id=current_question['id'],
        answer_value=answer_value
    )
    
    quiz_session, status_msg = await _ensure_next_question(message, quiz_session)
    await _maybe_send_mid_insight(message, quiz_session, state)
    
    # Проверяем завершён ли квиз
    if quiz_session.current_question_index >= quiz_session.total_questions:
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await _finish_quiz(message, quiz_session, state)
    else:
        await _show_current_question(message, quiz_session, state, status_msg)


@dp.message(QuizStates.waiting_for_answer, F.voice)
async def handle_voice_answer(message: Message, state: FSMContext):
    """Обработать голосовой ответ для текстовых вопросов."""
    data = await state.get_data()
    session_id = data.get('quiz_session_id')

    if not session_id:
        await message.answer("⚠️ Сессия потеряна")
        await state.clear()
        return

    quiz_session = await db_quiz_session.get(session_id)
    if not quiz_session:
        await message.answer("⚠️ Квиз не найден")
        await state.clear()
        return

    current_idx = quiz_session.current_question_index
    question = quiz_session.questions[current_idx]

    if question.get('type') != 'text':
        await message.answer("Сейчас нужно выбрать вариант на кнопке — голос сюда не зайдёт.")
        return

    voice_dir = Path("voice")
    ready_dir = Path("ready")
    voice_dir.mkdir(parents=True, exist_ok=True)
    ready_dir.mkdir(parents=True, exist_ok=True)

    token = uuid.uuid4().hex
    raw_path = voice_dir / f"quiz_{token}.ogg"
    wav_path = ready_dir / f"quiz_{token}.wav"

    try:
        file_info = await message.bot.get_file(message.voice.file_id)
        await message.bot.download_file(file_info.file_path, raw_path)
        convert_voice(str(raw_path), str(wav_path))
        transcript = await transcribe_audio(str(wav_path))
    except Exception as exc:
        logging.exception("Quiz voice processing failed", exc_info=exc)
        await message.answer("⚠️ Не смог разобрать голос — попробуй ещё раз или напиши текстом.")
        return
    finally:
        for path in (raw_path, wav_path):
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

    transcript = (transcript or "").strip()
    if not transcript:
        await message.answer("⚠️ Не получилось распознать. Скажи ещё раз или напиши текстом.")
        return

    quiz_session = await db_quiz_session.update_answer(
        session_id=session_id,
        question_id=question['id'],
        answer_value=transcript
    )

    await message.answer(f"🎙️ Принял голосовой ответ: {transcript}")

    quiz_session, status_msg = await _ensure_next_question(message, quiz_session)
    await _maybe_send_mid_insight(message, quiz_session, state)

    if quiz_session.current_question_index >= quiz_session.total_questions:
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await _finish_quiz(message, quiz_session, state)
    else:
        await _show_current_question(message, quiz_session, state, status_msg)


# ==========================================
# 🎨 ПОКАЗ ВОПРОСА
# ==========================================

async def _show_current_question(
    message: Message,
    quiz_session,
    state: FSMContext,
    status_msg_to_delete=None
):
    """
    Показать текущий вопрос
    
    Args:
        status_msg_to_delete: Опциональное статус-сообщение для удаления перед показом вопроса
    """
    current_idx = quiz_session.current_question_index
    total = quiz_session.total_questions
    
    logging.info(
        f"[quiz] Showing question: index={current_idx}, total={total}, "
        f"questions_len={len(quiz_session.questions or [])}"
    )
    
    if current_idx >= len(quiz_session.questions or []):
        logging.error(
            f"[quiz] Question index out of range! index={current_idx}, "
            f"questions_len={len(quiz_session.questions or [])}"
        )
        await message.answer("⚠️ Ошибка: вопрос не найден. Попробуйте /quiz заново")
        return
    
    # Удаляем предыдущий вопрос, если он есть
    data = await state.get_data()
    last_question_message_id = data.get('last_question_message_id')
    if last_question_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_question_message_id)
        except Exception:
            pass

    question = quiz_session.questions[current_idx]
    
    # Форматируем вопрос
    text = generator.format_question_for_telegram(
        question,
        current_idx + 1,
        total
    )
    
    # Создаём клавиатуру в зависимости от типа вопроса
    keyboard = _create_answer_keyboard(question)
    
    # Добавляем кнопку отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Выйти в меню", callback_data="quiz_go_menu")
    ])
    
    try:
        sent_message = await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"[quiz] Failed to send question: {e}", exc_info=True)
        raise

    # Удаляем статус после появления нового вопроса
    if status_msg_to_delete:
        try:
            await status_msg_to_delete.delete()
        except Exception:
            pass

    # Сохраняем ID последнего вопроса для последующего удаления
    await state.update_data(last_question_message_id=sent_message.message_id)


# ==========================================
# 🎉 ЗАВЕРШЕНИЕ КВИЗА
# ==========================================

async def _finish_quiz(message: Message, quiz_session, state: FSMContext):
    """
    Завершить квиз и показать результаты
    """
    user_id = message.chat.id
    
    # Сбрасываем последнее сообщение вопроса
    await state.update_data(last_question_message_id=None)

    # Показываем loading
    status_msg = await message.answer("🔄 Анализирую результаты...")
    
    try:
        # Анализируем результаты (переиспользуем pattern_analyzer!)
        quiz_data = {
            'data': {
                'questions': quiz_session.questions,
                'answers': quiz_session.answers
            },
            'category': quiz_session.category
        }
        
        results = await analyzer.analyze_quiz_results(
            user_id=user_id,
            quiz_session=quiz_data,
            category=quiz_session.category
        )
        
        # Сохраняем результаты
        await db_quiz_session.complete(quiz_session.id, results)
        
        # Форматируем для отображения
        formatted_text = await analyzer.format_results_for_telegram(results, user_id)
        
        # Удаляем loading
        await status_msg.delete()
        
        # Показываем результаты
        await message.answer(
            text=formatted_text,
            parse_mode='HTML'
        )
        
        # Возвращаем главное меню
        await message.answer(
            texts.menu,
            reply_markup=build_quiz_menu_keyboard(),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            f"⚠️ Ошибка при анализе: {e}\n\n"
            "Ваши ответы сохранены, попробуйте позже."
        )
    
    finally:
        # Очищаем FSM
        await state.clear()


# ==========================================
# 🔄 RESUME КВИЗА
# ==========================================

@dp.callback_query(F.data == 'quiz_resume')
async def resume_quiz_callback(call: CallbackQuery, state: FSMContext):
    """
    Продолжить незавершённый квиз
    """
    user_id = call.from_user.id
    
    # Получаем активную сессию
    quiz_session = await db_quiz_session.get_active(user_id)
    
    if not quiz_session:
        await call.answer("⚠️ Активный квиз не найден", show_alert=True)
        return
    
    # Сохраняем в FSM
    await state.update_data(
        quiz_session_id=quiz_session.id,
        last_question_message_id=None
    )
    await state.set_state(QuizStates.waiting_for_answer)
    
    # Скрываем клавиатуру Resume/New
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Показываем текущий вопрос
    await _show_current_question(call.message, quiz_session, state)


@dp.callback_query(F.data == 'quiz_new')
async def new_quiz_callback(call: CallbackQuery):
    """
    Начать новый квиз (отменить старый)
    """
    user_id = call.from_user.id
    
    # Отменяем старую сессию
    active_session = await db_quiz_session.get_active(user_id)
    if active_session:
        await db_quiz_session.cancel(active_session.id)
    
    # Показываем категории
    await _safe_set_text(
        call.message,
        "🧠 <b>Выберите категорию квиза:</b>",
        reply_markup=_categories_keyboard(),
        parse_mode='HTML'
    )


async def _compose_answer_history(quiz_session) -> list[dict]:
    """Собрать историю вопросов/ответов для генерации следующих шагов."""
    question_map = {item.get('id'): item for item in (quiz_session.questions or [])}
    history: list[dict] = []
    for answer in quiz_session.answers or []:
        question = question_map.get(answer.get('question_id'))
        if not question:
            continue
        history.append(
            {
                "question_text": question.get('text', ''),
                "answer_value": answer.get('value') or answer.get('answer_value', ''),
            }
        )
    return history


async def _queue_next_question_if_needed(quiz_session):
    """Гарантировать, что следующий вопрос уже готов перед показом."""
    if not quiz_session:
        return quiz_session

    if quiz_session.current_question_index >= quiz_session.total_questions:
        return quiz_session

    if len(quiz_session.questions or []) > quiz_session.current_question_index:
        return quiz_session

    if len(quiz_session.questions or []) >= quiz_session.total_questions:
        return quiz_session

    answer_history = await _compose_answer_history(quiz_session)
    user_profile = await db_user_profile.get_or_create(quiz_session.user_id)
    profile_data = {
        "patterns": user_profile.patterns.get('patterns', []),
    }

    next_number = len(quiz_session.questions or []) + 1
    new_question = await generator.generate_adaptive_question(
        category=quiz_session.category,
        question_number=next_number,
        previous_answers=answer_history,
        user_profile=profile_data,
    )

    if not new_question:
        logging.debug("[quiz] No adaptive question generated (session=%s)", quiz_session.id)
        return quiz_session

    normalized = generator._normalize_question_list([new_question], quiz_session.category)
    if not normalized:
        return quiz_session

    quiz_session.questions.extend(normalized)
    logging.info(
        "[quiz] Enqueued conversational follow-up (session=%s, total=%s)",
        quiz_session.id,
        len(quiz_session.questions),
    )
    return await db_quiz_session.update(quiz_session)


async def _ensure_next_question(message: Message, quiz_session) -> tuple:
    """
    ✨ TIER 1: Улучшенная генерация с timeout и анимированным таймером
    
    Показать статус генерации и убедиться, что следующий вопрос готов.
    
    Returns:
        (updated_session, status_msg) - session и опциональное статус-сообщение для удаления позже
    """
    import asyncio
    import time
    
    needs_generation = (
        quiz_session
        and quiz_session.current_question_index < quiz_session.total_questions
        and len(quiz_session.questions or []) <= quiz_session.current_question_index
    )

    status_msg = None
    updated_session = quiz_session

    if needs_generation:
        status_msg = await message.answer("⏳ Генерирую следующий вопрос...")

        # ✨ TIER 1: Генерация с timeout (30 сек) и анимированным таймером
        start_time = time.time()
        TIMEOUT_SECONDS = 30
        UPDATE_INTERVAL = 3  # Обновляем каждые 3 секунды
        
        async def generate_with_animation():
            """Генерировать вопрос с анимацией таймера"""
            generation_task = asyncio.create_task(_queue_next_question_if_needed(quiz_session))
            
            while not generation_task.done():
                elapsed = int(time.time() - start_time)
                remaining = max(0, TIMEOUT_SECONDS - elapsed)
                
                # Анимированный таймер: ⏳ → ⌛ → ⏳
                animation = "⌛" if (elapsed // 2) % 2 == 0 else "⏳"
                
                if remaining > 15:
                    timer_text = f"{animation} Генерирую вопрос..."
                elif remaining > 5:
                    timer_text = f"{animation} Генерирую вопрос... (~{remaining} сек)"
                else:
                    timer_text = f"⏱ Почти готово... ({remaining} сек)"
                
                try:
                    await status_msg.edit_text(timer_text)
                except Exception:
                    pass  # Игнорируем ошибки редактирования
                
                # Ждём либо завершения, либо интервал обновления
                try:
                    await asyncio.wait_for(
                        asyncio.shield(generation_task),
                        timeout=UPDATE_INTERVAL
                    )
                    break
                except asyncio.TimeoutError:
                    continue  # Продолжаем цикл анимации
            
            return await generation_task
        
        try:
            updated_session = await asyncio.wait_for(
                generate_with_animation(),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logging.error(
                f"[quiz] Generation timeout after {TIMEOUT_SECONDS}s for session {quiz_session.id}"
            )
            try:
                await status_msg.edit_text(
                    "⚠️ Генерация затянулась. Использую запасной вопрос..."
                )
            except Exception:  # noqa: BLE001
                pass

            updated_session = await _queue_next_question_if_needed(quiz_session)
        except Exception as err:  # noqa: BLE001
            logging.exception("[quiz] Unexpected error while generating question: %s", err)
            updated_session = await _queue_next_question_if_needed(quiz_session)
    
    # НЕ удаляем status_msg здесь — вернём его наружу для удаления перед показом вопроса
    return updated_session, status_msg


async def _maybe_send_mid_insight(message: Message, quiz_session, state: FSMContext):
    """Отправить короткий инсайт, если дошли до контрольной точки."""
    if not quiz_session:
        return

    trigger_points = {3, 6}
    index = quiz_session.current_question_index
    if index not in trigger_points:
        return

    data = await state.get_data()
    already_sent = set(data.get('mid_insight_sent', []))
    if index in already_sent:
        return

    patterns = await adaptive_quiz.analyze_patterns(quiz_session)
    if not patterns:
        return

    strong_pattern = next((p for p in patterns if p.get('confidence', 0) >= 0.7), None)
    if not strong_pattern:
        return

    insight_text = _format_mid_insight(strong_pattern)
    if not insight_text:
        return

    await message.answer(insight_text, parse_mode='HTML')
    already_sent.add(index)
    await state.update_data(mid_insight_sent=list(already_sent))


def _format_mid_insight(pattern: dict) -> str:
    import html

    title_raw = pattern.get('title_ru') or pattern.get('title') or 'Паттерн'
    title = html.escape(title_raw)
    contradiction = pattern.get('contradiction')
    hidden_dynamic = pattern.get('hidden_dynamic')
    blocked_resource = pattern.get('blocked_resource')

    parts = [f"💡 <b>Кажется, всплывает паттерн: {title}</b>"]
    if contradiction:
        parts.append(f"⚡ Противоречие: {html.escape(contradiction)}")
    if hidden_dynamic:
        parts.append(f"🔍 Скрытая динамика: {html.escape(hidden_dynamic)}")
    if blocked_resource:
        parts.append(f"🔓 Ресурс внутри: {html.escape(blocked_resource)}")
    parts.append("Продолжим и проверим, откликается ли тебе это?")

    return "\n".join(parts)


# ==========================================
# ⌨️ КЛАВИАТУРЫ
# ==========================================

def _categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с категориями квизов"""
    categories = generator.QUIZ_CATEGORIES
    
    buttons = []
    for cat_id, cat_info in categories.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat_info['emoji']} {cat_info['name']}",
                callback_data=f"quiz_category_{cat_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text='🏠 Меню',
            callback_data='quiz_go_menu'
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _add_emoji_to_option(text: str) -> str:
    """
    ✨ TIER 2: Добавить эмодзи к варианту ответа
    
    Mapping популярных вариантов ответов на эмодзи для улучшения UX
    """
    # Эмоциональные реакции
    emoji_map = {
        # Негативные эмоции
        'паника': '😰',
        'стыд': '😰',
        'тревога': '😰',
        'страх': '😨',
        'злость': '😤',
        'злюсь': '😤',
        'грусть': '😔',
        'растерянность': '😕',
        'смущ': '😅',
        
        # Позитивные/нейтральные
        'спокойно': '😌',
        'радость': '😊',
        'счастье': '😊',
        'уверенность': '💪',
        'интерес': '🤔',
        
        # Частота (для scale вопросов)
        'никогда': '⭕',
        'редко': '🟡',
        'иногда': '🟠',
        'часто': '🔴',
        'постоянно': '🔥',
        
        # Действия
        'избегаю': '🚫',
        'игнорирую': '🙈',
        'обсуждаю': '💬',
        'решаю': '✅',
        'жду': '⏳',
    }
    
    text_lower = text.lower()
    
    # Ищем совпадение по ключевым словам
    for keyword, emoji in emoji_map.items():
        if keyword in text_lower:
            # Добавляем эмодзи только если его ещё нет
            if not any(char in text for char in emoji_map.values()):
                return f"{emoji} {text}"
            return text
    
    # Если не нашли подходящий эмодзи - возвращаем как есть
    return text


def _create_answer_keyboard(question: dict) -> InlineKeyboardMarkup:
    """Создать клавиатуру для ответа на вопрос"""
    if question['type'] == 'scale':
        # 5-point scale - используем индексы вместо полного текста
        buttons = [
            [
                InlineKeyboardButton(
                    text=_add_emoji_to_option(option),  # ✨ TIER 2: добавляем эмодзи
                    callback_data=f"quiz_answer_{idx}"
                )
            ]
            for idx, option in enumerate(question.get('options', []))
        ]
    elif question['type'] == 'multiple_choice':
        # Multiple choice - используем индексы вместо полного текста
        buttons = [
            [
                InlineKeyboardButton(
                    text=_add_emoji_to_option(option),  # ✨ TIER 2: добавляем эмодзи
                    callback_data=f"quiz_answer_{idx}"
                )
            ]
            for idx, option in enumerate(question.get('options', []))
        ]
    else:
        # Text - no keyboard needed
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _resume_or_new_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура: продолжить или начать новый"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить", callback_data="quiz_resume")],
        [InlineKeyboardButton(text="🆕 Начать новый", callback_data="quiz_new")]
    ])

