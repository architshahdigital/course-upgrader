import { motion } from 'framer-motion'
import { ExternalLink, Sparkles } from 'lucide-react'
import type { CourseAnalysis, Verdict } from '../types'
import { PLATFORM_LABELS } from '../types'
import { RedundancyMeter } from './RedundancyMeter'

const VERDICT_STYLES: Record<Verdict, { label: string; badge: string; glow: string }> = {
  highly_recommended: {
    label: 'Highly Recommended',
    badge: 'border-emerald-500/30 bg-emerald-500/15 text-emerald-300',
    glow: 'shadow-[0_0_28px_-8px_rgba(16,185,129,0.55)]',
  },
  recommended: {
    label: 'Recommended',
    badge: 'border-green-500/30 bg-green-500/15 text-green-300',
    glow: 'shadow-[0_0_20px_-10px_rgba(34,197,94,0.4)]',
  },
  partial_overlap: {
    label: 'Partial Overlap',
    badge: 'border-amber-500/30 bg-amber-500/15 text-amber-300',
    glow: '',
  },
  redundant: {
    label: 'Redundant',
    badge: 'border-red-500/30 bg-red-500/15 text-red-300',
    glow: 'shadow-[0_0_20px_-10px_rgba(239,68,68,0.35)]',
  },
}

interface CourseCardProps {
  analysis: CourseAnalysis
  index: number
  onSelect: () => void
}

export function CourseCard({ analysis, index, onSelect }: CourseCardProps) {
  const style = VERDICT_STYLES[analysis.verdict] ?? VERDICT_STYLES.partial_overlap
  const { course } = analysis
  const hasUrl = Boolean(course.url) && course.url !== 'N/A'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index, 8) * 0.05 }}
      whileHover={{ y: -4 }}
      onClick={onSelect}
      className={`glass-panel group flex cursor-pointer flex-col rounded-2xl p-5 transition-shadow ${style.glow}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs uppercase tracking-wide text-zinc-500">
            {PLATFORM_LABELS[course.platform]}
          </p>
          <h3 className="mt-1 line-clamp-2 text-base font-semibold text-white">{course.title}</h3>
        </div>
        <RedundancyMeter overlapRate={analysis.overlap_rate} size={56} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style.badge}`}>{style.label}</span>
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
            course.price === 'free'
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              : course.price === 'paid'
                ? 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-300'
                : 'border-white/10 bg-white/5 text-zinc-400'
          }`}
        >
          {course.price === 'free' ? 'Free' : course.price === 'paid' ? 'Paid' : 'Price unknown'}
        </span>
        <span className="ml-auto text-sm font-semibold text-white">{Math.round(analysis.match_score)}/100</span>
      </div>

      {analysis.skill_delta.length > 0 && (
        <div className="mt-4">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-violet-300">
            <Sparkles className="h-3.5 w-3.5" />
            New skills you&apos;ll gain
          </div>
          <div className="flex flex-wrap gap-1.5">
            {analysis.skill_delta.slice(0, 4).map((skill) => (
              <span key={skill} className="rounded-md bg-violet-500/10 px-2 py-0.5 text-xs text-violet-200">
                {skill}
              </span>
            ))}
            {analysis.skill_delta.length > 4 && (
              <span className="rounded-md bg-white/5 px-2 py-0.5 text-xs text-zinc-400">
                +{analysis.skill_delta.length - 4} more
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mt-auto pt-4">
        {hasUrl && (
          <a
            href={course.url}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300"
          >
            View course <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </motion.div>
  )
}
