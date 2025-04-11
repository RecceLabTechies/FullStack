"""
ChromaDB Utility Module

This module provides a singleton class for managing ChromaDB connections and operations.
It centralizes all ChromaDB interactions, providing consistent access across
different components of the application.

Key features:
- Singleton pattern for ChromaDB client management
- Helper methods for common ChromaDB operations
- Consistent error handling and logging
"""

import logging
import os
from typing import Any, Dict, List

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """
    Singleton class for managing ChromaDB connections and operations.

    This class provides centralized access to the ChromaDB vector database,
    with methods for initializing connections, managing collections, and
    performing vector operations.

    Attributes:
        client: ChromaDB client instance
        embeddings_model: Model used for generating embeddings
    """

    client = None
    embeddings_model = None

    @classmethod
    def initialize(cls) -> bool:
        """
        Initialize the ChromaDB connection and embeddings model.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Connect to ChromaDB
            cls.client = chromadb.HttpClient(
                host=os.getenv("CHROMA_SERVER_HOST", "chromadb"),
                port=int(os.getenv("CHROMA_SERVER_PORT", "8000")),
            )

            # Test connection
            cls.client.heartbeat()

            # Initialize the embeddings model
            cls.embeddings_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            logger.info("Successfully connected to ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            return False

    @classmethod
    def get_client(cls):
        """
        Get the ChromaDB client instance, initializing it if needed.

        Returns:
            ChromaDB client instance
        """
        if cls.client is None:
            cls.initialize()
        return cls.client

    @classmethod
    def get_embeddings_model(cls):
        """
        Get the embeddings model, initializing if needed.

        Returns:
            Embeddings model instance
        """
        if cls.embeddings_model is None:
            cls.initialize()
        return cls.embeddings_model

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as a list of floats
        """
        if cls.embeddings_model is None:
            cls.initialize()
        return cls.embeddings_model.embed_query(text)

    @classmethod
    def get_or_create_collection(cls, collection_name: str) -> Any:
        """
        Get a ChromaDB collection or create it if it doesn't exist.

        Args:
            collection_name: Name of the collection

        Returns:
            ChromaDB collection
        """
        if cls.client is None:
            cls.initialize()

        try:
            return cls.client.get_collection(name=collection_name)
        except Exception:
            return cls.client.create_collection(name=collection_name)

    @classmethod
    def list_collections(cls) -> List[Any]:
        """
        List all collections in ChromaDB.

        Returns:
            List of ChromaDB collections
        """
        if cls.client is None:
            cls.initialize()

        return cls.client.list_collections()

    @classmethod
    def delete_collection(cls, collection_name: str) -> bool:
        """
        Delete a collection from ChromaDB.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if cls.client is None:
            cls.initialize()

        try:
            cls.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            return False

    @classmethod
    def find_similar(cls, collection_name: str, query: str, n_results: int = 3) -> Dict:
        """
        Find similar items in a collection based on a query.

        Args:
            collection_name: Name of the collection to search
            query: Query text to find similar items for
            n_results: Number of results to return

        Returns:
            Dictionary with search results
        """
        if cls.client is None:
            cls.initialize()

        try:
            collection = cls.get_or_create_collection(collection_name)
            query_embedding = cls.generate_embedding(query)

            return collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}
