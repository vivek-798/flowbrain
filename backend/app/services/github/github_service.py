from typing import List, Dict, Any

class GitHubService:
    def __init__(self, access_token: str = None):
        self.access_token = access_token

    def fetch_recent_repo_activity(self) -> List[Dict[str, Any]]:
        """
        Placeholder method to connect to the GitHub API, checking commits,
        pull requests, and open issues for development tracking.
        """
        return [
            {
                "id": "gh_1",
                "repo": "flowbrain/backend",
                "event": "Pull Request",
                "title": "feat: Notion Sync Pipeline integration",
                "status": "merged",
                "user": "lead-dev"
            },
            {
                "id": "gh_2",
                "repo": "flowbrain/frontend",
                "event": "Issue Opened",
                "title": "bug: OAuth callback redirect failure on mobile safari",
                "status": "open",
                "user": "qa-tester"
            }
        ]
