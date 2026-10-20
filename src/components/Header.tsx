import React, { useState, useEffect } from 'react';
import {
  FileText,
  Cpu,
  Terminal,
  User,
  LogIn,
  LogOut,
  ShieldCheck,
} from 'lucide-react';
import { fetchCurrentUser, removeStoredAuthToken } from '../services/api';
import { User as UserType } from '../types/auth';
import { AuthModal } from './auth/AuthModal';

interface HeaderProps {
  currentUser?: UserType | null;
  onUserChange?: (user: UserType | null) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser: propUser,
  onUserChange,
}) => {
  const [user, setUser] = useState<UserType | null>(propUser || null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  useEffect(() => {
    if (propUser !== undefined) {
      setUser(propUser);
      return;
    }
    async function loadUser() {
      try {
        const u = await fetchCurrentUser();
        setUser(u);
        if (onUserChange) onUserChange(u);
      } catch {
        setUser(null);
      }
    }
    loadUser();
  }, [propUser]);

  const handleLogout = () => {
    removeStoredAuthToken();
    setUser(null);
    if (onUserChange) onUserChange(null);
  };

  const handleAuthSuccess = (authenticatedUser: UserType) => {
    setUser(authenticatedUser);
    if (onUserChange) onUserChange(authenticatedUser);
  };

  return (
    <>
      <header className="border-b border-slate-200 bg-white shadow-xs sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-slate-900 text-white rounded-xl shadow-xs flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                    AI Resume Parser &amp; Job Matcher
                  </h1>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200 rounded">
                    Phase 19 Active
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Requirement Analysis • Deterministic Matching • Dense Embeddings
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {/* Architecture specs */}
              <div className="hidden md:flex items-center gap-2 text-xs text-slate-600 bg-slate-100/70 px-2.5 py-1 rounded-lg border border-slate-200 font-mono">
                <Cpu className="w-3.5 h-3.5 text-slate-500" />
                <span>8001</span>
                <span className="text-slate-300">|</span>
                <Terminal className="w-3.5 h-3.5 text-slate-500" />
                <span>3000</span>
              </div>

              {/* Authentication Controls */}
              {user ? (
                <div className="flex items-center gap-2.5">
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-950 font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="truncate max-w-[150px]">{user.full_name || user.email}</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Sign Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsAuthModalOpen(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors shadow-xs cursor-pointer"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </>
  );
};
