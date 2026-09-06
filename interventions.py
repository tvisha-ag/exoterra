"""
ExoTerra - Terraforming Interventions Module
User-initiated actions to modify planetary conditions
"""

import numpy as np
from typing import Dict, Callable
from planetary_state import PlanetaryState
from constants import *

class TerraformingIntervention:
    """Base class for terraforming actions"""
    
    def __init__(self, name: str, cost: float, duration: float = 0):
        """
        Parameters:
        -----------
        name : str
            Intervention name
        cost : float
            Energy/resource cost (arbitrary units)
        duration : float
            Time to complete (years)
        """
        self.name = name
        self.cost = cost
        self.duration = duration
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        """Apply intervention to state"""
        raise NotImplementedError
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        """Check if intervention can be applied"""
        return True, "OK"


class DeployOrbitalMirrors(TerraformingIntervention):
    """Deploy mirrors to increase/decrease stellar flux"""
    
    def __init__(self, num_mirrors: int, configuration: str = 'heating'):
        """
        Parameters:
        -----------
        num_mirrors : int
            Number of mirrors to deploy
        configuration : str
            'heating' (focus light) or 'shading' (block light)
        """
        super().__init__(
            name=f"Deploy {num_mirrors} Orbital Mirrors ({configuration})",
            cost=num_mirrors * 1000,
            duration=10
        )
        self.num_mirrors = num_mirrors
        self.configuration = configuration
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        new_state.orbital_mirrors += self.num_mirrors
        
        # Each mirror modifies effective stellar flux by ~1%
        if self.configuration == 'heating':
            flux_change = 1.0 + (0.01 * self.num_mirrors)
        else:  # shading
            flux_change = 1.0 - (0.01 * self.num_mirrors)
        
        new_state.stellar_flux *= flux_change
        
        return new_state
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        if self.configuration == 'shading' and state.orbital_mirrors < self.num_mirrors:
            return False, "Not enough mirrors to remove"
        return True, "OK"


class ReleaseGreenhouseGas(TerraformingIntervention):
    """Release greenhouse gases into atmosphere"""
    
    def __init__(self, gas_type: str, amount_kg: float):
        """
        Parameters:
        -----------
        gas_type : str
            Gas to release (CO2, CH4, etc.)
        amount_kg : float
            Mass of gas in kg
        """
        super().__init__(
            name=f"Release {amount_kg:.2e} kg of {gas_type}",
            cost=amount_kg / 1e9,  # Cost scales with amount
            duration=1
        )
        self.gas_type = gas_type
        self.amount_kg = amount_kg
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        
        # Convert mass to partial pressure
        # P = (m * g) / (A * MMW) * R * T
        radius_m = state.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        mass_kg = state.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        
        # Simplified: pressure increase from added mass
        pressure_increase = (self.amount_kg * gravity) / surface_area
        
        current = new_state.atmosphere.get(self.gas_type, 0)
        new_state.atmosphere[self.gas_type] = current + pressure_increase
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        if self.gas_type not in MOLECULAR_WEIGHTS:
            return False, f"Unknown gas type: {self.gas_type}"
        return True, "OK"


class VaporizeIceCap(TerraformingIntervention):
    """Sublimate polar ice caps to release volatiles"""
    
    def __init__(self, target: str = 'CO2', fraction: float = 0.1):
        """
        Parameters:
        -----------
        target : str
            'CO2' or 'H2O'
        fraction : float
            Fraction of ice to vaporize (0-1)
        """
        super().__init__(
            name=f"Vaporize {fraction*100}% of {target} ice",
            cost=fraction * 5000,
            duration=5
        )
        self.target = target
        self.fraction = fraction
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        
        if self.target == 'CO2':
            mass_to_release = new_state.co2_ice_mass * self.fraction
            new_state.co2_ice_mass -= mass_to_release
            
            # Convert to atmospheric pressure
            radius_m = state.planet_radius * EARTH_RADIUS
            surface_area = 4 * np.pi * radius_m ** 2
            mass_kg = state.planet_mass * EARTH_MASS
            gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
            
            pressure_increase = (mass_to_release * gravity) / surface_area
            new_state.atmosphere['CO2'] = new_state.atmosphere.get('CO2', 0) + pressure_increase
            
        elif self.target == 'H2O':
            mass_to_release = new_state.water_ice_mass * self.fraction
            new_state.water_ice_mass -= mass_to_release
            
            # Some becomes vapor, some becomes ocean
            vapor_fraction = 0.3 if new_state.surface_temperature > 273 else 0.9
            
            # Add to atmosphere
            radius_m = state.planet_radius * EARTH_RADIUS
            surface_area = 4 * np.pi * radius_m ** 2
            mass_kg = state.planet_mass * EARTH_MASS
            gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
            
            vapor_mass = mass_to_release * vapor_fraction
            pressure_increase = (vapor_mass * gravity) / surface_area
            new_state.atmospheric_water_vapor += pressure_increase
            new_state.atmosphere['H2O'] = new_state.atmospheric_water_vapor
            
            # Add to ocean
            ocean_mass = mass_to_release * (1 - vapor_fraction)
            ocean_depth = 3000  # m
            water_density = 1000  # kg/m^3
            ocean_area = ocean_mass / (ocean_depth * water_density)
            new_state.ocean_coverage = min(1.0, new_state.ocean_coverage + ocean_area / surface_area)
        
        new_state.surface_pressure = sum(new_state.atmosphere.values())
        
        return new_state
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        if self.target == 'CO2' and state.co2_ice_mass < 1e10:
            return False, "Insufficient CO2 ice"
        if self.target == 'H2O' and state.water_ice_mass < 1e10:
            return False, "Insufficient water ice"
        return True, "OK"


