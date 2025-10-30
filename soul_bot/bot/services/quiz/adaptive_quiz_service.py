"""
Adaptive Quiz Service - Pattern-Based Adaptation

Analyzes user answers mid-quiz to detect emerging patterns
and generates follow-up questions for deeper exploration.

Strategy:
1. Quick analysis after question 5 (midpoint)
2. If strong patterns detected (confidence > 0.7) → generate 2-3 follow-ups
3. Continue with remaining base questions
4. Final comprehensive analysis at quiz completion

Author: AI Agent
Created: 2025-10-30
"""

import logging
from typing import Optional

from bot.services.ai.gpt_service import GPTService
from database.models.quiz_session import QuizSession


logger = logging.getLogger(__name__)


class AdaptiveQuizService:
    """
    Handles adaptive quiz logic: pattern detection and follow-up question generation.
    """
    
    # Thresholds for adaptive behavior
    BRANCH_AFTER_QUESTION = 5  # Trigger analysis after Q5
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to generate follow-ups
    MAX_FOLLOWUP_QUESTIONS = 3  # Maximum additional questions per pattern
    MAX_TOTAL_FOLLOWUPS = 5  # Maximum total follow-ups across all patterns
    
    def __init__(self, gpt_service: GPTService):
        self.gpt = gpt_service
    
    async def should_branch(self, session: QuizSession) -> bool:
        """
        Determine if we should add follow-up questions based on current progress.
        
        Args:
            session: Current quiz session
            
        Returns:
            True if adaptive branching should occur
        """
        # Only branch once at midpoint
        if session.current_question_index != self.BRANCH_AFTER_QUESTION:
            return False
        
        # Don't branch if we already have follow-ups
        if len(session.questions) > session.total_questions:
            logger.info("Already branched, skipping")
            return False
        
        # Need at least 3 answers to analyze
        if len(session.answers) < 3:
            logger.warning("Not enough answers for branching")
            return False
        
        return True
    
    async def analyze_patterns(self, session: QuizSession) -> list[dict]:
        """
        Quick pattern analysis of answers so far.
        
        Args:
            session: Quiz session with answers
            
        Returns:
            List of detected patterns with confidence scores
        """
        # Prepare context from answers
        answers_text = self._format_answers_for_analysis(session)
        
        prompt = f"""Analyze these quiz answers and identify psychological patterns.

Category: {session.category}
Answers so far:
{answers_text}

Task:
1. Identify 1-3 psychological patterns
2. Rate confidence (0.0-1.0) for each pattern
3. Provide brief evidence

Return JSON:
[
  {{
    "title": "Pattern name (English)",
    "title_ru": "Название паттерна (Russian)",
    "confidence": 0.85,
    "evidence": ["Quote from answer 1", "Quote from answer 2"],
    "description": "Brief explanation"
  }}
]

Focus on patterns with strong evidence only."""

        try:
            response = await self.gpt.generate_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                temperature=0.3,
                json_mode=True
            )
            
            patterns = self._parse_patterns_response(response)
            logger.info(f"Quick analysis found {len(patterns)} patterns")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return []
    
    async def generate_followup_questions(
        self,
        pattern: dict,
        session: QuizSession
    ) -> list[dict]:
        """
        Generate follow-up questions to explore a detected pattern deeper.
        
        Args:
            pattern: Detected pattern dict
            session: Quiz session context
            
        Returns:
            List of follow-up questions in standard format
        """
        category = session.category
        pattern_title = pattern.get('title_ru', pattern.get('title'))
        evidence = pattern.get('evidence', [])
        
        prompt = f"""Generate follow-up questions for a detected psychological pattern.

Pattern: {pattern_title}
Evidence from user: {', '.join(evidence[:2])}
Quiz category: {category}

Task:
Generate {self.MAX_FOLLOWUP_QUESTIONS} questions to:
1. Confirm this pattern exists
2. Understand its severity/frequency
3. Explore triggers or contexts

Requirements:
- Questions in Russian, casual tone
- Mix of scales (1-5) and choice questions
- Relevant to pattern and category
- Not repetitive

Return JSON array:
[
  {{
    "type": "scale",
    "text": "Как часто это проявляется?",
    "scale_labels": {{"min": "Редко", "max": "Постоянно"}},
    "related_pattern": "{pattern_title}"
  }},
  {{
    "type": "choice",
    "text": "В каких ситуациях это усиливается?",
    "options": ["На работе", "В отношениях", "В одиночестве", "Другое"],
    "related_pattern": "{pattern_title}"
  }}
]"""

        try:
            response = await self.gpt.generate_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                temperature=0.5,
                json_mode=True
            )
            
            questions = self._parse_questions_response(response)
            logger.info(f"Generated {len(questions)} follow-up questions for {pattern_title}")
            
            # Mark as adaptive questions
            for q in questions:
                q['is_adaptive'] = True
                q['trigger_pattern'] = pattern_title
            
            return questions
            
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return []
    
    async def get_adaptive_questions(self, session: QuizSession) -> list[dict]:
        """
        Main method: analyze patterns and generate all follow-up questions.
        
        Args:
            session: Current quiz session
            
        Returns:
            List of adaptive follow-up questions to insert
        """
        # Analyze patterns
        patterns = await self.analyze_patterns(session)
        
        if not patterns:
            logger.info("No patterns detected for adaptive branching")
            return []
        
        # Filter patterns by confidence
        strong_patterns = [
            p for p in patterns
            if p.get('confidence', 0) >= self.CONFIDENCE_THRESHOLD
        ]
        
        if not strong_patterns:
            logger.info("No high-confidence patterns for branching")
            return []
        
        logger.info(f"Found {len(strong_patterns)} strong patterns")
        
        # Generate follow-ups for top patterns (limit to avoid quiz bloat)
        all_followups = []
        
        for pattern in strong_patterns[:2]:  # Max 2 patterns
            followups = await self.generate_followup_questions(pattern, session)
            all_followups.extend(followups)
            
            # Stop if we have enough
            if len(all_followups) >= self.MAX_TOTAL_FOLLOWUPS:
                break
        
        # Limit total follow-ups
        all_followups = all_followups[:self.MAX_TOTAL_FOLLOWUPS]
        
        logger.info(f"Generated {len(all_followups)} total follow-up questions")
        
        return all_followups
    
    def _format_answers_for_analysis(self, session: QuizSession) -> str:
        """Format answers into readable text for GPT analysis."""
        lines = []
        
        for i, (question, answer) in enumerate(zip(session.questions, session.answers), 1):
            q_text = question.get('text', '')
            a_value = answer.get('value', '')
            
            # For scale questions, include the actual value
            if question.get('type') == 'scale':
                scale_min = question.get('scale_labels', {}).get('min', '')
                scale_max = question.get('scale_labels', {}).get('max', '')
                lines.append(f"Q{i}: {q_text}\nA{i}: {a_value}/5 ({scale_min}...{scale_max})")
            
            # For choice questions
            elif question.get('type') == 'choice':
                lines.append(f"Q{i}: {q_text}\nA{i}: {a_value}")
            
            # For text questions
            else:
                lines.append(f"Q{i}: {q_text}\nA{i}: {a_value}")
        
        return "\n\n".join(lines)
    
    def _parse_patterns_response(self, response: str) -> list[dict]:
        """Parse GPT response into pattern objects."""
        import json
        
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            # Handle both formats: direct list or {"patterns": [...]}
            if isinstance(data, dict) and 'patterns' in data:
                patterns = data['patterns']
            elif isinstance(data, list):
                patterns = data
            else:
                logger.warning("Response is not a list or dict with 'patterns', wrapping")
                patterns = [data]
            
            # Validate structure
            valid_patterns = []
            for p in patterns:
                if isinstance(p, dict) and 'title' in p and 'confidence' in p:
                    valid_patterns.append(p)
                else:
                    logger.warning(f"Invalid pattern structure: {p}")
            
            return valid_patterns
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
    
    def _parse_questions_response(self, response: str) -> list[dict]:
        """Parse GPT response into question objects."""
        import json
        
        try:
            questions = json.loads(response)
            
            if not isinstance(questions, list):
                logger.warning("Response is not a list, wrapping")
                questions = [questions]
            
            # Validate structure
            valid_questions = []
            for q in questions:
                if isinstance(q, dict) and 'type' in q and 'text' in q:
                    valid_questions.append(q)
                else:
                    logger.warning(f"Invalid question structure: {q}")
            
            return valid_questions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []

