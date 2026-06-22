from typing import List, Dict, Any

class NotionService:
    def __init__(self, access_token: str = None):
        self.access_token = access_token

    def fetch_recent_notion_updates(self) -> List[Dict[str, Any]]:
        """
        Placeholder method to retrieve recent updates from the founder's Notion workspaces,
        tracking product roadmaps, company wikis, or planning boards.
        """
        return [
            {
                "id": "notion_1",
                "page": "FlowBrain Q3 Roadmap",
                "last_edited_by": "Alex Founder",
                "updated_at": "2026-06-18T09:00:00Z",
                "change_summary": "Added milestones for integrations release."
            },
            {
                "id": "notion_2",
                "page": "Weekly Sync Agenda",
                "last_edited_by": "Co-founder",
                "updated_at": "2026-06-17T17:30:00Z",
                "change_summary": "Added discussion item about cloud hosting budget increases."
            }
        ]
