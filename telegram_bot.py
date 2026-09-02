import logging
import os
import re
import xml.etree.ElementTree as ET
from textwrap import dedent

import httpx
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger("lymewire.telegram")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-5.5")
APP_NAME = os.getenv("APP_NAME", "Lymewire")
NCBI_TOOL_NAME = os.getenv("NCBI_TOOL_NAME", "lymewire")
NCBI_EMAIL = os.getenv("NCBI_EMAIL")
MAX_TELEGRAM_MESSAGE = 3900
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
CLINICALTRIALS_SEARCH_URL = "https://clinicaltrials.gov/api/v2/studies"

KNOWN_GUIDELINE_COMPARISONS = [
    {
        "name": "IDSA/AAN/ACR 2020 vs ILADS 2014 Lyme guidelines",
        "match_terms": ("idsa", "ilads", "lyme"),
        "pmids": ["33251700", "25077519", "38606630", "32457042"],
        "context": dedent(
            """
            Known guideline comparison seed:
            - IDSA/AAN/ACR 2020 Lyme disease guideline official page: https://www.idsociety.org/practice-guideline/lyme-disease/
            - IDSA/AAN/ACR 2020 guideline PubMed record: https://pubmed.ncbi.nlm.nih.gov/33251700/
            - ILADS treatment guideline official page: https://www.ilads.org/patient-care/ilads-treatment-guidelines/
            - ILADS 2014 guideline PubMed record: https://pubmed.ncbi.nlm.nih.gov/25077519/
            - Recent PTLDS treatment systematic review: https://pubmed.ncbi.nlm.nih.gov/38606630/
            - BMJ Lyme diagnosis/management review: https://pubmed.ncbi.nlm.nih.gov/32457042/

            Use these as retrieved context, not as permission to invent exact recommendations that are not present in the PubMed abstracts.
            The official pages are guideline source links; PubMed records are biomedical literature links.
            """
        ).strip(),
    }
]

KNOWN_GUIDELINE_LOOKUPS = [
    {
        "name": "IDSA/AAN/ACR 2020 Lyme disease guideline",
        "match_terms": ("idsa",),
        "pmids": ["33251700"],
        "context": dedent(
            """
            Official guideline source:
            - IDSA/AAN/ACR 2020 Lyme disease guideline: https://www.idsociety.org/practice-guideline/lyme-disease/
            - PubMed record: https://pubmed.ncbi.nlm.nih.gov/33251700/
            """
        ).strip(),
    },
    {
        "name": "ILADS 2014 Lyme disease treatment guideline",
        "match_terms": ("ilads",),
        "pmids": ["25077519"],
        "context": dedent(
            """
            Official guideline source:
            - ILADS treatment guidelines: https://www.ilads.org/patient-care/ilads-treatment-guidelines/
            - PubMed record: https://pubmed.ncbi.nlm.nih.gov/25077519/
            """
        ).strip(),
    },
    {
        "name": "CDC Lyme disease treatment and clinical care",
        "match_terms": ("cdc",),
        "pmids": ["33251700", "38606630", "32457042"],
        "context": dedent(
            """
            Official public-health sources:
            - CDC Lyme disease treatment page: https://www.cdc.gov/lyme/treatment/index.html
            - CDC clinical care page for healthcare providers: https://www.cdc.gov/lyme/hcp/clinical-care/index.html
            Supporting biomedical records may include the IDSA/AAN/ACR guideline and PTLDS reviews.
            """
        ).strip(),
    },
    {
        "name": "NICE NG95 Lyme disease guideline",
        "match_terms": ("nice",),
        "pmids": [],
        "context": dedent(
            """
            Official guideline sources:
            - NICE NG95 Lyme disease guideline: https://www.nice.org.uk/guidance/ng95
            - NCBI Bookshelf mirror: https://www.ncbi.nlm.nih.gov/books/NBK542111/
            - NICE evidence review for ongoing symptoms: https://www.ncbi.nlm.nih.gov/books/NBK578130/
            """
        ).strip(),
    },
]

