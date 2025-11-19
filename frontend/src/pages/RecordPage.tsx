import React, { useState } from 'react';
import { MicrophoneIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import VoiceRecordingInterface from '../components/recording/VoiceRecordingInterface';
import ErrorBoundary from '../components/common/ErrorBoundary';
import { VoiceRecording } from '../types/api';
import { useTranslation } from 'react-i18next';

const RecordPage: React.FC = () => {
    const { t } = useTranslation();
    const [completedRecordings, setCompletedRecordings] = useState<
        VoiceRecording[]
    >([]);

    const handleRecordingComplete = (recording: VoiceRecording) => {
        setCompletedRecordings((prev) => [recording, ...prev]);
    };

    return (
        <div className='max-w-4xl mx-auto'>
            <div className='text-center mb-8'>
                <MicrophoneIcon className='mx-auto h-16 w-16 text-indigo-600 mb-4' />
                <h1 className='text-3xl font-bold text-gray-900 mb-2'>
                    {t('recordPage-voice-recording-title')}
                </h1>
                <p className='text-gray-600'>
                    {t('recordPage-voice-recording-description')}
                </p>
            </div>

            {/* Recording Interface */}
            <ErrorBoundary>
                <VoiceRecordingInterface
                    onRecordingComplete={handleRecordingComplete}
                />
            </ErrorBoundary>

            {/* Completed Recordings */}
            {completedRecordings.length > 0 && (
                <div className='mt-8 bg-white rounded-lg shadow-md p-6 border border-gray-200'>
                    <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
                        <CheckCircleIcon className='w-5 h-5 mr-2 text-green-600' />
                        Recent Recordings
                    </h3>
                    <div className='space-y-3'>
                        {completedRecordings.slice(0, 5).map((recording) => (
                            <div
                                key={recording.id}
                                className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                            >
                                <div>
                                    <div className='font-medium text-gray-900'>
                                        Recording #{recording.id}
                                    </div>
                                    <div className='text-sm text-gray-600'>
                                        Duration:{' '}
                                        {Math.round(recording.duration)}s •
                                        Status: {recording.status}
                                    </div>
                                </div>
                                <div className='text-sm text-gray-500'>
                                    {new Date(
                                        recording.created_at
                                    ).toLocaleString()}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default RecordPage;
