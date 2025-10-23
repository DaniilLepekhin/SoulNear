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
  | 'chatHistory';

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

export interface ChatHistory {
  id: string;
  date: string;
  preview: string;
  messages: Message[];
}

export interface Track {
  media_id: string;
  name: string;
  duration?: string;
  url?: string;
  category?: string;
}
