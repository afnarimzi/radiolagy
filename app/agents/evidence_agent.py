"""
Evidence Agent - To be implemented
"""

# TODO: Implement Evidence Agent for literature search and research
"""
Evidence Validation Agent - PubMed RAG pipeline
Enhanced with performance tracking
"""
import os
import json
import time
import aiohttp
import asyncio
from groq import Groq
from dotenv import load_dotenv

from app.database.database import get_db
from app.database.crud import RadiologyDB
from app.models.evidence_models import EvidenceInput, EvidenceFindings, Citation
from app.utils.simple_timer import simple_timer
from app.utils.biomedbert_helper import biomedbert

load_dotenv()

PUBMED_SEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

class EvidenceAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"  # Higher TPM limits

    @simple_timer.time_agent("Evidence Agent")
    async def analyze(self, evidence_input: EvidenceInput, save_to_db: bool = True) -> EvidenceFindings:
        """Search PubMed and summarise evidence for diagnosis"""

        # Step 1: build enhanced search query using BiomedBERT
        expanded_query = self._build_search_query(
            evidence_input.diagnosis,
            evidence_input.radiology_findings
        )

        # Step 2: search PubMed
        pmids = await self._search_pubmed(expanded_query)

        # Step 3: fetch paper details
        papers = await self._fetch_abstracts(pmids)
        
        # Step 3.5: Re-rank papers using BiomedBERT semantic similarity
        # Use simple join of diagnosis terms as the original query for similarity
        base_query = " ".join(evidence_input.diagnosis[:2]) if evidence_input.diagnosis else "medical case"
        papers = biomedbert.rerank_papers(base_query, papers)
        print(f"✅ Re-ranked {len(papers)} papers by semantic similarity")

        # Step 4: summarise
        summary = self._summarise_evidence(papers, evidence_input.diagnosis)

        # Step 5: build citations
        citations = [Citation(**p) for p in papers]

        findings = EvidenceFindings(
            case_id=evidence_input.case_id,
            patient_code=evidence_input.patient_code,
            search_keywords=f"{expanded_query} [BiomedBERT enhanced]",
            evidence_summary=summary,
            citations=citations,
            total_papers_found=len(citations)
        )

        if save_to_db:
            self._save_to_db(evidence_input, findings)

        return findings

    def _build_search_query(
        self, 
        diagnosis: list, 
        radiology_findings: str
    ) -> str:
        """Build enhanced search query using BiomedBERT"""
        # Original keyword query
        if isinstance(diagnosis, list):
            base_query = " ".join(diagnosis[:2])
        else:
            base_query = str(diagnosis)
        
        # Add radiology context
        if radiology_findings:
            # Extract key terms from findings
            key_terms = []
            medical_terms = [
                "pleural effusion", "pneumothorax", 
                "cardiomegaly", "consolidation",
                "atelectasis", "pulmonary edema",
                "pneumonia", "mass", "nodule",
                "interstitial", "fibrosis"
            ]
            findings_lower = radiology_findings.lower()
            for term in medical_terms:
                if term in findings_lower:
                    key_terms.append(term)
            
            if key_terms:
                base_query = f"{base_query} {' '.join(key_terms[:2])}"
        
        # Expand with BiomedBERT synonyms
        expanded_query = biomedbert.expand_query(base_query)
        print(f"🔬 BiomedBERT expanded query: {expanded_query}")
        
        return expanded_query

    def _extract_keywords(self, diagnosis: list, findings: str) -> str:
        primary = diagnosis[0] if diagnosis else "unknown"
        prompt = f"""Extract the most relevant PubMed search keywords.
Diagnosis: {primary}
Findings: {findings}
Return ONLY a short search string (max 6 words). Nothing else."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()

    async def _search_pubmed(self, query: str, max_results: int = 5) -> list:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(PUBMED_SEARCH_URL, params=params) as response:
                data = await response.json()
                return data.get("esearchresult", {}).get("idlist", [])

    async def _fetch_abstracts(self, pmids: list) -> list:
        if not pmids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(PUBMED_SUMMARY_URL, params=params) as response:
                data = await response.json()
                papers = []
                for pmid in pmids:
                    try:
                        article = data["result"][pmid]
                        papers.append({
                            "pmid": pmid,
                            "title": article.get("title", "No title"),
                            "authors": [a["name"] for a in article.get("authors", [])[:3]],
                            "journal": article.get("fulljournalname", ""),
                            "year": article.get("pubdate", ""),
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        })
                    except Exception:
                        continue
                return papers

    def _summarise_evidence(self, papers: list, diagnosis: list) -> str:
        if not papers:
            return "No relevant papers found on PubMed for this diagnosis."
        primary = diagnosis[0] if diagnosis else "unknown"
        papers_text = "\n\n".join([
            f"Title: {p['title']}\nJournal: {p['journal']} ({p['year']})"
            for p in papers
        ])
        prompt = f"""You are a medical evidence analyst.
Diagnosis: {primary}
PubMed papers:
{papers_text}
Write a brief evidence summary (3-5 sentences). Be factual and clinical. Return only the summary."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def _save_to_db(self, evidence_input: EvidenceInput, findings: EvidenceFindings):
        import time
        start_time = time.time()
        db = next(get_db())
        try:
            radiology_db = RadiologyDB(db)
            radiology_db.save_agent_output(
                case_id=evidence_input.case_id,
                agent_type="evidence",
                output_data={
                    "search_keywords": findings.search_keywords,
                    "evidence_summary": findings.evidence_summary,
                    "citations": [c.dict() for c in findings.citations],
                    "total_papers_found": findings.total_papers_found
                },
                confidence=1.0,
                processing_time=round(time.time() - start_time, 2)
            )
        finally:
            db.close()