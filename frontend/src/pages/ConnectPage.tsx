import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integrationsService } from '../services/integrations';
import { Mail, Calendar, Github, BookOpen, Link2, Unlink, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export default function ConnectPage() {
  const queryClient = useQueryClient();
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: integrationsService.getIntegrations,
  });

  const connectMutation = useMutation({
    mutationFn: integrationsService.connectIntegration,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: async (provider: string) => {
      setSyncingId(provider);
      await integrationsService.syncAll([provider]);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setSyncingId(null);
    },
  });

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'gmail':
        return <Mail size={24} className="text-[#EA4335]" />;
      case 'calendar':
        return <Calendar size={24} className="text-[#4285F4]" />;
      case 'github':
        return <Github size={24} className="text-[#F0F6FC]" />;
      case 'notion':
        return <BookOpen size={24} className="text-[#FFFFFF]" />;
      default:
        return <Link2 size={24} />;
    }
  };

  const getProviderDescription = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'gmail':
        return 'Scans email headers for investor updates, Stripe logs, and partner alerts.';
      case 'calendar':
        return 'Tracks scheduling conflicts, customer calls, and product review meetings.';
      case 'github':
        return 'Reviews repository code activity, PR merges, rate alerts, and issue backlogs.';
      case 'notion':
        return 'Scans project wikis, agendas, databases, and general wiki page edits.';
      default:
        return '';
    }
  };

  if (isLoading || !integrations) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brandPurple/30 border-t-brandPurple rounded-full animate-spin mb-4" />
        <span className="text-sm text-gray-400">Loading integrations...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-gray-400">
          Connect your operations stack to FlowBrain. Our read-only connections feed metrics into your AI Chief of Staff.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {integrations.map((integration) => {
          const isSyncing = syncingId === integration.provider;
          const isComingSoon = ['github', 'notion'].includes(integration.provider.toLowerCase());
          
          return (
            <div
              key={integration.id}
              className={`p-6 rounded-2xl border bg-[#0D1117] transition-all duration-200 ${
                integration.connected && !isComingSoon
                  ? 'border-[#1C2A3A] hover:border-brandPurple/30'
                  : 'border-[#1C2A3A] opacity-75'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-white/[0.03] border border-[#1C2A3A] rounded-xl">
                    {getProviderIcon(integration.provider)}
                  </div>
                  <div>
                    <h3 className="font-heading text-lg font-bold text-white capitalize flex items-center gap-2">
                      <span>{integration.provider}</span>
                      {isComingSoon && (
                        <span className="text-[9px] font-extrabold bg-brandPurple/10 text-brandPurple px-1.5 py-0.5 rounded uppercase">
                          Coming Soon
                        </span>
                      )}
                    </h3>
                    {!isComingSoon && (
                      <span
                        className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full mt-1.5 ${
                          integration.connected
                            ? 'bg-brandGreen/10 text-brandGreen'
                            : 'bg-gray-500/10 text-gray-400'
                        }`}
                      >
                        {integration.connected ? 'Connected' : 'Not Connected'}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-gray-400 mt-4 leading-relaxed">
                {getProviderDescription(integration.provider)}
              </p>

              {/* Integration Stats / Metrics */}
              {integration.connected && !isComingSoon && (
                <div className="mt-3 space-y-1">
                  {integration.provider === 'gmail' && (
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Total Emails: <strong className="text-[#E2EBF9] font-semibold">{integration.email_count ?? 0}</strong></span>
                      <span>Unread: <strong className="text-brandRed font-semibold">{integration.unread_count ?? 0}</strong></span>
                    </div>
                  )}
                  {integration.provider === 'calendar' && (
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Upcoming Events: <strong className="text-[#E2EBF9] font-semibold">{integration.upcoming_events_count ?? 0}</strong></span>
                    </div>
                  )}
                </div>
              )}

              {/* Last Sync */}
              {integration.connected && !isComingSoon && (
                <div className="mt-4 pt-4 border-t border-[#1C2A3A] flex items-center justify-between text-[10px] text-gray-500">
                  <span>Last synchronized:</span>
                  <span className="font-medium">
                    {integration.last_sync
                      ? new Date(integration.last_sync).toLocaleString()
                      : 'Never'}
                  </span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-3 mt-6">
                {isComingSoon ? (
                  <button
                    disabled
                    className="w-full flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-white/5 text-gray-500 text-xs font-semibold cursor-not-allowed"
                  >
                    <span>Coming Soon</span>
                  </button>
                ) : integration.connected ? (
                  <>
                    <button
                      onClick={() => syncMutation.mutate(integration.provider)}
                      disabled={isSyncing}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border border-[#1C2A3A] hover:border-[#2563EB] hover:text-[#2563EB] text-xs font-semibold transition-all disabled:opacity-50"
                    >
                      <RefreshCw size={14} className={isSyncing ? 'animate-spin' : ''} />
                      <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
                    </button>
                    <button
                      onClick={() => connectMutation.mutate(integration.provider)}
                      className="flex items-center justify-center p-2 rounded-xl border border-brandRed/20 hover:bg-brandRed/10 text-brandRed hover:text-white transition-all"
                      title="Disconnect Integration"
                    >
                      <Unlink size={14} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectMutation.mutate(integration.provider)}
                    className="w-full flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-brandPurple text-white text-xs font-semibold hover:opacity-95 active:scale-98 transition-all"
                  >
                    <Link2 size={14} />
                    <span>Connect Account</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
