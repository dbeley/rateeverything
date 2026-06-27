"use client"

import { useEffect, useState } from "react"
import { api, EntityType } from "@/lib/api"
import Link from "next/link"
import { ArrowLeft, Star } from "lucide-react"
import { useParams } from "next/navigation"

export default function TypePage() {
  const params = useParams()
  const [type, setType] = useState<EntityType | null>(null)
  const [entities, setEntities] = useState<Array<{ id: number; name: string; avg_rating: number | null; rating_count: number }>>([])

  useEffect(() => {
    if (!params.id) return
    api.getType(Number(params.id)).then(setType).catch(console.error)
    api.getEntities({ type_id: Number(params.id), sort: "top", limit: 50 })
      .then(setEntities)
      .catch(console.error)
  }, [params.id])

  if (!type) {
    return <div className="text-zinc-500 text-center py-20">Chargement...</div>
  }

  return (
    <div>
      <Link href="/types" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 mb-6">
        <ArrowLeft className="w-4 h-4" /> Retour aux types
      </Link>

      <div className="flex items-center gap-3 mb-8">
        <span className="text-3xl">{type.emoji || "📋"}</span>
        <div>
          <h1 className="text-2xl font-bold text-white">{type.name}</h1>
          {type.description && <p className="text-zinc-400 mt-1">{type.description}</p>}
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-white mb-4">Entités de ce type</h2>
        <div className="grid gap-2">
          {entities.map((entity) => (
            <Link
              key={entity.id}
              href={`/entity/${entity.id}`}
              className="flex items-center justify-between bg-zinc-900/50 border border-zinc-800 rounded-xl px-5 py-4 hover:border-zinc-700 transition-colors"
            >
              <span className="text-zinc-200 font-medium">{entity.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-zinc-600">{entity.rating_count} note{entity.rating_count !== 1 ? "s" : ""}</span>
                {entity.avg_rating && (
                  <span className="flex items-center gap-1 text-amber-400 font-bold">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    {entity.avg_rating.toFixed(1)}
                  </span>
                )}
              </div>
            </Link>
          ))}
          {entities.length === 0 && (
            <p className="text-zinc-600 text-center py-8">Aucune entité de ce type pour le moment.</p>
          )}
        </div>
      </section>
    </div>
  )
}
