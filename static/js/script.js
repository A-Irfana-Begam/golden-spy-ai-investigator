
let investigationData = null;
let pageHistory = [];
let currentPage = "home-page";

function showPage(pageId) {
    const selectedPage = document.getElementById(pageId);

    if (!selectedPage) return;

    if (currentPage !== pageId) {
        pageHistory.push(currentPage);
    }

    currentPage = pageId;

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    selectedPage.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });

    updateNavigation();
}

function goBack() {
    if (pageHistory.length === 0) {
        showPage("home-page");
        return;
    }

    const previousPage = pageHistory.pop();
    currentPage = previousPage;

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    const page = document.getElementById(previousPage);

    if (page) {
        page.classList.add("active");
    } else {
        currentPage = "home-page";
        document.getElementById("home-page").classList.add("active");
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
    updateNavigation();
}

function updateNavigation() {
    const backButton = document.querySelector(".nav-actions button:last-child");

    if (backButton) {
        backButton.disabled = currentPage === "home-page";
        backButton.style.opacity =
            currentPage === "home-page" ? "0.4" : "1";
    }
}


// ADD SOURCE URL INPUT
function addUrl() {
    const container = document.getElementById("url-list");

    if (container.querySelectorAll(".url-row").length >= 8) {
        alert("Maximum 8 source URLs allowed.");
        return;
    }

    const row = document.createElement("div");
    row.className = "url-row";

    const input = document.createElement("input");
    input.type = "url";
    input.className = "source-url";
    input.placeholder = "Paste a real source URL";

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-url";
    removeButton.textContent = "×";
    removeButton.addEventListener("click", () => row.remove());

    row.append(input, removeButton);
    container.appendChild(row);
}


// REMOVE SOURCE URL INPUT
function removeUrl(button) {
    const rows = document.querySelectorAll(".url-row");

    if (rows.length > 1) {
        button.closest(".url-row").remove();
    } else {
        button.closest(".url-row").querySelector("input").value = "";
    }
}


// SAFE TEXT ELEMENT
function createTextElement(tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = String(text ?? "");

    if (className) element.className = className;

    return element;
}


// SAFE SOURCE LINK
function createSourceLink(url, allowedSources) {
    if (typeof url !== "string" || !allowedSources.includes(url)) {
        return null;
    }

    try {
        const parsed = new URL(url);

        if (!["http:", "https:"].includes(parsed.protocol)) {
            return null;
        }

        const link = document.createElement("a");
        link.href = parsed.href;
        link.textContent = "View original source";
        link.target = "_blank";
        link.rel = "noopener noreferrer";

        return link;
    } catch {
        return null;
    }
}


// DISPLAY TEXT LIST
function renderTextList(containerId, items) {
    const container = document.getElementById(containerId);
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        container.textContent = "No finding was returned for this section.";
        return;
    }

    const list = document.createElement("ul");

    items.forEach(item => {
        const listItem = document.createElement("li");

        if (typeof item === "string") {
            listItem.textContent = item;
        } else if (item && typeof item === "object") {
            listItem.textContent = Object.entries(item)
                .map(([key, value]) =>
                    `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`
                )
                .join(" | ");
        } else {
            listItem.textContent = String(item);
        }

        list.appendChild(listItem);
    });

    container.appendChild(list);
}


// VERIFIED INFORMATION
function renderVerified(items, allowedSources) {
    const container = document.getElementById("verified-content");
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        container.textContent = "No verified claims returned.";
        return;
    }

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "result-item";

        card.appendChild(createTextElement("p", item.claim));

        const link = createSourceLink(item.source, allowedSources);

        if (link) card.appendChild(link);

        container.appendChild(card);
    });
}


// POTENTIAL CONFLICTS
function renderConflicts(items, allowedSources) {
    const container = document.getElementById("conflicts-content");
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        container.textContent = "No potential conflicts returned.";
        return;
    }

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "result-item";

        card.appendChild(createTextElement("p", item.issue));

        if (Array.isArray(item.sources)) {
            item.sources.forEach(url => {
                const link = createSourceLink(url, allowedSources);
                if (link) card.appendChild(link);
            });
        }

        container.appendChild(card);
    });
}


