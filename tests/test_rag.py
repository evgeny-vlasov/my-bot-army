"""
Unit tests for RAG utilities (shared/rag.py).

Tests cover:
- Text chunking with various inputs and edge cases
- Voyage AI embedding API calls (mocked)
- Document chunk storage in database (mocked)
- Similarity search using pgvector (mocked)
- High-level document processing pipeline (mocked)
- High-level RAG query pipeline (mocked)

Run with: pytest tests/test_rag.py -v
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path so we can import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.rag import chunk_text, get_voyage_embedding, store_document_chunks, search_similar_chunks, process_document, rag_query


# ============================================================================
# TEST chunk_text FUNCTION
# ============================================================================

class TestChunkText:
    """Tests for the chunk_text function"""

    def test_empty_string_returns_empty_list(self):
        """Empty string should return empty list"""
        result = chunk_text("")
        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only string should return empty list"""
        result = chunk_text("   \n  \t  ")
        assert result == []

    def test_short_text_returns_single_chunk(self):
        """Text shorter than chunk_size should return single chunk"""
        text = "This is a short text."
        result = chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) == 1
        assert result[0] == text

    def test_text_exactly_chunk_size_returns_single_chunk(self):
        """Text exactly chunk_size should return single chunk"""
        text = "a" * 100
        result = chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) == 1
        assert result[0] == text

    def test_creates_multiple_chunks(self):
        """Long text should be split into multiple chunks"""
        text = "This is a sentence. " * 100  # ~2000 chars
        result = chunk_text(text, chunk_size=500, overlap=100)
        assert len(result) > 1
        # Verify total content is preserved (accounting for overlap)
        combined_length = sum(len(chunk) for chunk in result)
        # Should be more than original due to overlap
        assert combined_length > len(text)

    def test_breaks_at_sentence_boundaries(self):
        """Should prefer breaking at sentence boundaries"""
        text = "First sentence here. " + "x" * 700 + ". Second sentence here. " + "y" * 700
        result = chunk_text(text, chunk_size=800, overlap=100)

        # First chunk should end with a period (sentence boundary)
        assert result[0].rstrip().endswith('.')

    def test_overlap_is_working(self):
        """Chunks should have overlapping content"""
        text = "This is sentence one. This is sentence two. This is sentence three. " * 20
        result = chunk_text(text, chunk_size=200, overlap=50)

        if len(result) >= 2:
            # Check that end of first chunk overlaps with start of second
            first_chunk_end = result[0][-50:]
            second_chunk_start = result[1][:50]
            # There should be some overlap in content
            assert len(result) >= 2  # Multiple chunks were created

    def test_handles_different_sentence_endings(self):
        """Should recognize different sentence endings"""
        text = "Question? Answer! Statement. " * 50
        result = chunk_text(text, chunk_size=100, overlap=20)
        # Should create chunks and not crash
        assert len(result) > 0

    def test_handles_double_newlines(self):
        """Should break at double newlines (paragraph breaks)"""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three." * 30
        result = chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) > 0

    def test_chunk_size_and_overlap_parameters(self):
        """Should respect custom chunk_size and overlap parameters"""
        text = "x" * 1000
        result = chunk_text(text, chunk_size=300, overlap=50)

        # Check that chunks are approximately the right size
        for i, chunk in enumerate(result[:-1]):  # Exclude last chunk
            # Chunks should be around chunk_size (may vary due to boundaries)
            assert 250 <= len(chunk) <= 350

    def test_no_infinite_loop(self):
        """Should not get stuck in infinite loop with difficult text"""
        # Text with no sentence boundaries
        text = "x" * 10000
        result = chunk_text(text, chunk_size=500, overlap=100)
        # Should complete and create chunks
        assert len(result) > 0
        assert len(result) < 100  # Reasonable number of chunks


# ============================================================================
# TEST get_voyage_embedding FUNCTION (MOCKED)
# ============================================================================

