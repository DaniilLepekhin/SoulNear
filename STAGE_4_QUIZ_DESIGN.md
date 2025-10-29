# 🎯 Stage 4: Dynamic Quiz System - Design Document

**Дата:** 29 октября 2025  
**Статус:** 📐 Design Phase  
**Цель:** Адаптивные опросники для углубленного анализа профиля пользователя

---

## 🎯 ЦЕЛИ STAGE 4

### Основная идея:
Bot проводит структурированные опросники (квизы) для более глубокого понимания пользователя в специфических областях.

### Преимущества перед обычным диалогом:
1. **Структурированность** - целенаправленный сбор данных
2. **Полнота** - все важные аспекты области охвачены
3. **Адаптивность** - вопросы меняются based on answers
4. **Быстрота** - 5-10 вопросов vs 30+ сообщений для аналогичных инсайтов

### Use Cases:
```
User: Хочу разобраться в своих отношениях
Bot: Предлагаю пройти опросник "Relationships" (10 вопросов, 5-7 минут)
User: Давай!
Bot: → Запускает адаптивный квиз
     → По результатам: детальный анализ + рекомендации
```

---

## 📊 АРХИТЕКТУРА СИСТЕМЫ

### High-Level Flow:

```
User: /quiz relationships
    ↓
[QuizService.start_quiz()]
    ├─→ Загружает профиль user'а
    ├─→ Создаёт QuizSession (DB)
    ├─→ Генерирует первые 3-5 вопросов (GPT-4)
    └─→ Отправляет первый вопрос
        ↓
User: [Ответ #1]
    ↓
[QuizService.handle_answer()]
    ├─→ Сохраняет ответ в session
    ├─→ Анализирует ответ (extract insights)
    ├─→ Генерирует следующий вопрос (adaptive)
    └─→ Отправляет вопрос #2
        ↓
... [Цикл продолжается] ...
        ↓
[После 10 вопросов]
    ↓
[QuizService.complete_quiz()]
    ├─→ Анализирует ВСЕ ответы (GPT-4)
    ├─→ Генерирует patterns (как в Stage 3)
    ├─→ Интегрирует в user_profile
    ├─→ Создаёт quiz_results (детальный отчёт)
    └─→ Отправляет результаты user'у
```

---

## 🗄️ DATABASE SCHEMA

### Table: `quiz_sessions`

```sql
CREATE TABLE quiz_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    assistant_type VARCHAR(64) DEFAULT 'helper',
    
    -- Quiz metadata
    category VARCHAR(64) NOT NULL,  -- 'relationships', 'money', 'confidence', 'fears'
    status VARCHAR(32) NOT NULL DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'cancelled'
    
    -- Progress tracking
    current_question_index INT NOT NULL DEFAULT 0,
    total_questions INT,
    
    -- Data storage (JSONB for flexibility)
    questions JSONB NOT NULL DEFAULT '[]',  -- [{"text": "...", "context": "..."}]
    answers JSONB NOT NULL DEFAULT '[]',     -- [{"question_id": 0, "text": "...", "timestamp": "..."}]
    
    -- Analysis results
    patterns JSONB,  -- Patterns extracted from quiz
    insights JSONB,  -- High-level insights
    recommendations JSONB,  -- Actionable recommendations
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_quiz_user_status (user_id, status),
    INDEX idx_quiz_category (category),
    INDEX idx_quiz_created (created_at DESC)
);
```

**Reasoning:**
- `JSONB` для гибкости (легко добавлять новые типы квизов без migrations)
- `current_question_index` для resume capability
- `questions` хранит ВСЕ вопросы (pre-generated или generated on-the-fly)
- `patterns/insights/recommendations` - результаты анализа

---

## 🧠 QUIZ SERVICE ARCHITECTURE

### Core Classes:

