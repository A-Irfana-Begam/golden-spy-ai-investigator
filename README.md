# ✦ GOLDEN SPY
### AI-Assisted Information Gap Detection Platform

Golden Spy is an AI-assisted research platform that analyzes information from multiple web sources to identify potential information gaps, conflicting claims, outdated signals, and unanswered questions.

Instead of simply summarizing webpages, Golden Spy helps users understand what the available evidence supports, what remains unclear, and what needs further verification.

## 🎯 Problem Statement

Digital information is widely available, but it can be incomplete, inconsistent, or outdated. Manually comparing multiple sources takes time and makes it difficult to identify missing information and conflicting claims.

Golden Spy addresses this challenge through automated source collection and AI-assisted evidence analysis.

## 🚀 Key Features

- **Automatic Source Discovery:** Discover relevant webpages based on a research question.
- **Multiple Source Analysis:** Analyze content collected from multiple webpages.
- **Direct Answer:** Generate an answer based on the available source material.
- **Evidence Analysis:** Identify claims supported by the collected sources.
- **Information Gap Detection:** Highlight details that the available sources do not adequately explain.
- **Conflict Detection:** Identify potentially incompatible claims between sources.
- **Outdated Signal Detection:** Flag information that may require an updated source.
- **Unanswered Questions:** Identify questions that remain unresolved.
- **Verification Checklist:** Suggest follow-up tasks for checking important information.
- **Source References:** Connect findings to their source URLs.

## ⚙️ How It Works

1. **Submit a Research Question**  
   Enter a question and optionally provide webpage URLs.

2. **Collect Sources**  
   Golden Spy discovers relevant webpages and collects readable content.

3. **Analyze Evidence**  
   Gemini AI examines the extracted content and identifies supported findings and potential information gaps.

4. **Generate Investigation Report**  
   The platform presents findings, potential conflicts, outdated signals, unanswered questions, and verification tasks.

5. **Verify Findings**  
   Users can inspect original sources and manually verify AI-generated results.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| Google Gemini AI | AI-assisted evidence analysis |
| BeautifulSoup | Webpage content extraction |
| Requests | HTTP requests and source retrieval |
| HTML5 | Webpage structure |
| CSS3 | Styling and responsive design |
| JavaScript | Frontend interactions |
| Vercel | Deployment |

## 📁 Project Structure

```text
golden-spy-ai-investigator/
│
├── services/
│   ├── __init__.py
│   ├── ai_analyzer.py
│   └── source_fetcher.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── about.html
│   ├── hub.html
│   ├── index.html
│   └── investigate.html
│
├── .gitignore
├── README.md
├── app.py
└── requirements.txt
```

## 🔐 Environment Configuration

The application requires a Google Gemini API key.

Set the following environment variable in your deployment platform:

```env
GEMINI_API_KEY=your_api_key
```

Never commit API keys or secret credentials to the GitHub repository.

## ⚠️ Limitations

- Source discovery depends on search service availability.
- Some websites may block automated access or prevent content extraction.
- Analysis quality depends on the relevance and readability of collected sources.
- AI-generated findings may contain errors or miss important context.
- Potential conflicts and outdated signals require human verification.
- Golden Spy does not guarantee that every research question can be answered.

## 🔎 Important Note

Golden Spy is an information investigation and gap detection tool, not a fact-verification authority. Users should always check original sources before relying on generated findings.

## 🌟 Project Goal

To make information research more structured by helping users discover not only what available sources say, but also what information is missing, inconsistent, or still needs verification.
