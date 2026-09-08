import asyncio
import os
import re
import xml.etree.ElementTree as ET
from textwrap import dedent
from typing import Literal

import httpx
from openai import OpenAI
from pydantic import BaseModel, Field

BRAND_NAME = os.getenv("APP_NAME", "LymeWire")
MODEL = os.getenv("MODEL", "gpt-5.5")
NCBI_TOOL_NAME = os.getenv("NCBI_TOOL_NAME", "lymewire")
NCBI_EMAIL = os.getenv("NCBI_EMAIL")
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
CLINICALTRIALS_SEARCH_URL = "https://clinicaltrials.gov/api/v2/studies"

WireId = Literal["ask", "care", "research", "treatment", "guideline", "compare", "trial", "doctorbrief", "calm"]

client: OpenAI | None = None


def openai_client() -> OpenAI:
    global client
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=6000)
    wire: WireId = "ask"
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    profile: dict[str, str] = Field(default_factory=dict)


class AskResponse(BaseModel):
    brand: str
    wire: WireId
    answer: str
    retrieval_notes: list[str] = Field(default_factory=list)
    safety: dict[str, str] = Field(default_factory=dict)


class TimelineDraft(BaseModel):
    symptoms: str = ""
    tests: str = ""
    treatments: str = ""
    questions: str = ""


WIRE_DEFINITIONS = [
    {
        "id": "care",
        "name": "Care Wire",
        "purpose": "Treatment, doctor, hospital and center navigation without fake success-rate claims.",
        "status": "api-enabled",
    },
    {
        "id": "research",
        "name": "Research Wire",
        "purpose": "PubMed search, paper analysis and evidence cards.",
        "status": "retrieval-enabled",
    },
    {
        "id": "treatment",
        "name": "Treatment Wire",
        "purpose": "Treatment-claim benefit, risk and uncertainty review.",
        "status": "retrieval-enabled",
    },
    {
        "id": "guideline",
        "name": "Guideline Wire",
        "purpose": "CDC, NICE, IDSA/AAN/ACR and ILADS summaries and comparisons.",
        "status": "seeded-sources",
    },
    {
        "id": "trial",
        "name": "Trial Wire",
        "purpose": "ClinicalTrials.gov discovery and trial status cards.",
        "status": "retrieval-enabled",
    },
    {
        "id": "doctorbrief",
        "name": "Doctor Brief Wire",
        "purpose": "Clinician-facing appointment summary generation.",
        "status": "api-enabled",
    },
    {
        "id": "calm",
        "name": "Calm Wire",
        "purpose": "Panic-safe, low-alarm support with urgent red-flag screening.",
        "status": "api-enabled",
    },
]


BASE_PROMPT = dedent(
    """
    You are LymeWire, an evidence-aware Lyme disease and tick-borne illness product.
    Answer in the user's language when possible. Be clear, warm, practical and honest about uncertainty.

    Product contract:
    - LymeWire is not an AI doctor.
    - Do not diagnose, prescribe, change medication or replace urgent care.
    - Separate established guidance, limited evidence, hypotheses, anecdotes and unsupported claims.
    - Name evidence type when possible: guideline, systematic review, randomized trial, registry record, case report, animal/in-vitro.
    - Do not rank doctors or claim success rates without objective cited data.
    - Use plain readable output. No Markdown tables.
    - If sources are retrieved, cite PMID or NCT URLs.
    - If sources are not retrieved, say so plainly.
    """
).strip()

WIRE_PROMPTS: dict[str, str] = {
    "ask": "General LymeWire chat. Be concise, useful and safe.",
    "care": dedent(
        """
        Care Wire. Give a route first, caveats second.
        For Turkey/Izmir, use university hospital or training/research hospital Infectious Diseases as first route, with Rheumatology for persistent CRP/joint symptoms, Neurology for brain fog/focal symptoms, Cardiology for palpitations/fainting, Dermatology for rash.
        Mention Ege University and Dokuz Eylul only as starting points to verify, not guaranteed specialists.
        Include a short copy-paste appointment message when useful.
        """
    ).strip(),
    "research": "Research Wire. Use retrieved PubMed records. Separate primary trials, reviews, protocols and weakly related records.",
    "treatment": "Treatment Wire. Review benefit/risk/uncertainty. Do not tell the user to start, stop or change treatment.",
    "guideline": "Guideline Wire. Distinguish official guideline/source pages from PubMed records. Do not invent recommendations.",
    "compare": "Comparison Wire. Compare sources neutrally, but do not create false balance when evidence strength differs.",
    "trial": "Trial Wire. Use retrieved ClinicalTrials.gov records. Registry status does not prove efficacy or eligibility.",
    "doctorbrief": "Doctor Brief Wire. Produce a concise clinician-facing appointment brief from provided timeline/profile/history.",
    "calm": "Calm Wire. Respond warmly first, screen immediate red flags gently, give one grounding action and one practical next step.",
}

