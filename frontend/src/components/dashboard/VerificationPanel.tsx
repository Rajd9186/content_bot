'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ConfidenceMeter from '@/components/dashboard/ConfidenceMeter'
import type { Claim } from '@/types'
import { api } from '@/lib/api'

interface VerificationPanelProps {
  projectId: string
}

export default function VerificationPanel({ projectId }: VerificationPanelProps) {
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<{
    total_claims: number
    verified_count: number
    unverified_count: number
    contradicted_count: number
    unsupported_count: number
    average_confidence: number
  } | null>(null)

  useEffect(() => {
    const fetchVerification = async () => {
      try {
        const data = await api.verification.getClaims(projectId)
        setClaims(data.claims)
        setSummary({
          total_claims: data.total_claims,
          verified_count: data.verified_count,
          unverified_count: data.unverified_count,
          contradicted_count: data.contradicted_count,
          unsupported_count: data.unsupported_count,
          average_confidence: data.average_confidence,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load verification')
      } finally {
        setLoading(false)
      }
    }
    fetchVerification()
  }, [projectId])

  if (loading) return <LoadingSpinner message="Loading verification results..." />

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger-500">{error}</p>
      </Card>
    )
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'verified': return 'success'
      case 'unverified': return 'warning'
      case 'contradicted': return 'danger'
      case 'unsupported': return 'danger'
      default: return 'default'
    }
  }

  return (
    <div className="space-y-6">
      {summary && (
        <Card title="Verification Summary">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{summary.total_claims}</div>
              <div className="text-xs text-gray-500">Total Claims</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-verified-700">{summary.verified_count}</div>
              <div className="text-xs text-gray-500">Verified</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-warning-700">{summary.unverified_count}</div>
              <div className="text-xs text-gray-500">Unverified</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-danger-700">{summary.contradicted_count}</div>
              <div className="text-xs text-gray-500">Contradicted</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{summary.unsupported_count}</div>
              <div className="text-xs text-gray-500">Unsupported</div>
            </div>
          </div>
          <div className="mt-4">
            <ConfidenceMeter confidence={summary.average_confidence} />
          </div>
        </Card>
      )}

      <Card title="Claims" subtitle={`${claims.length} claims extracted and analyzed`}>
        <div className="space-y-3">
          {claims.length === 0 && (
            <p className="text-sm text-gray-400">No claims extracted yet.</p>
          )}
          {claims.map((claim) => (
            <div key={claim.id} className="border border-gray-100 rounded-lg p-4 space-y-2">
              <div className="flex items-start justify-between">
                <p className="text-sm text-gray-900 flex-1">{claim.claim_text}</p>
                <Badge variant={getStatusVariant(claim.status)} size="sm">
                  {claim.status}
                </Badge>
              </div>
              <div className="flex items-center space-x-3 text-xs">
                {claim.confidence !== null && (
                  <span className="text-gray-500">
                    Confidence: {Math.round(claim.confidence * 100)}%
                  </span>
                )}
                {claim.category && (
                  <Badge variant="default" size="sm">
                    {claim.category}
                  </Badge>
                )}
              </div>
              {claim.explanation && (
                <p className="text-xs text-gray-500 mt-1">{claim.explanation}</p>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
