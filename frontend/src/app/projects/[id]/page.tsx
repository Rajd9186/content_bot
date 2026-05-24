'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import type { Project, GeneratedContent, ContentGenerateResponse } from '@/types'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ProgressBar from '@/components/ui/ProgressBar'
import ContentViewer from '@/components/dashboard/ContentViewer'
import EvidencePanel from '@/components/dashboard/EvidencePanel'
import VerificationPanel from '@/components/dashboard/VerificationPanel'
import SourceTrustPanel from '@/components/dashboard/SourceTrustPanel'
import ConfidenceMeter from '@/components/dashboard/ConfidenceMeter'
import WorkflowTracePanel from '@/components/dashboard/WorkflowTracePanel'
import ContradictionPanel from '@/components/dashboard/ContradictionPanel'
import HyperlinkPanel from '@/components/dashboard/HyperlinkPanel'
import ChatPanel from '@/components/dashboard/ChatPanel'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  planning: 'Planning Topic...',
  researching: 'Researching Sources...',
  verifying: 'Verifying Claims...',
  generating: 'Generating Content...',
  self_verifying: 'Self-Verifying...',
  completed: 'Completed',
  failed: 'Failed',
}

const STATUS_BADGE_VARIANTS: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
  draft: 'default',
  planning: 'info',
  researching: 'info',
  verifying: 'warning',
  generating: 'info',
  self_verifying: 'warning',
  completed: 'success',
  failed: 'danger',
}

export default function ProjectPage() {
  const params = useParams()
  const projectId = params.id as string

  const [project, setProject] = useState<Project | null>(null)
  const [content, setContent] = useState<GeneratedContent | null>(null)
  const [generateResponse, setGenerateResponse] = useState<ContentGenerateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'content' | 'evidence' | 'verification' | 'sources' | 'workflow' | 'contradictions' | 'hyperlinks'>('content')
  const [polling, setPolling] = useState(false)

  useEffect(() => {
    loadProject()
  }, [projectId])

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    if (polling) {
      interval = setInterval(async () => {
        try {
          const updated = await api.projects.get(projectId)
          setProject(updated)
          if (updated.status === 'completed' || updated.status === 'failed') {
            setPolling(false)
            if (updated.status === 'completed') {
              const c = await api.content.getLatest(projectId)
              setContent(c)
            }
          }
        } catch {
          setPolling(false)
        }
      }, 3000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [polling, projectId])

  const loadProject = async () => {
    try {
      const p = await api.projects.get(projectId)
      setProject(p)

      if (p.status === 'completed') {
        const c = await api.content.getLatest(projectId)
        setContent(c)
      }

      if (['planning', 'researching', 'verifying', 'generating', 'self_verifying'].includes(p.status)) {
        setPolling(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    setPolling(true)
    try {
      const result = await api.content.generate(projectId)
      setGenerateResponse(result)
      await loadProject()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed')
    } finally {
      setGenerating(false)
      setPolling(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16">
        <LoadingSpinner size="lg" message="Loading project..." />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <Card>
          <div className="text-center py-8">
            <p className="text-danger-500 mb-4">{error || 'Project not found'}</p>
            <Link href="/">
              <Button variant="secondary">Back to Home</Button>
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  const isGenerating = generating || ['planning', 'researching', 'verifying', 'generating', 'self_verifying'].includes(project.status)
  const isCompleted = project.status === 'completed'
  const hasContent = content !== null || generateResponse !== null

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/" className="text-sm text-primary-600 hover:text-primary-800 mb-2 inline-block">
          &larr; Back to Home
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            <p className="text-gray-500 mt-1">{project.topic}</p>
            <div className="flex items-center space-x-3 mt-2">
              <Badge variant={STATUS_BADGE_VARIANTS[project.status] || 'default'}>
                {STATUS_LABELS[project.status] || project.status}
              </Badge>
              <Badge variant="default">{project.tone}</Badge>
              <Badge variant="default">{project.content_type.replace('_', ' ')}</Badge>
              {project.target_audience && (
                <Badge variant="info">{project.target_audience}</Badge>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {!isCompleted && !isGenerating && (
              <Button onClick={handleGenerate} loading={generating} size="lg">
                Generate Verified Content
              </Button>
            )}
            {isCompleted && (
              <Link href={`/dashboard?project=${projectId}`}>
                <Button variant="secondary">View Dashboard</Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {project.outline && (
        <Card title="Topic Outline" className="mb-6">
          <div className="space-y-3">
            {(project.outline as any).sections?.map((section: any, idx: number) => (
              <div key={idx} className="border-l-2 border-primary-200 pl-4">
                <h4 className="font-medium text-gray-900">{section.heading}</h4>
                <p className="text-sm text-gray-500">{section.purpose}</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {section.key_points?.map((point: string, i: number) => (
                    <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {isGenerating && (
        <Card className="mb-6">
          <div className="text-center py-8">
            <LoadingSpinner size="lg" message={STATUS_LABELS[project.status] || 'Processing...'} />
            <div className="mt-6 max-w-md mx-auto">
              <ProgressBar
                value={
                  project.status === 'planning' ? 0.2 :
                  project.status === 'researching' ? 0.4 :
                  project.status === 'verifying' ? 0.6 :
                  project.status === 'generating' ? 0.8 :
                  project.status === 'self_verifying' ? 0.9 : 0
                }
                label="Pipeline Progress"
                color="blue"
              />
            </div>
          </div>
        </Card>
      )}

      {isCompleted && hasContent && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="border-b border-gray-200 mb-6">
              <nav className="flex space-x-4 overflow-x-auto">
                {(['content', 'evidence', 'verification', 'sources', 'workflow', 'contradictions', 'hyperlinks'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                      activeTab === tab
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab === 'contradictions' ? 'Contradictions' :
                    tab === 'hyperlinks' ? 'Hyperlinks' :
                    tab === 'workflow' ? 'Workflow' :
                    tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </nav>
            </div>

            {activeTab === 'content' && content && (
              <ContentViewer content={content} />
            )}

            {activeTab === 'evidence' && (
              <EvidencePanel projectId={projectId} />
            )}

            {activeTab === 'verification' && (
              <VerificationPanel projectId={projectId} />
            )}

            {activeTab === 'sources' && (
              <SourceTrustPanel projectId={projectId} />
            )}

            {activeTab === 'workflow' && (
              <WorkflowTracePanel projectId={projectId} />
            )}

            {activeTab === 'contradictions' && (
              <ContradictionPanel projectId={projectId} />
            )}

            {activeTab === 'hyperlinks' && (
              <HyperlinkPanel projectId={projectId} />
            )}
          </div>
          
          <div className="lg:col-span-1">
            <ChatPanel projectId={projectId} />
          </div>
        </div>
      )}

      {isCompleted && !hasContent && (
        <Card>
          <div className="text-center py-8 text-gray-500">
            <p>Project is marked as completed but no content was generated.</p>
            <Button onClick={handleGenerate} loading={generating} className="mt-4">
              Retry Generation
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
