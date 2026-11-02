
import re
from collections import Counter
from urllib.parse import urlparse


STOP_WORDS = {
    "about", "after", "again", "against", "also", "among",
    "because", "before", "being", "between", "could",
    "does", "during", "each", "from", "have", "having",
    "into", "just", "more", "most", "other", "over",
    "same", "should", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "under", "until", "very",
    "what", "when", "where", "which", "while", "with",
    "would", "your", "will", "were", "been", "being",
    "using", "used", "use", "make", "made", "many",
    "much", "more", "less", "like", "well", "help",
    "learn", "read", "click", "home", "page", "website",
    "article", "latest", "readers", "today", "know",
    "information", "important", "including", "provide",
    "provides", "available", "need", "needs", "ways",
    "guide", "guides", "introduction", "overview",
    "question", "questions", "research"
}


def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())

    return {
        word for word in words
        if word not in STOP_WORDS
        and not word.isdigit()
    }


def extract_sentences(text):
    text = clean_text(text)

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 45
    ]


def get_source_domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return "Unknown source"


def calculate_relevance(question_keywords, sentence):
    sentence_keywords = extract_keywords(sentence)

    if not question_keywords or not sentence_keywords:
        return 0

    matched = question_keywords.intersection(sentence_keywords)

    return len(matched) / len(question_keywords)


def analyze_sources(question, sources):
    """
    Local rule-based investigation.

    This engine identifies relevant text and topical overlap.
    It does not establish factual truth or reliably detect contradictions.
    """

    question = clean_text(question)

    question_keywords = extract_keywords(question)

    usable_sources = [
        source for source in sources
        if source.get("status") == "success"
        and isinstance(source.get("text"), str)
        and source.get("text").strip()
    ]

    source_data = []
    all_relevant_sentences = []
    source_gaps = []

    for source in usable_sources:
        url = source.get("url", "")
        title = clean_text(source.get("title") or url)
        domain = get_source_domain(url)
        text = clean_text(source.get("text", ""))

        sentences = extract_sentences(text)

        relevant = []

        for sentence in sentences:
            score = calculate_relevance(
                question_keywords,
                sentence
            )

            # Require a meaningful keyword match.
            if score >= 0.25:
                relevant.append({
                    "sentence": sentence,
                    "score": score
                })

        relevant.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        # Avoid repeated sentences from the same source.
        unique_relevant = []
        seen_sentences = set()

        for item in relevant:
            sentence = item["sentence"]
            normalized = sentence.lower()

            if normalized in seen_sentences:
                continue

            seen_sentences.add(normalized)
            unique_relevant.append(item)

            if len(unique_relevant) >= 5:
                break

        source_data.append({
            "url": url,
            "title": title,
            "domain": domain,
            "keywords": extract_keywords(text),
            "relevant": unique_relevant
        })

        for item in unique_relevant:
            all_relevant_sentences.append({
                "claim": item["sentence"],
                "source": url,
                "domain": domain,
                "relevance": round(item["score"], 2)
            })

        if not unique_relevant:
            source_gaps.append({
                "gap": (
                    "No sufficiently relevant passage was identified "
                    "by keyword matching. This does not prove the "
                    "topic is absent from the webpage."
                ),
                "source": url
            })

    # Remove repeated claims across sources.
    verified_information = []
    seen_claims = set()

    for item in all_relevant_sentences:
        normalized = item["claim"].lower()

        if normalized in seen_claims:
            continue

        seen_claims.add(normalized)

        verified_information.append({
            "claim": item["claim"],
            "source": item["source"]
        })

    # Build a concise summary from relevant passages only.
    summary = [
        item["claim"]
        for item in verified_information[:5]
    ]

    # Compare keyword overlap only across different domains.
    corroboration = []
    seen_domain_pairs = set()

    for i in range(len(source_data)):
        for j in range(i + 1, len(source_data)):
            first = source_data[i]
            second = source_data[j]

            if first["domain"] == second["domain"]:
                continue

            common = (
                first["keywords"] & second["keywords"]
            )

            if len(common) < 3:
                continue

            pair = tuple(sorted([
                first["domain"],
                second["domain"]
            ]))

            if pair in seen_domain_pairs:
                continue

            seen_domain_pairs.add(pair)

            corroboration.append({
                "note": (
                    "These sources share topic-related keywords. "
                    "This does not establish independent confirmation."
                ),
                "analysis": (
                    "Topical overlap only; compare the original "
                    "statements before drawing conclusions."
                ),
                "source_1": first["url"],
                "source_2": second["url"]
            })

    # Do not invent conflicts or outdated findings.
    potential_conflicts = []
    outdated_signals = []

    # Unanswered questions are based on the availability of relevant text.
    if not verified_information:
        unanswered_questions = [
            {
                "question": (
                    "Which reliable sources directly address "
                    "the research question?"
                )
            }
        ]
        direct_answer = (
            "The collected sources did not provide enough "
            "clearly relevant text. Try more specific research "
            "terms or provide directly relevant webpages."
        )
    else:
        unanswered_questions = []
        direct_answer = (
            "Relevant passages were identified in the collected "
            "sources. They are presented as source-supported text, "
            "not independently verified facts."
        )

    # Verification tasks.
    verification_checklist = []

    if usable_sources:
        verification_checklist.append({
            "task": (
                "Open the original webpages and check whether "
                "the extracted passages accurately represent "
                "their context."
            ),
            "priority": "HIGH",
            "source": ", ".join(
                item["url"] for item in source_data
            )
        })

    if len(source_data) > 1:
        verification_checklist.append({
            "task": (
                "Check whether different sources provide "
                "independent evidence rather than repeating "
                "the same information."
            ),
            "priority": "MEDIUM",
            "source": ", ".join(
                item["url"] for item in source_data
            )
        })

    if source_gaps:
        verification_checklist.append({
            "task": (
                "Review sources with no keyword-matched passages "
                "and determine whether they contain relevant "
                "information expressed using different terminology."
            ),
            "priority": "MEDIUM",
            "source": ", ".join(
                item["source"] for item in source_gaps
            )
        })

    return {
        "direct_answer": direct_answer,
        "summary": summary,
        "verified_information": verified_information,
        "cross_source_corroboration": corroboration,
        "information_gaps": source_gaps,
        "potential_conflicts": potential_conflicts,
        "outdated_signals": outdated_signals,
        "unanswered_questions": unanswered_questions,
        "verification_checklist": verification_checklist
    }
