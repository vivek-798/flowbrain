import { Link, useLocation } from 'react-router-dom';
import { Brain, LayoutDashboard, Link2, History, BarChart3, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const location = useLocation();
  const currentPath = location.pathname;
  const { logout } = useAuth();

  const menuItems = [
    { name: 'Briefing', path: '/', icon: LayoutDashboard },
    { name: 'Connect', path: '/connect', icon: Link2 },
    { name: 'History', path: '/history', icon: History },
    { name: 'Insights', path: '/insights', icon: BarChart3 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
  };

  return (
    <aside className="w-64 bg-[#0D1117] border-r border-[#1C2A3A] flex flex-col h-full z-10">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-[#1C2A3A]">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="p-2 rounded-lg bg-gradient-to-tr from-brandBlue to-brandPurple text-white shadow-lg shadow-brandPurple/20 transition-transform group-hover:scale-105">
            <Brain size={20} />
          </div>
          <span className="font-heading text-lg font-bold tracking-tight text-[#E2EBF9] group-hover:text-white transition-colors">
            Flow<span className="text-brandPurple">Brain</span>
          </span>
        </Link>
      </div>

      {/* Menu Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = currentPath === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-brandPurple/10 to-brandBlue/5 text-white border-l-2 border-brandPurple'
                  : 'text-gray-400 hover:text-white hover:bg-white/[0.02]'
              }`}
            >
              <Icon
                size={18}
                className={`transition-colors duration-200 ${
                  isActive ? 'text-brandPurple' : 'text-gray-400 group-hover:text-[#E2EBF9]'
                }`}
              />
              <span className="font-heading">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Logout Row */}
      <div className="p-4 border-t border-[#1C2A3A]">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-400 hover:text-brandRed hover:bg-brandRed/10 transition-all duration-200 group"
        >
          <LogOut size={18} className="text-gray-400 group-hover:text-brandRed transition-colors" />
          <span className="font-heading">Logout</span>
        </button>
      </div>
    </aside>
  );
}
