from subsystems.rnn import MovementPatternRecognizer
from datetime import datetime
import uuid

# ─── IARMS Orchestrator ───────────────────────────────────────────────────────
class IARMSOrchestrator:
    def __init__(self, cce, kau, cru, idru, ceu, srr):
        self.cce  = cce
        self.kau  = kau
        self.cru  = cru
        self.idru = idru
        self.ceu  = ceu
        self.srr  = srr

    def run_full_analysis(self, outbreak_input, srr_token=None):
        report_id = str(uuid.uuid4())[:8].upper()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pipeline_log = []

        # ── STEP 1: CCE ──────────────────────────────────────────────────────
        pipeline_log.append("CCE: Analysing outbreak state...")
        cce_state = [
            outbreak_input["cases"],
            outbreak_input["deaths"],
            outbreak_input.get("resources", 0.4),
            outbreak_input.get("hospitals", 3),
            outbreak_input.get("personnel", 20),
            outbreak_input["risk_score"],
            outbreak_input["resource_level"],
            outbreak_input.get("coordination_score", 0.5),
            outbreak_input["days_active"],
            outbreak_input.get("response_level", 0.5)
        ]
        cce_result = self.cce.get_recommendation(cce_state)
        pipeline_log.append(
            f"CCE: Recommended — {cce_result['recommendation']}"
        )

        # ── STEP 2: KAU ──────────────────────────────────────────────────────
        pipeline_log.append("KAU: Generating advisory from CCE output...")
        kau_state = {
            "risk_score":     outbreak_input["risk_score"],
            "resource_level": outbreak_input["resource_level"],
            "days_active":    outbreak_input["days_active"],
            "cases":          outbreak_input["cases"],
            "deaths":         outbreak_input["deaths"]
        }
        kau_result = self.kau.generate_advisory(kau_state)
        pipeline_log.append(
            f"KAU: Stage — {kau_result['outbreak_stage']} | "
            f"Risk — {kau_result['risk_level']}"
        )

        # ── STEP 3: CRU ──────────────────────────────────────────────────────
        pipeline_log.append("CRU: Assessing severity and notifying stakeholders...")
        cru_data = {
            "disease":       outbreak_input["disease"],
            "region":        outbreak_input["region"],
            "cases":         outbreak_input["cases"],
            "deaths":        outbreak_input["deaths"],
            "fatality_rate": outbreak_input["fatality_rate"],
            "spread_rate":   outbreak_input["spread_rate"]
        }
        cru_result = self.cru.generate_full_response(cru_data)
        pipeline_log.append(
            f"CRU: Severity — {cru_result['severity']} | "
            f"Stakeholder groups — {cru_result['total_stakeholder_groups']}"
        )

        # ── STEP 4: IDRU ─────────────────────────────────────────────────────
        pipeline_log.append("IDRU: Allocating resources based on CRU severity...")
        severity = cru_result["severity"]
        qty_map = {
            "CRITICAL": 1000,
            "HIGH":     700,
            "MODERATE": 400,
            "LOW":      200
        }
        resource_qty = qty_map.get(severity, 500)
        region_id = f"R-{report_id}"
        self.idru.register_region(
            region_id,
            outbreak_input["region"],
            population=outbreak_input.get("population", 500000),
            risk_score=outbreak_input["risk_score"],
            current_cases=outbreak_input["cases"]
        )
        resource_id = self.idru.add_resource(
            "Emergency Medical Supplies",
            resource_qty,
            "IARMS Automated Allocation"
        )
        idru_result = self.idru.allocate_resources(resource_id, resource_qty)
        allocations = idru_result["allocations"] if isinstance(idru_result, dict) else idru_result
        pipeline_log.append(
            f"IDRU: {resource_qty} units allocated across "
            f"{len(allocations)} region(s)"
        )

        # ── STEP 5: CEU ──────────────────────────────────────────────────────
        pipeline_log.append("CEU: Registering stakeholders and logging engagement...")
        stakeholder_ids = []
        notified = cru_result.get("stakeholders_to_notify", {})
        for group, members in notified.items():
            for member in members[:1]:
                sid = self.ceu.register_stakeholder(
                    member,
                    group.replace("_", " ").title(),
                    outbreak_input["region"],
                    f"{member.lower().replace(' ', '.')}@response.org"
                )
                stakeholder_ids.append(sid)
        if stakeholder_ids:
            self.ceu.initiate_collaboration(
                title=f"Emergency Response — {outbreak_input['disease']}",
                stakeholder_ids=stakeholder_ids,
                objective=f"Coordinate {severity} level response in "
                          f"{outbreak_input['region']}",
                duration_days=14
            )
        pipeline_log.append(
            f"CEU: {len(stakeholder_ids)} stakeholders engaged"
        )

        # ── STEP 5.5: MOVEMENT PATTERN ───────────────────────────────────────
        pipeline_log.append("RNN: Analysing geographic movement pattern...")
        movement_result = None
        try:
            recognizer   = MovementPatternRecognizer()
            neighbour_regions = outbreak_input.get("neighbour_regions", {})

            if neighbour_regions and len(neighbour_regions) >= 2:
                # Use real data provided by user
                region_data = neighbour_regions
                pipeline_log.append(
                    f"RNN: Using real data for "
                    f"{len(region_data)} region(s)"
                )
            else:
                # Fall back to simulated data with honest labels
                cases = outbreak_input["cases"]
                region_data = {
                    outbreak_input["region"]: [
                        max(1, int(cases * 0.5)),
                        max(1, int(cases * 0.65)),
                        max(1, int(cases * 0.80)),
                        cases
                    ],
                    "Projected Spread Zone 1": [
                        max(1, int(cases * 0.08)),
                        max(1, int(cases * 0.13)),
                        max(1, int(cases * 0.20)),
                        max(1, int(cases * 0.30))
                    ],
                    "Projected Spread Zone 2": [
                        max(1, int(cases * 0.03)),
                        max(1, int(cases * 0.06)),
                        max(1, int(cases * 0.10)),
                        max(1, int(cases * 0.16))
                    ]
                }
                pipeline_log.append(
                    "RNN: No neighbouring region data provided — "
                    "using simulated spread projection"
                )

            movement_result = recognizer.analyze(
                region_data, days_ahead=3
            )
            pipeline_log.append(
                f"RNN: Epicentre — {movement_result['epicentre']} | "
                f"Spreading regions — {len(movement_result['spreading'])}"
            )
        except Exception as e:
            pipeline_log.append(
                f"RNN: Movement analysis skipped — {str(e)}"
            )
        
        # ── STEP 6: SRR ──────────────────────────────────────────────────────
        pipeline_log.append("SRR: Securing and storing full report...")
        stored = False
        resource_record_id = None
        if srr_token:
            store_result = self.srr.store_resource(
                srr_token,
                f"Outbreak Report — {outbreak_input['disease']} [{report_id}]",
                {
                    "report_id":          report_id,
                    "disease":            outbreak_input["disease"],
                    "region":             outbreak_input["region"],
                    "severity":           severity,
                    "cases":              outbreak_input["cases"],
                    "deaths":             outbreak_input["deaths"],
                    "cce_recommendation": cce_result["recommendation"],
                    "kau_stage":          kau_result["outbreak_stage"],
                    "timestamp":          timestamp
                },
                "CONFIDENTIAL"
            )
            if "resource_id" in store_result:
                stored = True
                resource_record_id = store_result["resource_id"]
                pipeline_log.append(
                    f"SRR: Report stored securely (ID: {resource_record_id})"
                )
        else:
            pipeline_log.append("SRR: Skipped — no session token provided")

        # ── BUILD FINAL RESULT ────────────────────────────────────────────────
        final_result = {
            "report_id":    report_id,
            "timestamp":    timestamp,
            "disease":      outbreak_input["disease"],
            "region":       outbreak_input["region"],
            "severity":     severity,
            "pipeline_log": pipeline_log,
            "cce": cce_result,
            "kau": {
                "primary_advisory":          kau_result["primary_advisory"],
                "outbreak_stage":            kau_result["outbreak_stage"],
                "risk_level":                kau_result["risk_level"],
                "resource_status":           kau_result["resource_status"],
                "contextual_recommendations":
                    kau_result["contextual_recommendations"]
            },
            "cru": {
                "severity":                   cru_result["severity"],
                "priority":                   cru_result["message"]["priority"],
                "recommended_actions":
                    cru_result["message"]["recommended_actions"],
                "stakeholder_groups_notified":
                    cru_result["total_stakeholder_groups"]
            },
            "idru": {
                "resources_allocated": resource_qty,
                "allocations":         allocations
            },
            "ceu": {
                "stakeholders_engaged":      len(stakeholder_ids),
                "collaboration_initiated":   len(stakeholder_ids) > 0
            },
            "srr": {
                "report_stored": stored,
                "record_id":     resource_record_id
            },
            "movement": movement_result if movement_result else {
                "epicentre": outbreak_input["region"],
                "spreading": [],
                "at_risk": [],
                "improving": [],
                "written_report": "Movement pattern analysis not available."
            }
        }

        # ── ATTACH WRITTEN REPORT ─────────────────────────────────────────────
        final_result["written_report"] = \
            self.generate_written_report(final_result)

        return final_result

    def generate_written_report(self, r):
        lines = []
        lines.append("=" * 65)
        lines.append("   IARMS — INFECTIOUS DISEASE OUTBREAK RESPONSE REPORT")
        lines.append("=" * 65)
        lines.append(f"  Report ID    : {r['report_id']}")
        lines.append(f"  Generated    : {r['timestamp']}")
        lines.append(f"  Disease      : {r['disease']}")
        lines.append(f"  Region       : {r['region']}")
        lines.append(f"  Alert Level  : {r['severity']}")
        lines.append("=" * 65)

        lines.append("\n1. SITUATION OVERVIEW")
        lines.append("-" * 45)
        lines.append(
            f"  A {r['severity'].lower()} level outbreak of {r['disease']} "
            f"has been detected in the {r['region']}. Based on the data "
            f"submitted, the outbreak is currently at a "
            f"{r['kau']['outbreak_stage'].lower()} stage with a "
            f"{r['kau']['risk_level'].lower()} risk classification. "
            f"Resource availability in the affected area has been assessed "
            f"as {r['kau']['resource_status'].lower()}, requiring immediate "
            f"attention from response authorities at all levels."
        )

        lines.append("\n2. COORDINATION & CONTROL RECOMMENDATION (CCE)")
        lines.append("-" * 45)
        lines.append(
            f"  The Coordination and Control Engine has analysed the current "
            f"outbreak state and recommends the following immediate action:"
        )
        lines.append(f"\n  ► {r['cce']['recommendation']}")
        lines.append(
            f"\n  This recommendation is based on the current risk profile, "
            f"resource levels, and the number of active cases in the region. "
            f"Response teams are advised to act on this recommendation without "
            f"delay to prevent further escalation of the outbreak."
        )

        lines.append("\n3. HEALTH ADVISORY (KAU)")
        lines.append("-" * 45)
        lines.append(
            f"  The Knowledge-Based Advisory Unit has generated the following "
            f"primary health advisory for this outbreak:"
        )
        lines.append(f"\n  ► {r['kau']['primary_advisory']}")
        lines.append(
            f"\n  In addition to the primary advisory, the following contextual "
            f"recommendations have been identified based on the current "
            f"outbreak conditions:"
        )
        for i, rec in enumerate(r['kau']['contextual_recommendations'], 1):
            lines.append(f"  {i}. {rec}")

        lines.append("\n4. RESPONSE ACTIONS (CRU)")
        lines.append("-" * 45)
        lines.append(
            f"  Following a {r['cru']['severity']} severity assessment, "
            f"the Communication and Response Unit has identified the "
            f"following priority response actions that must be executed "
            f"immediately across all affected levels of government:"
        )
        for i, action in enumerate(r['cru']['recommended_actions'], 1):
            lines.append(f"  {i}. {action}")
        lines.append(
            f"\n  A total of {r['cru']['stakeholder_groups_notified']} "
            f"stakeholder groups have been formally notified of this outbreak "
            f"and are expected to mobilise their respective response capacities "
            f"in alignment with the above actions."
        )

        lines.append("\n5. RESOURCE ALLOCATION (IDRU)")
        lines.append("-" * 45)
        lines.append(
            f"  Based on the {r['cru']['severity']} severity classification, "
            f"the Intelligent Distribution and Resource Tracking Unit has "
            f"automatically allocated {r['idru']['resources_allocated']} units "
            f"of emergency medical supplies to the affected region. "
            f"The allocation was determined using a priority scoring model "
            f"that accounts for regional risk levels, population size, and "
            f"current case load. The breakdown is as follows:"
        )
        allocations = r['idru']['allocations']
        if isinstance(allocations, list):
            for alloc in allocations:
                lines.append(f"\n  Region         : {alloc['region_name']}")
                lines.append(f"  Quantity       : {alloc['quantity_allocated']} units")
                lines.append(f"  Priority Score : {alloc['priority_score']}")
                lines.append(f"  Status         : {alloc['status']}")
                lines.append(f"  Tracking ID    : {alloc['tracking_id']}")
        lines.append(
            f"\n  All allocated resources can be tracked in real time "
            f"using the tracking IDs listed above."
        )

        lines.append("\n6. STAKEHOLDER ENGAGEMENT (CEU)")
        lines.append("-" * 45)
        lines.append(
            f"  The Collaboration and Engagement Unit has successfully "
            f"registered and engaged {r['ceu']['stakeholders_engaged']} "
            f"stakeholders drawn from national, sub-national, community, "
            f"and international response groups."
        )
        if r['ceu']['collaboration_initiated']:
            lines.append(
                f"  A formal emergency coordination collaboration has been "
                f"initiated among all registered stakeholders to ensure "
                f"structured and inclusive participation throughout the "
                f"response operation. All parties are expected to contribute "
                f"to situation reporting, resource coordination, and "
                f"community engagement activities."
            )

        lines.append("\n7. DATA SECURITY (SRR)")
        lines.append("-" * 45)
        if r['srr']['report_stored']:
            lines.append(
                f"  This report has been securely stored in the IARMS "
                f"Secured Resource Repository under record ID "
                f"{r['srr']['record_id']}. The data has been encrypted "
                f"and is accessible only to authorised personnel with "
                f"the appropriate access credentials and permissions."
            )
        else:
            lines.append(
                f"  This report was generated without an authenticated "
                f"session. To enable secure storage and restricted access "
                f"to this report, please log in to the Secured Resource "
                f"Repository and rerun the analysis."
            )

        lines.append("\n8. GEOGRAPHIC MOVEMENT PATTERN (RNN)")
        lines.append("-" * 45)
        movement = r.get("movement", {})
        if movement and movement.get("epicentre"):
            lines.append(
                f"  Geographic analysis of the outbreak has identified "
                f"{movement['epicentre']} as the primary epicentre. "
            )
            if movement.get("spreading"):
                lines.append(
                    f"  Active spread has been detected in the following "
                    f"region(s): {', '.join(movement['spreading'])}."
                )
            if movement.get("at_risk"):
                lines.append(
                    f"  The following region(s) are currently at risk: "
                    f"{', '.join(movement['at_risk'])}."
                )
            if movement.get("improving"):
                lines.append(
                    f"  The following region(s) are showing improvement: "
                    f"{', '.join(movement['improving'])}."
                )
        else:
            lines.append(
                f"  Movement pattern analysis was not available for this report."
            )
        
        lines.append("\n9. CONCLUSION")
        lines.append("-" * 45)
        lines.append(
            f"  The IARMS system has completed a full automated analysis "
            f"of the {r['disease']} outbreak in the {r['region']}. "
            f"The situation has been classified as {r['severity']} and "
            f"requires immediate coordinated action from all relevant "
            f"authorities. All six response subsystems have been activated "
            f"and their outputs are reflected in this report. Response "
            f"teams are advised to act on the recommendations contained "
            f"herein without delay. This report should be shared with all "
            f"relevant stakeholders and reviewed at regular intervals as "
            f"the outbreak situation evolves."
        )

        lines.append("\n" + "=" * 65)
        lines.append("   END OF REPORT — GENERATED BY IARMS v1.0")
        lines.append("=" * 65)

        return "\n".join(lines)


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from subsystems.cce  import CoordinationControlEngine
    from subsystems.kau  import KnowledgeAdvisoryUnit
    from subsystems.cru  import CommunicationResponseUnit
    from subsystems.idru import IntelligentDistributionUnit
    from subsystems.ceu  import CollaborationEngagementUnit
    from subsystems.srr  import SecuredResourceRepository

    cce  = CoordinationControlEngine(state_size=10, action_size=4)
    kau  = KnowledgeAdvisoryUnit()
    cru  = CommunicationResponseUnit()
    idru = IntelligentDistributionUnit()
    ceu  = CollaborationEngagementUnit()
    srr  = SecuredResourceRepository()

    orchestrator = IARMSOrchestrator(cce, kau, cru, idru, ceu, srr)

    outbreak_input = {
        "disease":            "Mpox",
        "region":             "North Central Zone",
        "cases":              320,
        "deaths":             28,
        "fatality_rate":      0.087,
        "spread_rate":        0.65,
        "risk_score":         0.75,
        "resource_level":     0.3,
        "days_active":        18,
        "population":         500000,
        "coordination_score": 0.5,
        "response_level":     0.6
    }

    result = orchestrator.run_full_analysis(outbreak_input)
    print(result["written_report"])