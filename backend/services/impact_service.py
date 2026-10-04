"""
CoolRoute Impact Service
Before/After intervention simulation.

All cooling, energy, and carbon values are:
- Derived from the ML model + scientific literature
- Labeled ESTIMATED with assumptions documented
- Never presented as measured facts
"""

import logging
import math
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Scientific basis for cooling estimates
# Bowler et al. (2010): urban trees cool 0.5-2°C in immediate vicinity
# Zupancic et al. (2015): 10% increase in tree canopy → ~1°C reduction
# Oke (1989): transpiration cooling coefficient ~0.05-0.12°C per mature tree
COOLING_METHODOLOGY = {
    "source": "Bowler et al. (2010), Zupancic et al. (2015), Oke (1989)",
    "approach": (
        "Each tree contributes avg_cooling_per_tree_c to LST reduction. "
        "NDVI increase from new canopy estimated as trees × canopy_area / grid_area. "
        "XGBoost model then predicts LST with updated NDVI and tree_cover inputs."
    ),
    "uncertainty": (
        "±1-2°C typical. Actual cooling depends on species survival rate (~70-85%), "
        "time to canopy maturity (3-5 years for meaningful effect), "
        "local wind patterns, and surrounding urban fabric."
    ),
}

# Energy savings: ~2-8% AC reduction per °C cooling (EPA estimate)
ENERGY_SAVINGS_KWH_PER_CELSIUS_PER_HOUSEHOLD = 150  # kWh/yr per °C per household
PEOPLE_PER_HOUSEHOLD = 4.3  # India average

# Carbon sequestration: ~22 kg CO2/yr per tree (varies widely)
CARBON_KG_PER_TREE_YR = 22


