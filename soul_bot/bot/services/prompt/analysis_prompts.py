"""
GPT Prompts для Pattern Analysis

Вынесены из pattern_analyzer.py для удобства модификации и тестирования.
"""

def get_quick_analysis_prompt(conversation_text: str, existing_summaries: list[str]) -> str:
    """
    Промпт для quick_analysis (каждые 3 сообщения)
    
    Args:
        conversation_text: Последние 10 сообщений formatted as "role: content"
        existing_summaries: Список существующих паттернов (titles only)
        
    Returns:
        Полный промпт для GPT-4o-mini
    """
    existing_patterns_str = "\n".join(existing_summaries) if existing_summaries else 'None yet'
    
    return f"""
Analyze this conversation and extract behavioral/emotional patterns.

⚠️ CRITICAL: Use ESTABLISHED CLINICAL/PSYCHOLOGICAL TERMINOLOGY, create BROAD patterns.

🌐 LANGUAGE RULE: ALL pattern titles MUST be in ENGLISH!
Examples: "Imposter Syndrome" (NOT "Синдром самозванца")
          "Perfectionism" (NOT "Перфекционизм")
          "Social Anxiety in Professional Settings" (NOT "Социальная тревога")
This ensures consistent embedding similarity and proper merging!

🎯 EXPECTED PATTERNS (these are SEPARATE, don't merge them):
1. "Imposter Syndrome" - feeling inadequate, fraud, "not good enough", fear of being exposed
2. "Perfectionism" - code must be perfect, rewriting 10 times, fear of mistakes, paralysis
3. "Social Anxiety in Professional Settings" - fear asking questions, avoiding meetings/calls
4. "Negative Self-Talk" - persistent internal critical voice
5. "Fear of Failure" - avoiding tasks due to anticipated negative outcomes
6. "Procrastination Through Over-Analysis" - paralysis by analysis, overthinking

⚠️ NOTE: Perfectionism ≠ Imposter Syndrome (they often co-occur but are DISTINCT patterns!)

🚨 CRITICAL PATTERNS CHECKLIST (MUST CHECK THESE FIRST):
These are high-priority patterns that MUST be detected if symptoms present:

1. **Burnout** (Professional Burnout):
   SYMPTOMS (if 2+ present → CREATE this pattern):
   - Working 10+ hours/day consistently
   - Cognitive dysfunction (forgetting meetings, tasks, important things)
   - Inability to concentrate/focus ("can't think", "can't concentrate")
   - Physical/emotional exhaustion ("no energy", "exhausted", "worn out")
   - Anhedonia ("don't remember when I was happy")
   - Sense of futility ("why bother", "pointless", "like a robot")
   
   If you see 2+ symptoms → CREATE pattern "Burnout" with frequency >= 5 and confidence >= 0.8
   This is CRITICAL for user safety!

2. **Acute Depression**:
   SYMPTOMS (if 3+ present → CREATE this pattern):
   - Hopelessness ("no point", "why try", "nothing matters")
   - Anhedonia ("don't remember when happy", "no pleasure")
   - Worthlessness ("loser", "failure", "everything wrong")
   - Fatigue persistent ("no energy", "exhausted always")
   - Suicidal ideation (IMMEDIATE flag if present)
   
   If you see 3+ symptoms → CREATE pattern "Acute Depression" with frequency >= 6 and confidence >= 0.8
   Suggest professional help in recommendations!

⚠️ These critical patterns take PRIORITY over other patterns. Check them FIRST before analyzing others.

✅ GOOD pattern titles (use THESE exact terms when applicable):
"Burnout" - professional burnout, working excessive hours, cognitive dysfunction
"Acute Depression" - severe depressive symptoms requiring professional attention
"Imposter Syndrome" - feeling inadequate despite evidence of competence
"Perfectionism" - setting unrealistically high standards, fear of mistakes  
"Social Anxiety in Professional Settings" - fear of judgment/criticism at work
"Negative Self-Talk" - persistent internal critical voice
"Procrastination Through Over-Analysis" - paralysis by analysis, overthinking
"Fear of Failure" - avoiding tasks due to anticipated negative outcomes
"Catastrophic Thinking" - expecting worst-case scenarios

❌ BAD examples (what NOT to do - from real test data):
"Негативное восприятие себя" → should be "Imposter Syndrome"
"Саморазрушительные мысли" → should be "Negative Self-Talk" 
"Социальное сравнение" → should be "Imposter Syndrome"
"Страх осуждения" → should be "Social Anxiety in Professional Settings"
"Seeking external validation" → part of "Imposter Syndrome"
"Difficulty with self-acceptance" → part of "Imposter Syndrome"

🎯 MERGING RULE (CRITICAL - FIXED LOGIC):
If you see evidence of an EXISTING pattern in current conversation → CREATE IT AGAIN with NEW evidence!
This is how we track frequency. The embeddings will auto-merge and increase occurrences.

Example: User says "I'm not good enough" again in messages 10-15
→ CREATE pattern "Imposter Syndrome" again with this NEW quote as evidence
→ System will merge it with existing pattern and increase occurrences: 1 → 2
→ This happens every time pattern appears → occurrences grows!

⚠️ DO create same pattern multiple times if it repeats in conversation
⚠️ DON'T create variations (Self-doubt, Low self-worth) - use established term
⚠️ WHEN IN DOUBT: Choose BROADER term, but DO return it if you see it again!

CONVERSATION (last 10 messages):
{conversation_text}

EXISTING PATTERNS (DO NOT create variations of these):
{existing_patterns_str}

Tasks:
1. Find 1-2 BROAD patterns in current conversation (CREATE again if it repeats!)
2. Use ENGLISH titles with established psychology/DSM terminology
3. Detect current mood and energy level
4. If theme repeats → CREATE pattern AGAIN with new evidence (for occurrences tracking!)

Return JSON:
{{
  "new_patterns": [
    {{
      "type": "behavioral|emotional|cognitive",
      "title": "Clinical Term (3-5 words, use established terminology)",
      "description": "Detailed psychological explanation with theory reference",
      "evidence": ["exact quote 1", "exact quote 2"],
      "tags": ["DSM-related", "clinical-psychology"],
      "frequency": "high|medium|low",
      "confidence": 0.7-1.0
    }}
  ],
  "mood": {{
    "current_mood": "slightly_down|neutral|good|energetic|stressed",
    "stress_level": "low|medium|high",
    "energy_level": "low|medium|high",
    "triggers": ["trigger1", "trigger2"]
  }}
}}

🚨 FINAL CHECK before returning:
- Is this title an ESTABLISHED psychological term? (Google it if unsure)
- Does it match an EXISTING pattern? (If yes → CREATE IT AGAIN with new evidence for tracking!)
- Would a clinical psychologist recognize this term? (If no → rephrase)

⚠️ REMEMBER: Re-creating existing patterns is GOOD - it tracks frequency!
"""