BASE_PROMPT = dedent(
    """
    You are Lymewire, an evidence-aware Lyme disease and tick-borne illness research assistant.
    Answer in the user's language when possible. Be clear, calm, practical, and honest about uncertainty.

    Product identity:
    - Lymewire is not an AI doctor.
    - Lymewire retrieves, compares, explains, and cites medical/scientific evidence.
    - Lymewire supports patients, suspected patients, clinicians, researchers, and advocates.
    - Lymewire's product promise is: evidence before opinion, no fake certainty, patient dignity, clinician usefulness, and safety boundaries.

    Response quality contract:
    - Do not give bland generic medical disclaimers as the main answer.
    - Start with the most useful direct answer, then explain evidence and uncertainty.
    - Make the answer usable for a patient: what to track, what to ask, what would change urgency.
    - Separate established guidance, limited evidence, hypotheses, anecdotes, and unsupported claims.
    - Name the evidence type when possible: guideline, systematic review, randomized trial, pilot trial, case report, animal/in-vitro, anecdote.
    - Make certainty visible with short labels such as higher confidence, mixed/uncertain, or weak evidence.
    - If sources are not retrieved, say so plainly and avoid pretending the answer is citation-backed.
    - Detect false premises and correct them gently.
    - Avoid both dismissal and overvalidation. Symptoms can be real even when cause/treatment is uncertain.
    - Prefer concrete next questions over vague "talk to your doctor" endings.

    Safety boundaries:
    - Do not diagnose, prescribe, change medication, or replace urgent care.
    - Encourage qualified clinicians for diagnosis and treatment decisions.
    - For emergency symptoms, advise urgent local medical help immediately.
    - For dosing, interactions, pregnancy, children, severe symptoms, or self-harm, use extra caution.
    - Use neutral wording such as "a clinician experienced with Lyme/tick-borne disease".
    - Never use the phrase "Lyme-literate".
    - Keep Telegram replies compact, readable, and action-oriented.
    """
).strip()

DEFAULT_RESPONSE_PROMPT = dedent(
    """
    Default conversation format:
    - If the user is only greeting or testing the bot, answer naturally and briefly.
    - For Lyme/tick-borne illness, symptom, treatment, test, article, or guideline questions, use these headings:
      Kisa cevap
      Kanit ve belirsizlik
      Ne takip edilmeli
      Doktora sorulacak iyi sorular
      Guvenlik / aciliyet
    - Keep each section short but substantive.
    - If the user writes Turkish, use Turkish headings and a warm, direct tone.
    - If the question needs sources, suggest the best command: /research, /paper, /treatment, /compare, /guideline, or /trial.
    """
).strip()

QUALITY_REPAIR_PROMPT = dedent(
    """
    The draft answer was too generic or not useful enough for Lymewire's quality bar.
    Rewrite it so it is specific, patient-useful, safe, and honest about uncertainty.

    Required improvements:
    - Lead with a direct practical answer.
    - Include evidence/uncertainty, not just reassurance.
    - Include what to track or bring to a clinician.
    - Include 2-4 sharp clinician questions when relevant.
    - Include emergency red flags when relevant.
    - Do not diagnose, prescribe, or invent sources.
    - Do not use the phrase "Lyme-literate".
    """
).strip()


EVIDENCE_CARD_PROMPT = dedent(
    """
    Strict Evidence Card output rules:
    - Your first visible line must be exactly: Bottom line
    - Do not start with any other title, including "Research scout summary", "Treatment summary", or similar.
    - Use this exact heading order:
      Bottom line
      Evidence Card
      What was retrieved
      What it supports
      What it does NOT prove
      Risks / caveats
      Practical next step
    - Include PMID and PubMed URL for each central paper when available.
    - Rank evidence strength as High / Moderate / Low / Very low and briefly justify it.
    - If the retrieved papers are not a perfect match, explicitly say so.
    - Do not overclaim from abstracts, reviews, pilots, animal studies, or uncontrolled studies.
    """
).strip()

GUIDELINE_CARD_PROMPT = dedent(
    """
    Strict guideline output rules:
    - Your first visible line must be exactly: Bottom line
    - Do not start with any other title.
    - Use this exact heading order:
      Bottom line
      Guideline Card
      Source identity
      What it recommends / emphasizes
      Evidence strength
      What it does NOT settle
      Risks / caveats
      Questions for a clinician
      Practical next step
    - Include official guideline links and PMID/PubMed URLs when available.
    - Clearly distinguish official guideline pages from PubMed literature records.
    - Do not invent recommendations, dosing, durations, or source text not present in retrieved context.
    """
).strip()

