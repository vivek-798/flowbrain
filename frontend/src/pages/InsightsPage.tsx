import { useQuery } from '@tanstack/react-query';
import { briefingService } from '../services/briefing';
import { AlertCircle, Calendar, ShieldAlert, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { motion } from 'framer-motion';

// Mock chart data representing scan activity over the last 7 days
const signalChartData = [
  { day: 'Mon', Gmail: 12, GitHub: 8, Notion: 5, Calendar: 4 },
  { day: 'Tue', Gmail: 18, GitHub: 15, Notion: 8, Calendar: 6 },
  { day: 'Wed', Gmail: 15, GitHub: 12, Notion: 10, Calendar: 3 },
  { day: 'Thu', Gmail: 22, GitHub: 19, Notion: 12, Calendar: 8 },
  { day: 'Fri', Gmail: 30, GitHub: 25, Notion: 15, Calendar: 5 },
  { day: 'Sat', Gmail: 8, GitHub: 4, Notion: 6, Calendar: 2 },
  { day: 'Sun', Gmail: 15, GitHub: 12, Notion: 8, Calendar: 4 },
];

export default function InsightsPage() {
  const { data: insights, isLoading } = useQuery({
    queryKey: ['insights'],
    queryFn: briefingService.getInsights,
  });

  if (isLoading || !insights) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brandPurple/30 border-t-brandPurple rounded-full animate-spin mb-4" />
        <span className="text-sm text-gray-400">Compiling analytical telemetry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Business Risk Score */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] relative overflow-hidden"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-gray-400 font-semibold">Business Risk Score</span>
            <AlertCircle size={16} className="text-brandBlue" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-white font-heading">
              {insights.business_risk_score}
            </span>
            <span className="text-xs text-gray-500 font-semibold">/ 100</span>
          </div>
          <p className="text-[10px] text-brandGreen font-medium mt-3 flex items-center gap-1">
            <span>●</span> Low operational threat levels detected.
          </p>
        </motion.div>

        {/* Open Risks */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117]"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-gray-400 font-semibold">Open Blockers</span>
            <ShieldAlert size={16} className="text-brandRed" />
          </div>
          <span className="text-4xl font-extrabold text-brandRed font-heading">
            {insights.open_risks}
          </span>
          <p className="text-[10px] text-gray-500 font-medium mt-3">
            Critical bottlenecks requiring immediate focus.
          </p>
        </motion.div>

        {/* Signal Scan Activity */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117]"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-gray-400 font-semibold">Signal Scans (24h)</span>
            <Activity size={16} className="text-brandPurple" />
          </div>
          <span className="text-4xl font-extrabold text-white font-heading">
            36
          </span>
          <p className="text-[10px] text-brandPurple font-medium mt-3 flex items-center gap-1">
            Active telemetry connections verified.
          </p>
        </motion.div>
      </div>

      {/* Analytics Chart & Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recharts Area Chart */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] lg:col-span-2 flex flex-col h-[350px]"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading text-sm font-bold text-white">Signal Scanning Volume</h3>
            <span className="text-[10px] text-gray-500 font-semibold">Signals Checked / Day</span>
          </div>
          
          <div className="flex-1 w-full h-full text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={signalChartData} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorGmail" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EA4335" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#EA4335" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorGitHub" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C2A3A" opacity={0.3} />
                <XAxis dataKey="day" stroke="#4B5563" fontSize={10} tickLine={false} />
                <YAxis stroke="#4B5563" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0D1117', borderColor: '#1C2A3A', borderRadius: '12px', color: '#E2EBF9' }}
                  itemStyle={{ fontSize: '11px' }}
                  labelStyle={{ fontSize: '11px', fontWeight: 'bold', marginBottom: '4px' }}
                />
                <Area type="monotone" dataKey="Gmail" stroke="#EA4335" strokeWidth={1.5} fillOpacity={1} fill="url(#colorGmail)" />
                <Area type="monotone" dataKey="GitHub" stroke="#2563EB" strokeWidth={1.5} fillOpacity={1} fill="url(#colorGitHub)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Upcoming Deadlines */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] flex flex-col h-[350px]"
        >
          <div className="flex items-center gap-2 mb-4 border-b border-[#1C2A3A] pb-3">
            <Calendar className="text-brandPurple" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">Upcoming Deadlines</h3>
          </div>
          
          <div className="space-y-3 flex-1 overflow-y-auto pr-1">
            {insights.upcoming_deadlines?.map((deadline) => (
              <div
                key={deadline.id}
                className="p-3.5 rounded-xl border border-white/[0.02] bg-white/[0.01] hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-xs font-semibold text-white truncate max-w-[120px]">
                    {deadline.project}
                  </h4>
                  <span
                    className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase ${
                      deadline.priority === 'high'
                        ? 'bg-brandRed/10 text-brandRed'
                        : 'bg-brandAmber/10 text-brandAmber'
                    }`}
                  >
                    {deadline.priority}
                  </span>
                </div>
                <span className="text-[10px] text-gray-500 font-medium">
                  Due: {new Date(deadline.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Activity Summary Grid */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117]"
      >
        <h3 className="font-heading text-sm font-bold text-white mb-4">Telemetry Integration Scan Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-white/[0.02] bg-white/[0.01]">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Gmail</span>
            <p className="text-xs font-semibold text-white mt-1.5 leading-relaxed">{insights.activity_summary.gmail}</p>
          </div>
          <div className="p-4 rounded-xl border border-white/[0.02] bg-white/[0.01]">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Calendar</span>
            <p className="text-xs font-semibold text-white mt-1.5 leading-relaxed">{insights.activity_summary.calendar}</p>
          </div>
          <div className="p-4 rounded-xl border border-white/[0.02] bg-white/[0.01]">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">GitHub</span>
            <p className="text-xs font-semibold text-white mt-1.5 leading-relaxed">{insights.activity_summary.github}</p>
          </div>
          <div className="p-4 rounded-xl border border-white/[0.02] bg-white/[0.01]">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Notion</span>
            <p className="text-xs font-semibold text-white mt-1.5 leading-relaxed">{insights.activity_summary.notion}</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
