'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getUserName, isAuthenticated, logout } from '@/lib/auth'

export default function Navbar() {
  const router = useRouter()
  const [authed, setAuthed] = useState(false)
  const [name, setName] = useState('')

  useEffect(() => {
    setAuthed(isAuthenticated())
    setName(getUserName())
  }, [])

  function handleLogout() {
    logout()
    router.push('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href={authed ? '/dashboard' : '/'} className="font-bold text-indigo-600 text-lg">
          AI Study Guide
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {authed ? (
            <>
              <span className="text-gray-500">Hi, {name}</span>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-600 hover:text-gray-900 font-medium">
                Log in
              </Link>
              <Link
                href="/signup"
                className="bg-indigo-600 text-white px-4 py-1.5 rounded-lg hover:bg-indigo-700 font-medium"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
