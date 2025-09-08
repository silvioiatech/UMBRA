"""
RAG Manager - Knowledge base ingestion and citation-based content generation
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from ...storage.r2_client import R2Client
from .model_provider_enhanced import EnhancedModelProviderManager
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Document for knowledge base"""
    id: str
    title: str
    content: str
    url: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    ingested_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow()

@dataclass
class Citation:
    """Citation for generated content"""
    doc_id: str
    title: str
    url: Optional[str]
    excerpt: str
    relevance_score: float

@dataclass
class RAGResult:
    """RAG generation result with citations"""
    text: str
    citations: List[Citation]
    confidence_score: float
    metadata: Dict[str, Any]

class RAGManager:
    """Retrieval Augmented Generation manager"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig, r2_client: Optional[R2Client] = None):
        self.ai_agent = ai_agent
        self.config = config
        self.r2_client = r2_client
        self.provider_manager = EnhancedModelProviderManager(config)
        
        # RAG settings
        self.bucket_name = config.get("R2_BUCKET", "umbra")
        self.kb_prefix = "creator/knowledge_base"
        self.max_documents = config.get("CREATOR_MAX_KB_DOCUMENTS", 1000)
        self.max_doc_size = config.get("CREATOR_MAX_DOC_SIZE_KB", 500) * 1024
        self.chunk_size = config.get("CREATOR_CHUNK_SIZE", 1000)
        self.overlap_size = config.get("CREATOR_CHUNK_OVERLAP", 200)
        
        # In-memory document store (in production, would use vector database)
        self.documents = {}
        self.document_chunks = {}
        self.knowledge_bases = {}
        
        logger.info("RAG manager initialized")
    
    async def ingest_documents(self, docs: List[Union[str, Dict[str, Any]]], 
                             tags: List[str] = None) -> str:
        """Ingest documents into knowledge base"""
        try:
            if len(docs) > self.max_documents:
                raise ContentError(f"Too many documents: {len(docs)} > {self.max_documents}", "rag_ingest")
            
            kb_id = self._generate_kb_id()
            ingested_docs = []
            
            for i, doc in enumerate(docs):
                try:
                    document = await self._process_document(doc, tags or [])
                    
                    # Check document size
                    if len(document.content.encode('utf-8')) > self.max_doc_size:
                        logger.warning(f"Document {i} exceeds size limit, truncating")
                        document.content = document.content[:self.max_doc_size]
                    
                    # Create chunks for better retrieval
                    chunks = self._create_document_chunks(document)
                    
                    # Store document and chunks
                    self.documents[document.id] = document
                    self.document_chunks[document.id] = chunks
                    ingested_docs.append(document)
                    
                except Exception as e:
                    logger.warning(f"Failed to process document {i}: {e}")
                    continue
            
            # Create knowledge base
            self.knowledge_bases[kb_id] = {
                "id": kb_id,
                "documents": [doc.id for doc in ingested_docs],
                "tags": tags or [],
                "created_at": datetime.utcnow(),
                "document_count": len(ingested_docs)
            }
            
            # Save to storage if available
            if self.r2_client:
                await self._save_knowledge_base(kb_id)
            
            logger.info(f"Ingested {len(ingested_docs)} documents into KB {kb_id}")
            return kb_id
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            raise ContentError(f"Document ingestion failed: {e}", "rag_ingest")
    
    async def generate_with_citations(self, brief: str, cite: bool = True, 
                                    kb_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate content with RAG and citations"""
        try:
            # Get text provider
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available for RAG generation", "rag_generate")
            
            # Retrieve relevant documents
            relevant_docs = await self._retrieve_relevant_documents(brief, kb_id)
            
            if not relevant_docs:
                # Generate without RAG
                result = await provider.generate_text(brief, max_tokens=1000)
                if not result.success:
                    raise ContentError(f"Text generation failed: {result.error}", "rag_generate")
                
                return {
                    "text": result.data,
                    "citations": [],
                    "confidence_score": 0.5,
                    "metadata": {
                        "rag_used": False,
                        "source_documents": 0
                    }
                }
            
            # Create enhanced prompt with context
            enhanced_prompt = await self._create_rag_prompt(brief, relevant_docs, cite)
            
            # Generate content
            result = await provider.generate_text(enhanced_prompt, max_tokens=1500, temperature=0.3)
            if not result.success:
                raise ContentError(f"RAG generation failed: {result.error}", "rag_generate")
            
            # Extract citations from generated text
            citations = await self._extract_citations(result.data, relevant_docs) if cite else []
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(relevant_docs, citations)
            
            return {
                "text": result.data,
                "citations": [self._citation_to_dict(c) for c in citations],
                "confidence_score": confidence_score,
                "metadata": {
                    "rag_used": True,
                    "source_documents": len(relevant_docs),
                    "citation_count": len(citations)
                }
            }
            
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            raise ContentError(f"RAG generation failed: {e}", "rag_generate")
    
    async def _process_document(self, doc: Union[str, Dict[str, Any]], tags: List[str]) -> Document:
        """Process document into standard format"""
        if isinstance(doc, str):
            # URL or file path
            if doc.startswith(("http://", "https://")):
                return await self._process_url_document(doc, tags)
            else:
                # Treat as content
                doc_id = self._generate_doc_id(doc)
                return Document(
                    id=doc_id,
                    title=f"Document {doc_id[:8]}",
                    content=doc,
                    tags=tags
                )
        
        elif isinstance(doc, dict):
            # Structured document
            content = doc.get("content", "")
            if not content and "file" in doc:
                content = await self._read_file_content(doc["file"])
            
            doc_id = doc.get("id") or self._generate_doc_id(content)
            
            return Document(
                id=doc_id,
                title=doc.get("title", f"Document {doc_id[:8]}"),
                content=content,
                url=doc.get("url"),
                tags=tags + doc.get("tags", []),
                metadata=doc.get("metadata", {})
            )
        
        else:
            raise ContentError(f"Unsupported document format: {type(doc)}", "document_processing")
    
    async def _process_url_document(self, url: str, tags: List[str]) -> Document:
        """Process document from URL"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Extract text content from HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup([\"script\", \"style\"]):\n                        script.decompose()\n                    \n                    # Get title\n                    title = soup.title.string if soup.title else url\n                    \n                    # Extract text content\n                    content = soup.get_text()\n                    \n                    # Clean up whitespace\n                    content = '\\n'.join(line.strip() for line in content.splitlines() if line.strip())\n                    \n                    doc_id = self._generate_doc_id(url)\n                    \n                    return Document(\n                        id=doc_id,\n                        title=title.strip(),\n                        content=content,\n                        url=url,\n                        tags=tags,\n                        metadata={\"source_type\": \"web\"}\n                    )\n                else:\n                    raise ContentError(f\"Failed to fetch URL {url}: {response.status_code}\", \"url_fetch\")\n                    \n        except Exception as e:\n            logger.error(f\"Failed to process URL document {url}: {e}\")\n            raise ContentError(f\"Failed to process URL document: {e}\", \"url_processing\")\n    \n    async def _read_file_content(self, file_path: str) -> str:\n        \"\"\"Read content from file\"\"\"\n        try:\n            # In a real implementation, this would handle various file types\n            # For now, assume text files\n            with open(file_path, 'r', encoding='utf-8') as f:\n                return f.read()\n        except Exception as e:\n            raise ContentError(f\"Failed to read file {file_path}: {e}\", \"file_reading\")\n    \n    def _create_document_chunks(self, document: Document) -> List[Dict[str, Any]]:\n        \"\"\"Create overlapping chunks from document\"\"\"\n        chunks = []\n        content = document.content\n        \n        # Simple word-based chunking\n        words = content.split()\n        \n        for i in range(0, len(words), self.chunk_size - self.overlap_size):\n            chunk_words = words[i:i + self.chunk_size]\n            chunk_text = ' '.join(chunk_words)\n            \n            chunk = {\n                \"id\": f\"{document.id}_{len(chunks)}\",\n                \"doc_id\": document.id,\n                \"content\": chunk_text,\n                \"start_word\": i,\n                \"end_word\": i + len(chunk_words),\n                \"metadata\": {\n                    \"title\": document.title,\n                    \"url\": document.url,\n                    \"tags\": document.tags\n                }\n            }\n            \n            chunks.append(chunk)\n            \n            if i + self.chunk_size >= len(words):\n                break\n        \n        return chunks\n    \n    async def _retrieve_relevant_documents(self, query: str, kb_id: Optional[str] = None) -> List[Dict[str, Any]]:\n        \"\"\"Retrieve relevant document chunks for query\"\"\"\n        relevant_chunks = []\n        \n        # Get documents to search\n        if kb_id and kb_id in self.knowledge_bases:\n            doc_ids = self.knowledge_bases[kb_id][\"documents\"]\n        else:\n            doc_ids = list(self.document_chunks.keys())\n        \n        # Simple keyword-based retrieval (in production, would use vector search)\n        query_words = set(query.lower().split())\n        \n        for doc_id in doc_ids:\n            if doc_id not in self.document_chunks:\n                continue\n                \n            chunks = self.document_chunks[doc_id]\n            \n            for chunk in chunks:\n                # Calculate relevance score\n                chunk_words = set(chunk[\"content\"].lower().split())\n                overlap = len(query_words.intersection(chunk_words))\n                relevance_score = overlap / len(query_words) if query_words else 0\n                \n                if relevance_score > 0.1:  # Minimum relevance threshold\n                    chunk[\"relevance_score\"] = relevance_score\n                    relevant_chunks.append(chunk)\n        \n        # Sort by relevance and return top chunks\n        relevant_chunks.sort(key=lambda x: x[\"relevance_score\"], reverse=True)\n        return relevant_chunks[:5]  # Top 5 most relevant chunks\n    \n    async def _create_rag_prompt(self, brief: str, relevant_docs: List[Dict[str, Any]], cite: bool) -> str:\n        \"\"\"Create enhanced prompt with retrieved context\"\"\"\n        context_parts = []\n        \n        for i, doc in enumerate(relevant_docs[:3]):  # Use top 3 documents\n            title = doc[\"metadata\"].get(\"title\", f\"Document {i+1}\")\n            content = doc[\"content\"][:500]  # Limit content length\n            context_parts.append(f\"Source {i+1} - {title}:\\n{content}\")\n        \n        context = \"\\n\\n\".join(context_parts)\n        \n        if cite:\n            citation_instruction = \"\"\"When referencing information from the sources, include citations in the format [Source X] where X is the source number.\"\"\"\n        else:\n            citation_instruction = \"\"\n        \n        prompt = f\"\"\"Based on the following sources, {brief}\n\nSources:\n{context}\n\n{citation_instruction}\n\nResponse:\"\"\"\n        \n        return prompt\n    \n    async def _extract_citations(self, generated_text: str, relevant_docs: List[Dict[str, Any]]) -> List[Citation]:\n        \"\"\"Extract citations from generated text\"\"\"\n        import re\n        \n        citations = []\n        \n        # Find citation patterns like [Source 1], [Source 2], etc.\n        citation_pattern = r'\\[Source (\\d+)\\]'\n        matches = re.findall(citation_pattern, generated_text)\n        \n        for match in matches:\n            source_num = int(match) - 1  # Convert to 0-based index\n            \n            if source_num < len(relevant_docs):\n                doc = relevant_docs[source_num]\n                doc_id = doc[\"doc_id\"]\n                \n                if doc_id in self.documents:\n                    original_doc = self.documents[doc_id]\n                    \n                    citation = Citation(\n                        doc_id=doc_id,\n                        title=original_doc.title,\n                        url=original_doc.url,\n                        excerpt=doc[\"content\"][:200] + \"...\",\n                        relevance_score=doc.get(\"relevance_score\", 0.0)\n                    )\n                    \n                    citations.append(citation)\n        \n        return citations\n    \n    def _calculate_confidence_score(self, relevant_docs: List[Dict[str, Any]], citations: List[Citation]) -> float:\n        \"\"\"Calculate confidence score for generated content\"\"\"\n        if not relevant_docs:\n            return 0.3  # Low confidence without sources\n        \n        # Base score from document relevance\n        avg_relevance = sum(doc.get(\"relevance_score\", 0) for doc in relevant_docs) / len(relevant_docs)\n        \n        # Boost for citations\n        citation_boost = min(len(citations) * 0.1, 0.3)\n        \n        # Document count factor\n        doc_count_factor = min(len(relevant_docs) * 0.05, 0.2)\n        \n        confidence = avg_relevance + citation_boost + doc_count_factor\n        return min(confidence, 1.0)\n    \n    def _citation_to_dict(self, citation: Citation) -> Dict[str, Any]:\n        \"\"\"Convert citation to dictionary\"\"\"\n        return {\n            \"doc_id\": citation.doc_id,\n            \"title\": citation.title,\n            \"url\": citation.url,\n            \"excerpt\": citation.excerpt,\n            \"relevance_score\": citation.relevance_score\n        }\n    \n    def _generate_kb_id(self) -> str:\n        \"\"\"Generate unique knowledge base ID\"\"\"\n        timestamp = datetime.utcnow().strftime(\"%Y%m%d_%H%M%S\")\n        random_part = hashlib.md5(f\"{timestamp}_{id(self)}\".encode()).hexdigest()[:8]\n        return f\"kb_{timestamp}_{random_part}\"\n    \n    def _generate_doc_id(self, content: str) -> str:\n        \"\"\"Generate document ID from content\"\"\"\n        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]\n    \n    async def _save_knowledge_base(self, kb_id: str):\n        \"\"\"Save knowledge base to storage\"\"\"\n        if not self.r2_client:\n            return\n        \n        try:\n            kb_data = {\n                \"knowledge_base\": self.knowledge_bases[kb_id],\n                \"documents\": {doc_id: {\n                    \"id\": doc.id,\n                    \"title\": doc.title,\n                    \"content\": doc.content,\n                    \"url\": doc.url,\n                    \"tags\": doc.tags,\n                    \"metadata\": doc.metadata,\n                    \"ingested_at\": doc.ingested_at.isoformat()\n                } for doc_id in self.knowledge_bases[kb_id][\"documents\"] if doc_id in self.documents},\n                \"chunks\": {doc_id: chunks for doc_id, chunks in self.document_chunks.items() \n                          if doc_id in self.knowledge_bases[kb_id][\"documents\"]}\n            }\n            \n            kb_key = f\"{self.kb_prefix}/{kb_id}.json\"\n            \n            await self.r2_client.put_object(\n                bucket=self.bucket_name,\n                key=kb_key,\n                data=json.dumps(kb_data, indent=2).encode('utf-8'),\n                content_type=\"application/json\",\n                metadata={\n                    \"creator\": \"umbra-rag\",\n                    \"kb_id\": kb_id,\n                    \"document_count\": str(len(self.knowledge_bases[kb_id][\"documents\"])),\n                    \"created_at\": datetime.utcnow().isoformat()\n                }\n            )\n            \n            logger.info(f\"Saved knowledge base {kb_id} to storage\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to save knowledge base {kb_id}: {e}\")\n    \n    async def load_knowledge_base(self, kb_id: str) -> bool:\n        \"\"\"Load knowledge base from storage\"\"\"\n        if not self.r2_client:\n            return False\n        \n        try:\n            kb_key = f\"{self.kb_prefix}/{kb_id}.json\"\n            \n            data = await self.r2_client.get_object(self.bucket_name, kb_key)\n            if not data:\n                return False\n            \n            kb_data = json.loads(data.decode('utf-8'))\n            \n            # Restore knowledge base\n            self.knowledge_bases[kb_id] = kb_data[\"knowledge_base\"]\n            \n            # Restore documents\n            for doc_id, doc_data in kb_data[\"documents\"].items():\n                self.documents[doc_id] = Document(\n                    id=doc_data[\"id\"],\n                    title=doc_data[\"title\"],\n                    content=doc_data[\"content\"],\n                    url=doc_data[\"url\"],\n                    tags=doc_data[\"tags\"],\n                    metadata=doc_data[\"metadata\"],\n                    ingested_at=datetime.fromisoformat(doc_data[\"ingested_at\"])\n                )\n            \n            # Restore chunks\n            self.document_chunks.update(kb_data[\"chunks\"])\n            \n            logger.info(f\"Loaded knowledge base {kb_id} from storage\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"Failed to load knowledge base {kb_id}: {e}\")\n            return False\n    \n    def list_knowledge_bases(self) -> List[Dict[str, Any]]:\n        \"\"\"List all available knowledge bases\"\"\"\n        return [\n            {\n                \"id\": kb_id,\n                \"document_count\": kb[\"document_count\"],\n                \"tags\": kb[\"tags\"],\n                \"created_at\": kb[\"created_at\"].isoformat()\n            }\n            for kb_id, kb in self.knowledge_bases.items()\n        ]\n    \n    def get_knowledge_base_info(self, kb_id: str) -> Optional[Dict[str, Any]]:\n        \"\"\"Get information about a specific knowledge base\"\"\"\n        if kb_id not in self.knowledge_bases:\n            return None\n        \n        kb = self.knowledge_bases[kb_id]\n        documents = [self.documents[doc_id] for doc_id in kb[\"documents\"] if doc_id in self.documents]\n        \n        return {\n            \"id\": kb_id,\n            \"document_count\": len(documents),\n            \"tags\": kb[\"tags\"],\n            \"created_at\": kb[\"created_at\"].isoformat(),\n            \"documents\": [\n                {\n                    \"id\": doc.id,\n                    \"title\": doc.title,\n                    \"url\": doc.url,\n                    \"tags\": doc.tags,\n                    \"content_length\": len(doc.content),\n                    \"ingested_at\": doc.ingested_at.isoformat()\n                }\n                for doc in documents\n            ]\n        }\n    \n    async def search_documents(self, query: str, kb_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:\n        \"\"\"Search documents in knowledge base\"\"\"\n        relevant_chunks = await self._retrieve_relevant_documents(query, kb_id)\n        \n        # Group by document and return top results\n        doc_results = {}\n        \n        for chunk in relevant_chunks[:limit]:\n            doc_id = chunk[\"doc_id\"]\n            \n            if doc_id not in doc_results or chunk[\"relevance_score\"] > doc_results[doc_id][\"relevance_score\"]:\n                doc_results[doc_id] = {\n                    \"doc_id\": doc_id,\n                    \"title\": chunk[\"metadata\"].get(\"title\", \"Unknown\"),\n                    \"url\": chunk[\"metadata\"].get(\"url\"),\n                    \"excerpt\": chunk[\"content\"][:200] + \"...\",\n                    \"relevance_score\": chunk[\"relevance_score\"],\n                    \"tags\": chunk[\"metadata\"].get(\"tags\", [])\n                }\n        \n        return list(doc_results.values())"