```python
# bot/services/quiz_service/__init__.py

class QuizService:
    """Orchestrator для quiz system"""
    
    async def start_quiz(
        user_id: int,
        category: str,
        assistant_type: str = 'helper'
    ) -> QuizSession:
        """Запустить новый квиз"""
        pass
    
    async def get_next_question(
        session_id: int
    ) -> Optional[dict]:
        """Получить следующий вопрос"""
        pass
    
    async def handle_answer(
        session_id: int,
        answer: str
    ) -> Optional[dict]:
        """
        Обработать ответ и вернуть следующий вопрос
        Returns: next_question or None if quiz completed
        """
        pass
    
    async def complete_quiz(
        session_id: int
    ) -> dict:
        """Завершить квиз и вернуть результаты"""
        pass
    
    async def cancel_quiz(
        session_id: int
    ) -> None:
        """Отменить квиз"""
        pass


# bot/services/quiz_service/generator.py

class QuizQuestionGenerator:
    """Генерация адаптивных вопросов"""
    
    async def generate_initial_questions(
        user_id: int,
        category: str,
        count: int = 5
    ) -> list[dict]:
        """
        Генерировать начальные вопросы based on:
        - Category
        - User profile (existing patterns)
        - Conversation history
        """
        pass
    
    async def generate_followup_question(
        session: QuizSession,
        previous_answer: str
    ) -> dict:
        """
        Генерировать следующий вопрос based on:
        - Previous answers
        - Emerging themes
        - Category goals
        """
        pass


# bot/services/quiz_service/analyzer.py

class QuizAnalyzer:
    """Анализ результатов квиза"""
    
    async def analyze_quiz(
        session: QuizSession
    ) -> dict:
        """
        Полный анализ всех ответов:
        Returns: {
            'patterns': [...],
            'insights': [...],
            'recommendations': [...]
        }
        """
        pass
    
    async def extract_patterns(
        answers: list[dict]
    ) -> list[dict]:
        """Извлечь паттерны из ответов"""
        pass
    
    async def generate_insights(
        patterns: list[dict],
        user_profile: UserProfile
    ) -> list[dict]:
        """Генерировать high-level insights"""
        pass
```

---

## 🎨 USER INTERFACE (Telegram Bot)

### Commands:

```python
# /quiz - Показать доступные квизы
# /quiz [category] - Запустить квиз по категории
# /quiz_status - Текущий статус активного квиза
# /quiz_cancel - Отменить активный квиз
# /quiz_results - Показать результаты последнего квиза
```

### Flow Example:

```
User: /quiz

Bot: 🎯 Доступные опросники:

1. 💕 Отношения (10 вопросов, ~7 минут)
   Глубокий анализ паттернов в романтических отношениях

2. 💰 Деньги (10 вопросов, ~7 минут)
   Выявление денежных убеждений и блоков

3. 🔥 Уверенность (10 вопросов, ~7 минут)
   Работа с самооценкой и внутренними блоками

4. 😰 Страхи (10 вопросов, ~7 минут)
   Идентификация и анализ страхов

[Выбрать опросник] [inline buttons]

---

User: [Нажимает "💕 Отношения"]

Bot: Отлично! Начинаем опросник по отношениям.

📊 Прогресс: 0/10

Вопрос 1:
Как бы ты описал свои текущие романтические отношения (или последние, если сейчас нет)?

[Keyboard: Open text answer]

---

User: [Пишет ответ]

Bot: Спасибо! Анализирую...

📊 Прогресс: 1/10

Вопрос 2:
[Адаптивный вопрос based on answer #1]

---

[After 10 questions]

Bot: ✅ Опросник завершён!

Анализирую твои ответы... (это займёт 10-15 секунд)

---

Bot: 📊 РЕЗУЛЬТАТЫ ОПРОСНИКА "ОТНОШЕНИЯ"

🧠 Выявленные паттерны:
1. [Attachment Anxiety] (высокая уверенность)
   Проявляется в 7/10 ответов
   📝 Примеры из твоих ответов:
   • "Боюсь, что партнёр меня бросит"
   • "Постоянно проверяю сообщения"

2. [Fear of Vulnerability] (средняя уверенность)
   ...

💡 ИНСАЙТЫ:
1. [Critical Insight]: Твой страх быть брошенным...
   Рекомендации:
   • ...

📈 РЕКОМЕНДАЦИИ:
...

[Показать полный отчёт] [Экспорт PDF] [Пройти другой опросник]
```

