---
name: perplexity
description: Web search and research using Perplexity AI. Use when user says "search", "find", "look up", "ask", "research", or "what's the latest" for generic queries. NOT for library/framework docs (use Context7) or workspace questions.
---

# Perplexity Tools

Use this skill only for generic web search and current-information questions.

Do not use this skill for:
- Library/framework documentation (use Context7)
- Graphite `gt` CLI questions (use Graphite MCP)
- Current workspace repository questions (use Nx MCP)

## Tool Name Mapping (Critical)

Use the exact tool names available in the runtime.

Common names:
- Perplexity Search: `mcp__perplexity__perplexity_search`
- Perplexity Ask: `mcp__perplexity__perplexity_ask`
- Perplexity Deep Research: `mcp__perplexity__perplexity_deep_research`
- Forbidden here: `mcp__perplexity__perplexity_research`

If the runtime exposes different names, use those exact names and keep the same decision logic.

## Decision Matrix

Use Perplexity Search when:
- User asks to search/find/look up recent or general web info
- User needs result links or source discovery

Use Perplexity Ask when:
- User asks for a synthesized explanation from current web context
- Links are less important than a direct answer

Use Perplexity Deep Research when:
- User explicitly asks for deep, multi-source research
- The question requires broad, high-confidence synthesis
- The deep research MCP tool is available

Use researcher agent (`/research <topic>`) when:
- Deep research MCP tool is unavailable
- You need an additional cross-check pass

Use something else (not Perplexity) when:
- Library docs/API references -> Context7
- Any `gt` mention -> Graphite MCP
- This workspace internals -> Nx MCP
- Single known URL fetch -> URL crawler tools

## Default Calls

Perplexity Search default (use first):
```typescript
mcp__perplexity__perplexity_search({
  query: "your search query",
  max_results: 3,
  max_tokens_per_page: 512
})
```

Increase only when needed:
- User requests comprehensive coverage
- Initial search is insufficient
- Topic requires wider source coverage

```typescript
mcp__perplexity__perplexity_search({
  query: "complex topic",
  max_results: 5,
  max_tokens_per_page: 1024
})
```

Perplexity Ask default:
```typescript
mcp__perplexity__perplexity_ask({
  messages: [
    {
      role: "user",
      content: "Explain how postgres advisory locks work"
    }
  ]
})
```

Perplexity Deep Research default:
```typescript
mcp__perplexity__perplexity_deep_research({
  query: "state of the art topic",
  recency: "month"
})
```

## Execution Policy

1. Classify intent before any tool call.
2. Route by priority chain below.
3. Start with minimal retrieval (`max_results: 3`).
4. Escalate limits only if needed.
5. Return concise output with citations/URLs when available.
6. If tools fail/unavailable, state that explicitly and use the next fallback.

## Tool Priority Chain

1. Context7 MCP for library/framework docs
2. Graphite MCP for any `gt` CLI question
3. Nx MCP for current workspace questions
4. Perplexity Search for generic searches
5. Perplexity Ask for conversational synthesis
6. Perplexity Deep Research for deep multi-source research
7. Built-in WebSearch as last resort

## Prohibited Tool

Never use: `mcp__perplexity__perplexity_research`

Use instead: researcher agent (`/research <topic>`)
- High token cost (often 30k to 50k)
- Better for deliberate multi-source synthesis
- Or use `mcp__perplexity__perplexity_deep_research` when available in this MCP

## Examples

Correct (Perplexity Search):
- "Find postgres migration best practices"
- "Search for React testing tutorials"
- "Look up latest trends in microservices"

Correct (Perplexity Ask):
- "Explain how postgres advisory locks work"
- "What are the trade-offs of microservices?"

Wrong (use Context7):
- "Search for React hooks documentation"
- "Find Next.js routing docs"
- "Look up Temporal workflow API"

Wrong (use Graphite MCP):
- "Search for gt stack commands"
- "Find gt branch workflow"

Wrong (use Nx MCP):
- "Search for build config" (in this workspace)
- "Find project dependencies" (in this workspace)

## Output Expectations

- Prefer short, actionable answers.
- Include links/citations for factual claims when available.
- Do not claim a web lookup happened unless a web tool was actually called.
- Keep context usage tight; avoid large dumps unless user asks.
