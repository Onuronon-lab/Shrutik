import React, { useState, useRef, useEffect } from 'react';
import { PlayIcon, PauseIcon, ArrowPathIcon } from '@heroicons/react/24/solid';

interface AudioPlayerProps {
  audioUrl: string;
  onLoadError?: (error: string) => void;
  className?: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl, onLoadError, className = '' }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setIsLoading(false);
      drawWaveform();
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
      drawWaveform();
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleError = () => {
      const errorMsg = 'Failed to load audio file';
      setError(errorMsg);
      setIsLoading(false);
      onLoadError?.(errorMsg);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      const currentAnimation = animationRef.current;
      if (currentAnimation) {
        cancelAnimationFrame(currentAnimation);
      }
    };
  }, [audioUrl, onLoadError]); // eslint-disable-line react-hooks/exhaustive-deps

  const drawWaveform = () => {
    const canvas = canvasRef.current;
    const audio = audioRef.current;
    if (!canvas || !audio) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw background
    ctx.fillStyle = '#f3f4f6';
    ctx.fillRect(0, 0, width, height);

    // Draw waveform bars (simplified visualization)
    const barCount = 50;
    const barWidth = width / barCount;
    const progress = duration > 0 ? currentTime / duration : 0;

    for (let i = 0; i < barCount; i++) {
      const barHeight = Math.random() * height * 0.8 + height * 0.1;
      const x = i * barWidth;
      const y = (height - barHeight) / 2;

      // Color based on progress
      if (i / barCount <= progress) {
        ctx.fillStyle = '#10b981'; // Green for played portion
      } else {
        ctx.fillStyle = '#d1d5db'; // Gray for unplayed portion
      }

      ctx.fillRect(x, y, barWidth - 1, barHeight);
    }

    // Draw progress line
    const progressX = progress * width;
    ctx.strokeStyle = '#059669';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(progressX, 0);
    ctx.lineTo(progressX, height);
    ctx.stroke();
  };

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.currentTime = 0;
    setCurrentTime(0);
    if (isPlaying) {
      audio.play();
    }
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const audio = audioRef.current;
    const canvas = canvasRef.current;
    if (!audio || !canvas || duration === 0) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const clickProgress = x / canvas.width;
    const newTime = clickProgress * duration;

    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <p className="text-red-600 text-sm">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Waveform Canvas */}
      <div className="mb-4">
        <canvas
          ref={canvasRef}
          width={400}
          height={80}
          className="w-full h-20 cursor-pointer border border-gray-200 rounded"
          onClick={handleCanvasClick}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={togglePlayPause}
            disabled={isLoading}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-full transition-colors"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : isPlaying ? (
              <PauseIcon className="w-5 h-5" />
            ) : (
              <PlayIcon className="w-5 h-5 ml-0.5" />
            )}
          </button>

          <button
            onClick={handleRestart}
            disabled={isLoading}
            className="flex items-center justify-center w-8 h-8 text-gray-600 hover:text-gray-800 disabled:text-gray-400 transition-colors"
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Time Display */}
        <div className="text-sm text-gray-600">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
