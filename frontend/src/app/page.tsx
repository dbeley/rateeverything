"use client"

import { useEffect, useState } from "react"
import { api, Entity, DashboardStats } from "@/lib/api"
import Link from "next/link"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts"
import { TrendingUp, Star, Layers, Shuffle, Plus } from "lucide-react"

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [trending, setTrending] = useState<Entity[]>([])
  const [randomEntity, setRandomEntity] = useState<Entity | null>(null)

  useEffect(() => {
    api.getDashboard().then(setStats).catch(console.error)
    api.getTrending(8).then(setTrending).catch(console.error)
    loadRandom()
  }, [])

  const loadRandom = async () => {
    try {
      const entity = await api.getRandom()
      setRandomEntity(entity)
    } catch {
      setRandomEntity(null)
    }
  }

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center py-12">
        <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          RateEverything
        </h1>
        <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
          Notez tout ce qui existe. Albums, coiffures, pochettes, films, performances, 
          expressions faciales... tout est culturel, tout est notable.
        </p>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Entités", value: stats.quick_stats.total_entities, icon: Layers, color: "from-indigo-500 to-blue-500" },
            { label: "Types", value: stats.quick_stats.total_types, icon: Star, color: "from-purple-500 to-pink-500" },
            { label: "Notes", value: stats.quick_stats.total_ratings, icon: TrendingUp, color: "from-amber-500 to-orange-500" },
          ].map((stat) => (
            <div key={stat.label} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 text-center">
              <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${stat.color} mb-3`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="text-3xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-zinc-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Random Entity CTA */}
      <div className="bg-gradient-to-r from-zinc-900 to-zinc-800/50 border border-zinc-800 rounded-xl p-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Envie de noter quelque chose ?</h3>
          <p className="text-zinc-400 text-sm">
            {randomEntity ? (
              <>
                Essaye <Link href={`/entity/${randomEntity.id}`} className="text-indigo-400 hover:underline">{randomEntity.name}</Link>
              </>
            ) : (
              "Découvre une entité aléatoire"
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadRandom} className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-white transition-colors">
            <Shuffle className="w-4 h-4" /> Aléatoire
          </button>
          <Link href="/create" className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white transition-colors">
            <Plus className="w-4 h-4" /> Créer
          </Link>
        </div>
      </div>

      {/* Trending */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-400" />
          Tendances
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {trending.map((entity) => (
            <Link
              key={entity.id}
              href={`/entity/${entity.id}`}
              className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{entity.name}</p>
                  <p className="text-xs text-zinc-500 mt-1">{entity.entity_type?.emoji} {entity.entity_type?.name}</p>
                </div>
                {entity.avg_rating && (
                  <div className="flex items-center gap-1 text-amber-400 text-sm font-bold ml-2">
                    <Star className="w-3 h-3 fill-current" />
                    {entity.avg_rating.toFixed(1)}
                  </div>
                )}
              </div>
              <p className="text-xs text-zinc-600 mt-2">{entity.rating_count} note{entity.rating_count !== 1 ? "s" : ""}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Active Types */}
      {stats && stats.most_active_types.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold text-white mb-4">Types d&apos;entités les plus actifs</h2>
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.most_active_types.map(t => ({ name: `${t.emoji || ""} ${t.name}`, count: t.rating_count }))}>
                <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                <YAxis tick={{ fill: '#a1a1aa' }} />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                  labelStyle={{ color: '#e4e4e7' }}
                />
                <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Explore link */}
      <div className="text-center py-8">
        <Link
          href="/types"
          className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-zinc-300 hover:text-white transition-all"
        >
          Explorer tous les types d&apos;entités →
        </Link>
      </div>
    </div>
  )
}
