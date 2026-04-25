'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'

type Session = { session_id: number; title: string; created_at: string }

export default function SubjectPage() {
  const router = useRouter()
  const { id } = useParams<{ id: string }>()
  const subjectId = parseInt(id)

  const [sessions, setSessions] = useState<Session[]>([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/login'); return }
    load()
  }, [])

  async function load() {
    try {
      setSessions(await api.getSessions(subjectId))
    } catch {
      setError('Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!newTitle.trim()) return
    setCreating(true)
    try {
      await api.createSession(subjectId, newTitle.trim())
      setNewTitle('')
      await load()
    } catch {
      setError('Failed to create session')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <Link href="/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back to subjects
      </Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Sessions</h1>

      <form onSubmit={handleCreate} className="flex gap-3 mb-8">
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New session title (e.g. Week 1 — Intro)"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={creating}
          className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? 'Adding…' : '+ Add session'}
        </button>
      </form>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : sessions.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No sessions yet</p>
          <p className="text-sm mt-1">Add a session to start generating study guides</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <Link
              key={s.session_id}
              href={`/session/${s.session_id}`}
              className="flex items-center justify-between bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
            >
              <div>
                <h2 className="font-semibold text-gray-900">{s.title}</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(s.created_at).toLocaleDateString()}
                </p>
              </div>
              <span className="text-indigo-500 text-sm font-medium">Open →</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
