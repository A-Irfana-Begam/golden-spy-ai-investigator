
import re
from collections import Counter
from urllib.parse import urlparse


STOP_WORDS = {
    "the", "and", "for", "that", "with", "this", "from",
    "are", "was", "were", "has", "have", "had", "will",
    "would", "could", "should", "about", "into", "their",
    "there", "they", "them", "then", "than", "when",
    "where", "which", "what", "who", "how", "why",
    "you", "your", "our", "its", "also", "been", "being",
    "not", "but", "can", "may", "more", "most", "some",
    "such", "only", "other", "over", "after", "before",
    "between", "through", "each", "both", "any", "all",
    "use", "used", "using", "one", "two", "new"
}

REPORT_FIELDS = [
    "direct_answer",
    "summary",
    "verified_information",
    "cross_source_corroboration",
    "information_gaps",
    "potential_conflicts",
    "outdated_signals",
    "unanswered_questions",
    "verification_checklist"
]


def clean_text(value):
    if not isinstance(value, str):
        return ""

    return re.sub(r"\s+", " ", value).strip()


def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9-]{2,}\b", text.lower())

    return {
        word for word in words
        if word not in STOP_WORDS
    }


def extract_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 35
    ]


def get_source_domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def analyze_sources(question, sources):
    usable_sources = [
        source for source in sources
        if source.get("status") == "success"
        and clean_text(source.get("text"))
    ]

    if not usable_sources:
        raise ValueError("No readable sources available for analysis.")

    question_keywords = extract_keywords(question)

    source_data = []

    for source in usable_sources:
        text = clean_text(source.get("text", ""))
        sentences = extract_sentences(text)
        keywords = extract_keywords(text)

        relevant_sentences = []

        for sentence in sentences:
            sentence_keywords = extract_keywords(sentence)

            if question_keywords.intersection(sentence_keywords):
                relevant_sentences.append(sentence)

        source_data.append({
            "url": source.get("url", ""),
            "title": clean_text(source.get("title", "")),
            "text": text,
            "keywords": keywords,
            "sentences": sentences,
            "relevant_sentences": relevant_sentences,
            "domain": get_source_domain(source.get("url", ""))
        })

    report = {
        "direct_answer": "",
        "summary": [],
        "verified_information": [],
        "cross_source_corroboration": [],
        "information_gaps": [],
        "potential_conflicts": [],
        "outdated_signals": [],
        "unanswered_questions": [],
        "verification_checklist": []
    }

    # Identify relevant source content.
    matching_sources = [
        source for source in source_data
        if source["relevant_sentences"]
    ]

    if matching_sources:
        report["direct_answer"] = (
            "Relevant information was found in the supplied sources. "
            "This local analysis does not independently establish the "
            "answer as fact. Review the source-supported statements below."
        )
    else:
        report["direct_answer"] = (
            "The supplied sources do not contain enough clearly relevant "
            "text to answer this question. More suitable sources are needed."
        )

    # Extract relevant statements.
    for source in matching_sources:
        for sentence in source["relevant_sentences"][:3]:
            report["verified_information"].append({
                "claim": sentence,
                "source": source["url"]
            })

    # Create a short summary from relevant statements.
    report["summary"] = [
        item["claim"]
        for item in report["verified_information"][:5]
    ]

    # Compare keyword overlap across different domains.
    for index, first in enumerate(source_data):
        for second in source_data[index + 1:]:
            if (
                not first["domain"]
                or not second["domain"]
                or first["domain"] == second["domain"]
            ):
                continue

            common = first["keywords"].intersection(second["keywords"])

            if len(common) >= 5:
                report["cross_source_corroboration"].append({
                    "claim": (
                        "The sources share several subject-related "
                        "keywords. This is a topical overlap, not proof "
                        "that they independently confirm the same claim."
                    ),
                    "sources": [first["url"], second["url"]],
                    "note": "Independent evidence has not been established."
                })

    # Identify sources with little or no relevant information.
    for source in source_data:
        if not source["relevant_sentences"]:
            report["information_gaps"].append({
                "gap": (
                    "No clearly relevant statements were identified "
                    "by keyword matching in this source."
                ),
                "source": source["url"]
            })

    # Local keyword matching cannot reliably establish contradictions.
    report["potential_conflicts"] = []

    # Dates alone cannot establish that information is outdated.
    report["outdated_signals"] = []

    if not matching_sources:
        report["unanswered_questions"].append(
            "Which reliable sources directly address the research question?"
        )

    report["verification_checklist"].append({
        "priority": "HIGH",
        "task": "Open the original webpages and verify relevant statements.",
        "source": ", ".join(
            source["url"] for source in usable_sources
        )
    })

    report["verification_checklist"].append({
        "priority": "MEDIUM",
        "task": (
            "Check whether different sources provide independent "
            "evidence rather than repeating the same information."
        ),
        "source": ", ".join(
            source["url"] for source in usable_sources
        )
    })

    return report
