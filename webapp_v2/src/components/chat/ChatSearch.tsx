import { useState } from 'react';
import type { Message } from '../../types';
import type { ReactElement } from 'react';

interface ChatSearchProps {
  messages: Message[];
  onResultClick: (messageIndex: number) => void;
}

export const ChatSearch = ({ messages, onResultClick }: ChatSearchProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const searchResults = searchQuery.trim()
    ? messages
        .map((msg, index) => ({ msg, index }))
        .filter(({ msg }) =>
          msg.content.toLowerCase().includes(searchQuery.toLowerCase())
        )
    : [];

  const handleResultClick = (index: number) => {
    onResultClick(index);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="chat-search">
      <button
        className="chat-search-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="Поиск по сообщениям"
      >
        🔍
      </button>

      {isOpen && (
        <div className="chat-search-panel">
          <div className="chat-search-header">
            <input
              type="text"
              className="chat-search-input"
              placeholder="Поиск по сообщениям..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            <button className="chat-search-close" onClick={() => setIsOpen(false)}>
              ✕
            </button>
          </div>

          <div className="chat-search-results">
            {searchQuery.trim() === '' && (
              <div className="chat-search-empty">
                Введите текст для поиска
              </div>
            )}

            {searchQuery.trim() !== '' && searchResults.length === 0 && (
              <div className="chat-search-empty">
                Ничего не найдено
              </div>
            )}

            {searchResults.map(({ msg, index }) => (
              <div
                key={msg.id}
                className="chat-search-result"
                onClick={() => handleResultClick(index)}
              >
                <div className="search-result-role">
                  {msg.role === 'user' ? 'Вы' : 'Ассистент'}
                </div>
                <div className="search-result-content">
                  {highlightMatch(msg.content, searchQuery)}
                </div>
                <div className="search-result-time">
                  {new Date(msg.timestamp).toLocaleString('ru-RU')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

function highlightMatch(text: string, query: string): ReactElement {
  if (!query.trim()) return <>{text}</>;

  const parts = text.split(new RegExp(`(${query})`, 'gi'));

  return (
    <>
      {parts.map((part, index) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={index}>{part}</mark>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </>
  );
}
