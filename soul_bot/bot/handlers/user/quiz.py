"""
🧠 Quiz Handlers (Stage 4)

Handlers для динамических квизов

Flow:
1. Пользователь → /quiz или кнопка "Пройти квиз"
2. Выбирает категорию (relationships/work/emotions/etc.)
3. Проходит 10 вопросов (FSM state: waiting_for_answer)
4. Получает результаты + обновление профиля
"""
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.loader import dp
from bot.states.states import QuizStates
from bot.services.quiz_service import generator, analyzer
from bot.services.quiz.adaptive_quiz_service import AdaptiveQuizService
from bot.services.ai.gpt_service import GPTService
import database.repository.quiz_session as db_quiz_session
import database.repository.user_profile as db_user_profile
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
            count=8,  # 🔥 UPGRADE: 8 базовых вопросов (+ 2-3 адаптивных = 10-11)
            user_profile=profile_data  # ← параметр готов для V2!
        )
        
        # Создаём сессию
        quiz_session = await db_quiz_session.create(
            user_id=user_id,
            category=category,
            questions=questions
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
    
    # 🔥 ADAPTIVE BRANCHING: проверяем нужно ли добавить follow-up вопросы
    if is_feature_enabled('ENABLE_ADAPTIVE_QUIZ') and await adaptive_quiz.should_branch(quiz_session):
        try:
            # Генерируем адаптивные вопросы
            followup_questions = await adaptive_quiz.get_adaptive_questions(quiz_session)
            
            if followup_questions:
                # Добавляем вопросы в сессию
                quiz_session.questions.extend(followup_questions)
                quiz_session.total_questions = len(quiz_session.questions)
                
                # Сохраняем обновленную сессию
                await db_quiz_session.update(quiz_session)
                
                # Уведомляем пользователя
                await call.message.answer(
                    "💡 Обнаружены интересные паттерны!\n"
                    f"Добавляю {len(followup_questions)} уточняющих вопроса...",
                    parse_mode='HTML'
                )
        except Exception as e:
            # Не блокируем квиз при ошибке адаптации
            import logging
            logging.error(f"Adaptive branching failed: {e}")
    
    # Проверяем завершён ли квиз
    if quiz_session.current_question_index >= quiz_session.total_questions:
        # Квиз завершён!
        await _finish_quiz(call.message, quiz_session, state)
    else:
        # Показываем следующий вопрос
        await _show_current_question(call.message, quiz_session, state)


@dp.message(QuizStates.waiting_for_answer)
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
    
    # Проверяем завершён ли квиз
    if quiz_session.current_question_index >= quiz_session.total_questions:
        await _finish_quiz(message, quiz_session, state)
    else:
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
    except:
        # Если не получилось edit - отправляем новое
        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )


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
        
        # Предлагаем пройти ещё
        await message.answer(
            "Хотите пройти ещё один квиз?",
            reply_markup=_categories_keyboard()
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

