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
                # Clean/parse sender email and name
                sender_email_val = sender
                sender_name_val = ""
                email_match = re.search(r'<([^>]+)>', sender)
                if email_match:
                    sender_email_val = email_match.group(1).strip()
                    sender_name_val = re.sub(r'<[^>]+>', '', sender).strip()
                else:
                    sender_email_val = sender.strip()
                    sender_name_val = ""

                # Subjects
                email_subject_val = subject
                thread_subject_val = re.sub(r'^(?:[Rr][Ee]|[Ff][Ww][Dd]):\s*', '', subject).strip()

                # IDs
                gmail_msg_id = email.get("gmail_message_id", "")
                th_id = email.get("thread_id", "")

                # Match client / company
                client_name_val = matched_clients[0] if matched_clients else None
                company_name_val = client_name_val
                if not company_name_val:
                    domain_match = re.search(r'@([^.]+)\.', sender_email_val)
                    if domain_match:
                        domain = domain_match.group(1).lower()
                        if domain not in ["gmail", "yahoo", "hotmail", "outlook", "live", "aol", "icloud", "mail", "zoho", "proton", "protonmail"]:
                            company_name_val = domain.capitalize()

                # Match project
                project_name_val = matched_projects[0] if matched_projects else None

                # Deadlines
                deadline_val = extracted_deadlines[0] if extracted_deadlines else None
                meeting_date_val = deadline_val

                # Invoice / proposal numbers
                invoice_match = re.search(r'(?:invoice|inv)\s*(?:#|no\.?|number:?)\s*([0-9a-zA-Z\-]+)', scan_text)
                invoice_number_val = invoice_match.group(1) if invoice_match else None

                proposal_match = re.search(r'(?:proposal|prop)\s*(?:#|no\.?|number:?)\s*([0-9a-zA-Z\-]+)', scan_text)
                proposal_number_val = proposal_match.group(1) if proposal_match else None

                # Contact person
                contact_person_val = sender_name_val if sender_name_val else None
                if not contact_person_val:
                    # Check if any team member name matches
                    team_members = business_context.get("team_members", [])
                    for tm in team_members:
                        if tm.get("name") and tm.get("name").lower() in scan_text:
                            contact_person_val = tm.get("name")
                            break

                # Owner
                owner_val = business_context.get("owner_name", "")

                # Participants
                participants_val = [sender_email_val]

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
                    "snippet": snippet[:150],
                    
                    # Rich signal metadata fields
                    "sender_name": sender_name_val or None,
                    "sender_email": sender_email_val or None,
                    "company_name": company_name_val or None,
                    "client_name": client_name_val or None,
                    "thread_subject": thread_subject_val or None,
                    "email_subject": email_subject_val or None,
                    "gmail_message_id": gmail_msg_id or None,
                    "thread_id": th_id or None,
                    "deadline": deadline_val or None,
                    "meeting_date": meeting_date_val or None,
                    "project_name": project_name_val or None,
                    "invoice_number": invoice_number_val or None,
                    "proposal_number": proposal_number_val or None,
                    "contact_person": contact_person_val or None,
                    "owner": owner_val or None,
                    "participants": participants_val
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
