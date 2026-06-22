import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integrationsService } from '../services/integrations';
import { briefingService } from '../services/briefing';
import { Mail, Calendar, AlertTriangle, RefreshCw, CheckCircle, Video, MapPin, User as UserIcon, Sparkles, TrendingUp, HelpCircle } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [syncMessage, setSyncMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: overview, isLoading, isError } = useQuery({
    queryKey: ['dashboardOverview'],
    queryFn: integrationsService.getDashboardOverview,
    refetchInterval: 15000,
  });

  const { data: briefing, isLoading: isLoadingBriefing } = useQuery({
    queryKey: ['latestBriefing'],
    queryFn: briefingService.getLatestBriefing,
  });

  const generateBriefingMutation = useMutation({
    mutationFn: briefingService.generateBriefing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['latestBriefing'] });
      showSyncMessage('success', 'AI briefing generated successfully!');
    },
    onError: (err: any) => {
      showSyncMessage('error', `AI briefing generation failed: ${err.message || err.detail || err}`);
    }
  });

  const syncGmailMutation = useMutation({
    mutationFn: integrationsService.syncGmail,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboardOverview'] });
      queryClient.invalidateQueries({ queryKey: ['latestBriefing'] });
      showSyncMessage('success', `Gmail synced successfully! ${data.emails_synced} emails processed.`);
    },
    onError: (err: any) => {
      showSyncMessage('error', `Gmail sync failed: ${err.message || err.detail || err}`);
    }
  });

  const syncCalendarMutation = useMutation({
    mutationFn: integrationsService.syncCalendar,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboardOverview'] });
      queryClient.invalidateQueries({ queryKey: ['latestBriefing'] });
      showSyncMessage('success', `Calendar synced successfully! ${data.events_synced} events processed.`);
    },
    onError: (err: any) => {
      showSyncMessage('error', `Calendar sync failed: ${err.message || err.detail || err}`);
    }
  });

  const showSyncMessage = (type: 'success' | 'error', text: string) => {
    setSyncMessage({ type, text });
    setTimeout(() => setSyncMessage(null), 5000);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brandPurple/30 border-t-brandPurple rounded-full animate-spin mb-4" />
        <span className="text-sm text-gray-400 font-medium">Loading overview metrics...</span>
      </div>
    );
  }

  if (isError || !overview) {
    return (
      <div className="p-6 rounded-xl border border-brandRed/20 bg-brandRed/5 text-center">
        <AlertTriangle className="mx-auto text-brandRed mb-3" size={32} />
        <h3 className="font-heading text-lg font-bold text-white mb-1">Failed to load overview data</h3>
        <p className="text-sm text-gray-400">Please make sure the backend is active.</p>
      </div>
    );
  }

  const isGmailConnected = overview.gmail_connected;
  const isCalendarConnected = overview.calendar_connected;

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      <AnimatePresence>
        {syncMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-4 right-4 z-50 p-4 rounded-xl border flex items-center gap-3 shadow-2xl ${
              syncMessage.type === 'success'
                ? 'bg-brandGreen/10 border-brandGreen/25 text-brandGreen'
                : 'bg-brandRed/10 border-brandRed/25 text-brandRed'
            }`}
          >
            {syncMessage.type === 'success' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
            <span className="text-xs font-semibold">{syncMessage.text}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs text-gray-500 font-semibold tracking-wider uppercase">Live Operations Overview</span>
          <h1 className="text-2xl font-bold text-white font-heading mt-1">Founder Dashboard</h1>
          {overview.last_sync ? (
            <p className="text-xs text-gray-400 mt-1">
              Last synchronized: {new Date(overview.last_sync).toLocaleString()}
            </p>
          ) : (
            <p className="text-xs text-gray-500 mt-1 italic">No sync records found.</p>
          )}
        </div>

        {/* Sync Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => syncGmailMutation.mutate()}
            disabled={!isGmailConnected || syncGmailMutation.isPending}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#1C2A3A] bg-[#0D1117] hover:border-brandPurple/40 text-white font-semibold text-xs transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={syncGmailMutation.isPending ? 'animate-spin' : ''} />
            <span>{syncGmailMutation.isPending ? 'Syncing Gmail...' : 'Sync Gmail'}</span>
          </button>
          <button
            onClick={() => syncCalendarMutation.mutate()}
            disabled={!isCalendarConnected || syncCalendarMutation.isPending}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#1C2A3A] bg-[#0D1117] hover:border-brandPurple/40 text-white font-semibold text-xs transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={syncCalendarMutation.isPending ? 'animate-spin' : ''} />
            <span>{syncCalendarMutation.isPending ? 'Syncing Calendar...' : 'Sync Calendar'}</span>
          </button>
        </div>
      </div>

      {/* AI Chief of Staff Briefing Section */}
      <div className="space-y-6">
        {isLoadingBriefing ? (
          <div className="p-6 rounded-2xl border border-borderColor bg-bgSurface/50 animate-pulse flex flex-col items-center justify-center min-h-[150px]">
            <div className="w-8 h-8 border-2 border-brandPurple/30 border-t-brandPurple rounded-full animate-spin mb-2" />
            <span className="text-xs text-gray-400">Loading Chief of Staff briefing...</span>
          </div>
        ) : briefing ? (
          <div className="space-y-6">
            {/* Focus Banner */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 rounded-2xl border border-brandPurple/30 bg-brandPurple/5 flex flex-col gap-4"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-brandPurple/10 rounded-xl text-brandPurple animate-pulse">
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <span className="text-[10px] text-brandPurple font-bold uppercase tracking-wider">Business Briefing Headline</span>
                    <h2 className="text-lg font-bold text-white font-heading mt-0.5">{briefing.headline || "No major business risks detected from available data."}</h2>
                  </div>
                </div>
                <button
                  onClick={() => generateBriefingMutation.mutate()}
                  disabled={generateBriefingMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2.5 bg-brandPurple hover:bg-brandPurple/90 disabled:bg-brandPurple/40 text-white font-bold text-xs rounded-xl transition-all shadow-md whitespace-nowrap self-end sm:self-auto"
                >
                  {generateBriefingMutation.isPending ? (
                    <>
                      <RefreshCw size={12} className="animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw size={12} />
                      <span>Regenerate Briefing</span>
                    </>
                  )}
                </button>
              </div>

              {(briefing.focus || briefing.ignored_count !== undefined) && (
                <div className="pt-3 border-t border-brandPurple/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <p className="text-gray-300">
                    <strong className="text-brandPurple font-bold uppercase tracking-wider text-[10px] block sm:inline sm:mr-2">Today's Focus:</strong>
                    {briefing.focus || "No urgent action needed today."}
                  </p>
                  {briefing.ignored_count !== undefined && (
                    <span className="text-gray-500 italic whitespace-nowrap">
                      Filtered out {briefing.ignored_count} noise signals
                    </span>
                  )}
                </div>
              )}
            </motion.div>

            {/* Briefing Grid details */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* About To Break */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
                className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col"
              >
                <div className="flex items-center justify-between pb-3 border-b border-brandRed/20 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-brandRed/10 rounded-lg text-brandRed">
                      <AlertTriangle size={16} />
                    </div>
                    <h3 className="font-heading text-sm font-bold text-white">About To Break</h3>
                  </div>
                  <span className="text-[10px] bg-brandRed/10 text-brandRed font-bold px-2 py-0.5 rounded-full font-mono">
                    {briefing.about_to_break?.length || 0}
                  </span>
                </div>
                
                {briefing.about_to_break && briefing.about_to_break.length > 0 ? (
                  <div className="space-y-3">
                    {briefing.about_to_break.map((item, index) => (
                      <div key={index} className="p-3 bg-brandRed/5 border border-brandRed/10 rounded-xl space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white leading-snug">{item.title}</span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {item.confidence && (
                              <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase ${
                                item.confidence === 'high' ? 'bg-brandGreen/10 text-brandGreen' :
                                item.confidence === 'medium' ? 'bg-brandAmber/10 text-brandAmber' :
                                'bg-brandRed/10 text-brandRed'
                              }`}>
                                {item.confidence} trust
                              </span>
                            )}
                            {item.source && (
                              <span className="text-[8px] bg-white/[0.03] text-gray-400 border border-[#1C2A3A] px-1 py-0.5 rounded font-mono">
                                {item.source}
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">{item.detail}</p>
                        {item.financial_impact && item.financial_impact !== 'N/A' && (
                          <div className="flex items-center justify-between pt-1.5 border-t border-brandRed/10 text-[10px]">
                            <span className="text-gray-500">Financial Impact:</span>
                            <span className="font-bold text-brandRed font-mono">{item.financial_impact}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-grow flex flex-col items-center justify-center py-6 text-center text-gray-500">
                    <CheckCircle size={24} className="text-brandGreen/40 mb-2" />
                    <p className="text-xs font-medium text-gray-400">All operations healthy</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">No critical issues identified.</p>
                  </div>
                )}
              </motion.div>

              {/* Needs Decision */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col"
              >
                <div className="flex items-center justify-between pb-3 border-b border-brandAmber/20 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-brandAmber/10 rounded-lg text-brandAmber">
                      <HelpCircle size={16} />
                    </div>
                    <h3 className="font-heading text-sm font-bold text-white">Needs Decision</h3>
                  </div>
                  <span className="text-[10px] bg-brandAmber/10 text-brandAmber font-bold px-2 py-0.5 rounded-full font-mono">
                    {briefing.needs_decision?.length || 0}
                  </span>
                </div>

                {briefing.needs_decision && briefing.needs_decision.length > 0 ? (
                  <div className="space-y-3">
                    {briefing.needs_decision.map((item, index) => (
                      <div key={index} className="p-3 bg-brandAmber/5 border border-brandAmber/10 rounded-xl space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white leading-snug">{item.title}</span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {item.confidence && (
                              <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase ${
                                item.confidence === 'high' ? 'bg-brandGreen/10 text-brandGreen' :
                                item.confidence === 'medium' ? 'bg-brandAmber/10 text-brandAmber' :
                                'bg-brandRed/10 text-brandRed'
                              }`}>
                                {item.confidence} trust
                              </span>
                            )}
                            {item.source && (
                              <span className="text-[8px] bg-white/[0.03] text-gray-400 border border-[#1C2A3A] px-1 py-0.5 rounded font-mono">
                                {item.source}
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">{item.detail}</p>
                        {item.financial_impact && item.financial_impact !== 'N/A' && (
                          <div className="flex items-center justify-between pt-1.5 border-t border-brandAmber/10 text-[10px]">
                            <span className="text-gray-500">Financial Impact:</span>
                            <span className="font-bold text-brandAmber font-mono">{item.financial_impact}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-grow flex flex-col items-center justify-center py-6 text-center text-gray-500">
                    <CheckCircle size={24} className="text-brandGreen/40 mb-2" />
                    <p className="text-xs font-medium text-gray-400">No actions pending</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">Everything is moving forward.</p>
                  </div>
                )}
              </motion.div>

              {/* Wins */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col"
              >
                <div className="flex items-center justify-between pb-3 border-b border-brandGreen/20 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-brandGreen/10 rounded-lg text-brandGreen">
                      <TrendingUp size={16} />
                    </div>
                    <h3 className="font-heading text-sm font-bold text-white">Wins</h3>
                  </div>
                  <span className="text-[10px] bg-brandGreen/10 text-brandGreen font-bold px-2 py-0.5 rounded-full font-mono">
                    {briefing.wins?.length || 0}
                  </span>
                </div>

                {briefing.wins && briefing.wins.length > 0 ? (
                  <div className="space-y-3">
                    {briefing.wins.map((item, index) => (
                      <div key={index} className="p-3 bg-brandGreen/5 border border-brandGreen/10 rounded-xl space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white leading-snug">{item.title}</span>
                          {item.source && (
                            <span className="text-[8px] bg-white/[0.03] text-gray-400 border border-[#1C2A3A] px-1 py-0.5 rounded font-mono shrink-0">
                              {item.source}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">{item.detail}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-grow flex flex-col items-center justify-center py-6 text-center text-gray-500">
                    <TrendingUp size={24} className="text-gray-600 mb-2" />
                    <p className="text-xs font-medium text-gray-400">No wins detected yet</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">Wins will sync automatically.</p>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        ) : (
          /* Empty State */
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-8 rounded-2xl border border-dashed border-[#1C2A3A] bg-gradient-to-br from-[#0D1117] to-[#121820] text-center max-w-2xl mx-auto space-y-4"
          >
            <div className="w-12 h-12 bg-brandPurple/10 text-brandPurple rounded-full flex items-center justify-center mx-auto mb-2 animate-pulse">
              <Sparkles size={24} />
            </div>
            <h3 className="font-heading text-lg font-bold text-white">No briefing generated yet</h3>
            <p className="text-sm text-gray-400 max-w-md mx-auto">
              FlowBrain can scan your operational database for Gmail and Calendar signals to synthesize a Chief of Staff Briefing.
            </p>
            <button
              onClick={() => generateBriefingMutation.mutate()}
              disabled={generateBriefingMutation.isPending}
              className="inline-flex items-center gap-2 px-6 py-3 bg-brandPurple hover:bg-brandPurple/95 disabled:bg-brandPurple/40 text-white font-bold text-sm rounded-xl transition-all shadow-lg hover:shadow-brandPurple/20 disabled:opacity-50"
            >
              {generateBriefingMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing Gmail and Calendar Signals...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Generate Briefing</span>
                </>
              )}
            </button>
          </motion.div>
        )}
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Gmail Stats Card */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col h-full justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="p-2.5 bg-[#EA4335]/10 rounded-xl text-[#EA4335]">
                  <Mail size={20} />
                </div>
                <h3 className="font-heading text-base font-bold text-white">Gmail Integration</h3>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                isGmailConnected ? 'bg-brandGreen/10 text-brandGreen' : 'bg-gray-500/10 text-gray-400'
              }`}>
                {isGmailConnected ? 'Connected' : 'Not Connected'}
              </span>
            </div>

            {isGmailConnected ? (
              overview.emails_total > 0 ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-white/[0.01] border border-[#1C2A3A] rounded-2xl">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Total Emails (30d)</span>
                    <p className="text-3xl font-extrabold text-white mt-1 font-heading">{overview.emails_total}</p>
                  </div>
                  <div className="p-4 bg-white/[0.01] border border-[#1C2A3A] rounded-2xl">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Unread Emails</span>
                    <p className="text-3xl font-extrabold text-brandRed mt-1 font-heading">{overview.emails_unread}</p>
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-2xl border border-dashed border-[#1C2A3A] text-center">
                  <p className="text-sm text-gray-400 font-medium">No emails synced yet</p>
                  <p className="text-xs text-gray-500 mt-1">Click "Sync Gmail" to fetch emails from the last 30 days.</p>
                </div>
              )
            ) : (
              <div className="p-6 rounded-2xl border border-dashed border-[#1C2A3A] text-center">
                <p className="text-sm text-brandAmber font-semibold">Connect Gmail to begin analysis</p>
                <p className="text-xs text-gray-500 mt-1">Enable Gmail connection in the Integrations panel.</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Calendar Stats Card */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col h-full justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="p-2.5 bg-[#4285F4]/10 rounded-xl text-[#4285F4]">
                  <Calendar size={20} />
                </div>
                <h3 className="font-heading text-base font-bold text-white">Google Calendar</h3>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                isCalendarConnected ? 'bg-brandGreen/10 text-brandGreen' : 'bg-gray-500/10 text-gray-400'
              }`}>
                {isCalendarConnected ? 'Connected' : 'Not Connected'}
              </span>
            </div>

            {isCalendarConnected ? (
              overview.calendar_events > 0 ? (
                <div className="p-4 bg-white/[0.01] border border-[#1C2A3A] rounded-2xl text-center">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Meetings This Month</span>
                  <p className="text-4xl font-extrabold text-white mt-1 font-heading">{overview.calendar_events}</p>
                </div>
              ) : (
                <div className="p-6 rounded-2xl border border-dashed border-[#1C2A3A] text-center">
                  <p className="text-sm text-gray-400 font-medium">No calendar events synced yet</p>
                  <p className="text-xs text-gray-500 mt-1">Click "Sync Calendar" to fetch this month's events.</p>
                </div>
              )
            ) : (
              <div className="p-6 rounded-2xl border border-dashed border-[#1C2A3A] text-center">
                <p className="text-sm text-brandAmber font-semibold">Connect Calendar to track events</p>
                <p className="text-xs text-gray-500 mt-1">Enable Google Calendar connection in the Integrations panel.</p>
              </div>
            )}
          </div>
        </motion.div>

      </div>

      {/* Next Upcoming Meeting Section */}
      {isCalendarConnected && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117]"
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Next Scheduled Meeting</span>
          </div>

          {overview.next_meeting && overview.next_meeting.title ? (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                <div>
                  <h2 className="text-xl font-bold text-white font-heading leading-tight">
                    {overview.next_meeting.title}
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    {overview.next_meeting.start_time ? new Date(overview.next_meeting.start_time).toLocaleString(undefined, {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit'
                    }) : ''}
                  </p>
                </div>

                {overview.next_meeting.meeting_link && (
                  <a
                    href={overview.next_meeting.meeting_link}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#4285F4]/10 hover:bg-[#4285F4]/20 border border-[#4285F4]/20 text-[#4285F4] rounded-lg text-xs font-semibold transition-all"
                  >
                    <Video size={12} />
                    <span>Join Google Meet</span>
                  </a>
                )}
              </div>

              {overview.next_meeting.description && (
                <p className="text-xs text-gray-400 bg-white/[0.01] border border-[#1C2A3A] p-3 rounded-xl leading-relaxed">
                  {overview.next_meeting.description}
                </p>
              )}

              <div className="flex flex-wrap gap-4 text-xs text-gray-400 pt-2 border-t border-[#1C2A3A]/50">
                {overview.next_meeting.organizer && (
                  <div className="flex items-center gap-1.5">
                    <UserIcon size={12} className="text-gray-500" />
                    <span>Organizer: <strong className="text-white font-medium">{overview.next_meeting.organizer}</strong></span>
                  </div>
                )}
                {overview.next_meeting.location && (
                  <div className="flex items-center gap-1.5">
                    <MapPin size={12} className="text-gray-500" />
                    <span>Location: <strong className="text-white font-medium">{overview.next_meeting.location}</strong></span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500 italic">No upcoming meetings scheduled.</p>
          )}
        </motion.div>
      )}
    </div>
  );
}
