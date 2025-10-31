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
    existing_patterns_str = "\n".join(existing_summaries) if existing_summaries else 'None yet'
    
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

═══════════════════════════════════════════════════════════════════
🚨 CRITICAL PATTERNS (detect first!)
═══════════════════════════════════════════════════════════════════

**Burnout** (2+ symptoms): 10+hrs work, memory issues, "like robot"
**Depression** (3+ symptoms): hopelessness, anhedonia, "no point"  
→ Set frequency>=5, confidence>=0.8

═══════════════════════════════════════════════════════════════════
📋 RULES
═══════════════════════════════════════════════════════════════════

• ALL titles in ENGLISH: "Imposter Syndrome" not "Синдром самозванца"
• Use ESTABLISHED terms (Burnout, Perfectionism, Social Anxiety)
• Evidence: 2-3 direct quotes max
• If pattern repeats → CREATE AGAIN (tracks frequency)

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
      "title": "Established Clinical Term (English)",
      
      "description": "Clinical description of surface behavior",
      
      "contradiction": "What contradiction exists? 'Says X but does Y because...'",
      
      "hidden_dynamic": "What DRIVES this? 'Real fear is... Dynamic: behavior serves to...'",
      
      "blocked_resource": "Hidden strength. 'This shows [quality], but directed against self instead of for self. Could redirect by...'",
      
      "evidence": ["exact quote 1", "exact quote 2"],
      "tags": ["clinical-term", "auto-detected"],
      "frequency": "high|medium|low",
      "confidence": 0.7-1.0
    }}
  ],
  "mood": {{
    "current_mood": "slightly_down|neutral|good|energetic|stressed",
    "stress_level": "low|medium|high|critical",
    "energy_level": "low|medium|high",
    "triggers": ["specific trigger phrases from conversation"]
  }}
}}

═══════════════════════════════════════════════════════════════════
✅ PRE-FLIGHT CHECKLIST
═══════════════════════════════════════════════════════════════════

Before returning JSON, verify:
1. ✓ Title = established psychological term (clinician would recognize)
2. ✓ Contradiction field filled (what person doesn't see)
3. ✓ Hidden_dynamic explains WHAT DRIVES behavior (not just describes it)
4. ✓ Blocked_resource shows STRENGTH not just problem
5. ✓ Evidence = EXACT quotes from user messages
6. ✓ If pattern repeats → created AGAIN for frequency tracking

═══════════════════════════════════════════════════════════════════
🎯 REMEMBER YOUR MISSION
═══════════════════════════════════════════════════════════════════

You are NOT a label-maker. You are a TRUTH-REVEALER.

Don't tell them what they already know ("you're anxious").
Show them what they CAN'T see ("your perfectionism is hiding you from the world").

DEPTH > CLASSIFICATION
INSIGHT > DIAGNOSIS  
REVELATION > DESCRIPTION

Now analyze.
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
    patterns_str = patterns_summary if patterns_summary else 'No patterns yet'
    
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
- "You do X because Y. Real fear is Z."
- Use THEIR WORDS from conversation
- Like honest friend who sees through bullshit

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
      "requires_professional_help": true|false
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

