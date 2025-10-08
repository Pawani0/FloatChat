import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Container,
  Box,
  TextField,
  IconButton,
  Typography,
  Paper,
  Avatar,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Divider,
  Menu,
  MenuItem,
  Card,
  CardContent,
  CircularProgress,
  ThemeProvider,
  createTheme,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Send, Mic, Download, ArrowLeft, History, Waves, Droplets, MapPin, TrendingUp, Paperclip, Square, X, Plus, Trash2 } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import MarkdownTableRenderer from '../components/MarkdownTableRenderer';

// Dark theme matching Dashboard and HomePage
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3b82f6', light: '#60a5fa', dark: '#2563eb' },
    secondary: { main: '#22d3ee', light: '#67e8f9', dark: '#06b6d4' },
    background: { default: '#04060f', paper: 'rgba(255, 255, 255, 0.03)' },
    text: { primary: '#f3f4f6', secondary: '#9ca3af' },
    divider: 'rgba(255, 255, 255, 0.1)',
  },
});

// Suggested prompts
const suggestedPrompts = [
  { icon: <Waves size={20} />, title: 'Ocean Temperature', prompt: 'Show me temperature trends in the Arabian Sea' },
  { icon: <Droplets size={20} />, title: 'Salinity Analysis', prompt: 'Analyze salinity patterns in Bay of Bengal' },
  { icon: <MapPin size={20} />, title: 'Float Tracking', prompt: 'Track Argo float trajectories in Indian Ocean' },
  { icon: <TrendingUp size={20} />, title: 'Anomaly Detection', prompt: 'Detect temperature anomalies in recent data' },
];

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  hasVisualization?: boolean;
  visualizationData?: any;
  visualizationType?: 'line' | 'area' | 'bar' | 'table';
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
}

