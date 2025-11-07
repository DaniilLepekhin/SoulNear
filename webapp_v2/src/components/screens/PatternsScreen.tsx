// ==========================================
// Patterns Screen - Визуализация AI-паттернов пользователя
// ==========================================

import { useEffect, useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import type { Pattern } from '../../types';

declare const Telegram: any;

interface PatternsScreenProps {
  isActive: boolean;
}

export const PatternsScreen = ({ isActive }: PatternsScreenProps) => {
  const telegram = Telegram?.WebApp;
  const { user, setScreen } = useAppStore();
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [filterType, setFilterType] = useState<'all' | 'behavioral' | 'emotional' | 'cognitive'>('all');

  useEffect(() => {
    if (!isActive) return;
    loadPatterns();
  }, [isActive, user]);

  const loadPatterns = async () => {
    if (!user) return;
    setLoading(true);
    const result = await api.getPatterns(user.id);
    if (result.success && result.data) {
      setPatterns(result.data);
    }
    setLoading(false);
  };

  const getFrequencyColor = (frequency: string) => {
    switch (frequency) {
      case 'high': return '#EF5350';
      case 'medium': return '#FFA726';
      case 'low': return '#66BB6A';
      default: return '#90A4AE';
    }
  };

  const getTypeEmoji = (type: string) => {
    switch (type) {
      case 'behavioral': return '🎭';
      case 'emotional': return '💫';
      case 'cognitive': return '🧠';
      default: return '🔮';
    }
  };

  const filteredPatterns = patterns.filter(p =>
    filterType === 'all' || p.type === filterType
  );

  const sortedPatterns = [...filteredPatterns].sort((a, b) =>
    b.occurrences - a.occurrences
  );

  const handlePatternClick = (pattern: Pattern) => {
    setSelectedPattern(pattern);
    telegram?.haptic?.('light');
  };

  const handleBack = () => {
    if (selectedPattern) {
      setSelectedPattern(null);
    } else {
      setScreen('main');
    }
    telegram?.haptic?.('light');
  };

  if (loading) {
    return (
      <div className={`screen ${isActive ? 'active' : ''}`}>
        <div className="screen-header">
          <button className="back-button" onClick={handleBack}>
            ← Назад
          </button>
          <h1>Мои паттерны</h1>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Загружаем ваши паттерны...</p>
        </div>
      </div>
    );
  }

  if (selectedPattern) {
    return (
      <div className={`screen pattern-detail-screen ${isActive ? 'active' : ''}`}>
        <div className="screen-header">
          <button className="back-button" onClick={handleBack}>
            ← Назад
          </button>
          <h1>{getTypeEmoji(selectedPattern.type)} {selectedPattern.title}</h1>
        </div>

        <div className="pattern-detail-content">
          {/* Основная информация */}
          <div className="pattern-section">
            <div className="pattern-stats-row">
              <div className="stat-pill">
                <span className="stat-label">Частота:</span>
                <span
                  className="stat-value"
                  style={{ color: getFrequencyColor(selectedPattern.frequency) }}
                >
                  {selectedPattern.frequency === 'high' ? 'Высокая' :
                   selectedPattern.frequency === 'medium' ? 'Средняя' : 'Низкая'}
                </span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Встречался:</span>
                <span className="stat-value">{selectedPattern.occurrences} раз</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Уверенность:</span>
                <span className="stat-value">{Math.round(selectedPattern.confidence * 100)}%</span>
              </div>
            </div>
          </div>

          {/* Описание */}
          {selectedPattern.description && (
            <div className="pattern-section">
              <h3>📝 Описание</h3>
              <p className="pattern-text">{selectedPattern.description}</p>
            </div>
          )}

          {/* V2 features */}
          {selectedPattern.contradiction && (
            <div className="pattern-section alert-section">
              <h3>⚡ Внутреннее противоречие</h3>
              <p className="pattern-text contradiction">{selectedPattern.contradiction}</p>
            </div>
          )}

          {selectedPattern.hidden_dynamic && (
            <div className="pattern-section insight-section">
              <h3>🔍 Скрытая динамика</h3>
              <p className="pattern-text">{selectedPattern.hidden_dynamic}</p>
            </div>
          )}

          {selectedPattern.blocked_resource && (
            <div className="pattern-section resource-section">
              <h3>💎 Заблокированный ресурс</h3>
              <p className="pattern-text">{selectedPattern.blocked_resource}</p>
            </div>
          )}

          {/* Цитаты из сообщений */}
          {selectedPattern.evidence && selectedPattern.evidence.length > 0 && (
            <div className="pattern-section">
              <h3>💬 Ваши слова</h3>
              <div className="evidence-list">
                {selectedPattern.evidence.slice(0, 5).map((quote, idx) => (
                  <div key={idx} className="evidence-item">
                    <span className="quote-mark">"</span>
                    {quote}
                    <span className="quote-mark">"</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Context weights (связь с темами) */}
          {selectedPattern.context_weights && Object.keys(selectedPattern.context_weights).length > 0 && (
            <div className="pattern-section">
              <h3>🎯 Связь с темами</h3>
              <div className="context-weights">
                {Object.entries(selectedPattern.context_weights)
                  .sort(([, a], [, b]) => b - a)
                  .map(([topic, weight]) => (
                    <div key={topic} className="context-weight-item">
                      <span className="topic-name">{topic}</span>
                      <div className="weight-bar">
                        <div
                          className="weight-fill"
                          style={{ width: `${weight * 100}%` }}
                        ></div>
                      </div>
                      <span className="weight-percent">{Math.round(weight * 100)}%</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Response hint */}
          {selectedPattern.response_hint && (
            <div className="pattern-section action-section">
              <h3>💡 Рекомендация</h3>
              <p className="pattern-text hint">{selectedPattern.response_hint}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`screen patterns-screen ${isActive ? 'active' : ''}`}>
      <div className="screen-header">
        <button className="back-button" onClick={handleBack}>
          ← Назад
        </button>
        <h1>Мои паттерны</h1>
      </div>

      {/* Фильтры */}
      <div className="pattern-filters">
        <button
          className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => setFilterType('all')}
        >
          Все ({patterns.length})
        </button>
        <button
          className={`filter-btn ${filterType === 'behavioral' ? 'active' : ''}`}
          onClick={() => setFilterType('behavioral')}
        >
          🎭 Поведенческие
        </button>
        <button
          className={`filter-btn ${filterType === 'emotional' ? 'active' : ''}`}
          onClick={() => setFilterType('emotional')}
        >
          💫 Эмоциональные
        </button>
        <button
          className={`filter-btn ${filterType === 'cognitive' ? 'active' : ''}`}
          onClick={() => setFilterType('cognitive')}
        >
          🧠 Когнитивные
        </button>
      </div>

      <div className="patterns-list">
        {sortedPatterns.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔮</div>
            <h3>Паттерны пока не обнаружены</h3>
            <p>Продолжайте общаться с AI-помощником, и система начнёт выявлять ваши паттерны поведения и мышления.</p>
          </div>
        ) : (
          sortedPatterns.map(pattern => (
            <div
              key={pattern.id}
              className="pattern-card"
              onClick={() => handlePatternClick(pattern)}
            >
              <div className="pattern-card-header">
                <span className="pattern-emoji">{getTypeEmoji(pattern.type)}</span>
                <h3>{pattern.title}</h3>
                <span
                  className="frequency-badge"
                  style={{ backgroundColor: getFrequencyColor(pattern.frequency) }}
                >
                  {pattern.occurrences}x
                </span>
              </div>

              {pattern.description && (
                <p className="pattern-preview">{pattern.description.slice(0, 120)}...</p>
              )}

              <div className="pattern-card-footer">
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{ width: `${pattern.confidence * 100}%` }}
                  ></div>
                </div>
                <span className="confidence-text">{Math.round(pattern.confidence * 100)}% уверенность</span>
              </div>

              {pattern.contradiction && (
                <div className="pattern-badge contradiction-badge">
                  ⚡ Есть противоречие
                </div>
              )}
              {pattern.blocked_resource && (
                <div className="pattern-badge resource-badge">
                  💎 Заблокирован ресурс
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
