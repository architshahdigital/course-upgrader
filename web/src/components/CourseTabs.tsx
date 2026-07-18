import { motion } from 'framer-motion'

export type CourseFilter = 'all' | 'free' | 'paid'

interface CourseTabsProps {
  active: CourseFilter
  onChange: (filter: CourseFilter) => void
  counts: Record<CourseFilter, number>
}

const TABS: { key: CourseFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'free', label: 'Free Lessons' },
  { key: 'paid', label: 'Paid Lessons' },
]

export function CourseTabs({ active, onChange, counts }: CourseTabsProps) {
  return (
    <div className="glass-panel inline-flex gap-1 rounded-full p-1">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={`relative rounded-full px-4 py-2 text-sm font-medium transition-colors ${
            active === tab.key ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          {active === tab.key && (
            <motion.div
              layoutId="active-course-tab"
              className="absolute inset-0 rounded-full bg-violet-500/80"
              transition={{ type: 'spring', duration: 0.5, bounce: 0.15 }}
            />
          )}
          <span className="relative z-10">
            {tab.label} <span className="opacity-70">({counts[tab.key]})</span>
          </span>
        </button>
      ))}
    </div>
  )
}