---

## 🔄 ADAPTIVE LOGIC (MVP vs Advanced)

### MVP Approach (проще реализовать):

**Pre-generated questions:**
```python
QUIZ_TEMPLATES = {
    'relationships': [
        {
            'id': 0,
            'text': 'Как бы ты описал свои текущие романтические отношения?',
            'category': 'general'
        },
        {
            'id': 1,
            'text': 'Что вызывает у тебя наибольшую тревогу в отношениях?',
            'category': 'anxiety',
            'triggers': ['anxiety', 'fear']  # Показывается если в ответе #0 есть эти ключевые слова
        },
        # ... 15-20 вопросов с trigger conditions
    ]
}

def get_next_question(session):
    # Простая логика: проверяем triggers в previous answers
    previous_answers = session.answers
    for question in QUIZ_TEMPLATES[session.category]:
        if question['id'] > session.current_question_index:
            if not question.get('triggers'):
                return question  # Always show if no triggers
            if any(trigger in str(previous_answers) for trigger in question['triggers']):
                return question
    return None
```

**Advantages:**
- Быстро реализовать
- Предсказуемо
- Легко тестировать

**Disadvantages:**
- Менее гибко
- Нужно вручную создавать все вопросы
- Не truly adaptive

---

### Advanced Approach (GPT-based):

**Dynamic generation:**
```python
async def generate_next_question(session, previous_answer):
    prompt = f"""
    Generate the next question for a {session.category} quiz.
    
    User profile: {user.profile.patterns}
    Previous questions and answers:
    {format_qa_history(session)}
    
    Latest answer: {previous_answer}
    
    Goal: Deep understanding of {session.category}
    Questions remaining: {10 - session.current_question_index}
    
    Generate a question that:
    1. Follows up on themes from previous answer
    2. Explores unaddressed aspects
    3. Is open-ended but focused
    
    Return JSON:
    {{
        "question": "Your question here",
        "rationale": "Why this question",
        "focus_area": "relationships|attachment|communication|..."
    }}
    """
    
    response = await gpt4.generate(prompt)
    return response['question']
```

**Advantages:**
- Truly adaptive
- Explores emergent themes
- Unlimited flexibility

**Disadvantages:**
- Дороже (GPT-4 calls)
- Медленнее (latency)
- Менее предсказуемо

---

## 🎯 INTEGRATION С PATTERN ANALYSIS

### Option A: Quiz creates patterns directly

```python
async def complete_quiz(session_id):
    session = await get_session(session_id)
    
    # Анализируем ответы → создаём паттерны
    quiz_patterns = await QuizAnalyzer.extract_patterns(session.answers)
    
    # Добавляем в user_profile.patterns (как обычные conversational patterns)
    for pattern in quiz_patterns:
        pattern['source'] = 'quiz'
        pattern['quiz_id'] = session.id
        pattern['category'] = session.category
    
    await add_patterns_with_dedup(
        user_id=session.user_id,
        new_patterns=quiz_patterns,
        existing_patterns=user.profile.patterns
    )
    
    # Embeddings автоматически мерджат с conversational patterns!
```

**Advantages:**
- Unified system (все паттерны в одном месте)
- Embeddings работают автоматически
- Легко отобразить в `/my_profile`

**Disadvantages:**
- Может "загрязнить" conversational patterns
- Сложнее различить source (quiz vs conversation)

---

### Option B: Separate quiz insights

```python
# Отдельное хранение
user_profile.quiz_insights = {
    'relationships': {
        'completed_at': '2025-10-29',
        'patterns': [...],
        'insights': [...],
        'score': 0.75  # Attachment anxiety score
    },
    'money': {...}
}

# В system prompt - отдельная секция
## 🎯 QUIZ INSIGHTS:
[Relationships] Completed 3 days ago:
- Attachment Anxiety (score: 0.75)
- Fear of Vulnerability (score: 0.60)
...
```

