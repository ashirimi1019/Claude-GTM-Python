'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Plus, X } from 'lucide-react';

// ---------------------------------------------------------------------------
// PillButton — toggle pill with active / inactive / danger states
// ---------------------------------------------------------------------------

export function PillButton({
  active,
  danger = false,
  onClick,
  disabled = false,
  children,
  className,
}: {
  active: boolean;
  danger?: boolean;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
        active && !danger && 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300',
        active && danger && 'bg-red-500/15 border-red-500/40 text-red-300',
        !active && 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
        disabled && 'opacity-30 cursor-not-allowed',
        className,
      )}
      aria-pressed={active}
    >
      {children}
    </button>
  );
}

// ---------------------------------------------------------------------------
// NumberInput — dark styled number input with label
// ---------------------------------------------------------------------------

export function NumberInput({
  label,
  value,
  onChange,
  placeholder,
  suffix,
  prefix,
  min,
  max,
  helpText,
}: {
  label: string;
  value: number | undefined | null;
  onChange: (v: number | undefined) => void;
  placeholder?: string;
  suffix?: string;
  prefix?: string;
  min?: number;
  max?: number;
  helpText?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-neutral-400">{label}</label>
      <div className="flex items-center gap-1">
        {prefix && <span className="text-xs text-neutral-500">{prefix}</span>}
        <input
          type="number"
          value={value ?? ''}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === '') {
              onChange(undefined);
            } else {
              const n = parseInt(raw, 10);
              if (!isNaN(n) && (min === undefined || n >= min) && (max === undefined || n <= max)) {
                onChange(n);
              }
            }
          }}
          placeholder={placeholder}
          min={min}
          max={max}
          className={cn(
            'w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder:text-neutral-600',
          )}
        />
        {suffix && <span className="text-xs text-neutral-500">{suffix}</span>}
      </div>
      {helpText && <p className="text-[10px] text-neutral-600">{helpText}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TagInput — input with tag pills, suggestion chips, add/remove
// ---------------------------------------------------------------------------

export function TagInput({
  label,
  tags,
  onChange,
  suggestions,
  placeholder,
  variant = 'default',
}: {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
  variant?: 'default' | 'danger' | 'amber';
}) {
  const [inputValue, setInputValue] = useState('');

  const addTag = (tag: string) => {
    const cleaned = tag.trim();
    if (cleaned && !tags.some((t) => t.toLowerCase() === cleaned.toLowerCase())) {
      onChange([...tags, cleaned]);
    }
    setInputValue('');
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    }
  };

  const available = suggestions?.filter((s) => !tags.some((t) => t.toLowerCase() === s.toLowerCase())) ?? [];

  const pillClass = (active: boolean) => {
    if (!active) return 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300';
    if (variant === 'danger') return 'bg-red-500/15 border-red-500/40 text-red-300';
    if (variant === 'amber') return 'bg-amber-500/15 border-amber-500/40 text-amber-300';
    return 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300';
  };

  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-neutral-400">{label}</label>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => removeTag(tag)}
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
                pillClass(true),
              )}
            >
              {tag}
              <X className="w-3 h-3" />
            </button>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Type and press Enter'}
          className={cn(
            'flex-1 bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder:text-neutral-600',
          )}
        />
        <button
          type="button"
          onClick={() => addTag(inputValue)}
          disabled={!inputValue.trim()}
          className="p-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-400 hover:text-white hover:border-neutral-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
      {available.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {available.slice(0, 8).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => addTag(s)}
              className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-500 hover:text-neutral-300 hover:border-neutral-600 transition-colors"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section — collapsible section with chevron, title, optional badge
// ---------------------------------------------------------------------------

export function Section({
  title,
  defaultOpen = false,
  badge,
  badgeVariant = 'default',
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  badge?: string;
  badgeVariant?: 'default' | 'amber' | 'danger';
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  const badgeClass =
    badgeVariant === 'amber'
      ? 'bg-amber-900/50 text-amber-300 border-amber-700/50'
      : badgeVariant === 'danger'
        ? 'bg-red-900/50 text-red-300 border-red-700/50'
        : 'bg-neutral-700 text-neutral-300 border-neutral-600';

  return (
    <div className="border border-neutral-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-neutral-300 bg-neutral-900/50 hover:bg-neutral-900 transition-colors"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        {title}
        {badge && (
          <span className={cn('ml-auto text-[10px] px-1.5 py-0.5 rounded border', badgeClass)}>
            {badge}
          </span>
        )}
      </button>
      {open && <div className="px-3 py-3 space-y-3 bg-neutral-950/50">{children}</div>}
    </div>
  );
}
