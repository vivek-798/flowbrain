import os
import litellm
import json
import time
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.core.config import settings

class BriefingProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def generate(self, context: str, system_prompt: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the briefing dictionary.
        Raises an exception if any failure occurs (API failure, parsing error, or schema validation issue).
        """
        pass


def _is_transient_error(e: Exception) -> bool:
    err_str = str(e).lower()
    
    # Check status code if present
    status_code = getattr(e, "status_code", None)
    if status_code in [401, 403, 429]:
        return False
        
    # Rate limit keywords
    if "429" in err_str or "rate limit" in err_str:
        return False
        
    # Auth keywords
    if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "permission" in err_str:
        return False

    # 1. 503 Service Unavailable
    if status_code == 503:
        return True
    if "503" in err_str or "serviceunavailable" in err_str.replace(" ", "") or "service unavailable" in err_str:
        return True
        
    # 2. Timeout / connection issues
    class_name = e.__class__.__name__.lower()
    if "timeout" in class_name or "connection" in class_name or "connect" in class_name:
        return True
    if "timeout" in err_str or "timed out" in err_str or "connection" in err_str:
        return True
            
    return False


def _parse_and_validate_ai_response(content: str) -> Dict[str, Any]:
    content_str = content.strip()
    if content_str.startswith("```"):
        lines = content_str.split("\n")
        if lines[0].startswith("```json"):
            content_str = "\n".join(lines[1:-1])
        elif lines[0].startswith("```"):
            content_str = "\n".join(lines[1:-1])
            
    try:
        parsed = json.loads(content_str.strip())
    except Exception as e:
        raise ValueError(f"Failed to parse response as JSON: {str(e)}")
        
    if not isinstance(parsed, dict):
        raise ValueError("AI response is not a JSON object/dictionary.")
        
    required_fields = ["headline", "red", "amber", "green", "focus", "ignored_count"]
    missing = [f for f in required_fields if f not in parsed]
    if missing:
        raise KeyError(f"AI response is missing required JSON fields: {', '.join(missing)}")
        
    print("ACTIONS FROM GEMINI:", json.dumps(
        parsed.get("actions", []), indent=2
    ))
        
    return parsed


class GeminiProvider(BriefingProvider):
    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return settings.MODEL  # gemini/gemini-2.5-flash

    def generate(self, context: str, system_prompt: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key or "mock" in api_key.lower():
            raise ValueError("Gemini API key is not configured or is a mock key.")
            
        print(f"[GeminiProvider] Sending context to Gemini using {self.model_name}...", flush=True)
        response = litellm.completion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the real operational data from the founder's integrations:\n\n{context}"}
            ],
            api_key=api_key
        )
        content = response.choices[0].message.content
        print("[GeminiProvider] AI Response received.", flush=True)
        return _parse_and_validate_ai_response(content)


class ClaudeProvider(BriefingProvider):
    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def model_name(self) -> str:
        return "anthropic/claude-3-haiku-20240307"

    def generate(self, context: str, system_prompt: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key or "mock" in api_key.lower():
            raise ValueError("Anthropic API key is not configured or is a mock key.")
            
        print(f"[ClaudeProvider] Sending context to Claude using {self.model_name}...", flush=True)
        response = litellm.completion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the real operational data from the founder's integrations:\n\n{context}"}
            ],
            api_key=api_key
        )
        content = response.choices[0].message.content
        print("[ClaudeProvider] AI Response received.", flush=True)
        return _parse_and_validate_ai_response(content)


class AlgorithmicProvider(BriefingProvider):
    @property
    def provider_name(self) -> str:
        return "algorithmic"

    @property
    def model_name(self) -> str:
        return "internal-heuristics"

    def generate(self, context: str, system_prompt: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        print("[AlgorithmicProvider] Running heuristic fallback...", flush=True)
        return AIService._generate_algorithmic_briefing(user_data)


class AIService:
    @staticmethod
    def is_noise_email(email: Dict[str, Any]) -> bool:
        """
        Check if an email is a generic automated notification/noise email.
        """
        subject = (email.get("subject") or "").lower()
        sender = (email.get("sender") or "").lower()
        snippet = (email.get("snippet") or "").lower()
        
        noise_keywords = [
            "deploy", "sign-in", "security", "build", "authorized", 
            "newsletter", "subscription", "notification", "github", "vercel",
            "privacy policy", "terms of service", "we've updated our", 
            "policy update", "terms and conditions"
        ]
        noise_senders = ["vercel", "github", "noreply", "no-reply", "alert", "security"]
        
        text_to_scan = f"{subject} {sender} {snippet}"
        if any(nk in text_to_scan for nk in noise_keywords):
            return True
        if any(ns in sender for ns in noise_senders):
            return True
            
        return False

    @staticmethod
    def _build_compressed_context(user_data: Dict[str, Any]) -> str:
        """
        Builds a compressed context string using RiskEngine and SignalExtractor.
        Omits raw email bodies entirely and truncates context to fit under token limits.
        """
        from app.services.ai.risk_engine import ProjectRiskEngine
        from app.services.ai.signal_extractor import SignalExtractor
        
        emails = user_data.get("emails", [])
        events = user_data.get("calendar_events", [])
        business_context = user_data.get("business_context") or {}
        
        # 1. Score projects using ProjectRiskEngine (Top 10)
        raw_projects = business_context.get("projects", [])
        scored_projects = ProjectRiskEngine.score_projects(raw_projects)
        
        # 2. Extract signals using SignalExtractor (Top 20)
        extracted_signals = SignalExtractor.extract_signals_from_emails(emails, business_context)
        
        # Diagnostics values
        emails_scanned = len(emails)
        signals_extracted = len(extracted_signals)
        projects_scored = len(raw_projects)
        
        context_parts = []
        
        # 3. Build BusinessContext section
        context_parts.append("=== BUSINESS CONTEXT ===")
        biz_type = business_context.get("business_type") or "Not specified"
        context_parts.append(f"Business Type: {biz_type}\n")
        
        context_parts.append("Clients:")
        clients = business_context.get("clients", [])
        if not clients:
            context_parts.append("  No clients configured.")
        else:
            for c in clients:
                notes_str = f" | Notes: {c.get('notes')}" if c.get('notes') else ""
                context_parts.append(f"  - Name: {c.get('name')} | Value: INR {c.get('value_inr')} | Status: {c.get('status')}{notes_str}")
        context_parts.append("")
        
        context_parts.append("Team Members:")
        team = business_context.get("team_members", [])
        if not team:
            context_parts.append("  No team members configured.")
        else:
            for t in team:
                email_str = f" ({t.get('email')})" if t.get('email') else ""
                context_parts.append(f"  - Name: {t.get('name')}{email_str} | Role: {t.get('role')}")
        context_parts.append("")
        
        # 4. Inject scored projects (Top 10)
        context_parts.append("=== ACTIVE PROJECTS (TOP 10 BY RISK SCORE) ===")
        if not scored_projects:
            context_parts.append("  No active projects configured.")
        else:
            for idx, p in enumerate(scored_projects, 1):
                context_parts.append(
                    f"  {idx}. Project: {p.get('name')} | Client: {p.get('client_name')} | Value: INR {p.get('value_inr')} | "
                    f"Deadline: {p.get('deadline')} | Completion: {p.get('completion_percent')}% | Status: {p.get('status')} | "
                    f"Risk Level: {p.get('risk_level')} (Score: {p.get('risk_score')})"
                )
        context_parts.append("")
        
        # 5. Inject extracted signals (Top 20)
        context_parts.append("=== BUSINESS SIGNALS (TOP 20 EXTRACTED FROM EMAILS) ===")
        if not extracted_signals:
            context_parts.append("  No relevant business signals extracted from emails.")
        else:
            for idx, sig in enumerate(extracted_signals, 1):
                urgency = ", ".join(sig["urgency_indicators"]) if sig["urgency_indicators"] else "none"
                payment = ", ".join(sig["payment_references"]) if sig["payment_references"] else "none"
                clients_str = ", ".join(sig["matched_clients"]) if sig["matched_clients"] else "none"
                proj_str = ", ".join(sig["matched_projects"]) if sig["matched_projects"] else "none"
                deadlines_str = ", ".join(sig["extracted_deadlines"]) if sig["extracted_deadlines"] else "none"
                
                context_parts.append(
                    f"Signal #{idx}:\n"
                    f"  Subject: {sig['subject']}\n"
                    f"  Sender: {sig['sender']}\n"
                    f"  Date: {sig['received_at']}\n"
                    f"  Unread: {sig['is_unread']}\n"
                    f"  Urgency Indicators: {urgency}\n"
                    f"  Payment References: {payment}\n"
                    f"  Matched Clients: {clients_str}\n"
                    f"  Matched Projects: {proj_str}\n"
                    f"  Extracted Deadlines: {deadlines_str}\n"
                    f"  Snippet: {sig['snippet']}\n"
                )
        context_parts.append("")
        
        # 6. Inject calendar events
        context_parts.append("=== UPCOMING MEETINGS ===")
        if not events:
            context_parts.append("  No calendar events synced yet.")
        else:
            for idx, event in enumerate(events, 1):
                title = event.get("title", "(No Title)")
                start = event.get("start_time", "")
                end = event.get("end_time", "")
                attendees = ", ".join(event.get("attendees", [])) if event.get("attendees") else ""
                
                context_parts.append(
                    f"Event #{idx}:\n"
                    f"  Title: {title}\n"
                    f"  Start: {start}\n"
                    f"  End: {end}\n"
                    f"  Attendees: {attendees}\n"
                )
                
        final_context = "\n".join(context_parts)
        
        # Safe character limit for 5000 tokens (approx 4 chars per token)
        max_chars = 5000 * 4
        if len(final_context) > max_chars:
            print(f"WARNING: Context length ({len(final_context)} chars) exceeds 5000 tokens limit. Truncating.", flush=True)
            final_context = final_context[:max_chars] + "\n... [TRUNCATED DUE TO CONTEXT LIMIT] ..."
            
        token_estimate = len(final_context) // 4
        
        # Print diagnostics logs
        print("--- CONTEXT BUILDER DIAGNOSTICS ---", flush=True)
        print(f"emails_scanned: {emails_scanned}", flush=True)
        print(f"signals_extracted: {signals_extracted}", flush=True)
        print(f"projects_scored: {projects_scored}", flush=True)
        print(f"final_prompt_token_estimate: {token_estimate}", flush=True)
        print("-----------------------------------", flush=True)
        
        return final_context

    @staticmethod
    def generate_briefing_summary(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI Chief of Staff Briefing Generator.
        Uses a provider abstraction pipeline to generate the briefing.
        Returns a structured founder briefing.
        """
        import time
        start_time = time.time()
        
        # Add diagnostics
        raw_emails = user_data.get("emails", [])
        events = user_data.get("calendar_events", [])
        print("RAW EMAILS LOADED:", len(raw_emails), flush=True)
        print("CALENDAR EVENTS LOADED:", len(events), flush=True)
        
        # 1. Run the noise filter FIRST, before building any AI context.
        filtered_emails = []
        noise_count = 0
        for e in raw_emails:
            if AIService.is_noise_email(e):
                noise_count += 1
            else:
                filtered_emails.append(e)
                
        print("FILTERED OUT NOISE EMAILS COUNT:", noise_count, flush=True)
        print("EMAILS REMAINING FOR CONTEXT:", len(filtered_emails), flush=True)
        
        # Construct updated user data containing only filtered emails
        filtered_user_data = {
            **user_data,
            "emails": filtered_emails
        }
        
        # Build the compressed context using pre-filtered emails
        context = AIService._build_compressed_context(filtered_user_data)
        print("--- [DIAGNOSTIC] Final Compressed Context Sent to AI ---", flush=True)
        try:
            print(context, flush=True)
        except UnicodeEncodeError:
            print(context.encode("ascii", errors="replace").decode("ascii"), flush=True)
        print("---------------------------------------------------------", flush=True)
        print("CONTEXT BUILT SUCCESSFULLY", flush=True)
        print("CONTEXT LENGTH:", len(context), flush=True)
        
        # Extract metrics for diagnostics
        emails_scanned = len(filtered_emails)
        from app.services.ai.signal_extractor import SignalExtractor
        from app.services.ai.risk_engine import ProjectRiskEngine
        business_context = filtered_user_data.get("business_context") or {}
        raw_projects = business_context.get("projects", [])
        signals_extracted = len(SignalExtractor.extract_signals_from_emails(filtered_emails, business_context))
        projects_scored = len(raw_projects)
        
        SYSTEM_PROMPT = """You are FlowBrain, an AI Chief of Staff for a small business owner.

Your ONLY job is to identify what genuinely matters to the BUSINESS — 
not technical noise, not automated notifications, not generic admin emails.

STRICT RULES:

1. IGNORE completely: deployment notifications, sign-in alerts, security 
   notifications, "build failed/succeeded" emails, third-party app 
   authorizations, newsletter subscriptions, automated platform emails.
   These are NOT business signals. Do not mention them even if present.

2. ONLY flag something as "About to break" (red) if it threatens:
   - Money (unpaid invoice, client about to leave, lost deal)
   - A real deadline tied to a paying client or project
   - Team capacity (someone overloaded, blocked, or unavailable)

3. WEIGHT every signal by financial impact using the business context 
   provided. Reason about RISK, not just deadline proximity — a 
   nearly-finished small project is lower risk than a half-finished 
   large project, even with a more distant deadline.

4. If you don't have enough information to judge business importance, 
   say so explicitly rather than guessing from email subject lines alone.

5. NEVER use a generic notification as a "win." A win is: payment 
   received, client praised work, deal closed, project delivered, 
   positive reply from a prospect.

6. A technical issue only becomes a business issue if:
   - it affects customers
   - it affects revenue
   - it blocks a launch
   - it blocks a paying client deliverable
   Otherwise ignore it completely, even if it looks urgent on the surface.

7. Prefer signals that appear in multiple places. For example: a client 
   mentioned in an email + a meeting on the calendar + an approaching 
   deadline = high confidence. A single isolated mention = lower 
   confidence. State your confidence level when it's based on only one 
   source.

8. NEVER classify personal calendar events (birthdays, anniversaries, 
   reminders, holidays) as business signals. Exclude them entirely 
   from the briefing.

9. When calculating priority, use this internally before assigning 
   Red/Amber/Green:
   Priority Score = (Revenue Impact × 50%) + (Deadline Risk × 30%) + 
   (Team Blocker × 20%)
   Do not show this score to the user — use it only to decide ranking 
   and color.

10. If all available information is low confidence or insufficient, 
    return exactly: "No major business risks detected from available 
    data." instead of inventing urgency to fill the briefing.

11. Never invent or estimate a financial value that was not explicitly 
    provided in BUSINESS CONTEXT or stated directly in an email/calendar 
    event. If financial impact is unknown, mark financial_impact as 
    null in actions and "Unknown" in briefing cards.

12. For emails expressing personal frustration, resignation, or leave 
    requests: only classify as RED if they explicitly name a specific 
    project deliverable, client deadline, or revenue amount that will 
    be directly impacted. An informal message saying someone wants to 
    leave without naming a specific business impact should be classified 
    as AMBER (needs decision) not RED (about to break). Never classify 
    a raw calendar event with no attendees, no description, and no 
    business context as a Needs Decision item.

ACTIONS ARRAY RULES:
1. Generate exactly ONE action per red card and ONE per amber card. 
   Never generate actions for green cards.
2. Each action must be SPECIFIC and CONCRETE — include the person's 
   name, company name, ₹ amount, and deadline where this data exists.
   BAD: "Follow up with client"
   GOOD: "Call Meera Krishnan at RetailMax about ₹18,00,000 contract 
   before board meeting June 25"
3. Sort actions by priority: financial_impact DESC first, then deadline 
   proximity, then team blockers. Priority 1 = highest financial risk.
4. Never invent names, amounts, or dates not present in the briefing 
   signals or business context.
5. due_date: extract from the signal deadline if available, else null.
6. financial_impact in actions: integer in rupees (e.g. 1800000 for 
   ₹18,00,000), or null if unknown. NEVER a formatted string.
7. source_signal must exactly match the title field of the red or 
   amber card it came from.

Respond ONLY in this exact JSON format. No markdown. No commentary. 
No text before or after the JSON object:
{
  "headline": "One sharp sentence on the single biggest business risk this week, OR 'No major business risks detected from available data.'",
  "red": [
    {
      "title": "...",
      "detail": "...",
      "financial_impact": "₹X or Unknown",
      "confidence": "high/medium/low"
    }
  ],
  "amber": [
    {
      "title": "...",
      "detail": "...",
      "financial_impact": "₹X or Unknown",
      "confidence": "high/medium/low"
    }
  ],
  "green": [
    {
      "title": "...",
      "detail": "..."
    }
  ],
  "focus": "The single most important action to take today, or 'No urgent action needed today.'",
  "ignored_count": 0,
  "actions": [
    {
      "title": "Short verb-first action max 8 words",
      "description": "Specific what/who/when in one sentence",
      "priority": 1,
      "due_date": "YYYY-MM-DD or null",
      "financial_impact": 850000,
      "source_type": "red or amber",
      "source_signal": "exact title of originating briefing card"
    }
  ]
}
"""

        token_estimate = (len(context) + len(SYSTEM_PROMPT)) // 4
        
        # Pluggable provider list in priority order
        providers: List[BriefingProvider] = [
            GeminiProvider(),
            ClaudeProvider(),
            AlgorithmicProvider()
        ]
        
        briefing_data = None
        provider_used = None
        model_used = None
        error_message = None
        errors_logged = []
        
        for provider in providers:
            try:
                # If provider is Claude, check if ANTHROPIC_API_KEY is present and not mock.
                # If not, skip it directly.
                if provider.provider_name == "claude":
                    api_key = settings.ANTHROPIC_API_KEY
                    if not api_key or "mock" in api_key.lower():
                        print("[ClaudeProvider] Skipped due to missing/mock API key.", flush=True)
                        continue
                        
                try:
                    briefing_data = provider.generate(context, SYSTEM_PROMPT, filtered_user_data)
                except Exception as e:
                    if _is_transient_error(e):
                        print(f"[AIService] transient error, retrying: {str(e)}", flush=True)
                        time.sleep(3)
                        # Retry once
                        briefing_data = provider.generate(context, SYSTEM_PROMPT, filtered_user_data)
                    else:
                        print(f"[AIService] permanent error, falling back immediately: {str(e)}", flush=True)
                        raise e
                        
                provider_used = provider.provider_name
                model_used = provider.model_name
                break
            except Exception as e:
                err_msg = f"Error in {provider.provider_name} ({provider.model_name}): {str(e)}"
                print(f"[AIService] {err_msg}", flush=True)
                errors_logged.append(err_msg)
                
        if not briefing_data:
            error_message = "; ".join(errors_logged)
            raise RuntimeError(f"All briefing providers failed. Errors: {error_message}")
            
        if errors_logged:
            error_message = "; ".join(errors_logged)
            
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Print diagnostics
        print("--- AI BRIEFING GENERATION DIAGNOSTICS ---", flush=True)
        print(f"provider_used: {provider_used}", flush=True)
        print(f"model_used: {model_used}", flush=True)
        print(f"response_time_ms: {response_time_ms}", flush=True)
        print(f"emails_scanned: {emails_scanned}", flush=True)
        print(f"signals_extracted: {signals_extracted}", flush=True)
        print(f"projects_scored: {projects_scored}", flush=True)
        print(f"token_estimate: {token_estimate}", flush=True)
        print(f"error_message: {error_message}", flush=True)
        print("------------------------------------------", flush=True)
        
        # Merge backend pre-filtered noise emails count
        briefing_data["ignored_count"] = briefing_data.get("ignored_count", 0) + noise_count
        return briefing_data


    @staticmethod
    def _generate_algorithmic_briefing(user_data: Dict[str, Any]) -> Dict[str, Any]:
        emails = user_data.get("emails", [])[:100]
        events = user_data.get("calendar_events", [])
        
        red = []
        amber = []
        green = []
        ignored_count = 0
        
        # Noise filter keywords (Rule 1)
        noise_keywords = ["deploy", "sign-in", "security", "build", "authorized", "newsletter", "subscription", "notification"]
        
        for email in emails:
            subject = email.get("subject", "").lower()
            snippet = email.get("snippet", "").lower()
            body_full = (email.get("body_full") or "").lower()
            text_to_scan = f"{subject} {snippet} {body_full}"
            
            # Apply Rule 1: Ignore completely noise emails
            if any(nk in text_to_scan for nk in noise_keywords):
                ignored_count += 1
                continue
                
            # Wins (green) - Rule 5: payment received, client praised work, deal closed, project delivered, positive reply
            if any(w in text_to_scan for w in ["win", "payment", "received", "praise", "closed", "signed", "delivered", "contract"]):
                green.append({
                    "title": email.get("subject", "Milestone Win"),
                    "detail": email.get("snippet", "")[:150]
                })
            # Blocker (red) - Rule 2: threatens Money, client/project deadline, team capacity
            elif any(b in text_to_scan for b in ["unpaid", "invoice", "overdue", "leave", "lost", "capacity", "overload", "blocked", "unavailable"]):
                red.append({
                    "title": email.get("subject", "Critical Business Risk"),
                    "detail": email.get("snippet", "")[:150],
                    "financial_impact": "₹50,000" if "invoice" in text_to_scan or "payment" in text_to_scan else "N/A",
                    "confidence": "high"
                })
            # Decisions (amber) - rule-based fallback decision
            elif any(d in text_to_scan for d in ["decide", "approve", "confirm", "budget", "choose", "review", "feedback"]):
                amber.append({
                    "title": email.get("subject", "Decision Required"),
                    "detail": email.get("snippet", "")[:150],
                    "financial_impact": "N/A",
                    "confidence": "medium"
                })
            else:
                ignored_count += 1
                
        # Scan calendar events
        for event in events:
            title = event.get("title", "").lower()
            desc = event.get("description", "").lower() if event.get("description") else ""
            text_to_scan = f"{title} {desc}"
            
            # Rule 8: Exclude personal events
            personal_keywords = ["birthday", "anniversary", "reminder", "holiday", "vacation", "personal"]
            if any(pk in text_to_scan for pk in personal_keywords):
                ignored_count += 1
                continue
                
            if any(w in text_to_scan for w in ["demo", "pitch", "launch", "interview", "call", "client", "meeting"]):
                amber.append({
                    "title": event.get("title", "Business Meeting"),
                    "detail": f"Scheduled start time: {event.get('start_time')}",
                    "financial_impact": "N/A",
                    "confidence": "high"
                })
            else:
                ignored_count += 1
                
        # Trim lists to max 3 items
        red = red[:3]
        amber = amber[:3]
        green = green[:3]
        
        # Focus logic
        focus = "No urgent action needed today."
        if red:
            focus = f"Resolve critical blocker: {red[0]['title']}"
        elif amber:
            focus = f"Attend meeting or resolve decision: {amber[0]['title']}"
        elif green:
            focus = f"Build momentum from win: {green[0]['title']}"
            
        headline = "No major business risks detected from available data."
        if red:
            headline = f"Critical Risk: {red[0]['title']}"
        elif amber:
            headline = f"Pending Action: {amber[0]['title']}"
            
        return {
            "headline": headline,
            "red": red,
            "amber": amber,
            "green": green,
            "focus": focus,
            "ignored_count": ignored_count
        }
