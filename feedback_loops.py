"""
ExoTerra - Climate Feedback Loops Module
Implements planetary feedback mechanisms
"""

import numpy as np
from planetary_state import PlanetaryState
from constants import *
from atmosphere_model import AtmosphereModel
from planetary_physics import PlanetaryPhysics

class FeedbackProcessor:
    """Processes climate feedback loops"""
    
    def __init__(self):
        self.physics = PlanetaryPhysics()
    
    def process_all_feedbacks(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Apply all feedback mechanisms for one timestep
        
        Parameters:
        -----------
        state : PlanetaryState
            Current state
        dt_years : float
            Timestep in years
            
        Returns:
        --------
        PlanetaryState : Updated state
        """
        new_state = state.copy()
        
        # Order matters - some feedbacks depend on others
        new_state = self.ice_albedo_feedback(new_state)
        new_state = self.co2_ice_sublimation(new_state, dt_years)
        new_state = self.water_phase_transitions(new_state, dt_years)
        new_state = self.photosynthesis(new_state, dt_years)
        new_state = self.atmospheric_escape(new_state, dt_years)
        new_state = self.carbonate_silicate_cycle(new_state, dt_years)
        new_state = self.update_temperature(new_state)
        new_state = self.biomass_growth(new_state, dt_years)
        new_state = self.atmospheric_processor_operation(new_state, dt_years)
        
        return new_state
    
    def ice_albedo_feedback(self, state: PlanetaryState) -> PlanetaryState:
        """
        Ice coverage affects planetary albedo
        More ice → higher albedo → more cooling (positive feedback)
        """
        new_state = state.copy()
        
        # Base albedo (ice-free)
        base_albedo = 0.15  # Dark rock/ocean
        ice_albedo = 0.7    # Bright ice
        ocean_albedo = 0.06  # Dark water
        cloud_albedo = 0.4   # Clouds
        
        # Weighted average
        ice_contribution = new_state.ice_coverage * ice_albedo
        ocean_contribution = new_state.ocean_coverage * ocean_albedo
        land_contribution = (1 - new_state.ice_coverage - new_state.ocean_coverage) * base_albedo
        
        # Cloud coverage depends on water vapor
        water_vapor_fraction = new_state.atmospheric_water_vapor / max(new_state.surface_pressure, 1)
        cloud_coverage = min(0.6, water_vapor_fraction * 2)  # Saturates at 60%
        
        new_state.albedo = (ice_contribution + ocean_contribution + land_contribution) * (1 - cloud_coverage) + \
                           cloud_coverage * cloud_albedo
        
        # Clamp to physical range
        new_state.albedo = np.clip(new_state.albedo, 0.05, 0.95)
        
        return new_state
    
    def co2_ice_sublimation(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        CO2 sublimes from ice caps when temperature exceeds ~148 K at Mars pressure
        Sublimation temperature depends on pressure (Clausius-Clapeyron)
        """
        new_state = state.copy()
        
        # CO2 sublimation curve (simplified)
        # At 1 bar, CO2 sublimes at 194.7 K
        # At 0.006 bar (Mars), sublimes at ~148 K
        
        pressure_bar = new_state.surface_pressure / 1e5
        sublimation_temp = 194.7 * (pressure_bar / 1.0) ** 0.08  # Rough approximation
        
        if new_state.surface_temperature > sublimation_temp and new_state.co2_ice_mass > 0:
            # Sublimation rate depends on temperature excess
            temp_excess = new_state.surface_temperature - sublimation_temp
            
            # Rate increases exponentially with temperature
            sublimation_fraction = min(1.0, 0.01 * temp_excess * dt_years / 10)
            
            mass_sublimed = new_state.co2_ice_mass * sublimation_fraction
            new_state.co2_ice_mass -= mass_sublimed
            
            # Add to atmosphere
            radius_m = state.planet_radius * EARTH_RADIUS
            surface_area = 4 * np.pi * radius_m ** 2
            mass_kg = state.planet_mass * EARTH_MASS
            gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
            
            pressure_increase = (mass_sublimed * gravity) / surface_area
            new_state.atmosphere['CO2'] = new_state.atmosphere.get('CO2', 0) + pressure_increase
        
        elif new_state.surface_temperature < sublimation_temp - 10:
            # Condensation - some atmospheric CO2 freezes
            condensation_rate = 0.005 * dt_years / 10  # Slow process
            
            current_co2 = new_state.atmosphere.get('CO2', 0)
            condensed_pressure = current_co2 * condensation_rate
            
            if condensed_pressure > 0:
                new_state.atmosphere['CO2'] = current_co2 - condensed_pressure
                
                # Convert pressure to mass
                radius_m = state.planet_radius * EARTH_RADIUS
                surface_area = 4 * np.pi * radius_m ** 2
                mass_kg = state.planet_mass * EARTH_MASS
                gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
                
                mass_condensed = condensed_pressure * surface_area / gravity
                new_state.co2_ice_mass += mass_condensed
        
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def water_phase_transitions(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Handle water ice ↔ liquid ↔ vapor transitions
        """
        new_state = state.copy()
        
        temp = new_state.surface_temperature
        pressure_bar = new_state.surface_pressure / 1e5
        
        # Water phase diagram (simplified)
        # Triple point: 273.16 K, 0.006 bar
        # Critical point: 647 K, 221 bar
        
        radius_m = state.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        
        # ICE → LIQUID (melting)
        if temp > 273 and new_state.water_ice_mass > 0 and pressure_bar > 0.006:
            melt_fraction = min(1.0, 0.1 * (temp - 273) / 10 * dt_years / 10)
            mass_melted = new_state.water_ice_mass * melt_fraction
            
            new_state.water_ice_mass -= mass_melted
            
            # Add to oceans
            ocean_depth = 3000
            water_density = 1000
            ocean_area_increase = mass_melted / (ocean_depth * water_density)
            new_state.ocean_coverage = min(1.0, new_state.ocean_coverage + ocean_area_increase / surface_area)
            
            # Update ice coverage
            if new_state.water_ice_mass > 0:
                ice_density = 917  # kg/m^3
                ice_thickness = 1000  # m average
                ice_area = new_state.water_ice_mass / (ice_thickness * ice_density)
                new_state.ice_coverage = min(1.0, ice_area / surface_area)
            else:
                new_state.ice_coverage = 0
        
        # LIQUID → ICE (freezing)
        elif temp < 273 and new_state.ocean_coverage > 0:
            freeze_fraction = min(1.0, 0.05 * (273 - temp) / 10 * dt_years / 10)
            
            ocean_depth = 3000
            water_density = 1000
            ocean_mass = new_state.ocean_coverage * surface_area * ocean_depth * water_density
            
            mass_frozen = ocean_mass * freeze_fraction
            
            new_state.water_ice_mass += mass_frozen
            
            # Reduce ocean
            ocean_area_decrease = mass_frozen / (ocean_depth * water_density)
            new_state.ocean_coverage = max(0, new_state.ocean_coverage - ocean_area_decrease / surface_area)
            
            # Update ice coverage
            ice_density = 917
            ice_thickness = 1000
            ice_area = new_state.water_ice_mass / (ice_thickness * ice_density)
            new_state.ice_coverage = min(1.0, ice_area / surface_area)
        
        # LIQUID ↔ VAPOR equilibrium
        if new_state.ocean_coverage > 0:
            # Saturation vapor pressure (Clausius-Clapeyron, simplified)
            # P_sat = P_0 * exp(-L/(R*T))
            # For water: P_sat(273K) ≈ 611 Pa
            
            p_sat = 611 * np.exp(-(2.5e6 / 461) * (1/temp - 1/273))  # Pa
            
            current_vapor = new_state.atmospheric_water_vapor
            
            # Evaporation/condensation rate
            if current_vapor < p_sat:
                # Evaporate
                evap_rate = 0.1 * (p_sat - current_vapor) * dt_years / 10
                new_state.atmospheric_water_vapor = min(p_sat, current_vapor + evap_rate)
            else:
                # Condense (rain)
                condense_rate = 0.2 * (current_vapor - p_sat) * dt_years / 10
                new_state.atmospheric_water_vapor = max(p_sat, current_vapor - condense_rate)
        
        new_state.atmosphere['H2O'] = new_state.atmospheric_water_vapor
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def photosynthesis(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Biological O2 production: 6 CO2 + 6 H2O → C6H12O6 + 6 O2
        """
        new_state = state.copy()
        
        if new_state.biomass == 0:
            return new_state
        
        # O2 production (kg/year)
        o2_produced_kg = new_state.o2_production_rate * dt_years
        
        # Consume CO2 (stoichiometry: 44 g CO2 → 32 g O2)
        co2_consumed_kg = o2_produced_kg * (44.0 / 32.0)
        
        # Convert to pressure changes
        radius_m = state.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        mass_kg = state.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        
        o2_pressure_increase = (o2_produced_kg * gravity) / surface_area
        co2_pressure_decrease = (co2_consumed_kg * gravity) / surface_area
        
        # Update atmosphere
        new_state.atmosphere['O2'] = new_state.atmosphere.get('O2', 0) + o2_pressure_increase
        new_state.atmosphere['CO2'] = max(0, new_state.atmosphere.get('CO2', 0) - co2_pressure_decrease)
        
        # If CO2 becomes limiting, reduce production
        if new_state.atmosphere['CO2'] < 100:  # < 100 Pa
            new_state.o2_production_rate *= 0.5  # Die-off
        
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def atmospheric_escape(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Atmospheric loss via Jeans escape and stellar wind stripping
        Reduced by magnetic field
        """
        new_state = state.copy()
        
        # Magnetic field protection factor
        if new_state.has_artificial_magnetosphere:
            protection_factor = 0.01  # 99% protection
        elif new_state.magnetic_field_strength > 0.1:
            protection_factor = 0.1 / new_state.magnetic_field_strength
        else:
            protection_factor = 1.0  # No protection
        
        # Calculate escape for light gases
        total_loss_kg = 0
        
        for gas in ['H2', 'He', 'H2O']:
            if gas not in new_state.atmosphere:
                continue
            
            molecular_mass = MOLECULAR_WEIGHTS[gas] / 1000  # kg/mol
            
            escape_rate = self.physics.jeans_escape_rate(
                state.planet_mass,
                state.planet_radius,
                new_state.surface_temperature,
                molecular_mass,
                new_state.atmosphere[gas]
            )
            
            # Apply magnetic protection and time
            escape_rate *= protection_factor
            mass_lost = escape_rate * dt_years * 365.25 * 24 * 3600  # Convert years to seconds
            
            total_loss_kg += mass_lost
            
            # Remove from atmosphere
            radius_m = state.planet_radius * EARTH_RADIUS
            surface_area = 4 * np.pi * radius_m ** 2
            mass_kg = state.planet_mass * EARTH_MASS
            gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
            
            pressure_lost = (mass_lost * gravity) / surface_area
            new_state.atmosphere[gas] = max(0, new_state.atmosphere[gas] - pressure_lost)
        
        new_state.cumulative_atmosphere_lost += total_loss_kg
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def carbonate_silicate_cycle(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Long-term geological CO2 regulation
        CO2 + CaSiO3 → CaCO3 + SiO2 (weathering, removes CO2)
        CaCO3 → CO2 + CaO (volcanism, adds CO2)
        """
        new_state = state.copy()
        
        # Only operates with liquid water
        if new_state.ocean_coverage < 0.01:
            return new_state
        
        # Weathering rate increases with temperature and CO2
        temp_factor = max(0, (new_state.surface_temperature - 273) / 20)
        co2_ppm = new_state.atmosphere.get('CO2', 0) / new_state.surface_pressure * 1e6
        co2_factor = co2_ppm / 280  # Normalized to Earth pre-industrial
        
        weathering_rate = temp_factor * co2_factor * 1e12  # kg CO2/year
        
        # Volcanic outgassing (roughly constant)
        volcanic_rate = 5e11  # kg CO2/year (Earth-like)
        
        net_co2_change_kg = (volcanic_rate - weathering_rate) * dt_years
        
        # Convert to pressure
        radius_m = state.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        mass_kg = state.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        
        pressure_change = (net_co2_change_kg * gravity) / surface_area
        new_state.atmosphere['CO2'] = max(0, new_state.atmosphere.get('CO2', 0) + pressure_change)
        
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def update_temperature(self, state: PlanetaryState) -> PlanetaryState:
        """Recalculate surface temperature based on current conditions"""
        new_state = state.copy()
        
        # Create atmosphere model
        atmosphere = AtmosphereModel(new_state.atmosphere, new_state.surface_pressure)
        
        # Calculate equilibrium temperature
        emissivity = atmosphere.emissivity()
        t_eq = self.physics.equilibrium_temperature(
            new_state.stellar_flux,
            new_state.albedo,
            emissivity
        )
        
        new_state.equilibrium_temperature = t_eq
        
        # Add greenhouse effect
        greenhouse = atmosphere.greenhouse_effect(t_eq)
        new_state.greenhouse_effect = greenhouse
        new_state.surface_temperature = t_eq + greenhouse
        
        return new_state
    
    def biomass_growth(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Biomass growth/decay based on conditions
        """
        new_state = state.copy()
        
        if new_state.biomass == 0:
            return new_state
        
        # Growth factors
        temp_c = new_state.surface_temperature - 273.15
        
        # Temperature factor (optimal 15-30°C)
        if 15 <= temp_c <= 30:
            temp_factor = 1.0
        elif 0 <= temp_c < 15 or 30 < temp_c <= 45:
            temp_factor = 0.5
        elif -10 <= temp_c < 0 or 45 < temp_c <= 60:
            temp_factor = 0.1
        else:
            temp_factor = -0.5  # Die-off
        
        # CO2 availability
        co2_ppm = new_state.atmosphere.get('CO2', 0) / new_state.surface_pressure * 1e6
        co2_factor = min(1.0, co2_ppm / 400)
        
        # Water availability
        water_factor = min(1.0, new_state.ocean_coverage / 0.1)
        
        # Net growth rate
        growth_rate = 0.05 * temp_factor * co2_factor * water_factor  # 5% per year optimal
        
        new_state.biomass *= (1 + growth_rate * dt_years)
        new_state.o2_production_rate = new_state.biomass * 1.0  # 1 kg O2 per kg biomass per year
        
        # Decay if conditions too harsh
        if new_state.biomass < 1e3:
            new_state.biomass = 0
            new_state.o2_production_rate = 0
        
        return new_state
    
    def atmospheric_processor_operation(self, state: PlanetaryState, dt_years: float) -> PlanetaryState:
        """
        Industrial CO2 → O2 conversion
        """
        new_state = state.copy()
        
        if new_state.atmospheric_processors == 0:
            return new_state
        
        # Processing capacity
        capacity_per_processor = 1e12  # kg CO2/year
        total_capacity = new_state.atmospheric_processors * capacity_per_processor * dt_years
        
        # Limited by available CO2
        radius_m = state.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        mass_kg = state.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        
        current_co2_pressure = new_state.atmosphere.get('CO2', 0)
        current_co2_mass = current_co2_pressure * surface_area / gravity
        
        co2_processed = min(total_capacity, current_co2_mass)
        
        # Convert CO2 → O2 (44 g CO2 → 32 g O2)
        o2_produced = co2_processed * (32.0 / 44.0)
        
        # Update atmosphere
        co2_pressure_decrease = (co2_processed * gravity) / surface_area
        o2_pressure_increase = (o2_produced * gravity) / surface_area
        
        new_state.atmosphere['CO2'] = max(0, current_co2_pressure - co2_pressure_decrease)
        new_state.atmosphere['O2'] = new_state.atmosphere.get('O2', 0) + o2_pressure_increase
        
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state