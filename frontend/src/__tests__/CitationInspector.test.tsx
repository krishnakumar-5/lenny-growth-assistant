import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CitationInspector } from '../components/CitationInspector';
import { SourceCitation } from '../types/api';

describe('CitationInspector Component', () => {
  it('renders nothing when citation is null', () => {
    const { container } = render(<CitationInspector citation={null} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders citation details and synthetic disclaimer correctly', () => {
    const onClose = vi.fn();
    const citation: SourceCitation = {
      chunk_id: 'chunk-999',
      transcript_id: 'trans-111',
      transcript_title: 'Growth Accounting & Retention Loops',
      source_filename: 'sample_fixture.md',
      chunk_index: 2,
      chunk_text: 'This is the verified chunk excerpt explaining cohort metrics.',
      score: 41.2,
      metadata: {
        guest: 'Elena Verna',
        episode: 42,
        synthetic_test_data: true,
      },
    };

    render(<CitationInspector citation={citation} onClose={onClose} />);

    expect(screen.getByText('Growth Accounting & Retention Loops')).toBeDefined();
    expect(screen.getByText('Elena Verna')).toBeDefined();
    expect(screen.getByText('42')).toBeDefined();
    expect(screen.getByText('Synthetic Benchmark Test Data:')).toBeDefined();
    expect(screen.getByText('Score: 41.2')).toBeDefined();
    expect(screen.getByText(/This is the verified chunk excerpt/i)).toBeDefined();

    const closeBtn = screen.getByText('Close Inspector');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });
});