TRIAL_CARD_PROMPT = dedent(
    """
    Strict clinical trial output rules:
    - Your first visible line must be exactly: Bottom line
    - Do not start with any other title.
    - Use this exact heading order:
      Bottom line
      Trial Card
      What was retrieved
      Trial status snapshot
      What is being tested
      Who it may apply to
      What this does NOT prove
      Risks / caveats
      Practical next step
    - Include NCT ID and ClinicalTrials.gov URL for each central trial when available.
    - Clearly distinguish recruiting, active, completed, terminated, and unknown status.
    - Do not imply that a listed trial proves a treatment works.
    - Do not encourage enrollment as medical advice; suggest discussing eligibility with a qualified clinician/research site.
    """
).strip()

COMPARE_CARD_PROMPT = dedent(
    """
    Strict comparison output rules:
    - Your first visible line must be exactly: Bottom line
    - Do not start with any other title.
    - Use this exact heading order:
      Bottom line
      Comparison Card
      What was retrieved
      Side-by-side comparison
      Where they agree
      Where they differ
      What this does NOT prove
      Risks / caveats
      Practical next step
    - Compare positions neutrally, but do not create false balance when evidence strength differs.
    - Include PMID and PubMed URL for central papers when available.
    - If the retrieved PubMed records do not directly represent both sides, say so clearly.
    - Do not invent guideline text, organization positions, citations, or URLs.
    """
).strip()

MODE_PROMPTS = {
    "default": BASE_PROMPT + "\n\n" + DEFAULT_RESPONSE_PROMPT,
    "symptoms": BASE_PROMPT
    + "\n\nMode: symptom intake. Use the headings: Kisa cevap, Kirmizi bayraklar, Belirti zaman cizelgesi, Takip edilecek veriler, Doktora hazir not. Be concrete and do not claim permanent storage.",
    "doctorbrief": BASE_PROMPT
    + "\n\nMode: doctor brief. Produce a clinician-facing appointment brief with: main concern, timeline, current meds/supplements if provided, tests/results to bring, differential questions to raise, and what would change urgency. Make it copy-paste useful.",
    "paper": BASE_PROMPT
    + "\n\nMode: paper/article analysis. Use the retrieved PubMed record when present. Do not invent missing paper details.\n\n"
    + EVIDENCE_CARD_PROMPT,
    "research": BASE_PROMPT
    + "\n\nMode: research scout. Use retrieved PubMed records when present. Compare what the papers appear to address, identify the most relevant records, and suggest what to read next. Do not overclaim beyond titles/abstracts.\n\n"
    + EVIDENCE_CARD_PROMPT,
    "treatment": BASE_PROMPT
    + "\n\nMode: treatment evidence review. Use retrieved PubMed records when present. Separate established guideline-backed care, plausible but uncertain approaches, unsupported claims, risks, and clinician questions. Do not tell the user to start/stop/change treatment.\n\n"
    + EVIDENCE_CARD_PROMPT,
    "compare": BASE_PROMPT
    + "\n\nMode: source/guideline comparison. Use retrieved PubMed records when present. Compare two organizations, guidelines, studies, or claims side-by-side. Separate agreement, disagreement, evidence quality, and patient-facing implications. Do not invent source details.\n\n"
    + COMPARE_CARD_PROMPT,
    "guideline": BASE_PROMPT
    + "\n\nMode: guideline card. Use retrieved official guideline seed context and PubMed records when present. Summarize one guideline/source, its scope, what it emphasizes, evidence strength, caveats, and patient-facing clinician questions.\n\n"
    + GUIDELINE_CARD_PROMPT,
    "trial": BASE_PROMPT
    + "\n\nMode: clinical trial scout. Use retrieved ClinicalTrials.gov study records when present. Summarize trial status, intervention, phase, population, eligibility caveats, and practical next steps. Do not imply efficacy from registration alone.\n\n"
    + TRIAL_CARD_PROMPT,
    "source": BASE_PROMPT
    + "\n\nMode: source-aware answer. Separate established evidence from uncertain or controversial claims. Mention source types users should verify, such as CDC, ECDC, NICE, peer-reviewed reviews, NIH trials, IDSA, ILADS, or local guidelines. Do not invent URLs.",
    "calm": BASE_PROMPT
    + "\n\nMode: anxiety support. Use a grounding, non-alarming tone. First check for emergency red flags, then give a short breathing/grounding step and one practical next action. Avoid spiraling possibilities.",
}

