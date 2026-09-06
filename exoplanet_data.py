"""
ExoTerra - Exoplanet Data Module
Real exoplanet data from NASA/ESA discoveries
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from constants import *

class ExoplanetDatabase:
    """Database of real exoplanets with measured/estimated parameters"""
    
    def __init__(self):
        self.planets = self._initialize_database()
    
    def _initialize_database(self) -> pd.DataFrame:
        """
        Initialize with curated exoplanet data
        Sources: NASA Exoplanet Archive, scientific literature
        """
        
        exoplanet_data = {
            'name': [
                'TRAPPIST-1e',
                'TRAPPIST-1f', 
                'TRAPPIST-1g',
                'Proxima Centauri b',
                'Gliese 667C c',
                'Kepler-442b',
                'LHS 1140 b',
                'TOI-700 d',
                'K2-18 b',
            ],
            
            # Planetary Properties
            'mass': [  # Earth masses
                0.692,
                0.934,
                1.148,
                1.27,
                3.8,
                2.34,
                6.65,
                1.72,
                8.63,
            ],
            
            'radius': [  # Earth radii
                0.920,
                1.045,
                1.129,
                1.07,
                1.54,
                1.34,
                1.43,
                1.19,
                2.61,
            ],
            
            'semi_major_axis': [  # AU
                0.02928,
                0.03849,
                0.04683,
                0.04857,
                0.1251,
                0.409,
                0.0875,
                0.1633,
                0.1429,
            ],
            
            'orbital_period': [  # Earth days
                6.10,
                9.21,
                12.35,
                11.19,
                28.14,
                112.3,
                24.74,
                37.42,
                32.94,
            ],
            
            # Stellar Properties
            'star_mass': [  # Solar masses
                0.089,
                0.089,
                0.089,
                0.122,
                0.31,
                0.61,
                0.146,
                0.415,
                0.45,
            ],
            
            'star_radius': [  # Solar radii
                0.117,
                0.117,
                0.117,
                0.154,
                0.42,
                0.60,
                0.186,
                0.422,
                0.45,
            ],
            
            'star_temperature': [  # Kelvin
                2566,
                2566,
                2566,
                3042,
                3700,
                4402,
                3131,
                3480,
                3457,
            ],
            
            'star_luminosity': [  # Solar luminosities
                0.000525,
                0.000525,
                0.000525,
                0.00165,
                0.0137,
                0.212,
                0.00298,
                0.0233,
                0.0190,
            ],
            
            # Initial Atmospheric Estimates (highly speculative for most)
            'initial_pressure': [  # Earth atmospheres (1 atm = 101325 Pa)
                1.0,
                1.0,
                1.0,
                0.5,
                2.0,
                1.5,
                1.0,
                1.2,
                10.0,  # Known to have atmosphere
            ],
            
            'initial_albedo': [  # Bond albedo
                0.3,
                0.3,
                0.3,
                0.3,
                0.3,
                0.3,
                0.3,
                0.3,
                0.2,
            ],
            
            # Discovery information
            'discovery_year': [
                2017, 2017, 2017, 2016, 2011, 2015, 2017, 2020, 2015
            ],
            
            'discovery_method': [
                'Transit', 'Transit', 'Transit', 'RV', 'RV', 
                'Transit', 'Transit', 'Transit', 'Transit'
            ],
        }
        
        df = pd.DataFrame(exoplanet_data)
        
        # Calculate derived properties
        df['gravity'] = self._calculate_surface_gravity(
            df['mass'].values, 
            df['radius'].values
        )
        
        df['escape_velocity'] = self._calculate_escape_velocity(
            df['mass'].values,
            df['radius'].values
        )
        
        df['density'] = self._calculate_density(
            df['mass'].values,
            df['radius'].values
        )
        
        return df
    
    def _calculate_surface_gravity(self, mass_earth: np.ndarray, 
                                   radius_earth: np.ndarray) -> np.ndarray:
        """Calculate surface gravity in m/s^2"""
        mass_kg = mass_earth * EARTH_MASS
        radius_m = radius_earth * EARTH_RADIUS
        return GRAVITATIONAL_CONSTANT * mass_kg / (radius_m ** 2)
    
    def _calculate_escape_velocity(self, mass_earth: np.ndarray,
                                   radius_earth: np.ndarray) -> np.ndarray:
        """Calculate escape velocity in km/s"""
        mass_kg = mass_earth * EARTH_MASS
        radius_m = radius_earth * EARTH_RADIUS
        v_esc = np.sqrt(2 * GRAVITATIONAL_CONSTANT * mass_kg / radius_m)
        return v_esc / 1000  # Convert to km/s
    
    def _calculate_density(self, mass_earth: np.ndarray,
                          radius_earth: np.ndarray) -> np.ndarray:
        """Calculate bulk density in g/cm^3"""
        mass_kg = mass_earth * EARTH_MASS
        radius_m = radius_earth * EARTH_RADIUS
        volume_m3 = (4/3) * np.pi * radius_m ** 3
        density_kg_m3 = mass_kg / volume_m3
        return density_kg_m3 / 1000  # Convert to g/cm^3
    
    def get_planet(self, name: str) -> Optional[pd.Series]:
        """Retrieve a specific planet's data"""
        planet = self.planets[self.planets['name'] == name]
        if len(planet) == 0:
            return None
        return planet.iloc[0]
    
    def get_all_planets(self) -> pd.DataFrame:
        """Get all planets in database"""
        return self.planets.copy()
    
    def add_custom_planet(self, planet_data: Dict) -> None:
        """Add a custom planet to the database"""
        required_fields = ['name', 'mass', 'radius', 'semi_major_axis',
                          'star_mass', 'star_luminosity', 'star_temperature']
        
        if not all(field in planet_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")
        
        # Calculate derived properties
        planet_data['gravity'] = self._calculate_surface_gravity(
            np.array([planet_data['mass']]),
            np.array([planet_data['radius']])
        )[0]
        
        planet_data['escape_velocity'] = self._calculate_escape_velocity(
            np.array([planet_data['mass']]),
            np.array([planet_data['radius']])
        )[0]
        
        planet_data['density'] = self._calculate_density(
            np.array([planet_data['mass']]),
            np.array([planet_data['radius']])
        )[0]
        
        self.planets = pd.concat([
            self.planets,
            pd.DataFrame([planet_data])
        ], ignore_index=True)
    
    def summary_statistics(self) -> pd.DataFrame:
        """Get summary statistics of the database"""
        numeric_cols = self.planets.select_dtypes(include=[np.number]).columns
        return self.planets[numeric_cols].describe()