'use client'

import ReactMarkdown from 'react-markdown'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import type { GeneratedContent } from '@/types'

interface ContentViewerProps {
  content: GeneratedContent
}

export default function ContentViewer({ content }: ContentViewerProps) {
  return (
    <div className="space-y-6">
      <Card>
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {content.seo_metadata?.meta_title || 'Generated Content'}
              </h2>
              <div className="flex items-center space-x-3 mt-2">
                <Badge variant="info">
                  {content.word_count?.toLocaleString()} words
                </Badge>
                {content.overall_confidence !== null && (
                  <Badge
                    variant={
                      content.overall_confidence >= 0.8
                        ? 'success'
                        : content.overall_confidence >= 0.6
                        ? 'warning'
                        : 'danger'
                    }
                  >
                    {Math.round(content.overall_confidence * 100)}% confidence
                  </Badge>
                )}
                <Badge variant="default">
                  {content.citations.length} citations
                </Badge>
              </div>
            </div>
          </div>

          {content.summary && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-1">Summary</p>
              <p className="text-sm text-gray-600">{content.summary}</p>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="prose-custom max-w-none">
          <ReactMarkdown>{content.markdown}</ReactMarkdown>
        </div>
      </Card>

      {content.citations.length > 0 && (
        <Card title="References & Citations" subtitle={`${content.citations.length} sources cited`}>
          <div className="space-y-3">
            {content.citations.map((citation) => (
              <div
                key={citation.id}
                className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
              >
                <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-xs font-medium">
                  {citation.id}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    {citation.text}
                  </p>
                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary-600 hover:text-primary-800 mt-1 inline-block"
                  >
                    {citation.source_title || citation.source_url}
                  </a>
                  {citation.confidence && (
                    <div className="mt-1">
                      <Badge
                        variant={citation.confidence >= 0.8 ? 'success' : 'warning'}
                        size="sm"
                      >
                        {Math.round(citation.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