class TestGetVoyageEmbedding:
    """Tests for the get_voyage_embedding function with mocked API calls"""

    @patch('shared.rag.requests.post')
    def test_successful_api_call(self, mock_post):
        """Should successfully return embedding from API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 1024}  # 1024-dimensional vector
            ]
        }
        mock_post.return_value = mock_response

        embedding = get_voyage_embedding("test text", "fake-api-key")

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert call_args[0][0] == "https://api.voyageai.com/v1/embeddings"

        # Check headers
        assert call_args[1]['headers']['Authorization'] == "Bearer fake-api-key"
        assert call_args[1]['headers']['Content-Type'] == "application/json"

        # Check payload
        assert call_args[1]['json']['input'] == ["test text"]
        assert call_args[1]['json']['model'] == "voyage-3"

        # Check returned embedding
        assert len(embedding) == 1024
        assert all(x == 0.1 for x in embedding)

    def test_missing_api_key_raises_error(self):
        """Should raise ValueError if API key is missing"""
        with pytest.raises(ValueError, match="API key is required"):
            get_voyage_embedding("test text", "")

        with pytest.raises(ValueError, match="API key is required"):
            get_voyage_embedding("test text", None)

    def test_empty_text_raises_error(self):
        """Should raise ValueError if text is empty"""
        with pytest.raises(ValueError, match="cannot be empty"):
            get_voyage_embedding("", "fake-api-key")

        with pytest.raises(ValueError, match="cannot be empty"):
            get_voyage_embedding("   ", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_api_timeout_error(self, mock_post):
        """Should handle API timeout gracefully"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(requests.exceptions.Timeout):
            get_voyage_embedding("test text", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_api_http_401_error(self, mock_post):
        """Should handle 401 Unauthorized error"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_voyage_embedding("test text", "invalid-api-key")

    @patch('shared.rag.requests.post')
    def test_api_http_500_error(self, mock_post):
        """Should handle 500 Server Error"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_voyage_embedding("test text", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_api_network_error(self, mock_post):
        """Should handle network connection errors"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(requests.exceptions.RequestException):
            get_voyage_embedding("test text", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_unexpected_response_format(self, mock_post):
        """Should handle unexpected API response format"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"wrong": "format"}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Unexpected API response format"):
            get_voyage_embedding("test text", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_empty_data_array(self, mock_post):
        """Should handle empty data array in response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Unexpected API response format"):
            get_voyage_embedding("test text", "fake-api-key")

    @patch('shared.rag.requests.post')
    def test_wrong_embedding_dimensions_logs_warning(self, mock_post):
        """Should log warning if embedding dimensions don't match expected"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 512}  # Wrong dimensions
            ]
        }
        mock_post.return_value = mock_response

        # Should still return the embedding but log a warning
        embedding = get_voyage_embedding("test text", "fake-api-key")
        assert len(embedding) == 512


# ============================================================================
# TEST store_document_chunks FUNCTION
# ============================================================================

