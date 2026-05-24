'use client'

import { useState, useEffect, useRef } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { api } from '@/lib/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface WorkflowEvent {
  id: string
  node_name: string
  event_type: string
  message: string
  data?: any
  timestamp: string
}

interface ChatPanelProps {
  projectId: string
}

export default function ChatPanel({ projectId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState<WorkflowEvent[]>([])
  const [activeTab, setActiveTab] = useState<'chat' | 'activity'>('chat')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Poll for workflow events for live visualization
    const interval = setInterval(async () => {
      try {
        const data = await api.chat.getEvents(projectId)
        setEvents(data)
      } catch (err) {
        console.error('Failed to fetch events', err)
      }
    }, 3000)
    
    return () => clearInterval(interval)
  }, [projectId])

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await api.chat.send(projectId, input, messages)
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMsg])
      
      // If tool calls exist, handle them (e.g. trigger navigation or workflow)
      if (response.tool_calls && response.tool_calls.length > 0) {
        // Handle trigger_workflow etc.
        console.log('Bot triggered tools:', response.tool_calls)
      }
    } catch (err) {
      console.error('Chat failed', err)
    } finally {
      setLoading(false)
    }
  }

  const getEventIcon = (type: string) => {
    switch(type) {
      case 'discovery': return '🔍'
      case 'claim': return '📝'
      case 'contradiction': return '⚠️'
      case 'warning': return '🔸'
      case 'error': return '🔴'
      default: return 'ℹ️'
    }
  }

  return (
    <div className="flex flex-col h-[600px] border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm">
      <div className="flex border-b border-gray-100">
        <button 
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'chat' ? 'bg-primary-50 text-primary-600 border-b-2 border-primary-500' : 'text-gray-500 hover:bg-gray-50'}`}
        >
          Research Copilot
        </button>
        <button 
          onClick={() => setActiveTab('activity')}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'activity' ? 'bg-primary-50 text-primary-600 border-b-2 border-primary-500' : 'text-gray-500 hover:bg-gray-50'}`}
        >
          Live Activity {events.length > 0 && <span className="ml-1 bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded-full text-[10px]">{events.length}</span>}
        </button>
      </div>

      <div className="flex-1 overflow-hidden relative flex flex-col">
        {activeTab === 'chat' ? (
          <>
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-10">
                  <div className="text-4xl mb-4">🤖</div>
                  <h3 className="text-gray-900 font-medium">Research Copilot</h3>
                  <p className="text-gray-500 text-sm max-w-xs mx-auto mt-2">
                    Ask me about findings, contradictions, or tell me to run another research pass.
                  </p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
                    msg.role === 'user' 
                    ? 'bg-primary-600 text-white rounded-tr-none' 
                    : 'bg-gray-100 text-gray-800 rounded-tl-none'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-2">
                    <LoadingSpinner size="sm" />
                  </div>
                </div>
              )}
            </div>
            
            <form onSubmit={handleSend} className="p-4 border-t border-gray-100 bg-gray-50">
              <div className="flex space-x-2">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question..."
                  className="flex-1 bg-white border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <Button type="submit" disabled={!input.trim() || loading}>
                  Send
                </Button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {events.length === 0 ? (
              <div className="text-center py-20 text-gray-400 text-sm">
                No active events. Start a research workflow to see live updates.
              </div>
            ) : (
              events.map((event) => (
                <div key={event.id} className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm animate-in fade-in slide-in-from-right-4 duration-300">
                  <div className="flex items-start space-x-3">
                    <span className="text-lg">{getEventIcon(event.event_type)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="default" size="sm">{event.node_name.replace('_', ' ')}</Badge>
                        <span className="text-[10px] text-gray-400">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-xs text-gray-700 font-medium leading-normal">{event.message}</p>
                      {event.data && event.event_type === 'discovery' && (
                        <div className="mt-2 text-[10px] bg-primary-50 text-primary-700 p-1.5 rounded truncate">
                          {event.data.url}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