START_TEXT = dedent(
    f"""
    {APP_NAME} aktif.

    Lyme, kene kaynakli enfeksiyonlar, makaleler, tedavi iddialari, semptom takibi ve doktor randevusuna hazirlik icin bana yazabilirsin.

    Komutlar:
    /symptoms - belirti kaydi ve doktorluk ozet
    /doctorbrief - randevuya hazirlik ozeti
    /paper - PubMed PMID/abstract/makale analizi
    /research - PubMed aramasi + kanit karti
    /treatment - PubMed destekli tedavi kanit-risk karti
    /compare - iki kaynak/guideline/iddia karsilastirma
    /guideline - tek guideline/resmi kaynak ozeti
    /trial - ClinicalTrials.gov klinik calisma aramasi
    /source - kaynak/kanit odakli yanit modu
    /calm - panik veya anksiyete aninda sakin mod
    /safety - acil uyari sinirlari
    /help - nasil kullanilir

    Not: Tani koymam, ilac/tedavi emri vermem. Acil veya kotulesen belirtilerde yerel acil saglik hizmetine basvur.
    """
).strip()

HELP_TEXT = dedent(
    """
    Sorunu normal mesaj olarak yazabilirsin.

    Hizli kullanim:
    /symptoms Bugun bas agrisi, carpinti ve halsizlik var. Ates yok.
    /doctorbrief 3 haftadir doksisiklin kullandim, ishal ve halsizlik oldu.
    /paper 12345678
    /paper chronic lyme antibiotic trial
    /research post-treatment Lyme disease syndrome randomized trial
    /treatment long-term antibiotics post-treatment Lyme disease syndrome
    /compare IDSA vs ILADS chronic Lyme treatment
    /guideline NICE Lyme disease ongoing symptoms
    /trial post-treatment Lyme disease syndrome
    /source Kronik Lyme konusunda kanit tartismasi ne?
    /calm Panik oldum, kalbim hizli atiyor.

    /paper, /research, /treatment, /compare ve /guideline kaynak/PubMed kaydi cekmeye calisir. /trial ClinicalTrials.gov uzerinden klinik calisma arar.
    """
).strip()

SAFETY_TEXT = dedent(
    """
    Acil destek gerektirebilecek durumlar:
    - Nefes darligi, gogus agrisi, bayilma, yeni felc/konusma bozuklugu
    - Yuksek ates, ense sertligi, siddetli bas agrisi, bilinc bulanıklığı
    - Hizla artan dokuntu, yuz/dil/ses tellerinde sisme
    - Siddetli karin agrisi, yogun kanama, hamilelik supheli acil durumlar
    - Kendine zarar verme dusuncesi

    Boyle bir durumda botla bekleme; bulundugun yerdeki acil saglik hattini ara veya en yakin acile git.
    """
).strip()

COMMAND_HINTS = {
    "symptoms": "Belirtilerini, ne zaman basladigini, ates olup olmadigini, kullandigin ilaclari ve seni en cok korkutan seyi tek mesajda yaz.",
    "doctorbrief": "Randevu icin sikayetini, sureyi, mevcut ilaclari, test sonuclarini ve doktora sormak istediklerini yaz.",
    "paper": "PMID, DOI, makale basligi, PubMed arama cumlesi, abstract veya metin yapistir. PMID/baslik varsa PubMed'den cekip analiz edecegim.",
    "research": "PubMed'de ne arayayim? Ornek: post-treatment Lyme disease syndrome randomized trial",
    "treatment": "Hangi tedavi veya iddiayi PubMed destekli inceleyeyim? Ornek: long-term antibiotics post-treatment Lyme disease syndrome",
    "compare": "Neyi karsilastirayim? Ornek: IDSA vs ILADS chronic Lyme treatment",
    "guideline": "Hangi guideline/resmi kaynagi ozetleyeyim? Ornek: CDC Lyme treatment veya NICE ongoing symptoms",
    "trial": "ClinicalTrials.gov'da ne arayayim? Ornek: post-treatment Lyme disease syndrome veya Lyme vaccine",
    "source": "Hangi iddia veya konuyu kaynak/kanit acisindan inceleyeyim? Tek mesajda yaz.",
    "calm": "Once guvende misin? Gogus agrisi, bayilma, nefes darligi veya kendine zarar dusuncesi varsa acile yonel. Yoksa ne hissettigini yaz, beraber daraltalim.",
}