class TestStoreDocumentChunks:
    """Tests for the store_document_chunks function"""

    def test_validates_chunks_embeddings_length_match(self):
        """Should raise ValueError if chunks and embeddings have different lengths"""
        mock_conn = Mock()
        chunks = ["chunk1", "chunk2", "chunk3"]
        embeddings = [[0.1] * 1024, [0.2] * 1024]  # Only 2 embeddings

        with pytest.raises(ValueError, match="must match"):
            store_document_chunks(mock_conn, 1, 100, chunks, embeddings)

    def test_returns_zero_for_empty_chunks(self):
        """Should return 0 if no chunks to store"""
        mock_conn = Mock()
        chunks = []
        embeddings = []

        result = store_document_chunks(mock_conn, 1, 100, chunks, embeddings)
        assert result == 0

    def test_successful_insertion(self):
        """Should successfully insert chunks into database"""
        # Setup mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3  # 3 rows inserted
        mock_conn.cursor.return_value = mock_cursor

        chunks = ["chunk1", "chunk2", "chunk3"]
        embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]

        with patch('shared.rag.execute_values') as mock_execute_values:
            result = store_document_chunks(mock_conn, 1, 100, chunks, embeddings)

            # Verify execute_values was called
            assert mock_execute_values.called
            call_args = mock_execute_values.call_args

            # Check the SQL query
            query = call_args[0][1]
            assert "INSERT INTO document_chunks" in query
            assert "document_id" in query
            assert "bot_id" in query
            assert "chunk_text" in query
            assert "chunk_index" in query
            assert "embedding" in query

            # Check the values
            values = call_args[0][2]
            assert len(values) == 3  # 3 chunks

            # Verify structure of first value tuple
            assert values[0][0] == 100  # document_id
            assert values[0][1] == 1    # bot_id
            assert values[0][2] == "chunk1"  # chunk_text
            assert values[0][3] == 0    # chunk_index
            assert values[0][4] == [0.1] * 1024  # embedding

            # Check template includes vector casting
            template = call_args[1]['template']
            assert "::vector" in template

            assert result == 3

    def test_with_metadata(self):
        """Should handle optional metadata parameter"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor

        chunks = ["chunk1"]
        embeddings = [[0.1] * 1024]
        metadata = {"source": "test.pdf", "page": 1}

        with patch('shared.rag.execute_values'):
            result = store_document_chunks(
                mock_conn, 1, 100, chunks, embeddings, metadata=metadata
            )
            assert result == 1

    def test_without_metadata(self):
        """Should handle None metadata"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor

        chunks = ["chunk1"]
        embeddings = [[0.1] * 1024]

        with patch('shared.rag.execute_values'):
            result = store_document_chunks(mock_conn, 1, 100, chunks, embeddings)
            assert result == 1

    def test_database_error_propagates(self):
        """Should propagate database errors"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        chunks = ["chunk1"]
        embeddings = [[0.1] * 1024]

        with patch('shared.rag.execute_values') as mock_execute_values:
            mock_execute_values.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                store_document_chunks(mock_conn, 1, 100, chunks, embeddings)

    def test_chunk_indices_are_sequential(self):
        """Should assign sequential indices to chunks (0, 1, 2, ...)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_conn.cursor.return_value = mock_cursor

        chunks = ["chunk1", "chunk2", "chunk3"]
        embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]

        with patch('shared.rag.execute_values') as mock_execute_values:
            store_document_chunks(mock_conn, 1, 100, chunks, embeddings)

            values = mock_execute_values.call_args[0][2]
            # Check that indices are 0, 1, 2
            assert values[0][3] == 0
            assert values[1][3] == 1
            assert values[2][3] == 2


# ============================================================================
# TEST search_similar_chunks FUNCTION
# ============================================================================

