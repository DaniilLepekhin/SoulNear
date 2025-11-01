import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { telegram } from '../../services/telegram';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
  onReaction?: (messageId: string, reaction: 'like' | 'dislike') => void;
  onEdit?: (messageId: string) => void;
  isLastUserMessage?: boolean;
}

export const MessageBubble = ({ message, onReaction, onEdit, isLastUserMessage }: MessageBubbleProps) => {
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      telegram.hapticSuccess();
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
      telegram.hapticError();
    }
  };

  const handleReaction = (reaction: 'like' | 'dislike') => {
    if (onReaction) {
      onReaction(message.id, reaction);
      telegram.haptic('light');
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(message.id);
      telegram.haptic('light');
    }
  };

  return (
    <div
      className={`message ${message.role}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      onTouchStart={() => setShowActions(true)}
    >
      <div className="message-bubble">
        {message.role === 'assistant' ? (
          <div className="message-content markdown">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : (
          <p>{message.content}</p>
        )}

        <div className="message-footer">
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString('ru-RU', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>

          {message.status && (
            <span className="message-status">
              {message.status === 'sending' && '⏱'}
              {message.status === 'sent' && '✓'}
              {message.status === 'error' && '⚠️'}
            </span>
          )}
        </div>

        {showActions && (
          <div className="message-actions">
            {message.role === 'assistant' && (
              <>
                <button
                  className="action-btn copy-btn"
                  onClick={handleCopy}
                  title="Копировать"
                >
                  {copied ? '✓' : '📋'}
                </button>
                <button
                  className="action-btn like-btn"
                  onClick={() => handleReaction('like')}
                  title="Хороший ответ"
                >
                  👍
                </button>
                <button
                  className="action-btn dislike-btn"
                  onClick={() => handleReaction('dislike')}
                  title="Плохой ответ"
                >
                  👎
                </button>
              </>
            )}

            {message.role === 'user' && isLastUserMessage && (
              <button
                className="action-btn edit-btn"
                onClick={handleEdit}
                title="Редактировать"
              >
                ✏️
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
