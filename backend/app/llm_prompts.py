"""
Prompts for the LLM integration in RateEverything.
Each function returns a list of messages to send to the LLM.
"""

from typing import Optional


def system_prompt() -> str:
    return """Tu es un agent ontologique pour le site RateEverything, une plateforme de notation culturelle généralisée.

Tu travailles sur l'ontologie du site — les types d'entités, les entités elles-mêmes, leurs métadonnées et leurs relations.

RÈGLES STRICTES :
1. Ne JAMAIS halluciner. Tu peux proposer des entités à créer, mais marque-les clairement comme "suggested_new".
2. Confiance minimale de 70% pour proposer une relation. En dessous : ne propose rien.
3. Tu extrais TOUJOURS les métadonnées depuis le nom et la description.
4. Tu réponds UNIQUEMENT en JSON valide, sans texte avant/après.
5. Ne JAMAIS générer de relations avec des entités qui n'existent pas dans la liste fournie.
6. Si le nom d'entité est bizarre ou insultant, flag "suspicious" avec une raison.

FORMAT DE RÉPONSE ATTENDU (JSON) :
{
  "entity_name_normalized": "...",
  "confidence_name": 0.95,
  "type": {
    "action": "reuse" | "create" | "suggest_rename",
    "type_id": null | 123,
    "suggested_new_type": { ... }
  },
  "metadata": {
    "nom_propriete": {
      "value": "...",
      "source": "extracted_from_name" | "extracted_from_description" | "inferred",
      "confidence": 0.9,
      "property_type": "date" | "text" | "number" | "location" | "nationality"
    }
  },
  "relations": {
    "auto_confirm": [],
    "suggest_to_user": [],
    "suggested_new_entities": []
  },
  "tags": [],
  "charts_suggestions": { "auto_generate": [] }
}"""


def process_entity_prompt(
    name: str,
    type_name: Optional[str] = None,
    description: Optional[str] = None,
    existing_types: Optional[list[dict]] = None,
    existing_entities: Optional[list[dict]] = None,
) -> list[dict]:
    """Generate prompt for processing a new entity"""
    types_str = _format_list(existing_types, default="Aucun type existant")
    entities_str = _format_list(existing_entities[:50], default="Aucune entité existante")

    user_content = f"""Analyse cette nouvelle entité à créer :

Nom : "{name}"
Type déclaré : "{type_name or 'Non spécifié'}"
Description : "{description or 'Non spécifiée'}"

Types existants dans la base :
{types_str}

Entités existantes (les plus populaires) :
{entities_str}

Tâches :
1. Normalise le nom de l'entité (corrige orthographe, capitalisation, format)
2. Choisis le bon type : réutilise un existant ou suggères-en un nouveau
3. Extrais toutes les métadonnées possibles du nom et de la description
4. Trouve les relations avec les entités existantes (minimum 70% de confiance)
5. Suggère des entités connexes qui n'existent pas encore
6. Génère des tags pertinents pour la recherche"""

    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_content},
    ]


def suggest_type_prompt(
    raw_type_name: str,
    description: Optional[str] = None,
    existing_types: Optional[list[dict]] = None,
) -> list[dict]:
    """Generate prompt for creating/validating a new entity type"""
    types_str = _format_list(existing_types)

    user_content = f"""Un utilisateur veut créer un nouveau type d'entité :

Nom : "{raw_type_name}"
Description : "{description or 'Non spécifiée'}"

Types existants :
{types_str}

Analyse :
1. Valide ou rejette ce type. Est-ce un doublon ? Est-ce du troll ?
2. Suggère un type parent dans l'ontologie existante
3. Génère une description wiki concise expliquant ce type
4. Choisis un émoji représentatif
5. Suggère un schéma de métadonnées pour ce type (propriétés typiques)
6. Propose 3 exemples d'entités de ce type pour amorcer la pompe

Format JSON :
{{
  "is_valid": true,
  "reason": "...",
  "duplicate_of": null | "nom_du_type_existant",
  "suggested_parent": {{ "name": "...", "id": null | 123 }},
  "description": "...",
  "emoji": "...",
  "metadata_schema": [
    {{ "property_name": "...", "property_type": "text|date|number|...", "is_facet": true }}
  ],
  "example_entities": ["...", "...", "..."],
  "absurdity_level": 0.0
}}"""

    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_content},
    ]


def suggest_relations_prompt(
    entity_name: str,
    entity_type_name: str,
    entity_metadata: dict,
    existing_entities: list[dict],
) -> list[dict]:
    """Generate prompt for suggesting relations after entity creation"""
    entities_str = _format_list(existing_entities[:50])

    user_content = f"""L'entité "{entity_name}" (type: {entity_type_name}) vient d'être créée.

Ses métadonnées : {json.dumps(entity_metadata, ensure_ascii=False, indent=2)}

Entités existantes dans la base :
{entities_str}

Tâche : trouve des relations pertinentes entre cette nouvelle entité et les entités existantes.
Pour chaque relation :
- target_entity_id (null si nouvelle entité à créer)
- target_entity_name
- relation_type (verbe décrivant le lien, ex: "a_pour_coiffure")
- reverse_relation (verbe inverse, ex: "est_la_coiffure_de")
- confidence (0.0 à 1.0)
- reason (courte explication)

Ne propose que des relations avec ≥ 0.7 de confiance."""

    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_content},
    ]


def summarize_entity_prompt(entity: dict, ratings: list[dict]) -> list[dict]:
    """Generate a summary/description for an entity page"""
    avg = sum(r["score"] for r in ratings) / len(ratings) if ratings else 0

    user_content = f"""Génère un résumé de 2-3 phrases pour présenter cette entité :

Nom : {entity['name']}
Type : {entity.get('entity_type_name', 'N/A')}
Note moyenne : {avg:.1f}/10 ({len(ratings)} notes)
Description actuelle : {entity.get('description', 'N/A')}
Métadonnées : {json.dumps(entity.get('metadata', {}), ensure_ascii=False)}

Écris un texte engageant qui explique pourquoi cette entité est notable et ce
que les utilisateurs notent à son sujet. Ton : informatif mais accessible."""

    return [
        {"role": "system", "content": "Tu es un rédacteur culturel pour RateEverything. Tu écris des présentations d'entités courtes et engageantes en français. Réponds uniquement avec le texte du résumé, sans formatage JSON."},
        {"role": "user", "content": user_content},
    ]


import json


def _format_list(items: Optional[list[dict]], default: str = "Aucun") -> str:
    if not items:
        return default
    formatted = []
    for item in items:
        if "id" in item and "name" in item:
            formatted.append(f"  - [{item['id']}] {item.get('emoji', '')} {item['name']}")
        else:
            formatted.append(f"  - {item}")
    return "\n".join(formatted[:30])  # limit to 30 lines
