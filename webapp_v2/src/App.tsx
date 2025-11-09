import { useEffect } from 'react';
import { useAppStore } from './stores/useAppStore';
import { telegram } from './services/telegram';

import { SplashScreen } from './components/screens/SplashScreen';
import { OnboardingScreen } from './components/screens/OnboardingScreen';
import { MainScreen } from './components/screens/MainScreen';
import { VoiceChatScreen } from './components/screens/VoiceChatScreen';
import { ChatScreen } from './components/screens/ChatScreen';
import { GeneralVoiceScreen } from './components/screens/GeneralVoiceScreen';
import { PracticesScreen } from './components/screens/PracticesScreen';
import { PracticePlayerScreen } from './components/screens/PracticePlayerScreen';
import { ChatHistoryScreen } from './components/screens/ChatHistoryScreen';
import { ProfileScreen } from './components/screens/ProfileScreen';
import { AnalysisScreen } from './components/screens/AnalysisScreen';
import { AnalysisChatScreen } from './components/screens/AnalysisChatScreen';
import { AnalysisVoiceScreen } from './components/screens/AnalysisVoiceScreen';
import { DreamsChatScreen } from './components/screens/DreamsChatScreen';
import { PatternsScreen } from './components/screens/PatternsScreen';
import { FullscreenPlayer } from './components/player/FullscreenPlayer';
import { VideoPlayer } from './components/player/VideoPlayer';
import { MiniPlayer } from './components/player/MiniPlayer';

function App() {
  const currentScreen = useAppStore((state) => state.currentScreen);
  const setUser = useAppStore((state) => state.setUser);
  const showPlayer = useAppStore((state) => state.showPlayer);
  const activeTrack = useAppStore((state) => state.activeTrack);

  useEffect(() => {
    const user = telegram.getUser();
    if (user) {
      setUser(user);
    } else {
      console.warn('Running outside Telegram, using test user');
      setUser({ id: 123456, firstName: 'Тест', lastName: 'User', username: 'testuser' });
    }
  }, [setUser]);

  return (
    <>
      <SplashScreen isActive={currentScreen === 'splash'} />
      <OnboardingScreen isActive={currentScreen === 'onboarding'} />
      <MainScreen isActive={currentScreen === 'main'} />
      <VoiceChatScreen isActive={currentScreen === 'voiceChat'} />
      <ChatScreen isActive={currentScreen === 'chat'} />
      <GeneralVoiceScreen isActive={currentScreen === 'generalVoice'} />
      <PracticesScreen isActive={currentScreen === 'practices'} />
      <PracticePlayerScreen isActive={currentScreen === 'practicePlayer'} />
      <ChatHistoryScreen isActive={currentScreen === 'chatHistory'} />
      <ProfileScreen isActive={currentScreen === 'profile'} />
      <AnalysisScreen isActive={currentScreen === 'analysis'} />
      <AnalysisChatScreen isActive={currentScreen === 'analysisChat'} />
      <AnalysisVoiceScreen isActive={currentScreen === 'analysisVoice'} />
      <DreamsChatScreen isActive={currentScreen === 'dreamsChat'} />
      <PatternsScreen isActive={currentScreen === 'patterns'} />

      {/* Media Players */}
      {showPlayer && activeTrack && (
        activeTrack.mediaType === 'video' ? <VideoPlayer /> : <FullscreenPlayer />
      )}
      {!showPlayer && activeTrack && activeTrack.mediaType !== 'video' && <MiniPlayer />}
    </>
  );
}

export default App;
