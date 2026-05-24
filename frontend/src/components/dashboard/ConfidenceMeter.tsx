'use client'

import ProgressBar from '@/components/ui/ProgressBar'

interface ConfidenceMeterProps {
  confidence: number | null
  size?: 'sm' | 'md'
}

export default function ConfidenceMeter({ confidence, size = 'md' }: ConfidenceMeterProps) {
  if (confidence === null || confidence === undefined) {
    return (
      <div className="text-sm text-gray-400">
        No confidence score available
      </div>
    )
  }

  const getColor = (value: number) => {
    if (value >= 0.8) return 'green'
    if (value >= 0.6) return 'blue'
    if (value >= 0.4) return 'yellow'
    return 'red'
  }

  const getLabel = (value: number) => {
    if (value >= 0.9) return 'Very High Confidence'
    if (value >= 0.8) return 'High Confidence'
    if (value >= 0.6) return 'Moderate Confidence'
    if (value >= 0.4) return 'Low Confidence'
    return 'Very Low Confidence'
  }

  return (
    <div className="space-y-2">
      <ProgressBar
        value={confidence}
        label={getLabel(confidence)}
        color={getColor(confidence)}
        size={size}
      />
    </div>
  )
}
