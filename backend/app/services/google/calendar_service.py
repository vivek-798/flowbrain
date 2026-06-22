import httpx
import calendar
import datetime as dt
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.integration import Integration
from app.models.calendar_event import CalendarEvent
from app.services.google_auth import refresh_user_google_tokens

class CalendarService:
    def __init__(self, db: Session):
        self.db = db

    async def sync_user_calendar(self, user: User) -> dict:
        """
        Connects to Google Calendar API, fetches events for the current calendar month,
        upserts them in the database, and updates integration sync timestamp.
        """
        integration = self.db.query(Integration).filter(
            Integration.user_id == user.id,
            Integration.provider == "calendar",
            Integration.connected == True
        ).first()

        if not integration:
            raise Exception("Calendar integration is not connected for this user.")

        access_token = integration.access_token

        # Calculate time range: from the start of the current month until the end of the current month
        now_dt = datetime.now(timezone.utc)
        start_of_month = datetime(now_dt.year, now_dt.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        _, last_day = calendar.monthrange(now_dt.year, now_dt.month)
        end_of_month = datetime(now_dt.year, now_dt.month, last_day, 23, 59, 59, tzinfo=timezone.utc)

        time_min = start_of_month.isoformat()
        time_max = end_of_month.isoformat()

        async def fetch_events(token: str) -> httpx.Response:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    params={
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "singleEvents": "true",
                        "orderBy": "startTime",
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                return res

        res = await fetch_events(access_token)

        # Handle 401 expiry by refreshing tokens
        if res.status_code == 401:
            try:
                access_token = await refresh_user_google_tokens(self.db, user.id)
                res = await fetch_events(access_token)
            except Exception as e:
                raise Exception(f"Failed to refresh Google token during Calendar sync: {str(e)}")

        if res.status_code != 200:
            raise Exception(f"Google Calendar API events list error: {res.text}")

        events_data = res.json().get("items", [])
        if not events_data:
            integration.last_sync = datetime.now(timezone.utc)
            self.db.commit()
            return {"status": "success", "synced": 0}

        synced_count = 0
        for item in events_data:
            if item.get("status") == "cancelled":
                continue

            event_id = item.get("id")
            title = item.get("summary", "(No Title)")
            description = item.get("description", "")
            location = item.get("location", "")

            # Start/End times
            start_data = item.get("start", {})
            end_data = item.get("end", {})
            start_str = start_data.get("dateTime") or start_data.get("date")
            end_str = end_data.get("dateTime") or end_data.get("date")

            if not start_str or not end_str:
                continue

            start_time = dt.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_time = dt.datetime.fromisoformat(end_str.replace("Z", "+00:00"))

            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            # Attendees
            attendees_list = []
            for att in item.get("attendees", []):
                email = att.get("email")
                if email:
                    attendees_list.append(email)

            organizer = item.get("organizer", {}).get("email", "")

            # Meeting link (Google Meet or external link)
            meeting_link = item.get("hangoutLink")
            if not meeting_link:
                conference_data = item.get("conferenceData", {})
                entry_points = conference_data.get("entryPoints", [])
                for ep in entry_points:
                    if ep.get("entryPointType") == "video":
                        meeting_link = ep.get("uri")
                        break

            # Upsert Event
            event_record = self.db.query(CalendarEvent).filter(CalendarEvent.google_event_id == event_id).first()
            if not event_record:
                event_record = CalendarEvent(
                    user_id=user.id,
                    google_event_id=event_id,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    attendees=attendees_list,
                    organizer=organizer,
                    meeting_link=meeting_link,
                    location=location
                )
                self.db.add(event_record)
            else:
                event_record.title = title
                event_record.description = description
                event_record.start_time = start_time
                event_record.end_time = end_time
                event_record.attendees = attendees_list
                event_record.organizer = organizer
                event_record.meeting_link = meeting_link
                event_record.location = location
                event_record.updated_at = datetime.now(timezone.utc)

            synced_count += 1

        integration.last_sync = datetime.now(timezone.utc)
        self.db.commit()

        return {"status": "success", "synced": synced_count}
