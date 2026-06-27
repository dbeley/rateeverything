"use client"

import { useState, useEffect } from "react"
import { api, EntityType, Entity } from "@/lib/api"
import { useRouter } from "next/navigation"
import { Sparkles, Plus } from "lucide-react"

export default function CreatePage() {
  const router = useRouter()
  const [types, setTypes] = useState<EntityType[]>([])
  const [name, setName] = useState("")
  const [typeId, setTypeId] = useState<number | "new" | "">("")
  const [description, setDescription] = useState("")
  const [newTypeName, setNewTypeName] = useState("")
  const [newTypeEmoji, setNewTypeEmoji] = useState("")
  const [tags, setTags] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [llmAnalysis, setLlmAnalysis] = useState<any>(null)
  const [analyzing, setAnalyzing] = useState(false)
  useEffect(() => {
    api.getTypes().then(setTypes).catch(console.error)
  }, [])

  const analyzeWithLLM = async () => {
    if (!name.trim()) return
    setAnalyzing(true)
    try {
      const result = await api.analyzeEntity({
        user_input_raw: name,
        type_name: typeId === "new" ? newTypeName : types.find(t => t.id === typeId)?.name,
        description: description || undefined,
      }) as { entity_name_normalized?: string; confidence_name?: number; tags?: string[]; metadata?: Record<string, unknown> }
      setLlmAnalysis(result as Record<string, unknown>)
      if (result.entity_name_normalized && (result.confidence_name ?? 0) > 0.8) {
        setName(result.entity_name_normalized)
      }
    } catch (e) {
      console.error(e)
    }
    setAnalyzing(false)
  }

  const submit = async () => {
    if (!name.trim()) return
    setSubmitting(true)
    try {
      let finalTypeId = Number(typeId)

      // Create new type if needed
      if (typeId === "new" && newTypeName) {
        const newType = await api.createType({
          name: newTypeName,
          emoji: newTypeEmoji || undefined,
        })
        finalTypeId = newType.id
      }

      const entity = await api.createEntity({
        name: name.trim(),
        entity_type_id: finalTypeId,
        description: description.trim() || undefined,
        tags: tags ? tags.split(",").map(t => t.trim()).filter(Boolean) : undefined,
      })

      router.push(`/entity/${entity.id}`)
    } catch (e) {
      console.error(e)
      alert("Erreur lors de la création")
    }
    setSubmitting(false)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-2">Nouvelle entité</h1>
      <p className="text-zinc-400 mb-8">
        Crée une nouvelle entité à noter. Choisis un type existant ou crées-en un nouveau.
      </p>

      <div className="space-y-6">
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">Nom de l&apos;entité</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: La coupe de Kendrick Lamar dans Not Like Us"
              className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500"
            />
            <button
              onClick={analyzeWithLLM}
              disabled={analyzing || !name.trim()}
              className="px-4 py-3 bg-indigo-600/20 border border-indigo-800/30 rounded-xl text-indigo-300 hover:bg-indigo-600/30 disabled:opacity-30"
              title="Analyser avec l'IA"
            >
              <Sparkles className={`w-5 h-5 ${analyzing ? "animate-pulse" : ""}`} />
            </button>
          </div>
        </div>

        {/* LLM Analysis Results */}
        {llmAnalysis && (
          <div className="bg-indigo-950/30 border border-indigo-800/30 rounded-xl p-4 text-sm">
            <h4 className="text-indigo-300 font-medium mb-2 flex items-center gap-1">
              <Sparkles className="w-4 h-4" /> Suggestion IA
            </h4>
            {llmAnalysis.entity_name_normalized && (
              <p className="text-zinc-300">Nom normalisé : <strong>{llmAnalysis.entity_name_normalized as string}</strong></p>
            )}
            {llmAnalysis.tags && (llmAnalysis.tags as string[]).length > 0 && (
              <div className="flex gap-1 mt-2">
                {(llmAnalysis.tags as string[]).map((tag: string) => (
                  <span key={tag} className="px-2 py-0.5 bg-indigo-900/50 rounded text-xs text-indigo-300">#{tag}</span>
                ))}
              </div>
            )}
            {llmAnalysis.metadata && typeof llmAnalysis.metadata === 'object' && Object.keys(llmAnalysis.metadata as Record<string, unknown>).length > 0 && (
              <div className="mt-2 text-zinc-500">
                Métadonnées détectées : {Object.keys(llmAnalysis.metadata as Record<string, unknown>).join(", ")}
              </div>
            )}
          </div>
        )}

        {/* Type */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">Type d&apos;entité</label>
          <select
            value={typeId}
            onChange={(e) => setTypeId(e.target.value === "" ? "" : e.target.value === "new" ? "new" : Number(e.target.value))}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white outline-none focus:border-indigo-500"
          >
            <option value="">Sélectionne un type</option>
            {types.map((t) => (
              <option key={t.id} value={t.id}>{t.emoji || "📋"} {t.name}</option>
            ))}
            <option value="new">➕ Créer un nouveau type...</option>
          </select>
        </div>

        {/* New type fields */}
        {typeId === "new" && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
            <div>
              <label className="block text-xs font-medium text-zinc-500 mb-1">Nom du nouveau type</label>
              <input
                type="text"
                value={newTypeName}
                onChange={(e) => setNewTypeName(e.target.value)}
                placeholder="Ex: Coiffure de rappeur"
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-600 text-sm outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-500 mb-1">Emoji</label>
              <input
                type="text"
                value={newTypeEmoji}
                onChange={(e) => setNewTypeEmoji(e.target.value)}
                placeholder="💈"
                maxLength={2}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-600 text-sm outline-none"
              />
            </div>
          </div>
        )}

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ajoute une description (optionnelle)"
            rows={3}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500 resize-none"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">Tags</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="kendrick, rap, 2024 (séparés par des virgules)"
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 outline-none focus:border-indigo-500"
          />
        </div>

        {/* Submit */}
        <button
          onClick={submit}
          disabled={submitting || !name.trim() || typeId === ""}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-600 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
        >
          {submitting ? (
            "Création en cours..."
          ) : (
            <>
              <Plus className="w-5 h-5" /> Créer l&apos;entité
            </>
          )}
        </button>
      </div>
    </div>
  )
}
