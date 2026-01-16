import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BatchFeedback } from '../BatchFeedback';
import { TranslatedError } from '../../../../../types/errors';

describe('BatchFeedback Component', () => {
  describe('Rendering Behavior', () => {
    it('should render nothing when no error or success provided', () => {
      const { container } = render(<BatchFeedback />);
      expect(container.firstChild).toBeNull();
    });

    it('should render nothing when error and success are null', () => {
      const { container } = render(<BatchFeedback error={null} success={null} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Success Message Rendering', () => {
    it('should render success message when provided', () => {
      const successMessage = 'Export batch created successfully!';
      render(<BatchFeedback success={successMessage} />);

      expect(screen.getByText(successMessage)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-success');
    });

    it('should display success icon with success message', () => {
      render(<BatchFeedback success="Success!" />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();

      // Check for CheckCircleIcon (svg element)
      const svg = alert.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should have proper accessibility attributes for success', () => {
      render(<BatchFeedback success="Success!" />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Error Title Rendering', () => {
    it('should render error title', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks for batch creation',
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Insufficient chunks for batch creation')).toBeInTheDocument();
    });

    it('should render error with proper styling', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
      };

      render(<BatchFeedback error={error} />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-destructive');
      expect(alert).toHaveClass('border-destructive-border');
      expect(alert).toHaveClass('text-destructive-foreground');
    });

    it('should display error icon with error message', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
      };

      render(<BatchFeedback error={error} />);

      const alert = screen.getByRole('alert');

      // Check for ExclamationTriangleIcon (svg element)
      const svg = alert.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should render error title with aria-label', () => {
      const error: TranslatedError = {
        title: 'Test error title',
      };

      render(<BatchFeedback error={error} />);

      const errorTitle = screen.getByLabelText('Error message');
      expect(errorTitle).toHaveTextContent('Test error title');
    });
  });

  describe('Error Message Rendering', () => {
    it('should render optional error message when provided', () => {
      const error: TranslatedError = {
        title: 'Error title',
        message: 'This is a detailed error message explaining what went wrong.',
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Error title')).toBeInTheDocument();
      expect(
        screen.getByText('This is a detailed error message explaining what went wrong.')
      ).toBeInTheDocument();
    });

    it('should not render message section when message is not provided', () => {
      const error: TranslatedError = {
        title: 'Error title',
      };

      const { container } = render(<BatchFeedback error={error} />);

      // Only the title should be present, no additional message paragraph
      const paragraphs = container.querySelectorAll('p');
      expect(paragraphs).toHaveLength(1); // Only the title paragraph
    });
  });

  describe('Error Details Rendering - Insufficient Chunks', () => {
    it('should render insufficient chunks context', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Context:')).toBeInTheDocument();
      expect(screen.getByText(/Available chunks:/)).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText(/Required chunks:/)).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('should render user role when provided in insufficient chunks context', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks',
        details: {
          available_chunks: 45,
          required_chunks: 50,
          user_role: 'sworik_developer',
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText(/Your role:/)).toBeInTheDocument();
      expect(screen.getByText('sworik_developer')).toBeInTheDocument();
    });

    it('should not render user role when not provided', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText(/Your role:/)).not.toBeInTheDocument();
    });

    it('should have proper accessibility attributes for error context', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
      };

      render(<BatchFeedback error={error} />);

      const contextRegion = screen.getByLabelText('Error context');
      expect(contextRegion).toBeInTheDocument();
      expect(contextRegion).toHaveAttribute('role', 'region');
    });
  });

  describe('Error Details Rendering - Quota Exceeded', () => {
    it('should render quota status context', () => {
      const error: TranslatedError = {
        title: 'Quota exceeded',
        details: {
          downloads_today: 10,
          daily_limit: 10,
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Quota Status:')).toBeInTheDocument();
      expect(screen.getByText(/Downloads today:/)).toBeInTheDocument();
      expect(screen.getByText('10/10')).toBeInTheDocument();
    });

    it('should render reset time when provided', () => {
      const resetTime = '2024-01-16T00:00:00Z';
      const error: TranslatedError = {
        title: 'Quota exceeded',
        details: {
          downloads_today: 10,
          daily_limit: 10,
          reset_time: resetTime,
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText(/Resets at:/)).toBeInTheDocument();
      // The date will be formatted by toLocaleString()
      const formattedDate = new Date(resetTime).toLocaleString();
      expect(screen.getByText(formattedDate)).toBeInTheDocument();
    });

    it('should render hours until reset when provided', () => {
      const error: TranslatedError = {
        title: 'Quota exceeded',
        details: {
          downloads_today: 10,
          daily_limit: 10,
          hours_until_reset: 5,
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText(/Time remaining:/)).toBeInTheDocument();
      expect(screen.getByText('5 hours')).toBeInTheDocument();
    });

    it('should have proper accessibility attributes for quota status', () => {
      const error: TranslatedError = {
        title: 'Quota exceeded',
        details: {
          downloads_today: 10,
          daily_limit: 10,
        },
      };

      render(<BatchFeedback error={error} />);

      const quotaRegion = screen.getByLabelText('Quota status');
      expect(quotaRegion).toBeInTheDocument();
      expect(quotaRegion).toHaveAttribute('role', 'region');
    });
  });

  describe('Suggestions Rendering', () => {
    it('should render suggestions list', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
        suggestions: [
          'Wait for more chunks to be processed',
          'Contact an admin for assistance',
          'Try adjusting your filters',
        ],
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Wait for more chunks to be processed')).toBeInTheDocument();
      expect(screen.getByText('Contact an admin for assistance')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument();
    });

    it('should render suggestions with proper list structure', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
        suggestions: ['Suggestion 1', 'Suggestion 2'],
      };

      render(<BatchFeedback error={error} />);

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(2);
    });

    it('should not render suggestions section when suggestions array is empty', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
        suggestions: [],
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText('Suggestions:')).not.toBeInTheDocument();
    });

    it('should not render suggestions section when suggestions is undefined', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText('Suggestions:')).not.toBeInTheDocument();
    });

    it('should have proper accessibility attributes for suggestions', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
        suggestions: ['Suggestion 1'],
      };

      render(<BatchFeedback error={error} />);

      const suggestionsRegion = screen.getByLabelText('Suggestions to resolve error');
      expect(suggestionsRegion).toBeInTheDocument();
      expect(suggestionsRegion).toHaveAttribute('role', 'region');
    });

    it('should display lightbulb icon with suggestions', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
        suggestions: ['Suggestion 1'],
      };

      render(<BatchFeedback error={error} />);

      const suggestionsRegion = screen.getByLabelText('Suggestions to resolve error');

      // Check for LightBulbIcon (svg element)
      const svg = suggestionsRegion.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Conditional Rendering Based on Error Structure', () => {
    it('should render only title when no other fields provided', () => {
      const error: TranslatedError = {
        title: 'Simple error',
      };

      const { container } = render(<BatchFeedback error={error} />);

      expect(screen.getByText('Simple error')).toBeInTheDocument();
      expect(screen.queryByText('Context:')).not.toBeInTheDocument();
      expect(screen.queryByText('Quota Status:')).not.toBeInTheDocument();
      expect(screen.queryByText('Suggestions:')).not.toBeInTheDocument();

      // Should only have the main alert div and title
      const regions = container.querySelectorAll('[role="region"]');
      expect(regions).toHaveLength(0);
    });

    it('should render all sections when all fields provided', () => {
      const error: TranslatedError = {
        title: 'Complete error',
        message: 'Detailed message',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
        suggestions: ['Suggestion 1', 'Suggestion 2'],
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByText('Complete error')).toBeInTheDocument();
      expect(screen.getByText('Detailed message')).toBeInTheDocument();
      expect(screen.getByText('Context:')).toBeInTheDocument();
      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
    });

    it('should not render details section when details object is empty', () => {
      const error: TranslatedError = {
        title: 'Error',
        details: {},
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText('Context:')).not.toBeInTheDocument();
      expect(screen.queryByText('Quota Status:')).not.toBeInTheDocument();
    });

    it('should not render insufficient chunks context when only partial fields present', () => {
      const error: TranslatedError = {
        title: 'Error',
        details: {
          available_chunks: 45,
          // missing required_chunks
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText('Context:')).not.toBeInTheDocument();
    });

    it('should not render quota context when only partial fields present', () => {
      const error: TranslatedError = {
        title: 'Error',
        details: {
          downloads_today: 10,
          // missing daily_limit
        },
      };

      render(<BatchFeedback error={error} />);

      expect(screen.queryByText('Quota Status:')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility Attributes', () => {
    it('should have proper ARIA attributes for error alert', () => {
      const error: TranslatedError = {
        title: 'Error occurred',
      };

      render(<BatchFeedback error={error} />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'assertive');
      expect(alert).toHaveAttribute('aria-atomic', 'true');
    });

    it('should have proper ARIA attributes for success alert', () => {
      render(<BatchFeedback success="Success!" />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
      expect(alert).not.toHaveAttribute('aria-atomic');
    });

    it('should mark decorative icons as aria-hidden', () => {
      const error: TranslatedError = {
        title: 'Error',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
        suggestions: ['Suggestion'],
      };

      const { container } = render(<BatchFeedback error={error} />);

      // All icons should be aria-hidden
      const icons = container.querySelectorAll('svg');
      icons.forEach(icon => {
        expect(icon).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('should provide descriptive aria-labels for regions', () => {
      const error: TranslatedError = {
        title: 'Error',
        details: {
          available_chunks: 45,
          required_chunks: 50,
        },
        suggestions: ['Suggestion'],
      };

      render(<BatchFeedback error={error} />);

      expect(screen.getByLabelText('Error message')).toBeInTheDocument();
      expect(screen.getByLabelText('Error context')).toBeInTheDocument();
      expect(screen.getByLabelText('Suggestions to resolve error')).toBeInTheDocument();
    });
  });

  describe('Complex Error Scenarios', () => {
    it('should handle error with both insufficient chunks and suggestions', () => {
      const error: TranslatedError = {
        title: 'Insufficient chunks for batch creation',
        message: 'Not enough audio chunks are available.',
        details: {
          available_chunks: 45,
          required_chunks: 50,
          user_role: 'sworik_developer',
        },
        suggestions: ['Wait for more chunks to be processed', 'Contact an admin'],
      };

      render(<BatchFeedback error={error} />);

      // Verify all sections are rendered
      expect(screen.getByText('Insufficient chunks for batch creation')).toBeInTheDocument();
      expect(screen.getByText('Not enough audio chunks are available.')).toBeInTheDocument();
      expect(screen.getByText('Context:')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('sworik_developer')).toBeInTheDocument();
      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Wait for more chunks to be processed')).toBeInTheDocument();
      expect(screen.getByText('Contact an admin')).toBeInTheDocument();
    });

    it('should handle error with quota details and suggestions', () => {
      const error: TranslatedError = {
        title: 'Daily download limit exceeded',
        message: 'You have reached your daily download limit.',
        details: {
          downloads_today: 10,
          daily_limit: 10,
          reset_time: '2024-01-16T00:00:00Z',
          hours_until_reset: 5,
        },
        suggestions: ['Wait until quota resets', 'Contact an admin if urgent'],
      };

      render(<BatchFeedback error={error} />);

      // Verify all sections are rendered
      expect(screen.getByText('Daily download limit exceeded')).toBeInTheDocument();
      expect(screen.getByText('You have reached your daily download limit.')).toBeInTheDocument();
      expect(screen.getByText('Quota Status:')).toBeInTheDocument();
      expect(screen.getByText('10/10')).toBeInTheDocument();
      expect(screen.getByText(/Resets at:/)).toBeInTheDocument();
      expect(screen.getByText('5 hours')).toBeInTheDocument();
      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Wait until quota resets')).toBeInTheDocument();
      expect(screen.getByText('Contact an admin if urgent')).toBeInTheDocument();
    });
  });
});
