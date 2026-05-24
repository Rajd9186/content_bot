'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { api } from '@/lib/api'
import type { Claim } from '@/types'

interface EvidenceItem {
  id: string
  snippet: string
  relevance_score: number | null
  source_url: string | null
  source_domain: string | null
  source_trust_score: number | null
  claim_id: string | null
}

interface EvidencePanelProps {
  projectId: string
}

export default function EvidencePanel({ projectId }: EvidencePanelProps) {
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [avgRelevance, setAvgRelevance] = useState(0)
  const [viewMode, setViewMode] = useState<'list' | 'relationship'>('relationship')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evidenceData, claimsData] = await Promise.all([
          api.evidence.list(projectId),
          api.verification.getClaims(projectId)
        ])
        setEvidence(evidenceData.evidence)
        setAvgRelevance(evidenceData.average_relevance)
        setClaims(claimsData.claims)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load evidence')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [projectId])

  if (loading) return <LoadingSpinner message="Loading evidence and relationships..." />

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger-500">{error}</p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            onClick={() => setViewMode('relationship')}
            className={`px-4 py-1.5 text-xs font-medium border rounded-l-lg transition-colors ${
              viewMode === 'relationship' 
              ? 'bg-primary-600 text-white border-primary-600' 
              : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
            }`}
          >
            Relationship View
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-1.5 text-xs font-medium border rounded-r-lg transition-colors ${
              viewMode === 'list' 
              ? 'bg-primary-600 text-white border-primary-600' 
              : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
            }`}
          >
            Flat List
          </button>
        </div>
      </div>

      <Card
        title={viewMode === 'relationship' ? "Evidence Relationships" : "Evidence Sources"}
        subtitle={`${evidence.length} pieces of evidence (avg relevance: ${Math.round(avgRelevance * 100)}%)`}
      >
        <div className="space-y-6">
          {evidence.length === 0 && (
            <p className="text-sm text-gray-400">No evidence collected yet.</p>
          )}

          {viewMode === 'relationship' ? (
            <div className="space-y-8">
              {claims.length > 0 ? (
                claims.map(claim => {
                  const claimEvidence = evidence.filter(e => e.claim_id === claim.id);
                  if (claimEvidence.length === 0) return null;

                  return (
                    <div key={claim.id} className="relative pl-6 border-l-2 border-gray-100">
                      <div className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-primary-500 border-2 border-white" />
                      <div className="mb-4">
                        <Badge variant={claim.status === 'verified' ? 'success' : 'warning'} size="sm" className="mb-2">
                          Claim
                        </Badge>
                        <p className="text-sm font-medium text-gray-900 leading-snug">
                          {claim.claim_text}
                        </p>
                      </div>
                      <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
                        {claimEvidence.map(item => (
                          <div key={item.id} className="bg-gray-50 rounded-lg p-3 border border-gray-100 text-xs">
                            <p className="text-gray-600 mb-2 italic">"{item.snippet.substring(0, 150)}..."</p>
                            <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-200">
                              <span className="text-primary-600 truncate max-w-[150px] font-medium">{item.source_domain}</span>
                              <Badge variant="success" size="sm">Trust: {Math.round((item.source_trust_score || 0.7) * 100)}%</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-gray-400">No claim relationships identified.</p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {evidence.map((item) => (
                <div key={item.id} className="border border-gray-100 rounded-lg p-4 space-y-2">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {item.snippet.length > 300
                      ? `${item.snippet.substring(0, 300)}...`
                      : item.snippet}
                  </p>
                  <div className="flex items-center space-x-3 text-xs">
                    {item.source_domain && (
                      <Badge variant="info" size="sm">
                        {item.source_domain}
                      </Badge>
                    )}
                    {item.relevance_score !== null && (
                      <Badge
                        variant={item.relevance_score >= 0.8 ? 'success' : 'default'}
                        size="sm"
                      >
                        {Math.round(item.relevance_score * 100)}% relevant
                      </Badge>
                    )}
                    {item.source_trust_score !== null && (
                      <Badge
                        variant={item.source_trust_score >= 0.8 ? 'success' : 'warning'}
                        size="sm"
                      >
                        Trust: {Math.round(item.source_trust_score * 100)}%
                      </Badge>
                    )}
                  </div>
                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary-600 hover:text-primary-800 block truncate"
                    >
                      {item.source_url}
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
