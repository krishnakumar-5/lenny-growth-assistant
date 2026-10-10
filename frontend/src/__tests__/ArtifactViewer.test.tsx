import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ArtifactViewer } from '../components/ArtifactViewer';
import { Ship30Response } from '../types/api';

describe('ArtifactViewer Component', () => {
  it('renders nothing when artifact is null', () => {
    const { container } = render(<ArtifactViewer artifact={null} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders essay preview, word count constraint badge, and attribution', () => {
    const onClose = vi.fn();
    const mockArtifact: Ship30Response = {
      title: 'Stop Obsessing Over Acquisition',
      hook: 'Most early-stage startups obsess over acquisition while users bleed out.',
      word_count: 245,
      within_constraints: true,
      content_markdown: '# Stop Obsessing Over Acquisition\n\nFull essay text here.\n\nKey takeaways.',
      content_html: '<h1>Stop Obsessing Over Acquisition</h1><p>Full essay HTML</p>',
      guest_attribution: 'Elena Verna',
      sources: [
        {
          chunk_id: 'c-1',
          transcript_id: 't-1',
          transcript_title: 'Elena Verna on PLG',
          source_filename: 'elena_verna.md',
          chunk_index: 0,
          chunk_text: 'Retention precedes acquisition.',
          score: 35.0,
          metadata: {},
        },
      ],
      created_at: '2026-10-10T00:00:00Z',
    };

    render(<ArtifactViewer artifact={mockArtifact} onClose={onClose} />);

    expect(screen.getAllByText('Stop Obsessing Over Acquisition').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Elena Verna/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/245 words • Ship 30 Compliant/i)).toBeDefined();
    expect(screen.getByText('Elena Verna on PLG (#0)')).toBeDefined();

    // Tab switching to HTML Card
    const htmlTab = screen.getByText('HTML Card (Isolated)');
    fireEvent.click(htmlTab);
    const iframe = screen.getByTitle('Sanitized HTML Artifact Preview') as HTMLIFrameElement;
    expect(iframe).toBeDefined();
    expect(iframe.getAttribute('sandbox')).toBe('');

    // Tab switching to Raw Markdown
    const rawTab = screen.getByText('Raw Markdown');
    fireEvent.click(rawTab);
    expect(screen.getByText(/Full essay text here/i)).toBeDefined();
  });
});
