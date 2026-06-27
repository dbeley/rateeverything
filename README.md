# RateEverything 🎯

Notez tout ce qui existe. Albums, coiffures, pochettes, films, performances, expressions faciales... **tout est culturel, tout est notable.**

RateEverything est une plateforme de notation culturelle généralisée avec une ontologie auto-générée par IA.

## Concept

Contrairement aux sites de critique traditionnels, RateEverything ne pré-définit pas ce qui est "notable". L'ontologie émerge des utilisateurs, assistée par un LLM (DeepSeek) qui :

- Normalise les noms d'entités
- Suggère des types d'entités et les positionne dans l'ontologie
- Extrait les métadonnées automatiquement
- Détecte les relations entre entités
- Génère des résumés et des descriptions

### Exemples

| Type | Entité | Note |
|---|---|---|
| 🎵 Morceau de rap | Not Like Us — Kendrick Lamar | 9.2/10 |
| 💇 Coiffure de rappeur | La coupe de Kendrick dans Not Like Us | 7.8/10 |
| 👟 Placement de produit | Nike Air Force 1 dans le clip | 9.5/10 |
| 📚 Essai philosophique | Note de bas de page #42 dans "Simulacres..." | 6.0/10 |

## Stack technique

- **Backend** : Python / FastAPI + SQLAlchemy async + PostgreSQL
- **Frontend** : Next.js 16 + Tailwind CSS v4 + Recharts
- **LLM** : DeepSeek API (deepseek-chat)
- **Tests** : Pytest + aiosqlite (100% pass)

## Architecture

```
rateeverything/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application FastAPI
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models.py            # Modèles ORM (7 tables)
│   │   ├── schemas.py           # Schémas Pydantic
│   │   ├── llm_client.py        # Client DeepSeek API
│   │   ├── llm_prompts.py       # Prompts LLM
│   │   ├── routes_types.py      # CRUD types d'entités
│   │   ├── routes_entities.py   # CRUD entités + search
│   │   ├── routes_ratings.py    # CRUD notes
│   │   ├── routes_relations.py  # CRUD relations + graphe
│   │   ├── routes_llm.py        # Endpoints LLM
│   │   └── routes_charts.py     # Données de charts
│   └── tests/
│       └── test_api.py          # 12 tests API
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Dashboard
│       │   ├── create/page.tsx  # Création d'entité
│       │   ├── entity/[id]/page.tsx  # Détail entité
│       │   ├── random/page.tsx  # Entité aléatoire
│       │   ├── type/[id]/page.tsx   # Détail type
│       │   └── types/page.tsx   # Arbre des types
│       ├── components/
│       │   └── Navbar.tsx       # Navigation
│       └── lib/
│           ├── api.ts           # Client API
│           └── utils.ts         # Utilitaires
└── docker-compose.yml
```

## Modèle de données

7 tables principales :

- **EntityType** — Types d'entités (ontologie, hiérarchie parent/enfant)
- **Entity** — Entités (liées à un type, avec métadonnées JSON)
- **Rating** — Notes des utilisateurs (score 0-10, review, tags)
- **RelationType** — Types de relations (ex: "a_pour_coiffure", "est_la_coiffure_de")
- **EntityLink** — Liens entre entités (graphe orienté typé)
- **EntityMetadata** — Métadonnées structurées indexées
- **EntityTag** — Tags libres pour la recherche

## API REST

### Types
- `GET /api/types` — Liste des types
- `GET /api/types/tree` — Arbre ontologique
- `POST /api/types` — Créer un type
- `GET /api/types/{id}` — Détail d'un type

### Entités
- `GET /api/entities` — Liste (filtres: type_id, search, sort)
- `GET /api/entities/search?q=...` — Recherche full-text
- `GET /api/entities/trending` — Tendances
- `GET /api/entities/random` — Entité aléatoire
- `POST /api/entities` — Créer (+ enrichissement LLM)
- `GET /api/entities/{id}` — Détail

### Notes
- `POST /api/ratings` — Noter une entité (score 0-10)
- `GET /api/ratings/stats/{id}` — Statistiques

### Relations
- `GET /api/relations/graph/{id}` — Graphe des relations
- `POST /api/relations/links` — Lier deux entités

### Charts
- `GET /api/charts/entity/{id}` — Distribution, évolution
- `GET /api/charts/type/{id}` — Top entités, timeline
- `GET /api/charts/dashboard` — Stats globales

### LLM
- `POST /api/llm/analyze-entity` — Analyse LLM d'une entité
- `POST /api/llm/suggest-type` — Suggestion de type
- `POST /api/llm/summarize-entity/{id}` — Résumé IA

## Installation

### Avec Docker

```bash
# Cloner
git clone https://github.com/dbeley/rateeverything.git
cd rateeverything

# Configurer la clé DeepSeek
echo "sk-votre-cle-api" > ~/.deepseek_api_key

# Lancer
docker compose up -d

# Accès : http://localhost:3000
# API : http://localhost:8000/api
```

### Sans Docker

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Lancer PostgreSQL, puis :
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
pnpm install
pnpm dev
```

### Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

## Roadmap

- [x] Backend API REST complet
- [x] Intégration LLM (DeepSeek)
- [x] Frontend Next.js (dashboard, entités, types)
- [x] Charts (distribution, évolution, top)
- [x] Graphe de relations
- [ ] Authentification (comptes utilisateurs)
- [ ] Collections / listes personnelles
- [ ] Badges et achievements
- [ ] Page profil utilisateur
- [ ] Recherche vectorielle (pgvector)
- [ ] Mode "délire" pour les types absurdes
- [ ] Import batch depuis RateYourMusic/Letterboxd

## Licence

MIT
