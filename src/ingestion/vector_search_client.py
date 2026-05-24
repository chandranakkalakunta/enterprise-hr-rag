"""
Vector Search Client - Enterprise HR RAG Platform
"""
import logging
logger = logging.getLogger(__name__)


class VectorSearchClient:
    def __init__(self, project_id, region, index_endpoint_id, deployed_index_id):
        from google.cloud import aiplatform
        aiplatform.init(project=project_id, location=region)
        self.project_id = project_id
        self.region = region
        self.index_endpoint_id = index_endpoint_id
        self.deployed_index_id = deployed_index_id
        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoint_id
        )
        logger.info(f"Vector Search client initialized")

    def upsert_embeddings(self, embeddings, batch_size=100):
        """Upsert embeddings using streaming update API."""
        try:
            from google.cloud.aiplatform_v1 import IndexServiceClient
            from google.cloud.aiplatform_v1.types import IndexDatapoint, UpsertDatapointsRequest

            client = IndexServiceClient(
                client_options={"api_endpoint": f"{self.region}-aiplatform.googleapis.com"}
            )

            # Get index name from endpoint
            endpoint_info = self.endpoint.gca_resource
            deployed = endpoint_info.deployed_indexes
            index_name = None
            for d in deployed:
                if d.id == self.deployed_index_id:
                    index_name = d.index
                    break

            if not index_name:
                logger.warning("Could not find deployed index name")
                return False

            total = 0
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                datapoints = []
                for item in batch:
                    dp = IndexDatapoint(
                        datapoint_id=item["id"],
                        feature_vector=item["embedding"]
                    )
                    datapoints.append(dp)

                request = UpsertDatapointsRequest(
                    index=index_name,
                    datapoints=datapoints
                )
                client.upsert_datapoints(request=request)
                total += len(batch)
                logger.info(f"Upserted {total}/{len(embeddings)}")

            logger.info(f"Total upserted: {total}")
            return True

        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return False

    def delete_embeddings(self, datapoint_ids: list) -> bool:
        """Delete embeddings from Vector Search index."""
        try:
            from google.cloud.aiplatform_v1 import IndexServiceClient
            from google.cloud.aiplatform_v1.types import RemoveDatapointsRequest

            client = IndexServiceClient(
                client_options={"api_endpoint": f"{self.region}-aiplatform.googleapis.com"}
            )

            endpoint_info = self.endpoint.gca_resource
            index_name = None
            for d in endpoint_info.deployed_indexes:
                if d.id == self.deployed_index_id:
                    index_name = d.index
                    break

            if not index_name:
                logger.warning("Could not find index name for delete")
                return False

            request = RemoveDatapointsRequest(
                index=index_name,
                datapoint_ids=datapoint_ids
            )
            client.remove_datapoints(request=request)
            logger.info(f"Deleted {len(datapoint_ids)} embeddings")
            return True

        except Exception as e:
            logger.error(f"Delete embeddings failed: {e}")
            return False

    def query(self, query_embedding, top_k=10):
        """Query Vector Search."""
        try:
            response = self.endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[query_embedding],
                num_neighbors=top_k
            )
            results = []
            if response and response[0]:
                for neighbor in response[0]:
                    results.append({
                        "id": neighbor.id,
                        "distance": neighbor.distance
                    })
            logger.info(f"Query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
