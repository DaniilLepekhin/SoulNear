# Test Persona: Alex

**Name:** Alex  
**Age:** 32  
**Occupation:** Senior Software Engineer at mid-sized tech company  
**Location:** Remote work (originally from Moscow)  

## Target Patterns to Embed

1. **Burnout / Emotional Exhaustion**
   - Works 10-12 hours daily
   - Can't disconnect from work thoughts
   - Physical exhaustion, sleep issues
   
2. **Overthinking / Analysis Paralysis**
   - Spends too much time on decisions
   - Second-guesses choices
   - Gets stuck in "what if" loops

3. **Workaholism**
   - Defines self-worth by productivity
   - Guilt when not working
   - Difficulty taking breaks

4. **Self-Criticism / Harsh Inner Dialogue**
   - Harsh on mistakes
   - Compares to "better" engineers
   - Dismisses achievements

5. **Avoidance of Delegation**
   - "Faster to do it myself"
   - Doesn't trust others with tasks
   - Micromanagement tendencies

## Key Phrases to Use

**Burnout:**
- "Даже во сне думаю о баге, который не могу починить"
- "Чувствую себя выжатым как лимон"
- "Хочется просто лечь и ничего не делать неделю"

**Overthinking:**
- "Потратил 3 часа на выбор архитектуры, все еще не уверен"
- "А что если я выбрал не тот подход?"
- "Постоянно пересматриваю свои решения"

**Workaholism:**
- "Суббота, но решил поработать пару часов"
- "Отпуск через неделю, а я уже чувствую вину"
- "Продуктивность = самооценка"

**Self-Criticism:**
- "Опять накосячил, другой бы справился лучше"
- "Смотрю на код коллег - у них все элегантнее"
- "Похвалили на ревью, но я вижу только недостатки"

**Avoidance of Delegation:**
- "Быстрее самому сделать, чем объяснять джуниору"
- "Делегировал задачу, но все равно проверяю каждую строчку"
- "Не могу расслабиться, пока все не сделаю сам"

## Expected Bot Behavior

- Should detect 4-5 patterns after 30 messages
- Should provide contextual examples
- Should offer insights about connection between patterns (e.g., Overthinking + Self-Criticism → Burnout)
- Should match with existing patterns if similar (e.g., if "Perfectionism" was detected for Maria, it might merge with "Self-Criticism" for Alex)

## Success Criteria

1. ✅ 30 messages sent
2. ✅ Bot responds to all messages (waiting for "thinking" messages)
3. ✅ 4-5 patterns detected (80%+ of target patterns)
4. ✅ Patterns have correct frequency (new: 1-2, existing: increased)
5. ✅ `/my_profile` shows merged view (Maria patterns + Alex patterns)
6. ✅ Evidence/examples from Alex messages present
7. ✅ Insights generated