export function ChatBotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [isRecording, setIsRecording] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const initialSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      timestamp: new Date(),
    };
    setChatSessions([initialSession]);
    setCurrentSessionId(initialSession.id);
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call real ChatBot API
      const response = await fetch('http://34.93.9.34:8000/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const apiData = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: apiData.summary,
        timestamp: new Date(),
        hasVisualization: apiData.hasVisualization,
        visualizationData: apiData.data,
        visualizationType: apiData.visualizationType,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === currentSessionId
            ? {
                ...session,
                messages: [...session.messages, userMessage, assistantMessage],
                title: session.messages.length === 0 ? input.slice(0, 30) + '...' : session.title,
              }
            : session
        )
      );
    } catch (error) {
      console.error('ChatBot API error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error instanceof Error 
          ? `Sorry, I encountered an error: ${error.message}. 

🔧 Troubleshooting:
- Backend is now running on HTTPS at https://api.chikaz.com
- Please check your internet connection and try again
- If the problem persists, contact the administrator`
          : 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromptClick = (prompt: string) => {
    setInput(prompt);
  };

  const handleNewChat = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      timestamp: new Date(),
    };
    setChatSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    setMessages([]);
    setDrawerOpen(false);
  };

  const handleSessionClick = (sessionId: string) => {
    const session = chatSessions.find((s) => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setMessages(session.messages);
      setDrawerOpen(false);
    }
  };

  const handleDeleteSession = (sessionId: string) => {
    setChatSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (currentSessionId === sessionId) handleNewChat();
  };

  const handleVoiceInput = () => {
    if (!isRecording) {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        setInput('What is the current temperature in Arabian Sea?');
      }, 2000);
    } else {
      setIsRecording(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: `Uploaded file: ${file.name}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
    }
  };

  const handleExportChat = () => {
    const currentSession = chatSessions.find((s) => s.id === currentSessionId);
    if (currentSession) {
      const chatText = currentSession.messages
        .map((msg) => `${msg.role.toUpperCase()}: ${msg.content}`)
        .join('\n\n');
      const blob = new Blob([chatText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-${currentSession.id}.txt`;
      a.click();
    }
    setExportDialogOpen(false);
  };

  const renderVisualization = (message: Message) => {
    if (!message.hasVisualization || !message.visualizationData) return null;

    const data = message.visualizationData;

    return (
      <Card elevation={0} sx={{ mt: 2, bgcolor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              {message.visualizationType === 'line' ? (
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                  <XAxis dataKey="name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(4, 6, 15, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px' }} />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6' }} />
                </LineChart>
              ) : message.visualizationType === 'area' ? (
                <AreaChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                  <XAxis dataKey="name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(4, 6, 15, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px' }} />
                  <Legend />
                  <Area type="monotone" dataKey="value" stroke="#22d3ee" fill="rgba(34, 211, 238, 0.2)" />
                </AreaChart>
              ) : (
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                  <XAxis dataKey="name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(4, 6, 15, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px' }} />
                  <Legend />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              )}
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ minHeight: '100vh', bgcolor: '#04060f', position: 'relative', display: 'flex', flexDirection: 'column',
        '&::before': { content: '""', position: 'absolute', inset: 0, background: 'radial-gradient(circle at top, rgba(59,130,246,0.12), transparent 55%), radial-gradient(circle at bottom, rgba(14,116,144,0.16), transparent 60%)', pointerEvents: 'none', zIndex: 0 }
      }}>
        {/* Header */}
        <Box sx={{ position: 'sticky', top: 0, zIndex: 50, backdropFilter: 'blur(16px)', bgcolor: 'rgba(4, 6, 15, 0.8)', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Container maxWidth="xl">
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.375rem 0.75rem', borderRadius: '9999px', border: '1px solid rgba(255, 255, 255, 0.15)', fontSize: '0.875rem', color: '#d1d5db', textDecoration: 'none', transition: 'all 0.2s' }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)'; e.currentTarget.style.color = '#ffffff'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)'; e.currentTarget.style.color = '#d1d5db'; }}>
                  <ArrowLeft size={14} /> Back to Home
                </Link>
                <Typography variant="h6" sx={{ fontWeight: 600, background: 'linear-gradient(to right, #60a5fa, #67e8f9)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                  FloatChat Assistant
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton onClick={() => setDrawerOpen(true)} sx={{ color: '#9ca3af', '&:hover': { color: '#60a5fa', bgcolor: 'rgba(59, 130, 246, 0.1)' } }}>
                  <History />
                </IconButton>
                <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} sx={{ color: '#9ca3af', '&:hover': { color: '#60a5fa', bgcolor: 'rgba(59, 130, 246, 0.1)' } }}>
                  <Download />
                </IconButton>
              </Box>
            </Box>
          </Container>
        </Box>

        {/* Main Chat Area */}
        <Box sx={{ flex: 1, overflow: 'auto', position: 'relative', zIndex: 1 }}>
          <Container maxWidth="lg" sx={{ py: 4 }}>
            {messages.length === 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 4 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" sx={{ fontWeight: 700, mb: 2, background: 'linear-gradient(to right, #60a5fa, #67e8f9)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                    Welcome to FloatChat
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    Your AI-powered ocean data analyst
                  </Typography>
                </Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2, width: '100%', maxWidth: '800px' }}>
                  {suggestedPrompts.map((prompt, index) => (
                    <Card key={index} elevation={0} sx={{ bgcolor: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', cursor: 'pointer', transition: 'all 0.2s',
                      '&:hover': { bgcolor: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.3)', transform: 'translateY(-2px)' }
                    }} onClick={() => handlePromptClick(prompt.prompt)}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                          <Box sx={{ color: '#60a5fa', display: 'flex', alignItems: 'center' }}>{prompt.icon}</Box>
                          <Typography variant="subtitle1" fontWeight={600}>{prompt.title}</Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">{prompt.prompt}</Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </Box>
            ) : (
              <Box sx={{ pb: 2 }}>
                {messages.map((message) => (
                  <Box key={message.id} sx={{ display: 'flex', justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start', mb: 3 }}>
                    <Box sx={{ display: 'flex', gap: 2, maxWidth: '80%', flexDirection: message.role === 'user' ? 'row-reverse' : 'row' }}>
                      <Avatar sx={{ bgcolor: message.role === 'user' ? '#3b82f6' : '#22d3ee', width: 36, height: 36 }}>
                        {message.role === 'user' ? 'U' : 'AI'}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Paper elevation={0} sx={{ p: 2, bgcolor: message.role === 'user' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 2 }}>
                          <MarkdownTableRenderer content={message.content} />
                          {renderVisualization(message)}
                        </Paper>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                ))}
                {isLoading && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Avatar sx={{ bgcolor: '#22d3ee', width: 36, height: 36 }}>AI</Avatar>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 2 }}>
                      <CircularProgress size={20} />
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Box>
            )}
          </Container>
        </Box>

        {/* Input Area */}
        <Box sx={{ position: 'sticky', bottom: 0, zIndex: 10, bgcolor: 'rgba(4, 6, 15, 0.95)', backdropFilter: 'blur(16px)', borderTop: '1px solid rgba(255, 255, 255, 0.1)', py: 2 }}>
          <Container maxWidth="lg">
            <Paper elevation={0} sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, bgcolor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 3 }}>
              <IconButton size="small" onClick={() => fileInputRef.current?.click()} sx={{ color: '#9ca3af', '&:hover': { color: '#60a5fa' } }}>
                <Paperclip fontSize="small" />
              </IconButton>
              <input ref={fileInputRef} type="file" hidden onChange={handleFileUpload} accept="image/*,.csv,.json" />
              <TextField fullWidth multiline maxRows={4} value={input} onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }}}
                placeholder="Ask about ocean data, temperature, salinity, or floats..."
                variant="standard" InputProps={{ disableUnderline: true, sx: { color: '#f3f4f6', fontSize: '0.95rem' } }}
                sx={{ '& .MuiInputBase-input::placeholder': { color: '#6b7280', opacity: 1 } }}
              />
              <IconButton size="small" onClick={handleVoiceInput} sx={{ color: isRecording ? '#ef4444' : '#9ca3af', '&:hover': { color: isRecording ? '#dc2626' : '#60a5fa' } }}>
                {isRecording ? <Square fontSize="small" /> : <Mic fontSize="small" />}
              </IconButton>
              <IconButton onClick={handleSendMessage} disabled={!input.trim() || isLoading} sx={{ bgcolor: '#3b82f6', color: 'white', '&:hover': { bgcolor: '#2563eb' }, '&:disabled': { bgcolor: 'rgba(59, 130, 246, 0.3)' } }}>
                <Send fontSize="small" />
              </IconButton>
            </Paper>
          </Container>
        </Box>

        {/* Chat History Drawer */}
        <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)} PaperProps={{ sx: { width: 300, bgcolor: 'rgba(4, 6, 15, 0.98)', borderRight: '1px solid rgba(255, 255, 255, 0.1)' } }}>
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>Chat History</Typography>
              <IconButton size="small" onClick={() => setDrawerOpen(false)}><X fontSize="small" /></IconButton>
            </Box>
            <Button fullWidth variant="contained" startIcon={<Plus />} onClick={handleNewChat} sx={{ mb: 2, bgcolor: '#3b82f6', '&:hover': { bgcolor: '#2563eb' } }}>
              New Chat
            </Button>
            <Divider sx={{ mb: 2 }} />
            <List>
              {chatSessions.map((session) => (
                <ListItem key={session.id} disablePadding secondaryAction={
                  <IconButton edge="end" size="small" onClick={() => handleDeleteSession(session.id)} sx={{ color: '#9ca3af', '&:hover': { color: '#ef4444' } }}>
                    <Trash2 fontSize="small" />
                  </IconButton>
                }>
                  <ListItemButton selected={session.id === currentSessionId} onClick={() => handleSessionClick(session.id)}
                    sx={{ borderRadius: 1, '&.Mui-selected': { bgcolor: 'rgba(59, 130, 246, 0.15)', '&:hover': { bgcolor: 'rgba(59, 130, 246, 0.2)' } } }}>
                    <ListItemText primary={session.title} secondary={session.timestamp.toLocaleDateString()} primaryTypographyProps={{ noWrap: true }} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>

        {/* Export Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)} PaperProps={{ sx: { bgcolor: 'rgba(4, 6, 15, 0.98)', border: '1px solid rgba(255, 255, 255, 0.1)' } }}>
          <MenuItem onClick={() => { setExportDialogOpen(true); setAnchorEl(null); }}>Export as Text</MenuItem>
          <MenuItem onClick={() => setAnchorEl(null)}>Export as JSON</MenuItem>
        </Menu>

        {/* Export Dialog */}
        <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)} PaperProps={{ sx: { bgcolor: 'rgba(4, 6, 15, 0.98)', border: '1px solid rgba(255, 255, 255, 0.1)' } }}>
          <DialogTitle>Export Chat</DialogTitle>
          <DialogContent><Typography>Export your current chat session as a text file?</Typography></DialogContent>
          <DialogActions>
            <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleExportChat} variant="contained">Export</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ThemeProvider>
  );
}
