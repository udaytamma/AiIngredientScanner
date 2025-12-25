#!/usr/bin/env python3
"""Audit and clean Qdrant ingredient database.

This script helps identify and remove duplicate ingredients from the
Qdrant vector database. Duplicates can occur when:
1. The same ingredient is stored with different names (e.g., "Salicylic Acid" vs "salicylic acid")
2. Similar ingredients are stored multiple times from different queries

Usage:
    # List all ingredients in the database
    python scripts/audit_qdrant.py --list

    # Find potential duplicates (semantic similarity > threshold)
    python scripts/audit_qdrant.py --find-duplicates

    # Delete specific ingredients by name
    python scripts/audit_qdrant.py --delete "Ingredient Name 1" "Ingredient Name 2"

    # Clean all duplicates interactively
    python scripts/audit_qdrant.py --clean

    # Dry run (show what would be deleted without actually deleting)
    python scripts/audit_qdrant.py --clean --dry-run
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client.models import Filter, FieldCondition, MatchValue

from config.settings import get_settings
from config.logging_config import get_logger
from tools.ingredient_lookup import (
    get_qdrant_client,
    ensure_collection_exists,
    get_embedding,
    COLLECTION_NAME,
)


logger = get_logger(__name__)


def list_all_ingredients() -> list[dict]:
    """List all ingredients in the Qdrant database.

    Returns:
        List of ingredient records with id, name, and metadata.
    """
    client = get_qdrant_client()
    ensure_collection_exists(client)

    # Scroll through all points in the collection
    ingredients = []
    offset = None

    while True:
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = results

        for point in points:
            payload = point.payload or {}
            ingredients.append({
                "id": point.id,
                "name": payload.get("name", "Unknown"),
                "purpose": payload.get("purpose", ""),
                "safety_rating": payload.get("safety_rating", 5),
                "category": payload.get("category", "Unknown"),
                "source": payload.get("source", "unknown"),
            })

        if next_offset is None:
            break
        offset = next_offset

    return ingredients


def find_duplicates(similarity_threshold: float = 0.95) -> list[tuple[dict, dict, float]]:
    """Find potential duplicate ingredients based on semantic similarity.

    Args:
        similarity_threshold: Minimum cosine similarity to consider as duplicate.

    Returns:
        List of (ingredient1, ingredient2, similarity_score) tuples.
    """
    client = get_qdrant_client()
    ensure_collection_exists(client)

    ingredients = list_all_ingredients()
    duplicates = []

    # Compare each ingredient against all others
    for i, ing1 in enumerate(ingredients):
        # Get embedding for this ingredient
        embedding = get_embedding(ing1["name"].lower().strip())

        # Search for similar ingredients
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=5,  # Get top 5 matches
        )

        for point in results.points:
            if point.id == ing1["id"]:
                continue  # Skip self

            similarity = point.score
            if similarity >= similarity_threshold:
                payload = point.payload or {}
                ing2 = {
                    "id": point.id,
                    "name": payload.get("name", "Unknown"),
                    "purpose": payload.get("purpose", ""),
                    "safety_rating": payload.get("safety_rating", 5),
                    "category": payload.get("category", "Unknown"),
                }

                # Avoid duplicate pairs (A,B) and (B,A)
                pair_key = tuple(sorted([ing1["id"], ing2["id"]]))
                pair_exists = any(
                    tuple(sorted([d[0]["id"], d[1]["id"]])) == pair_key
                    for d in duplicates
                )
                if not pair_exists:
                    duplicates.append((ing1, ing2, similarity))

    return duplicates


def find_exact_name_duplicates() -> dict[str, list[dict]]:
    """Find ingredients with exact same name (case-insensitive).

    Returns:
        Dict mapping lowercase name to list of ingredient records.
    """
    ingredients = list_all_ingredients()
    name_groups = defaultdict(list)

    for ing in ingredients:
        name_lower = ing["name"].lower().strip()
        name_groups[name_lower].append(ing)

    # Filter to only groups with duplicates
    return {name: ings for name, ings in name_groups.items() if len(ings) > 1}


def delete_ingredients(ids: list[int], dry_run: bool = False) -> int:
    """Delete ingredients by their IDs.

    Args:
        ids: List of point IDs to delete.
        dry_run: If True, don't actually delete.

    Returns:
        Number of points deleted (or would be deleted in dry run).
    """
    if dry_run:
        print(f"[DRY RUN] Would delete {len(ids)} points")
        return len(ids)

    client = get_qdrant_client()

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=ids,
    )

    print(f"Deleted {len(ids)} points")
    return len(ids)


def delete_by_name(names: list[str], dry_run: bool = False) -> int:
    """Delete ingredients by name.

    Args:
        names: List of ingredient names to delete.
        dry_run: If True, don't actually delete.

    Returns:
        Number of points deleted.
    """
    ingredients = list_all_ingredients()
    names_lower = {n.lower().strip() for n in names}

    ids_to_delete = [
        ing["id"] for ing in ingredients
        if ing["name"].lower().strip() in names_lower
    ]

    if not ids_to_delete:
        print("No matching ingredients found")
        return 0

    print(f"Found {len(ids_to_delete)} ingredient(s) to delete")
    return delete_ingredients(ids_to_delete, dry_run)


def interactive_clean(dry_run: bool = False):
    """Interactively review and clean duplicates.

    Args:
        dry_run: If True, don't actually delete.
    """
    # First check for exact name duplicates
    print("\n=== Checking for exact name duplicates ===\n")
    exact_dupes = find_exact_name_duplicates()

    if exact_dupes:
        print(f"Found {len(exact_dupes)} names with duplicates:\n")
        ids_to_delete = []

        for name, ings in exact_dupes.items():
            print(f"  '{name}' has {len(ings)} entries:")
            # Keep the first one, mark others for deletion
            for i, ing in enumerate(ings):
                status = "KEEP" if i == 0 else "DELETE"
                print(f"    [{status}] ID: {ing['id']}, Category: {ing['category']}")
                if i > 0:
                    ids_to_delete.append(ing["id"])
            print()

        if ids_to_delete:
            if dry_run:
                print(f"[DRY RUN] Would delete {len(ids_to_delete)} duplicate entries")
            else:
                confirm = input(f"Delete {len(ids_to_delete)} duplicate entries? (y/N): ")
                if confirm.lower() == 'y':
                    delete_ingredients(ids_to_delete)
                else:
                    print("Skipped deletion")
    else:
        print("No exact name duplicates found")

    # Then check for semantic duplicates
    print("\n=== Checking for semantic duplicates (>95% similarity) ===\n")
    semantic_dupes = find_duplicates(0.95)

    if semantic_dupes:
        print(f"Found {len(semantic_dupes)} potential semantic duplicates:\n")
        for ing1, ing2, similarity in semantic_dupes:
            print(f"  Similarity: {similarity:.3f}")
            print(f"    1. '{ing1['name']}' (ID: {ing1['id']})")
            print(f"    2. '{ing2['name']}' (ID: {ing2['id']})")
            print()
    else:
        print("No semantic duplicates found")


def main():
    parser = argparse.ArgumentParser(
        description="Audit and clean Qdrant ingredient database"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all ingredients in the database"
    )
    parser.add_argument(
        "--find-duplicates", "-f",
        action="store_true",
        help="Find potential duplicates based on semantic similarity"
    )
    parser.add_argument(
        "--delete", "-d",
        nargs="+",
        metavar="NAME",
        help="Delete ingredients by name"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Interactively clean duplicates"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.95,
        help="Similarity threshold for duplicate detection (default: 0.95)"
    )

    args = parser.parse_args()

    # Default to --list if no action specified
    if not any([args.list, args.find_duplicates, args.delete, args.clean]):
        args.list = True

    try:
        if args.list:
            print("\n=== All Ingredients in Qdrant ===\n")
            ingredients = list_all_ingredients()
            if not ingredients:
                print("No ingredients found in database")
            else:
                print(f"Total: {len(ingredients)} ingredients\n")
                for ing in sorted(ingredients, key=lambda x: x["name"].lower()):
                    print(f"  [{ing['id']}] {ing['name']}")
                    print(f"      Category: {ing['category']}, Safety: {ing['safety_rating']}/10")

        if args.find_duplicates:
            print(f"\n=== Finding Duplicates (threshold: {args.threshold}) ===\n")
            duplicates = find_duplicates(args.threshold)
            if not duplicates:
                print("No duplicates found")
            else:
                print(f"Found {len(duplicates)} potential duplicate pairs:\n")
                for ing1, ing2, similarity in duplicates:
                    print(f"  Similarity: {similarity:.3f}")
                    print(f"    1. '{ing1['name']}' (ID: {ing1['id']})")
                    print(f"    2. '{ing2['name']}' (ID: {ing2['id']})")
                    print()

        if args.delete:
            delete_by_name(args.delete, args.dry_run)

        if args.clean:
            interactive_clean(args.dry_run)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