def require_env() -> None:
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def command_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    return " ".join(context.args).strip() if context.args else ""


def ncbi_params(extra: dict) -> dict:
    params = {"tool": NCBI_TOOL_NAME, **extra}
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    return params


def extract_pmids(text: str) -> list[str]:
    pmids = re.findall(r"(?i)(?:PMID[:\s#]*|pubmed\.ncbi\.nlm\.nih\.gov/)(\d{6,9})", text)
    stripped = text.strip()
    if not pmids and re.fullmatch(r"\d{6,9}", stripped):
        pmids = [stripped]
    return list(dict.fromkeys(pmids))[:5]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return clean_text("".join(element.itertext()))


def article_year(article: ET.Element) -> str:
    for path in (
        ".//ArticleDate/Year",
        ".//JournalIssue/PubDate/Year",
        ".//JournalIssue/PubDate/MedlineDate",
    ):
        value = clean_text(article.findtext(path))
        if value:
            return value
    return "Unknown year"


def article_doi(article: ET.Element) -> str:
    for article_id in article.findall(".//ArticleId"):
        if article_id.attrib.get("IdType", "").lower() == "doi":
            return clean_text(article_id.text)
    return ""


def article_abstract(article: ET.Element) -> str:
    parts = []
    for abstract_text in article.findall(".//Abstract/AbstractText"):
        label = abstract_text.attrib.get("Label")
        text = element_text(abstract_text)
        if text and label:
            parts.append(f"{label}: {text}")
        elif text:
            parts.append(text)
    return " ".join(parts)


