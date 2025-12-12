import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import QuantitySelector from '../QuantitySelector';
import i18n from '../../../i18n';

describe('QuantitySelector', () => {
  const mockOnQuantityChange = jest.fn();

  const renderWithI18n = (ui: React.ReactElement) =>
    render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

  beforeAll(() => {
    i18n.changeLanguage('bn');
  });

  beforeEach(() => {
    mockOnQuantityChange.mockClear();
  });

  test('renders quantity options', () => {
    renderWithI18n(
      <QuantitySelector selectedQuantity={0} onQuantityChange={mockOnQuantityChange} />
    );

    expect(screen.getByText('২টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('৫টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('১০টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('১৫টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('২০টি বাক্য')).toBeInTheDocument();
  });

  test('calls onQuantityChange when option is selected', () => {
    renderWithI18n(
      <QuantitySelector selectedQuantity={0} onQuantityChange={mockOnQuantityChange} />
    );

    const fiveOption = screen.getByText('৫টি বাক্য');
    fireEvent.click(fiveOption);

    expect(mockOnQuantityChange).toHaveBeenCalledWith(5);
  });

  test('shows selected quantity with visual indicator', () => {
    renderWithI18n(
      <QuantitySelector selectedQuantity={10} onQuantityChange={mockOnQuantityChange} />
    );

    const tenOptionButton = screen.getByText('১০টি বাক্য').closest('button');
    expect(tenOptionButton).toHaveClass('border-current');
  });

  test('shows instructions when quantity is selected', () => {
    renderWithI18n(
      <QuantitySelector selectedQuantity={5} onQuantityChange={mockOnQuantityChange} />
    );

    expect(
      screen.getByText(/আপনি ৫টি বাক্য ট্রান্সক্রাইব করার জন্য নির্বাচন করেছেন/)
    ).toBeInTheDocument();
  });
});
