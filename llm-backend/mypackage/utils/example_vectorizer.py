"""
Example Vectorizer Utility

This module provides functionality to vectorize and retrieve examples from JSON files.
It indexes all examples in ChromaDB for efficient similarity search and retrieval.

Key features:
- Vectorization of examples from JSON files
- Collection management for example vectors
- Similarity-based example retrieval for various functions
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from mypackage.utils.chroma_db import ChromaDBManager

logger = logging.getLogger(__name__)

# Constants
EXAMPLES_DIR = (
    Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "examples"
)
COLLECTION_PREFIX = "examples_"  # Prefix for example collections in ChromaDB


class ExampleVectorizer:
    """
    Utility class for vectorizing and retrieving examples from the examples directory.
    """

    @classmethod
    def vectorize_examples(cls, force_refresh: bool = False) -> Dict[str, int]:
        """
        Vectorize all example files in the examples directory.

        Args:
            force_refresh: If True, delete existing collections and recreate them

        Returns:
            Dictionary mapping collection names to the number of examples vectorized
        """
        result = {}

        # Ensure ChromaDB is initialized
        if not ChromaDBManager.client:
            ChromaDBManager.initialize()

        # List all collections
        all_collections = [c.name for c in ChromaDBManager.list_collections()]

        # Process each JSON file in the examples directory
        for json_file in EXAMPLES_DIR.glob("*.json"):
            function_name = json_file.stem
            collection_name = f"{COLLECTION_PREFIX}{function_name}"

            # Check if collection exists and handle refresh
            if collection_name in all_collections:
                if force_refresh:
                    logger.info(
                        f"Deleting existing collection {collection_name} for refresh"
                    )
                    ChromaDBManager.delete_collection(collection_name)
                else:
                    logger.info(
                        f"Collection {collection_name} already exists, skipping"
                    )
                    collection = ChromaDBManager.get_or_create_collection(
                        collection_name
                    )
                    result[function_name] = collection.count()
                    continue

            # Create collection
            collection = ChromaDBManager.get_or_create_collection(collection_name)

            # Load examples from JSON file
            try:
                with open(json_file, "r") as f:
                    examples = json.load(f)

                logger.info(f"Loaded {len(examples)} examples from {json_file}")

                # Vectorize and add each example
                for i, example in enumerate(examples):
                    if "query" in example:
                        # Generate embedding for the query
                        try:
                            query_text = example["query"]
                            query_embedding = ChromaDBManager.generate_embedding(
                                query_text
                            )

                            # Add to collection
                            collection.add(
                                ids=[f"{function_name}_{i}"],
                                embeddings=[query_embedding],
                                documents=[query_text],
                                metadatas=[
                                    {
                                        "function": function_name,
                                        "example_id": i,
                                        "full_example": json.dumps(example),
                                    }
                                ],
                            )
                            logger.debug(f"Vectorized example {i} from {function_name}")
                        except Exception as e:
                            logger.error(
                                f"Failed to vectorize example {i} from {function_name}: {e}"
                            )

                result[function_name] = collection.count()
                logger.info(
                    f"Vectorized {collection.count()} examples for {function_name}"
                )

            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
                result[function_name] = 0

        return result

    @classmethod
    def get_similar_examples(
        cls, function_name: str, query: str, n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar examples for a specific function.

        Args:
            function_name: Name of the function to get examples for
            query: User query to find similar examples for
            n_results: Number of examples to return

        Returns:
            List of example dictionaries with distance information added
        """
        collection_name = f"{COLLECTION_PREFIX}{function_name}"

        # Check if collection exists
        collections = [c.name for c in ChromaDBManager.list_collections()]
        if collection_name not in collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return []

        # Find similar examples
        try:
            results = ChromaDBManager.find_similar(
                collection_name=collection_name, query=query, n_results=n_results
            )

            # Process results
            examples = []
            if results["ids"] and results["ids"][0]:
                for i, example_id in enumerate(results["ids"][0]):
                    try:
                        metadata = results["metadatas"][0][i]
                        distance = (
                            results["distances"][0][i]
                            if "distances" in results and results["distances"]
                            else 1.0
                        )

                        # Parse the full example from metadata
                        example = json.loads(metadata.get("full_example", "{}"))

                        # Add distance information
                        example["distance"] = distance
                        examples.append(example)
                    except Exception as e:
                        logger.error(f"Error processing example result {i}: {e}")

            logger.info(f"Found {len(examples)} similar examples for {function_name}")
            return examples
        except Exception as e:
            logger.error(f"Error finding similar examples for {function_name}: {e}")
            return []


# Initialize function to run when module is imported
def initialize_examples(force_refresh: bool = False):
    """
    Initialize all example collections.

    Args:
        force_refresh: If True, delete existing collections and recreate them

    Returns:
        Dictionary of results from vectorization
    """
    return ExampleVectorizer.vectorize_examples(force_refresh=force_refresh)
