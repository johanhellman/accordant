# LLM Council API Documentation

This document describes the REST API surface for the LLM Council backend.

**Base URL**: `http://localhost:8001` (development)

## Overview

The LLM Council API is a FastAPI-based REST API that provides endpoints for:
- Managing conversations
- Sending messages to the council
- Streaming responses from the 3-stage deliberation process

## Authentication

Currently, no authentication is required. The API is designed for local development use.

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:5173` (default Vite dev server)
- `http://localhost:3000` (alternative frontend port)

This can be configured via environment variables (see `backend/main.py`).

## Endpoints

### Health Check

#### `GET /`

Check if the API is running.

**Response**:
```json
{
  "status": "ok",
  "service": "LLM Council API"
}
```

---

### Conversations

#### `GET /api/conversations`

List all conversations (metadata only).

**Response**: `List[ConversationMetadata]`

```json
[
  {
    "id": "uuid-string",
    "created_at": "2025-11-25T10:00:00",
    "title": "Conversation Title",
    "message_count": 5
  }
]
```

**Notes**:
- Conversations are sorted by creation time (newest first)
- Only metadata is returned, not full conversation content

---

#### `POST /api/conversations`

Create a new conversation.

**Request Body**: `{}` (empty object)

**Response**: `Conversation`

```json
{
  "id": "uuid-string",
  "created_at": "2025-11-25T10:00:00",
  "title": "New Conversation",
  "messages": []
}
```

**Notes**:
- A new UUID is generated for the conversation ID
- The conversation is persisted to `data/conversations/{id}.json`

---

#### `GET /api/conversations/{conversation_id}`

Get a specific conversation with all its messages.

**Path Parameters**:
- `conversation_id` (string): The UUID of the conversation

**Response**: `Conversation`

