import React, { useState, useRef, useEffect } from 'react';
import { CheckIcon, ForwardIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';

interface TranscriptionFormProps {
  chunkId: number;
  onSubmit: (text: string) => void;
  onSkip: () => void;
  isSubmitting?: boolean;
  placeholder?: string;
  className?: string;
}

const TranscriptionForm: React.FC<TranscriptionFormProps> = ({
  chunkId,
  onSubmit,
  onSkip,
  isSubmitting = false,
  placeholder = 'এখানে বাংলায় অডিওর ট্রান্সক্রিপশন লিখুন...',
  className = '',
}) => {
  const [text, setText] = useState('');
  const [showBanglaKeyboard, setShowBanglaKeyboard] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { t } = useTranslation();

  // Bangla keyboard layout (simplified)
  const banglaKeys = [
    ['১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯', '০'],
    ['ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ'],
    ['ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন'],
    ['প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'শ', 'ষ'],
    ['স', 'হ', 'ড়', 'ঢ়', 'য়', 'ৎ', 'ং', 'ঃ', 'ঁ'],
    ['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ'],
    ['্', '।', '?', '!', ',', ';', ':', '"', "'", ' '],
  ];

  useEffect(() => {
    // Reset form when chunk changes
    setText('');
  }, [chunkId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !isSubmitting) {
      onSubmit(text.trim());
    }
  };

  const handleKeyPress = (key: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newText = text.substring(0, start) + key + text.substring(end);

    setText(newText);

    // Set cursor position after the inserted character
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + key.length;
      textarea.focus();
    }, 0);
  };

  const handleTextareaKeyDown = (e: React.KeyboardEvent) => {
    // Handle common shortcuts
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit(e);
      }
    }
  };

  const isTextValid = text.trim().length > 0;

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Text Input Area */}
        <div>
          <label htmlFor="transcription" className="block text-sm font-medium text-gray-700 mb-2">
            {t('transcriptionForm-title')}
          </label>
          <div className="relative">
            <textarea
              ref={textareaRef}
              id="transcription"
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={handleTextareaKeyDown}
              placeholder={placeholder}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 resize-none"
              style={{ fontFamily: 'SolaimanLipi, Kalpurush, Arial, sans-serif' }}
              disabled={isSubmitting}
            />

            {/* Virtual Keyboard Toggle */}
            <button
              type="button"
              onClick={() => setShowBanglaKeyboard(!showBanglaKeyboard)}
              className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 rounded transition-colors"
            >
              {showBanglaKeyboard
                ? t('transcriptionForm-hide-keyboard')
                : t('transcriptionForm-toggle-keyboard')}
            </button>
          </div>

          {/* Character Count */}
          <div className="mt-1 text-xs text-gray-500 text-right">
            {t('transcriptionForm-char-count', { count: text.length })} {text.length} অক্ষর
          </div>
        </div>

        {/* Virtual Bangla Keyboard */}
        {showBanglaKeyboard && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="space-y-2">
              {banglaKeys.map((row, rowIndex) => (
                <div key={rowIndex} className="flex flex-wrap gap-1 justify-center">
                  {row.map((key, keyIndex) => (
                    <button
                      key={keyIndex}
                      type="button"
                      onClick={() => handleKeyPress(key)}
                      className="min-w-[2rem] h-8 px-2 bg-white hover:bg-gray-100 border border-gray-300 rounded text-sm transition-colors"
                      style={{ fontFamily: 'SolaimanLipi, Kalpurush, Arial, sans-serif' }}
                    >
                      {key}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-4">
          <button
            type="button"
            onClick={onSkip}
            disabled={isSubmitting}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-transparent border border-gray-300 rounded-md transition-colors"
          >
            <ForwardIcon className="w-4 h-4 mr-2" />
            {t('transcriptionForm-skip')}
          </button>

          <div className="flex items-center space-x-3">
            <div className="text-sm text-gray-500">{t('transcriptionForm-shortcut')}</div>
            <button
              type="submit"
              disabled={!isTextValid || isSubmitting}
              className="flex items-center px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md transition-colors"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  {t('transcriptionForm-submitting')}
                </>
              ) : (
                <>
                  <CheckIcon className="w-4 h-4 mr-2" />
                  {t('transcriptionForm-submit')}
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default TranscriptionForm;