GUIDELINE_SEEDS = {
    "cdc": "CDC Lyme clinical care: https://www.cdc.gov/lyme/hcp/clinical-care/index.html\nCDC chronic symptoms/PTLDS: https://www.cdc.gov/lyme/signs-symptoms/chronic-symptoms-and-lyme-disease.html",
    "idsa": "IDSA/AAN/ACR 2020 Lyme guideline: https://www.idsociety.org/practice-guideline/lyme-disease/\nPubMed: https://pubmed.ncbi.nlm.nih.gov/33251700/",
    "nice": "NICE NG95 Lyme disease: https://www.nice.org.uk/guidance/ng95",
    "ilads": "ILADS treatment guidelines: https://www.ilads.org/patient-care/ilads-treatment-guidelines/\nPubMed: https://pubmed.ncbi.nlm.nih.gov/25077519/",
}


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return clean_text("".join(element.itertext()))


def extract_pmids(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"(?i)(?:PMID[:\s#]*|pubmed\.ncbi\.nlm\.nih\.gov/)(\d{6,9})", text)))


def ncbi_params(params: dict[str, str]) -> dict[str, str]:
    enriched = {"tool": NCBI_TOOL_NAME, **params}
    if NCBI_EMAIL:
        enriched["email"] = NCBI_EMAIL
    return enriched


