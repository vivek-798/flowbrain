from datetime import datetime, timezone
from typing import List, Dict, Any

class ProjectRiskEngine:
    @staticmethod
    def score_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scores active projects quantitatively:
        Score = value_inr * deadline_factor * completion_factor
        
        deadline_factor:
          - Overdue (< 0 days): 3.0
          - Today/Critical (0-3 days): 2.5
          - Soon (4-7 days): 2.0
          - Month (8-30 days): 1.5
          - Normal (> 30 days): 1.0
          - No deadline: 1.0
        
        completion_factor:
          - (100 - completion_percent) / 100
        """
        scored_projects = []
        now = datetime.now(timezone.utc)
        
        for p in projects:
            value = float(p.get("value_inr") or 0.0)
            completion = float(p.get("completion_percent") or 0.0)
            deadline_str = p.get("deadline")
            
            # 1. Deadline Factor
            deadline_factor = 1.0
            if deadline_str:
                try:
                    # Expecting YYYY-MM-DD
                    deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    days_remaining = (deadline_date - now).days
                    
                    if days_remaining < 0:
                        deadline_factor = 3.0
                    elif days_remaining <= 3:
                        deadline_factor = 2.5
                    elif days_remaining <= 7:
                        deadline_factor = 2.0
                    elif days_remaining <= 30:
                        deadline_factor = 1.5
                    else:
                        deadline_factor = 1.0
                except Exception:
                    deadline_factor = 1.0
            
            # 2. Completion Factor
            completion_factor = (100.0 - completion) / 100.0
            if completion_factor < 0.0:
                completion_factor = 0.0
                
            # Score
            score = value * deadline_factor * completion_factor
            
            # Categorize Risk
            if score >= 500000:
                risk_level = "High"
            elif score >= 100000:
                risk_level = "Medium"
            else:
                risk_level = "Low"
                
            # Completed projects are 0 risk
            if completion >= 100:
                score = 0.0
                risk_level = "Low"
                
            scored_projects.append({
                **p,
                "risk_score": round(score, 2),
                "risk_level": risk_level
            })
            
        # Sort descending by risk score
        scored_projects.sort(key=lambda x: x["risk_score"], reverse=True)
        return scored_projects[:10]