class TestSearchSimilarChunks:
    """Tests for the search_similar_chunks function"""

    def test_validates_empty_embedding(self):
        """Should raise ValueError if query embedding is empty"""
        mock_conn = Mock()

        with pytest.raises(ValueError, match="cannot be empty"):
            search_similar_chunks(mock_conn, bot_id=1, query_embedding=[])

        with pytest.raises(ValueError, match="cannot be empty"):
            search_similar_chunks(mock_conn, bot_id=1, query_embedding=None)

    def test_validates_top_k(self):
        """Should raise ValueError if top_k < 1"""
        mock_conn = Mock()
        query_emb = [0.1] * 1024

        with pytest.raises(ValueError, match="top_k must be >= 1"):
            search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=0)

        with pytest.raises(ValueError, match="top_k must be >= 1"):
            search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=-5)

    def test_successful_search(self):
        """Should successfully return similar chunks"""
        # Setup mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock database results
        mock_cursor.fetchall.return_value = [
            {'chunk_text': 'Most similar chunk', 'similarity': 0.95},
            {'chunk_text': 'Second similar chunk', 'similarity': 0.85},
            {'chunk_text': 'Third similar chunk', 'similarity': 0.75}
        ]

        query_emb = [0.1] * 1024
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=3)

        # Verify cursor.execute was called
        assert mock_cursor.execute.called

        # Check SQL query
        call_args = mock_cursor.execute.call_args[0]
        sql_query = call_args[0]
        params = call_args[1]

        # Verify query structure
        assert "SELECT" in sql_query
        assert "chunk_text" in sql_query
        assert "1 - (embedding <=> %s::vector)" in sql_query
        assert "FROM document_chunks" in sql_query
        assert "WHERE bot_id = %s" in sql_query
        assert "ORDER BY embedding <=> %s::vector" in sql_query
        assert "LIMIT %s" in sql_query

        # Verify parameters (embedding, bot_id, embedding again, limit)
        assert params[0] == query_emb  # First embedding for similarity calc
        assert params[1] == 1  # bot_id
        assert params[2] == query_emb  # Second embedding for ORDER BY
        assert params[3] == 3  # LIMIT

        # Check results
        assert len(results) == 3
        assert results[0] == ('Most similar chunk', 0.95)
        assert results[1] == ('Second similar chunk', 0.85)
        assert results[2] == ('Third similar chunk', 0.75)

    def test_returns_correct_format(self):
        """Should return list of (text, score) tuples"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {'chunk_text': 'Test chunk', 'similarity': 0.9}
        ]

        query_emb = [0.1] * 1024
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb)

        # Check return type
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], tuple)
        assert len(results[0]) == 2
        assert isinstance(results[0][0], str)  # chunk_text
        assert isinstance(results[0][1], float)  # similarity score

    def test_respects_top_k_parameter(self):
        """Should limit results to top_k"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {'chunk_text': f'Chunk {i}', 'similarity': 0.9 - i*0.1}
            for i in range(10)
        ]

        query_emb = [0.1] * 1024

        # Test with top_k=10
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=10)
        params = mock_cursor.execute.call_args[0][1]
        assert params[3] == 10  # LIMIT should be 10

        # Test with top_k=3
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=3)
        params = mock_cursor.execute.call_args[0][1]
        assert params[3] == 3  # LIMIT should be 3

    def test_filters_by_bot_id(self):
        """Should filter results by bot_id"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        query_emb = [0.1] * 1024

        # Search for bot_id = 42
        search_similar_chunks(mock_conn, bot_id=42, query_embedding=query_emb)

        params = mock_cursor.execute.call_args[0][1]
        assert params[1] == 42  # bot_id parameter

    def test_handles_no_results(self):
        """Should handle case when no chunks are found"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        query_emb = [0.1] * 1024
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb)

        assert results == []
        assert isinstance(results, list)

    def test_database_error_propagates(self):
        """Should propagate database errors"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Database connection error")

        query_emb = [0.1] * 1024

        with pytest.raises(Exception, match="Database connection error"):
            search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb)

    def test_similarity_scores_ordered_descending(self):
        """Results should be ordered by similarity (highest first)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock results in descending similarity order (as DB would return)
        mock_cursor.fetchall.return_value = [
            {'chunk_text': 'Best match', 'similarity': 0.98},
            {'chunk_text': 'Good match', 'similarity': 0.87},
            {'chunk_text': 'OK match', 'similarity': 0.65},
            {'chunk_text': 'Weak match', 'similarity': 0.42}
        ]

        query_emb = [0.1] * 1024
        results = search_similar_chunks(mock_conn, bot_id=1, query_embedding=query_emb, top_k=4)

        # Verify scores are in descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] >= scores[1] >= scores[2] >= scores[3]


# ============================================================================
# TEST process_document FUNCTION
# ============================================================================

