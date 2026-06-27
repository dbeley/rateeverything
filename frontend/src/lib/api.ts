const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export interface EntityType {
  id: number
  name: string
  description: string | null
  emoji: string | null
  parent_type_id: number | null
  is_verified: boolean
  absurdity_level: number
  created_at: string
}

export interface EntityTypeTree extends EntityType {
  children: EntityTypeTree[]
  entity_count: number
}

export interface Entity {
  id: number
  name: string
  entity_type_id: number
  entity_type: EntityType | null
  description: string | null
  image_url: string | null
  metadata: Record<string, unknown> | null
  avg_rating: number | null
  rating_count: number
  created_at: string
}

export interface Rating {
  id: number
  user_id: number
  entity_id: number
  entity: Entity | null
  score: number
  review: string | null
  tags: string[] | null
  has_spoiler: boolean
  created_at: string
  updated_at: string
}

export interface RelationType {
  id: number
  name: string
  reverse_name: string | null
  description: string | null
  category: string | null
}

export interface EntityLink {
  id: number
  source_entity_id: number
  target_entity_id: number
  relation_type_id: number
  relation_type: RelationType | null
  source_entity: Entity | null
  target_entity: Entity | null
  metadata: Record<string, unknown> | null
  confidence: number
  auto_generated: boolean
}

export interface EntityGraph {
  nodes: Array<{
    id: number
    name: string
    type: string
    is_center: boolean
  }>
  edges: Array<{
    source: number
    target: number
    relation: string
    reverse_relation: string | null
    confidence: number
    auto_generated: boolean
  }>
}

export interface ChartConfig {
  chart_type: string
  title: string
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
  }>
}

export interface EntityCharts {
  rating_distribution: ChartConfig | null
  rating_over_time: ChartConfig | null
  comparative_radar: ChartConfig | null
  metadata_breakdown: Record<string, ChartConfig> | null
}

export interface DashboardStats {
  most_active_types: Array<{
    id: number
    name: string
    emoji: string | null
    rating_count: number
  }>
  quick_stats: {
    total_entities: number
    total_types: number
    total_ratings: number
  }
}

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(`API error ${res.status}: ${error}`)
  }
  return res.json()
}

export const api = {
  // Types
  getTypes: (search?: string) =>
    fetcher<EntityType[]>(`/types${search ? `?search=${search}` : ""}`),
  getTypeTree: () => fetcher<EntityTypeTree[]>("/types/tree"),
  getType: (id: number) => fetcher<EntityType>(`/types/${id}`),
  createType: (data: Partial<EntityType>) =>
    fetcher<EntityType>("/types", { method: "POST", body: JSON.stringify(data) }),

  // Entities
  getEntities: (params?: { type_id?: number; search?: string; sort?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.type_id) qs.set("type_id", String(params.type_id))
    if (params?.search) qs.set("search", params.search)
    if (params?.sort) qs.set("sort", params.sort)
    if (params?.limit) qs.set("limit", String(params.limit))
    if (params?.offset) qs.set("offset", String(params.offset))
    return fetcher<Entity[]>(`/entities?${qs}`)
  },
  searchEntities: (q: string) => fetcher<Entity[]>(`/entities/search?q=${encodeURIComponent(q)}`),
  getEntity: (id: number) => fetcher<Entity>(`/entities/${id}`),
  getTrending: (limit?: number) => fetcher<Entity[]>(`/entities/trending${limit ? `?limit=${limit}` : ""}`),
  getRandom: () => fetcher<Entity>("/entities/random"),
  createEntity: (data: { name: string; entity_type_id: number; description?: string; metadata?: Record<string, unknown>; tags?: string[] }) =>
    fetcher<Entity>("/entities", { method: "POST", body: JSON.stringify(data) }),

  // Ratings
  getRatings: (params?: { entity_id?: number; user_id?: number; sort?: string }) => {
    const qs = new URLSearchParams()
    if (params?.entity_id) qs.set("entity_id", String(params.entity_id))
    if (params?.user_id) qs.set("user_id", String(params.user_id))
    if (params?.sort) qs.set("sort", params.sort)
    return fetcher<Rating[]>(`/ratings?${qs}`)
  },
  getRatingStats: (entity_id: number) => fetcher<{ avg: number; count: number; min: number; max: number }>(`/ratings/stats/${entity_id}`),
  createRating: (data: { entity_id: number; score: number; review?: string; tags?: string[]; has_spoiler?: boolean }, userId = 1) =>
    fetcher<Rating>(`/ratings?user_id=${userId}`, { method: "POST", body: JSON.stringify(data) }),

  // Relations
  getRelationTypes: () => fetcher<RelationType[]>("/relations/types"),
  getEntityGraph: (entity_id: number) => fetcher<EntityGraph>(`/relations/graph/${entity_id}`),
  createLink: (data: { source_entity_id: number; target_entity_id: number; relation_type_id: number }) =>
    fetcher<EntityLink>("/relations/links", { method: "POST", body: JSON.stringify(data) }),

  // Charts
  getEntityCharts: (entity_id: number) => fetcher<EntityCharts>(`/charts/entity/${entity_id}`),
  getDashboard: () => fetcher<DashboardStats>("/charts/dashboard"),

  // LLM
  analyzeEntity: (data: { user_input_raw: string; type_name?: string; description?: string }) =>
    fetcher("/llm/analyze-entity", { method: "POST", body: JSON.stringify(data) }),
  suggestType: (name: string, description?: string) =>
    fetcher(`/llm/suggest-type?name=${encodeURIComponent(name)}${description ? `&description=${encodeURIComponent(description)}` : ""}`, { method: "POST" }),
}
