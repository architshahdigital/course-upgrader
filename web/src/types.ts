export type Platform =
  | 'coursera'
  | 'udemy'
  | 'edx'
  | 'simplilearn'
  | 'great_learning'
  | 'google_digital_garage'
  | 'other'

export type Verdict = 'highly_recommended' | 'recommended' | 'partial_overlap' | 'redundant'

export type Price = 'free' | 'paid' | null

export interface CandidateProfile {
  name: string | null
  skills: string[]
  tools: string[]
  job_titles: string[]
  experience_years: number | null
  education: string[]
  career_goal: string | null
}

export interface Course {
  title: string
  url: string
  platform: Platform
  description: string
  price: Price
  provider: string | null
}

export interface CourseAnalysis {
  course: Course
  overlap_rate: number
  skill_delta: string[]
  match_score: number
  verdict: Verdict
  reasoning: string
}

export interface AnalyzeResponse {
  profile: CandidateProfile
  results: CourseAnalysis[]
}

export interface CheckCourseResponse {
  profile: CandidateProfile
  result: CourseAnalysis
}

export const PLATFORM_LABELS: Record<Platform, string> = {
  coursera: 'Coursera',
  udemy: 'Udemy',
  edx: 'edX',
  simplilearn: 'Simplilearn',
  great_learning: 'Great Learning',
  google_digital_garage: 'Google Digital Garage',
  other: 'Other',
}
