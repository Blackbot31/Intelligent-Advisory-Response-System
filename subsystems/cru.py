import numpy as np
from datetime import datetime

# ─── Communication & Response Unit ──────────────────────────────────────────
class CommunicationResponseUnit:
    def __init__(self):
        self.response_channels = [
            "National Emergency Broadcast",
            "Sub-national Health Agency Alert",
            "Community Health Worker Network",
            "Digital Media and Social Platforms",
            "Healthcare Facility Direct Alert"
        ]

        self.response_templates = {
            "critical": {
                "subject": "URGENT: Critical Outbreak Alert",
                "priority": "CRITICAL",
                "escalation_level": 3
            },
            "high": {
                "subject": "HIGH ALERT: Outbreak Response Required",
                "priority": "HIGH",
                "escalation_level": 2
            },
            "moderate": {
                "subject": "NOTICE: Outbreak Monitoring Update",
                "priority": "MODERATE",
                "escalation_level": 1
            },
            "low": {
                "subject": "UPDATE: Routine Outbreak Surveillance",
                "priority": "LOW",
                "escalation_level": 0
            }
        }

        self.stakeholders = {
            "national": [
                "Federal Ministry of Health",
                "National Centre for Disease Control",
                "National Emergency Management Agency"
            ],
            "sub_national": [
                "State Ministries of Health",
                "Local Government Health Departments",
                "District Surveillance Officers"
            ],
            "community": [
                "Community Health Workers",
                "Traditional and Religious Leaders",
                "Community Development Associations"
            ],
            "international": [
                "World Health Organization",
                "Africa CDC",
                "International Red Cross"
            ]
        }

    def assess_severity(self, outbreak_data):
        score = 0
        if outbreak_data["cases"] > 500:
            score += 3
        elif outbreak_data["cases"] > 200:
            score += 2
        elif outbreak_data["cases"] > 50:
            score += 1

        if outbreak_data["fatality_rate"] > 0.05:
            score += 3
        elif outbreak_data["fatality_rate"] > 0.02:
            score += 2
        elif outbreak_data["fatality_rate"] > 0.01:
            score += 1

        if outbreak_data["spread_rate"] > 0.7:
            score += 3
        elif outbreak_data["spread_rate"] > 0.4:
            score += 2
        elif outbreak_data["spread_rate"] > 0.2:
            score += 1

        if score >= 7:
            return "critical"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "moderate"
        else:
            return "low"

    def identify_stakeholders(self, severity):
        if severity == "critical":
            return self.stakeholders
        elif severity == "high":
            return {
                "national": self.stakeholders["national"],
                "sub_national": self.stakeholders["sub_national"],
                "international": self.stakeholders["international"]
            }
        elif severity == "moderate":
            return {
                "national": self.stakeholders["national"],
                "sub_national": self.stakeholders["sub_national"]
            }
        else:
            return {
                "sub_national": self.stakeholders["sub_national"]
            }

    def generate_response_message(self, outbreak_data, severity):
        template = self.response_templates[severity]
        message = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subject": template["subject"],
            "priority": template["priority"],
            "escalation_level": template["escalation_level"],
            "disease": outbreak_data["disease"],
            "affected_region": outbreak_data["region"],
            "total_cases": outbreak_data["cases"],
            "total_deaths": outbreak_data["deaths"],
            "fatality_rate": f"{outbreak_data['fatality_rate'] * 100:.2f}%",
            "spread_rate": f"{outbreak_data['spread_rate'] * 100:.2f}%",
            "recommended_actions": self.get_response_actions(severity),
            "active_channels": self.response_channels
        }
        return message

    def get_response_actions(self, severity):
        actions = {
            "critical": [
                "Immediately activate national emergency response committee",
                "Deploy rapid response teams to all affected regions",
                "Issue national public health emergency declaration",
                "Request international support and technical assistance",
                "Enforce movement restrictions in hotspot areas"
            ],
            "high": [
                "Activate sub-national response coordination teams",
                "Scale up case detection and contact tracing",
                "Increase supply of personal protective equipment",
                "Issue high alert advisory to all health facilities"
            ],
            "moderate": [
                "Strengthen surveillance in affected communities",
                "Issue public awareness messages",
                "Monitor resource levels in affected facilities"
            ],
            "low": [
                "Continue routine surveillance",
                "Update situation reports",
                "Maintain readiness of response teams"
            ]
        }
        return actions[severity]

    def generate_full_response(self, outbreak_data):
        severity   = self.assess_severity(outbreak_data)
        stakeholders = self.identify_stakeholders(severity)
        message    = self.generate_response_message(outbreak_data, severity)
        hierarchy  = self.generate_coordination_hierarchy(severity, outbreak_data)
        result = {
            "severity":                severity.upper(),
            "message":                 message,
            "stakeholders_to_notify":  stakeholders,
            "total_stakeholder_groups": len(stakeholders),
            "coordination_hierarchy":  hierarchy
        }
        result["written_report"] = self.generate_written_report(result)
        return result
    
    def generate_coordination_hierarchy(self, severity, outbreak_data):
        hierarchy = {
            "levels": [],
            "activation_chain": [],
            "reporting_structure": {}
        }

        # Always include sub-national
        sub_national = {
            "level":        "Sub-National",
            "tier":         3,
            "status":       "ACTIVATED",
            "responsible":  [
                "State Ministries of Health",
                "Local Government Health Departments",
                "District Surveillance Officers"
            ],
            "responsibilities": [
                "First line case detection and reporting",
                "Local resource deployment",
                "Community mobilisation",
                "Daily situation reporting to national level"
            ]
        }
        hierarchy["levels"].append(sub_national)
        hierarchy["activation_chain"].append("Sub-National")

        # Add national for moderate and above
        if severity in ("moderate", "high", "critical"):
            national = {
                "level":       "National",
                "tier":        2,
                "status":      "ACTIVATED",
                "responsible": [
                    "Federal Ministry of Health",
                    "National Centre for Disease Control",
                    "National Emergency Management Agency"
                ],
                "responsibilities": [
                    "Policy direction and coordination",
                    "National resource allocation",
                    "Inter-agency coordination",
                    "International liaison"
                ]
            }
            hierarchy["levels"].append(national)
            hierarchy["activation_chain"].append("National")

        # Add international for high and critical
        if severity in ("high", "critical"):
            international = {
                "level":       "International",
                "tier":        1,
                "status":      "NOTIFIED",
                "responsible": [
                    "World Health Organization",
                    "Africa CDC",
                    "International Red Cross"
                ],
                "responsibilities": [
                    "Technical assistance and guidance",
                    "International resource mobilisation",
                    "Global health security coordination",
                    "Cross-border outbreak monitoring"
                ]
            }
            hierarchy["levels"].append(international)
            hierarchy["activation_chain"].append("International")

        # Add community for critical
        if severity == "critical":
            community = {
                "level":       "Community",
                "tier":        4,
                "status":      "ENGAGED",
                "responsible": [
                    "Community Health Workers",
                    "Traditional and Religious Leaders",
                    "Community Development Associations"
                ],
                "responsibilities": [
                    "Community awareness and education",
                    "Case identification and referral",
                    "Social mobilisation",
                    "Rumour management"
                ]
            }
            hierarchy["levels"].append(community)
            hierarchy["activation_chain"].append("Community")

        # Build reporting structure
        hierarchy["reporting_structure"] = {
            "flow": "Community → Sub-National → National → International",
            "frequency": {
                "critical": "Every 6 hours",
                "high":     "Every 12 hours",
                "moderate": "Every 24 hours",
                "low":      "Every 48 hours"
            }.get(severity, "Every 24 hours"),
            "primary_coordinator": "National Centre for Disease Control"
            if severity in ("moderate", "high", "critical")
            else "District Surveillance Officers"
        }

        return hierarchy
        
    def generate_written_report(self, result):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = result["message"]

        lines = []
        lines.append("COMMUNICATION AND RESPONSE UNIT")
        lines.append("Outbreak Response Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("OUTBREAK SUMMARY")
        lines.append("")
        lines.append(
            f"  A disease outbreak involving {msg['disease']} has been reported in the "
            f"{msg['affected_region']}. As of the time of this report, a total of "
            f"{msg['total_cases']} cases and {msg['total_deaths']} deaths have been recorded. "
            f"The fatality rate currently stands at {msg['fatality_rate']} and the spread rate "
            f"has been assessed at {msg['spread_rate']}. These figures have been used to determine "
            f"the severity classification and appropriate response actions for this outbreak."
        )
        lines.append("")

        lines.append("SEVERITY CLASSIFICATION")
        lines.append("")
        lines.append(
            f"  Following a comprehensive assessment of the case count, fatality rate, and "
            f"spread rate of this outbreak, the situation has been formally classified as:"
        )
        lines.append("")
        lines.append(f"  Severity Level  : {result['severity']}")
        lines.append(f"  Priority Level  : {msg['priority']}")
        lines.append(f"  Escalation Level: {msg['escalation_level']} of 3")
        lines.append("")
        lines.append(
            f"  This classification reflects the current intensity and trajectory of the "
            f"outbreak and will determine the level of response mobilisation required across "
            f"all government and health system levels."
        )
        lines.append("")

        lines.append("PRIORITY RESPONSE ACTIONS")
        lines.append("")
        lines.append(
            f"  Based on the severity classification above, the following response actions "
            f"have been identified and must be implemented immediately across all relevant "
            f"levels of government and the health system:"
        )
        lines.append("")
        for i, action in enumerate(msg["recommended_actions"], 1):
            lines.append(f"  {i}. {action}.")
        lines.append("")

        lines.append("STAKEHOLDER NOTIFICATION")
        lines.append("\nCOORDINATION HIERARCHY")
        lines.append("")
        hierarchy = result.get("coordination_hierarchy", {})
        if hierarchy:
            lines.append(
                f"  The following coordination levels have been activated "
                f"for this outbreak response:"
            )
            lines.append("")
            for level in sorted(
                hierarchy.get("levels", []),
                key=lambda x: x["tier"]
            ):
                lines.append(
                    f"  {level['level']} Level "
                    f"[Tier {level['tier']}] — {level['status']}"
                )
                for org in level["responsible"]:
                    lines.append(f"    - {org}")
                lines.append("")

            struct = hierarchy.get("reporting_structure", {})
            if struct:
                lines.append(
                    f"  Reporting Flow   : {struct.get('flow', '—')}"
                )
                lines.append(
                    f"  Reporting Freq   : {struct.get('frequency', '—')}"
                )
                lines.append(
                    f"  Lead Coordinator : "
                    f"{struct.get('primary_coordinator', '—')}"
                )
            lines.append("")
        lines.append(
            f"  A total of {result['total_stakeholder_groups']} stakeholder group(s) have "
            f"been identified for formal notification based on the severity level of this "
            f"outbreak. The following organisations and agencies are required to mobilise "
            f"their respective response capacities in alignment with the priority actions "
            f"listed above:"
        )
        lines.append("")
        notified = result.get("stakeholders_to_notify", {})
        for group, members in notified.items():
            lines.append(f"  {group.replace('_', ' ').title()}:")
            for m in members:
                lines.append(f"    - {m}")
            lines.append("")

        lines.append("COMMUNICATION NOTE")
        lines.append("")
        lines.append(
            f"  This report has been generated to support coordinated communication and "
            f"response efforts across all levels of the outbreak response structure. "
            f"All notified stakeholders are expected to acknowledge this report and provide "
            f"situation updates at regular intervals. Response activities should be guided "
            f"by the priority actions listed above and reviewed as the outbreak situation evolves."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)


# ─── Quick Test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cru = CommunicationResponseUnit()

    outbreak_data = {
        "disease": "Mpox",
        "region": "North Central Zone",
        "cases": 320,
        "deaths": 28,
        "fatality_rate": 0.087,
        "spread_rate": 0.65
    }

    result = cru.generate_full_response(outbreak_data)

    print("CRU Response Report:")
    print(f"  Disease          : {result['message']['disease']}")
    print(f"  Region           : {result['message']['affected_region']}")
    print(f"  Severity         : {result['severity']}")
    print(f"  Priority         : {result['message']['priority']}")
    print(f"  Total Cases      : {result['message']['total_cases']}")
    print(f"  Total Deaths     : {result['message']['total_deaths']}")
    print(f"  Fatality Rate    : {result['message']['fatality_rate']}")
    print(f"  Recommended Actions:")
    for action in result["message"]["recommended_actions"]:
        print(f"    - {action}")
    print(f"  Stakeholder Groups Notified: {result['total_stakeholder_groups']}")
    print("CRU subsystem loaded successfully!")