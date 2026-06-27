import { useQuery, useMutation } from '@tanstack/react-query';
import { actionsService, ActionItem } from '../services/actions';
import { useState, useEffect } from 'react';
import { Check, X, Calendar, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ActionItemsSection() {
  const [localItems, setLocalItems] = useState<ActionItem[]>([]);
  const [exitingIds, setExitingIds] = useState<Record<number, 'done' | 'dismissed'>>({});


  const { data: actions, refetch: refetchActions } = useQuery({
    queryKey: ['actionsList'],
    queryFn: actionsService.getActions,
  });

  const { data: summary, refetch: refetchSummary } = useQuery({
    queryKey: ['actionsSummary'],
    queryFn: actionsService.getActionsSummary,
  });

  useEffect(() => {
    if (actions) {
      setLocalItems(actions);
    }
  }, [actions]);

  // Expose triggers for other components (e.g. DashboardPage) to refetch
  useEffect(() => {
    const handleRefetch = () => {
      refetchActions();
      refetchSummary();
    };
    window.addEventListener('refetchActions', handleRefetch);
    return () => window.removeEventListener('refetchActions', handleRefetch);
  }, [refetchActions, refetchSummary]);

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: 'done' | 'dismissed' }) =>
      actionsService.updateActionStatus(id, status),
  });

  const handleAction = async (id: number, status: 'done' | 'dismissed') => {
    // 1. Mark as exiting immediately to trigger animation
    setExitingIds((prev) => ({ ...prev, [id]: status }));

    // 2. Trigger mutation
    try {
      await updateStatusMutation.mutateAsync({ id, status });
    } catch (err) {
      console.error("Failed to update status on server:", err);
      // Revert exit state on failure
      setExitingIds((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      return;
    }

    // 3. Remove from local list and refresh summary metrics after animation
    setTimeout(() => {
      setLocalItems((prev) => prev.filter((item) => item.id !== id));
      refetchSummary();
    }, 300);
  };

  const formatRupees = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDueDateText = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getCardDateStyle = (dateStr: string | null) => {
    if (!dateStr) return { bg: '', text: '' };
    
    const due = new Date(dateStr);
    const now = new Date();
    due.setHours(0, 0, 0, 0);
    now.setHours(0, 0, 0, 0);
    
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return { bg: 'bg-[#EF4444]/20 border border-[#EF4444]/30', text: 'text-[#EF4444]' };
    } else if (diffDays <= 2) {
      return { bg: 'bg-[#F59E0B]/20 border border-[#F59E0B]/30', text: 'text-[#F59E0B]' };
    } else {
      return { bg: 'bg-[#1C2A3A]', text: 'text-[#6B84A8]' };
    }
  };

  const getSummaryDateStyle = (dateStr: string | null) => {
    if (!dateStr) return 'text-gray-500';
    const due = new Date(dateStr);
    const now = new Date();
    due.setHours(0, 0, 0, 0);
    now.setHours(0, 0, 0, 0);
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return 'text-[#EF4444] font-bold';
    } else if (diffDays <= 2) {
      return 'text-[#F59E0B] font-bold';
    } else {
      return 'text-[#6B84A8]';
    }
  };

  const formatSummaryDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-4">
      {/* Summary Bar */}
      {summary && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-xl border border-[#1C2A3A] bg-[#090D14] gap-2">
          <div className="flex items-center gap-3">
            <span className="text-sm">✅</span>
            <span className="text-sm font-bold text-white font-heading">Action Items</span>
            <span className="text-xs text-gray-400">
              {summary.total_pending} pending &middot; <span className="text-brandGreen font-bold">₹{formatRupees(summary.total_financial_at_stake)}</span> at stake
            </span>
          </div>
          {summary.total_pending > 0 && summary.next_due_date && (
            <div className="text-xs">
              <span className="text-gray-500">Next due: </span>
              <span className={getSummaryDateStyle(summary.next_due_date)}>
                {formatSummaryDate(summary.next_due_date)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Action Items List */}
      <div className="space-y-3 relative overflow-hidden">
        <AnimatePresence initial={false}>
          {localItems.length > 0 ? (
            localItems.map((item) => {
              const exitType = exitingIds[item.id];
              const dateStyle = getCardDateStyle(item.due_date);
              
              return (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={
                    exitType === 'done'
                      ? { opacity: 0, scale: 0.95 }
                      : exitType === 'dismissed'
                      ? { x: '-110%', opacity: 0 }
                      : { opacity: 0 }
                  }
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  className="p-4 rounded-xl border border-[#1C2A3A] bg-[#0D1117] hover:border-brandPurple/20 transition-colors flex flex-col gap-3"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      {/* Priority badge */}
                      <div className="w-5 h-5 rounded-full bg-brandPurple/15 border border-brandPurple/30 flex items-center justify-center text-[10px] font-bold text-brandPurple shrink-0 mt-0.5">
                        {item.priority}
                      </div>
                      
                      {/* Source indicator dot and title */}
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full shrink-0 ${
                              item.source_type === 'red' ? 'bg-[#EF4444]' : 'bg-[#F59E0B]'
                            }`}
                          />
                          <h4 className="text-sm font-bold text-white font-heading leading-snug">
                            {item.title}
                          </h4>
                        </div>
                        {item.description && (
                          <p className="text-xs text-gray-400 leading-relaxed pl-4">
                            {item.description}
                          </p>
                        )}
                        
                        {/* Meta chips (Client, Project, Duration) */}
                        <div className="flex flex-wrap gap-2 pl-4 pt-1">
                          {item.client_name && (
                            <span className="text-[10px] bg-[#1E293B] text-gray-300 px-2 py-0.5 rounded border border-[#334155]/30">
                              Client: <span className="text-white font-semibold">{item.client_name}</span>
                            </span>
                          )}
                          {item.project_name && (
                            <span className="text-[10px] bg-[#1E293B] text-gray-300 px-2 py-0.5 rounded border border-[#334155]/30">
                              Project: <span className="text-white font-semibold">{item.project_name}</span>
                            </span>
                          )}
                          {item.estimated_duration && (
                            <span className="text-[10px] bg-[#1C2A3A]/40 text-gray-400 px-2 py-0.5 rounded border border-[#1C2A3A]/60">
                              Duration: <span className="text-white font-semibold">{item.estimated_duration}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card bottom status and actions */}
                  <div className="flex items-center justify-between pt-2 border-t border-[#1C2A3A]/40 text-xs">
                    <div className="flex items-center gap-3">
                      {/* Due date chip */}
                      {item.due_date && (
                        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-medium ${dateStyle.bg} ${dateStyle.text}`}>
                          <Calendar size={10} />
                          <span>{formatDueDateText(item.due_date)}</span>
                        </div>
                      )}
                      
                      {/* Financial impact badge */}
                      {item.financial_impact !== null && (
                        <div className="text-[10px] font-bold text-brandGreen font-mono">
                          &#8377; {formatRupees(item.financial_impact)}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Done button */}
                      <button
                        onClick={() => handleAction(item.id, 'done')}
                        className="bg-[#10B981]/10 text-[#10B981] hover:bg-[#10B981]/20 px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition-all"
                      >
                        <Check size={11} />
                        <span>Done</span>
                      </button>
                      
                      {/* Dismiss button */}
                      <button
                        onClick={() => handleAction(item.id, 'dismissed')}
                        className="bg-transparent text-[#374E70] hover:text-white px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition-all"
                      >
                        <X size={11} />
                        <span>Dismiss</span>
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-6 rounded-xl border border-dashed border-[#1C2A3A]/60 bg-[#0D1117]/30 text-center flex flex-col items-center justify-center gap-2"
            >
              <div className="w-8 h-8 rounded-full bg-brandGreen/10 flex items-center justify-center text-brandGreen">
                <CheckCircle size={16} />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white leading-snug">All caught up</h4>
                <p className="text-[10px] text-gray-500 mt-0.5">No pending actions.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
