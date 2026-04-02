# ChatGPT-style Enhancements for Hybrid Search System

To transform the current search-based system into a conversational, "ChatGPT-like" intelligence, we suggest the following 10 upgrades:

1.  **Session-based Conversation Memory**: Currently the AI works like a "Goldfish" and forgets the previous message. We should implement a short-term memory (last 3-5 turns) that is sent back to the LLM during generation.
2.  **Persistent Chat History (DB Logic)**: Create a `chat_messages` table in the database to store both User questions and AI answers permanently. This allows for long-term history and multi-day chat sessions.
3.  [COMPLETED] **Streaming AI Responses (SSE)**: Instead of waiting for the full block of text to arrive, we should use Server-Sent Events (SSE) to "type" the answer word-by-word in real-time. (✅ Implemented in `rag.js` and `assistant.js`)
4.  [PARTIAL] **Markdown & Syntax Highlighting**: Beautiful Markdown rendering and code blocks in AI answers. (✅ Implemented custom parser with code block "Copy" support in `rag.js`)
5.  **Multi-turn RAG (Re-querying)**: Use the chat history to "rewrite" the user's latest query before searching.
6.  **Stop / Interrupt Button**: Add a way for the user to "Stop" an AI response in the middle of generation.
7.  **Conversation Sidebar**: Build a "History Sidebar" (like ChatGPT) to switch between different chat threads.
8.  [COMPLETED] **Chat-First Input Muscle Memory**: Implement "Enter to Send" behavior to match industry-standard chat applications. (✅ Implemented in `chat_logic.js`)
9.  [PARTIAL] **AI Personality / System Prompting**: Optimized the "Expert Academic Research Assistant" system prompt across all providers. (✅ Standardized in `LLMProvider.py`)
10. **Clear/New Chat Functionality**: Provide a quick way to "Wipe the current memory" and start a clean state.

---
*Progress tracked as of April 2026*
