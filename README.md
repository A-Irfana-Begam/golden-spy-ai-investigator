# ✦ GOLDEN SPY
### Information Gap Detection Platform

Golden Spy is a web-based research platform that analyzes information collected from multiple web sources to highlight potential information gaps, source-supported findings, and unanswered questions.

Instead of simply summarizing webpages, Golden Spy helps users understand what the collected sources mention, what remains unclear, and what needs further verification.

## 🎯 Problem Statement

Digital information can be incomplete, inconsistent, or outdated. Comparing multiple sources manually takes time and makes it difficult to identify missing details and areas that require further investigation.

Golden Spy aims to make this process more structured through automated source collection and local rule-based evidence analysis.

## 🚀 Key Features

- **Automatic Source Discovery:** Find relevant webpages based on a research question.
- **Multiple Source Analysis:** Collect and examine content from multiple webpages.
- **Source-Supported Information:** Highlight text from collected sources that matches the research question.
- **Information Gap Detection:** Identify sources that do not contain clearly relevant information.
- **Topical Cross-Source Comparison:** Highlight overlapping keywords across different sources.
- **Unanswered Questions:** Indicate when the collected sources do not provide clearly relevant information.
- **Verification Checklist:** Suggest follow-up tasks for manually checking findings.
- **Source References:** Display the URLs used during the investigation.
- **API-Key-Free Operation:** Perform analysis locally without requiring an external AI API.

## ⚙️ How It Works

1. **Submit a Research Question**  
   Enter a question and optionally provide webpage URLs.

2. **Collect Sources**  
   Golden Spy discovers relevant webpages and extracts readable content.

3. **Analyze Information**  
   The local rule-based engine uses keyword matching and text comparison to identify relevant passages and potential information gaps.

4. **Generate an Investigation Report**  
   The platform presents source-supported information, topical overlaps, information gaps, unanswered questions, and verification tasks.

5. **Verify Findings**  
   Users inspect the original sources and manually verify the collected information.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| Requests | HTTP requests and source retrieval |
| BeautifulSoup | Webpage content extraction |
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

## 💻 Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/A-Irfana-Begam/golden-spy-ai-investigator.git
cd golden-spy-ai-investigator
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Start the application**

```bash
python app.py
```

**4. Open in your browser**

```text
http://127.0.0.1:5000
```

## 🔐 Configuration

Golden Spy does not require an external AI API key or API credentials.

The analysis is performed using a local rule-based engine.

## ⚠️ Limitations

- Source discovery depends on the availability of the search service.
- Some websites may block automated access or prevent content extraction.
- Analysis depends on the relevance and readability of collected webpage content.
- Keyword-based matching cannot fully understand context or meaning.
- Topical overlap does not prove that sources independently confirm a claim.
- The current engine does not reliably detect contradictions or determine whether information is outdated.
- Findings require manual verification using original sources.

## 🔎 Important Note

Golden Spy is an information investigation and gap detection tool, not a fact-verification authority or an AI-powered analysis system. Its findings are preliminary signals generated through rule-based text analysis. Always consult original sources before relying on them.

## 🌟 Project Goal

To make information research more structured by helping users identify relevant information, recognize possible gaps, compare source content, and determine what still needs verification.
