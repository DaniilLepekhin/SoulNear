// ==========================================
// Button Component
// ==========================================

import 'react';
import { telegram } from '../../services/telegram';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  disabled?: boolean;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  disabled = false,
  className = '',
}) => {
  const handleClick = () => {
    if (!disabled && onClick) {
      telegram.haptic('light');
      onClick();
    }
  };

  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth && 'btn-full-width',
    disabled && 'btn-disabled',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} onClick={handleClick} disabled={disabled}>
      {children}
    </button>
  );
};
