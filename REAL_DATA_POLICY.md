# FlowBrain Real Data Policy

To transition FlowBrain from prototype mock-ups to a secure, enterprise-grade AI Chief of Staff tool, all subsystems must strictly adhere to the following principles.

---

## 🎨 Frontend Rule: Never Render Synthetic Business Data

The client application must only display operational facts retrieved from real, authenticated user connections and database tables.

1. **No Placeholders**: Never render simulated briefings, fake metrics, dummy activity logs, or sample statistics.
2. **Contextual Empty States**: If an integration is unconnected or has not yet synced data, display clean empty states (e.g., `"No emails synced yet"`, `"Connect Gmail to begin analysis"`, `"No calendar events synced yet"`) that clearly instruct the user how to populate the view.
3. **No Synthetic Charts**: Charts must map directly to raw database quantities. If no history is found, render an appropriate "No scanning volume history found" message rather than sample sine-wave datasets.

---

## ⚙️ Backend Rule: Never Return Fabricated Analytics

The API server must act as a single source of truth for the founder's verified signals.

1. **Strict Database Bindings**: Analytics, scan activity counts, blockers list, wins, and next meeting details must be calculated dynamically via SQL queries against active tables (`emails`, `calendar_events`, etc.).
2. **No Seed/Mock Payloads**: All hardcoded "alex-founder" dummy configurations, static insights endpoints, and placeholder briefing arrays must be removed from the server routes.
3. **Real Ingestion Pipelines**: Data must flow solely from official third-party platform credentials (e.g., Google OAuth access tokens) into the local or production database, with automated token refreshing for continuous background updates.
