"""
ExoTerra - Planetary State Module
Tracks complete state of planet over time
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from copy import deepcopy
from constants import *
from atmosphere_model import AtmosphereModel

@dataclass
class PlanetaryState:
    """
    Complete snapshot of planetary state at a given time
    """
    
    # Time
    time_years: float = 0.0
    
    # Orbital/Stellar (fixed)
    planet_mass: float = 1.0  # Earth masses
    planet_radius: float = 1.0  # Earth radii
    semi_major_axis: float = 1.0  # AU
    star_luminosity: float = 1.0  # Solar luminosities
    star_mass: float = 1.0  # Solar masses
    
    # Atmospheric composition (Pa partial pressures)
    atmosphere: Dict[str, float] = field(default_factory=lambda: {
        'N2': 79000.0,
        'O2': 21000.0,
        'CO2': 40.0,
        'H2O': 1000.0,
    })
    
    # Surface properties
    surface_temperature: float = 288.0  # K
    surface_pressure: float = 101325.0  # Pa
    albedo: float = 0.3
    
    # Water inventory
    ocean_coverage: float = 0.0  # Fraction of surface (0-1)
    ice_coverage: float = 0.0  # Fraction of surface (0-1)
    subsurface_ice_mass: float = 0.0  # kg
    atmospheric_water_vapor: float = 1000.0  # Pa partial pressure
    
    # Ice reservoirs (volatile storage)
    co2_ice_mass: float = 0.0  # kg (polar caps, subsurface)
    water_ice_mass: float = 0.0  # kg (polar caps, glaciers)
    
    # Magnetic field
    magnetic_field_strength: float = 0.0  # Earth = 1.0 (relative)
    has_artificial_magnetosphere: bool = False
    
    # Biological activity
    biomass: float = 0.0  # kg (primarily microbes/plants)
    o2_production_rate: float = 0.0  # kg O2/year
    
    # Technological infrastructure
    orbital_mirrors: int = 0  # Number of mirrors
    atmospheric_processors: int = 0  # CO2 -> O2 converters
    
    # Energy budget components
    stellar_flux: float = 1361.0  # W/m^2
    greenhouse_effect: float = 33.0  # K
    equilibrium_temperature: float = 255.0  # K
    
    # Atmospheric loss tracking
    cumulative_atmosphere_lost: float = 0.0  # kg
    
    def copy(self) -> 'PlanetaryState':
        """Create deep copy of state"""
        return deepcopy(self)
    
    def total_atmosphere_mass(self) -> float:
        """Calculate total atmospheric mass in kg"""
        radius_m = self.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        mass_kg = self.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        
        # Mass = Pressure * Area / g
        return self.surface_pressure * surface_area / gravity
    
    def total_water_mass(self) -> float:
        """Total water mass (all phases) in kg"""
        radius_m = self.planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        
        # Ocean mass (assume 3 km average depth like Earth)
        ocean_depth = 3000  # meters
        water_density = 1000  # kg/m^3
        ocean_mass = self.ocean_coverage * surface_area * ocean_depth * water_density
        
        # Ice mass
        ice_mass = self.water_ice_mass + self.subsurface_ice_mass
        
        # Atmospheric water vapor
        mass_kg = self.planet_mass * EARTH_MASS
        gravity = GRAVITATIONAL_CONSTANT * mass_kg / radius_m ** 2
        vapor_mass = self.atmospheric_water_vapor * surface_area / gravity
        
        return ocean_mass + ice_mass + vapor_mass
    
    def atmospheric_composition_fractions(self) -> Dict[str, float]:
        """Get molar fractions of atmospheric gases"""
        total_pressure = sum(self.atmosphere.values())
        if total_pressure == 0:
            return {}
        return {gas: p / total_pressure for gas, p in self.atmosphere.items()}
    
    def get_summary(self) -> Dict:
        """Get human-readable summary"""
        return {
            'Time (years)': self.time_years,
            'Temperature (°C)': self.surface_temperature - 273.15,
            'Pressure (bar)': self.surface_pressure / 1e5,
            'Ocean coverage (%)': self.ocean_coverage * 100,
            'Ice coverage (%)': self.ice_coverage * 100,
            'O2 level (%)': self.atmosphere.get('O2', 0) / self.surface_pressure * 100,
            'CO2 (ppm)': self.atmosphere.get('CO2', 0) / self.surface_pressure * 1e6,
            'Biomass (kg)': self.biomass,
        }


class StateHistory:
    """Tracks planetary state evolution over time"""
    
    def __init__(self):
        self.states: List[PlanetaryState] = []
        self.events: List[Dict] = []  # Log of interventions and major events
    
    def add_state(self, state: PlanetaryState):
        """Add a state snapshot"""
        self.states.append(state.copy())
    
    def add_event(self, time: float, event_type: str, description: str, 
                  parameters: Dict = None):
        """Log an event"""
        self.events.append({
            'time': time,
            'type': event_type,
            'description': description,
            'parameters': parameters or {}
        })
    
    def get_timeseries(self, attribute: str) -> tuple:
        """Extract timeseries of a specific attribute"""
        times = [s.time_years for s in self.states]
        
        # Handle nested attributes
        values = []
        for state in self.states:
            if '.' in attribute:
                parts = attribute.split('.')
                value = getattr(state, parts[0])
                for part in parts[1:]:
                    value = getattr(value, part) if hasattr(value, part) else value.get(part, 0)
            else:
                value = getattr(state, attribute, 0)
            values.append(value)
        
        return np.array(times), np.array(values)
    
    def get_current_state(self) -> Optional[PlanetaryState]:
        """Get most recent state"""
        return self.states[-1].copy() if self.states else None
    
    def get_initial_state(self) -> Optional[PlanetaryState]:
        """Get initial state"""
        return self.states[0].copy() if self.states else None