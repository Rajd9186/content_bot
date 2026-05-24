'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { api } from '@/lib/api'
import type { Contradiction } from '@/types'

interface ContradictionPanelProps {
  projectId: string
}

const SEVERITY_COLORS: Record<string, 'danger' | 'warning' | 'info'> = {
  high: 'danger',
  medium: 'warning',
  low: 'info',
}

export default function ContradictionPanel({ projectId }: ContradictionPanelProps) {
  const [contradictions, setContradictions] = useState<Contradiction[]>([])
  const [resolving, setResolving] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.workflow.getContradictions(projectId)
        setContradictions(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contradictions')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [projectId])

  const handleResolve = async (id: string) => {
    setResolving((prev) => ({ ...prev, [id]: true }))
    try {
      await api.workflow.resolveContradiction(projectId, id, 'Reviewed and accepted as contextual difference')
      setContradictions((prev) =>
        prev.map((c) => (c.id === id ? { ...c, resolved: true } : c))
      )
    } catch {
      // ignore
    } finally {
      setResolving((prev) => ({ ...prev, [id]: false }))
    }
  }

  if (loading) return <LoadingSpinner message="Loading contradictions..." />

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger-500">{error}</p>
      </Card>
    )
  }

  if (contradictions.length === 0) {
    return (
      <Card title="Contradiction Analysis" subtitle="No contradictions detected">
        <div className="text-center py-6 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <p className="text-sm">All claims are consistent — no contradictions found.</p>
        </div>
      </Card>
    )
  }

  const highCount = contradictions.filter((c) => c.severity === 'high' && !c.resolved).length
  const unresolved = contradictions.filter((c) => !c.resolved).length

  return (
    <Card
      title="Contradiction Analysis"
      subtitle={`${contradictions.length} found — ${highCount} high severity, ${unresolved} unresolved`}
    >
      <div className="space-y-4">
        {contradictions.map((c) => (
          <div
            key={c.id}
            className={`border rounded-lg p-4 ${
              c.resolved ? 'border-green-200 bg-green-50/30' :
              c.severity === 'high' ? 'border-red-200 bg-red-50/30' :
              c.severity === 'medium' ? 'border-yellow-200 bg-yellow-50/30' :
              'border-gray-200'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Badge variant={SEVERITY_COLORS[c.severity] || 'default'} size="sm">
                  {c.severity}
                </Badge>
                {c.resolved && (
                  <Badge variant="success" size="sm">Resolved</Badge>
                )}
              </div>
              {!c.resolved && (
                <button
                  onClick={() => handleResolve(c.id)}
                  disabled={resolving[c.id]}
                  className="text-xs text-primary-600 hover:text-primary-800 disabled:opacity-50"
                >
                  {resolving[c.id] ? 'Resolving...' : 'Mark Resolved'}
                </button>
              )}
            </div>

            <p className="text-sm text-gray-800 mb-3">{c.claim_text}</p>

            {c.conflicting_sources && c.conflicting_sources.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Conflicting Sources</p>
                {c.conflicting_sources.map((cs, idx) => (
                  <div key={idx} className="text-xs bg-white rounded border border-gray-100 p-2">
                    <span className="font-medium text-gray-700">{cs.source}:</span>{' '}
                    <span className="text-gray-500">{cs.statement}</span>
                  </div>
                ))}
              </div>
            )}

            {c.explanation && (
              <p className="text-xs text-gray-500 mt-2 italic">{c.explanation}</p>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}