class SeedMicroorganisms(TerraformingIntervention):
    """Introduce photosynthetic organisms"""
    
    def __init__(self, organism_type: str = 'cyanobacteria', seed_mass: float = 1e6):
        """
        Parameters:
        -----------
        organism_type : str
            Type of organism
        seed_mass : float
            Initial biomass in kg
        """
        super().__init__(
            name=f"Seed {organism_type} ({seed_mass:.2e} kg)",
            cost=seed_mass / 1000,
            duration=0.5
        )
        self.organism_type = organism_type
        self.seed_mass = seed_mass
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        new_state.biomass += self.seed_mass
        
        # Set baseline O2 production
        # Cyanobacteria: ~1 kg O2 per kg biomass per year (rough estimate)
        if self.organism_type == 'cyanobacteria':
            new_state.o2_production_rate = self.seed_mass * 1.0
        elif self.organism_type == 'algae':
            new_state.o2_production_rate = self.seed_mass * 1.5
        elif self.organism_type == 'plants':
            new_state.o2_production_rate = self.seed_mass * 0.5
        
        return new_state
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        # Need liquid water
        if state.ocean_coverage < 0.01:
            return False, "Requires liquid water (ocean coverage < 1%)"
        
        # Need tolerable temperature
        temp_c = state.surface_temperature - 273.15
        if temp_c < -20 or temp_c > 80:
            return False, f"Temperature ({temp_c:.1f}°C) outside viable range"
        
        # Need some CO2 for photosynthesis
        co2_ppm = state.atmosphere.get('CO2', 0) / state.surface_pressure * 1e6
        if co2_ppm < 100:
            return False, "Insufficient CO2 for photosynthesis"
        
        return True, "OK"


class ActivateMagneticFieldGenerator(TerraformingIntervention):
    """Deploy artificial magnetosphere"""
    
    def __init__(self, field_strength: float = 1.0):
        """
        Parameters:
        -----------
        field_strength : float
            Relative to Earth's field (1.0 = Earth-like)
        """
        super().__init__(
            name=f"Activate Magnetic Field Generator ({field_strength}x Earth)",
            cost=field_strength * 10000,
            duration=20
        )
        self.field_strength = field_strength
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        new_state.has_artificial_magnetosphere = True
        new_state.magnetic_field_strength = self.field_strength
        return new_state
    
    def is_applicable(self, state: PlanetaryState) -> tuple[bool, str]:
        if state.has_artificial_magnetosphere:
            return False, "Magnetic field already active"
        return True, "OK"


class BuildAtmosphericProcessor(TerraformingIntervention):
    """Build CO2 → O2 conversion facilities"""
    
    def __init__(self, num_processors: int = 1, capacity_kg_per_year: float = 1e12):
        """
        Parameters:
        -----------
        num_processors : int
            Number of facilities
        capacity_kg_per_year : float
            CO2 processing capacity per processor
        """
        super().__init__(
            name=f"Build {num_processors} Atmospheric Processors",
            cost=num_processors * 2000,
            duration=15
        )
        self.num_processors = num_processors
        self.capacity = capacity_kg_per_year
    
    def apply(self, state: PlanetaryState) -> PlanetaryState:
        new_state = state.copy()
        new_state.atmospheric_processors += self.num_processors
        return new_state


class InterventionLibrary:
    """Collection of all available interventions"""
    
    @staticmethod
    def get_all_interventions() -> Dict[str, type]:
        """Get dictionary of all intervention classes"""
        return {
            'orbital_mirrors_heat': lambda: DeployOrbitalMirrors(5, 'heating'),
            'orbital_mirrors_shade': lambda: DeployOrbitalMirrors(5, 'shading'),
            'release_co2_small': lambda: ReleaseGreenhouseGas('CO2', 1e15),
            'release_co2_large': lambda: ReleaseGreenhouseGas('CO2', 1e16),
            'release_ch4': lambda: ReleaseGreenhouseGas('CH4', 1e14),
            'vaporize_co2_ice': lambda: VaporizeIceCap('CO2', 0.1),
            'vaporize_water_ice': lambda: VaporizeIceCap('H2O', 0.1),
            'seed_cyanobacteria': lambda: SeedMicroorganisms('cyanobacteria', 1e9),
            'seed_algae': lambda: SeedMicroorganisms('algae', 1e9),
            'activate_magnetic_field': lambda: ActivateMagneticFieldGenerator(1.0),
            'build_processors': lambda: BuildAtmosphericProcessor(10, 1e12),
        }
    
    @staticmethod
    def describe_all():
        """Print descriptions of all interventions"""
        library = InterventionLibrary.get_all_interventions()
        for key, intervention_factory in library.items():
            intervention = intervention_factory()
            print(f"{key:30s}: {intervention.name} (Cost: {intervention.cost:.0f}, Duration: {intervention.duration} yr)")