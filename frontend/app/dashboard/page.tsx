'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { getUserId, isAuthenticated } from '@/lib/auth'

type Subject = { subject_id: number; subject_name: string; created_at: string }

export default function DashboardPage() {
  const router = useRouter()
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/login'); return }
    load()
  }, [])

  async function load() {
    try {
      const userId = getUserId()!
      const data = await api.getSubjects(userId)
      setSubjects(data)
    } catch {
      setError('Failed to load subjects')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      const userId = getUserId()!
      await api.createSubject(userId, newName.trim())
      setNewName('')
      await load()
    } catch {
      setError('Failed to create subject')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Subjects</h1>

      <form onSubmit={handleCreate} className="flex gap-3 mb-8">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New subject (e.g. Machine Learning)"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={creating}
          className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? 'Adding…' : '+ Add subject'}
        </button>
      </form>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : subjects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No subjects yet</p>
          <p className="text-sm mt-1">Add one above to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {subjects.map((s) => (
            <Link
              key={s.subject_id}
              href={`/subject/${s.subject_id}`}
              className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
            >
              <h2 className="font-semibold text-gray-900">{s.subject_name}</h2>
              <p className="text-xs text-gray-400 mt-1">
                {new Date(s.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