// OUTDATED SIGNALS
function renderOutdated(items, allowedSources) {
    const container = document.getElementById("outdated-content");
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        container.textContent = "No outdated signals returned.";
        return;
    }

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "result-item";

        card.appendChild(createTextElement("p", item.signal));

        const link = createSourceLink(item.source, allowedSources);
        if (link) card.appendChild(link);

        container.appendChild(card);
    });
}


// VERIFICATION CHECKLIST
function renderChecklist(items, allowedSources) {
    const container = document.getElementById("verification-list");
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        container.appendChild(
            createTextElement("p", "No verification tasks returned.", "empty-state")
        );
        return;
    }

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "verification-item";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.setAttribute("aria-label", "Mark task complete");

        const content = document.createElement("div");

        content.appendChild(
            createTextElement("strong", item.priority || "PRIORITY NOT SPECIFIED")
        );

        content.appendChild(
            createTextElement("p", item.task || "Verification task not specified.")
        );

        const link = createSourceLink(item.source, allowedSources);
        if (link) content.appendChild(link);

        card.append(checkbox, content);
        container.appendChild(card);
    });
}


// REAL FETCHED SOURCES
function renderSources(sources) {
    const container = document.getElementById("source-evidence-list");
    container.replaceChildren();

    if (!Array.isArray(sources) || sources.length === 0) {
        container.textContent = "No sources were fetched.";
        return;
    }

    const allowedSources = sources
        .filter(source => source.status === "success")
        .map(source => source.url);

    sources.forEach(source => {
        const card = document.createElement("div");
        card.className = "source-item";

        card.appendChild(
            createTextElement("h3", source.title || "Untitled source")
        );

        card.appendChild(
            createTextElement("p", "Fetch status: " + source.status)
        );

        if (source.status === "success") {
            const text = source.text || "";

            card.appendChild(
                createTextElement(
                    "p",
                    text.slice(0, 600) + (text.length > 600 ? "..." : "")
                )
            );
        } else {
            card.appendChild(
                createTextElement("p", source.error || "Source could not be accessed.")
            );
        }

        const link = createSourceLink(source.url, allowedSources);
        if (link) card.appendChild(link);

        container.appendChild(card);
    });
}


// COMPLETE REPORT
function displayReport(data) {
    const analysis = data.analysis || {};

    const allowedSources = (data.sources || [])
        .filter(source => source.status === "success")
        .map(source => source.url);

    renderTextList("summary-content", analysis.summary);
    renderVerified(analysis.verified_information, allowedSources);
    renderTextList("gaps-content", analysis.information_gaps);
    renderConflicts(analysis.potential_conflicts, allowedSources);
    renderOutdated(analysis.outdated_signals, allowedSources);
    renderTextList("questions-content", analysis.unanswered_questions);
    renderChecklist(analysis.verification_checklist, allowedSources);
    renderSources(data.sources);
}


// START INVESTIGATION
async function startInvestigation() {
    const question = document.getElementById("question").value.trim();

    const urls = Array.from(document.querySelectorAll(".source-url"))
        .map(input => input.value.trim())
        .filter(Boolean);

    if (!question) {
        alert("Please enter your research question.");
        return;
    }

    if (urls.length === 0) {
        alert("Please provide at least one real source URL.");
        return;
    }

    if (urls.length > 8) {
        alert("Maximum 8 source URLs allowed.");
        return;
    }

    for (const url of urls) {
        try {
            const parsed = new URL(url);

            if (!["http:", "https:"].includes(parsed.protocol)) {
                throw new Error();
            }
        } catch {
            alert("Please enter valid HTTP or HTTPS source URLs.");
            return;
        }
    }

    const uniqueUrls = [...new Set(urls)];

    showPage("investigation-page");

    const status = document.getElementById("investigation-status");
    const errorBox = document.getElementById("investigation-error");

    errorBox.classList.add("hidden");
    status.textContent = "Fetching your real source material...";

    try {
        const response = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: question,
                urls: uniqueUrls
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Investigation could not be completed.");
        }

        investigationData = data;
        displayReport(data);

        status.textContent = "Investigation completed.";
        showPage("report-page");

    } catch (error) {
        status.textContent = "Investigation could not be completed.";
        errorBox.textContent = error.message || "An unexpected error occurred.";
        errorBox.classList.remove("hidden");
    }
}


// INITIAL PAGE
document.addEventListener("DOMContentLoaded", () => {
    pageHistory = [];
    currentPage = "home-page";
    showPage("home-page");
});
