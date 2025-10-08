import { Plus, Settings, User, MessageSquare, Clock, Calendar } from 'lucide-react';
import { ChatMessage } from '../types/ocean';

interface SidebarProps {
  messages: ChatMessage[];
  onNewChat: () => void;
  onShowSettings: () => void;
  variant?: 'light' | 'dark';
}

export function Sidebar({ messages, onNewChat, onShowSettings, variant = 'light' }: SidebarProps) {
  const isDark = variant === 'dark';

  const groupMessagesByDate = (messages: ChatMessage[]) => {
    const groups: Record<string, ChatMessage[]> = {};
    const now = new Date();
    const today = now.toDateString();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString();
    
    messages.forEach(msg => {
      const msgDate = msg.timestamp.toDateString();
      let groupKey: string;
      
      if (msgDate === today) {
        groupKey = 'Today';
      } else if (msgDate === yesterday) {
        groupKey = 'Yesterday';
      } else {
        const daysAgo = Math.floor((now.getTime() - msg.timestamp.getTime()) / (24 * 60 * 60 * 1000));
        if (daysAgo <= 7) {
          groupKey = 'Previous 7 days';
        } else if (daysAgo <= 30) {
          groupKey = 'Previous 30 days';
        } else {
          groupKey = 'Older';
        }
      }
      
      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(msg);
    });
    
    return groups;
  };

  const messageGroups = groupMessagesByDate(messages.filter(m => m.type === 'user'));

  const baseText = isDark ? 'text-gray-100' : 'text-gray-800';
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-500';

  const containerClasses = `w-72 flex flex-col h-full ${
    isDark ? 'bg-white/[0.04] border-r border-white/10 text-gray-100' : 'bg-gray-50 border-r border-gray-200 text-gray-800'
  }`;

  const sectionBorder = isDark ? 'border-white/10' : 'border-gray-200';
  const historyHover = isDark ? 'hover:bg-white/10' : 'hover:bg-gray-100';
  const ctaButton = isDark
    ? 'bg-gradient-to-r from-blue-500/70 to-cyan-400/60 text-white hover:from-blue-400 hover:to-cyan-300'
    : 'bg-blue-600 text-white hover:bg-blue-700';
  const footerButton = isDark ? 'text-gray-300 hover:bg-white/10' : 'text-gray-600 hover:bg-gray-100';

  return (
    <div className={containerClasses}>
      <div className={`p-4 border-b ${sectionBorder}`}>
        <button
          onClick={onNewChat}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${ctaButton}`}
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {Object.entries(messageGroups).map(([group, groupMessages]) => (
          <div key={group} className="mb-6">
            <h3
              className={`text-xs font-medium uppercase tracking-wider mb-2 flex items-center gap-1 ${
                isDark ? 'text-gray-300' : 'text-gray-500'
              }`}
            >
              {group === 'Today' && <Clock className="w-3 h-3" />}
              {group === 'Yesterday' && <Calendar className="w-3 h-3" />}
              {group.includes('Previous') && <Calendar className="w-3 h-3" />}
              {group}
            </h3>
            <div className="space-y-1">
              {groupMessages.slice(0, 5).map((msg) => (
                <button
                  key={msg.id}
                  className={`w-full text-left p-2 rounded-md transition-colors group ${historyHover}`}
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare className={`w-4 h-4 mt-0.5 flex-shrink-0 ${subtleText}`} />
                    <div className="min-w-0 flex-1">
                      <p className={`text-sm truncate ${baseText}`}>
                        {msg.content.length > 40 ? `${msg.content.slice(0, 40)}...` : msg.content}
                      </p>
                      <p className={`text-xs ${subtleText}`}>
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}

        {Object.keys(messageGroups).length === 0 && (
          <div className="text-center py-8">
            <MessageSquare className={`w-8 h-8 mx-auto mb-2 ${isDark ? 'text-gray-500' : 'text-gray-300'}`} />
            <p className={`text-sm ${subtleText}`}>No chat history yet</p>
            <p className={`text-xs mt-1 ${subtleText}`}>Start a conversation to see your chats here</p>
          </div>
        )}
      </div>

      <div className={`p-4 space-y-2 border-t ${sectionBorder}`}>
      <button
          onClick={onShowSettings}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${footerButton}`}
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>
        <button className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${footerButton}`}>
          <User className="w-4 h-4" />
          Profile
        </button>
      </div>
    </div>
  );
}