import Link from 'next/link'

export default function LandingPage() {
  return (
    <div className="text-center py-20">
      <h1 className="text-5xl font-bold text-gray-900 mb-4">
        Study smarter with <span className="text-indigo-600">AI</span>
      </h1>
      <p className="text-xl text-gray-500 mb-10 max-w-xl mx-auto">
        Generate structured study guides from any topic — powered by OpenAI, Gemini, and DeepSeek combined.
      </p>
      <div className="flex justify-center gap-4">
        <Link
          href="/signup"
          className="bg-indigo-600 text-white px-8 py-3 rounded-xl text-lg font-semibold hover:bg-indigo-700"
        >
          Get started free
        </Link>
        <Link
          href="/login"
          className="border border-gray-300 text-gray-700 px-8 py-3 rounded-xl text-lg font-semibold hover:bg-gray-100"
        >
          Log in
        </Link>
      </div>

      <div className="mt-24 grid grid-cols-3 gap-8 text-left">
        {[
          { title: 'Multi-AI', desc: 'Combines OpenAI, Gemini & DeepSeek for the best results.' },
          { title: 'Structured', desc: 'Get sections, prerequisites, time estimates and tips.' },
          { title: 'Organised', desc: 'Organise guides into subjects and sessions.' },
        ].map((f) => (
          <div key={f.title} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
            <p className="text-gray-500 text-sm">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
