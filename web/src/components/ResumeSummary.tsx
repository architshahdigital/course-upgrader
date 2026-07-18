import { motion } from 'framer-motion'
import { Briefcase, GraduationCap, Target } from 'lucide-react'
import type { CandidateProfile } from '../types'

interface ResumeSummaryProps {
  profile: CandidateProfile
}

export function ResumeSummary({ profile }: ResumeSummaryProps) {
  const allSkills = [...profile.skills, ...profile.tools]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-panel rounded-2xl p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">Candidate</p>
          <h2 className="text-xl font-semibold text-white">{profile.name ?? 'Your Profile'}</h2>
        </div>
        {profile.career_goal && (
          <div className="flex items-center gap-2 rounded-full bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
            <Target className="h-4 w-4" />
            {profile.career_goal}
          </div>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-white/5 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Briefcase className="h-4 w-4" />
            <span className="text-xs uppercase tracking-wide">Experience</span>
          </div>
          <p className="mt-2 text-2xl font-semibold text-white">
            {profile.experience_years ? `${profile.experience_years}y` : '—'}
          </p>
        </div>
        <div className="rounded-xl bg-white/5 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <GraduationCap className="h-4 w-4" />
            <span className="text-xs uppercase tracking-wide">Recent role</span>
          </div>
          <p
            className="mt-2 truncate text-sm font-medium text-white"
            title={profile.job_titles.join(', ')}
          >
            {profile.job_titles.slice(0, 1).join(', ') || '—'}
          </p>
        </div>
        <div className="rounded-xl bg-white/5 p-4">
          <span className="text-xs uppercase tracking-wide text-zinc-400">Skills detected</span>
          <p className="mt-2 text-2xl font-semibold text-white">{allSkills.length}</p>
        </div>
      </div>

      <div className="mt-6">
        <p className="mb-2 text-xs uppercase tracking-wider text-zinc-500">Skills &amp; tools</p>
        <div className="flex flex-wrap gap-2">
          {allSkills.slice(0, 24).map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-300"
            >
              {skill}
            </span>
          ))}
          {allSkills.length > 24 && (
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-500">
              +{allSkills.length - 24} more
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}
