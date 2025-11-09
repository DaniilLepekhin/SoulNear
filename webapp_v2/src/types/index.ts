export type Screen =
  | 'splash'
  | 'onboarding'
  | 'main'
  | 'chat'
  | 'voiceChat'
  | 'generalVoice'
  | 'analysisVoice'
  | 'dreams'
  | 'dreamsChat'
  | 'dreamsVoice'
  | 'practices'
  | 'practicePlayer'
  | 'analysis'
  | 'analysisChat'
  | 'profile'
  | 'chatHistory'
  | 'patterns'    // 🆕 AI Patterns
  | 'insights'    // 🆕 AI Insights
  | 'quiz';       // 🆕 Adaptive Quizzes

export interface User {
  id: number;
  firstName: string;
  lastName?: string;
  username?: string;
  photoUrl?: string;
  languageCode?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
  reaction?: 'like' | 'dislike';
}

export interface Practice {
  id: number;
  title: string;
  description: string;
  duration: string;
  category: string;
  audioUrl?: string;
  imageUrl?: string;
  isPremium: boolean;
}

export interface CalendarDay {
  day: number;
  mood: 'happy' | 'neutral' | 'sad' | null;
  isCompleted: boolean;
  isActive: boolean;
}

export type Mood = 'happy' | 'neutral' | 'sad';
export type AnalysisTopic = 'relationships' | 'money' | 'confidence' | 'fears';

export interface AnalysisConfig {
  title: string;
  prompt: string;
  color: string;
}

export type AssistantType = 'helper' | 'relationships' | 'money' | 'confidence' | 'fears' | 'dreams';

export interface ChatThread {
  id: string;
  assistant_type: AssistantType;
  thread_id: string; // OpenAI thread ID
  created_at: Date;
  updated_at: Date;
  preview: string; // First user message or generated preview
}

export interface ChatHistory {
  id: string;
  date: string;
  preview: string;
  messages: Message[];
  assistant_type: AssistantType;
}

export interface Track {
  media_id: string;
  name: string;
  duration?: string;
  url?: string;
  category?: string;
  mediaType?: 'audio' | 'video';  // 🎬 Distinguish between audio and video content
}

// ==========================================
// 🧠 AI PATTERNS & INSIGHTS (NEW - from soul_bot)
// ==========================================

export interface Pattern {
  id: string;
  type: 'behavioral' | 'emotional' | 'cognitive';
  title: string;
  description: string;
  contradiction?: string;        // V2: внутреннее противоречие
  hidden_dynamic?: string;        // V2: скрытая динамика
  blocked_resource?: string;      // V2: заблокированный ресурс
  evidence: string[];             // Цитаты из сообщений
  tags?: string[];
  primary_context?: string;       // Основная тема (relationships/money/work)
  context_weights?: { [key: string]: number }; // Связь с темами
  frequency: 'high' | 'medium' | 'low';
  confidence: number;             // 0.0 - 1.0
  response_hint?: string;         // Что упомянуть в следующем ответе
  occurrences: number;            // Сколько раз встречался
  first_detected: string;         // ISO timestamp
  last_detected: string;          // ISO timestamp
  related_patterns?: string[];    // IDs связанных паттернов
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  category?: string;
  priority: 'high' | 'medium' | 'low';
  derived_from: string[];         // Pattern IDs
  recommendations?: string[];
  response_hint?: string;
  created_at: string;
  last_updated: string;
}

export interface EmotionalState {
  current_mood: string;
  stress_level: 'critical' | 'high' | 'medium' | 'low';
  energy_level: 'high' | 'medium' | 'low';
  triggers?: string[];
  mood_history?: { date: string; mood: string; triggers?: string[] }[];
  auto_corrections?: { field: string; old_value: string; new_value: string; reason: string }[];
}

export interface UserProfile {
  user_id: number;
  patterns: {
    patterns: Pattern[];
    last_updated?: string;
  };
  insights: {
    insights: Insight[];
    last_updated?: string;
  };
  emotional_state: EmotionalState;
  learning_preferences?: {
    works_well: string[];
    doesnt_work: string[];
  };
  tone_style?: 'formal' | 'friendly' | 'sarcastic' | 'motivating';
  personality?: 'mentor' | 'friend' | 'coach' | 'therapist';
  message_length?: 'ultra_brief' | 'brief' | 'medium' | 'detailed';
  custom_instructions?: string;
}

// ==========================================
// 🎯 ADAPTIVE QUIZZES (NEW)
// ==========================================

export interface QuizQuestion {
  id: string;
  text: string;
  type: 'text' | 'scale' | 'multiple_choice';
  category: 'relationships' | 'money' | 'purpose' | 'fears';
  options?: string[];
  preface?: string;
}

export interface QuizAnswer {
  question_id: string;
  question_text: string;
  question_type: string;
  answer_value: string;
  timestamp: string;
}

export interface QuizSession {
  session_id: string;
  user_id: number;
  category: string;
  status: 'active' | 'completed' | 'abandoned';
  current_question_index: number;
  questions: QuizQuestion[];
  answers: QuizAnswer[];
  analysis_result?: string;
  created_at: string;
  updated_at: string;
}
