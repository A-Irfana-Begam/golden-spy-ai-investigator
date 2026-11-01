
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
        if (urlList.querySelectorAll(".source-url").length >= 8) {
            alert("Maximum 8 sources allowed.");
            return;
        }

        const input = document.createElement("input");
        input.type = "url";
        input.className = "source-url";
        input.placeholder = "https://example.com";
        input.maxLength = 2048;

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

                const fields = [
                    ["claim", ""],
                    ["gap", ""],
                    ["signal", ""],
                    ["claim_1", "Claim 1: "],
                    ["claim_2", "Claim 2: "],
                    ["note", "Analysis: "],
                    ["task", "Task: "],
                    ["priority", "Priority: "],
                    ["source", "Source: "],
                    ["source_1", "Source 1: "],
                    ["source_2", "Source 2: "]
                ];

                fields.forEach(([key, label]) => {
                    if (typeof item[key] === "string" && item[key].trim()) {
                        details.push(label + item[key]);
                    }
                });

                if (Array.isArray(item.sources)) {
                    details.push(
                        "Supporting sources: " +
                        item.sources.filter(
                            source => typeof source === "string"
                        ).join(", ")
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


function validateSourceUrls(urls) {
    for (const value of urls) {
        try {
            const url = new URL(value);

            if (
                !["http:", "https:"].includes(url.protocol) ||
                !url.hostname ||
                url.username ||
                url.password
            ) {
                return false;
            }
        } catch {
            return false;
        }
    }

    return true;
}


if (investigateButton) {
    investigateButton.onclick = async () => {
        const questionInput = document.getElementById("question");
        const status = document.getElementById("status");
        const results = document.getElementById("results");
        const report = document.getElementById("report");

        if (!questionInput || !status || !results || !report) {
            return;
        }

        const question = questionInput.value.trim();

        const urls = [
            ...document.querySelectorAll(".source-url")
        ]
            .map(input => input.value.trim())
            .filter(Boolean);

        if (!question) {
            status.textContent = "Enter a research question.";
            return;
        }

        if (urls.length > 8) {
            status.textContent = "Maximum 8 sources allowed.";
            return;
        }

        if (!validateSourceUrls(urls)) {
            status.textContent =
                "Enter valid HTTP or HTTPS webpage URLs.";
            return;
        }

        investigateButton.disabled = true;
        status.textContent =
            "⏳ Discovering sources and investigating...";

        results.hidden = true;
        report.replaceChildren();

        const controller = new AbortController();

        const timeout = setTimeout(() => {
            controller.abort();
        }, 120000);

        try {
            const response = await fetch("/api/investigate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question,
                    urls
                }),
                signal: controller.signal
            });

            let data;

            try {
                data = await response.json();
            } catch {
                throw new Error(
                    "Server returned an invalid response. Please try again."
                );
            }

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Investigation failed."
                );
            }

            if (!data.analysis || typeof data.analysis !== "object") {
                throw new Error(
                    "Investigation report is incomplete. Please try again."
                );
            }

            const analysis = data.analysis;

            const sections = [
                ["SUMMARY", analysis.summary],
                [
                    "SOURCE-SUPPORTED INFORMATION",
                    analysis.verified_information
                ],
                [
                    "CROSS-SOURCE CORROBORATION",
                    analysis.cross_source_corroboration
                ],
                ["INFORMATION GAPS", analysis.information_gaps],
                ["POTENTIAL CONFLICTS", analysis.potential_conflicts],
                ["OUTDATED SIGNALS", analysis.outdated_signals],
                [
                    "UNANSWERED QUESTIONS",
                    analysis.unanswered_questions
                ],
                [
                    "VERIFICATION CHECKLIST",
                    analysis.verification_checklist
                ]
            ];

            sections.forEach(([title, items]) => {
                report.appendChild(createCard(title, items));
            });

            const sourceStatus = Array.isArray(data.sources)
                ? data.sources.map(source => ({
                    claim: source.title || source.url || "Unknown source",
                    signal: "Status: " + (source.status || "unknown"),
                    note: source.error || ""
                }))
                : [];

            report.appendChild(
                createCard("SOURCE STATUS", sourceStatus)
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
                behavior: "smooth",
                block: "start"
            });

        } catch (error) {
            if (error.name === "AbortError") {
                status.textContent =
                    "⚠ Request timed out. Please try again.";
            } else {
                status.textContent =
                    "⚠ " + (error.message || "Investigation failed.");
            }

        } finally {
            clearTimeout(timeout);
            investigateButton.disabled = false;
        }
    };
}
