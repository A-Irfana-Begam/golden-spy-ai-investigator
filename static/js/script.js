
const particles = document.getElementById("particles");

for (let i = 0; i < 55; i++) {
    const p = document.createElement("span");
    p.className = "particle";
    p.style.left = Math.random() * 100 + "%";
    p.style.animationDelay = Math.random() * 8 + "s";
    p.style.animationDuration = 5 + Math.random() * 8 + "s";
    particles.appendChild(p);
}

const urlList = document.getElementById("url-list");

document.getElementById("add-source").onclick = () => {
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

function createCard(title, items) {
    const card = document.createElement("div");
    card.className = "report-card";

    const heading = document.createElement("h3");
    heading.textContent = title;
    card.appendChild(heading);

    const list = document.createElement("ul");

    items.forEach(item => {
        const li = document.createElement("li");

        if (typeof item === "string") {
            li.textContent = item;
        } else {
            li.textContent = [
                item.claim || item.signal || item.task || "",
                item.source ? " | Source: " + item.source : ""
            ].join("");
        }

        list.appendChild(li);
    });

    card.appendChild(list);
    return card;
}

document.getElementById("investigate").onclick = async () => {
    const question = document.getElementById("question").value.trim();

    const urls = [...document.querySelectorAll(".source-url")]
        .map(input => input.value.trim())
        .filter(Boolean);

    const status = document.getElementById("status");
    const results = document.getElementById("results");
    const report = document.getElementById("report");
    const button = document.getElementById("investigate");

    if (!question || !urls.length) {
        status.textContent = "Enter a question and at least one URL.";
        return;
    }

    button.disabled = true;
    status.textContent = "⏳ Investigating sources...";
    results.hidden = true;
    report.replaceChildren();

    try {
        const response = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, urls })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Investigation failed.");
        }

        const analysis = data.analysis;

        report.appendChild(createCard("SUMMARY", analysis.summary || []));
        report.appendChild(createCard("VERIFIED INFORMATION", analysis.verified_information || []));
        report.appendChild(createCard("INFORMATION GAPS", analysis.information_gaps || []));
        report.appendChild(createCard("POTENTIAL CONFLICTS", analysis.potential_conflicts || []));
        report.appendChild(createCard("OUTDATED SIGNALS", analysis.outdated_signals || []));
        report.appendChild(createCard("UNANSWERED QUESTIONS", analysis.unanswered_questions || []));
        report.appendChild(createCard("VERIFICATION CHECKLIST", analysis.verification_checklist || []));

        report.appendChild(createCard("SOURCE STATUS",
            (data.sources || []).map(s =>
                `${s.title || s.url}: ${s.status}${s.error ? " - " + s.error : ""}`
            )
        ));

        report.appendChild(createCard("ANALYSIS MODE", [
            data.analysis_mode,
            data.disclaimer
        ]));

        results.hidden = false;
        status.textContent = "✓ Investigation completed.";
        results.scrollIntoView({ behavior: "smooth" });

    } catch (error) {
        status.textContent = "⚠ " + error.message;
    } finally {
        button.disabled = false;
    }
};
