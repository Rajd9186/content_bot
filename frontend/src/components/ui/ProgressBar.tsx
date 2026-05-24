interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  size?: 'sm' | 'md'
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

export default function ProgressBar({
  value,
  max = 1,
  label,
  size = 'md',
  color = 'blue',
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  const colors = {
    blue: 'bg-primary-500',
    green: 'bg-verified-500',
    yellow: 'bg-warning-500',
    red: 'bg-danger-500',
  }

  const heights = {
    sm: 'h-1.5',
    md: 'h-2.5',
  }

  return (
    <div className="space-y-1">
      {label && (
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">{label}</span>
          <span className="text-gray-900 font-medium">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${heights[size]}`}>
        <div
          className={`${colors[color]} ${heights[size]} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
