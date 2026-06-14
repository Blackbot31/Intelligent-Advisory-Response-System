from datetime import datetime
import uuid

# ─── Collaboration & Engagement Unit ─────────────────────────────────────────
class CollaborationEngagementUnit:
    def __init__(self):
        self.stakeholders = {}
        self.engagement_log = []
        self.active_collaborations = {}
        self.feedback_registry = {}

        self.stakeholder_types = [
            "Government Agency",
            "Healthcare Facility",
            "Community Organisation",
            "International Partner",
            "Research Institution",
            "Non-Governmental Organisation"
        ]

        self.engagement_channels = [
            "Virtual Meeting",
            "Field Coordination",
            "Situation Report",
            "Emergency Broadcast",
            "Direct Communication"
        ]

    def register_stakeholder(self, name, stakeholder_type,
                              region, contact):
        stakeholder_id = str(uuid.uuid4())[:8].upper()
        self.stakeholders[stakeholder_id] = {
            "stakeholder_id": stakeholder_id,
            "name": name,
            "type": stakeholder_type,
            "region": region,
            "contact": contact,
            "status": "Active",
            "engagements": 0,
            "date_registered": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return stakeholder_id

    def initiate_collaboration(self, title, stakeholder_ids,
                                objective, duration_days):
        collab_id = str(uuid.uuid4())[:8].upper()
        participants = []
        for sid in stakeholder_ids:
            if sid in self.stakeholders:
                participants.append({
                    "id": sid,
                    "name": self.stakeholders[sid]["name"],
                    "type": self.stakeholders[sid]["type"]
                })
                self.stakeholders[sid]["engagements"] += 1

        self.active_collaborations[collab_id] = {
            "collaboration_id": collab_id,
            "title": title,
            "objective": objective,
            "participants": participants,
            "total_participants": len(participants),
            "duration_days": duration_days,
            "status": "Active",
            "outcomes": [],
            "start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return collab_id

    def log_engagement(self, stakeholder_id, channel, summary):
        if stakeholder_id not in self.stakeholders:
            return {"error": "Stakeholder not found"}
        engagement_id = str(uuid.uuid4())[:8].upper()
        record = {
            "engagement_id": engagement_id,
            "stakeholder_id": stakeholder_id,
            "stakeholder_name": self.stakeholders[stakeholder_id]["name"],
            "channel": channel,
            "summary": summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.engagement_log.append(record)
        self.stakeholders[stakeholder_id]["engagements"] += 1
        return record

    def submit_feedback(self, stakeholder_id, feedback_type,
                         message, rating):
        if stakeholder_id not in self.stakeholders:
            return {"error": "Stakeholder not found"}
        feedback_id = str(uuid.uuid4())[:8].upper()
        self.feedback_registry[feedback_id] = {
            "feedback_id": feedback_id,
            "stakeholder_id": stakeholder_id,
            "stakeholder_name": self.stakeholders[stakeholder_id]["name"],
            "feedback_type": feedback_type,
            "message": message,
            "rating": rating,
            "status": "Received",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.feedback_registry[feedback_id]

    def get_engagement_summary(self):
        total_feedback = len(self.feedback_registry)
        avg_rating = 0
        if total_feedback > 0:
            avg_rating = round(
                sum(f["rating"] for f in
                    self.feedback_registry.values()) / total_feedback, 2
            )
        summary = {
            "total_stakeholders": len(self.stakeholders),
            "total_engagements": len(self.engagement_log),
            "active_collaborations": len(self.active_collaborations),
            "total_feedback_received": total_feedback,
            "average_feedback_rating": avg_rating,
            "stakeholder_list": [
                {
                    "name": s["name"],
                    "type": s["type"],
                    "region": s["region"],
                    "engagements": s["engagements"]
                }
                for s in self.stakeholders.values()
            ]
        }
        summary["written_report"] = self.generate_written_report(summary)
        return summary
        
    def generate_written_report(self, summary):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("COLLABORATION AND ENGAGEMENT UNIT")
        lines.append("Stakeholder Engagement Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("ENGAGEMENT OVERVIEW")
        lines.append("")
        lines.append(
            f"  The Collaboration and Engagement Unit has completed a review of all "
            f"stakeholder engagement activities related to the current outbreak response. "
            f"A total of {summary['total_stakeholders']} stakeholder(s) have been registered "
            f"and are actively participating in the response operation. Across all registered "
            f"stakeholders, a combined total of {summary['total_engagements']} engagement(s) "
            f"have been logged through various communication channels including virtual meetings, "
            f"field coordination, situation reports, and direct communication."
        )
        lines.append("")

        lines.append("COLLABORATION STATUS")
        lines.append("")
        lines.append(
            f"  There are currently {summary['active_collaborations']} active collaboration(s) "
            f"in progress among the registered stakeholders. These collaborations have been "
            f"formally initiated to ensure structured and inclusive participation from all "
            f"relevant agencies and organisations throughout the duration of the outbreak response. "
            f"All participating stakeholders are expected to contribute to situation reporting, "
            f"resource coordination, and community engagement activities."
        )
        lines.append("")

        lines.append("FEEDBACK SUMMARY")
        lines.append("")
        if summary["total_feedback_received"] > 0:
            lines.append(
                f"  A total of {summary['total_feedback_received']} feedback submission(s) "
                f"have been received from registered stakeholders. The average feedback rating "
                f"across all submissions is {summary['average_feedback_rating']} out of 5.0. "
                f"This feedback is being used to continuously improve the coordination and "
                f"communication processes of the response operation."
            )
        else:
            lines.append(
                f"  No feedback submissions have been received from stakeholders at this time. "
                f"Stakeholders are encouraged to submit feedback on the coordination process "
                f"to support continuous improvement of the response operation."
            )
        lines.append("")

        if summary["stakeholder_list"]:
            lines.append("REGISTERED STAKEHOLDERS")
            lines.append("")
            for s in summary["stakeholder_list"]:
                lines.append(
                    f"  {s['name']} is registered as a {s['type']} based in the "
                    f"{s['region']} region, with {s['engagements']} engagement(s) recorded "
                    f"to date."
                )
            lines.append("")

        lines.append("ENGAGEMENT NOTE")
        lines.append("")
        lines.append(
            f"  All stakeholders registered in this system are considered active participants "
            f"in the outbreak response and are expected to maintain regular communication with "
            f"the coordination unit. Response coordinators are advised to review this engagement "
            f"report regularly and follow up with any stakeholders who have not been actively "
            f"participating in the response activities."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)


# ─── Quick Test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ceu = CollaborationEngagementUnit()

    # Register stakeholders
    s1 = ceu.register_stakeholder(
        "Federal Ministry of Health",
        "Government Agency", "National", "fmoh@health.gov.ng")
    s2 = ceu.register_stakeholder(
        "WHO Nigeria Office",
        "International Partner", "National", "who.ng@who.int")
    s3 = ceu.register_stakeholder(
        "North Central Community Health Network",
        "Community Organisation", "North Central", "ncchn@health.org")

    # Initiate collaboration
    collab = ceu.initiate_collaboration(
        title="Emergency Outbreak Coordination Meeting",
        stakeholder_ids=[s1, s2, s3],
        objective="Coordinate response activities across all affected zones",
        duration_days=14
    )

    # Log engagements
    ceu.log_engagement(s1, "Virtual Meeting",
                       "Reviewed resource deployment status")
    ceu.log_engagement(s2, "Situation Report",
                       "WHO provided technical guidance on case management")
    ceu.log_engagement(s3, "Field Coordination",
                       "Community health workers briefed on protocols")

    # Submit feedback
    ceu.submit_feedback(s1, "Response Effectiveness",
                        "Coordination improved significantly", 4.5)
    ceu.submit_feedback(s2, "System Usability",
                        "Advisory system is clear and actionable", 4.8)

    # Get summary
    summary = ceu.get_engagement_summary()

    print("CEU Engagement Summary:")
    print(f"  Total Stakeholders       : {summary['total_stakeholders']}")
    print(f"  Total Engagements        : {summary['total_engagements']}")
    print(f"  Active Collaborations    : {summary['active_collaborations']}")
    print(f"  Total Feedback Received  : {summary['total_feedback_received']}")
    print(f"  Average Feedback Rating  : {summary['average_feedback_rating']}")
    print(f"  Stakeholder List         :")
    for s in summary["stakeholder_list"]:
        print(f"    - {s['name']:<45} "
              f"Type: {s['type']:<25} "
              f"Engagements: {s['engagements']}")
    print("CEU subsystem loaded successfully!")