import { useEffect, useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';
import { useVideoPlayer } from '../../hooks/useVideoPlayer';
import type { Track } from '../../types';

interface PracticesScreenProps {
  isActive: boolean;
}

export const PracticesScreen = ({ isActive }: PracticesScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);
  const [practicesData, setPracticesData] = useState<{ practices: any[]; music?: any[]; videos?: any[] } | null>(null);
  const { playTrack: playAudioTrack } = useAudioPlayer();
  const { playTrack: playVideoTrack } = useVideoPlayer();

  // Helper function to play track based on mediaType
  const playTrack = (track: Track) => {
    if (track.mediaType === 'video') {
      playVideoTrack(track);
    } else {
      playAudioTrack(track);
    }
  };

  useEffect(() => {
    loadPractices();
  }, []);

  const loadPractices = async () => {
    const result = await api.getPractices();
    if (result.success && result.data) {
      setPracticesData(result.data);
    } else {
      console.error('❌ Failed to load practices:', result.error);
    }
  };

  const filterPractices = (filter: string, event: React.MouseEvent) => {
    // Update filter buttons
    event.currentTarget.parentElement?.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    (event.currentTarget as HTMLElement).classList.add('active');

    // Filter practice items
    const practiceItems = document.querySelectorAll('.practice-item');
    practiceItems.forEach(item => {
      const itemCategory = item.getAttribute('data-category');
      const isFavorite = item.getAttribute('data-favorite') === 'true';

      if (filter === 'all') {
        (item as HTMLElement).style.display = '';
      } else if (filter === 'favorites') {
        (item as HTMLElement).style.display = isFavorite ? '' : 'none';
      } else {
        (item as HTMLElement).style.display = itemCategory === filter ? '' : 'none';
      }
    });

    // Also handle category sections
    const categorySections = document.querySelectorAll('.practice-category');
    categorySections.forEach(section => {
      const categoryType = section.getAttribute('data-category');

      if (filter === 'all') {
        (section as HTMLElement).style.display = '';
      } else if (filter === 'favorites') {
        // Check if any items in this category are favorites
        const favoriteItems = section.querySelectorAll('.practice-item[data-favorite="true"]');
        (section as HTMLElement).style.display = favoriteItems.length > 0 ? '' : 'none';
      } else {
        (section as HTMLElement).style.display = categoryType === filter ? '' : 'none';
      }
    });

    console.log('Filter selected:', filter);
  };

  const selectPlanItem = (event: React.MouseEvent) => {
    event.currentTarget.parentElement?.querySelectorAll('.plan-item').forEach(item => {
      item.classList.remove('active');
      (item as HTMLElement).style.background = '#FFFFFF';
      (item as HTMLElement).style.color = '#2E6BEB';
    });
    (event.currentTarget as HTMLElement).classList.add('active');
    (event.currentTarget as HTMLElement).style.background = '#2E6BEB';
    (event.currentTarget as HTMLElement).style.color = 'white';
  };

  return (
    <div className={`screen practices-screen ${isActive ? 'active' : ''}`} id="practices-screen">
      <div className="practices-header">
        <h1 className="practices-title">Практики</h1>
      </div>

      <div className="practices-filters">
        <button className="filter-btn active" onClick={(e) => filterPractices('all', e)}>Все</button>
        <button className="filter-btn favorite-filter" onClick={(e) => filterPractices('favorites', e)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="none"/>
          </svg>
        </button>
        <button className="filter-btn" onClick={(e) => filterPractices('meditation', e)}>Медитации</button>
        <button className="filter-btn" onClick={(e) => filterPractices('yoga', e)}>Йога</button>
        <button className="filter-btn" onClick={(e) => filterPractices('music', e)}>Музыка</button>
      </div>

      <div className="practices-content">
        <div className="practice-category" data-category="all">
          <div className="practice-cards-row">
            <div className="practice-card plan-card practice-item" data-category="all" data-favorite="false">
              <div className="card-header">
                <h3 className="card-title">План<br/>на день</h3>
              </div>
              <div className="plan-items" style={{display: 'flex', flexDirection: 'column', gap: '2px', margin: 0, padding: 0}}>
                <button className="plan-item active" onClick={selectPlanItem} style={{padding: '6px 12px', borderRadius: '16px', fontSize: '12px', height: '32px', border: '1px solid #2E6BEB', background: '#2E6BEB', color: 'white', cursor: 'pointer', textAlign: 'left', fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', margin: 0, boxSizing: 'border-box', pointerEvents: 'auto', position: 'relative', zIndex: 10}}>Аффирмации</button>
                <button className="plan-item" onClick={selectPlanItem} style={{padding: '6px 12px', borderRadius: '16px', fontSize: '12px', height: '32px', border: '1px solid #2E6BEB', background: '#FFFFFF', color: '#2E6BEB', cursor: 'pointer', textAlign: 'left', fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', margin: 0, boxSizing: 'border-box', pointerEvents: 'auto', position: 'relative', zIndex: 10}}>Медитация</button>
                <button className="plan-item" onClick={selectPlanItem} style={{padding: '6px 12px', borderRadius: '16px', fontSize: '12px', height: '32px', border: '1px solid #2E6BEB', background: '#FFFFFF', color: '#2E6BEB', cursor: 'pointer', textAlign: 'left', fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', margin: 0, boxSizing: 'border-box', pointerEvents: 'auto', position: 'relative', zIndex: 10}}>Мантры</button>
              </div>
            </div>

            <div className="practice-card evening-card practice-item" data-category="all" data-favorite="false" onClick={(e) => filterPractices('yoga', e)}>
              <h3 className="evening-title">Йога<br/>практики</h3>
            </div>
          </div>
        </div>

        {/* Dynamic practices from API */}
        {practicesData?.practices && Array.isArray(practicesData.practices) && practicesData.practices.map((category: any, idx: number) => (
          category.items && category.items.length > 0 && (
            <div key={idx} className="practice-category" data-category="meditation">
              <div className="category-header">
                <h3 className="category-title">{category.name}</h3>
              </div>
              {category.items.map((item: any, itemIdx: number) => (
                <div
                  key={itemIdx}
                  className="meditation-card practice-item"
                  data-category="meditation"
                  data-favorite="false"
                  data-media-id={item.media_id || ''}
                >
                  <button className="practice-favorite-btn" onClick={(e) => { e.stopPropagation(); console.log('Toggle favorite'); }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" stroke="#4A90E2" strokeWidth="1.5" fill="none"/>
                    </svg>
                  </button>
                  <div className="meditation-info">
                    <h4 className="meditation-title">{item.name}</h4>
                    <div className="meditation-tags">
                      <span className="tag">Медитация</span>
                    </div>
                  </div>
                  <button className="meditation-play-btn" onClick={() => {
                    const track: Track = {
                      media_id: item.media_id || String(itemIdx),
                      name: item.name,
                      url: item.url,
                      category: 'Медитация'
                    };
                    playTrack(track);
                  }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M8 5V19L19 12L8 5Z" fill="white"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )
        ))}

        {/* Yoga videos */}
        {practicesData?.videos && Array.isArray(practicesData.videos) && (() => {
          const yogaCategory = practicesData.videos.find((cat: any) => cat.name === '🧘 Йога');
          return yogaCategory && yogaCategory.items && yogaCategory.items.length > 0 && (
            <div className="practice-category" data-category="yoga">
              <div className="category-header">
                <h3 className="category-title">🧘 Йога практики</h3>
              </div>
              {yogaCategory.items.map((item: any, idx: number) => {
                const emoji = item.name.includes('Утренняя') ? '☀️' : '🌙';
                // Remove existing emojis from the name
                const cleanName = item.name.replace(/[☀️🌙]/g, '').trim();
                const displayName = cleanName.replace('практика', '<br>практика');
                return (
                  <div
                    key={idx}
                    className="practice-card evening-card practice-item"
                    data-category="yoga"
                    data-favorite="false"
                    data-media-id={item.media_id || ''}
                    onClick={(e) => {
                      if (!(e.target as HTMLElement).closest('.card-favorite-btn')) {
                        const track: Track = {
                          media_id: item.media_id || String(idx),
                          name: item.name,
                          url: item.url,
                          category: 'Йога',
                          mediaType: 'video'  // 🎬 Yoga videos are video content
                        };
                        playTrack(track);
                      }
                    }}
                  >
                    <h3 className="evening-title" dangerouslySetInnerHTML={{ __html: `${emoji} ${displayName}` }}></h3>
                    <button className="card-favorite-btn" onClick={(e) => { e.stopPropagation(); console.log('Toggle favorite'); }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" stroke="#4A90E2" strokeWidth="1.5" fill="none"/>
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
          );
        })()}

        {/* Music */}
        {practicesData?.music && Array.isArray(practicesData.music) && practicesData.music.length > 0 && (
          <div className="practice-category" data-category="music">
            <div className="category-header">
              <h3 className="category-title">🎵 Ханг музыка</h3>
            </div>
            {practicesData.music.map((track: any, idx: number) => (
              <div
                key={idx}
                className="meditation-card practice-item"
                data-category="music"
                data-favorite="false"
                data-media-id={track.media_id || ''}
                data-audio-url={track.url || ''}
              >
                <button className="practice-favorite-btn" onClick={(e) => { e.stopPropagation(); console.log('Toggle favorite'); }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" stroke="#4A90E2" strokeWidth="1.5" fill="none"/>
                  </svg>
                </button>
                <div className="meditation-info">
                  <h4 className="meditation-title">{track.name}</h4>
                  <div className="meditation-tags">
                    <span className="tag">{track.duration}</span>
                    <span className="tag">Релакс</span>
                  </div>
                </div>
                <button className="meditation-play-btn" onClick={() => {
                  const audioTrack: Track = {
                    media_id: track.media_id || String(idx),
                    name: track.name,
                    url: track.url,
                    duration: track.duration,
                    category: 'Музыка',
                    mediaType: 'audio'  // 🎵 Music tracks are audio content
                  };
                  playTrack(audioTrack);
                }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M8 5V19L19 12L8 5Z" fill="white"/>
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bottom-nav">
        <div className="nav-item" onClick={() => setScreen('main')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setScreen('voiceChat')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item active" onClick={() => setScreen('practices')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 6h4v4H6V6zm0 8h4v4H6v-4zm8-8h4v4h-4V6zm0 8h4v4h-4v-4z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setScreen('profile')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v1c0 .55.45 1 1 1h14c.55 0 1-.45 1-1v-1c0-2.66-5.33-4-8-4z" fill="currentColor"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
