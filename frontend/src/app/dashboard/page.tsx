'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import type { VerificationDashboard, Project } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ConfidenceMeter from '@/components/dashboard/ConfidenceMeter'

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [dashboard, setDashboard] = useState<VerificationDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (selectedProject) {
      loadDashboard(selectedProject)
    }
  }, [selectedProject])

  const loadProjects = async () => {
    try {
      const list = await api.projects.list()
      setProjects(list)
      if (list.length > 0) {
        setSelectedProject(list[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  const loadDashboard = async (projectId: string) => {
    setDashboardLoading(true)
    try {
      const data = await api.verification.getDashboard(projectId)
      setDashboard(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setDashboardLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <LoadingSpinner size="lg" message="Loading dashboard..." />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Verification Dashboard</h1>
        <p className="text-gray-500 mt-1">
          View trust metrics, verification results, and source quality across all projects
        </p>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-500 text-danger-700 px-4 py-3 rounded-lg text-sm mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <Card title="Projects">
            {projects.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-gray-400 mb-4">No projects yet</p>
                <Link href="/">
                  <Button variant="primary" size="sm">Create Project</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => setSelectedProject(project.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedProject === project.id
                        ? 'bg-primary-50 border border-primary-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {project.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge
                        variant={
                          project.status === 'completed'
                            ? 'success'
                            : project.status === 'failed'
                            ? 'danger'
                            : 'default'
                        }
                        size="sm"
                      >
                        {project.status}
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="lg:col-span-3">
          {dashboardLoading ? (
            <LoadingSpinner message="Loading verification data..." />
          ) : dashboard ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900">
                      {dashboard.claims.total_claims}
                    </div>
                    <p className="text-sm text-gray-500">Total Claims</p>
                  </div>
                </Card>
                <Card>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-verified-700">
                      {dashboard.claims.verified_count}
                    </div>
                    <p className="text-sm text-gray-500">Verified</p>
                  </div>
                </Card>
                <Card>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-danger-700">
                      {dashboard.claims.contradicted_count + dashboard.claims.unsupported_count}
                    </div>
                    <p className="text-sm text-gray-500">Issues Found</p>
                  </div>
                </Card>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card title="Confidence Score">
                  <ConfidenceMeter
                    confidence={dashboard.claims.average_confidence}
                  />
                </Card>

                <Card title="Source Trust Score">
                  <ConfidenceMeter
                    confidence={dashboard.sources.average_trust_score}
                  />
                </Card>
              </div>

              <Card title="Content Overview">
                {dashboard.content.has_content ? (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {dashboard.content.word_count?.toLocaleString() || '-'}
                      </div>
                      <p className="text-xs text-gray-500">Word Count</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {dashboard.content.citations_count}
                      </div>
                      <p className="text-xs text-gray-500">Citations</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {dashboard.content.overall_confidence !== null
                          ? `${Math.round(dashboard.content.overall_confidence * 100)}%`
                          : '-'}
                      </div>
                      <p className="text-xs text-gray-500">Overall Confidence</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 text-center py-4">
                    Content not yet generated for this project
                  </p>
                )}
              </Card>

              <Card title="Claims Breakdown" subtitle="Status distribution">
                {dashboard.claims.items.length > 0 ? (
                  <div className="space-y-3">
                    {dashboard.claims.items.map((claim) => (
                      <div key={claim.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 truncate">{claim.claim_text}</p>
                          {claim.explanation && (
                            <p className="text-xs text-gray-500 mt-1">{claim.explanation}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          <Badge
                            variant={
                              claim.status === 'verified' ? 'success' :
                              claim.status === 'contradicted' ? 'danger' :
                              claim.status === 'unsupported' ? 'danger' : 'warning'
                            }
                            size="sm"
                          >
                            {claim.status}
                          </Badge>
                          {claim.confidence !== null && (
                            <span className="text-xs text-gray-500 w-12 text-right">
                              {Math.round(claim.confidence * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 text-center py-4">No claims extracted</p>
                )}
              </Card>

              <div className="text-center">
                <Link href={`/projects/${dashboard.project.id}`}>
                  <Button variant="primary">View Full Project Details</Button>
                </Link>
              </div>
            </div>
          ) : (
            <Card>
              <div className="text-center py-8">
                <p className="text-gray-400">Select a project to view verification metrics</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
