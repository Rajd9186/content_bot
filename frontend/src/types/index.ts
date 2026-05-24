export interface Project {
  id: string
  topic: string
  title: string
  points_to_cover: string[]
  tone: string
  content_type: string
  target_audience: string | null
  seo_keywords: string[]
  status: ProjectStatus
  outline: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export type ProjectStatus =
  | 'draft'
  | 'planning'
  | 'researching'
  | 'verifying'
  | 'generating'
  | 'self_verifying'
  | 'completed'
  | 'failed'

export interface ProjectCreate {
  topic: string
  title: string
  points_to_cover: string[]
  tone: string
  content_type: string
  target_audience?: string
  seo_keywords: string[]
}

export interface GeneratedContent {
  id: string
  project_id: string
  markdown: string
  summary: string | null
  word_count: number | null
  citations: Citation[]
  seo_metadata: SeoMetadata | null
  overall_confidence: number | null
  created_at: string
}

export interface Citation {
  id: number
  text: string
  source_url: string
  source_title: string
  claim_id: string
  confidence: number
}

export interface SeoMetadata {
  meta_title: string
  meta_description: string
  focus_keywords: string[]
}

export interface Claim {
  id: string
  project_id: string
  claim_text: string
  confidence: number | null
  status: ClaimStatus
  explanation: string | null
  category: string | null
  created_at: string
}

export type ClaimStatus = 'verified' | 'unverified' | 'contradicted' | 'unsupported'

export interface EvidenceItem {
  id: string
  project_id: string
  claim_id: string | null
  source_id: string | null
  snippet: string
  relevance_score: number | null
  extracted_at: string
  source_url: string | null
  source_domain: string | null
  source_trust_score: number | null
}

export interface Source {
  id: string
  project_id: string
  url: string
  domain: string
  title: string | null
  trust_score: number | null
  author: string | null
  published_date: string | null
  snippet: string | null
  created_at: string
}

export interface VerificationDashboard {
  project: {
    id: string
    title: string
    topic: string
    status: string
    tone: string
    content_type: string
  }
  claims: {
    total_claims: number
    verified_count: number
    unverified_count: number
    contradicted_count: number
    unsupported_count: number
    average_confidence: number
    items: Claim[]
  }
  sources: {
    total: number
    average_trust_score: number
    items: Array<{
      id: string
      url: string
      domain: string
      trust_score: number | null
      title: string | null
    }>
  }
  evidence: {
    total: number
    average_relevance: number
  }
  content: {
    has_content: boolean
    word_count: number | null
    overall_confidence: number | null
    citations_count: number
  }
}

export interface WorkflowExecution {
  id: string
  project_id: string
  status: string
  current_node: string
  error: string | null
  telemetry: Record<string, unknown> | null
  started_at: string
  completed_at: string | null
  steps: WorkflowStep[]
}

export interface WorkflowStep {
  id: string
  workflow_id: string
  node_name: string
  agent_name: string | null
  status: string
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  error: string | null
  retry_count: number
}

export interface WorkflowTelemetry {
  total_duration_ms: number
  node_durations: Record<string, number>
  total_retries: number
  total_llm_calls: number
  total_sources: number
  total_claims: number
  total_contradictions: number
  revision_count: number
  hyperlinks_checked: number
  hyperlinks_valid: number
  overall_quality_score: number
}

export interface Contradiction {
  id: string
  project_id: string
  claim_text: string
  severity: string
  conflicting_sources: Array<{ source: string; statement: string }>
  explanation: string | null
  resolved: boolean
  created_at: string
}

export interface HyperlinkValidation {
  id: string
  project_id: string
  url: string
  label: string | null
  status: string
  status_code: number | null
  error_message: string | null
  resolved_url: string | null
  is_verified: boolean
  checked_at: string | null
  created_at: string
}

export interface HyperlinkSummary {
  total: number
  verified: number
  broken: number
  pending: number
  verification_rate: number
}

export interface ContentGenerateResponse {
  project_id: string
  content_id: string
  markdown: string
  summary: string
  word_count: number
  citations: Citation[]
  seo_metadata: SeoMetadata
  overall_confidence: number
  claims: Array<{
    id: string
    claim_text: string
    confidence: number | null
    status: string
  }>
  verification_summary: {
    total_claims: number
    verified_count: number
    unverified_count: number
    contradicted_count: number
    unsupported_count: number
    average_confidence: number
    audit_passed: boolean
    hallucination_risk_score: number
    issues_found: number
  }
  contradictions?: Array<{
    id: string
    claim_text: string
    severity: string
    explanation: string | null
  }>
  hyperlinks?: Array<{
    id: string
    url: string
    status: string
    is_verified: boolean
  }>
  telemetry?: {
    total_duration_ms: number
    node_durations: Record<string, number>
    total_sources: number
    total_claims: number
    total_contradictions: number
    revision_count: number
    overall_quality_score: number
  }
  steps_completed?: string[]
  workflow_id?: string
}
