# NeuroLink Installation Guide for LLM Wiki

[NeuroLink](https://github.com/juspay/neurolink) is a universal AI integration platform that unifies 30+ LLM providers under a single consistent API. This guide shows how to integrate NeuroLink with LLM Wiki for multi-provider support.

## Installation

### Prerequisites

- Node.js 16+ (for TypeScript environment)
- Existing LLM Wiki installation
- Package manager: npm, yarn, or pnpm

### Install NeuroLink

Using pnpm (recommended):

```bash
cd your-wiki-directory
pnpm add @juspay/neurolink
```

Using npm:

```bash
npm install @juspay/neurolink
```

Using yarn:

```bash
yarn add @juspay/neurolink
```

## Integration with LLM Wiki

### 1. Configure Provider API Keys

Set up environment variables for your preferred providers:

```bash
# .env or export in your shell
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### 2. Create a NeuroLink Configuration File

Create `neurolink.config.json` in your wiki root:

```json
{
  "defaultProvider": "anthropic",
  "providers": [
    "anthropic",
    "openai",
    "google"
  ],
  "fallbackChain": [
    "claude-3-opus",
    "gpt-4",
    "gemini-pro"
  ],
  "models": {
    "ingest": "claude-3-opus",
    "search": "gpt-4",
    "synthesis": "claude-3-opus"
  },
  "timeout": 30000,
  "retryPolicy": {
    "maxRetries": 3,
    "backoffMultiplier": 2
  }
}
```

### 3. Initialize NeuroLink in Your Agent

In your agent initialization (typically in `AGENTS.md` or your agent configuration):

```javascript
import { NeuroLink } from '@juspay/neurolink';

const neurolink = new NeuroLink({
  configPath: './neurolink.config.json',
  providers: ['anthropic', 'openai', 'google'],
  apiKeys: {
    anthropic: process.env.ANTHROPIC_API_KEY,
    openai: process.env.OPENAI_API_KEY,
    google: process.env.GOOGLE_API_KEY,
  }
});

// Use for ingest operations
export const ingestWithNeuroLink = async (content) => {
  return await neurolink.chat.completions.create({
    messages: [
      { role: 'system', content: 'You are a wiki maintenance agent...' },
      { role: 'user', content }
    ],
    model: 'claude-3-opus',
    fallbackTo: ['gpt-4', 'gemini-pro'],
  });
};

// Use for search synthesis
export const synthesizeWithNeuroLink = async (query, context) => {
  return await neurolink.chat.completions.create({
    messages: [
      { role: 'system', content: 'Synthesize wiki content...' },
      { role: 'user', content: `Query: ${query}\n\nContext: ${context}` }
    ],
    model: 'auto', // Let NeuroLink choose
    selectProvider: 'cost-effective',
  });
};
```

### 4. Integration with MCP Servers

NeuroLink integrates with MCP servers, which works well with LLM Wiki's MCP architecture:

```json
{
  "mcpServers": {
    "wiki-filesystem": {
      "command": "python",
      "args": ["-m", "mcp.server.filesystem", "./wiki"],
      "env": {}
    },
    "neurolink-provider": {
      "command": "node",
      "args": ["./neurolink-mcp-bridge.js"],
      "env": {
        "NEUROLINK_CONFIG": "./neurolink.config.json"
      }
    }
  }
}
```

## Use Cases for LLM Wiki

### 1. Multi-Provider Ingest

Use different providers for different ingest operations:

```javascript
// Fast, cost-effective ingest for simple sources
const fastIngest = await neurolink.chat.completions.create({
  messages: [{ role: 'user', content: sourceContent }],
  model: 'gpt-3.5-turbo', // Faster, cheaper
  selectProvider: 'cheapest',
});

// Complex analysis for technical sources
const complexIngest = await neurolink.chat.completions.create({
  messages: [{ role: 'user', content: sourceContent }],
  model: 'claude-3-opus', // More capable
  selectProvider: 'most-capable',
});
```

### 2. Resilient Synthesis

Ensure synthesis operations complete even if one provider fails:

```javascript
const synthesis = await neurolink.chat.completions.create({
  messages: [
    { role: 'system', content: 'Generate wiki synthesis...' },
    { role: 'user', content: synthesisPrompt }
  ],
  model: 'gpt-4',
  fallbackTo: ['claude-3-opus', 'gemini-pro'],
  maxRetries: 3,
});
```

### 3. Cross-Provider Consistency

Validate wiki updates with multiple providers:

```javascript
const [anthropicResult, openaiResult, googleResult] = await Promise.allSettled([
  neurolink.chat.completions.create({
    messages: [{ role: 'user', content: 'Validate this wiki update...' }],
    model: 'claude-3-opus',
    provider: 'anthropic',
  }),
  neurolink.chat.completions.create({
    messages: [{ role: 'user', content: 'Validate this wiki update...' }],
    model: 'gpt-4',
    provider: 'openai',
  }),
  neurolink.chat.completions.create({
    messages: [{ role: 'user', content: 'Validate this wiki update...' }],
    model: 'gemini-pro',
    provider: 'google',
  })
]);
```

## Supported Providers for LLM Wiki

NeuroLink supports 30+ providers, including:

| Provider | Best For | Models |
|----------|----------|--------|
| **Anthropic** | Complex reasoning, reliable output | Claude 3 Opus, Sonnet, Haiku |
| **OpenAI** | Vision, diverse use cases | GPT-4, GPT-4 Vision, GPT-3.5 |
| **Google** | Multimodal, cost-effective | Gemini Pro, Palm 2 |
| **AWS Bedrock** | Enterprise, self-hosted | Claude, Mistral, Llama |
| **Mistral** | Speed, cost optimization | Mistral Large, Medium |
| **Groq** | Real-time, speed-critical | Mixtral, Llama |

## Advanced Configuration

### Cost Optimization

```json
{
  "costOptimization": {
    "enabled": true,
    "targetCost": "minimal",
    "trackedMetrics": ["tokens", "latency", "cost"]
  },
  "providers": [
    {
      "name": "openai",
      "costPerMtkToken": 0.00001,
      "costPerPromptToken": 0.000003
    },
    {
      "name": "anthropic",
      "costPerMtkToken": 0.0000075,
      "costPerPromptToken": 0.000003
    }
  ]
}
```

### Observability with OpenTelemetry

```json
{
  "observability": {
    "enabled": true,
    "otelEndpoint": "http://localhost:4317",
    "tracingSampleRate": 0.1,
    "metricsInterval": 60000
  }
}
```

### Context Window Management

```javascript
// Automatically manage large wiki documents
const response = await neurolink.chat.completions.create({
  messages: wikiMessages,
  model: 'claude-3-opus',
  contextCompaction: {
    enabled: true,
    strategy: 'summarize',
    maxTokens: 200000,
  }
});
```

## CLI Usage

Use NeuroLink CLI directly with wiki operations:

```bash
# Check available providers
npx @juspay/neurolink providers list

# Test provider connectivity
npx @juspay/neurolink test --provider anthropic

# Query a provider
npx @juspay/neurolink chat --provider gpt-4 "Analyze this wiki structure"

# Estimate costs
npx @juspay/neurolink cost --query "ingest 1000 pages" --providers anthropic,openai,google
```

## Troubleshooting

### Provider Authentication Issues

```bash
# Verify API keys are set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Set them if missing
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### Fallback Chain Not Working

Ensure all providers in fallback chain have valid API keys:

```javascript
// Check which providers are configured
const client = new NeuroLink({ configPath: './neurolink.config.json' });
console.log(client.getAvailableProviders());
```

### High Latency

Use cost-optimized providers for non-critical operations:

```javascript
// For fast responses, use Groq or smaller models
const response = await neurolink.chat.completions.create({
  messages: [{ role: 'user', content: 'Quick summary' }],
  model: 'auto',
  selectProvider: 'fastest', // Prioritize latency
  timeout: 10000,
});
```

## Example: Complete LLM Wiki + NeuroLink Setup

```bash
# 1. Initialize wiki
wiki init my-ai-wiki --git
cd my-ai-wiki

# 2. Install NeuroLink
pnpm add @juspay/neurolink

# 3. Configure
cat > neurolink.config.json << EOF
{
  "defaultProvider": "anthropic",
  "providers": ["anthropic", "openai", "google"],
  "fallbackChain": ["claude-3-opus", "gpt-4", "gemini-pro"]
}
EOF

# 4. Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# 5. Initialize wiki
wiki init-check

# 6. Add a source
cp ~/Downloads/article.md raw/

# 7. Tell agent to ingest with NeuroLink
# "Ingest raw/article.md using NeuroLink for multi-provider resilience"
```

## Resources

- [NeuroLink GitHub](https://github.com/juspay/neurolink)
- [NeuroLink Documentation](https://github.com/juspay/neurolink#readme)
- [LLM Wiki Documentation](https://github.com/cobusgreyling/llm-wiki)
- [Supported Models](https://github.com/juspay/neurolink/blob/main/docs/MODELS.md)

## Next Steps

1. **Set up environment variables** for your preferred providers
2. **Configure neurolink.config.json** in your wiki directory
3. **Update your agent** to use NeuroLink for ingest and synthesis
4. **Test with a simple source** to verify multi-provider fallback
5. **Monitor costs** using NeuroLink's built-in cost tracking

For more information, see the [NeuroLink GitHub repository](https://github.com/juspay/neurolink).
