'use client'

import { useState, useEffect } from 'react'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ProgressBar from '@/components/ui/ProgressBar'
import { api } from '@/lib/api'
import type { WorkflowExecution, WorkflowTelemetry } from '@/types'

interface WorkflowTracePanelProps {
  projectId: string
}

const NODE_LABELS: Record<string, string> = {
  planner: 'Task Planning',
  research: 'Parallel Research',
  claim_extraction: 'Claim Extraction',
  contradiction_detection: 'Contradiction Detection',
  content_writer: 'Content Writing',
  critique: 'Critique',
  revision: 'Revision',
  self_verification: 'Self Verification',
  hyperlink_validation: 'Hyperlink Validation',
}

const NODE_ORDER = [
  'planner', 'research', 'claim_extraction', 'contradiction_detection',
  'content_writer', 'critique', 'revision', 'self_verification', 'hyperlink_validation',
]

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.round(ms)}ms`
}

export default function WorkflowTracePanel({ projectId }: WorkflowTracePanelProps) {
  const [workflow, setWorkflow] = useState<WorkflowExecution | null>(null)
  const [telemetry, setTelemetry] = useState<WorkflowTelemetry | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    const fetchData = async () => {
      try {
        const [wf, tel] = await Promise.all([
          api.workflow.get(projectId),
          api.workflow.getTelemetry(projectId),
        ])
        setWorkflow(wf)
        setTelemetry(tel)
        
        // If workflow is still running, poll every 2 seconds
        if (wf && (wf.status === 'running' || wf.status === 'queued')) {
           if (!interval) {
             interval = setInterval(fetchData, 2000)
           }
        } else if (interval) {
           clearInterval(interval)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load workflow data')
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [projectId])

  if (loading) return <LoadingSpinner message="Loading workflow trace..." />

  if (error || !workflow) {
    return (
      <Card>
        <p className="text-sm text-gray-400">
          {error || 'No workflow execution found. Generate content using v2 mode first.'}
        </p>
      </Card>
    )
  }

  const nodeDurations = telemetry?.node_durations || {}

  const getNodeBadge = (nodeName: string) => {
    const step = workflow.steps.find((s) => s.node_name === nodeName)
    if (!step) {
      if (workflow.current_node === nodeName && workflow.status === 'running') return 'warning' as const;
      return 'default' as const
    }
    return step.status === 'completed' ? 'success' as const : step.status === 'failed' ? 'danger' as const : 'warning' as const
  }

  return (
    <div className="space-y-6">
      <Card title="Workflow Telemetry" subtitle={workflow.status === 'running' ? "Execution in progress..." : "Multi-agent execution summary"}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {formatMs(telemetry?.total_duration_ms || 0)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Total Duration</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{telemetry?.total_sources || 0}</div>
            <div className="text-xs text-gray-500 mt-1">Sources Collected</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{telemetry?.total_claims || 0}</div>
            <div className="text-xs text-gray-500 mt-1">Claims Extracted</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{telemetry?.revision_count || 0}</div>
            <div className="text-xs text-gray-500 mt-1">Revisions Made</div>
          </div>
        </div>
        {telemetry && (
          <div className="mt-4">
            <ProgressBar
              value={telemetry.overall_quality_score}
              label="Overall Quality Score"
              color={
                telemetry.overall_quality_score >= 0.8 ? 'green' :
                telemetry.overall_quality_score >= 0.6 ? 'blue' : 'yellow'
              }
            />
          </div>
        )}
      </Card>

      <Card title="Execution Trace" subtitle="LangGraph multi-agent node execution">
        <div className="space-y-1">
          {NODE_ORDER.map((nodeName, idx) => {
            const step = workflow.steps.find((s) => s.node_name === nodeName)
            const duration = nodeDurations[nodeName]
            const isLast = idx === NODE_ORDER.length - 1
            const badge = getNodeBadge(nodeName)
            const isLoop = nodeName === 'critique' || nodeName === 'revision'

            return (
              <div key={nodeName} className="flex items-start">
                <div className="flex flex-col items-center mr-3">
                  <div className={`w-3 h-3 rounded-full border-2 ${
                    badge === 'success' ? 'bg-green-500 border-green-500' :
                    badge === 'danger' ? 'bg-red-500 border-red-500' :
                    badge === 'warning' ? 'bg-yellow-400 border-yellow-400' :
                    'bg-gray-200 border-gray-300'
                  }`} />
                  {!isLast && <div className="w-0.5 h-8 bg-gray-200" />}
                </div>
                <div className="flex-1 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {NODE_LABELS[nodeName] || nodeName}
                    </span>
                    {isLoop && (
                      <Badge variant="info" size="sm">loop</Badge>
                    )}
                    {step && step.retry_count > 0 && (
                      <Badge variant="warning" size="sm">{step.retry_count} retries</Badge>
                    )}
                    <span className="text-xs text-gray-400 ml-auto">
                      {duration ? formatMs(duration) : ''}
                    </span>
                  </div>
                  {step?.error && (
                    <p className="text-xs text-red-500 mt-0.5">{step.error}</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
