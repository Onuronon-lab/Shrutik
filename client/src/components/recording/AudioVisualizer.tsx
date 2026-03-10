import React, { useEffect, useRef, useState } from 'react';
import { useRecordingStore } from '../../stores/recordingStore';

interface AudioVisualizerProps {
  isRecording: boolean;
  className?: string;
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ isRecording, className = '' }) => {
  // Get stream from the recording store instead of props
  const stream = useRecordingStore(state => state.stream);
  const animationRef = useRef<number | undefined>(undefined);
  const analyserRef = useRef<AnalyserNode | undefined>(undefined);
  const [audioLevel, setAudioLevel] = useState(0);

  useEffect(() => {
    if (!stream || !isRecording) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      setAudioLevel(0);
      return;
    }

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);

    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    source.connect(analyser);

    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateVisualizer = () => {
      if (!analyserRef.current) return;

      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average audio level
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      setAudioLevel(average);

      if (isRecording) {
        animationRef.current = requestAnimationFrame(updateVisualizer);
      }
    };

    updateVisualizer();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      audioContext.close();
    };
  }, [stream, isRecording]);

  // Simple bar visualizer when no canvas is needed
  const renderSimpleBars = () => {
    const bars = Array.from({ length: 5 }, (_, i) => {
      const height = isRecording ? Math.max(10, (audioLevel / 255) * 40 + Math.random() * 10) : 10;

      return (
        <div
          key={i}
          className="audio-bar"
          style={{
            height: `${height}px`,
            animationDelay: `${i * 0.1}s`,
            opacity: isRecording ? 1 : 0.3,
          }}
        />
      );
    });

    return <div className={`audio-visualizer ${className}`}>{bars}</div>;
  };

  return renderSimpleBars();
};

export default AudioVisualizer;
