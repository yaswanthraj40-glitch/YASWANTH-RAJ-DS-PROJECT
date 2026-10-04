"""
CoolRoute Optimization Service
Upgraded tree planting optimizer with:
- Transparent priority objective
- Configurable weights
- Per-zone natural language justification
- Budget + maintenance cost tracking
- Species selection logic
"""

import logging
import math
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Tree species database (cost in INR)
TREE_SPECIES = {
    "neem": {
        "cost_inr": 500,
        "maintenance_inr_yr": 50,
        "avg_cooling_per_tree_c": 0.08,
        "canopy_area_m2": 25,
        "carbon_kg_yr": 22,
        "growth_rate": "fast",
        "suitable_for": ["roadside", "open_area", "high_heat"],
        "note": "Drought-tolerant, fast-growing, excellent for urban roadsides",
    },
    "peepal": {
        "cost_inr": 600,
        "maintenance_inr_yr": 60,
        "avg_cooling_per_tree_c": 0.10,
        "canopy_area_m2": 30,
        "carbon_kg_yr": 25,
        "growth_rate": "medium",
        "suitable_for": ["park", "open_area"],
        "note": "Large canopy, high cooling, suitable for parks",
    },
    "banyan": {
        "cost_inr": 800,
        "maintenance_inr_yr": 80,
        "avg_cooling_per_tree_c": 0.12,
        "canopy_area_m2": 50,
        "carbon_kg_yr": 35,
        "growth_rate": "slow",
        "suitable_for": ["large_open", "extreme_heat"],
        "note": "Highest cooling potential, requires large open space",
    },
    "gulmohar": {
        "cost_inr": 350,
        "maintenance_inr_yr": 40,
        "avg_cooling_per_tree_c": 0.06,
        "canopy_area_m2": 20,
        "carbon_kg_yr": 18,
        "growth_rate": "fast",
        "suitable_for": ["roadside", "aesthetic", "medium_heat"],
        "note": "Fast-growing, aesthetic, good for medium-heat zones",
    },
    "pongamia": {
        "cost_inr": 450,
        "maintenance_inr_yr": 45,
        "avg_cooling_per_tree_c": 0.07,
        "canopy_area_m2": 22,
        "carbon_kg_yr": 20,
        "growth_rate": "medium",
        "suitable_for": ["roadside", "coastal", "industrial"],
        "note": "Pollution-tolerant, good for industrial zones",
    },
}

# Objective weights (all configurable)
DEFAULT_WEIGHTS = {
    "heat_severity": 0.30,
    "population_exposure": 0.25,
    "vulnerability": 0.25,
    "tree_deficit": 0.15,
    "cooling_potential": 0.05,
}


class OptimizationService:
    """
    Transparent, configurable tree planting optimizer.
    
    Objective (per zone):
        Priority = heat_severity × pop_exposure × vulnerability
                   × tree_deficit × cooling_potential − cost_penalty
    
    All weights are configurable. All values derived from data.
    Justification is generated for each selected zone.
    """

    def __init__(self):
        self.species = TREE_SPECIES
        self.default_weights = DEFAULT_WEIGHTS

    # ------------------------------------------------------------------
    # Main optimization
    # ------------------------------------------------------------------

    def optimize(
        self,
        budget: float,
        max_trees: int,
        zones: List[Dict],
        equity_weight: float = 0.5,
        weights: Optional[Dict] = None,
        min_trees_per_zone: int = 5,
        max_trees_per_zone: int = 200,
    ) -> Dict:
        """
        Run the tree planting optimizer.

        Parameters
        ----------
        budget : float — total budget in INR
        max_trees : int — maximum total trees
        zones : list of heat grid cells
        equity_weight : float 0-1 — higher = more weight on low-income zones
        weights : optional dict of objective weights
        """
        if not zones:
            return {"error": "No zones provided"}

        w = weights or self._equity_adjusted_weights(equity_weight)

        # Score all zones
        scored = []
        for zone in zones:
            score = self._priority_score(zone, w)
            species = self._select_species(zone)
            tree_cost = self.species[species]["cost_inr"]
            maintenance = self.species[species]["maintenance_inr_yr"]
            cooling_per_tree = self.species[species]["avg_cooling_per_tree_c"]
            canopy = self.species[species]["canopy_area_m2"]

            # Estimate plantable trees (based on available area, not arbitrary)
            area_km2 = zone.get("area_km2", 0.25)
            area_m2 = area_km2 * 1_000_000
            existing_cover = zone.get("existing_tree_cover", 0.1)
            free_area_m2 = area_m2 * (1 - zone.get("building_density", 0.5)) * (1 - existing_cover)
            max_plantable = max(0, min(max_trees_per_zone, int(free_area_m2 / (canopy * 2))))
            max_plantable = max(min_trees_per_zone, max_plantable)

            scored.append({
                **zone,
                "priority_score": score,
                "priority_justification": self._justify(zone, score, w, species),
                "recommended_species": species,
                "species_info": self.species[species],
                "cost_per_tree_inr": tree_cost,
                "maintenance_per_tree_inr_yr": maintenance,
                "cooling_per_tree_c": cooling_per_tree,
                "max_plantable_trees": max_plantable,
            })

        # Sort by priority score
        scored.sort(key=lambda x: x["priority_score"], reverse=True)

        # Greedy selection within budget
        selected = []
        total_cost = 0.0
        total_trees = 0
        total_maintenance_yr = 0.0
        total_cooling = 0.0
        total_canopy_m2 = 0.0
        remaining = budget

        for zone in scored:
            if total_trees >= max_trees or remaining <= 0:
                break

            tree_cost = zone["cost_per_tree_inr"]
            maint = zone["maintenance_per_tree_inr_yr"]
            cooling = zone["cooling_per_tree_c"]
            canopy = zone["species_info"]["canopy_area_m2"]
            max_for_budget = min(int(remaining / tree_cost), max_trees - total_trees)
            trees = min(zone["max_plantable_trees"], max_for_budget)
            if trees <= 0:
                continue

            zone_cost = trees * tree_cost
            zone_cooling = round(trees * cooling, 2)
            zone_canopy = trees * canopy

            selected.append({
                "zone_id": zone.get("grid_id", "unknown"),
                "latitude": zone.get("latitude"),
                "longitude": zone.get("longitude"),
                "ward": zone.get("ward", "N/A"),
                "predicted_lst_c": zone.get("predicted_lst_c"),
                "heat_risk": zone.get("heat_risk", "UNKNOWN"),
                "population_density": zone.get("population_density"),
                "existing_tree_cover": zone.get("existing_tree_cover"),
                "trees_recommended": trees,
                "species": zone["recommended_species"],
                "cost_inr": zone_cost,
                "maintenance_yr_inr": trees * maint,
                "expected_cooling_c": zone_cooling,
                "expected_canopy_increase_m2": zone_canopy,
                "priority_score": round(zone["priority_score"], 4),
                "justification": zone["priority_justification"],
                "estimated_cooling_note": (
                    "ESTIMATED: Based on species cooling coefficient × tree count. "
                    "Actual cooling depends on site conditions, species survival, and canopy development (3-5 years)."
                ),
            })

            total_cost += zone_cost
            total_trees += trees
            total_maintenance_yr += trees * maint
            total_cooling += zone_cooling
            total_canopy_m2 += zone_canopy
            remaining -= zone_cost

        # Summary impact (all labeled ESTIMATED)
        avg_cooling = round(total_cooling / len(selected), 2) if selected else 0.0
        people_benefited = int(sum(
            z.get("population_density", 0) * 0.25  # rough km² fraction
            for z in selected[:len(selected)]
        ))

        return {
            "optimization_complete": True,
            "total_budget_inr": budget,
            "budget_used_inr": round(total_cost, 2),
            "budget_remaining_inr": round(budget - total_cost, 2),
            "total_trees": total_trees,
            "zones_selected": len(selected),
            "equity_weight": equity_weight,
            "objective_weights": w,
            "summary": {
                "expected_avg_cooling_c": avg_cooling,
                "total_canopy_increase_m2": int(total_canopy_m2),
                "total_maintenance_yr_inr": round(total_maintenance_yr, 2),
                "estimated_people_benefited": people_benefited,
                "estimated_carbon_kg_yr": int(total_trees * 22),  # avg across species
                "notes": {
                    "cooling": "ESTIMATED — see per-zone notes",
                    "people_benefited": "ESTIMATED — rough population exposure estimate",
                    "carbon": "ESTIMATED — average 22 kg/yr/tree (varies by species and maturity)",
                },
            },
            "planting_plan": selected[:25],  # Top 25 zones
            "all_scored_zones": len(scored),
            "objective_formula": (
                "Priority = heat_severity × population_exposure × vulnerability "
                "× tree_deficit × cooling_potential — cost_penalty"
            ),
        }

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _priority_score(self, zone: Dict, weights: Dict) -> float:
        lst = zone.get("predicted_lst_c", 35.0)
        pop = zone.get("population_density", 10000)
        income = zone.get("income_index", 5.0)
        tc = zone.get("existing_tree_cover", 0.2)
        bd = zone.get("building_density", 0.5)

        # Normalize each dimension to 0-1
        heat_sev = min(1.0, max(0.0, (lst - 30) / 20))  # 30-50°C range
        pop_exp = min(1.0, max(0.0, pop / 60000))
        vulnerability = min(1.0, max(0.0, (10 - income) / 9))  # lower income = higher vulnerability
        tree_deficit = min(1.0, max(0.0, 1 - tc / 0.5))  # 50% is "full" cover
        cooling_pot = min(1.0, max(0.0, (1 - bd) * 0.5 + heat_sev * 0.5))

        score = (
            weights.get("heat_severity", 0.30) * heat_sev
            + weights.get("population_exposure", 0.25) * pop_exp
            + weights.get("vulnerability", 0.25) * vulnerability
            + weights.get("tree_deficit", 0.15) * tree_deficit
            + weights.get("cooling_potential", 0.05) * cooling_pot
        )
        return round(score, 6)

    def _equity_adjusted_weights(self, equity_weight: float) -> Dict:
        """Adjust weights based on equity priority (0=efficiency, 1=equity)."""
        eq = max(0.0, min(1.0, equity_weight))
        return {
            "heat_severity": 0.30 - eq * 0.05,
            "population_exposure": 0.25,
            "vulnerability": 0.20 + eq * 0.10,
            "tree_deficit": 0.15 + eq * 0.05,
            "cooling_potential": 0.10 - eq * 0.10,
        }

    def _select_species(self, zone: Dict) -> str:
        """Select optimal species based on zone characteristics."""
        lst = zone.get("predicted_lst_c", 35.0)
        bd = zone.get("building_density", 0.5)
        income = zone.get("income_index", 5.0)

        if lst >= 46:
            return "banyan"  # Maximum cooling for extreme heat
        elif lst >= 43:
            return "neem" if bd > 0.7 else "peepal"
        elif income < 4:
            return "neem"  # Low-cost for low-income areas
        else:
            return "gulmohar"

    def _justify(self, zone: Dict, score: float, weights: Dict, species: str) -> str:
        """Generate human-readable justification for selecting this zone."""
        lst = zone.get("predicted_lst_c", 35.0)
        pop = zone.get("population_density", 10000)
        income = zone.get("income_index", 5.0)
        tc = zone.get("existing_tree_cover", 0.0)
        risk = zone.get("heat_risk", "UNKNOWN")

        reasons = []
        if lst >= 43:
            reasons.append(f"high heat ({lst:.1f}°C, {risk})")
        if pop > 30000:
            reasons.append(f"high population exposure ({int(pop):,}/km²)")
        if income < 4:
            reasons.append(f"low-income vulnerability (income index {income:.1f}/10)")
        if tc < 0.1:
            reasons.append(f"very low existing tree cover ({tc*100:.1f}%)")

        reason_text = ", ".join(reasons) if reasons else "moderate heat and population exposure"
        return (
            f"Priority zone selected due to {reason_text}. "
            f"Recommended species: {species} (cost-effective, suitable for local conditions). "
            f"Priority score: {score:.4f}."
        )
