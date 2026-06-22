import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { RefreshCw, CheckCircle2, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { integrationsService } from '../../services/integrations';

export default function Header() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [syncing, setSyncing] = useState(false);
  const [synced, setSynced] = useState(false);

  const getPageTitle = (path: string) => {
    switch (path) {
      case '/':
        return 'Briefing Hub';
      case '/connect':
        return 'App Connections';
      case '/history':
        return 'History Logs';
      case '/insights':
        return 'Metrics & Insights';
      case '/settings':
        return 'System Settings';
      default:
        return 'FlowBrain';
    }
  };

  const handleSync = async () => {
    if (syncing) return;
    setSyncing(true);
    setSynced(false);
    try {
      await integrationsService.syncAll();
      setSynced(true);
      setTimeout(() => setSynced(false), 3000); // Reset synced status after 3s
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="h-16 bg-[#0D1117]/80 backdrop-blur-md border-b border-[#1C2A3A] flex items-center justify-between px-8 z-10">
      {/* Title */}
      <h1 className="text-xl font-bold font-heading text-white tracking-tight">
        {getPageTitle(location.pathname)}
      </h1>

      {/* Control Actions */}
      <div className="flex items-center gap-6">
        {/* Sync Trigger */}
        <button
          onClick={handleSync}
          disabled={syncing}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-200 ${
            syncing
              ? 'bg-brandPurple/10 border-brandPurple text-brandPurple cursor-not-allowed'
              : synced
              ? 'bg-brandGreen/10 border-brandGreen text-brandGreen'
              : 'bg-transparent border-[#1C2A3A] hover:border-brandPurple text-[#E2EBF9]'
          }`}
        >
          {syncing ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : synced ? (
            <CheckCircle2 size={14} />
          ) : (
            <RefreshCw size={14} />
          )}
          <span>{syncing ? 'Syncing...' : synced ? 'Synced' : 'Sync Signal'}</span>
        </button>

        {/* User Badge */}
        {user && (
          <div className="flex items-center gap-4 border-l border-[#1C2A3A] pl-6">
            <div className="flex flex-col text-right">
              <span className="text-xs font-semibold text-[#E2EBF9]">{user.name}</span>
              <span className="text-[10px] text-gray-400 font-medium">{user.email}</span>
            </div>
            <img
              src={user.avatar_url}
              alt={user.name}
              className="w-9 h-9 rounded-full border border-brandPurple/50 shadow-md shadow-brandPurple/10 object-cover"
              onError={(e) => {
                // Fallback avatar if unsplash image fails to load
                (e.target as HTMLImageElement).src = 'https://api.dicebear.com/7.x/bottts/svg?seed=founder';
              }}
            />
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-gray-400 hover:text-brandRed hover:bg-brandRed/10 rounded-lg transition-all duration-200"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
