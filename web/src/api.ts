import type { AnalyzeResponse, CheckCourseResponse } from './types'

export class ApiError extends Error {}

async function parseErrorBody(response: Response): Promise<string> {
  try {
    const body = await response.json()
    return body.detail || response.statusText
  } catch {
    return response.statusText
  }
}

export interface AnalyzeOptions {
  resume: File
  goal: string
  platforms?: string[]
  maxCourses?: number
  llm?: string
  freeOnly?: boolean
}

export async function analyzeResume({
  resume,
  goal,
  platforms,
  maxCourses,
  llm,
  freeOnly,
}: AnalyzeOptions): Promise<AnalyzeResponse> {
  const form = new FormData()
  form.append('resume', resume)
  form.append('goal', goal)
  if (platforms && platforms.length) form.append('platforms', platforms.join(','))
  if (maxCourses) form.append('max_courses', String(maxCourses))
  if (llm) form.append('llm', llm)
  if (freeOnly) form.append('free_only', 'true')

  const response = await fetch('/api/analyze', { method: 'POST', body: form })
  if (!response.ok) throw new ApiError(await parseErrorBody(response))
  return response.json()
}

export interface CheckCourseOptions {
  resume: File
  goal: string
  course: string
  courseDescription?: string
  platform?: string
  llm?: string
}

export async function checkCourse({
  resume,
  goal,
  course,
  courseDescription,
  platform,
  llm,
}: CheckCourseOptions): Promise<CheckCourseResponse> {
  const form = new FormData()
  form.append('resume', resume)
  form.append('goal', goal)
  form.append('course', course)
  if (courseDescription) form.append('course_description', courseDescription)
  if (platform) form.append('platform', platform)
  if (llm) form.append('llm', llm)

  const response = await fetch('/api/check-course', { method: 'POST', body: form })
  if (!response.ok) throw new ApiError(await parseErrorBody(response))
  return response.json()
}
