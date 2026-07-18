import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { GraduationCap, Loader2, Search, Sparkles } from 'lucide-react'
import { UploadZone } from './components/UploadZone'
import { ResumeSummary } from './components/ResumeSummary'
import { CourseTabs, type CourseFilter } from './components/CourseTabs'
import { CourseCard } from './components/CourseCard'
import { DetailModal } from './components/DetailModal'
import { analyzeResume, checkCourse, ApiError } from './api'
import type { CandidateProfile, CourseAnalysis } from './types'
import { PLATFORM_LABELS } from './types'

const PLATFORM_OPTIONS = Object.entries(PLATFORM_LABELS).filter(([key]) => key !== 'other') as [
  keyof typeof PLATFORM_LABELS,
  string,
][]

function App() {
  const [resume, setResume] = useState<File | null>(null)
  const [goal, setGoal] = useState('')
  const [platforms, setPlatforms] = useState<string[]>([])
  const [freeOnly, setFreeOnly] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [results, setResults] = useState<CourseAnalysis[]>([])
  const [filter, setFilter] = useState<CourseFilter>('all')
  const [selected, setSelected] = useState<CourseAnalysis | null>(null)

  const [quickCourse, setQuickCourse] = useState('')
  const [quickLoading, setQuickLoading] = useState(false)
  const [quickError, setQuickError] = useState<string | null>(null)
  const [quickResult, setQuickResult] = useState<CourseAnalysis | null>(null)

  const canSubmit = Boolean(resume) && goal.trim().length > 0 && !loading

  const counts = useMemo(
    () => ({
      all: results.length,
      free: results.filter((r) => r.course.price === 'free').length,
      paid: results.filter((r) => r.course.price === 'paid').length,
    }),
    [results],
  )

  const filteredResults = useMemo(() => {
    if (filter === 'all') return results
    return results.filter((r) => r.course.price === filter)
  }, [results, filter])

  function togglePlatform(key: string) {
    setPlatforms((prev) => (prev.includes(key) ? prev.filter((p) => p !== key) : [...prev, key]))
  }

  async function handleSubmit() {
    if (!resume || !goal.trim()) return
    setLoading(true)
    setError(null)
    setResults([])
    setProfile(null)
    try {
      const data = await analyzeResume({ resume, goal: goal.trim(), platforms, freeOnly })
      setProfile(data.profile)
      setResults(data.results)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleQuickCheck() {
    if (!resume || !goal.trim() || !quickCourse.trim()) return
    setQuickLoading(true)
    setQuickError(null)
    setQuickResult(null)
    try {
      const data = await checkCourse({ resume, goal: goal.trim(), course: quickCourse.trim() })
      setQuickResult(data.result)
    } catch (err) {
      setQuickError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setQuickLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas pb-24">
      <header className="border-b border-white/5 px-6 py-6">
        <div className="mx-auto flex max-w-6xl items-center gap-3">
          <div className="rounded-xl bg-violet-500/10 p-2 text-violet-400">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">Course Upgrader</h1>
            <p className="text-sm text-zinc-500">Stop taking redundant courses. Find your real skill delta.</p>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-10 max-w-6xl px-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
          {/* Left column: input form */}
          <div className="flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel rounded-2xl p-6"
            >
              <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">1. Your resume</h2>
              <div className="mt-3">
                <UploadZone file={resume} onFileSelected={setResume} />
              </div>

              <h2 className="mt-6 text-sm font-semibold uppercase tracking-wide text-zinc-400">2. Career goal</h2>
              <input
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="e.g. Machine Learning Engineer"
                className="mt-3 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:border-violet-400/60 focus:outline-none"
              />

              <h2 className="mt-6 text-sm font-semibold uppercase tracking-wide text-zinc-400">
                3. Platforms (optional)
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {PLATFORM_OPTIONS.map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => togglePlatform(key)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                      platforms.includes(key)
                        ? 'border-violet-400/60 bg-violet-500/20 text-violet-200'
                        : 'border-white/10 bg-white/5 text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <label className="mt-5 flex items-center gap-2 text-sm text-zinc-400">
                <input
                  type="checkbox"
                  checked={freeOnly}
                  onChange={(e) => setFreeOnly(e.target.checked)}
                  className="h-4 w-4 rounded border-white/20 bg-white/5 text-violet-500 focus:ring-0"
                />
                Only show free courses
              </label>

              <button
                type="button"
                disabled={!canSubmit}
                onClick={handleSubmit}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-500 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-violet-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-zinc-500"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" /> Find my courses
                  </>
                )}
              </button>

              {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
            </motion.div>

            {/* Quick single-course check */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="glass-panel rounded-2xl p-6"
            >
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">
                <Search className="h-4 w-4" /> Quick check a specific course
              </h2>
              <p className="mt-2 text-xs text-zinc-500">Already found a course? Paste its name or URL.</p>
              <input
                value={quickCourse}
                onChange={(e) => setQuickCourse(e.target.value)}
                placeholder="Course name or URL"
                className="mt-3 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:border-violet-400/60 focus:outline-none"
              />
              <button
                type="button"
                disabled={!resume || !goal.trim() || !quickCourse.trim() || quickLoading}
                onClick={handleQuickCheck}
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:text-zinc-500"
              >
                {quickLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Checking...
                  </>
                ) : (
                  'Is it worth it?'
                )}
              </button>
              {quickError && <p className="mt-3 text-sm text-red-400">{quickError}</p>}
              {quickResult && (
                <div className="mt-4">
                  <CourseCard analysis={quickResult} index={0} onSelect={() => setSelected(quickResult)} />
                </div>
              )}
            </motion.div>
          </div>

          {/* Right column: results */}
          <div className="flex flex-col gap-6">
            <AnimatePresence>
              {profile && <ResumeSummary key="summary" profile={profile} />}
            </AnimatePresence>

            {results.length > 0 && (
              <div className="flex items-center justify-between">
                <CourseTabs active={filter} onChange={setFilter} counts={counts} />
                <p className="text-sm text-zinc-500">{filteredResults.length} courses</p>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <AnimatePresence>
                {filteredResults.map((analysis, index) => (
                  <CourseCard
                    key={analysis.course.url + analysis.course.title}
                    analysis={analysis}
                    index={index}
                    onSelect={() => setSelected(analysis)}
                  />
                ))}
              </AnimatePresence>
            </div>

            {!loading && !profile && results.length === 0 && (
              <div className="glass-panel flex flex-col items-center justify-center rounded-2xl px-8 py-20 text-center">
                <GraduationCap className="h-10 w-10 text-zinc-700" />
                <p className="mt-4 max-w-sm text-sm text-zinc-500">
                  Upload your resume and tell us your career goal to see which courses actually teach you
                  something new.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <DetailModal analysis={selected} profile={profile} onClose={() => setSelected(null)} />
    </div>
  )
}

export default App
