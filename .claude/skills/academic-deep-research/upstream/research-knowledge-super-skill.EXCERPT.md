---
name: research-knowledge-super-skill
description: Comprehensive research and knowledge management skill merging Perplexity Computer's research, data exploration, statistical analysis, and visualization skills with Claude Code's tapestry knowledge graphs, article extraction, content research, brainstorming, RAG system building, and prompt engineering. Covers deep research workflows, knowledge graph construction, academic research, data analysis, statistical methods, content synthesis, and AI-powered information retrieval. Use for research projects, literature reviews, data analysis, knowledge management, competitive research, or any investigation requiring deep synthesis.
license: MIT
metadata:
  author: get-zeked
  version: '1.0'
---

# Research & Knowledge Super-Skill

A unified research and knowledge management system merging deep research workflows, data profiling, statistical methods, visualization, knowledge graph construction, content extraction, RAG systems, brainstorming, and iterative learning into a single actionable playbook.

---

## Table of Contents

1. [Gap Analysis: Perplexity Computer vs Claude Code Skills](#1-gap-analysis-perplexity-computer-vs-claude-code-skills)
2. [Research Methodology & Workflows](#2-research-methodology--workflows)
3. [Knowledge Graph Construction](#3-knowledge-graph-construction)
4. [Content Extraction & Synthesis](#4-content-extraction--synthesis)
5. [Data Exploration & Profiling](#5-data-exploration--profiling)
6. [Statistical Analysis & Methods](#6-statistical-analysis--methods)
7. [Data Visualization & Communication](#7-data-visualization--communication)
8. [Data Validation & Quality Assurance](#8-data-validation--quality-assurance)
9. [Creative Ideation & Brainstorming](#9-creative-ideation--brainstorming)
10. [RAG Systems & AI-Powered Research](#10-rag-systems--ai-powered-research)
11. [Iterative Learning & Feedback](#11-iterative-learning--feedback)
12. [Unique Perplexity Computer Capabilities](#12-unique-perplexity-computer-capabilities)
13. [Research Templates & Frameworks](#13-research-templates--frameworks)

---

## 1. Gap Analysis: Perplexity Computer vs Claude Code Skills

Understanding where each platform excels helps route tasks to the right approach.

| Capability | Perplexity Computer | Claude Code (Tapestry ecosystem) | Combined Advantage |
|---|---|---|---|
| **Live web search** | Native, real-time, multi-source | None (static training data) | Perplexity for current facts |
| **Academic search** | Dedicated academic vertical | None natively | Perplexity for papers/citations |
| **Social media search** | X/Twitter search built-in | None | Perplexity for trend monitoring |
| **Knowledge graph construction** | Not native | Tapestry skill (linked entities from docs) | Claude for local doc synthesis |
| **Article extraction** | fetch_url with LLM processing | article-extractor + reader/trafilatura tools | Both; Claude tools for batch processing |
| **YouTube transcript extraction** | No yt-dlp; fetch transcript endpoint | yt-dlp + VTT deduplication pipeline | Claude for video corpus |
| **Data exploration (CSV/SQL)** | Full Python/SQL environment | Bash tools | Perplexity for live analysis |
| **Statistical analysis** | Full scipy/statsmodels/numpy | Limited to scripting | Perplexity for serious stats |
| **Data visualization** | matplotlib/seaborn/plotly | Bash + Python scripts | Perplexity produces rendered charts |
| **Brainstorming/design** | Can brainstorm; no hard-gate | Hard-gate design-before-code discipline | Claude for disciplined ideation |
| **RAG evaluation** | Can build/evaluate RAG pipelines | rag_evaluator.py scripts | Both; different strengths |
| **Prompt engineering** | Inline; no dedicated optimizer | prompt_optimizer.py scripts | Claude for systematic optimization |
| **Iterative learning plans** | Not native | Ship-Learn-Next planner | Claude for action plan generation |
| **External integrations** | 400+ connected services | File system / local tools | Perplexity for live external data |
| **Multi-agent parallelism** | Subagent spawning | Single conversation | Perplexity for parallel research |
| **Memory across sessions** | memory_search tool | CLAUDE.md / project context | Perplexity for persistent memory |
| **Content calendar / SEO** | Not native | content-creator skill | Claude for content workflows |
| **PDF processing** | pdf skill (extract, merge, OCR) | pdftotext via bash | Perplexity for richer PDF manipulation |

**Routing Decision Rule**:
- Current information, live data, external APIs → **Perplexity Computer**
- Local file corpus, video transcripts, iterative plans, prompt tuning → **Claude Code**
- Statistical analysis, visualization, data validation → **Perplexity Computer** (full Python env)
- Knowledge graph from your documents, action planning, RAG evaluation → **Claude Code**

---

## 2. Research Methodology & Workflows

### 2.1 The Research Hierarchy

Before launching any research task, establish the question tier:

| Tier | Question Type | Approach |
|---|---|---|
| **Tier 1** | Single verifiable fact | One search; cite source |
| **Tier 2** | Comparative analysis | Parallel searches; synthesis table |
| **Tier 3** | Investigative / exploratory | Iterative search; subagent parallelism |
| **Tier 4** | Literature review / meta-analysis | Academic search; citation network |
| **Tier 5** | Strategic intelligence | Competitive research; 400+ integrations |

### 2.2 Deep Research Workflow (Perplexity Computer)

This workflow applies to Tier 3–5 questions requiring synthesis across many sources.

#### Phase 1: Orientation (5–10 minutes)
1. **Formulate 3 seed queries** — broad, medium, and specific versions of the question
2. **Run parallel searches** — use `search_web` with all three queries simultaneously
3. **Identify authoritative sources** — note publishers, institutions, primary data owners
4. **Map the knowledge landscape** — what is known, disputed, unknown, or recent?

#### Phase 2: Deep Dive (15–45 minutes)
1. **Fetch primary sources** — use `fetch_url` on authoritative URLs (not aggregators)
2. **Cross-reference claims** — any fact cited by only one source is provisional
3. **Academic layer** — use `search_vertical(vertical="academic")` for peer-reviewed material
4. **Social layer** — use `search_social` for real-time discourse and emerging viewpoints
5. **Save intermediate findings** — write structured notes with source URLs to workspace

#### Phase 3: Synthesis (10–20 minutes)
1. **Build a claims registry** — list all factual assertions with their source strength
2. **Identify consensus vs. contested areas** — where do sources agree vs. diverge?
3. **Flag recency of information** — is this 2024 data or 2020 data?
4. **Draft the research brief** using the template in §13.1

#### Phase 4: Quality Check
1. Verify every quantitative claim against its source
2. Check that primary sources (not aggregators) are cited for key data
3. Apply the survivorship bias check: who is NOT in these sources?
4. Rate confidence: High (multiple primary sources) / Medium (one primary) / Low (secondary only)

### 2.3 Parallelized Subagent Research

For large research tasks (10+ entities, multiple regions, multi-faceted topics):

```
Master Agent Plan:
├── Subagent A: Topic domain X (searches + saves findings to workspace/research-A.json)
├── Subagent B: Topic domain Y (searches + saves findings to workspace/research-B.json)
├── Subagent C: Collect verified image/media URLs
└── Master Agent: Reads all workspace files, synthesizes, builds final artifact
```

**Rules for parallelization:**
- Each subagent writes to a unique filename (never overwrite)
- Subagents include source URLs for every fact
- Master agent does NOT re-research; only synthesizes
- Never build the final asset before all research files are complete

### 2.4 Research Continuity Across Sessions

At the start of any research-heavy task:
1. Search memory for prior work on the same topic
2. Read relevant workspace files from previous sessions
3. Build on prior findings rather than starting fresh
4. Note what changed since the last research run (date-sensitive facts)

### 4.5 Source Quality Tiers

| Tier | Type | Trust Level | Example |
|---|---|---|---|
| 1 | Peer-reviewed meta-analysis | Highest | Cochrane reviews, IPCC reports |
| 2 | Primary peer-reviewed study | Very high | Nature, NEJM, NBER working papers |
| 3 | Government / institutional data | High | BLS, Census, WHO statistics |
| 4 | Primary news reporting | Medium-high | NYT, FT, Reuters original reporting |
| 5 | Industry reports | Medium | Gartner, McKinsey, analyst reports |
| 6 | Expert blog / newsletter | Medium-low | Substack experts, trade publications |
| 7 | General blog / forum | Low | Reddit, Medium, general blogs |
| 8 | Social media post | Very low | Twitter/X, Facebook, TikTok |

**Rule**: Never cite Tier 6–8 sources as the sole basis for a factual claim. Always cross-reference to Tier 1–5.

---

