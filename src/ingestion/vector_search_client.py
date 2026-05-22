"""
Vector Search Client — Enterprise HR RAG Platform
Handles Vertex AI Vector Search operations
"""
import logging
import os
import json
from typing import Optional

logger = logging.getLogger(__name__)


class VectorSearchClient:
    """
    Manages Vertex AI Vector Search operations:
    - Upsert embeddings
    - Query similar vectors
    - Delete vectors
    """

    def __init__(
        self,
        project_id: str,
        region: str,
        index_endpoint_id: str,
        deployed_index_id: str
    ):
        from google.cloud import aiplatform
        aiplatform.init(project=project_id, location=region)

        self.project_id = project_id
        self.region = region
        self.index_endpoint_id = index_endpoint_id
        self.deployed_index_id = deployed_index_id

        # Initialize index endpoint
        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoint_id
        )
        logger.info(f"Vector Search client initialized: {index_endpoint_id}")

    def upsert_embeddings(
        self,
        embeddings: list[dict],
        batch_size: int = 100
    ) -> bool:
        """
        Upsert embeddings to Vector Search index.
        embeddings: list of {id, embedding, ...metadata}
        """
        try:
            total = 0
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]

                # Format for Vector Search
                datapoints = []
                for item in batch:
                    datapoints.append({
                        "datapoint_id": item['id'],
                        "feature_vector": item['embedding'],
                        "restricts": [
                            {
                                "namespace": "document_id",
                                "allow_list": [item.get('document_id', '')]
                            }
                        ],
                        "crowding_tag": {
                            "crowding_attribute": item.get('document_id', '')
                        }
                    })

                # Upsert to index
                # Use streaming update API
                from google.cloud.aiplatform_v1 import IndexServiceClient
                from google.cloud.aiplatform_v1.types import IndexDatapoint

                index_client = IndexServiceClient(
                    client_options={"api_endpoint": f"asia-south1-aiplatform.googleapis.com"}
                )

                index_datapoints = []
                for dp in datapoints:
                    index_datapoints.append(
                        IndexDatapoint(
                            datapoint_id=dp['datapoint_id'],
                            feature_vector=dp['feature_vector']
                        )
                    )

                index_name = self.endpoint.deployed_indexes[0].index
                index_client.upsert_datapoints(
                    index=index_name,
                    datapoints=index_datapoints
                )

                total += len(batch)
                logger.info(f"Upserted {total}/{len(embeddings)} embeddings")

            logger.info(f"✅ Total upserted: {total}")
            return True

        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return False

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_document_id: Optional[str] = None
    ) -> list[dict]:
        """
        Query Vector Search for similar vectors.
        Returns list of {id, distance} dicts.
        """
        try:
            # Build numeric filter if needed
            restricts = None
            if filter_document_id:
                restricts = [
                    aiplatform.matching_engine.matching_engine_index_endpoint\
                        .Namespace(
                            name="document_id",
                            allow_tokens=[filter_document_id]
                        )
                ]

            # Query the endpoint
            response = self.endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[query_embedding],
                num_neighbors=top_k
            )

            # Parse results
            results = []
            if response and response[0]:
                for neighbor in response[0]:
                    results.append({
                        'id': neighbor.id,
                        'distance': neighbor.distance
                    })

            logger.info(f"Query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def delete_embeddings(self, datapoint_ids: list[str]) -> bool:
        """Delete embeddings from index by ID."""
        try:
            self.endpoint.remove_datapoints(
                deployed_index_id=self.deployed_index_id,
                datapoint_ids=datapoint_ids
            )
            logger.info(f"Deleted {len(datapoint_ids)} embeddings")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
