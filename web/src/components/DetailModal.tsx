import { AnimatePresence, motion } from 'framer-motion'
import { ExternalLink, X } from 'lucide-react'
import type { CandidateProfile, CourseAnalysis } from '../types'
import { PLATFORM_LABELS } from '../types'
import { RedundancyMeter } from './RedundancyMeter'

interface DetailModalProps {
  analysis: CourseAnalysis | null
  profile: CandidateProfile | null
  onClose: () => void
}

export function DetailModal({ analysis, profile, onClose }: DetailModalProps) {
  return (
    <AnimatePresence>
      {analysis && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.97 }}
            transition={{ type: 'spring', duration: 0.4, bounce: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="glass-panel relative max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-2xl p-6 sm:p-8"
          >
            <button
              type="button"
              onClick={onClose}
              className="absolute right-5 top-5 rounded-full p-1.5 text-zinc-400 hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex flex-wrap items-start justify-between gap-4 pr-8">
              <div>
                <p className="text-xs uppercase tracking-wide text-zinc-500">
                  {PLATFORM_LABELS[analysis.course.platform]}
                </p>
                <h2 className="mt-1 text-2xl font-semibold text-white">{analysis.course.title}</h2>
                {analysis.course.url && analysis.course.url !== 'N/A' && (
                  <a
                    href={analysis.course.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex items-center gap-1 text-sm text-violet-300 hover:text-violet-200"
                  >
                    Open course <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
              <div className="flex items-center gap-4">
                <RedundancyMeter overlapRate={analysis.overlap_rate} size={72} />
                <div className="text-right">
                  <p className="text-xs uppercase tracking-wide text-zinc-500">Match Score</p>
                  <p className="text-3xl font-bold text-white">{Math.round(analysis.match_score)}</p>
                </div>
              </div>
            </div>

            <p className="mt-6 rounded-xl bg-white/5 p-4 text-sm leading-relaxed text-zinc-300">
              {analysis.reasoning}
            </p>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  What you already know
                </p>
                <div className="flex max-h-48 flex-wrap gap-1.5 overflow-y-auto">
                  {(profile?.skills ?? [])
                    .concat(profile?.tools ?? [])
                    .slice(0, 40)
                    .map((skill) => (
                      <span key={skill} className="rounded-md bg-white/10 px-2 py-1 text-xs text-zinc-300">
                        {skill}
                      </span>
                    ))}
                </div>
              </div>
              <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-violet-300">
                  New skill delta
                </p>
                <div className="flex max-h-48 flex-wrap gap-1.5 overflow-y-auto">
                  {analysis.skill_delta.length ? (
                    analysis.skill_delta.map((skill) => (
                      <span key={skill} className="rounded-md bg-violet-500/20 px-2 py-1 text-xs text-violet-100">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-zinc-500">No new skills identified.</span>
                  )}
                </div>
              </div>
            </div>

            {analysis.course.description && (
              <div className="mt-6">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Course description
                </p>
                <p className="max-h-40 overflow-y-auto rounded-xl bg-white/5 p-4 text-sm leading-relaxed text-zinc-400">
                  {analysis.course.description}
                </p>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
