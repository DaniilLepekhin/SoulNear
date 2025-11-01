"""
🧠 Quiz Handlers (Stage 4)

Handlers для динамических квизов

Flow:
1. Пользователь → /quiz или кнопка "Пройти квиз"
2. Выбирает категорию (relationships/money/purpose)
3. Проходит 8–12 вопросов диалогового квиза (FSM state: waiting_for_answer)
4. Получает результаты + обновление профиля
"""
import logging
import os
import uuid
from pathlib import Path
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.loader import dp
from bot.states.states import QuizStates
from bot.services.quiz_service import generator, analyzer
from bot.services.quiz.adaptive_quiz_service import AdaptiveQuizService
from bot.services.ai.gpt_service import GPTService
from bot.functions.speech import convert_voice, transcribe_audio
import database.repository.quiz_session as db_quiz_session
import database.repository.user_profile as db_user_profile
from bot.keyboards.start import menu as main_menu_keyboard
from config import is_feature_enabled

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


@dp.callback_query(F.data == 'quiz_start')
async def quiz_start_callback(call: CallbackQuery):
    """
    Кнопка "🧠 Психологический квиз" из главного меню
    """
    if not is_feature_enabled('ENABLE_DYNAMIC_QUIZ'):
        await call.message.edit_text("⚠️ Квизы временно недоступны")
        await call.answer()
        return
    
    # Проверяем есть ли активный квиз
    active_session = await db_quiz_session.get_active(call.from_user.id)
    if active_session:
        # Resume
        await call.message.edit_text(
            "📝 У вас есть незавершённый квиз!\n\n"
            f"Категория: {active_session.category}\n"
            f"Прогресс: {active_session.current_question_index}/{active_session.total_questions}\n\n"
            "Хотите продолжить или начать новый?",
            reply_markup=_resume_or_new_keyboard()
        )
        await call.answer()
        return
    
    # Показываем категории
    await call.message.edit_text(
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
    user_id = call.from_user.id
    
    await call.answer("🔄 Генерирую вопросы...")
    
    try:
        # Получаем профиль (для V2 адаптации, пока не используется)
        profile = await db_user_profile.get_or_create(user_id)
        profile_data = {
            "patterns": profile.patterns.get('patterns', [])
        }
        
        # Генерируем вопросы (MVP: без адаптации)
        questions = await generator.generate_questions(
            category=category,
            count=3,
            user_profile=profile_data  # ← параметр готов для V2!
        )
        
        # Создаём сессию
        quiz_session = await db_quiz_session.create(
            user_id=user_id,
            category=category,
            questions=questions,
            total_questions=generator.TARGET_QUESTION_COUNT,
        )
        
        # Сохраняем session_id в FSM
        await state.update_data(quiz_session_id=quiz_session.id)
        await state.set_state(QuizStates.waiting_for_answer)
        
        # Показываем первый вопрос
        await _show_current_question(call.message, quiz_session, state)
        
    except Exception as e:
        await call.message.edit_text(
            f"⚠️ Ошибка при создании квиза: {e}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )


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

    quiz_session = await _ensure_next_question(call.message, quiz_session)
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
            import logging
            logging.error(f"Adaptive branching failed: {e}")
    
    # Проверяем завершён ли квиз
    logging.info(
        f"[quiz] After adaptive branch: index={quiz_session.current_question_index}, "
        f"total={quiz_session.total_questions}, questions_len={len(quiz_session.questions or [])}"
    )
    if quiz_session.current_question_index >= quiz_session.total_questions:
        # Квиз завершён!
        await _finish_quiz(call.message, quiz_session, state)
    else:
        # Показываем следующий вопрос
        await _show_current_question(call.message, quiz_session, state)


@dp.message(QuizStates.waiting_for_answer, F.text)
async def handle_text_answer(message: Message, state: FSMContext):
    """
    Обработка текстового ответа (для type=text вопросов)
    """
    answer_value = message.text
    
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
    
    quiz_session = await _ensure_next_question(message, quiz_session)
    await _maybe_send_mid_insight(message, quiz_session, state)
    
    # Проверяем завершён ли квиз
    if quiz_session.current_question_index >= quiz_session.total_questions:
        await _finish_quiz(message, quiz_session, state)
    else:
        quiz_session = await _ensure_next_question(message, quiz_session)
        await _show_current_question(message, quiz_session, state)


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

    quiz_session = await _ensure_next_question(message, quiz_session)
    await _maybe_send_mid_insight(message, quiz_session, state)

    if quiz_session.current_question_index >= quiz_session.total_questions:
        await _finish_quiz(message, quiz_session, state)
    else:
        quiz_session = await _ensure_next_question(message, quiz_session)
        await _show_current_question(message, quiz_session, state)


# ==========================================
# 🎨 ПОКАЗ ВОПРОСА
# ==========================================

async def _show_current_question(message: Message, quiz_session, state: FSMContext):
    """
    Показать текущий вопрос
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
        InlineKeyboardButton(text="❌ Отменить квиз", callback_data="quiz_cancel")
    ])
    
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        # Если не получилось edit - отправляем новое
        logging.debug(f"[quiz] Cannot edit message (expected for voice/text answers): {e}")
        try:
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"[quiz] Failed to send question: {e}", exc_info=True)
            raise


# ==========================================
# 🎉 ЗАВЕРШЕНИЕ КВИЗА
# ==========================================

async def _finish_quiz(message: Message, quiz_session, state: FSMContext):
    """
    Завершить квиз и показать результаты
    """
    user_id = message.chat.id
    
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
            "🏠 Главная",
            reply_markup=main_menu_keyboard
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
# ❌ ОТМЕНА КВИЗА
# ==========================================

@dp.callback_query(F.data == 'quiz_cancel')
async def cancel_quiz_callback(call: CallbackQuery, state: FSMContext):
    """
    Отменить квиз
    """
    data = await state.get_data()
    session_id = data.get('quiz_session_id')
    
    if session_id:
        await db_quiz_session.cancel(session_id)
    
    await state.clear()
    
    await call.message.edit_text(
        "❌ Квиз отменён.\n\n"
        "Вы можете начать новый в любое время: /quiz"
    )

    await call.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_keyboard
    )


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
    await state.update_data(quiz_session_id=quiz_session.id)
    await state.set_state(QuizStates.waiting_for_answer)
    
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
    await call.message.edit_text(
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


async def _ensure_next_question(message: Message, quiz_session) -> object:
    """Показать статус генерации и убедиться, что следующий вопрос готов."""
    needs_generation = (
        quiz_session
        and quiz_session.current_question_index < quiz_session.total_questions
        and len(quiz_session.questions or []) <= quiz_session.current_question_index
    )

    status_msg = None
    if needs_generation:
        status_msg = await message.answer("⏳ Генерирую следующий вопрос...")

    try:
        updated_session = await _queue_next_question_if_needed(quiz_session)
    finally:
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

    return updated_session


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

    title = html.escape(pattern.get('title', 'Паттерн'))
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
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_answer_keyboard(question: dict) -> InlineKeyboardMarkup:
    """Создать клавиатуру для ответа на вопрос"""
    if question['type'] == 'scale':
        # 5-point scale - используем индексы вместо полного текста
        buttons = [
            [
                InlineKeyboardButton(
                    text=option,
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
                    text=option,
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

