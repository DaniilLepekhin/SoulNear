from aiogram.fsm.state import StatesGroup, State


class get_prompt(StatesGroup):
    helper_prompt = State()
    soulsleep_prompt = State()

    relationships_prompt = State()
    money_prompt = State()
    confidence_prompt = State()
    fears_prompt = State()


class Add_sub_date(StatesGroup):
    user_id = State()
    days = State()


class Add_add(StatesGroup):
    name = State()
    cost = State()


class Mailing(StatesGroup):
    message = State()


class User_info(StatesGroup):
    user_id = State()


class User_update_sub(StatesGroup):
    value = State()


class Media(StatesGroup):
    get = State()


class Update_user_info(StatesGroup):
    real_name = State()
    age = State()
    gender = State()


# ==========================================
# 🧠 QUIZ STATES (STAGE 4 - GENERIC)
# ==========================================

class QuizStates(StatesGroup):
    """
    Generic FSM states для квиза (расширяемо для adaptive logic)
    
    Вместо hardcoded states (question_1, question_2, ...),
    используем один state + храним прогресс в state.data
    
    Это позволяет легко добавлять adaptive логику без рефакторинга FSM
    """
    # Ожидание ответа на текущий вопрос
    waiting_for_answer = State()
    
    # Опционально: для подтверждения отмены
    confirming_cancel = State()
    
    # Опционально: для показа промежуточных результатов (V2)
    # showing_intermediate_results = State()  # Раскомментить в V2