def get_deep_analysis_prompt(conversation_text: str, patterns_summary: str) -> str:
    """
    Промпт для deep_analysis (каждые 20 сообщений)
    
    Args:
        conversation_text: Последние 30 сообщений
        patterns_summary: Форматированный список всех паттернов
        
    Returns:
        Полный промпт для GPT-4o
    """
    patterns_str = patterns_summary if patterns_summary else 'No patterns yet'
    
    return f"""
Deep analysis of user's behavioral patterns and conversation history.

CONVERSATION (last 30 messages):
{conversation_text}

IDENTIFIED PATTERNS:
{patterns_str}

Tasks:
1. Generate 1-2 HIGH-LEVEL INSIGHTS from patterns
2. Provide actionable RECOMMENDATIONS
3. Identify what communication style WORKS WELL vs DOESN'T WORK

Return JSON:
{{
  "insights": [
    {{
      "category": "personality|behavior|emotional",
      "title": "Insight title",
      "description": "Detailed description connecting multiple patterns",
      "impact": "negative|neutral|positive",
      "recommendations": ["action1", "action2"],
      "derived_from_pattern_titles": ["pattern title 1", "pattern title 2"],
      "priority": "high|medium|low"
    }}
  ],
  "learning": {{
    "works_well": ["what works for this user"],
    "doesnt_work": ["what doesn't work"]
  }}
}}
"""


# Future: Add more prompts here as needed
# - prompt for semantic search
# - prompt for pattern consolidation
# - prompt for quiz generation

