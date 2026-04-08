# DRY Architecture & Hardening Roadmap

This document outlines the strategic steps to transition the Hybrid Search codebase toward a more modular, "Don't Repeat Yourself" (DRY) architecture.

## 1. API Service Layer (`/static/services/api.js`)
Currently, `fetch` calls are scattered across `deleteRecord.js`, `search_dynamic.js`, and `assistant.js`.
- **Action**: Centralize all backend communication into a single utility.
- **Benefit**: Standardized error handling, automatic loading state management, and easier transition to newer API versions.

## 2. Global Modal Manager (`/static/utils/modal_manager.js`)
We are currently manually manipulating the DOM (swapping titles, icons, and buttons) each time we use the `quickDeleteModal`.
- **Action**: Create a `ModalController` that accepts a JSON configuration (e.g., `{ title: '...', icon: '...', onConfirm: ... }`).
- **Benefit**: Eliminates redundant DOM selection code and prevents "state leakage" (where old text persists in a new modal instance).

## 3. UI/UX State Sync (`/static/utils/state_manager.js`)
Control states (Search Mode, AI Toggle, LTR setting) are currently managed via fragmented `localStorage` calls and manual form inputs.
- **Action**: Implement a "Single Source of Truth" that automatically synchronizes the DOM, LocalStorage, and the URL parameters.
- **Benefit**: Guarantees that the UI always matches the URL and the user's saved preferences across refreshes without repetitive sync logic.

## 4. CSS Design Tokens & Components (`/static/css/components/`)
Many premium UI elements (modals, cards, badges) use inline styles or ad-hoc classes.
- **Action**: Extract repeated styles (border-radius: 12px, shadow layouts, etc.) into a "Core Library" of CSS tokens and utility classes.
- **Benefit**: Ensures a perfectly consistent aesthetic across the app and makes creating new components 3x faster.

## 5. Template Modularization (`/templates/components/`)
Main templates like `chat_base.html` are becoming complex through deep nesting.
- **Action**: Continue fragmenting the UI into small, focused components (e.g., `search_input.html`, `results_list.html`).
- **Benefit**: Improved readability and much faster manual audits.
