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
  showPlayer: boolean;

  // Actions
  setScreen: (screen: Screen) => void;
  goBack: () => void;
  setUser: (user: User) => void;
  addChatMessage: (message: Message) => void;
  clearChatMessages: () => void;
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
  setShowPlayer: (show: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  currentScreen: 'splash',
  previousScreen: null,
  user: null,
  chatMessages: [],
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
  showPlayer: false,

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

  clearChatMessages: () => set({ chatMessages: [] }),

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
  setShowPlayer: (show) => set({ showPlayer: show }),
}));
