'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Textarea from '@/components/ui/Textarea'
import { api } from '@/lib/api'

const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'academic', label: 'Academic' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'persuasive', label: 'Persuasive' },
  { value: 'informative', label: 'Informative' },
]

const CONTENT_TYPE_OPTIONS = [
  { value: 'article', label: 'Article' },
  { value: 'blog_post', label: 'Blog Post' },
  { value: 'research_paper', label: 'Research Paper' },
  { value: 'report', label: 'Report' },
  { value: 'white_paper', label: 'White Paper' },
  { value: 'case_study', label: 'Case Study' },
]

type Mode = 'quick' | 'full'

export default function ContentForm() {
  const router = useRouter()
  const [mode, setMode] = useState<Mode>('full')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quickTopic, setQuickTopic] = useState('')
  const [formData, setFormData] = useState({
    topic: '',
    title: '',
    points_to_cover: '',
    tone: 'professional',
    content_type: 'article',
    target_audience: '',
    seo_keywords: '',
  })

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleQuickSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!quickTopic.trim()) return
    setLoading(true)
    setError(null)
    try {
      const project = await api.projects.quickCreate(quickTopic.trim())
      router.push(`/projects/${project.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  const handleFullSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const project = await api.projects.create({
        topic: formData.topic,
        title: formData.title,
        points_to_cover: formData.points_to_cover
          .split('\n')
          .map((p) => p.trim())
          .filter(Boolean),
        tone: formData.tone,
        content_type: formData.content_type,
        target_audience: formData.target_audience || undefined,
        seo_keywords: formData.seo_keywords
          .split(',')
          .map((k) => k.trim())
          .filter(Boolean),
      })
      router.push(`/projects/${project.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4 border-b border-gray-200 pb-4">
        <button
          type="button"
          onClick={() => setMode('full')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            mode === 'full'
              ? 'bg-primary-100 text-primary-700 border border-primary-300'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          Full Input
        </button>
        <button
          type="button"
          onClick={() => setMode('quick')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            mode === 'quick'
              ? 'bg-primary-100 text-primary-700 border border-primary-300'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          Quick Mode
        </button>
        {mode === 'quick' && (
          <span className="text-xs text-gray-400">
            Just provide a topic — we&apos;ll infer the rest
          </span>
        )}
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-500 text-danger-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {mode === 'quick' ? (
        <form onSubmit={handleQuickSubmit} className="space-y-4">
          <Textarea
            label="Topic"
            placeholder="e.g., Impact of AI on Healthcare. Or go deeper: Artificial Intelligence in Healthcare — diagnosis, drug discovery, ethics, and what it means for patients and providers by 2030"
            value={quickTopic}
            onChange={(e) => setQuickTopic(e.target.value)}
            rows={4}
            required
          />
          <div className="flex justify-end">
            <Button type="submit" size="lg" loading={loading}>
              {loading ? 'Creating Project...' : 'Auto-Generate & Create'}
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleFullSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
              <Input
                label="Topic"
                name="topic"
                placeholder="e.g., Impact of AI on Healthcare"
                value={formData.topic}
                onChange={handleChange}
                required
              />

              <Input
                label="Title"
                name="title"
                placeholder="e.g., The Transformation of Healthcare Through Artificial Intelligence"
                value={formData.title}
                onChange={handleChange}
                required
              />

              <Select
                label="Tone"
                name="tone"
                options={TONE_OPTIONS}
                value={formData.tone}
                onChange={handleChange}
              />

              <Select
                label="Content Type"
                name="content_type"
                options={CONTENT_TYPE_OPTIONS}
                value={formData.content_type}
                onChange={handleChange}
              />
            </div>

            <div className="space-y-6">
              <Input
                label="Target Audience"
                name="target_audience"
                placeholder="e.g., Healthcare professionals, CTOs"
                value={formData.target_audience}
                onChange={handleChange}
              />

              <Input
                label="SEO Keywords"
                name="seo_keywords"
                placeholder="e.g., AI healthcare, machine learning, medical diagnosis"
                value={formData.seo_keywords}
                onChange={handleChange}
              />

              <Textarea
                label="Points to Cover"
                name="points_to_cover"
                placeholder="One point per line:&#10;AI diagnosis accuracy&#10;Drug discovery&#10;Patient monitoring"
                value={formData.points_to_cover}
                onChange={handleChange}
                rows={6}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Button type="submit" size="lg" loading={loading}>
              {loading ? 'Creating Project...' : 'Generate Verified Content'}
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}
