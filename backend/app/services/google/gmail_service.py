import asyncio
import httpx
import base64
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.integration import Integration
from app.models.email import Email
from app.services.google_auth import refresh_user_google_tokens

class GmailService:
    def __init__(self, db: Session):
        self.db = db

    def _parse_body_preview(self, payload: dict) -> str:
        body_data = ""
        if "parts" in payload:
            # Recursively find plain text or html parts
            def find_text_part(parts):
                for part in parts:
                    mime_type = part.get("mimeType", "")
                    if mime_type == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return data
                    elif mime_type == "text/html":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return data
                    if "parts" in part:
                        found = find_text_part(part["parts"])
                        if found:
                            return found
                return None
            
            data = find_text_part(payload["parts"])
            if data:
                try:
                    body_data = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
                except Exception:
                    pass
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    body_data = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
                except Exception:
                    pass
        
        return body_data[:500] if body_data else ""

    def _parse_body_full(self, payload: dict) -> str:
        body_data = ""
        if "parts" in payload:
            # Recursively find plain text or html parts
            def find_text_part(parts):
                for part in parts:
                    mime_type = part.get("mimeType", "")
                    if mime_type == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return data
                    elif mime_type == "text/html":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return data
                    if "parts" in part:
                        found = find_text_part(part["parts"])
                        if found:
                            return found
                return None
            
            data = find_text_part(payload["parts"])
            if data:
                try:
                    body_data = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
                except Exception:
                    pass
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    body_data = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
                except Exception:
                    pass
        
        return body_data if body_data else ""

    async def sync_user_emails(self, user: User) -> dict:
        """
        Connects to Gmail API, fetches emails from the last 30 days,
        upserts them in the database, and updates integration sync timestamp.
        """
        integration = self.db.query(Integration).filter(
            Integration.user_id == user.id,
            Integration.provider == "gmail",
            Integration.connected == True
        ).first()

        if not integration:
            raise Exception("Gmail integration is not connected for this user.")

        access_token = integration.access_token

        # Query parameter to filter messages from the last 30 days
        thirty_days_ago = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
        q_filter = f"after:{thirty_days_ago}"

        async def fetch_messages_list(token: str) -> httpx.Response:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    params={"maxResults": 100, "q": q_filter},
                    headers={"Authorization": f"Bearer {token}"}
                )
                return res

        res = await fetch_messages_list(access_token)

        # Handle 401 expiry by refreshing tokens
        if res.status_code == 401:
            try:
                access_token = await refresh_user_google_tokens(self.db, user.id)
                res = await fetch_messages_list(access_token)
            except Exception as e:
                raise Exception(f"Failed to refresh Google token during Gmail sync: {str(e)}")

        if res.status_code != 200:
            raise Exception(f"Google Gmail API list error: {res.text}")

        messages_data = res.json().get("messages", [])
        if not messages_data:
            integration.last_sync = datetime.now(timezone.utc)
            self.db.commit()
            return {
                "messages_returned": 0,
                "inserted": 0,
                "updated": 0,
                "skipped": 0
            }

        # Concurrently fetch details for each email ID
        semaphore = asyncio.Semaphore(15)
        
        async def fetch_detail(client: httpx.AsyncClient, msg_id: str) -> dict:
            async with semaphore:
                detail_res = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if detail_res.status_code == 200:
                    return detail_res.json()
                return None

        async with httpx.AsyncClient() as client:
            tasks = [fetch_detail(client, msg["id"]) for msg in messages_data]
            details_list = await asyncio.gather(*tasks)

        messages_returned = len(messages_data)
        inserted = 0
        updated = 0
        skipped = 0

        for details in details_list:
            if not details:
                skipped += 1
                continue

            msg_id = details.get("id")
            thread_id = details.get("threadId")
            snippet = details.get("snippet", "")
            label_ids = details.get("labelIds", [])
            is_unread = "UNREAD" in label_ids
            internal_date = details.get("internalDate")

            received_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)

            sender = "Unknown"
            recipients = ""
            subject = "(No Subject)"
            
            headers = details.get("payload", {}).get("headers", [])
            for h in headers:
                name = h.get("name", "").lower()
                value = h.get("value", "")
                if name == "from":
                    sender = value
                elif name == "to":
                    recipients = value
                elif name == "subject":
                    subject = value

            body_preview = self._parse_body_preview(details.get("payload", {}))
            body_full = self._parse_body_full(details.get("payload", {}))

            # Upsert Email
            email_record = self.db.query(Email).filter(Email.gmail_message_id == msg_id).first()
            if email_record and email_record.is_excluded:
                skipped += 1
                continue

            if not email_record:
                email_record = Email(
                    user_id=user.id,
                    gmail_message_id=msg_id,
                    thread_id=thread_id,
                    sender=sender,
                    recipients=recipients,
                    subject=subject,
                    snippet=snippet,
                    body_preview=body_preview,
                    body_full=body_full,
                    labels=label_ids,
                    received_at=received_at,
                    is_unread=is_unread
                )
                self.db.add(email_record)
                inserted += 1
            else:
                email_record.thread_id = thread_id
                email_record.sender = sender
                email_record.recipients = recipients
                email_record.subject = subject
                email_record.snippet = snippet
                email_record.body_preview = body_preview
                email_record.body_full = body_full
                email_record.labels = label_ids
                email_record.is_unread = is_unread
                email_record.received_at = received_at
                updated += 1

        print("Messages returned from Gmail:", messages_returned, flush=True)
        print("Emails inserted:", inserted, flush=True)
        print("Emails updated:", updated, flush=True)
        print("Emails skipped:", skipped, flush=True)

        integration.last_sync = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "messages_returned": messages_returned,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped
        }
