"""
GPT Prompts для Pattern Analysis

Вынесены из pattern_analyzer.py для удобства модификации и тестирования.
"""

def get_quick_analysis_prompt(conversation_text: str, existing_summaries: list[str]) -> str:
    """
    Промпт для quick_analysis V2 - ГЛУБОКИЙ АНАЛИЗ (каждые 3 сообщения)
    
    НОВАЯ ФИЛОСОФИЯ: НЕ классифицируем ("он перфекционист"), А РАСКРЫВАЕМ динамику!
    
    Args:
        conversation_text: Последние 10 сообщений formatted as "role: content"
        existing_summaries: Список существующих паттернов (titles only)
        
    Returns:
        Полный промпт для GPT-4o-mini
    """
    existing_patterns_str = "\n".join(existing_summaries) if existing_summaries else 'нет сохранённых паттернов'
    
    return f"""
🔍 You are a psychological DETECTIVE - REVEAL hidden dynamics, don't label.

═══════════════════════════════════════════════════════════════════
YOUR TASK: 3-Step Framework
═══════════════════════════════════════════════════════════════════

1️⃣ DETECT CONTRADICTION (what they don't see)
   • Emotional oscillations (high→low in minutes)
   • "Want to start" + "but scared" = desire vs self-protection
   • "Colleagues slack" + "Maybe I'm problem?" = blame → self-doubt

2️⃣ UNCOVER HIDDEN DYNAMIC (WHY behavior exists)
   DON'T: "He procrastinates"  
   DO: "Procrastination protects from disappointment"
   
   Framework: Surface → Hidden fear → Core need
   Example: "Perfectionism is ARMOR hiding fear of being seen"

3️⃣ IDENTIFY BLOCKED RESOURCE (distorted strength)
   • Perfectionism → High standards (power!) misdirected AGAINST self
   • Procrastination → Caution (wisdom!) but blocks all action
   → How to REDIRECT this resource?

🎯 RESPONSE HINT (MANDATORY)
   • Synthesize contradiction + hidden dynamic + blocked resource
   • Must be written in RUSSIAN, Soul Near — тёплый, точный, честный тон
   • 1-2 предложения (до 45 слов) и обязательно заканчивай открытым вопросом
   • Этот текст сразу отправится пользователю, не используй списки или обращения «дорогой/дорогая»

═══════════════════════════════════════════════════════════════════
🚨 CRITICAL PATTERNS (detect first!)
═══════════════════════════════════════════════════════════════════

**Burnout** (2+ symptoms): 10+hrs work, memory issues, "like robot"
**Depression** (3+ symptoms): hopelessness, anhedonia, "no point"  
→ Set frequency>=5, confidence>=0.8

═══════════════════════════════════════════════════════════════════
📋 RULES
═══════════════════════════════════════════════════════════════════

• Название паттерна — живой русский термин (без латиницы и кальки).
• Все поля (description, contradiction, hidden_dynamic, blocked_resource, response_hint) формулируй на русском языке.
• Каждый блок держи в 1–2 коротких предложениях (до 180 символов), заканчивай точкой или вопросом, без многоточий.
• Используй узнаваемые психологические понятия, но переводи их на русский («Синдром самозванца», «Перфекционизм», «Финансовая тревога»).
• Evidence: оставь 2–3 точные цитаты пользователя (без сокращений и выдумок).
• Primary context: выбери тему, где паттерн проявляется сильнее всего (relationships|money|work|purpose|confidence|fears|self).
• Context weights: оцени релевантность тем (0.0–1.0) и верни словарь {"relationships": 1.0, "money": 0.4, ...}.
• Если паттерн повторяется — создай новую запись, чтобы отслеживать частоту.

═══════════════════════════════════════════════════════════════════
📊 CONVERSATION TO ANALYZE
═══════════════════════════════════════════════════════════════════

MESSAGES (last 10):
{conversation_text}

EXISTING PATTERNS (DON'T create variations):
{existing_patterns_str}

═══════════════════════════════════════════════════════════════════
📤 RETURN FORMAT (JSON)
═══════════════════════════════════════════════════════════════════

{{
  "new_patterns": [
    {{
      "type": "behavioral|emotional|cognitive",
      "title": "Русское название паттерна",

      "description": "Короткое описание проявления (на русском)",

      "contradiction": "Где конфликт? 'Говорит X, делает Y, потому что...'",

      "hidden_dynamic": "Что движет? 'Истинный страх... Поведение служит...'",

      "blocked_resource": "Какая сила спрятана? 'Это показывает [качество], но направлено против себя. Как перенаправить?'",

      "evidence": ["точная цитата 1", "точная цитата 2"],
      "tags": ["основной термин", "авто"],
      "primary_context": "relationships",
      "context_weights": {
        "relationships": 1.0,
        "money": 0.4,
        "work": 0.3,
        "purpose": 0.2,
        "confidence": 0.6,
        "fears": 0.8,
        "self": 0.5
      },
      "frequency": "high|medium|low",
      "confidence": 0.7-1.0,
      "response_hint": "Зеркало в стиле Soul Near на русском (1–2 предложения)."
    }}
  ],
  "mood": {{
    "current_mood": "slightly_down|neutral|good|energetic|stressed",
    "stress_level": "low|medium|high|critical",
    "energy_level": "low|medium|high",
    "triggers": ["ключевые фразы из диалога"]
  }}
}}

═══════════════════════════════════════════════════════════════════
✅ PRE-FLIGHT CHECKLIST
═══════════════════════════════════════════════════════════════════

Перед отправкой JSON проверь:
1. ✓ Title — понятное русское название паттерна.
2. ✓ Contradiction заполнено и показывает конфликт между словами и действиями.
3. ✓ Hidden_dynamic объясняет, что двигает поведением (а не повторяет описание).
4. ✓ Blocked_resource подсвечивает силу/ресурс, а не ещё одну проблему.
5. ✓ Evidence содержит точные цитаты пользователя.
6. ✓ Каждый текстовый блок ≤ 180 символов и заканчивается завершённым предложением.
7. ✓ Повторяющийся паттерн добавлен заново для учёта частоты.

═══════════════════════════════════════════════════════════════════
🎯 REMEMBER YOUR MISSION
═══════════════════════════════════════════════════════════════════

Ты не штампуешь ярлыки — ты подсвечиваешь правду.

Не повторяй очевидное («ты тревожишься»).
Покажи то, что человек не видит («твой перфекционизм прячет тебя от мира»).

ГЛУБИНА > КЛАССИФИКАЦИЯ
ИНСАЙТ > ДИАГНОЗ  
ОТКРЫТИЕ > ОПИСАНИЕ

Теперь анализируй.
"""