```json
{
  "id": "uuid-string",
  "created_at": "2025-11-25T10:00:00",
  "title": "Conversation Title",
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    },
    {
      "role": "assistant",
      "stage1": [...],
      "stage2": [...],
      "stage3": {
        "model": "gemini/gemini-2.5-pro",
        "response": "The capital of France is Paris..."
      }
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Conversation does not exist

---

#### `POST /api/conversations/{conversation_id}/message`

Send a message to the council and run the 3-stage deliberation process.

**Path Parameters**:
- `conversation_id` (string): The UUID of the conversation

**Request Body**: `SendMessageRequest`

```json
{
  "content": "What is the capital of France?"
}
```

**Response**:

```json
{
  "stage1": [
    {
      "model": "openai/gpt-5",
      "response": "The capital of France is Paris...",
      "personality_id": null,
      "personality_name": "openai/gpt-5"
    }
  ],
  "stage2": [
    {
      "model": "openai/gpt-5",
      "personality_name": "openai/gpt-5",
      "ranking": "Response A provides accurate information...\n\nFINAL RANKING:\n1. Response A\n2. Response B",
      "parsed_ranking": ["Response A", "Response B"]
    }
  ],
  "stage3": {
    "model": "gemini/gemini-2.5-pro",
    "response": "PART 1: COUNCIL REPORT\n...\n\nPART 2: FINAL ANSWER\nThe capital of France is Paris..."
  },
  "metadata": {
    "label_to_model": {
      "Response A": "openai/gpt-5",
      "Response B": "gemini/gemini-2.5-pro"
    },
    "aggregate_rankings": [
      {
        "model": "openai/gpt-5",
        "average_rank": 1.5,
        "rankings_count": 2
      }
    ]
  }
}
```

**Notes**:
- If this is the first message in the conversation, a title is automatically generated
- The user message is added to the conversation before processing
- The assistant response (with all stages) is added to the conversation after processing
- Voting history is recorded automatically
- This endpoint waits for all stages to complete before returning

**Error Responses**:
- `404 Not Found`: Conversation does not exist

---

#### `POST /api/conversations/{conversation_id}/message/stream`

Send a message and stream the 3-stage council process as Server-Sent Events (SSE).

**Path Parameters**:
- `conversation_id` (string): The UUID of the conversation

**Request Body**: `SendMessageRequest`

```json
{
  "content": "What is the capital of France?"
}
```

**Response**: `text/event-stream`

The response is a stream of Server-Sent Events. Each event has a `type` and optional `data` field:

**Event Types**:

1. `stage1_start` - Stage 1 (collecting responses) has started
   ```json
   {"type": "stage1_start"}
   ```

2. `stage1_complete` - Stage 1 has completed
   ```json
   {
     "type": "stage1_complete",
     "data": [
       {
         "model": "openai/gpt-5",
         "response": "...",
         "personality_id": null,
         "personality_name": "openai/gpt-5"
       }
     ]
   }
   ```

3. `stage2_start` - Stage 2 (collecting rankings) has started
   ```json
   {"type": "stage2_start"}
   ```

4. `stage2_complete` - Stage 2 has completed
   ```json
   {
     "type": "stage2_complete",
     "data": [...],
     "metadata": {
       "label_to_model": {...},
       "aggregate_rankings": [...]
     }
   }
   ```

5. `stage3_start` - Stage 3 (synthesizing final answer) has started
   ```json
   {"type": "stage3_start"}
   ```

6. `stage3_complete` - Stage 3 has completed
   ```json
   {
     "type": "stage3_complete",
     "data": {
       "model": "gemini/gemini-2.5-pro",
       "response": "..."
     }
   }
   ```

7. `title_complete` - Title generation has completed (only for first message)
   ```json
   {
     "type": "title_complete",
     "data": {
       "title": "Capital of France"
     }
   }
   ```

8. `complete` - All processing is complete
   ```json
   {"type": "complete"}
   ```

9. `error` - An error occurred
   ```json
   {
     "type": "error",
     "message": "Error description"
   }
   ```

**Notes**:
- Events are sent as they occur, allowing real-time UI updates
- The conversation is updated in the background as stages complete
- Title generation runs in parallel with Stage 1 (for first message only)
- Use EventSource API in JavaScript to consume this stream

**Example JavaScript Usage**:
```javascript
const eventSource = new EventSource(
  `/api/conversations/${conversationId}/message/stream`,
  {
    method: 'POST',
    body: JSON.stringify({ content: 'Hello' })
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'stage1_complete':
      // Update UI with Stage 1 results
      break;
    case 'stage2_complete':
      // Update UI with Stage 2 results
      break;
    case 'stage3_complete':
      // Update UI with final answer
      break;
  }
};
```

**Error Responses**:
- `404 Not Found`: Conversation does not exist
- Error events are sent in the stream if processing fails

---

## Data Models

### ConversationMetadata

```typescript
{
  id: string;              // UUID
  created_at: string;      // ISO 8601 timestamp
  title: string;            // Conversation title
  message_count: number;    // Number of messages
}
```

### Conversation

```typescript
{
  id: string;               // UUID
  created_at: string;       // ISO 8601 timestamp
  title: string;            // Conversation title
  messages: Message[];      // Array of messages
}
```

### Message

User message:
```typescript
{
  role: "user";
  content: string;
}
```

Assistant message:
```typescript
{
  role: "assistant";
  stage1: Stage1Result[];
  stage2: Stage2Result[];
  stage3: Stage3Result;
}
```

### Stage1Result

```typescript
{
  model: string;                    // OpenRouter model identifier
  response: string;                 // Model's response text
  personality_id: string | null;    // Personality ID (if using personalities)
  personality_name: string | null; // Personality name (if using personalities)
}
```

### Stage2Result

```typescript
{
  model: string;                    // OpenRouter model identifier
  personality_name: string | null;  // Personality name (if using personalities)
  ranking: string;                  // Full ranking text from model
  parsed_ranking: string[];         // Extracted ranking labels (e.g., ["Response A", "Response B"])
}
```

### Stage3Result

```typescript
{
  model: string;  // Chairman model identifier
  response: string; // Final synthesized answer (includes PART 1: COUNCIL REPORT and PART 2: FINAL ANSWER)
}
```

### SendMessageRequest

```typescript
{
  content: string; // User's message content
}
```

### Metadata

```typescript
{
  label_to_model: { [label: string]: string }; // Maps "Response A" to model name
  aggregate_rankings: AggregateRanking[];      // Average rankings across all voters
}
```

### AggregateRanking

```typescript
{
  model: string;        // Model name
  average_rank: number; // Average position (lower is better)
  rankings_count: number; // Number of votes received
}
```

---

## Error Handling

All endpoints may return standard HTTP error codes:

- `400 Bad Request`: Invalid request body or parameters
- `404 Not Found`: Resource (conversation) does not exist
- `500 Internal Server Error`: Server error during processing

Error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

For streaming endpoints, errors are sent as SSE events with `type: "error"`.

---

## Rate Limiting

Currently, no rate limiting is implemented. The API uses a semaphore to limit concurrent LLM API requests (configurable via `MAX_CONCURRENT_REQUESTS` environment variable, default: 4).

---

## Notes

- All timestamps are in UTC and ISO 8601 format
- Conversation IDs are UUIDs (v4)
- The API is stateless except for conversation storage
- Metadata (label_to_model, aggregate_rankings) is ephemeral and only returned in API responses, not persisted
- See `backend/main.py` for implementation details
- See `docs/adr/` for architectural decisions

---

## Admin API

### Models

#### `GET /api/models`

List available models from the configured provider.

**Response**: `List[ModelInfo]`

```json
[
  {
    "id": "openai/gpt-4",
    "name": "GPT-4",
    "provider": "openai"
  }
]
```

### Personalities

#### `GET /api/personalities`

List all personalities.

**Response**: `List[Personality]`

#### `POST /api/personalities`

Create a new personality.

**Request Body**: `Personality`

#### `GET /api/personalities/{id}`

Get a specific personality.

#### `PUT /api/personalities/{id}`

Update a personality.

**Request Body**: `Personality`

#### `DELETE /api/personalities/{id}`

Delete a personality.

### System Prompts

#### `GET /api/system-prompts`

Get current system prompts and configuration.

**Response**:
```json
{
  "base_system_prompt": "...",
  "chairman_prompt": "...",
  "title_generation_prompt": "...",
  "chairman_model": "openai/gpt-4",
  "title_generation_model": "openai/gpt-3.5-turbo"
}
```

#### `PUT /api/system-prompts`

Update system prompts and configuration.

**Request Body**: Same as GET response.

