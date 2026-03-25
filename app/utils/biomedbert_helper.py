"""
BiomedBERT Semantic Search Helper
Enhances PubMed search with medical embeddings
"""
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

MODEL_NAME = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"

class BiomedBERTHelper:
    _instance = None  # singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        print("Loading BiomedBERT model...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME)
        self.model.eval()
        self._initialized = True
        print("✅ BiomedBERT loaded!")
    
    def get_embedding(self, text: str) -> torch.Tensor:
        """Convert medical text to embedding vector"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)
    
    def cosine_similarity(
        self, a: torch.Tensor, b: torch.Tensor
    ) -> float:
        """Calculate similarity between embeddings"""
        return torch.nn.functional.cosine_similarity(
            a, b
        ).item()
    
    def expand_query(self, query: str) -> str:
        """Expand medical query with synonyms"""
        medical_synonyms = {
            "pleural effusion": 
                "pleural effusion OR thoracic fluid OR hydrothorax",
            "pneumonia": 
                "pneumonia OR consolidation OR pulmonary infection",
            "cardiomegaly": 
                "cardiomegaly OR enlarged heart OR cardiac enlargement",
            "pneumothorax": 
                "pneumothorax OR collapsed lung",
            "atelectasis": 
                "atelectasis OR lung collapse",
            "pulmonary edema": 
                "pulmonary edema OR lung edema OR pulmonary congestion",
            "congestive heart failure": 
                "congestive heart failure OR CHF OR cardiac failure",
            "interstitial lung disease": 
                "interstitial lung disease OR ILD OR pulmonary fibrosis",
            "mass nodule": 
                "pulmonary nodule OR lung mass OR solitary nodule",
            "consolidation": 
                "consolidation OR airspace opacity OR lobar consolidation"
        }
        lower_query = query.lower()
        for key, expansion in medical_synonyms.items():
            if key in lower_query:
                return expansion
        return query
    
    def rerank_papers(
        self, 
        query: str, 
        papers: List[dict]
    ) -> List[dict]:
        """Re-rank papers by semantic similarity to query"""
        if not papers:
            return papers
        
        try:
            query_embedding = self.get_embedding(query)
            scored_papers = []
            
            for paper in papers:
                # Combine title and abstract for scoring
                paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                paper_embedding = self.get_embedding(
                    paper_text[:512]
                )
                score = self.cosine_similarity(
                    query_embedding, paper_embedding
                )
                scored_papers.append((score, paper))
            
            # Sort by similarity score
            scored_papers.sort(key=lambda x: x[0], reverse=True)
            return [paper for _, paper in scored_papers]
        
        except Exception as e:
            print(f"Re-ranking failed: {e}, using original order")
            return papers


# Global singleton instance
biomedbert = BiomedBERTHelper()