async def pubmed_search(query: str, limit: int = 5) -> list[str]:
    params = ncbi_params(
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(limit),
            "sort": "relevance",
        }
    )
    async with httpx.AsyncClient(timeout=20) as http:
        response = await http.get(PUBMED_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


async def pubmed_fetch(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = ncbi_params(
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
    )
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.get(PUBMED_FETCH_URL, params=params)
        response.raise_for_status()
        xml_text = response.text

    root = ET.fromstring(xml_text)
    records = []
    for item in root.findall(".//PubmedArticle"):
        pmid = clean_text(item.findtext("./MedlineCitation/PMID"))
        title = element_text(item.find("./MedlineCitation/Article/ArticleTitle"))
        journal = clean_text(item.findtext("./MedlineCitation/Article/Journal/Title"))
        abstract = article_abstract(item)
        doi = article_doi(item)
        records.append(
            {
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "year": article_year(item),
                "doi": doi,
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            }
        )
    return records


def format_pubmed_records(records: list[dict]) -> str:
    blocks = []
    for index, record in enumerate(records, start=1):
        abstract = record.get("abstract") or "No abstract available in PubMed response."
        if len(abstract) > 1400:
            abstract = abstract[:1400].rstrip() + "..."
        blocks.append(
            dedent(
                f"""
                [{index}] PMID: {record.get('pmid')}
                Title: {record.get('title')}
                Journal/year: {record.get('journal')} / {record.get('year')}
                DOI: {record.get('doi') or 'Not listed'}
                URL: {record.get('url')}
                Abstract: {abstract}
                """
            ).strip()
        )
    return "\n\n".join(blocks)


async def build_pubmed_context(query_or_pmid: str, limit: int = 5) -> tuple[str, list[str]]:
    pmids = extract_pmids(query_or_pmid)
    search_note = []
    if pmids:
        search_note.append(f"Detected PMID(s): {', '.join(pmids)}")
    else:
        search_note.append(f"PubMed search query: {query_or_pmid}")
        pmids = await pubmed_search(query_or_pmid, limit=limit)
        search_note.append(f"Retrieved PMID(s): {', '.join(pmids) if pmids else 'none'}")

    records = await pubmed_fetch(pmids)
    if not records:
        return "No PubMed records were retrieved.", search_note
    return format_pubmed_records(records), search_note


def match_known_guideline_comparison(query: str) -> dict | None:
    lowered = query.lower()
    for item in KNOWN_GUIDELINE_COMPARISONS:
        if all(term in lowered for term in item["match_terms"]):
            return item
    return None


async def build_compare_context(query_or_pmid: str, limit: int = 5) -> tuple[str, list[str]]:
    known = match_known_guideline_comparison(query_or_pmid)
    if known:
        records = await pubmed_fetch(known["pmids"])
        context_parts = [known["context"]]
        if records:
            context_parts.append(format_pubmed_records(records))
        return "\n\n".join(context_parts), [
            f"Matched known comparison: {known['name']}",
            f"Seeded PMID(s): {', '.join(known['pmids'])}",
        ]

    return await build_pubmed_context(query_or_pmid, limit=limit)


def match_known_guideline_lookup(query: str) -> dict | None:
    lowered = query.lower()
    for item in KNOWN_GUIDELINE_LOOKUPS:
        if all(term in lowered for term in item["match_terms"]):
            return item
    return None


async def build_guideline_context(query_or_pmid: str, limit: int = 5) -> tuple[str, list[str]]:
    known = match_known_guideline_lookup(query_or_pmid)
    if known:
        context_parts = [known["context"]]
        if known["pmids"]:
            records = await pubmed_fetch(known["pmids"])
            if records:
                context_parts.append(format_pubmed_records(records))
        return "\n\n".join(context_parts), [
            f"Matched known guideline/source: {known['name']}",
            f"Seeded PMID(s): {', '.join(known['pmids']) if known['pmids'] else 'none'}",
        ]

    return await build_pubmed_context(query_or_pmid, limit=limit)


def trial_value(value, fallback: str = "Not listed") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        cleaned = [str(item) for item in value if item]
        return ", ".join(cleaned) if cleaned else fallback
    if isinstance(value, dict):
        return str(value.get("date") or value.get("count") or fallback)
    text = str(value).strip()
    return text if text else fallback


async def clinicaltrials_search(query: str, limit: int = 5) -> list[dict]:
    params = {
        "format": "json",
        "query.term": query,
        "pageSize": str(limit),
    }
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.get(CLINICALTRIALS_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("studies", [])


def format_trial_records(studies: list[dict]) -> str:
    blocks = []
    for index, study in enumerate(studies, start=1):
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        design = protocol.get("designModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        contacts = protocol.get("contactsLocationsModule", {})

        nct_id = identification.get("nctId", "")
        title = identification.get("briefTitle") or identification.get("officialTitle") or "Untitled"
        interventions = []
        for item in arms.get("interventions", []) or []:
            name = item.get("name")
            itype = item.get("type")
            if name and itype:
                interventions.append(f"{itype}: {name}")
            elif name:
                interventions.append(name)

        locations = []
        for location in contacts.get("locations", []) or []:
            facility = location.get("facility")
            city = location.get("city")
            country = location.get("country")
            parts = [part for part in (facility, city, country) if part]
            if parts:
                locations.append(", ".join(parts))
            if len(locations) >= 3:
                break

        summary = description.get("briefSummary") or "No brief summary listed."
        if len(summary) > 900:
            summary = summary[:900].rstrip() + "..."

        criteria = eligibility.get("eligibilityCriteria") or ""
        if len(criteria) > 700:
            criteria = criteria[:700].rstrip() + "..."

        blocks.append(
            dedent(
                f"""
                [{index}] NCT ID: {nct_id}
                Title: {clean_text(title)}
                URL: https://clinicaltrials.gov/study/{nct_id}
                Overall status: {trial_value(status.get('overallStatus'))}
                Start date: {trial_value(status.get('startDateStruct'))}
                Completion date: {trial_value(status.get('completionDateStruct'))}
                Study type: {trial_value(design.get('studyType'))}
                Phase(s): {trial_value(design.get('phases'))}
                Enrollment: {trial_value((design.get('enrollmentInfo') or {}).get('count'))}
                Conditions: {trial_value(conditions.get('conditions'))}
                Interventions: {trial_value(interventions)}
                Locations sample: {trial_value(locations)}
                Brief summary: {clean_text(summary)}
                Eligibility excerpt: {clean_text(criteria)}
                """
            ).strip()
        )
    return "\n\n".join(blocks)


async def build_trial_context(query: str, limit: int = 5) -> tuple[str, list[str]]:
    studies = await clinicaltrials_search(query, limit=limit)
    if not studies:
        return "No ClinicalTrials.gov study records were retrieved.", [f"ClinicalTrials.gov query: {query}"]
    return format_trial_records(studies), [
        f"ClinicalTrials.gov query: {query}",
        f"Retrieved trial record count: {len(studies)}",
    ]


def normalize_answer(answer: str, evidence_card: bool = False) -> str:
    normalized = answer.strip()
    normalized = re.sub(r"(?i)Lyme-literate", "clinician experienced with Lyme/tick-borne disease", normalized)
    normalized = re.sub(r"(?im)^#{1,6}\s*Research scout summary[^\n]*\n+", "", normalized)
    normalized = re.sub(r"(?im)^#{1,6}\s*Treatment summary[^\n]*\n+", "", normalized)
    normalized = re.sub(r"(?im)^#{1,6}\s*General medical disclaimer[^\n]*\n+", "", normalized)
    normalized = normalized.replace("This is not medical advice.", "")
    normalized = normalized.replace("Bu tıbbi tavsiye değildir.", "")
    normalized = normalized.replace("Bu tibbi tavsiye degildir.", "")
    if evidence_card and not re.match(r"(?i)^#{0,3}\s*Bottom line\b", normalized):
        normalized = "Bottom line\n\n" + normalized
    return normalized.strip()


def needs_quality_repair(answer: str, evidence_card: bool = False) -> bool:
    if evidence_card:
        return False
    text = answer.strip()
    if len(text) < 320:
        return True
    lowered = text.lower()
    has_generic_exit = any(
        phrase in lowered
        for phrase in (
            "consult your doctor",
            "talk to your doctor",
            "doktorunuza danış",
            "doktorunuza danis",
            "bir doktora danış",
            "bir doktora danis",
        )
    )
    has_useful_structure = any(
        marker in lowered
        for marker in (
            "kanıt",
            "kanit",
            "belirsizlik",
            "takip",
            "sorulacak",
            "red flag",
            "kırmızı",
            "kirmizi",
            "acil",
            "pmid",
            "nct",
        )
    )
    return has_generic_exit and not has_useful_structure


async def send_chunks(update: Update, text: str) -> None:
    if not update.message:
        return
    clean = text.strip() or "Cevap uretilemedi. Biraz daha detay yazar misin?"
    for start in range(0, len(clean), MAX_TELEGRAM_MESSAGE):
        await update.message.reply_text(clean[start : start + MAX_TELEGRAM_MESSAGE])


async def ask_model(
    update: Update,
    prompt: str,
    user_text: str,
    evidence_card: bool = False,
    quality_repair: bool = True,
) -> None:
    if not update.message:
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
        )
        answer = normalize_answer(response.output_text, evidence_card=evidence_card)

        if quality_repair and needs_quality_repair(answer, evidence_card=evidence_card):
            repair_response = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": prompt + "\n\n" + QUALITY_REPAIR_PROMPT},
                    {
                        "role": "user",
                        "content": dedent(
                            f"""
                            Original user request:
                            {user_text}

                            Draft answer that needs improvement:
                            {answer}

                            Rewrite the answer now.
                            """
                        ).strip(),
                    },
                ],
            )
            answer = normalize_answer(repair_response.output_text, evidence_card=evidence_card)
    except Exception:
        logger.exception("Telegram answer failed")
        answer = "Su an cevap uretirken sorun yasadim. Birazdan tekrar dener misin?"

    await send_chunks(update, answer)


async def ask_with_pubmed(
    update: Update,
    prompt: str,
    user_text: str,
    mode_label: str,
    compare_mode: bool = False,
    guideline_mode: bool = False,
) -> None:
    if not update.message:
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        if compare_mode:
            pubmed_context, search_note = await build_compare_context(user_text)
        elif guideline_mode:
            pubmed_context, search_note = await build_guideline_context(user_text)
        else:
            pubmed_context, search_note = await build_pubmed_context(user_text)
        enriched = dedent(
            f"""
            User request:
            {user_text}

            Retrieval notes:
            {'; '.join(search_note)}

            Retrieved PubMed context:
            {pubmed_context}

            Task:
            Use the retrieved PubMed context for the {mode_label}. If records are weakly related or missing abstracts, say that clearly. Keep the answer practical and safe.
            The final answer must start with the exact line "Bottom line" and follow the Evidence Card heading order from the system instructions.
            """
        ).strip()
        await ask_model(update, prompt, enriched, evidence_card=True)
    except Exception:
        logger.exception("PubMed retrieval failed")
        fallback = dedent(
            f"""
            PubMed kaydini su an cekemedim; yine de verdigin metin/arama cumlesi uzerinden guvenli bir on analiz yapabilirim.

            Istersen tekrar dene veya PMID/abstract'i direkt yapistir.
            """
        ).strip()
        await send_chunks(update, fallback)


async def ask_with_trials(update: Update, prompt: str, user_text: str) -> None:
    if not update.message:
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        trial_context, search_note = await build_trial_context(user_text)
        enriched = dedent(
            f"""
            User request:
            {user_text}

            Retrieval notes:
            {'; '.join(search_note)}

            Retrieved ClinicalTrials.gov context:
            {trial_context}

            Task:
            Use the retrieved ClinicalTrials.gov context for the clinical trial scout summary.
            If records are weakly related, terminated, not recruiting, or missing details, say that clearly.
            The final answer must start with the exact line "Bottom line" and follow the Trial Card heading order from the system instructions.
            """
        ).strip()
        await ask_model(update, prompt, enriched, evidence_card=True)
    except Exception:
        logger.exception("ClinicalTrials.gov retrieval failed")
        fallback = dedent(
            """
            ClinicalTrials.gov kaydini su an cekemedim. Arama cumlesini biraz daraltip tekrar deneyebilirsin.

            Ornek: /trial post-treatment Lyme disease syndrome
            """
        ).strip()
        await send_chunks(update, fallback)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, HELP_TEXT)


