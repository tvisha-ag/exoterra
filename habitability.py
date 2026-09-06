"""
ExoTerra - Habitability Scoring Module
Evaluates planetary habitability on multiple criteria
"""

import numpy as np
from typing import Dict, List, Tuple
from planetary_state import PlanetaryState
from constants import *

class HabitabilityIndex:
    """
    Comprehensive habitability scoring system
    Returns score from 0 (completely uninhabitable) to 100 (Earth-like)
    """
    
    def __init__(self):
        self.weights = {
            'temperature': 0.25,
            'pressure': 0.15,
            'water': 0.20,
            'oxygen': 0.15,
            'uv_protection': 0.10,
            'magnetic_field': 0.05,
            'atmospheric_stability': 0.10,
        }
    
    def calculate(self, state: PlanetaryState) -> Dict:
        """
        Calculate habitability index and component scores
        
        Returns:
        --------
        dict : {
            'total_score': float (0-100),
            'component_scores': dict,
            'limiting_factors': list,
            'classification': str
        }
        """
        
        scores = {}
        
        # 1. Temperature Score
        scores['temperature'] = self._score_temperature(state)
        
        # 2. Pressure Score
        scores['pressure'] = self._score_pressure(state)
        
        # 3. Water Availability
        scores['water'] = self._score_water(state)
        
        # 4. Oxygen Levels
        scores['oxygen'] = self._score_oxygen(state)
        
        # 5. UV Protection
        scores['uv_protection'] = self._score_uv_protection(state)
        
        # 6. Magnetic Field
        scores['magnetic_field'] = self._score_magnetic_field(state)
        
        # 7. Atmospheric Stability
        scores['atmospheric_stability'] = self._score_atmospheric_stability(state)
        
        # Calculate weighted total
        total_score = sum(scores[key] * self.weights[key] for key in self.weights)
        total_score *= 100  # Convert to 0-100 scale
        
        # Identify limiting factors (scores < 50%)
        limiting_factors = [key for key, score in scores.items() if score < 0.5]
        
        # Classify habitability
        classification = self._classify_habitability(total_score, scores)
        
        return {
            'total_score': total_score,
            'component_scores': {k: v * 100 for k, v in scores.items()},
            'limiting_factors': limiting_factors,
            'classification': classification,
            'earth_similarity_index': self._earth_similarity_index(state),
        }
    
    def _score_temperature(self, state: PlanetaryState) -> float:
        """
        Score temperature suitability
        Optimal: 0-30°C (273-303 K)
        Tolerable: -20 to 50°C
        """
        temp_c = state.surface_temperature - 273.15
        
        if 0 <= temp_c <= 30:
            return 1.0
        elif -20 <= temp_c < 0:
            return 1.0 - abs(temp_c) / 20 * 0.3
        elif 30 < temp_c <= 50:
            return 1.0 - (temp_c - 30) / 20 * 0.3
        elif -50 <= temp_c < -20:
            return 0.5 - (abs(temp_c) - 20) / 30 * 0.5
        elif 50 < temp_c <= 80:
            return 0.5 - (temp_c - 50) / 30 * 0.5
        else:
            return 0.0
    
    def _score_pressure(self, state: PlanetaryState) -> float:
        """
        Score atmospheric pressure
        Optimal: 0.5-2.0 bar
        Tolerable: 0.1-5.0 bar
        """
        pressure_bar = state.surface_pressure / 1e5
        
        if 0.5 <= pressure_bar <= 2.0:
            return 1.0
        elif 0.1 <= pressure_bar < 0.5:
            return (pressure_bar - 0.1) / 0.4 * 0.5 + 0.5
        elif 2.0 < pressure_bar <= 5.0:
            return 1.0 - (pressure_bar - 2.0) / 3.0 * 0.5
        elif 0.01 <= pressure_bar < 0.1:
            return (pressure_bar - 0.01) / 0.09 * 0.5
        elif 5.0 < pressure_bar <= 10.0:
            return 0.5 - (pressure_bar - 5.0) / 5.0 * 0.5
        else:
            return 0.0
    
    def _score_water(self, state: PlanetaryState) -> float:
        """
        Score water availability (liquid + vapor)
        Optimal: 30-70% ocean coverage
        """
        ocean_score = 0
        if 0.3 <= state.ocean_coverage <= 0.7:
            ocean_score = 1.0
        elif 0.1 <= state.ocean_coverage < 0.3:
            ocean_score = (state.ocean_coverage - 0.1) / 0.2 * 0.5 + 0.5
        elif 0.7 < state.ocean_coverage <= 0.9:
            ocean_score = 1.0 - (state.ocean_coverage - 0.7) / 0.2 * 0.3
        elif 0 < state.ocean_coverage < 0.1:
            ocean_score = state.ocean_coverage / 0.1 * 0.5
        
        # Bonus for atmospheric water vapor
        water_vapor_ppm = state.atmospheric_water_vapor / max(state.surface_pressure, 1) * 1e6
        vapor_score = min(1.0, water_vapor_ppm / 10000)  # Optimal ~1%
        
        return ocean_score * 0.8 + vapor_score * 0.2
    
    def _score_oxygen(self, state: PlanetaryState) -> float:
        """
        Score breathable oxygen levels
        Optimal: 15-25%
        Minimum: 10%
        """
        o2_fraction = state.atmosphere.get('O2', 0) / max(state.surface_pressure, 1)
        o2_percent = o2_fraction * 100
        
        if 15 <= o2_percent <= 25:
            return 1.0
        elif 10 <= o2_percent < 15:
            return (o2_percent - 10) / 5 * 0.5 + 0.5
        elif 25 < o2_percent <= 30:
            return 1.0 - (o2_percent - 25) / 5 * 0.3
        elif 5 <= o2_percent < 10:
            return (o2_percent - 5) / 5 * 0.5
        elif 30 < o2_percent <= 40:
            return 0.7 - (o2_percent - 30) / 10 * 0.4
        elif 1 <= o2_percent < 5:
            return o2_percent / 5 * 0.3
        else:
            return 0.0
    
    def _score_uv_protection(self, state: PlanetaryState) -> float:
        """
        Score UV radiation protection
        Requires ozone layer or thick atmosphere
        """
        # Simplified: O2 → O3 conversion
        o2_pressure = state.atmosphere.get('O2', 0)
        
        # Rough estimate: need ~10% of Earth's O2 to form protective ozone
        earth_o2 = 21000  # Pa
        o2_ratio = o2_pressure / earth_o2
        
        ozone_score = min(1.0, o2_ratio * 10)
        
        # Thick atmosphere also provides protection
        pressure_bar = state.surface_pressure / 1e5
        pressure_score = min(1.0, pressure_bar / 2.0)
        
        return max(ozone_score, pressure_score * 0.5)
    
    def _score_magnetic_field(self, state: PlanetaryState) -> float:
        """
        Score magnetic field protection
        """
        if state.has_artificial_magnetosphere:
            return min(1.0, state.magnetic_field_strength)
        elif state.magnetic_field_strength > 0:
            return min(1.0, state.magnetic_field_strength)
        else:
            # Thick atmosphere can partially compensate
            pressure_bar = state.surface_pressure / 1e5
            return min(0.3, pressure_bar / 10)
    
    def _score_atmospheric_stability(self, state: PlanetaryState) -> float:
        """
        Score atmospheric retention capability
        Based on escape velocity and temperature
        """
        from planetary_physics import PlanetaryPhysics
        
        physics = PlanetaryPhysics()
        
        # Check Jeans parameter for major atmospheric constituents
        scores = []
        
        for gas in ['N2', 'O2', 'CO2']:
            if gas not in state.atmosphere:
                continue
            
            molecular_mass = MOLECULAR_WEIGHTS[gas] / 1000
            lambda_j = physics.jeans_escape_parameter(
                state.planet_mass,
                state.planet_radius,
                state.surface_temperature,
                molecular_mass
            )
            
            # λ > 6: good retention
            if lambda_j > 10:
                scores.append(1.0)
            elif lambda_j > 6:
                scores.append(0.8)
            elif lambda_j > 4:
                scores.append(0.5)
            else:
                scores.append(0.2)
        
        if not scores:
            return 0.5
        
        return np.mean(scores)
    
    def _earth_similarity_index(self, state: PlanetaryState) -> float:
        """
        Calculate Earth Similarity Index (ESI)
        Based on Schulze-Makuch et al. 2011
        """
        # Planetary properties
        radius_ratio = state.planet_radius / 1.0
        mass_ratio = state.planet_mass / 1.0
        
        # Surface conditions
        temp_ratio = state.surface_temperature / 288.0
        
        # ESI calculation (geometric mean of component similarities)
        radius_sim = 1 - abs(radius_ratio - 1) / (radius_ratio + 1)
        mass_sim = 1 - abs(mass_ratio - 1) / (mass_ratio + 1)
        temp_sim = 1 - abs(temp_ratio - 1) / (temp_ratio + 1)
        
        esi = (radius_sim * mass_sim * temp_sim ** 2) ** 0.25
        
        return esi * 100  # Convert to percentage
    
    def _classify_habitability(self, total_score: float, component_scores: Dict) -> str:
        """
        Classify planet based on habitability score
        """
        if total_score >= 80:
            return "Earth-like (Highly Habitable)"
        elif total_score >= 60:
            return "Habitable (with moderate adaptation)"
        elif total_score >= 40:
            return "Marginally Habitable (extreme environments only)"
        elif total_score >= 20:
            return "Pre-habitable (terraforming in progress)"
        else:
            return "Uninhabitable"
    
    def get_recommendations(self, state: PlanetaryState, scores: Dict) -> List[str]:
        """
        Generate terraforming recommendations based on scores
        """
        recommendations = []
        
        component_scores = scores['component_scores']
        
        if component_scores['temperature'] < 50:
            temp_c = state.surface_temperature - 273.15
            if temp_c < 0:
                recommendations.append("🌡️ Deploy orbital mirrors to increase temperature")
                recommendations.append("🌡️ Release greenhouse gases (CO2, CH4)")
            else:
                recommendations.append("🌡️ Deploy solar shades to reduce temperature")
                recommendations.append("🌡️ Increase albedo (cloud seeding, ice caps)")
        
        if component_scores['pressure'] < 50:
            pressure_bar = state.surface_pressure / 1e5
            if pressure_bar < 0.5:
                recommendations.append("💨 Increase atmospheric pressure (vaporize ice caps)")
            else:
                recommendations.append("💨 Reduce atmospheric pressure (atmospheric escape)")
        
        if component_scores['water'] < 50:
            if state.ocean_coverage < 0.1:
                recommendations.append("💧 Deliver water (comet impacts, vaporize ice)")
        
        if component_scores['oxygen'] < 50:
            o2_percent = state.atmosphere.get('O2', 0) / max(state.surface_pressure, 1) * 100
            if o2_percent < 10:
                recommendations.append("🌱 Seed photosynthetic organisms")
                recommendations.append("🏭 Build atmospheric processors (CO2 → O2)")
        
        if component_scores['magnetic_field'] < 50:
            if not state.has_artificial_magnetosphere:
                recommendations.append("🧲 Activate magnetic field generator")
        
        return recommendations