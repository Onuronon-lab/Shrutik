import React, { useState } from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import QuantitySelector from '../components/transcription/QuantitySelector';
import TranscriptionInterface from '../components/transcription/TranscriptionInterface';

const TranscribePage: React.FC = () => {
  const [selectedQuantity, setSelectedQuantity] = useState<number>(0);
  const [sessionStarted, setSessionStarted] = useState(false);

  const handleQuantityChange = (quantity: number) => {
    setSelectedQuantity(quantity);
  };

  const handleStartSession = () => {
    if (selectedQuantity > 0) {
      setSessionStarted(true);
    }
  };

  const handleSessionComplete = () => {
    setSessionStarted(false);
    setSelectedQuantity(0);
  };

  const handleBackToSelection = () => {
    setSessionStarted(false);
  };

  if (sessionStarted) {
    return (
      <div className="max-w-4xl mx-auto">
        <TranscriptionInterface
          selectedQuantity={selectedQuantity}
          onComplete={handleSessionComplete}
          onBack={handleBackToSelection}
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <DocumentTextIcon className="mx-auto h-16 w-16 text-success mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">অডিও ট্রান্সক্রিপশন</h1>
        <p className="text-secondary-foreground">
          অডিও ক্লিপ শুনুন এবং নির্ভুল বাংলা ট্রান্সক্রিপশন প্রদান করুন
        </p>
      </div>

      <div className="space-y-6">
        {/* Quantity Selection */}
        <QuantitySelector
          selectedQuantity={selectedQuantity}
          onQuantityChange={handleQuantityChange}
        />

        {/* Start Button */}
        {selectedQuantity > 0 && (
          <div className="text-center">
            <button
              onClick={handleStartSession}
              className="px-8 py-3 bg-success hover:bg-success-hover text-success-foreground text-lg font-semibold rounded-lg transition-colors shadow-md hover:shadow-lg"
            >
              ট্রান্সক্রিপশন শুরু করুন
            </button>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-info border border-info-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-info-foreground mb-4">নির্দেশনা:</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-info-foreground">
            <div>
              <h4 className="font-medium mb-2">🎧 অডিও শোনার জন্য:</h4>
              <ul className="space-y-1 text-xs">
                <li>• প্লে বাটনে ক্লিক করুন</li>
                <li>• ওয়েভফর্মে ক্লিক করে যেকোনো অংশে যান</li>
                <li>• রিস্টার্ট বাটনে ক্লিক করে আবার শুরু করুন</li>
                <li>• প্রয়োজনে একাধিকবার শুনুন</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">✍️ ট্রান্সক্রিপশনের জন্য:</h4>
              <ul className="space-y-1 text-xs">
                <li>• যথাসম্ভব নির্ভুল বাংলায় লিখুন</li>
                <li>• বাংলা কীবোর্ড ব্যবহার করতে পারেন</li>
                <li>• অস্পষ্ট অডিও এড়িয়ে যান</li>
                <li>• Ctrl+Enter দিয়ে দ্রুত জমা দিন</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscribePage;