'use client'

import ContentForm from '@/components/forms/ContentForm'
import Card from '@/components/ui/Card'

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">
          Verified AI Research Writer
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Generate fact-checked, evidence-backed content with full transparency.
          Every claim is verified against trusted sources before publishing.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
        <div className="flex items-start space-x-3">
          <div className="w-10 h-10 bg-verified-50 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-verified-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h3 className="font-medium text-gray-900">Evidence-Backed</h3>
            <p className="text-sm text-gray-500">Every claim verified against trusted sources</p>
          </div>
        </div>
        <div className="flex items-start space-x-3">
          <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h3 className="font-medium text-gray-900">Transparent Metrics</h3>
            <p className="text-sm text-gray-500">Confidence scores, trust ratings, and contradictions shown</p>
          </div>
        </div>
        <div className="flex items-start space-x-3">
          <div className="w-10 h-10 bg-warning-50 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-warning-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div>
            <h3 className="font-medium text-gray-900">Anti-Hallucination</h3>
            <p className="text-sm text-gray-500">Self-verification catches unsupported statements</p>
          </div>
        </div>
      </div>

      <Card title="Create New Content" subtitle="Fill in the details below to generate verified, fact-checked content">
        <ContentForm />
      </Card>
    </div>
  )
}
