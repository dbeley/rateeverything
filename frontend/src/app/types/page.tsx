"use client"

import { useEffect, useState } from "react"
import { api, EntityTypeTree } from "@/lib/api"
import Link from "next/link"
import { ChevronRight } from "lucide-react"

function TypeNode({ node, depth = 0 }: { node: EntityTypeTree; depth?: number }) {
  const hasChildren = node.children && node.children.length > 0

  return (
    <div>
      <Link
        href={`/type/${node.id}`}
        className="flex items-center gap-2 px-4 py-3 rounded-lg hover:bg-zinc-900 transition-colors group"
        style={{ paddingLeft: `${16 + depth * 20}px` }}
      >
        <span className="text-lg">{node.emoji || "📋"}</span>
        <span className="flex-1 font-medium text-zinc-200 group-hover:text-white">{node.name}</span>
        <span className="text-xs text-zinc-600">{node.entity_count} entités</span>
        {hasChildren && <ChevronRight className="w-4 h-4 text-zinc-600" />}
      </Link>
      {hasChildren && node.children.map((child) => (
        <TypeNode key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}

export default function TypesPage() {
  const [tree, setTree] = useState<EntityTypeTree[]>([])

  useEffect(() => {
    api.getTypeTree().then(setTree).catch(console.error)
  }, [])

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Types d&apos;entités</h1>
        <p className="text-zinc-400">Explore l&apos;ontologie complète. Chaque type peut avoir des sous-types.</p>
      </div>

      <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden">
        {tree.map((node) => (
          <TypeNode key={node.id} node={node} />
        ))}
        {tree.length === 0 && (
          <div className="p-8 text-center text-zinc-600">
            Aucun type d&apos;entité pour le moment.{" "}
            <Link href="/create" className="text-indigo-400 hover:underline">Crée le premier !</Link>
          </div>
        )}
      </div>
    </div>
  )
}
