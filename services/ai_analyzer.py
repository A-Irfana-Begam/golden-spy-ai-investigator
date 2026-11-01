
import re
from datetime import datetime
from itertools import combinations


STOPWORDS = {
    "what", "when", "where", "which", "who", "why", "how",
    "the", "and", "for", "from", "with", "about", "are",
    "was", "were", "does", "did", "this", "that", "have",
    "has", "been", "into", "their", "they", "there"
}

CONTRAST_WORDS = {
    "not", "no", "never", "false", "denied", "failed",
    "cancelled", "canceled", "opposed", "rejected"
}


def get_words(text):
    return set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))


def get_sentences(text):
    return [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', text)
        if len(s.strip()) > 25
    ]


def analyze_sources(question, sources):
    report = {
        "summary": [],
        "verified_information": [],
        "information_gaps": [],
        "potential_conflicts": [],
        "outdated_signals": [],
        "unanswered_questions": [],
        "verification_checklist": []
    }

    usable = [
        s for s in sources
        if s.get("status") == "success"
        and s.get("text", "").strip()
    ]

    if not usable:
        raise ValueError("No readable sources found.")

    question_words = get_words(question) - STOPWORDS

    if not question_words:
        raise ValueError("Please enter a more specific research question.")

    all_sentences = []

    for source in usable:
        url = source["url"]
        sentences = get_sentences(source["text"])

        matched = []

        for sentence in sentences:
            words = get_words(sentence)
            common = words.intersection(question_words)

            if common:
                matched.append(sentence)
                all_sentences.append({
                    "text": sentence,
                    "url": url,
                    "words": words
                })

        for sentence in matched[:5]:
            report["verified_information"].append({
                "claim": sentence[:500],
                "source": url
            })

        missing = question_words - get_words(source["text"])

        if missing:
            report["information_gaps"].append({
                "gap": "Research terms not found: " +
                       ", ".join(sorted(missing)),
                "source": url
            })

        years = re.findall(r'\b(?:19|20)\d{2}\b', source["text"])

        old_years = sorted({
            int(y) for y in years
            if int(y) < datetime.now().year - 2
        })

        if old_years:
            report["outdated_signals"].append({
                "signal": "Older year references found: " +
                          ", ".join(map(str, old_years)),
                "source": url
            })

    # Find possible opposing statements across sources.
    for first, second in combinations(all_sentences, 2):
        if first["url"] == second["url"]:
            continue

        shared = first["words"].intersection(second["words"])
        if len(shared) < 3:
            continue

        first_negative = bool(first["words"] & CONTRAST_WORDS)
        second_negative = bool(second["words"] & CONTRAST_WORDS)

        if first_negative != second_negative:
            report["potential_conflicts"].append({
                "claim_1": first["text"][:300],
                "source_1": first["url"],
                "claim_2": second["text"][:300],
                "source_2": second["url"],
                "note": "Possible difference detected. Manual verification required."
            })

        if len(report["potential_conflicts"]) >= 10:
            break

    if not report["verified_information"]:
        report["information_gaps"].append(
            "No relevant sentences matched the research question."
        )

    report["summary"] = [
        f"Reviewed {len(usable)} accessible sources.",
        f"Found {len(report['verified_information'])} relevant sentences.",
        f"Detected {len(report['information_gaps'])} possible information gaps.",
        f"Found {len(report['potential_conflicts'])} possible conflicts."
    ]

    report["unanswered_questions"].append(
        "Do the sources provide enough evidence to answer the research question?"
    )

    report["verification_checklist"].append({
        "priority": "HIGH",
        "task": "Verify important claims against original sources.",
        "source": usable[0]["url"]
    })

    report["verification_checklist"].append({
        "priority": "MEDIUM",
        "task": "Check missing information and older date references.",
        "source": usable[0]["url"]
    })

    return report
