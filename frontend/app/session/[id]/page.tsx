'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { getUserId, isAuthenticated } from '@/lib/auth'

type Chat = { chat_id: number; question: string; answer: string; created_at: string }
type Guide = {
  overview: string
  sections: { title: string; content: string }[]
  estimated_time_hours: number | null
  prerequisites: string[]
  extra_tips: string[]
  sources: { provider: string; model: string; snippet: string }[]
}

export default function SessionPage() {
  const router = useRouter()
  const { id } = useParams<{ id: string }>()
  const sessionId = parseInt(id)

  const [chats, setChats] = useState<Chat[]>([])
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [guide, setGuide] = useState<Guide | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/login'); return }
    loadChats()
  }, [])

  async function loadChats() {
    try {
      setChats(await api.getChats(sessionId))
    } catch {
      setError('Failed to load chat history')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) return
    setGenerating(true)
    setGuide(null)
    setError('')
    try {
      const userId = getUserId()!
      const res = await api.runPipeline(userId, prompt.trim())
      setGuide(res.guide)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Guide generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div>
      <Link href="javascript:history.back()" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back
      </Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Study Session</h1>

      {/* Generate guide */}
      <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-8">
        <h2 className="font-semibold text-gray-900 mb-3">Generate a Study Guide</h2>
        <form onSubmit={handleGenerate} className="flex gap-3">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Explain neural networks from scratch"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={generating}
            className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 whitespace-nowrap"
          >
            {generating ? 'Generating…' : 'Generate'}
          </button>
        </form>
        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      </div>

      {/* Generated guide */}
      {generating && (
        <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-8 mb-8 text-center">
          <div className="inline-block w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-indigo-700 font-medium">Asking AI providers…</p>
          <p className="text-indigo-400 text-sm mt-1">This may take 10–20 seconds</p>
        </div>
      )}

      {guide && <GuideDisplay guide={guide} />}

      {/* Chat history */}
      {!loading && chats.length > 0 && (
        <div className="mt-8">
          <h2 className="font-semibold text-gray-900 mb-4">Previous chats</h2>
          <div className="space-y-3">
            {chats.map((c) => (
              <div key={c.chat_id} className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
                <p className="text-sm font-medium text-gray-900 mb-1">Q: {c.question}</p>
                <p className="text-sm text-gray-500">A: {c.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function GuideDisplay({ guide }: { guide: Guide }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-600 px-6 py-5">
        <h2 className="text-white font-bold text-lg">Study Guide</h2>
        {guide.estimated_time_hours && (
          <p className="text-indigo-200 text-sm mt-0.5">
            Estimated time: {guide.estimated_time_hours}h
          </p>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Overview */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Overview</h3>
          <p className="text-gray-600 text-sm leading-relaxed">{guide.overview}</p>
        </div>

        {/* Prerequisites */}
        {guide.prerequisites?.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Prerequisites</h3>
            <ul className="list-disc list-inside space-y-1">
              {guide.prerequisites.map((p, i) => (
                <li key={i} className="text-gray-600 text-sm">{p}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Sections */}
        {guide.sections?.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Sections</h3>
            <div className="space-y-3">
              {guide.sections.map((s, i) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <h4 className="font-medium text-gray-900 text-sm mb-1">
                    {i + 1}. {s.title}
                  </h4>
                  <p className="text-gray-500 text-sm leading-relaxed">{s.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tips */}
        {guide.extra_tips?.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Tips</h3>
            <ul className="list-disc list-inside space-y-1">
              {guide.extra_tips.map((t, i) => (
                <li key={i} className="text-gray-600 text-sm">{t}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Sources */}
        {guide.sources?.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-500 text-xs uppercase tracking-wide mb-2">
              Sources
            </h3>
            <div className="flex gap-2 flex-wrap">
              {guide.sources.map((s, i) => (
                <span key={i} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
                  {s.provider} {s.model ? `(${s.model})` : ''}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
