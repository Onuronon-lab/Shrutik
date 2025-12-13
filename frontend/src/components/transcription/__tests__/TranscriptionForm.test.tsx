import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest';
import TranscriptionForm from '../TranscriptionForm';
import i18n from '../../../i18n';

const renderWithI18n = (ui: React.ReactElement) =>
  render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

describe('TranscriptionForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnSkip = vi.fn();

  beforeAll(() => {
    i18n.changeLanguage('bn');
  });

  beforeEach(() => {
    mockOnSubmit.mockClear();
    mockOnSkip.mockClear();
  });

  it('renders transcription form elements', () => {
    renderWithI18n(<TranscriptionForm chunkId={1} onSubmit={mockOnSubmit} onSkip={mockOnSkip} />);

    expect(screen.getByLabelText('ট্রান্সক্রিপশন')).toBeInTheDocument();
    expect(screen.getByText('জমা দিন')).toBeInTheDocument();
    expect(screen.getByText('এড়িয়ে যান')).toBeInTheDocument();
  });

  it('calls onSubmit when form is submitted with text', async () => {
    renderWithI18n(<TranscriptionForm chunkId={1} onSubmit={mockOnSubmit} onSkip={mockOnSkip} />);

    const textarea = screen.getByLabelText('ট্রান্সক্রিপশন');
    const submitButton = screen.getByText('জমা দিন');

    fireEvent.change(textarea, { target: { value: 'এটি একটি পরীক্ষা' } });

    await waitFor(() => expect(submitButton).not.toBeDisabled());
    fireEvent.click(submitButton);

    await waitFor(() => expect(mockOnSubmit).toHaveBeenCalledWith('এটি একটি পরীক্ষা'));
  });

  it('calls onSkip when skip button is clicked', () => {
    renderWithI18n(<TranscriptionForm chunkId={1} onSubmit={mockOnSubmit} onSkip={mockOnSkip} />);

    const skipButton = screen.getByText('এড়িয়ে যান');
    fireEvent.click(skipButton);

    expect(mockOnSkip).toHaveBeenCalled();
  });

  it('disables submit button when text is empty', () => {
    renderWithI18n(<TranscriptionForm chunkId={1} onSubmit={mockOnSubmit} onSkip={mockOnSkip} />);

    const submitButton = screen.getByText('জমা দিন');
    expect(submitButton).toBeDisabled();
  });

  it('shows character count', async () => {
    renderWithI18n(<TranscriptionForm chunkId={1} onSubmit={mockOnSubmit} onSkip={mockOnSkip} />);

    const textarea = screen.getByLabelText('ট্রান্সক্রিপশন');
    fireEvent.change(textarea, { target: { value: 'পরীক্ষা' } });

    await waitFor(() => expect(screen.getByText('৭ অক্ষর')).toBeInTheDocument());
  });
});
