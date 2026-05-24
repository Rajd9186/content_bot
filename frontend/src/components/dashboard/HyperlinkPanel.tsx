'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ProgressBar from '@/components/ui/ProgressBar'
import { api } from '@/lib/api'
import type { HyperlinkValidation, HyperlinkSummary } from '@/types'

interface HyperlinkPanelProps {
  projectId: string
}

const STATUS_BADGE: Record<string, 'success' | 'danger' | 'warning' | 'default'> = {
  valid: 'success',
  broken: 'danger',
  suspicious: 'warning',
  unknown: 'default',
  pending: 'default',
}

export default function HyperlinkPanel({ projectId }: HyperlinkPanelProps) {
  const [hyperlinks, setHyperlinks] = useState<HyperlinkValidation[]>([])
  const [summary, setSummary] = useState<HyperlinkSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [hl, sm] = await Promise.all([
          api.workflow.getHyperlinks(projectId),
          api.workflow.getHyperlinkSummary(projectId).catch(() => null),
        ])
        setHyperlinks(hl)
        setSummary(sm)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load hyperlinks')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [projectId])

  if (loading) return <LoadingSpinner message="Loading hyperlink validation..." />

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger-500">{error}</p>
      </Card>
    )
  }

  if (hyperlinks.length === 0) {
    return (
      <Card title="Hyperlink Validation" subtitle="Citation link verification">
        <div className="text-center py-6 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <p className="text-sm">No links to validate. Generate content first.</p>
        </div>
      </Card>
    )
  }

  const verifiedCount = hyperlinks.filter((h) => h.is_verified).length

  return (
    <Card
      title="Hyperlink Validation"
      subtitle={`${hyperlinks.length} links checked — ${verifiedCount} verified`}
    >
      {summary && (
        <div className="mb-6">
          <ProgressBar
            value={summary.verification_rate}
            label="Verification Rate"
            color={summary.verification_rate >= 0.8 ? 'green' : summary.verification_rate >= 0.5 ? 'yellow' : 'red'}
          />
          <div className="grid grid-cols-4 gap-3 mt-4">
            <div className="text-center p-2 bg-gray-50 rounded text-sm">
              <span className="font-bold text-gray-900">{summary.total}</span>
              <span className="text-gray-500 ml-1">total</span>
            </div>
            <div className="text-center p-2 bg-verified-50 rounded text-sm">
              <span className="font-bold text-verified-700">{summary.verified}</span>
              <span className="text-verified-600 ml-1">verified</span>
            </div>
            <div className="text-center p-2 bg-danger-50 rounded text-sm">
              <span className="font-bold text-danger-700">{summary.broken}</span>
              <span className="text-danger-600 ml-1">broken</span>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded text-sm">
              <span className="font-bold text-gray-900">{summary.pending}</span>
              <span className="text-gray-500 ml-1">pending</span>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {hyperlinks.map((hl) => (
          <div
            key={hl.id}
            className="flex items-start space-x-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50"
          >
            <div className="flex-shrink-0 mt-0.5">
              {hl.is_verified ? (
                <svg className="w-4 h-4 text-verified-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-warning-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <Badge variant={STATUS_BADGE[hl.status] || 'default'} size="sm">
                  {hl.status}
                </Badge>
                {hl.label && (
                  <span className="text-xs text-gray-500 truncate">{hl.label}</span>
                )}
              </div>
              <a
                href={hl.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary-600 hover:text-primary-800 hover:underline truncate block mt-0.5"
              >
                {hl.url}
              </a>
              {hl.error_message && (
                <p className="text-xs text-danger-500 mt-0.5">{hl.error_message}</p>
              )}
              {hl.resolved_url && (
                <p className="text-xs text-gray-400 mt-0.5">Resolved: {hl.resolved_url}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