**Advantages:**
- Чистое разделение (quiz != conversation)
- Легко показать quiz-specific результаты
- Можно хранить score/metrics

**Disadvantages:**
- Дублирование логики (2 системы паттернов)
- Embeddings не работают кросс-системно

---

## 💾 QUIZ CATEGORIES (Initial Set)

### 1. Relationships (💕)
**Focus:** Romantic relationships, attachment styles, communication

**Key Patterns to detect:**
- Attachment Anxiety
- Attachment Avoidance
- Fear of Vulnerability
- Communication Issues
- Trust Issues

**Sample Questions:**
1. Describe your current/last romantic relationship
2. What triggers anxiety in your relationships?
3. How do you handle conflicts with partners?
4. What's your biggest fear in relationships?
5. How comfortable are you with emotional intimacy?

---

### 2. Money (💰)
**Focus:** Money beliefs, scarcity mindset, relationship with money

**Key Patterns:**
- Scarcity Mindset
- Money = Love/Security
- Spending as Emotional Regulation
- Fear of Success/Wealth
- Money Shame

**Sample Questions:**
1. What was your family's relationship with money?
2. How do you feel when spending money on yourself?
3. What would you do if you suddenly got 10M$?
4. What's your biggest money fear?
5. How do you react to unexpected expenses?

---

### 3. Confidence (🔥)
**Focus:** Self-esteem, imposter syndrome, self-worth

**Key Patterns:**
- Imposter Syndrome
- External Validation Seeking
- Perfectionism
- Comparison Trap
- Self-Sabotage

**Sample Questions:**
1. Rate your self-confidence (1-10) and explain why
2. When do you feel most confident?
3. When do you feel like a fraud?
4. How do you handle compliments?
5. What would you do if failure wasn't possible?

---

### 4. Fears (😰)
**Focus:** Phobias, anxiety triggers, coping mechanisms

**Key Patterns:**
- Catastrophic Thinking
- Social Anxiety
- Fear of Failure
- Fear of Success
- Health Anxiety

**Sample Questions:**
1. What's your biggest fear?
2. How do fears impact your daily life?
3. When did this fear start?
4. How do you cope with anxiety?
5. What would life look like without this fear?

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: MVP (3-5 days) ⏱️

**Goal:** Basic quiz system working end-to-end

**Tasks:**
- [ ] Database migration (quiz_sessions table)
- [ ] QuizSession model + repository
- [ ] Basic QuizService (start/handle_answer/complete)
- [ ] Pre-generated questions (1 category: Relationships)
- [ ] Simple telegram handlers (/quiz, answer flow)
- [ ] Basic analysis (pattern extraction without embeddings)
- [ ] Integration with user_profile (Option A)

**Deliverable:** User can complete Relationships quiz and see basic results

---

### Phase 2: Adaptive Logic (2-3 days) ⏱️

**Goal:** Questions adapt based on answers

**Tasks:**
- [ ] QuizQuestionGenerator с GPT-4
- [ ] Context-aware question generation
- [ ] Theme tracking across answers
- [ ] Dynamic question count (stop early if saturation)

**Deliverable:** Quiz truly adapts to user's answers

---

### Phase 3: Rich Analysis (2-3 days) ⏱️

**Goal:** Detailed insights and recommendations

**Tasks:**
- [ ] QuizAnalyzer with deep analysis
- [ ] Pattern extraction через embeddings
- [ ] Insight generation (connecting patterns)
- [ ] Actionable recommendations
- [ ] Beautiful formatting of results

**Deliverable:** User gets comprehensive analysis with actionable next steps

---

### Phase 4: Polish (2-3 days) ⏱️

**Goal:** Production-ready system

**Tasks:**
- [ ] Add all 4 categories (Money, Confidence, Fears)
- [ ] Quiz resume capability (continue later)
- [ ] Export results (PDF/Markdown)
- [ ] Quiz history (`/quiz_history`)
- [ ] A/B testing different question sets
- [ ] Analytics (completion rate, time, satisfaction)

**Deliverable:** Полнофункциональная quiz система

