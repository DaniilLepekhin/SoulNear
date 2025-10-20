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
import { DreamsScreen } from './components/screens/DreamsScreen';
import { DreamsChatScreen } from './components/screens/DreamsChatScreen';
import { DreamsVoiceScreen } from './components/screens/DreamsVoiceScreen';

function App() {
  const currentScreen = useAppStore((state) => state.currentScreen);
  const setUser = useAppStore((state) => state.setUser);

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
      <DreamsScreen isActive={currentScreen === 'dreams'} />
      <DreamsChatScreen isActive={currentScreen === 'dreamsChat'} />
      <DreamsVoiceScreen isActive={currentScreen === 'dreamsVoice'} />
    </>
  );
}

export default App;
