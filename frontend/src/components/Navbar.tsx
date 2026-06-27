"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Compass, Home, Shuffle, Plus, Search, LogIn, User } from "lucide-react"
import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth"

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/types", label: "Types", icon: Compass },
  { href: "/random", label: "Random", icon: Shuffle },
  { href: "/create", label: "Créer", icon: Plus },
]

export default function Navbar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<Array<{ id: number; name: string }>>([])
  const [showSearch, setShowSearch] = useState(false)

  const handleSearch = async (q: string) => {
    setSearchQuery(q)
    if (q.length < 2) {
      setSearchResults([])
      return
    }
    try {
      const results = await api.searchEntities(q)
      setSearchResults(results.slice(0, 8))
    } catch {
      setSearchResults([])
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-black/80 backdrop-blur-sm">
      <div className="flex h-16 items-center px-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2 mr-8">
          <span className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            RateEverything
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-900"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex-1" />

        {/* Search */}
        <div className="relative mr-2">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="p-2 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-900"
          >
            <Search className="w-5 h-5" />
          </button>
          {showSearch && (
            <div className="absolute right-0 top-12 w-80 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden">
              <input
                type="text"
                placeholder="Rechercher une entité..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full px-4 py-3 bg-transparent text-white placeholder-zinc-500 border-b border-zinc-800 outline-none"
                autoFocus
              />
              {searchResults.length > 0 && (
                <div className="max-h-64 overflow-y-auto">
                  {searchResults.map((r) => (
                    <Link
                      key={r.id}
                      href={`/entity/${r.id}`}
                      onClick={() => { setShowSearch(false); setSearchResults([]) }}
                      className="block px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
                    >
                      {r.name}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Auth */}
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-zinc-400">{user.display_name || user.username}</span>
            <button
              onClick={logout}
              className="text-xs text-zinc-600 hover:text-zinc-400"
            >
              Déconnexion
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-900 transition-colors"
          >
            <LogIn className="w-4 h-4" />
            Connexion
          </Link>
        )}
      </div>
    </header>
  )
}
