import React from 'react';
import { ShieldCheck, Calendar, ExternalLink, KeyRound } from 'lucide-react';
import { Certification } from '../../types/resume';

export interface CertificationsSectionProps {
  certifications?: Certification[] | null;
}

export const CertificationsSection: React.FC<CertificationsSectionProps> = ({
  certifications = [],
}) => {
  const hasItems = certifications && certifications.length > 0;

  return (
    <section
      aria-labelledby="certifications-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="certifications-heading" className="text-base font-bold text-slate-900">
              Certifications &amp; Licenses
            </h2>
            <p className="text-xs text-slate-500">Verified credentials &amp; industry certifications</p>
          </div>
        </div>
        {hasItems && (
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {certifications.length} {certifications.length === 1 ? 'credential' : 'credentials'}
          </span>
        )}
      </div>

      {!hasItems ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Certifications Recorded</p>
          <p className="text-xs text-slate-400 mt-1">
            No professional licenses or certificates were listed in this resume.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {certifications.map((cert, idx) => (
            <article
              key={`${cert.name}-${idx}`}
              className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-slate-900">{cert.name}</h3>
                  {cert.url && (
                    <a
                      href={cert.url.startsWith('http') ? cert.url : `https://${cert.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-amber-700 hover:text-amber-900 shrink-0 focus-visible:outline-2 focus-visible:outline-emerald-600"
                      title="Verify credential"
                      aria-label={`Verify ${cert.name} credential`}
                    >
                      <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
                    </a>
                  )}
                </div>

                {cert.issuer && (
                  <div className="text-xs font-medium text-slate-600 mb-2">
                    {cert.issuer}
                  </div>
                )}

                {cert.credential_id && (
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono mb-2">
                    <KeyRound className="w-3 h-3 text-slate-400" aria-hidden="true" />
                    <span>ID: {cert.credential_id}</span>
                  </div>
                )}
              </div>

              {(cert.issue_date || cert.expiration_date) && (
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" aria-hidden="true" />
                    <span>Issued: {cert.issue_date || 'N/A'}</span>
                  </span>
                  {cert.expiration_date && (
                    <span>Expires: {cert.expiration_date}</span>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
