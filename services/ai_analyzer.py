
import re
from datetime import datetime

def empty_report():
    return {
        "summary": [],
        "verified_information": [],
        "information_gaps": [],
        "potential_conflicts": [],
        "outdated_signals": [],
        "unanswered_questions": [],
        "verification_checklist": []
    }


def analyze_sources(question, sources):
    report = empty_report()

    usable = [
        s for s in sources
        if s.get("status") == "success" and s.get("text", "").strip()
    ]

    if not usable:
        raise ValueError("No readable sources found.")

    keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', question.lower()))

    for source in usable:
        text = source["text"]
        url = source["url"]

        sentences = re.split(r'(?<=[.!?])\s+', text)

        matched = [
            sentence.strip() for sentence in sentences
            if keywords.intersection(
                set(re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower()))
            )
        ]

        report["verified_information"].extend([
            {"claim": sentence[:500], "source": url}
            for sentence in matched[:5]
        ])

        dates = re.findall(
            r'\b(?:19|20)\d{2}\b', text
        )

        old_dates = [
            int(year) for year in dates
            if int(year) < datetime.now().year - 2
        ]

        if old_dates:
            report["outdated_signals"].append({
                "signal": "Older year detected: " +
                          ", ".join(map(str, sorted(set(old_dates)))),
                "source": url
            })

    if not report["verified_information"]:
        report["information_gaps"].append(
            "No sentences matching the research keywords were found."
        )

    report["summary"].append(
        f"Reviewed {len(usable)} accessible sources."
    )

    report["summary"].append(
        f"Found {len(report['verified_information'])} "
        "sentences matching research keywords."
    )

    report["unanswered_questions"].append(
        "Are all important requirements covered by the sources?"
    )

    report["verification_checklist"].append({
        "priority": "HIGH",
        "task": "Verify important details using the original official sources.",
        "source": usable[0]["url"]
    })

    report["verification_checklist"].append({
        "priority": "MEDIUM",
        "task": "Check whether the information is current and complete.",
        "source": usable[0]["url"]
    })

    return report
