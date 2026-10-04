'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex h-full w-full items-center justify-center min-h-[350px]">
      <div className="text-center panel p-6 max-w-md">
        <h2 className="text-base font-semibold text-zinc-100 mb-2">Something went wrong</h2>
        <p className="text-zinc-400 text-xs mb-4">{error.message || 'An unexpected error occurred'}</p>
        <button
          onClick={() => reset()}
          className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  )
}
