import re
from typing import Dict, Any, List

class SignalExtractor:
    @staticmethod
    def extract_signals_from_emails(emails: List[Dict[str, Any]], business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts key business signals from emails locally using Python regex and keyword heuristics.
        Does not query Gemini/LLM, ensuring raw body_full text is filtered out and converted
        to lightweight metadata records before sending it to the AI.
        """
        extracted_signals = []
        if not business_context:
            business_context = {}
            
        clients = [c.get("name") for c in business_context.get("clients", []) if c.get("name")]
        projects = [p.get("name") for p in business_context.get("projects", []) if p.get("name")]
        
        urgency_keywords = ["urgent", "asap", "deadline", "break", "block", "error", "fail", "delay", "important", "immediately", "action required"]
        payment_keywords = ["invoice", "payment", "unpaid", "overdue", "price", "cost", "billing", "wire", "transfer"]
        
        for email in emails:
            subject = email.get("subject", "")
            sender = email.get("sender", "")
            snippet = email.get("snippet", "")
            body_full = email.get("body_full") or ""
            
            # Scan lowercase combined representation (subject, snippet, and start of body)
            scan_text = f"{subject} {snippet} {body_full[:2000]}".lower()
            
            # 1. Match Clients
            matched_clients = []
            for c in clients:
                if c.lower() in scan_text:
                    matched_clients.append(c)
                    
            # 2. Match Projects
            matched_projects = []
            for p in projects:
                if p.lower() in scan_text:
                    matched_projects.append(p)
                    
            # 3. Urgency Indicators
            urgency_indicators = []
            for kw in urgency_keywords:
                if kw in scan_text:
                    urgency_indicators.append(kw)
                    
            # 4. Payment References
            payment_references = []
            for kw in payment_keywords:
                if kw in scan_text:
                    payment_references.append(kw)
            # Find currency symbols (e.g. ₹50,000, $400, INR 1000)
            currency_matches = re.findall(r'(?:[\$₹£€]|usd|inr|eur)\s*\d+(?:,\d+)*(?:\.\d+)?', scan_text)
            if currency_matches:
                payment_references.extend(currency_matches[:3])
                
            # 5. Extract Deadlines (date patterns like YYYY-MM-DD or DD/MM/YYYY)
            date_matches = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', scan_text)
            slash_matches = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', scan_text)
            
            extracted_deadlines = list(set(date_matches + slash_matches))[:3]
            
            # A record counts as a business signal if it contains any client link, project link, 
            # urgency match, payment reference, or date pattern.
            is_signal = (
                matched_clients or 
                matched_projects or 
                urgency_indicators or 
                payment_references or 
                extracted_deadlines
            )
            
            if is_signal:
                extracted_signals.append({
                    "subject": subject,
                    "sender": sender,
                    "received_at": email.get("received_at", ""),
                    "is_unread": email.get("is_unread", False),
                    "labels": email.get("labels", []),
                    "urgency_indicators": list(set(urgency_indicators)),
                    "matched_clients": list(set(matched_clients)),
                    "matched_projects": list(set(matched_projects)),
                    "payment_references": list(set(payment_references)),
                    "extracted_deadlines": extracted_deadlines,
                    "snippet": snippet[:150]
                })
                
        # Heuristic scoring to bubble up the most important signals
        # Score = (2 if unread else 0) + len(urgency_indicators) + (2 if client/project match else 0) + (1 if payment match)
        def score_signal(sig):
            score = 0
            if sig["is_unread"]:
                score += 2
            score += len(sig["urgency_indicators"])
            if sig["matched_clients"] or sig["matched_projects"]:
                score += 2
            if sig["payment_references"]:
                score += 1
            return score
            
        extracted_signals.sort(key=score_signal, reverse=True)
        return extracted_signals[:20]
