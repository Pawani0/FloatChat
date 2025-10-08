import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
} from '@mui/material';

interface MarkdownTableRendererProps {
  content: string;
}

interface ParsedTable {
  headers: string[];
  rows: string[][];
}

const parseMarkdownTable = (tableText: string): ParsedTable | null => {
  const lines = tableText.trim().split('\n');
  if (lines.length < 3) return null;

  // Extract headers (first line)
  const headers = lines[0]
    .split('|')
    .map(h => h.trim())
    .filter(h => h.length > 0);

  // Skip separator line (second line with dashes)
  // Extract data rows (remaining lines)
  const rows: string[][] = [];
  for (let i = 2; i < lines.length; i++) {
    const cells = lines[i]
      .split('|')
      .map(c => c.trim())
      .filter(c => c.length > 0);
    
    if (cells.length > 0) {
      rows.push(cells);
    }
  }

  return { headers, rows };
};

const MarkdownTableRenderer: React.FC<MarkdownTableRendererProps> = ({ content }) => {
  // Check if content contains markdown table
  const hasTable = content.includes('|') && content.includes('---');

  if (!hasTable) {
    // No table found, render as regular text
    return (
      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
        {content}
      </Typography>
    );
  }

  // Split content into parts (text before table, table, text after table)
  const parts: (string | ParsedTable)[] = [];
  const lines = content.split('\n');
  let currentText: string[] = [];
  let inTable = false;
  let tableLines: string[] = [];

  for (const line of lines) {
    if (line.includes('|') && !inTable) {
      // Start of table
      if (currentText.length > 0) {
        parts.push(currentText.join('\n'));
        currentText = [];
      }
      inTable = true;
      tableLines.push(line);
    } else if (inTable && line.includes('|')) {
      // Continue table
      tableLines.push(line);
    } else if (inTable && !line.includes('|')) {
      // End of table
      const parsed = parseMarkdownTable(tableLines.join('\n'));
      if (parsed) {
        parts.push(parsed);
      }
      tableLines = [];
      inTable = false;
      if (line.trim()) {
        currentText.push(line);
      }
    } else {
      // Regular text
      currentText.push(line);
    }
  }

  // Handle remaining content
  if (inTable && tableLines.length > 0) {
    const parsed = parseMarkdownTable(tableLines.join('\n'));
    if (parsed) {
      parts.push(parsed);
    }
  }
  if (currentText.length > 0) {
    parts.push(currentText.join('\n'));
  }

  return (
    <Box>
      {parts.map((part, index) => {
        if (typeof part === 'string') {
          // Render text
          return (
            <Typography
              key={index}
              variant="body1"
              sx={{ whiteSpace: 'pre-wrap', mb: part.trim().length > 0 ? 2 : 0 }}
            >
              {part}
            </Typography>
          );
        } else {
          // Render table
          return (
            <TableContainer
              key={index}
              component={Paper}
              elevation={0}
              sx={{
                mb: 2,
                mt: 2,
                bgcolor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 2,
                maxHeight: 400,
                maxWidth: '100%',
                overflowX: 'auto',
                overflowY: 'auto',
                '&::-webkit-scrollbar': {
                  width: '8px',
                  height: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                },
                '&::-webkit-scrollbar-thumb': {
                  bgcolor: 'rgba(59, 130, 246, 0.5)',
                  borderRadius: '4px',
                  '&:hover': {
                    bgcolor: 'rgba(59, 130, 246, 0.7)',
                  },
                },
              }}
            >
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    {part.headers.map((header, i) => (
                      <TableCell
                        key={i}
                        sx={{
                          bgcolor: 'rgba(59, 130, 246, 0.15)',
                          color: '#60a5fa',
                          fontWeight: 600,
                          borderBottom: '2px solid rgba(59, 130, 246, 0.3)',
                          fontSize: '0.875rem',
                        }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {part.rows.map((row, rowIndex) => (
                    <TableRow
                      key={rowIndex}
                      sx={{
                        '&:nth-of-type(even)': {
                          bgcolor: 'rgba(255, 255, 255, 0.02)',
                        },
                        '&:hover': {
                          bgcolor: 'rgba(59, 130, 246, 0.08)',
                        },
                      }}
                    >
                      {row.map((cell, cellIndex) => (
                        <TableCell
                          key={cellIndex}
                          sx={{
                            color: '#d1d5db',
                            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                            fontSize: '0.875rem',
                          }}
                        >
                          {cell}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          );
        }
      })}
    </Box>
  );
};

export default MarkdownTableRenderer;
