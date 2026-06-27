"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth"
import Link from "next/link"

export default function LoginPage() {
  const router = useRouter()
  const { login, register, user } = useAuth()
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  if (user) {
    router.push("/")
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      if (isRegister) {
        await register(username, password, displayName || undefined)
      } else {
        await login(username, password)
      }
      router.push("/")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue")
    }
    setLoading(false)
  }

  return (
    <div className="max-w-md mx-auto mt-16">
      <h1 className="text-2xl font-bold text-white mb-2 text-center">
        {isRegister ? "Créer un compte" : "Connexion"}
      </h1>
      <p className="text-zinc-500 text-center mb-8 text-sm">
        {isRegister
          ? "Rejoins RateEverything et commence à noter"
          : "Connecte-toi pour noter des entités"}
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1.5">Nom d&apos;utilisateur</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500"
          />
        </div>

        {isRegister && (
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">Nom affiché (optionnel)</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1.5">Mot de passe</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800/30 rounded-xl text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-500 rounded-xl text-white font-medium transition-colors"
        >
          {loading ? "..." : isRegister ? "Créer mon compte" : "Se connecter"}
        </button>
      </form>

      <p className="text-center text-sm text-zinc-600 mt-6">
        {isRegister ? "Déjà un compte ?" : "Pas encore de compte ?"}{" "}
        <button
          onClick={() => { setIsRegister(!isRegister); setError("") }}
          className="text-indigo-400 hover:underline"
        >
          {isRegister ? "Connecte-toi" : "Inscris-toi"}
        </button>
      </p>
    </div>
  )
}