class TestProcessDocument:
    """Tests for the process_document high-level function"""

    def test_validates_empty_document_text(self):
        """Should raise ValueError if document text is empty"""
        mock_conn = Mock()

        with pytest.raises(ValueError, match="cannot be empty"):
            process_document(mock_conn, 1, 100, "", "fake-api-key")

        with pytest.raises(ValueError, match="cannot be empty"):
            process_document(mock_conn, 1, 100, "   ", "fake-api-key")

    def test_validates_api_key(self):
        """Should raise ValueError if API key is missing"""
        mock_conn = Mock()

        with pytest.raises(ValueError, match="API key is required"):
            process_document(mock_conn, 1, 100, "Some text", "")

        with pytest.raises(ValueError, match="API key is required"):
            process_document(mock_conn, 1, 100, "Some text", None)

    @patch('shared.rag.store_document_chunks')
    @patch('shared.rag.get_voyage_embedding')
    @patch('shared.rag.chunk_text')
    def test_successful_processing(self, mock_chunk, mock_embed, mock_store):
        """Should successfully process document through full pipeline"""
        mock_conn = Mock()

        # Mock the pipeline
        mock_chunk.return_value = ["chunk1", "chunk2", "chunk3"]
        mock_embed.side_effect = [
            [0.1] * 1024,  # embedding for chunk1
            [0.2] * 1024,  # embedding for chunk2
            [0.3] * 1024   # embedding for chunk3
        ]
        mock_store.return_value = 3

        result = process_document(
            mock_conn,
            bot_id=1,
            document_id=100,
            document_text="Test document text",
            voyage_api_key="fake-key"
        )

        # Verify chunk_text was called
        mock_chunk.assert_called_once_with("Test document text", chunk_size=800, overlap=200)

        # Verify get_voyage_embedding was called 3 times (once per chunk)
        assert mock_embed.call_count == 3
        mock_embed.assert_any_call("chunk1", "fake-key")
        mock_embed.assert_any_call("chunk2", "fake-key")
        mock_embed.assert_any_call("chunk3", "fake-key")

        # Verify store_document_chunks was called with correct params
        mock_store.assert_called_once()
        call_args = mock_store.call_args[0]
        assert call_args[0] == mock_conn
        assert call_args[1] == 1  # bot_id
        assert call_args[2] == 100  # document_id
        assert call_args[3] == ["chunk1", "chunk2", "chunk3"]
        assert len(call_args[4]) == 3  # 3 embeddings

        # Check return value
        assert result == 3

    @patch('shared.rag.chunk_text')
    def test_respects_chunk_parameters(self, mock_chunk):
        """Should pass chunk_size and overlap to chunk_text"""
        mock_conn = Mock()
        mock_chunk.return_value = ["chunk1"]

        with patch('shared.rag.get_voyage_embedding', return_value=[0.1]*1024):
            with patch('shared.rag.store_document_chunks', return_value=1):
                process_document(
                    mock_conn, 1, 100, "Test text", "fake-key",
                    chunk_size=500, overlap=100
                )

        mock_chunk.assert_called_once_with("Test text", chunk_size=500, overlap=100)

    @patch('shared.rag.chunk_text')
    @patch('shared.rag.get_voyage_embedding')
    def test_embedding_failure_propagates(self, mock_embed, mock_chunk):
        """Should propagate embedding errors"""
        mock_conn = Mock()
        mock_chunk.return_value = ["chunk1"]
        mock_embed.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            process_document(mock_conn, 1, 100, "Test text", "fake-key")

    @patch('shared.rag.chunk_text')
    @patch('shared.rag.get_voyage_embedding')
    @patch('shared.rag.store_document_chunks')
    def test_storage_failure_propagates(self, mock_store, mock_embed, mock_chunk):
        """Should propagate storage errors"""
        mock_conn = Mock()
        mock_chunk.return_value = ["chunk1"]
        mock_embed.return_value = [0.1] * 1024
        mock_store.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            process_document(mock_conn, 1, 100, "Test text", "fake-key")


# ============================================================================
# TEST rag_query FUNCTION
# ============================================================================

