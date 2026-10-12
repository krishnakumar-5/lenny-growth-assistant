import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ContextPanel } from '../components/ContextPanel';
import { SourceCitation } from '../types/api';

describe('ContextPanel Component', () => {
  const mockSources: SourceCitation[] = [
    {
      chunk_id: 'c-101',
      transcript_id: 't-101',
      transcript_title: 'Elena Verna on PLG & Reverse Trials',
      source_filename: 'elena_verna.md',
      chunk_index: 3,
      chunk_text: 'A reverse trial provides premium access upfront.',
      score: 48.6,
      metadata: {
        guest: 'Elena Verna',
        episode: 88,
        source_url: 'https://www.lennysnewsletter.com/p/elena-verna',
        youtube_url: 'https://youtube.com/watch?v=12345',
      },
    },
  ];

  it('renders context panel with citations, metadata, and external links', () => {
    const onSelectCitation = vi.fn();
    const onClose = vi.fn();

    render(
      <ContextPanel
        isOpen={true}
        onClose={onClose}
        sources={mockSources}
        onSelectCitation={onSelectCitation}
        latestArtifact={null}
        onOpenArtifact={vi.fn()}
      />
    );

    expect(screen.getByText('Context & Provenance')).toBeDefined();
    expect(screen.getByText('Elena Verna on PLG & Reverse Trials')).toBeDefined();
    expect(screen.getAllByText(/Elena Verna/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Substack Post')).toBeDefined();
    expect(screen.getByText('YouTube')).toBeDefined();

    // Click citation to inspect
    const citationCard = screen.getByText('Elena Verna on PLG & Reverse Trials');
    fireEvent.click(citationCard);
    expect(onSelectCitation).toHaveBeenCalledWith(mockSources[0]);
  });

  it('renders empty state when no sources are active', () => {
    render(
      <ContextPanel
        isOpen={true}
        onClose={vi.fn()}
        sources={[]}
        latestArtifact={null}
        onOpenArtifact={vi.fn()}
      />
    );

    expect(screen.getByText('No active turn selected')).toBeDefined();
  });
});