def get_deep_analysis_prompt(conversation_text: str, patterns_summary: str) -> str:
    """
    Промпт для deep_analysis V2 - ИНСАЙТЫ ВМЕСТО КЛАССИФИКАЦИИ (каждые 20 сообщений)
    
    ФИЛОСОФИЯ: Соединяем паттерны → раскрываем СИСТЕМУ → даём откровение
    
    Args:
        conversation_text: Последние 30 сообщений
        patterns_summary: Форматированный список всех паттернов
        
    Returns:
        Полный промпт для GPT-4o
    """
    patterns_str = patterns_summary if patterns_summary else 'паттернов пока нет'
    
    return f"""
You are a psychological SYNTHESIZER. You see the BIG PICTURE.

MISSION: Connect patterns → reveal SYSTEM → deliver REVELATION

═══════════════════════════════════════════════════════════════════
📊 DATA FOR ANALYSIS
═══════════════════════════════════════════════════════════════════

CONVERSATION (last 30 messages):
{conversation_text}

DETECTED PATTERNS:
{patterns_str}

═══════════════════════════════════════════════════════════════════
🧠 YOUR TASK: SYNTHESIS (not summary!)
═══════════════════════════════════════════════════════════════════

STEP 1: FIND THE SYSTEM
─────────────────────────────────────────────────────────────────
Patterns don't exist in isolation. They form a SYSTEM.

QUESTIONS:
- How do patterns REINFORCE each other?
- What's the CYCLE? (Pattern A triggers Pattern B triggers Pattern A...)
- Where's the TRAP? (behavioral loop that keeps person stuck)

EXAMPLE:
Perfectionism → Fear of judgment → Isolation → More perfectionism
"He uses perfectionism to avoid vulnerability, but isolation makes 
him MORE afraid of being seen, so he perfects even harder. Closed loop."

STEP 2: IDENTIFY THE BLOCKAGE
─────────────────────────────────────────────────────────────────
Where is person STUCK? Not "what's wrong" but "what's BLOCKING growth"?

FRAMEWORK: Resource → Blockage → Freedom

EXAMPLE:
Resource: High standards + deep caring
Blockage: Directing it AGAINST self ("I'm not enough")
Freedom: What if directed FOR self? ("My standards show I care deeply")

STEP 3: CRAFT THE REVELATION
─────────────────────────────────────────────────────────────────
Insight = something person CAN'T see but will recognize instantly when told.

❌ BAD: "You have imposter syndrome and perfectionism"
✅ GOOD: "You're not afraid of failure. You're afraid success will prove 
         you're fraud. So you sabotage BEFORE the world can reject you."

STYLE:
- Direct, conversational (no clinical jargon for user!)
- Пиши все пользовательские текстовые поля на русском языке
- Каждый блок (title, the_system, the_blockage, the_way_out, why_this_matters) держи в 2 коротких предложениях максимум (≤ 220 символов), без многоточий на конце.
- "You do X because Y. Real fear is Z."
- Use THEIR WORDS from conversation
- Like honest friend who sees through bullshit

🔥 RESPONSE HINT (REQUIRED)
- Deliver 1-2 sentences (до 60 слов) in RUSSIAN the assistant can reuse immediately.
- Mirror the contradiction + name the hidden need + invite reflection (заканчивай вопросом или короткой паузой "...Что поймаешь, если остановишься?").
- Tone: Soul Near (тёплая точность без морали).

═══════════════════════════════════════════════════════════════════
📤 RETURN FORMAT (JSON)
═══════════════════════════════════════════════════════════════════

{{
  "insights": [
    {{
      "category": "behavioral_system|emotional_dynamic|core_blockage",
      
      "title": "One-sentence revelation (user-facing, not clinical)",
      
      "the_system": "How patterns interconnect. 'Pattern A leads to B which reinforces A. This creates closed loop where...'",
      
      "the_blockage": "What STOPS growth. 'Resource [X] is blocked by [fear/belief]. This prevents...'",
      
      "the_way_out": "Concrete, actionable shift (not generic advice). 'Instead of [current behavior], try [specific alternative] to redirect [resource] FOR yourself.'",
      
      "why_this_matters": "Personal impact. 'If you break this loop, you'll be able to... The cost of staying here is...'",
      
      "derived_from_pattern_titles": ["Pattern 1", "Pattern 2"],
      "priority": "high|medium|low",
      "requires_professional_help": true|false,
      "response_hint": "Short Soul Near style mirror for the next reply (2 sentences max)."
    }}
  ],
  "learning": {{
    "works_well": [
      "Specific communication styles that resonated (with examples from conversation)"
    ],
    "doesnt_work": [
      "Styles that triggered resistance (with examples)"
    ]
  }}
}}

═══════════════════════════════════════════════════════════════════
✅ QUALITY CHECKLIST
═══════════════════════════════════════════════════════════════════

Before returning, verify each insight:

1. ✓ REVELATION test: Would user think "Holy shit, that's it!"?
2. ✓ SPECIFICITY test: Uses quotes/details from THEIR conversation?
3. ✓ SYSTEM test: Shows how patterns interconnect (not just list)?
4. ✓ ACTION test: "Way out" is CONCRETE (not "set boundaries")?
5. ✓ NO JARGON test: Avoids clinical terms in user-facing text?
6. ✓ LENGTH test: Каждый текстовый блок ≤ 220 символов и завершён точкой или вопросом.

═══════════════════════════════════════════════════════════════════
🎯 EXAMPLES: GOOD vs BAD INSIGHTS
═══════════════════════════════════════════════════════════════════

❌ BAD INSIGHT:
Title: "Perfectionism and low self-esteem"
Description: "You have high standards but doubt yourself. 
              Recommend: practice self-compassion."

WHY BAD: Generic, tells what user knows, vague advice

✅ GOOD INSIGHT:
Title: "Perfectionism hides you from the world"
The_system: "You say 'I want to start project' but immediately 
            find reasons to delay ('not ready yet', 'need more time'). 
            Pattern: Desire → Fear → Perfectionism (armor) → No action.
            Loop continues because perfectionism WORKS - it protects 
            you from being seen and potentially rejected."
            
The_blockage: "Your high standards (resource) are aimed AGAINST you 
              ('I'm not good enough yet') instead of FOR you 
              ('I care deeply about my work'). This keeps you safe 
              but isolated."
              
The_way_out: "Publish ONE thing at 70% quality. Not to succeed, 
             but to practice being SEEN as imperfect. Notice: 
             world doesn't end. That's the crack in armor."
             
Why_this_matters: "Right now you're choosing safety over growth. 
                  Every 'not ready yet' is another day hiding. 
                  Cost: your potential never gets to exist outside 
                  your head."

═══════════════════════════════════════════════════════════════════
🔥 REMEMBER
═══════════════════════════════════════════════════════════════════

You're not writing a clinical report. You're having honest conversation 
with someone who's STUCK and needs to see their blind spot.

Be the friend who says "Dude, here's what I see..."

DEPTH > DESCRIPTION
REVELATION > DIAGNOSIS
TRUTH > TACT

Now synthesize.
"""


# Future: Add more prompts here as needed
# - prompt for semantic search
# - prompt for pattern consolidation
# - prompt for quiz generation

