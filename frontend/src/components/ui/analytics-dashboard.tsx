"use client";
import { cn } from "@/lib/utils";
import React, { useRef, useEffect, useState } from 'react';

export type AnalyticsDashboardProps = {
  totalMessages: number;
  totalReplies: number;
  totalMeetings: number;
  companiesCount: number;
  contactsCount: number;
  campaignsCount: number;
  replyRate: number;   // 0.0–1.0
  meetingRate: number; // 0.0–1.0
};

export const MinimalProfessionalCard = ({
  totalMessages,
  totalReplies,
  totalMeetings,
  companiesCount,
  contactsCount,
  campaignsCount,
  replyRate,
  meetingRate,
}: AnalyticsDashboardProps) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Progress ring = reply rate (capped at 100%), min 5% so ring is visible
  const progress = totalMessages > 0 ? Math.max(Math.round(replyRate * 100), 1) : 0;
  const circumference = 2 * Math.PI * 20;
  const strokeDashoffset = circumference - (circumference * Math.min(progress, 100)) / 100;

  useEffect(() => {
    const card = cardRef.current;
    if (!card) return;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 6;
      const rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -6;
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    };
    const handleMouseEnter = () => setIsHovered(true);
    const handleMouseLeave = () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
      setIsHovered(false);
    };
    card.addEventListener('mousemove', handleMouseMove);
    card.addEventListener('mouseenter', handleMouseEnter);
    card.addEventListener('mouseleave', handleMouseLeave);
    return () => {
      card.removeEventListener('mousemove', handleMouseMove);
      card.removeEventListener('mouseenter', handleMouseEnter);
      card.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  const replyPct = totalMessages > 0 ? (replyRate * 100).toFixed(1) + '%' : '—';
  const meetingPct = totalReplies > 0 ? (meetingRate * 100).toFixed(1) + '%' : '—';

  // Key insights derived from real data
  const insights: string[] = [];
  if (replyRate >= 0.05) insights.push(`Strong reply rate at ${replyPct}`);
  else if (totalMessages > 0) insights.push(`Reply rate ${replyPct} — room to improve copy`);
  if (contactsCount > 0 && companiesCount > 0)
    insights.push(`${(contactsCount / companiesCount).toFixed(1)} contacts per company avg`);
  if (totalMeetings > 0)
    insights.push(`${totalMeetings} meeting${totalMeetings > 1 ? 's' : ''} booked across ${campaignsCount} campaign${campaignsCount !== 1 ? 's' : ''}`);
  if (insights.length === 0) insights.push('Run Skills 4 & 5 to generate outreach data');

  return (
    <div className="flex items-center justify-center w-full p-8 bg-neutral-950">
      <div
        ref={cardRef}
        className="w-full max-w-lg rounded-2xl p-8 transition-all duration-300 ease-out bg-neutral-900 border border-neutral-800
          shadow-[0_1px_3px_rgba(0,0,0,0.4),0_10px_40px_rgba(0,0,0,0.5)]
          hover:shadow-[0_1px_3px_rgba(0,0,0,0.4),0_20px_60px_rgba(0,0,0,0.7)]"
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold mb-1 text-white">
              Outreach Overview
            </h1>
            <p className="text-sm text-neutral-500">
              {campaignsCount} active campaign{campaignsCount !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Progress Ring — reply rate */}
          <div className="relative">
            <svg width="60" height="60" style={{ animation: 'float 3s ease-in-out infinite' }}>
              <defs>
                <linearGradient id="sq-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
              <circle cx="30" cy="30" r="20" fill="none" stroke="currentColor" strokeWidth="4" className="text-neutral-800" />
              <circle
                cx="30" cy="30" r="20" fill="none"
                stroke={totalMessages > 0 ? "url(#sq-gradient)" : "#404040"}
                strokeWidth="4" strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-700 -rotate-90 origin-center"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[10px] font-bold text-white leading-none">{replyPct}</span>
              <span className="text-[8px] text-neutral-500 leading-none mt-0.5">reply</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 relative border-b border-neutral-800">
            {['overview', 'pipeline', 'insights'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-4 py-2 text-sm font-medium capitalize transition-colors relative z-10",
                  activeTab === tab ? 'text-indigo-400' : 'text-neutral-500 hover:text-neutral-300'
                )}
              >
                {tab}
              </button>
            ))}
            <div
              className="absolute bottom-0 h-0.5 bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300 ease-in-out"
              style={{
                left: activeTab === 'overview' ? '0px' : activeTab === 'pipeline' ? '96px' : '192px',
                width: '96px',
              }}
            />
          </div>
        </div>

        {/* Tab content */}
        <div className="space-y-4">
          {activeTab === 'overview' && (
            <>
              <div className="rounded-lg p-4 border bg-neutral-800/50 border-neutral-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-neutral-400">Messages Sent</span>
                  {totalMessages > 0 && (
                    <span className="text-xs px-2 py-1 rounded-full text-indigo-400 bg-indigo-900/30">
                      {totalReplies} replies
                    </span>
                  )}
                </div>
                <p className="text-2xl font-semibold text-gray-100">{totalMessages.toLocaleString() || '0'}</p>
                <div className="mt-3 h-1.5 rounded-full overflow-hidden bg-neutral-700">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-700"
                    style={{ width: isHovered ? `${Math.min(progress + 8, 100)}%` : `${Math.min(progress, 100)}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Reply Rate', value: replyPct },
                  { label: 'Meetings', value: totalMeetings.toString() },
                  { label: 'Meeting %', value: meetingPct },
                ].map((metric) => (
                  <div key={metric.label} className="rounded-lg p-3 border bg-neutral-800/50 border-neutral-700">
                    <p className="text-xs mb-1 text-neutral-500">{metric.label}</p>
                    <p className="text-lg font-semibold text-neutral-200">{metric.value}</p>
                  </div>
                ))}
              </div>
            </>
          )}

          {activeTab === 'pipeline' && (
            <div className="space-y-3">
              {[
                { color: 'bg-indigo-500', label: 'Companies Discovered', value: companiesCount.toLocaleString() },
                { color: 'bg-violet-500', label: 'Contacts Enriched', value: contactsCount.toLocaleString() },
                { color: 'bg-emerald-500', label: 'Replies Received', value: totalReplies.toLocaleString() },
                { color: 'bg-amber-500', label: 'Meetings Booked', value: totalMeetings.toLocaleString() },
              ].map((item, index) => (
                <div key={item.label} className={cn("flex items-center justify-between py-3", index < 3 ? 'border-b border-neutral-800' : '')}>
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${item.color}`} />
                    <span className="text-sm text-neutral-300">{item.label}</span>
                  </div>
                  <span className="text-sm font-medium text-white">{item.value}</span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'insights' && (
            <div className="space-y-3">
              <div className="rounded-lg p-4 border bg-gradient-to-r from-indigo-900/20 to-violet-900/20 border-neutral-700">
                <h3 className="text-sm font-medium mb-2 text-gray-100">Campaign Health</h3>
                <p className="text-xs leading-relaxed text-neutral-400">
                  {totalMessages > 0
                    ? `${totalMessages.toLocaleString()} messages sent across ${campaignsCount} campaign${campaignsCount !== 1 ? 's' : ''}. Reply rate is ${replyPct}${replyRate >= 0.05 ? ' — on target.' : ' — consider refreshing copy.'}`
                    : 'No messages sent yet. Run Skills 3–5 to launch outreach.'}
                </p>
              </div>
              <div className="rounded-lg p-4 border bg-neutral-800/50 border-neutral-700">
                <h3 className="text-sm font-medium mb-2 text-gray-100">Key Signals</h3>
                <ul className="space-y-2">
                  {insights.map((insight) => (
                    <li key={insight} className="flex items-start space-x-2">
                      <span className="text-xs mt-0.5 text-neutral-600">›</span>
                      <span className="text-xs text-neutral-400">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 flex gap-3">
          <button
            onClick={() => setActiveTab('pipeline')}
            className="flex-1 py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-lg font-medium text-sm hover:from-indigo-500 hover:to-violet-500 transition-all duration-200 shadow-sm hover:shadow-indigo-900/40 hover:shadow-lg"
          >
            View Pipeline
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className="flex-1 py-2.5 px-4 rounded-lg font-medium text-sm transition-all duration-200 border bg-neutral-800 text-neutral-300 hover:bg-neutral-700 border-neutral-700"
          >
            Insights
          </button>
        </div>
      </div>
    </div>
  );
};