async def pubmed_search(query: str, limit: int = 6) -> list[str]:
    params = ncbi_params({"db": "pubmed", "term": query, "retmode": "json", "retmax": str(limit), "sort": "relevance"})
    async with httpx.AsyncClient(timeout=20) as http:
        response = await http.get(PUBMED_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


async def pubmed_fetch(pmids: list[str]) -> list[dict[str, str]]:
    if not pmids:
        return []
    params = ncbi_params({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "rettype": "abstract"})
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.get(PUBMED_FETCH_URL, params=params)
        response.raise_for_status()
    root = ET.fromstring(response.text)
    records = []
    for item in root.findall(".//PubmedArticle"):
        pmid = clean_text(item.findtext("./MedlineCitation/PMID"))
        title = element_text(item.find("./MedlineCitation/Article/ArticleTitle"))
        journal = clean_text(item.findtext("./MedlineCitation/Article/Journal/Title"))
        year = clean_text(item.findtext(".//PubDate/Year")) or "Unknown year"
        abstract = " ".join(element_text(part) for part in item.findall(".//Abstract/AbstractText")).strip()
        records.append(
            {
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "year": year,
                "abstract": abstract[:1400],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return records


def format_pubmed(records: list[dict[str, str]]) -> str:
    if not records:
        return "No PubMed records were retrieved."
    return "\n\n".join(
        f"[{idx}] PMID: {record['pmid']}\nTitle: {record['title']}\nJournal/year: {record['journal']} / {record['year']}\nURL: {record['url']}\nAbstract: {record['abstract'] or 'No abstract available.'}"
        for idx, record in enumerate(records, 1)
    )


def public_research_query(question: str, wire: WireId) -> str:
    lowered = question.lower()
    if "ptlds" in lowered or "post-treatment" in lowered or "post treatment" in lowered:
        base = '("post-treatment Lyme disease" OR PTLDS OR "post Lyme disease")'
    elif "babesia" in lowered or "babesiosis" in lowered:
        base = '"babesiosis"'
    elif "bartonella" in lowered:
        base = '"Bartonella"'
    else:
        base = '"Lyme disease"'

    qualifiers = []
    if wire == "treatment" or re.search(r"\b(treatment|tedavi|antibiotic|antibiyotik)\b", lowered):
        qualifiers.append("treatment")
    if re.search(r"\b(randomized|randomize|rct)\b", lowered):
        qualifiers.append('"randomized controlled trial"[Publication Type]')
    if wire == "guideline":
        qualifiers.append("(guideline[Publication Type] OR practice guideline[Publication Type] OR review[Publication Type])")
    return " AND ".join([base, *qualifiers])


async def build_pubmed_context(question: str, wire: WireId) -> tuple[str, list[str]]:
    pmids = extract_pmids(question)
    notes = []
    if pmids:
        notes.append(f"Detected PMID(s): {', '.join(pmids)}")
    else:
        queries = [public_research_query(question, wire)]
        lowered = question.lower()
        if "ptlds" in lowered and re.search(r"\b(randomized|randomize|rct)\b", lowered):
            queries.extend(
                [
                    '"Randomized Trial of Longer-Term Therapy for Symptoms Attributed to Lyme Disease"[Title]',
                    '("post-treatment Lyme disease" OR PTLDS) AND (yoga OR rehabilitation OR exercise OR psychotherapy) AND "randomized controlled trial"[Publication Type]',
                ]
            )
        id_lists = await asyncio.gather(*(pubmed_search(query, limit=6) for query in queries))
        pmids = []
        seen = set()
        for id_list in id_lists:
            for pmid in id_list:
                if pmid not in seen:
                    seen.add(pmid)
                    pmids.append(pmid)
        notes.extend(f"PubMed query {idx}: {query}" for idx, query in enumerate(queries, 1))
        notes.append(f"Unique PMID(s): {', '.join(pmids[:10]) if pmids else 'none'}")
    return format_pubmed(await pubmed_fetch(pmids[:10])), notes


async def clinicaltrials_search(query: str, limit: int = 5) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.get(CLINICALTRIALS_SEARCH_URL, params={"format": "json", "query.term": query, "pageSize": str(limit)})
        response.raise_for_status()
        data = response.json()
    return data.get("studies", [])


def format_trials(studies: list[dict]) -> str:
    if not studies:
        return "No ClinicalTrials.gov study records were retrieved."
    blocks = []
    for idx, study in enumerate(studies, 1):
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        conditions = protocol.get("conditionsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        nct = ident.get("nctId", "")
        interventions = ", ".join(item.get("name", "") for item in arms.get("interventions", []) if item.get("name"))
        blocks.append(
            f"[{idx}] NCT ID: {nct}\nTitle: {ident.get('briefTitle') or ident.get('officialTitle')}\nURL: https://clinicaltrials.gov/study/{nct}\nStatus: {status.get('overallStatus')}\nStudy type: {design.get('studyType')}\nPhase(s): {', '.join(design.get('phases') or []) or 'Not listed'}\nConditions: {', '.join(conditions.get('conditions') or [])}\nInterventions: {interventions or 'Not listed'}"
        )
    return "\n\n".join(blocks)


def history_block(history: list[ChatMessage]) -> str:
    if not history:
        return "No recent app history provided."
    return "\n".join(f"{item.role}: {item.content[:1200]}" for item in history[-10:])


def profile_block(profile: dict[str, str]) -> str:
    allowed = {key: value for key, value in profile.items() if key in {"location", "language", "goals", "known_context"} and value}
    if not allowed:
        return "No user profile context provided."
    return "\n".join(f"{key}: {value[:1000]}" for key, value in allowed.items())


def build_doctor_brief(timeline: TimelineDraft) -> str:
    return dedent(
        f"""
        LymeWire doctor brief draft

        Main symptoms: {timeline.symptoms or "Not entered yet."}
        Tests / objective findings: {timeline.tests or "Not entered yet."}
        Treatments tried: {timeline.treatments or "Not entered yet."}
        Questions for clinician: {timeline.questions or "Not entered yet."}

        Request: Please reassess active Lyme/tick-borne infection, PTLDS/persistent symptoms, coinfections, inflammatory/autoimmune causes, neurologic causes, medication effects, sleep/dysautonomia contributors, and other plausible explanations.
        """
    ).strip()


async def answer_product(request: AskRequest) -> AskResponse:
    wire_prompt = WIRE_PROMPTS.get(request.wire, WIRE_PROMPTS["ask"])
    retrieval_context = "No external retrieval was used for this answer."
    notes: list[str] = []

    try:
        if request.wire in {"research", "treatment"}:
            retrieval_context, notes = await build_pubmed_context(request.question, request.wire)
        elif request.wire == "guideline":
            seed = "\n\n".join(value for key, value in GUIDELINE_SEEDS.items() if key in request.question.lower())
            retrieval_context, notes = await build_pubmed_context(request.question, request.wire)
            if seed:
                retrieval_context = seed + "\n\n" + retrieval_context
                notes.insert(0, "Matched seeded official guideline source(s).")
        elif request.wire == "compare":
            seed = "\n\n".join(value for key, value in GUIDELINE_SEEDS.items() if key in request.question.lower())
            retrieval_context, notes = await build_pubmed_context(request.question, request.wire)
            if seed:
                retrieval_context = seed + "\n\n" + retrieval_context
                notes.insert(0, "Matched seeded comparison source(s).")
        elif request.wire == "trial":
            query = request.question or "Lyme Disease"
            studies = await clinicaltrials_search(query)
            retrieval_context = format_trials(studies)
            notes = [f"ClinicalTrials.gov query: {query}", f"Retrieved trial record count: {len(studies)}"]
    except Exception as exc:
        retrieval_context = f"Retrieval failed: {type(exc).__name__}. Do not pretend sources were retrieved."
        notes.append("Retrieval failed; answer should be cautious and uncited.")

    system_prompt = f"{BASE_PROMPT}\n\n{wire_prompt}"
    user_prompt = dedent(
        f"""
        Wire: {request.wire}

        Recent app history:
        {history_block(request.history)}

        User profile context:
        {profile_block(request.profile)}

        Retrieved source context:
        {retrieval_context}

        User question:
        {request.question}

        Answer now as the LymeWire product interface. Keep it compact and useful.
        """
    ).strip()

    response = openai_client().responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return AskResponse(
        brand=BRAND_NAME,
        wire=request.wire,
        answer=response.output_text.strip(),
        retrieval_notes=notes,
        safety={"medical_boundary": "no diagnosis, prescribing or medication changes"},
    )


def timeline_schema() -> dict:
    return {
        "brand": BRAND_NAME,
        "storage": "local-first",
        "fields": [
            {"id": "symptoms", "label": "Dominant symptoms", "type": "long_text"},
            {"id": "tests", "label": "Tests and objective findings", "type": "long_text"},
            {"id": "treatments", "label": "Treatments tried", "type": "long_text"},
            {"id": "questions", "label": "Questions for clinician", "type": "long_text"},
        ],
        "privacy": "Do not sync medical records until account, consent, encryption and deletion/export flows exist.",
    }