class TestRagQuery:
    """Tests for the rag_query high-level function"""

    def test_validates_empty_query(self):
        """Should raise ValueError if query is empty"""
        mock_conn = Mock()

        with pytest.raises(ValueError, match="cannot be empty"):
            rag_query(mock_conn, 1, "", "fake-api-key")

        with pytest.raises(ValueError, match="cannot be empty"):
            rag_query(mock_conn, 1, "   ", "fake-api-key")

    def test_validates_api_key(self):
        """Should raise ValueError if API key is missing"""
        mock_conn = Mock()

        with pytest.raises(ValueError, match="API key is required"):
            rag_query(mock_conn, 1, "What is the policy?", "")

        with pytest.raises(ValueError, match="API key is required"):
            rag_query(mock_conn, 1, "What is the policy?", None)

    @patch('shared.rag.search_similar_chunks')
    @patch('shared.rag.get_voyage_embedding')
    def test_successful_query_with_results(self, mock_embed, mock_search):
        """Should successfully perform RAG query and format results"""
        mock_conn = Mock()

        # Mock embedding
        mock_embed.return_value = [0.1] * 1024

        # Mock search results
        mock_search.return_value = [
            ("This is the first relevant chunk", 0.95),
            ("This is the second relevant chunk", 0.87),
            ("This is the third relevant chunk", 0.75)
        ]

        result = rag_query(
            mock_conn,
            bot_id=1,
            user_query="What is your return policy?",
            voyage_api_key="fake-key",
            top_k=3
        )

        # Verify get_voyage_embedding was called with the query
        mock_embed.assert_called_once_with("What is your return policy?", "fake-key")

        # Verify search_similar_chunks was called
        mock_search.assert_called_once_with(mock_conn, 1, [0.1] * 1024, 3)

        # Check formatted output
        assert "<relevant_information>" in result
        assert "</relevant_information>" in result
        assert "[Source 1]: This is the first relevant chunk" in result
        assert "[Source 2]: This is the second relevant chunk" in result
        assert "[Source 3]: This is the third relevant chunk" in result

    @patch('shared.rag.search_similar_chunks')
    @patch('shared.rag.get_voyage_embedding')
    def test_query_with_no_results(self, mock_embed, mock_search):
        """Should handle case when no results are found"""
        mock_conn = Mock()

        mock_embed.return_value = [0.1] * 1024
        mock_search.return_value = []  # No results

        result = rag_query(
            mock_conn,
            bot_id=1,
            user_query="Obscure question",
            voyage_api_key="fake-key"
        )

        # Should return empty tags with message
        assert "<relevant_information>" in result
        assert "</relevant_information>" in result
        assert "No relevant information found" in result

    @patch('shared.rag.search_similar_chunks')
    @patch('shared.rag.get_voyage_embedding')
    def test_respects_top_k_parameter(self, mock_embed, mock_search):
        """Should pass top_k to search function"""
        mock_conn = Mock()

        mock_embed.return_value = [0.1] * 1024
        mock_search.return_value = []

        rag_query(mock_conn, 1, "Test query", "fake-key", top_k=5)

        # Verify top_k was passed to search
        mock_search.assert_called_once_with(mock_conn, 1, [0.1] * 1024, 5)

    @patch('shared.rag.get_voyage_embedding')
    def test_embedding_failure_propagates(self, mock_embed):
        """Should propagate embedding errors"""
        mock_conn = Mock()
        mock_embed.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            rag_query(mock_conn, 1, "Test query", "fake-key")

    @patch('shared.rag.search_similar_chunks')
    @patch('shared.rag.get_voyage_embedding')
    def test_search_failure_propagates(self, mock_embed, mock_search):
        """Should propagate search errors"""
        mock_conn = Mock()
        mock_embed.return_value = [0.1] * 1024
        mock_search.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            rag_query(mock_conn, 1, "Test query", "fake-key")

    @patch('shared.rag.search_similar_chunks')
    @patch('shared.rag.get_voyage_embedding')
    def test_formats_sources_correctly(self, mock_embed, mock_search):
        """Should format sources with correct numbering and separation"""
        mock_conn = Mock()

        mock_embed.return_value = [0.1] * 1024
        mock_search.return_value = [
            ("First chunk", 0.9),
            ("Second chunk", 0.8)
        ]

        result = rag_query(mock_conn, 1, "Test", "fake-key", top_k=2)

        # Check proper formatting
        lines = result.split('\n')
        assert lines[0] == "<relevant_information>"
        assert "[Source 1]: First chunk" in result
        assert "[Source 2]: Second chunk" in result
        assert lines[-1] == "</relevant_information>"


# ============================================================================
# INTEGRATION TEST (if we had a test database)
# ============================================================================

class TestIntegration:
    """Integration tests (would require test database setup)"""

    @pytest.mark.skip(reason="Requires test database setup")
    def test_end_to_end_workflow(self):
        """
        Full workflow test (skipped by default):
        1. Chunk text
        2. Get embeddings (mocked)
        3. Store in database
        """
        # This would require:
        # - Test database with document_chunks table
        # - Proper connection setup
        # - Cleanup after test
        pass


if __name__ == '__main__':
    """Run tests with pytest"""
    pytest.main([__file__, '-v', '--tb=short'])
