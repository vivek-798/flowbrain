import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Brain, Chrome } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }

    const token = searchParams.get('token');
    const name = searchParams.get('name');
    const email = searchParams.get('email');
    const avatarUrl = searchParams.get('avatar_url');

    if (token && email) {
      login(token, {
        name: name || '',
        email: email,
        avatar_url: avatarUrl || 'https://api.dicebear.com/7.x/bottts/svg?seed=founder'
      });
      // Clear parameters and redirect to Dashboard
      navigate('/', { replace: true });
    }
  }, [searchParams, navigate, isAuthenticated, login]);

  const handleLogin = () => {
    setLoading(true);
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const absoluteApiUrl = apiBaseUrl.startsWith('http')
      ? apiBaseUrl
      : `${window.location.origin}${apiBaseUrl}`;
    window.location.href = `${absoluteApiUrl}/auth/google/login`;
  };

  return (
    <div className="min-h-screen bg-[#07090F] flex items-center justify-center relative overflow-hidden font-body text-[#E2EBF9]">
      {/* Decorative Gradient Blobs */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] rounded-full bg-brandPurple/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-brandBlue/10 blur-[120px] pointer-events-none" />

      {/* Main card */}
      <div className="w-full max-w-md p-8 rounded-2xl border border-[#1C2A3A] bg-[#0D1117]/60 backdrop-blur-xl shadow-2xl relative z-10 flex flex-col items-center">
        {/* Logo */}
        <div className="p-4 rounded-2xl bg-gradient-to-tr from-brandBlue to-brandPurple text-white shadow-xl shadow-brandPurple/20 mb-6">
          <Brain size={40} />
        </div>

        <h1 className="font-heading text-3xl font-extrabold tracking-tight text-white mb-2 text-center">
          Flow<span className="text-brandPurple">Brain</span>
        </h1>
        <p className="text-gray-400 text-sm text-center mb-8 max-w-[280px]">
          The AI Chief of Staff for startup founders. Connect your tools, sync business signals, and review daily briefings.
        </p>

        {/* Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-xl text-sm font-semibold bg-white text-[#07090F] hover:bg-white/90 transition-all duration-200 shadow-md active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Chrome size={18} />
          <span>{loading ? 'Redirecting to Google...' : 'Sign in with Google'}</span>
        </button>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-[#1C2A3A] w-full text-center">
          <span className="text-xs text-gray-500 font-medium">
            FlowBrain connects securely using read-only Google and Notion credentials.
          </span>
        </div>
      </div>
    </div>
  );
}

