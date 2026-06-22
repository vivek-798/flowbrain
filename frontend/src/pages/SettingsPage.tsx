import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { briefingService, SettingsData, ClientData, ProjectData, TeamMemberData, BusinessContextData } from '../services/briefing';
import { User, Bell, Shield, Cpu, Save, CheckCircle2, Briefcase, Plus, Trash2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id || 1;

  const [success, setSuccess] = useState(false);
  const [form, setForm] = useState<Partial<SettingsData>>({});

  // Business Context Form States
  const [bizType, setBizType] = useState('');
  const [clients, setClients] = useState<ClientData[]>([]);
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMemberData[]>([]);

  // Inline inputs to add items
  const [newClientName, setNewClientName] = useState('');
  const [newClientValue, setNewClientValue] = useState(0);
  const [newClientStatus, setNewClientStatus] = useState('active');
  const [newClientNotes, setNewClientNotes] = useState('');

  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectClient, setNewProjectClient] = useState('');
  const [newProjectValue, setNewProjectValue] = useState(0);
  const [newProjectDeadline, setNewProjectDeadline] = useState('');
  const [newProjectCompletion, setNewProjectCompletion] = useState(0);
  const [newProjectStatus, setNewProjectStatus] = useState('active');

  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('');
  const [newMemberEmail, setNewMemberEmail] = useState('');

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: briefingService.getSettings,
  });

  const { data: businessContext, isLoading: isLoadingContext } = useQuery({
    queryKey: ['businessContext', userId],
    queryFn: () => briefingService.getBusinessContext(userId),
    enabled: !!userId,
  });

  useEffect(() => {
    if (settings) {
      setForm(settings);
    }
  }, [settings]);

  useEffect(() => {
    if (businessContext) {
      setBizType(businessContext.business_type || '');
      setClients(businessContext.clients || []);
      setProjects(businessContext.projects || []);
      setTeamMembers(businessContext.team_members || []);
    }
  }, [businessContext]);

  const [contextSuccess, setContextSuccess] = useState(false);

  const updateMutation = useMutation({
    mutationFn: briefingService.updateSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(['settings'], data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    },
  });

  const saveContextMutation = useMutation({
    mutationFn: (data: BusinessContextData) => briefingService.updateBusinessContext(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['businessContext', userId] });
      setContextSuccess(true);
      setTimeout(() => setContextSuccess(false), 3000);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(form);
    saveContextMutation.mutate({
      business_type: bizType,
      clients,
      projects,
      team_members: teamMembers
    });
  };

  const handleAddClient = () => {
    if (!newClientName) return;
    setClients(prev => [...prev, {
      name: newClientName,
      value_inr: Number(newClientValue) || 0,
      status: newClientStatus,
      notes: newClientNotes
    }]);
    setNewClientName('');
    setNewClientValue(0);
    setNewClientStatus('active');
    setNewClientNotes('');
  };

  const handleRemoveClient = (index: number) => {
    setClients(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddProject = () => {
    if (!newProjectName) return;
    setProjects(prev => [...prev, {
      name: newProjectName,
      client_name: newProjectClient,
      value_inr: Number(newProjectValue) || 0,
      deadline: newProjectDeadline,
      completion_percent: Number(newProjectCompletion) || 0,
      status: newProjectStatus
    }]);
    setNewProjectName('');
    setNewProjectClient('');
    setNewProjectValue(0);
    setNewProjectDeadline('');
    setNewProjectCompletion(0);
    setNewProjectStatus('active');
  };

  const handleRemoveProject = (index: number) => {
    setProjects(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddMember = () => {
    if (!newMemberName || !newMemberRole) return;
    setTeamMembers(prev => [...prev, {
      name: newMemberName,
      role: newMemberRole,
      email: newMemberEmail
    }]);
    setNewMemberName('');
    setNewMemberRole('');
    setNewMemberEmail('');
  };

  const handleRemoveMember = (index: number) => {
    setTeamMembers(prev => prev.filter((_, i) => i !== index));
  };

  const handleChange = (field: keyof SettingsData, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  if (isLoading || isLoadingContext || !settings) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brandPurple/30 border-t-brandPurple rounded-full animate-spin mb-4" />
        <span className="text-sm text-gray-400">Loading system parameters...</span>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Profile Details */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-[#1C2A3A] pb-3 mb-1">
            <User className="text-brandPurple" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">Founder Profile</h3>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={form.name || ''}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-[#07090F] border border-[#1C2A3A] hover:border-brandPurple/30 focus:border-brandPurple focus:outline-none text-xs text-white transition-colors"
                placeholder="Full Name"
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1.5">
                Work Email Address
              </label>
              <input
                type="email"
                value={form.email || ''}
                disabled
                className="w-full px-4 py-2.5 rounded-xl bg-[#07090F]/50 border border-[#1C2A3A] text-xs text-gray-500 cursor-not-allowed"
                placeholder="email@example.com"
              />
            </div>
          </div>
        </motion.div>

        {/* Notifications & Automation */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-[#1C2A3A] pb-3 mb-1">
            <Bell className="text-brandBlue" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">Notifications & Alerts</h3>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold text-white">Daily Email Reports</h4>
              <p className="text-[10px] text-gray-500 mt-0.5">Receive summary updates in your inbox every morning.</p>
            </div>
            <button
              type="button"
              onClick={() => handleChange('email_notifications', !form.email_notifications)}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center ${
                form.email_notifications ? 'bg-brandPurple' : 'bg-[#1C2A3A]'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full bg-white transition-transform absolute ${
                  form.email_notifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </motion.div>

        {/* Privacy & Security */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-[#1C2A3A] pb-3 mb-1">
            <Shield className="text-brandGreen" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">Data Privacy</h3>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold text-white">Share Telemetry Analytics</h4>
              <p className="text-[10px] text-gray-500 mt-0.5">Allow sharing diagnostic metrics for system improvements.</p>
            </div>
            <button
              type="button"
              onClick={() => handleChange('share_analytics', !form.share_analytics)}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center ${
                form.share_analytics ? 'bg-brandPurple' : 'bg-[#1C2A3A]'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full bg-white transition-transform absolute ${
                  form.share_analytics ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </motion.div>

        {/* AI Provider configuration */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-[#1C2A3A] pb-3 mb-1">
            <Cpu className="text-brandAmber" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">AI Engine Models</h3>
          </div>

          <div>
            <label className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1.5">
              Select AI Intelligence Provider
            </label>
            <select
              value={form.ai_provider || ''}
              onChange={(e) => handleChange('ai_provider', e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#07090F] border border-[#1C2A3A] focus:border-brandPurple focus:outline-none text-xs text-white transition-colors cursor-pointer"
            >
              <option value="Claude Haiku">Claude 3 Haiku (Recommended)</option>
              <option value="Claude Sonnet">Claude 3.5 Sonnet</option>
              <option value="GPT-4o">GPT-4o</option>
            </select>
            <span className="text-[9px] text-gray-500 font-medium block mt-1.5">
              FlowBrain uses LiteLLM interface layer. API configuration key is sourced from backend `.env`.
            </span>
          </div>
        </motion.div>

        {/* Business Context Section */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="p-6 rounded-2xl border border-[#1C2A3A] bg-[#0D1117] space-y-6"
        >
          <div className="flex items-center gap-2 border-b border-[#1C2A3A] pb-3 mb-1">
            <Briefcase className="text-brandPurple" size={16} />
            <h3 className="font-heading text-sm font-bold text-white">Business Context</h3>
          </div>

          {/* Business Type */}
          <div>
            <label className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1.5">
              Business Type / Industry
            </label>
            <input
              type="text"
              value={bizType}
              onChange={(e) => setBizType(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#07090F] border border-[#1C2A3A] hover:border-brandPurple/30 focus:border-brandPurple focus:outline-none text-xs text-white transition-colors"
              placeholder="e.g. Design agency, B2B SaaS, E-commerce brand"
            />
          </div>

          {/* Clients List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#1C2A3A]/45 pb-1">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Clients ({clients.length})</span>
            </div>
            
            {clients.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#1C2A3A] text-gray-500 font-mono text-[10px] uppercase">
                      <th className="py-2 font-semibold">Name</th>
                      <th className="py-2 font-semibold">Value (INR)</th>
                      <th className="py-2 font-semibold">Status</th>
                      <th className="py-2 font-semibold">Notes</th>
                      <th className="py-2 w-10 text-center">Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clients.map((c, idx) => (
                      <tr key={idx} className="border-b border-[#1C2A3A]/50 text-white">
                        <td className="py-2 font-medium">{c.name}</td>
                        <td className="py-2 font-mono">₹{c.value_inr.toLocaleString()}</td>
                        <td className="py-2">
                          <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase ${
                            c.status === 'active' ? 'bg-brandGreen/10 text-brandGreen' :
                            c.status === 'at-risk' ? 'bg-brandAmber/10 text-brandAmber' :
                            'bg-brandRed/10 text-brandRed'
                          }`}>
                            {c.status}
                          </span>
                        </td>
                        <td className="py-2 text-gray-400 max-w-[150px] truncate" title={c.notes}>{c.notes || '-'}</td>
                        <td className="py-2 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveClient(idx)}
                            className="text-brandRed hover:text-brandRed/80 transition-colors p-1"
                          >
                            <Trash2 size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Inline inputs to add client */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#07090F] p-3 rounded-xl border border-[#1C2A3A]/50">
              <input
                type="text"
                value={newClientName}
                onChange={(e) => setNewClientName(e.target.value)}
                placeholder="Client Name"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
              />
              <input
                type="number"
                value={newClientValue || ''}
                onChange={(e) => setNewClientValue(Number(e.target.value))}
                placeholder="Value (INR)"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none font-mono"
              />
              <select
                value={newClientStatus}
                onChange={(e) => setNewClientStatus(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none cursor-pointer"
              >
                <option value="active">Active</option>
                <option value="at-risk">At-Risk</option>
                <option value="lost">Lost</option>
              </select>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newClientNotes}
                  onChange={(e) => setNewClientNotes(e.target.value)}
                  placeholder="Notes"
                  className="flex-1 px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddClient}
                  className="px-3 py-1.5 bg-brandPurple hover:bg-brandPurple/90 rounded-lg text-white font-bold transition-all text-xs shrink-0 flex items-center justify-center"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Projects List */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between border-b border-[#1C2A3A]/45 pb-1">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Active Projects ({projects.length})</span>
            </div>
            
            {projects.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#1C2A3A] text-gray-500 font-mono text-[10px] uppercase">
                      <th className="py-2 font-semibold">Project</th>
                      <th className="py-2 font-semibold">Client</th>
                      <th className="py-2 font-semibold">Value</th>
                      <th className="py-2 font-semibold">Deadline</th>
                      <th className="py-2 font-semibold">Comp. %</th>
                      <th className="py-2 font-semibold">Status</th>
                      <th className="py-2 w-10 text-center">Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((p, idx) => (
                      <tr key={idx} className="border-b border-[#1C2A3A]/50 text-white">
                        <td className="py-2 font-medium">{p.name}</td>
                        <td className="py-2 text-gray-400">{p.client_name}</td>
                        <td className="py-2 font-mono">₹{p.value_inr.toLocaleString()}</td>
                        <td className="py-2 text-gray-400">{p.deadline || '-'}</td>
                        <td className="py-2 font-mono">{p.completion_percent}%</td>
                        <td className="py-2">
                          <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase ${
                            p.status === 'active' ? 'bg-brandGreen/10 text-brandGreen' :
                            p.status === 'at-risk' ? 'bg-brandAmber/10 text-brandAmber' :
                            'bg-brandRed/10 text-brandRed'
                          }`}>
                            {p.status}
                          </span>
                        </td>
                        <td className="py-2 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveProject(idx)}
                            className="text-brandRed hover:text-brandRed/80 transition-colors p-1"
                          >
                            <Trash2 size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Inline inputs to add project */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 bg-[#07090F] p-3 rounded-xl border border-[#1C2A3A]/50">
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Project Name"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
              />
              <select
                value={newProjectClient}
                onChange={(e) => setNewProjectClient(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none cursor-pointer"
              >
                <option value="">Select Client Link</option>
                {clients.map((c, i) => (
                  <option key={i} value={c.name}>{c.name}</option>
                ))}
                {clients.length === 0 && <option disabled>No clients added yet</option>}
              </select>
              <input
                type="number"
                value={newProjectValue || ''}
                onChange={(e) => setNewProjectValue(Number(e.target.value))}
                placeholder="Value (INR)"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none font-mono"
              />
              <input
                type="date"
                value={newProjectDeadline}
                onChange={(e) => setNewProjectDeadline(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none cursor-pointer"
              />
              <input
                type="number"
                value={newProjectCompletion || ''}
                onChange={(e) => setNewProjectCompletion(Number(e.target.value))}
                placeholder="Comp. %"
                min="0"
                max="100"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none font-mono"
              />
              <div className="flex gap-2">
                <select
                  value={newProjectStatus}
                  onChange={(e) => setNewProjectStatus(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none cursor-pointer"
                >
                  <option value="active">Active</option>
                  <option value="at-risk">At-Risk</option>
                  <option value="completed">Completed</option>
                  <option value="lost">Lost</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddProject}
                  className="px-3 py-1.5 bg-brandPurple hover:bg-brandPurple/90 rounded-lg text-white font-bold transition-all text-xs shrink-0 flex items-center justify-center"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Team Members List */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between border-b border-[#1C2A3A]/45 pb-1">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Team Members ({teamMembers.length})</span>
            </div>
            
            {teamMembers.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#1C2A3A] text-gray-500 font-mono text-[10px] uppercase">
                      <th className="py-2 font-semibold">Name</th>
                      <th className="py-2 font-semibold">Role</th>
                      <th className="py-2 font-semibold">Email</th>
                      <th className="py-2 w-10 text-center">Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamMembers.map((t, idx) => (
                      <tr key={idx} className="border-b border-[#1C2A3A]/50 text-white">
                        <td className="py-2 font-medium">{t.name}</td>
                        <td className="py-2 text-gray-400">{t.role}</td>
                        <td className="py-2 text-gray-400 font-mono">{t.email || '-'}</td>
                        <td className="py-2 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveMember(idx)}
                            className="text-brandRed hover:text-brandRed/80 transition-colors p-1"
                          >
                            <Trash2 size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Inline inputs to add team member */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-[#07090F] p-3 rounded-xl border border-[#1C2A3A]/50">
              <input
                type="text"
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
                placeholder="Name"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
              />
              <input
                type="text"
                value={newMemberRole}
                onChange={(e) => setNewMemberRole(e.target.value)}
                placeholder="Role"
                className="px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
              />
              <div className="flex gap-2">
                <input
                  type="email"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder="Email"
                  className="flex-1 px-3 py-1.5 rounded-lg bg-[#0D1117] border border-[#1C2A3A] text-xs text-white focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddMember}
                  className="px-3 py-1.5 bg-brandPurple hover:bg-brandPurple/90 rounded-lg text-white font-bold transition-all text-xs shrink-0 flex items-center justify-center"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Submit Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center text-brandGreen gap-1 text-xs font-semibold h-9">
            {(success || contextSuccess) && (
              <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-1.5">
                <CheckCircle2 size={16} />
                <span>Settings saved successfully</span>
              </motion.div>
            )}
          </div>
          
          <button
            type="submit"
            disabled={updateMutation.isPending || saveContextMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brandPurple text-white text-xs font-semibold hover:opacity-95 active:scale-95 transition-all shadow-md shadow-brandPurple/15 disabled:opacity-50"
          >
            <Save size={14} />
            <span>{updateMutation.isPending || saveContextMutation.isPending ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