async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, SAFETY_TEXT)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS[mode])
        return
    await ask_model(update, MODE_PROMPTS[mode], text, quality_repair=(mode != "calm"))


async def symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "symptoms")


async def doctorbrief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "doctorbrief")


async def paper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["paper"])
        return
    await ask_with_pubmed(update, MODE_PROMPTS["paper"], text, "paper/article analysis")


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["research"])
        return
    await ask_with_pubmed(update, MODE_PROMPTS["research"], text, "research scout summary")


async def treatment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["treatment"])
        return
    await ask_with_pubmed(update, MODE_PROMPTS["treatment"], text, "treatment evidence review")


async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["compare"])
        return
    await ask_with_pubmed(
        update,
        MODE_PROMPTS["compare"],
        text,
        "source/guideline comparison",
        compare_mode=True,
    )


async def guideline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["guideline"])
        return
    await ask_with_pubmed(
        update,
        MODE_PROMPTS["guideline"],
        text,
        "guideline/source card",
        guideline_mode=True,
    )


async def trial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS["trial"])
        return
    await ask_with_trials(update, MODE_PROMPTS["trial"], text)


async def source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "source")


async def calm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "calm")


async def answer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    if not question:
        return

    await ask_model(update, MODE_PROMPTS["default"], question, quality_repair=True)


def build_application() -> Application:
    require_env()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("safety", safety))
    application.add_handler(CommandHandler("symptoms", symptoms))
    application.add_handler(CommandHandler("doctorbrief", doctorbrief))
    application.add_handler(CommandHandler("paper", paper))
    application.add_handler(CommandHandler("research", research))
    application.add_handler(CommandHandler("treatment", treatment))
    application.add_handler(CommandHandler("compare", compare))
    application.add_handler(CommandHandler("guideline", guideline))
    application.add_handler(CommandHandler("trial", trial))
    application.add_handler(CommandHandler("source", source))
    application.add_handler(CommandHandler("calm", calm))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_message))
    return application


def main() -> None:
    application = build_application()
    logger.info("Starting %s Telegram bot with model %s", APP_NAME, MODEL)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
