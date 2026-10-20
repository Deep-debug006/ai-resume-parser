import React, { useState } from 'react';
import {
  Mail,
  Phone,
  MapPin,
  Linkedin,
  Github,
  Globe,
  User,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react';
import { PersonalInfo as PersonalInfoType } from '../../types/resume';

export interface PersonalInfoProps {
  info?: PersonalInfoType | null;
}

export const PersonalInfo: React.FC<PersonalInfoProps> = ({ info }) => {
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(label);
    setTimeout(() => setCopiedItem(null), 2000);
  };

  const hasAnyInfo =
    info &&
    (info.email ||
      info.phone ||
      info.location ||
      info.linkedin_url ||
      info.github_url ||
      info.portfolio_url);

  if (!hasAnyInfo) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
          <User className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          Contact &amp; Personal Info
        </h2>
        <div className="p-4 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <p className="text-xs text-slate-500">No contact information detected in resume.</p>
        </div>
      </div>
    );
  }

  return (
    <section
      aria-labelledby="personal-info-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
        <h2
          id="personal-info-heading"
          className="text-sm font-semibold uppercase tracking-wider text-slate-900 flex items-center gap-2"
        >
          <User className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          Contact &amp; Personal Info
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Email */}
        {info.email && (
          <div className="group flex items-center justify-between p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/70 border border-slate-200/60 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
                <Mail className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <span className="block text-[10px] uppercase font-semibold text-slate-400">Email</span>
                <a
                  href={`mailto:${info.email}`}
                  className="text-xs font-medium text-slate-800 hover:text-emerald-700 truncate block transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600"
                >
                  {info.email}
                </a>
              </div>
            </div>
            <button
              type="button"
              onClick={() => copyToClipboard(info.email!, 'email')}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
              title="Copy email address"
              aria-label="Copy email address"
            >
              {copiedItem === 'email' ? (
                <Check className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        )}

        {/* Phone */}
        {info.phone && (
          <div className="group flex items-center justify-between p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/70 border border-slate-200/60 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center shrink-0">
                <Phone className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <span className="block text-[10px] uppercase font-semibold text-slate-400">Phone</span>
                <a
                  href={`tel:${info.phone}`}
                  className="text-xs font-medium text-slate-800 hover:text-sky-700 truncate block transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600"
                >
                  {info.phone}
                </a>
              </div>
            </div>
            <button
              type="button"
              onClick={() => copyToClipboard(info.phone!, 'phone')}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
              title="Copy phone number"
              aria-label="Copy phone number"
            >
              {copiedItem === 'phone' ? (
                <Check className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        )}

        {/* Location */}
        {info.location && (
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50/70 border border-slate-200/60">
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
              <MapPin className="w-4 h-4" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <span className="block text-[10px] uppercase font-semibold text-slate-400">Location</span>
              <span className="text-xs font-medium text-slate-800 truncate block">
                {info.location}
              </span>
            </div>
          </div>
        )}

        {/* LinkedIn */}
        {info.linkedin_url && (
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/70 border border-slate-200/60 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center shrink-0">
                <Linkedin className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <span className="block text-[10px] uppercase font-semibold text-slate-400">LinkedIn</span>
                <a
                  href={info.linkedin_url.startsWith('http') ? info.linkedin_url : `https://${info.linkedin_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-blue-700 hover:text-blue-900 truncate block transition-colors inline-flex items-center gap-1 focus-visible:outline-2 focus-visible:outline-emerald-600"
                >
                  <span className="truncate">{info.linkedin_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                  <ExternalLink className="w-3 h-3 shrink-0 opacity-70" aria-hidden="true" />
                </a>
              </div>
            </div>
          </div>
        )}

        {/* GitHub */}
        {info.github_url && (
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/70 border border-slate-200/60 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-800 flex items-center justify-center shrink-0">
                <Github className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <span className="block text-[10px] uppercase font-semibold text-slate-400">GitHub</span>
                <a
                  href={info.github_url.startsWith('http') ? info.github_url : `https://${info.github_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-slate-800 hover:text-slate-950 truncate block transition-colors inline-flex items-center gap-1 focus-visible:outline-2 focus-visible:outline-emerald-600"
                >
                  <span className="truncate">{info.github_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                  <ExternalLink className="w-3 h-3 shrink-0 opacity-70" aria-hidden="true" />
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Portfolio / Website */}
        {info.portfolio_url && (
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/70 border border-slate-200/60 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                <Globe className="w-4 h-4" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <span className="block text-[10px] uppercase font-semibold text-slate-400">Portfolio</span>
                <a
                  href={info.portfolio_url.startsWith('http') ? info.portfolio_url : `https://${info.portfolio_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-teal-700 hover:text-teal-900 truncate block transition-colors inline-flex items-center gap-1 focus-visible:outline-2 focus-visible:outline-emerald-600"
                >
                  <span className="truncate">{info.portfolio_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                  <ExternalLink className="w-3 h-3 shrink-0 opacity-70" aria-hidden="true" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
