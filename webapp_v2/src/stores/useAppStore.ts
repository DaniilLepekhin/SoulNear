// ==========================================
// Main App Store (Zustand)
// ==========================================

import { create } from 'zustand';
import type { Screen, User, Message, CalendarDay, Mood, AnalysisTopic, Track } from '../types';

interface AppState {
  // Navigation
  currentScreen: Screen;
  previousScreen: Screen | null;

  // User
  user: User | null;

  // Chat
  chatMessages: Message[];
  currentThreadId: string;

  // Calendar
  calendarDays: CalendarDay[];

  // Selected mood
  selectedMood: Mood | null;

  // Recording state
  isRecording: boolean;

  // Analysis
  currentAnalysisTopic: AnalysisTopic | null;
  analysisMessages: Message[];

  // Dreams
  dreamMessages: Message[];

  // Loading state
  isLoading: boolean;

  // Audio Player
  activeTrack: Track | null;
  isPlaying: boolean;
  duration: number;
  currentTime: number;
  showPlayer: boolean;
  sleepTimer: number | null; // Minutes until auto-stop (null = disabled)
  sleepTimerStartTime: number | null; // Timestamp when timer was set

  // Actions
  setScreen: (screen: Screen) => void;
  goBack: () => void;
  setUser: (user: User) => void;
  addChatMessage: (message: Message) => void;
  updateChatMessage: (id: string, updates: Partial<Message>) => void;
  clearChatMessages: () => void;
  setCurrentThreadId: (threadId: string) => void;
  setSelectedMood: (mood: Mood | null) => void;
  setIsRecording: (isRecording: boolean) => void;
  setCurrentAnalysisTopic: (topic: AnalysisTopic | null) => void;
  addAnalysisMessage: (message: Message) => void;
  clearAnalysisMessages: () => void;
  addDreamMessage: (message: Message) => void;
  clearDreamMessages: () => void;
  setIsLoading: (isLoading: boolean) => void;
  updateCalendarDay: (day: number, mood: Mood) => void;
  setActiveTrack: (track: Track | null) => void;
  setIsPlaying: (isPlaying: boolean) => void;
  setDuration: (duration: number) => void;
  setCurrentTime: (time: number) => void;
  setShowPlayer: (show: boolean) => void;
  setSleepTimer: (minutes: number | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  currentScreen: 'splash',
  previousScreen: null,
  user: null,
  chatMessages: [],
  currentThreadId: 'main',
  calendarDays: [
    { day: 4, mood: 'happy', isCompleted: true, isActive: false },
    { day: 5, mood: 'neutral', isCompleted: true, isActive: false },
    { day: 6, mood: null, isCompleted: false, isActive: true },
    { day: 7, mood: null, isCompleted: false, isActive: false },
    { day: 8, mood: null, isCompleted: false, isActive: false },
    { day: 9, mood: null, isCompleted: false, isActive: false },
  ],
  selectedMood: null,
  isRecording: false,
  currentAnalysisTopic: null,
  analysisMessages: [],
  dreamMessages: [],
  isLoading: false,
  activeTrack: null,
  isPlaying: false,
  duration: 0,
  currentTime: 0,
  showPlayer: false,
  sleepTimer: null,
  sleepTimerStartTime: null,

  // Actions
  setScreen: (screen) =>
    set((state) => ({
      previousScreen: state.currentScreen,
      currentScreen: screen,
    })),

  goBack: () =>
    set((state) => ({
      currentScreen: state.previousScreen || 'main',
      previousScreen: null,
    })),

  setUser: (user) => set({ user }),

  addChatMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message],
    })),

  updateChatMessage: (id, updates) =>
    set((state) => ({
      chatMessages: state.chatMessages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  clearChatMessages: () => set({ chatMessages: [] }),

  setCurrentThreadId: (threadId) => set({ currentThreadId: threadId }),

  setSelectedMood: (mood) => set({ selectedMood: mood }),

  setIsRecording: (isRecording) => set({ isRecording }),

  setCurrentAnalysisTopic: (topic) => set({ currentAnalysisTopic: topic }),

  addAnalysisMessage: (message) =>
    set((state) => ({
      analysisMessages: [...state.analysisMessages, message],
    })),

  clearAnalysisMessages: () => set({ analysisMessages: [] }),

  addDreamMessage: (message) =>
    set((state) => ({
      dreamMessages: [...state.dreamMessages, message],
    })),

  clearDreamMessages: () => set({ dreamMessages: [] }),

  setIsLoading: (isLoading) => set({ isLoading }),

  updateCalendarDay: (day, mood) =>
    set((state) => ({
      calendarDays: state.calendarDays.map((d) =>
        d.day === day ? { ...d, mood, isCompleted: true } : d
      ),
    })),

  setActiveTrack: (track) => set({ activeTrack: track }),
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setDuration: (duration) => set({ duration }),
  setCurrentTime: (time) => set({ currentTime: time }),
  setShowPlayer: (show) => set({ showPlayer: show }),
  setSleepTimer: (minutes) => set({
    sleepTimer: minutes,
    sleepTimerStartTime: minutes !== null ? Date.now() : null
  }),
}));
