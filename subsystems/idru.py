import numpy as np
from datetime import datetime
import uuid

# ─── Intelligent Distribution & Resource Tracking Unit ───────────────────────
class IntelligentDistributionUnit:
    def __init__(self):
        self.resource_registry = {}
        self.distribution_log = []
        self.regions = {}

        self.resource_types = [
            "Personal Protective Equipment",
            "Vaccines",
            "Antiviral Medications",
            "Medical Personnel",
            "Testing Kits",
            "Oxygen Supplies",
            "Food and Water Supplies",
            "Ambulances and Transport"
        ]

    def register_region(self, region_id, region_name, population,
                        risk_score, current_cases):
        self.regions[region_id] = {
            "name": region_name,
            "population": population,
            "risk_score": risk_score,
            "current_cases": current_cases,
            "resources_allocated": {},
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def add_resource(self, resource_type, quantity, source):
        resource_id = str(uuid.uuid4())[:8].upper()
        self.resource_registry[resource_id] = {
            "resource_id": resource_id,
            "type": resource_type,
            "total_quantity": quantity,
            "available_quantity": quantity,
            "source": source,
            "status": "Available",
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return resource_id

    def calculate_priority_score(self, region):
        score = (
            region["risk_score"] * 0.4 +
            (region["current_cases"] / max(region["population"], 1)) * 0.4 +
            (1 / max(len(region["resources_allocated"]), 1)) * 0.2
        )
        return round(score, 4)

    def allocate_resources(self, resource_id, total_quantity):
        if not self.regions:
            return {"error": "No regions registered"}

        if resource_id not in self.resource_registry:
            return {"error": "Resource not found"}

        # Score and rank all regions
        region_scores = []
        for rid, region in self.regions.items():
            score = self.calculate_priority_score(region)
            region_scores.append((rid, score))

        region_scores.sort(key=lambda x: x[1], reverse=True)

        # Distribute proportionally by priority score
        total_score = sum(score for _, score in region_scores)
        allocations = []

        remaining = total_quantity
        for i, (rid, score) in enumerate(region_scores):
            if i == len(region_scores) - 1:
                allocated = remaining
            else:
                allocated = round((score / total_score) * total_quantity)
                remaining -= allocated

            self.regions[rid]["resources_allocated"][resource_id] = allocated

            allocation_record = {
                "tracking_id": str(uuid.uuid4())[:8].upper(),
                "resource_id": resource_id,
                "resource_type": self.resource_registry[resource_id]["type"],
                "region_id": rid,
                "region_name": self.regions[rid]["name"],
                "quantity_allocated": allocated,
                "priority_score": score,
                "status": "Dispatched",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.distribution_log.append(allocation_record)
            allocations.append(allocation_record)

        self.resource_registry[resource_id]["available_quantity"] -= total_quantity
        self.resource_registry[resource_id]["status"] = "Distributed"
        
        written = self.generate_written_report(
            allocations,
            self.resource_registry[resource_id]["type"],
            total_quantity
        )
        return {"allocations": allocations, "written_report": written}
        
    def get_tracking_report(self):
        report = {
            "total_resources_registered": len(self.resource_registry),
            "total_regions": len(self.regions),
            "total_distributions": len(self.distribution_log),
            "distribution_log": self.distribution_log,
            "resource_status": [
                {
                    "resource_id": rid,
                    "type": r["type"],
                    "total": r["total_quantity"],
                    "available": r["available_quantity"],
                    "status": r["status"]
                }
                for rid, r in self.resource_registry.items()
            ]
        }
        if self.distribution_log:
            report["written_report"] = self.generate_written_report(
                self.distribution_log,
                "All Resources",
                sum(r["total_quantity"] for r in self.resource_registry.values())
            )
        else:
            report["written_report"] = (
                "INTELLIGENT DISTRIBUTION AND TRACKING UNIT\n"
                "Resource Allocation and Tracking Report\n\n"
                "No allocations have been recorded yet. Register a region "
                "and add a resource to generate a full tracking report."
            )
        return report
    
    def generate_written_report(self, allocations, resource_type, total_qty):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("INTELLIGENT DISTRIBUTION AND TRACKING UNIT")
        lines.append("Resource Allocation and Tracking Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("ALLOCATION SUMMARY")
        lines.append("")
        lines.append(
            f"  The Intelligent Distribution and Tracking Unit has completed an automated "
            f"resource allocation exercise for this outbreak response. A total of {total_qty} "
            f"units of {resource_type} have been allocated across {len(allocations)} affected "
            f"region(s). Allocations were determined using a priority scoring model that "
            f"accounts for each region's risk level, current case load relative to population, "
            f"and existing resource availability. Regions with higher risk and greater need "
            f"received a proportionally larger share of the available resources."
        )
        lines.append("")

        lines.append("REGION-BY-REGION ALLOCATION BREAKDOWN")
        lines.append("")
        for i, alloc in enumerate(allocations, 1):
            lines.append(f"  Region {i}: {alloc['region_name']}")
            lines.append(
                f"  A total of {alloc['quantity_allocated']} units of {alloc['resource_type']} "
                f"have been allocated to this region based on a priority score of "
                f"{alloc['priority_score']}. The allocation has been dispatched and assigned "
                f"a unique tracking identifier of {alloc['tracking_id']} for monitoring purposes. "
                f"Current dispatch status: {alloc['status']}."
            )
            lines.append("")

        lines.append("TRACKING AND ACCOUNTABILITY")
        lines.append("")
        lines.append(
            f"  Every allocation listed in this report has been assigned a unique tracking "
            f"identifier. Response coordinators are advised to use these identifiers to "
            f"monitor the delivery status of each allocation and verify that resources have "
            f"reached their intended destinations. Any discrepancies or delivery failures "
            f"should be reported immediately to the relevant coordination authority for "
            f"follow-up action."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)


# ─── Quick Test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    idru = IntelligentDistributionUnit()

    # Register regions
    idru.register_region("R001", "North Central Zone",
                         population=500000, risk_score=0.85,
                         current_cases=320)
    idru.register_region("R002", "South West Zone",
                         population=750000, risk_score=0.55,
                         current_cases=120)
    idru.register_region("R003", "North East Zone",
                         population=300000, risk_score=0.70,
                         current_cases=210)

    # Add resources
    res1 = idru.add_resource("Testing Kits", 1000, "Federal Ministry of Health")
    res2 = idru.add_resource("Personal Protective Equipment",
                             500, "WHO Emergency Supply")

    # Allocate resources
    allocations = idru.allocate_resources(res1, 1000)

    print("IDRU Distribution Report:")
    print(f"  Resource Type : Testing Kits")
    print(f"  Total Quantity: 1000")
    print(f"  Allocations   :")
    for alloc in allocations:
        print(f"    - {alloc['region_name']:<25} "
              f"Qty: {alloc['quantity_allocated']:<6} "
              f"Priority Score: {alloc['priority_score']:<8} "
              f"Status: {alloc['status']} "
              f"Tracking ID: {alloc['tracking_id']}")

    report = idru.get_tracking_report()
    print(f"\n  Total Resources Registered : {report['total_resources_registered']}")
    print(f"  Total Regions              : {report['total_regions']}")
    print(f"  Total Distributions        : {report['total_distributions']}")
    print("IDRU subsystem loaded successfully!")