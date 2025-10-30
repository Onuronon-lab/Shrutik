import React from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';

interface QuantitySelectorProps {
  selectedQuantity: number;
  onQuantityChange: (quantity: number) => void;
  disabled?: boolean;
  className?: string;
}

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  selectedQuantity,
  onQuantityChange,
  disabled = false,
  className = ''
}) => {
  const quantities = [
    { value: 2, label: '২টি বাক্য', time: '~৫ মিনিট', color: 'bg-green-100 text-green-800 border-green-200' },
    { value: 5, label: '৫টি বাক্য', time: '~১০ মিনিট', color: 'bg-blue-100 text-blue-800 border-blue-200' },
    { value: 10, label: '১০টি বাক্য', time: '~২০ মিনিট', color: 'bg-purple-100 text-purple-800 border-purple-200' },
    { value: 15, label: '১৫টি বাক্য', time: '~৩০ মিনিট', color: 'bg-orange-100 text-orange-800 border-orange-200' },
    { value: 20, label: '২০টি বাক্য', time: '~৪০ মিনিট', color: 'bg-red-100 text-red-800 border-red-200' }
  ];

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          কতটি বাক্য ট্রান্সক্রাইব করতে চান?
        </h3>
        <p className="text-gray-600 text-sm">
          আপনার সুবিধামতো পরিমাণ নির্বাচন করুন
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {quantities.map((option) => (
          <button
            key={option.value}
            onClick={() => onQuantityChange(option.value)}
            disabled={disabled}
            className={`
              relative p-4 rounded-lg border-2 transition-all duration-200 text-center
              ${selectedQuantity === option.value 
                ? `${option.color} border-current shadow-md transform scale-105` 
                : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-sm'}
            `}
          >
            {/* Selection Indicator */}
            {selectedQuantity === option.value && (
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            )}

            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {option.value}
              </div>
              <div className="text-sm font-medium">
                {option.label}
              </div>
              <div className="flex items-center justify-center text-xs opacity-75">
                <ClockIcon className="w-3 h-3 mr-1" />
                {option.time}
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedQuantity > 0 && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">আপনি {selectedQuantity}টি বাক্য ট্রান্সক্রাইব করার জন্য নির্বাচন করেছেন</p>
              <ul className="text-xs space-y-1 opacity-90">
                <li>• প্রতিটি অডিও ক্লিপ মনোযোগ দিয়ে শুনুন</li>
                <li>• যথাসম্ভব নির্ভুল বাংলায় লিখুন</li>
                <li>• অস্পষ্ট অডিও এড়িয়ে যেতে পারেন</li>
                <li>• যেকোনো সময় বন্ধ করে পরে আবার শুরু করতে পারেন</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuantitySelector;