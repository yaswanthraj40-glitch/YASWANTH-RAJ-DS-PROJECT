"""
Tree Planting Optimization Engine
Uses scoring + greedy selection with real-world constraints
"""

import numpy as np
from typing import List, Dict, Optional

class PlantingOptimizer:
    def __init__(self):
        self.tree_species = {
            "neem": {"cost": 500, "cooling": 0.08, "growth": "Fast", "maintenance": 50},
            "gulmohar": {"cost": 350, "cooling": 0.06, "growth": "Medium", "maintenance": 40},
            "banyan": {"cost": 800, "cooling": 0.12, "growth": "Slow", "maintenance": 80},
            "peepal": {"cost": 600, "cooling": 0.10, "growth": "Medium", "maintenance": 60},
            "amaltas": {"cost": 400, "cooling": 0.05, "growth": "Fast", "maintenance": 45}
        }

    def calculate_priority_score(self, zone: Dict, equity_weight: float = 0.5) -> float:
        """
        Calculate planting priority score for a zone
        Higher score = higher priority
        """
        # Normalize features (0-1 scale)
        temp_norm = min(max((zone["temperature"] - 30) / 20, 0), 1)
        pop_norm = min(max(zone["population"] / 50000, 0), 1)
        income_vulnerability = 1 - min(max(zone["income"] / 10, 0), 1)

        # Equity-weighted social score
        social_score = (
            income_vulnerability * 0.4 * equity_weight +
            pop_norm * 0.3 +
            temp_norm * 0.3
        )

        # Cost effectiveness (simplified)
        plantable_area = 1000  # sqm assumption
        cost_per_tree = 500
        expected_cooling = temp_norm * 2.5

        roi_score = (expected_cooling * social_score) / (cost_per_tree / max(plantable_area, 1))

        return roi_score

    def optimize(self, budget: float, max_trees: int, zones: List[Dict], 
                 equity_weight: float = 0.5) -> Dict:
        """
        Generate optimized planting plan
        """
        # Calculate scores for all zones
        scored_zones = []
        for zone in zones:
            score = self.calculate_priority_score(zone, equity_weight)
            scored_zones.append({
                **zone,
                "priority_score": score,
                "recommended_trees": min(50, int((zone["temperature"] - 35) * 5)),
                "expected_cooling": round((zone["temperature"] - 35) * 0.15, 2)
            })

        # Sort by priority score (descending)
        scored_zones.sort(key=lambda x: x["priority_score"], reverse=True)

        # Greedy selection within budget
        selected_zones = []
        total_cost = 0
        total_trees = 0
        remaining_budget = budget

        for zone in scored_zones:
            if total_trees >= max_trees:
                break

            zone_cost = zone["recommended_trees"] * 500
            if zone_cost > remaining_budget:
                # Partial allocation
                affordable_trees = int(remaining_budget / 500)
                if affordable_trees > 0:
                    zone["recommended_trees"] = affordable_trees
                    zone["expected_cooling"] = round(affordable_trees * 0.08, 2)
                    selected_zones.append(zone)
                    total_cost += affordable_trees * 500
                    total_trees += affordable_trees
                break

            selected_zones.append(zone)
            total_cost += zone_cost
            total_trees += zone["recommended_trees"]
            remaining_budget -= zone_cost

        return {
            "total_budget": budget,
            "budget_used": total_cost,
            "budget_remaining": budget - total_cost,
            "total_trees": total_trees,
            "zones_selected": len(selected_zones),
            "expected_avg_cooling": round(
                sum(z["expected_cooling"] for z in selected_zones) / max(len(selected_zones), 1), 2
            ),
            "planting_plan": [
                {
                    "zone_id": z["id"],
                    "ward": z["ward"],
                    "coordinates": z["coordinates"][0],  # Center point
                    "temperature": z["temperature"],
                    "trees": z["recommended_trees"],
                    "cost": z["recommended_trees"] * 500,
                    "expected_cooling": z["expected_cooling"],
                    "priority_score": round(z["priority_score"], 4),
                    "species_recommended": "neem" if z["temperature"] > 42 else "gulmohar"
                }
                for z in selected_zones[:20]  # Top 20 zones
            ]
        }
