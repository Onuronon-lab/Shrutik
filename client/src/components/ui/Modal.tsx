import { ReactNode } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  showCloseButton?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  className,
}: ModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className={cn(
          'bg-card rounded-lg shadow-xl p-6 w-full mx-4 border border-border relative',
          sizeClasses[size],
          className
        )}
        onClick={e => e.stopPropagation()}
      >
        {title && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="text-secondary-foreground hover:text-foreground transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
