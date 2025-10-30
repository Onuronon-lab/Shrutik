import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TranscriptionForm from '../TranscriptionForm';

describe('TranscriptionForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnSkip = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
    mockOnSkip.mockClear();
  });

  test('renders transcription form elements', () => {
    render(
      <TranscriptionForm
        chunkId={1}
        onSubmit={mockOnSubmit}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByLabelText('ট্রান্সক্রিপশন')).toBeInTheDocument();
    expect(screen.getByText('জমা দিন')).toBeInTheDocument();
    expect(screen.getByText('এড়িয়ে যান')).toBeInTheDocument();
  });

  test('calls onSubmit when form is submitted with text', () => {
    render(
      <TranscriptionForm
        chunkId={1}
        onSubmit={mockOnSubmit}
        onSkip={mockOnSkip}
      />
    );

    const textarea = screen.getByLabelText('ট্রান্সক্রিপশন');
    const submitButton = screen.getByText('জমা দিন');

    fireEvent.change(textarea, { target: { value: 'এটি একটি পরীক্ষা' } });
    fireEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith('এটি একটি পরীক্ষা');
  });

  test('calls onSkip when skip button is clicked', () => {
    render(
      <TranscriptionForm
        chunkId={1}
        onSubmit={mockOnSubmit}
        onSkip={mockOnSkip}
      />
    );

    const skipButton = screen.getByText('এড়িয়ে যান');
    fireEvent.click(skipButton);

    expect(mockOnSkip).toHaveBeenCalled();
  });

  test('disables submit button when text is empty', () => {
    render(
      <TranscriptionForm
        chunkId={1}
        onSubmit={mockOnSubmit}
        onSkip={mockOnSkip}
      />
    );

    const submitButton = screen.getByText('জমা দিন');
    expect(submitButton).toBeDisabled();
  });

  test('shows character count', () => {
    render(
      <TranscriptionForm
        chunkId={1}
        onSubmit={mockOnSubmit}
        onSkip={mockOnSkip}
      />
    );

    const textarea = screen.getByLabelText('ট্রান্সক্রিপশন');
    fireEvent.change(textarea, { target: { value: 'পরীক্ষা' } });

    expect(screen.getByText('৬ অক্ষর')).toBeInTheDocument();
  });
});