class ImpactService:
    """
    Simulates before/after tree planting impact.
    
    Uses ML model to predict "after" LST by updating NDVI and tree_cover
    based on planned tree additions. All outputs labeled ESTIMATED.
    """

    def __init__(self, ml_service):
        self.ml = ml_service

    def simulate(
        self,
        zones: List[Dict],
        planting_plan: List[Dict],
        tree_species_db: Optional[Dict] = None,
    ) -> Dict:
        """
        Run before/after simulation for a set of zones with a planting plan.

        Parameters
        ----------
        zones : list of grid cells with features (before state)
        planting_plan : output from OptimizationService.optimize()['planting_plan']
        tree_species_db : species cooling coefficients

        Returns
        -------
        dict with before/after comparison, labeled ESTIMATED
        """
        if tree_species_db is None:
            from services.optimization_service import TREE_SPECIES
            tree_species_db = TREE_SPECIES

        # Map planting plan by zone_id for lookup
        plan_by_zone = {p["zone_id"]: p for p in planting_plan}

        results = []
        total_before_pop_exposure = 0.0
        total_after_pop_exposure = 0.0
        total_trees = 0
        total_canopy_m2 = 0

        for zone in zones:
            zone_id = zone.get("grid_id")
            plan = plan_by_zone.get(zone_id)

            # BEFORE state
            lst_before = zone.get("predicted_lst_c", 35.0)
            risk_before = self._classify_risk(lst_before)
            tc_before = zone.get("existing_tree_cover", 0.1)
            ndvi_before = zone.get("ndvi", 0.3)
            pop = zone.get("population_density", 10000)
            area_km2 = zone.get("area_km2", 0.25)
            pop_total = pop * area_km2

            if plan:
                # AFTER state: update features based on new trees
                n_trees = plan.get("trees_recommended", 0)
                species = plan.get("species", "neem")
                sp_info = tree_species_db.get(species, tree_species_db["neem"])
                canopy_per_tree = sp_info.get("canopy_area_m2", 25)
                cooling_per_tree = sp_info.get("avg_cooling_per_tree_c", 0.08)

                area_m2 = area_km2 * 1_000_000
                new_canopy_m2 = n_trees * canopy_per_tree
                canopy_increase_fraction = min(0.3, new_canopy_m2 / area_m2)

                # Updated features for "after" prediction
                updated_features = {
                    **zone,
                    "existing_tree_cover": min(0.8, tc_before + canopy_increase_fraction),
                    "ndvi": min(0.75, ndvi_before + canopy_increase_fraction * 0.5),
                    # albedo decreases slightly with more vegetation
                    "albedo": max(0.10, zone.get("albedo", 0.25) - canopy_increase_fraction * 0.1),
                }

                # ML prediction for "after" state
                after_prediction = self.ml.predict(updated_features)
                lst_after = after_prediction.get("predicted_lst_c", lst_before)
                # Apply species-specific cooling (conservative: 70% survival rate)
                direct_cooling = n_trees * cooling_per_tree * 0.70
                lst_after_with_direct = round(lst_after - min(direct_cooling, 5.0), 2)
                lst_after_final = max(28.0, lst_after_with_direct)

                risk_after = self._classify_risk(lst_after_final)
                cooling_delta = round(lst_before - lst_after_final, 2)
                tc_after = updated_features["existing_tree_cover"]

                total_trees += n_trees
                total_canopy_m2 += new_canopy_m2
            else:
                # Zone not in planting plan
                lst_after_final = lst_before
                risk_after = risk_before
                cooling_delta = 0.0
                tc_after = tc_before
                n_trees = 0

            heat_exposure_before = lst_before * pop_total
            heat_exposure_after = lst_after_final * pop_total
            total_before_pop_exposure += heat_exposure_before
            total_after_pop_exposure += heat_exposure_after

            results.append({
                "zone_id": zone_id,
                "latitude": zone.get("latitude"),
                "longitude": zone.get("longitude"),
                "before": {
                    "predicted_lst_c": lst_before,
                    "heat_risk": risk_before["level"],
                    "heat_risk_color": risk_before["color"],
                    "tree_cover_pct": round(tc_before * 100, 1),
                    "ndvi": round(ndvi_before, 3),
                    "population": int(pop_total),
                },
                "after": {
                    "predicted_lst_c": lst_after_final,
                    "heat_risk": risk_after["level"],
                    "heat_risk_color": risk_after["color"],
                    "tree_cover_pct": round(tc_after * 100, 1),
                    "trees_added": n_trees,
                },
                "delta": {
                    "cooling_c": cooling_delta,
                    "tree_cover_increase_pct": round((tc_after - tc_before) * 100, 1),
                    "risk_improved": risk_after["level"] != risk_before["level"],
                },
                "is_estimated": True,
                "cooling_note": COOLING_METHODOLOGY["uncertainty"],
            })

        # City-wide summary
        avg_lst_before = total_before_pop_exposure / max(sum(
            z.get("population_density", 1) * z.get("area_km2", 0.25) for z in zones
        ), 1)
        avg_lst_after = total_after_pop_exposure / max(sum(
            z.get("population_density", 1) * z.get("area_km2", 0.25) for z in zones
        ), 1)

        treated_zones = [r for r in results if r["delta"]["cooling_c"] > 0]
        avg_cooling = (
            sum(r["delta"]["cooling_c"] for r in treated_zones) / len(treated_zones)
            if treated_zones else 0.0
        )

        # Energy savings estimate
        households = sum(
            z.get("population_density", 0) * z.get("area_km2", 0.25) / PEOPLE_PER_HOUSEHOLD
            for z in zones
            if z.get("grid_id") in plan_by_zone
        )
        energy_saved_kwh_yr = round(households * avg_cooling * ENERGY_SAVINGS_KWH_PER_CELSIUS_PER_HOUSEHOLD, 0)
        carbon_sequestered_kg_yr = total_trees * CARBON_KG_PER_TREE_YR

        return {
            "simulation_complete": True,
            "zones_treated": len(treated_zones),
            "total_zones": len(zones),
            "total_trees_planted": total_trees,
            "total_new_canopy_m2": int(total_canopy_m2),
            "zone_results": results,
            "summary": {
                "avg_lst_before_c": round(avg_lst_before, 2),
                "avg_lst_after_c": round(avg_lst_after, 2),
                "avg_cooling_c": round(avg_cooling, 2),
                "risk_upgrades": sum(1 for r in results if r["delta"]["risk_improved"]),
                "estimated_energy_saved_kwh_yr": int(energy_saved_kwh_yr),
                "estimated_carbon_sequestered_kg_yr": carbon_sequestered_kg_yr,
                "estimated_carbon_sequestered_tons_yr": round(carbon_sequestered_kg_yr / 1000, 1),
            },
            "methodology": COOLING_METHODOLOGY,
            "assumptions": {
                "tree_survival_rate": "70% (conservative estimate)",
                "cooling_per_tree": "Species-specific (0.06–0.12°C, from species DB)",
                "canopy_maturity": "Full effect at 3-5 years (values shown are at maturity)",
                "energy_savings": f"{ENERGY_SAVINGS_KWH_PER_CELSIUS_PER_HOUSEHOLD} kWh/yr per °C per household (EPA estimate)",
                "carbon": f"{CARBON_KG_PER_TREE_YR} kg CO₂/yr per tree (species average, varies widely)",
            },
            "is_estimated": True,
            "disclaimer": (
                "All 'after' values are ESTIMATED projections based on ML model predictions "
                "with updated feature inputs. They are NOT measured outcomes. "
                "Actual cooling depends on site conditions, species survival, and time."
            ),
        }

    def _classify_risk(self, lst: float) -> Dict:
        if lst >= 46:
            return {"level": "EXTREME", "color": "#ff0000"}
        elif lst >= 43:
            return {"level": "HIGH", "color": "#ff006e"}
        elif lst >= 40:
            return {"level": "MODERATE", "color": "#ffb703"}
        else:
            return {"level": "LOW", "color": "#00ff88"}
