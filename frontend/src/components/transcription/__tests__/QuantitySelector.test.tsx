import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import QuantitySelector from '../QuantitySelector';

describe('QuantitySelector', () => {
  const mockOnQuantityChange = jest.fn();

  beforeEach(() => {
    mockOnQuantityChange.mockClear();
  });

  test('renders quantity options', () => {
    render(<QuantitySelector selectedQuantity={0} onQuantityChange={mockOnQuantityChange} />);

    expect(screen.getByText('২টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('৫টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('১০টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('১৫টি বাক্য')).toBeInTheDocument();
    expect(screen.getByText('২০টি বাক্য')).toBeInTheDocument();
  });

  test('calls onQuantityChange when option is selected', () => {
    render(<QuantitySelector selectedQuantity={0} onQuantityChange={mockOnQuantityChange} />);

    const fiveOption = screen.getByRole('button', { name: /৫টি বাক্য/ });
    fireEvent.click(fiveOption);

    expect(mockOnQuantityChange).toHaveBeenCalledWith(5);
  });

  test('shows selected quantity with visual indicator', () => {
    render(<QuantitySelector selectedQuantity={10} onQuantityChange={mockOnQuantityChange} />);

    const tenOption = screen.getByRole('button', { name: /১০টি বাক্য/ });
    expect(tenOption).toHaveClass('border-current');
  });

  test('shows instructions when quantity is selected', () => {
    render(<QuantitySelector selectedQuantity={5} onQuantityChange={mockOnQuantityChange} />);

    expect(
      screen.getByText(/আপনি ৫টি বাক্য ট্রান্সক্রাইব করার জন্য নির্বাচন করেছেন/)
    ).toBeInTheDocument();
  });
});
