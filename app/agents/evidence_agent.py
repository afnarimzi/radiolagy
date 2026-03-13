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

load_dotenv()

PUBMED_SEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

class EvidenceAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"  # Stable GROQ model

    @simple_timer.time_agent("Evidence Agent")
    async def analyze(self, evidence_input: EvidenceInput, save_to_db: bool = True) -> EvidenceFindings:
        """Search PubMed and summarise evidence for diagnosis"""

        # Step 1: extract keywords
        keywords = self._extract_keywords(
            evidence_input.diagnosis,
            evidence_input.radiology_findings
        )

        # Step 2: search PubMed
        pmids = await self._search_pubmed(keywords)

        # Step 3: fetch paper details
        papers = await self._fetch_abstracts(pmids)

        # Step 4: summarise
        summary = self._summarise_evidence(papers, evidence_input.diagnosis)

        # Step 5: build citations
        citations = [Citation(**p) for p in papers]

        findings = EvidenceFindings(
            case_id=evidence_input.case_id,
            patient_code=evidence_input.patient_code,
            search_keywords=keywords,
            evidence_summary=summary,
            citations=citations,
            total_papers_found=len(citations)
        )

        if save_to_db:
            self._save_to_db(evidence_input, findings)

        return findings

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