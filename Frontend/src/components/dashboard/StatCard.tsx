import { FC, ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  title: string;
  value: string | number;
  loading: boolean;
  color: string;
}

export const StatCard: FC<StatCardProps> = ({ icon, title, value, loading, color }) => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-lg border border-slate-700/50 rounded-xl p-4 flex items-center shadow-lg transition-all duration-300 hover:bg-slate-700/60 hover:shadow-cyan-500/10">
      <div className={`mr-4 text-3xl ${color}`}>
        {icon}
      </div>
      <div>
        <div className="font-bold text-xs text-slate-400 uppercase tracking-wider">{title}</div>
        <div className="text-2xl font-bold text-white">
          {loading ? <span className="animate-pulse">...</span> : value}
        </div>
      </div>
    </div>
  );
};