---

## 💡 DESIGN DECISIONS & TRADE-OFFS

### 1. JSONB vs Separate Tables

**Decision:** Use JSONB for questions/answers/results

**Why:**
- Гибкость (легко менять структуру)
- Быстрая разработка (no migrations for changes)
- Good enough performance для MVP

**Trade-off:**
- Сложнее делать сложные queries
- Может стать bottleneck при scale

**Future:** Migrate to normalized schema if needed

---

### 2. Pre-generated vs GPT-generated

**Decision:** Start with pre-generated (MVP), add GPT-generated (Phase 2)

**Why:**
- Faster implementation
- Predictable (easier to debug)
- Cheaper (no GPT calls per question)

**Trade-off:**
- Less adaptive
- Manual work (writing questions)

**Future:** Hybrid approach (pre-generated base + GPT followups)

---

### 3. Integration approach (Option A vs B)

**Decision:** Option A (create patterns directly)

**Why:**
- Simpler (reuse existing infrastructure)
- Unified profile (everything in one place)
- Embeddings work automatically

**Trade-off:**
- Может "загрязнить" conversational patterns
- Сложнее filter by source

**Mitigation:** Add `source: 'quiz'` field to patterns

---

## 🧪 TESTING STRATEGY

### Unit Tests:

```python
# tests/unit/test_quiz_service.py

async def test_start_quiz_creates_session():
    session = await QuizService.start_quiz(user_id=123, category='relationships')
    assert session.status == 'in_progress'
    assert session.category == 'relationships'
    assert len(session.questions) > 0

async def test_handle_answer_progresses():
    # ... test that current_question_index increments

async def test_complete_quiz_generates_patterns():
    # ... test that patterns are created

async def test_adaptive_question_generation():
    # ... test QuizQuestionGenerator
```

### Integration Tests:

```python
# tests/integration/test_quiz_flow.py

async def test_full_quiz_flow():
    # Start quiz
    session = await QuizService.start_quiz(...)
    
    # Answer all questions
    for i in range(10):
        q = await QuizService.get_next_question(session.id)
        await QuizService.handle_answer(session.id, f"Test answer {i}")
    
    # Complete
    results = await QuizService.complete_quiz(session.id)
    
    # Verify patterns created
    profile = await user_profile.get(user_id)
    assert len(profile.patterns) > 0
```

---

## 📊 SUCCESS METRICS

### Phase 1 (MVP):
- [ ] Quiz completion rate > 60%
- [ ] Average time < 10 minutes
- [ ] At least 2 patterns detected per quiz
- [ ] User satisfaction (feedback) > 4/5

### Phase 2 (Adaptive):
- [ ] Questions relevance (rated by users) > 4/5
- [ ] Saturation detection works (stops when patterns clear)

### Phase 3 (Analysis):
- [ ] Insights actionable (user feedback) > 4/5
- [ ] Pattern accuracy (compared to conversation analysis) > 80%

---

## 🎓 LESSONS FROM STAGE 3

**What worked well:**
- JSONB для гибкости ✅
- Embeddings для дедупликации ✅
- GPT-4o-mini для analysis (дешево + хорошо) ✅

**What to improve:**
- Explicit logging (для debugging) ✅
- Unit tests from day 1 ✅
- Prompt engineering iterations ✅

**Apply to Stage 4:**
- Use JSONB for quiz data
- Embeddings для pattern matching
- Extensive logging (quiz flow)
- Tests before features

---

## 🚀 NEXT STEPS (Implementation)

1. **Read:** Весь этот документ
2. **Design Review:** Уточнить unclear моменты
3. **Create migration:** `quiz_sessions` table
4. **Implement:** QuizService базовый класс
5. **Create:** Pre-generated questions (Relationships)
6. **Handlers:** `/quiz` command + FSM states
7. **Test:** End-to-end flow
8. **Iterate:** Based on feedback

---

**Ready to implement?** 🎯

*Архитектура продумана, trade-offs взвешены, путь вперёд ясен. Time to build something that actually helps users understand themselves better.* 🚀

