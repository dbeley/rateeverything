"use client"

import { useEffect, useState, use } from "react"
import { api, Entity, EntityCharts, Rating, EntityGraph } from "@/lib/api"
import Link from "next/link"
import { ArrowLeft, Star, Edit3, Share2, Network } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts"

// Quick rating component
function RateButton({ entityId, onRated }: { entityId: number; onRated: () => void }) {
  const [showForm, setShowForm] = useState(false)
  const [score, setScore] = useState(5)
  const [review, setReview] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    setSubmitting(true)
    try {
      await api.createRating({ entity_id: entityId, score, review: review || undefined })
      setShowForm(false)
      onRated()
    } catch (e) {
      console.error(e)
    }
    setSubmitting(false)
  }

  return (
    <div>
      <button
        onClick={() => setShowForm(!showForm)}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white transition-colors"
      >
        <Edit3 className="w-4 h-4" /> Noter
      </button>
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowForm(false)}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-6">Donner une note</h3>
            <div className="flex items-center justify-center gap-2 mb-6">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                <button
                  key={n}
                  onClick={() => setScore(n)}
                  className={`w-9 h-9 rounded-lg text-sm font-bold transition-colors ${
                    score === n ? "bg-indigo-600 text-white" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <textarea
              placeholder="Ajouter un commentaire (optionnel)"
              value={review}
              onChange={(e) => setReview(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 resize-none h-24 outline-none"
            />
            <div className="flex gap-3 mt-4">
              <button onClick={() => setShowForm(false)} className="flex-1 py-2.5 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm text-zinc-300">
                Annuler
              </button>
              <button onClick={submit} disabled={submitting} className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm text-white disabled:opacity-50">
                {submitting ? "..." : "Noter"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function EntityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [entity, setEntity] = useState<Entity | null>(null)
  const [charts, setCharts] = useState<EntityCharts | null>(null)
  const [ratings, setRatings] = useState<Rating[]>([])
  const [graph, setGraph] = useState<EntityGraph | null>(null)
  const [showGraph, setShowGraph] = useState(false)

  const load = async () => {
    if (!id) return
    const entityData = await api.getEntity(Number(id))
    setEntity(entityData)
    api.getEntityCharts(Number(id)).then(setCharts).catch(console.error)
    api.getRatings({ entity_id: Number(id), sort: "newest" }).then(setRatings).catch(console.error)
    api.getEntityGraph(Number(id)).then(setGraph).catch(console.error)
  }

  useEffect(() => { load() }, [id])

  if (!entity) {
    return <div className="text-zinc-500 text-center py-20">Chargement...</div>
  }

  const chartData = charts?.rating_distribution?.labels?.map((label, i) => ({
    name: label,
    value: charts.rating_distribution?.datasets[0]?.data[i] || 0,
  })) || []

  const timeData = charts?.rating_over_time?.labels?.map((label, i) => ({
    date: label.slice(5, 10),
    score: charts.rating_over_time?.datasets[0]?.data[i] || 0,
  })) || []

  return (
    <div>
      <Link href="/" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 mb-6">
        <ArrowLeft className="w-4 h-4" /> Retour
      </Link>

      {/* Entity Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-2 text-sm text-zinc-500 mb-2">
            {entity.entity_type && (
              <Link href={`/type/${entity.entity_type_id}`} className="hover:text-zinc-300">
                {entity.entity_type.emoji} {entity.entity_type.name}
              </Link>
            )}
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">{entity.name}</h1>
          {entity.description && <p className="text-zinc-400">{entity.description}</p>}
          <div className="flex items-center gap-4 mt-4">
            {entity.avg_rating && (
              <div className="flex items-center gap-1.5">
                <Star className="w-5 h-5 text-amber-400 fill-current" />
                <span className="text-2xl font-bold text-white">{entity.avg_rating.toFixed(1)}</span>
                <span className="text-sm text-zinc-600">/10</span>
              </div>
            )}
            <span className="text-sm text-zinc-600">{entity.rating_count} note{entity.rating_count !== 1 ? "s" : ""}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <RateButton entityId={entity.id} onRated={load} />
          <button
            onClick={() => setShowGraph(!showGraph)}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
          >
            <Network className="w-4 h-4" /> Graphe
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors">
            <Share2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Rating Distribution */}
        {chartData.length > 0 && (
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wider">Distribution des notes</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                <YAxis tick={{ fill: '#a1a1aa' }} />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                  labelStyle={{ color: '#e4e4e7' }}
                />
                <Bar dataKey="value" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Rating Over Time */}
        {timeData.length > 0 && (
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wider">Évolution de la note</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={timeData}>
                <XAxis dataKey="date" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                <YAxis domain={[0, 10]} tick={{ fill: '#a1a1aa' }} />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                  labelStyle={{ color: '#e4e4e7' }}
                />
                <Line type="monotone" dataKey="score" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Relation Graph */}
      {showGraph && graph && graph.nodes.length > 1 && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 mb-8">
          <h3 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wider">Graphe des relations</h3>
          <div className="flex flex-wrap gap-2">
            {graph.nodes.map((node) => (
              <Link
                key={node.id}
                href={`/entity/${node.id}`}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  node.is_center
                    ? "bg-indigo-600 text-white font-bold"
                    : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                }`}
              >
                {node.name}
              </Link>
            ))}
          </div>
          <div className="mt-4 space-y-1">
            {graph.edges.map((edge, i) => (
              <div key={i} className="text-xs text-zinc-500">
                <span className="text-zinc-300">{graph.nodes.find(n => n.id === edge.source)?.name}</span>
                {" "}{edge.relation}{" "}
                <span className="text-zinc-300">{graph.nodes.find(n => n.id === edge.target)?.name}</span>
                {edge.auto_generated && <span className="text-indigo-500 ml-1">(auto)</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {entity.metadata && Object.keys(entity.metadata).length > 0 && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 mb-8">
          <h3 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wider">Métadonnées</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(entity.metadata).map(([key, val]) => (
              <div key={key} className="bg-zinc-800/50 rounded-lg px-4 py-3">
                <div className="text-xs text-zinc-500 uppercase">{key}</div>
                <div className="text-sm text-zinc-200 mt-0.5">{String(val)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviews */}
      <section>
        <h3 className="text-lg font-semibold text-white mb-4">Avis ({ratings.length})</h3>
        <div className="space-y-3">
          {ratings.map((rating) => (
            <div key={rating.id} className="bg-zinc-900/50 border border-zinc-800 rounded-xl px-5 py-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-amber-400 font-bold">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    {rating.score}/10
                  </span>
                  <span className="text-xs text-zinc-600">Utilisateur #{rating.user_id}</span>
                </div>
                <span className="text-xs text-zinc-600">
                  {new Date(rating.created_at).toLocaleDateString("fr-FR")}
                </span>
              </div>
              {rating.review && <p className="text-sm text-zinc-300">{rating.review}</p>}
              {rating.tags && rating.tags.length > 0 && (
                <div className="flex gap-1 mt-2">
                  {rating.tags.map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-500">#{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {ratings.length === 0 && (
            <p className="text-zinc-600 text-center py-8">Aucun avis pour le moment. Sois le premier !</p>
          )}
        </div>
      </section>
    </div>
  )
}
