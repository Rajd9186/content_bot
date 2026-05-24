'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ProgressBar from '@/components/ui/ProgressBar'
import { api } from '@/lib/api'

interface SourceItem {
  id: string
  url: string
  domain: string
  title: string | null
  trust_score: number | null
}

interface SourceTrustPanelProps {
  projectId: string
}

export default function SourceTrustPanel({ projectId }: SourceTrustPanelProps) {
  const [sources, setSources] = useState<SourceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [avgTrust, setAvgTrust] = useState(0)

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const data = await api.verification.getSources(projectId)
        setSources(data.sources)
        setAvgTrust(data.average_trust_score)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sources')
      } finally {
        setLoading(false)
      }
    }
    fetchSources()
  }, [projectId])

  if (loading) return <LoadingSpinner message="Loading source trust metrics..." />

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger-500">{error}</p>
      </Card>
    )
  }

  return (
    <Card
      title="Source Trust Scores"
      subtitle={`${sources.length} sources evaluated`}
    >
      <div className="space-y-4">
        <ProgressBar
          value={avgTrust}
          label="Average Trust Score"
          color={avgTrust >= 0.8 ? 'green' : avgTrust >= 0.6 ? 'blue' : 'yellow'}
        />

        <div className="space-y-2 mt-4">
          {sources.length === 0 && (
            <p className="text-sm text-gray-400">No sources collected yet.</p>
          )}
          {sources.map((source) => (
            <div
              key={source.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {source.title || source.url}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="info" size="sm">
                    {source.domain}
                  </Badge>
                  {source.trust_score !== null && (
                    <Badge
                      variant={source.trust_score >= 0.8 ? 'success' : source.trust_score >= 0.6 ? 'warning' : 'danger'}
                      size="sm"
                    >
                      {Math.round(source.trust_score * 100)}% trust
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
