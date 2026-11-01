
const particles = document.getElementById("particles");

if (particles) {
    for (let i = 0; i < 55; i++) {
        const p = document.createElement("span");
        p.className = "particle";
        p.style.left = Math.random() * 100 + "%";
        p.style.animationDelay = Math.random() * 8 + "s";
        p.style.animationDuration = 5 + Math.random() * 8 + "s";
        particles.appendChild(p);
    }
}

const urlList = document.getElementById("url-list");
const addSourceButton = document.getElementById("add-source");
const investigateButton = document.getElementById("investigate");


if (addSourceButton && urlList) {
    addSourceButton.onclick = () => {
        if (urlList.children.length >= 8) {
            alert("Maximum 8 sources allowed.");
            return;
        }

        const input = document.createElement("input");
        input.type = "url";
        input.className = "source-url";
        input.placeholder = "https://example.com";

        urlList.appendChild(input);
    };
}


function createCard(title, items) {
    const card = document.createElement("div");
    card.className = "report-card";

    const heading = document.createElement("h3");
    heading.textContent = title;
    card.appendChild(heading);

    const list = document.createElement("ul");

    if (!Array.isArray(items) || items.length === 0) {
        const empty = document.createElement("li");
        empty.textContent = "No findings detected.";
        list.appendChild(empty);
    } else {
        items.forEach(item => {
            const li = document.createElement("li");

            if (typeof item === "string") {
                li.textContent = item;
            } else if (item && typeof item === "object") {
                const details = [];

                if (item.claim) details.push(item.claim);
                if (item.gap) details.push(item.gap);
                if (item.signal) details.push(item.signal);

                if (item.claim_1) {
                    details.push("Claim 1: " + item.claim_1);
                }

                if (item.claim_2) {
                    details.push("Claim 2: " + item.claim_2);
                }

                if (item.note) {
                    details.push("Analysis: " + item.note);
                }

                if (item.task) {
                    details.push("Task: " + item.task);
                }

                if (item.priority) {
                    details.push("Priority: " + item.priority);
                }

                if (item.source) {
                    details.push("Source: " + item.source);
                }

                if (item.source_1) {
                    details.push("Source 1: " + item.source_1);
                }

                if (item.source_2) {
                    details.push("Source 2: " + item.source_2);
                }

                if (Array.isArray(item.sources)) {
                    details.push(
                        "Supporting sources: " + item.sources.join(", ")
                    );
                }

                li.textContent = details.length
                    ? details.join(" | ")
                    : "No details available.";
            } else {
                li.textContent = "No details available.";
            }

            list.appendChild(li);
        });
    }

    card.appendChild(list);
    return card;
}


if (investigateButton) {
    investigateButton.onclick = async () => {
        const question = document.getElementById("question").value.trim();

        const urls = [
            ...document.querySelectorAll(".source-url")
        ]
            .map(input => input.value.trim())
            .filter(Boolean);

        const status = document.getElementById("status");
        const results = document.getElementById("results");
        const report = document.getElementById("report");

        if (!question) {
            status.textContent = "Enter a research question.";
            return;
        }

        if (urls.length > 8) {
            status.textContent = "Maximum 8 sources allowed.";
            return;
        }

        investigateButton.disabled = true;
        status.textContent = "⏳ Discovering sources and investigating...";
        results.hidden = true;
        report.replaceChildren();

        try {
            const response = await fetch("/api/investigate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question,
                    urls
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Investigation failed."
                );
            }

            const analysis = data.analysis || {};

            report.appendChild(
                createCard("SUMMARY", analysis.summary)
            );

            report.appendChild(
                createCard(
                    "SOURCE-SUPPORTED INFORMATION",
                    analysis.verified_information
                )
            );

            report.appendChild(
                createCard(
                    "CROSS-SOURCE CORROBORATION",
                    analysis.cross_source_corroboration
                )
            );

            report.appendChild(
                createCard(
                    "INFORMATION GAPS",
                    analysis.information_gaps
                )
            );

            report.appendChild(
                createCard(
                    "POTENTIAL CONFLICTS",
                    analysis.potential_conflicts
                )
            );

            report.appendChild(
                createCard(
                    "OUTDATED SIGNALS",
                    analysis.outdated_signals
                )
            );

            report.appendChild(
                createCard(
                    "UNANSWERED QUESTIONS",
                    analysis.unanswered_questions
                )
            );

            report.appendChild(
                createCard(
                    "VERIFICATION CHECKLIST",
                    analysis.verification_checklist
                )
            );

            const sourceStatus = (data.sources || []).map(source => ({
                claim: source.title || source.url,
                signal: "Status: " + source.status,
                note: source.error || ""
            }));

            report.appendChild(
                createCard("DISCOVERED SOURCE STATUS", sourceStatus)
            );

            report.appendChild(
                createCard("ANALYSIS MODE", [
                    data.analysis_mode || "Gemini AI",
                    data.disclaimer || ""
                ])
            );

            results.hidden = false;
            status.textContent = "✓ Investigation completed.";

            results.scrollIntoView({
                behavior: "smooth"
            });

        } catch (error) {
            status.textContent = "⚠ " + error.message;

        } finally {
            investigateButton.disabled = false;
        }
    };
}
