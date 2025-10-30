# 🔥 Quiz Upgrade V2: Optimized Adaptive System

## 📊 Changes Summary

### 1. **Base Questions: 10 → 8**
```python
# generator.py:62
count: int = 8  # Was 10
```

**Rationale:** Shorter base quiz = faster completion, less fatigue

---

### 2. **Adaptive Questions: Generate 5, Select Top 2-3**
```python
# adaptive_quiz_service.py:35-37
GENERATE_CANDIDATE_QUESTIONS = 5  # Generate 5 candidates
SELECT_TOP_QUESTIONS = 3          # Select top 2-3
MAX_TOTAL_FOLLOWUPS = 3           # Was 5
```

**Logic Flow:**
1. GPT generates 5 candidate questions
2. Each question gets `quality_score` (0.0-1.0) + `reasoning`
3. Sort by `quality_score` (descending)
4. Select top 3 questions
5. Remove metadata (`quality_score`, `reasoning`) before returning

**Code (lines 195-221):**
```python
# Sort by quality_score (descending)
sorted_questions = sorted(
    all_questions,
    key=lambda q: q.get('quality_score', 0.5),
    reverse=True
)

# Select top questions (2-3)
top_count = min(self.SELECT_TOP_QUESTIONS, len(sorted_questions))
questions = sorted_questions[:top_count]

logger.info(
    f"Selected top {len(questions)}/{len(all_questions)} questions "
    f"(scores: {[q.get('quality_score', 0) for q in questions]})"
)
```

---

### 3. **Focus on Single Strongest Pattern**
```python
# adaptive_quiz_service.py:261-267
# 🔥 UPGRADE: Focus on strongest pattern only
if strong_patterns:
    top_pattern = strong_patterns[0]
    logger.info(f"Focusing on strongest pattern: {top_pattern.get('title')} (confidence: {top_pattern.get('confidence')})")
    
    followups = await self.generate_followup_questions(top_pattern, session)
    all_followups.extend(followups)
```

**Rationale:** Instead of 2 patterns × 2-3 questions = bloat, focus deeply on 1 pattern

---

## 🎯 Expected Quiz Flow

### **Scenario 1: No Strong Patterns**
```
Base: 8 questions
Adaptive: 0 (no patterns detected)
Total: 8 questions
```

### **Scenario 2: Strong Pattern Detected**
```
Base: 8 questions
Adaptive: 2-3 (from strongest pattern)
Total: 10-11 questions
```

### **Max Limit**
```
Base: 8
Adaptive: 3 (MAX_TOTAL_FOLLOWUPS)
Total: 11 questions (< 15 ✅)
```

---

## ✅ Validation Checklist

- [x] Base questions reduced to 8
- [x] Adaptive generates 5 candidates
- [x] GPT ranks questions by quality_score
- [x] Top 2-3 questions selected
- [x] Focus on single strongest pattern
- [x] Max 3 adaptive questions enforced
- [x] Total < 15 questions guaranteed
- [x] Logging updated for debugging

---

## 🧪 Test Plan

1. **Start fresh quiz** → Should show "Вопрос 1/8"
2. **Complete 5 questions** → Trigger adaptive analysis
3. **If pattern detected** → "Добавляю 2-3 вопроса" + log shows quality scores
4. **Total questions** → 8-11 (never > 15)
5. **Complete quiz** → Verify confidence scores (⭐⭐⭐) in results

---

## 📝 Logs to Watch

```
Generated 5 candidate questions for {pattern}
Selected top 3/5 questions (scores: [0.95, 0.85, 0.80])
Focusing on strongest pattern: {pattern} (confidence: 0.85)
Generated 3 total follow-up questions
```

