interface RedundancyMeterProps {
  overlapRate: number
  size?: number
}

function colorFor(rate: number): string {
  if (rate >= 70) return '#f87171' // red-400 — mostly redundant
  if (rate >= 40) return '#facb1d' // amber-400 — partial overlap
  return '#4ade80' // green-400 — mostly new
}

export function RedundancyMeter({ overlapRate, size = 64 }: RedundancyMeterProps) {
  const stroke = 6
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.min(100, Math.max(0, overlapRate))
  const offset = circumference - (clamped / 100) * circumference
  const color = colorFor(clamped)

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.3s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span className="text-sm font-semibold" style={{ color }}>
          {Math.round(clamped)}%
        </span>
        <span className="mt-0.5 text-[9px] uppercase tracking-wide text-zinc-500">overlap</span>
      </div>
    </div>
  )
}
