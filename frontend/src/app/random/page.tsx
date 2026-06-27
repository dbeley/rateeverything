"use client"

import { useEffect, useState } from "react"
import { api, Entity } from "@/lib/api"
import { useRouter } from "next/navigation"
import { Shuffle } from "lucide-react"

export default function RandomPage() {
  const router = useRouter()
  const [entity, setEntity] = useState<Entity | null>(null)
  const [loading, setLoading] = useState(true)

  const loadRandom = async () => {
    setLoading(true)
    try {
      const e = await api.getRandom()
      setEntity(e)
    } catch {
      setEntity(null)
    }
    setLoading(false)
  }

  useEffect(() => { loadRandom() }, [])

  if (loading) {
    return <div className="text-center py-20 text-zinc-500">Chargement d&apos;une entité aléatoire...</div>
  }

  if (!entity) {
    return (
      <div className="text-center py-20">
        <p className="text-zinc-500 mb-4">Aucune entité disponible</p>
        <button onClick={loadRandom} className="px-4 py-2 bg-zinc-800 rounded-lg text-sm text-zinc-300">
          Réessayer
        </button>
      </div>
    )
  }

  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-900 rounded-full text-xs text-zinc-500 mb-6">
        <Shuffle className="w-3 h-3" /> Entité aléatoire
      </div>

      <div
        className="max-w-lg mx-auto bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 cursor-pointer hover:border-zinc-700 transition-colors"
        onClick={() => router.push(`/entity/${entity.id}`)}
      >
        <div className="text-2xl font-bold text-white mb-2">{entity.name}</div>
        {entity.entity_type && (
          <div className="text-sm text-zinc-500 mb-4">
            {entity.entity_type.emoji} {entity.entity_type.name}
          </div>
        )}
        {entity.avg_rating && (
          <div className="text-4xl font-bold text-amber-400 mb-2">
            {entity.avg_rating.toFixed(1)}
          </div>
        )}
        <div className="text-sm text-zinc-600">{entity.rating_count} note{entity.rating_count !== 1 ? "s" : ""}</div>
      </div>

      <button
        onClick={loadRandom}
        className="mt-8 inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-zinc-300 hover:text-white transition-all"
      >
        <Shuffle className="w-4 h-4" /> Une autre
      </button>
    </div>
  )
}
