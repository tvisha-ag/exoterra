"""
ExoTerra - Planetary Physics Engine
Core thermodynamic and planetary science calculations
"""

import numpy as np
from typing import Tuple, Optional
from constants import *
from atmosphere_model import AtmosphereModel

class PlanetaryPhysics:
    """
    Core physics engine for planetary climate modeling
    """
    
    @staticmethod
    def stellar_flux(star_luminosity: float, semi_major_axis: float) -> float:
        """
        Calculate stellar flux received at planet's orbital distance
        
        F = L_star / (4π a²)
        
        Parameters:
        -----------
        star_luminosity : float
            Stellar luminosity in solar luminosities
        semi_major_axis : float
            Orbital semi-major axis in AU
            
        Returns:
        --------
        float : Stellar flux in W/m^2
        """
        luminosity_watts = star_luminosity * SOLAR_LUMINOSITY
        distance_m = semi_major_axis * AU
        
        flux = luminosity_watts / (4 * np.pi * distance_m ** 2)
        return flux
    
    @staticmethod
    def equilibrium_temperature(stellar_flux: float, albedo: float,
                               emissivity: float = 1.0) -> float:
        """
        Calculate planetary equilibrium temperature
        
        T_eq = [(F(1-A)) / (4σε)]^0.25
        
        Parameters:
        -----------
        stellar_flux : float
            Incident stellar flux in W/m^2
        albedo : float
            Bond albedo (0-1)
        emissivity : float
            Infrared emissivity (0-1), default 1.0
            
        Returns:
        --------
        float : Equilibrium temperature in K
        """
        absorbed_flux = stellar_flux * (1 - albedo)
        # Factor of 4 from geometry (sphere vs. disk)
        temp = (absorbed_flux / (4 * STEFAN_BOLTZMANN * emissivity)) ** 0.25
        return temp
    
    @staticmethod
    def surface_temperature(equilibrium_temp: float, 
                          atmosphere: AtmosphereModel) -> float:
        """
        Calculate surface temperature including greenhouse effect
        
        Parameters:
        -----------
        equilibrium_temp : float
            Equilibrium temperature in K
        atmosphere : AtmosphereModel
            Atmospheric model object
            
        Returns:
        --------
        float : Surface temperature in K
        """
        greenhouse_warming = atmosphere.greenhouse_effect(equilibrium_temp)
        return equilibrium_temp + greenhouse_warming
    
    @staticmethod
    def jeans_escape_parameter(planet_mass: float, planet_radius: float,
                              temperature: float, molecular_mass: float) -> float:
        """
        Calculate Jeans escape parameter
        
        λ = GMm / (kTr)
        
        λ > 6: Negligible escape
        λ < 6: Significant atmospheric loss
        
        Parameters:
        -----------
        planet_mass : float
            Planet mass in Earth masses
        planet_radius : float
            Planet radius in Earth radii
        temperature : float
            Exospheric temperature in K
        molecular_mass : float
            Molecular mass in kg/mol
            
        Returns:
        --------
        float : Jeans parameter (dimensionless)
        """
        mass_kg = planet_mass * EARTH_MASS
        radius_m = planet_radius * EARTH_RADIUS
        
        # Exobase at ~500 km above surface (rough approximation)
        exobase_radius = radius_m + 500e3
        
        molecular_mass_kg = molecular_mass / AVOGADRO
        
        lambda_j = (GRAVITATIONAL_CONSTANT * mass_kg * molecular_mass_kg) / \
                   (BOLTZMANN_CONSTANT * temperature * exobase_radius)
        
        return lambda_j
    
    @staticmethod
    def jeans_escape_rate(planet_mass: float, planet_radius: float,
                         temperature: float, molecular_mass: float,
                         atmospheric_pressure: float) -> float:
        """
        Calculate Jeans escape rate
        
        Φ = n * v_th * exp(-λ) * (1 + λ) / 2
        
        Parameters:
        -----------
        planet_mass : float
            Planet mass in Earth masses
        planet_radius : float
            Planet radius in Earth radii
        temperature : float
            Exospheric temperature in K
        molecular_mass : float
            Molecular mass in kg/mol
        atmospheric_pressure : float
            Surface pressure in Pa
            
        Returns:
        --------
        float : Escape rate in kg/s
        """
        lambda_j = PlanetaryPhysics.jeans_escape_parameter(
            planet_mass, planet_radius, temperature, molecular_mass
        )
        
        # If lambda > 10, escape is negligible
        if lambda_j > 10:
            return 0.0
        
        # Number density at exobase (simplified)
        molecular_mass_kg = molecular_mass / AVOGADRO
        
        # Thermal velocity
        v_th = np.sqrt(8 * BOLTZMANN_CONSTANT * temperature / 
                      (np.pi * molecular_mass_kg))
        
        # Number density (rough approximation)
        radius_m = planet_radius * EARTH_RADIUS
        exobase_radius = radius_m + 500e3
        surface_area = 4 * np.pi * exobase_radius ** 2
        
        # Scale height approximation
        gravity = GRAVITATIONAL_CONSTANT * (planet_mass * EARTH_MASS) / radius_m ** 2
        scale_height = (BOLTZMANN_CONSTANT * temperature) / (molecular_mass_kg * gravity)
        
        # Density at exobase
        n_exobase = (atmospheric_pressure / (BOLTZMANN_CONSTANT * temperature)) * \
                    np.exp(-500e3 / scale_height)
        
        # Jeans escape flux (particles/m^2/s)
        phi = n_exobase * v_th * np.exp(-lambda_j) * (1 + lambda_j) / 2
        
        # Total escape rate
        escape_rate = phi * surface_area * molecular_mass_kg
        
        return escape_rate
    
    @staticmethod
    def atmospheric_lifetime(planet_mass: float, planet_radius: float,
                            temperature: float, molecular_mass: float,
                            atmospheric_pressure: float) -> float:
        """
        Estimate atmospheric lifetime against Jeans escape
        
        Parameters:
        -----------
        [Same as jeans_escape_rate]
        
        Returns:
        --------
        float : Lifetime in years (or np.inf if stable)
        """
        escape_rate = PlanetaryPhysics.jeans_escape_rate(
            planet_mass, planet_radius, temperature, 
            molecular_mass, atmospheric_pressure
        )
        
        if escape_rate == 0:
            return np.inf
        
        # Estimate total atmospheric mass
        radius_m = planet_radius * EARTH_RADIUS
        surface_area = 4 * np.pi * radius_m ** 2
        gravity = GRAVITATIONAL_CONSTANT * (planet_mass * EARTH_MASS) / radius_m ** 2
        
        # Total mass = pressure * area / gravity
        total_mass = atmospheric_pressure * surface_area / gravity
        
        # Lifetime in seconds
        lifetime_s = total_mass / escape_rate
        
        # Convert to years
        lifetime_years = lifetime_s / (365.25 * 24 * 3600)
        
        return lifetime_years
    
    @staticmethod
    def habitable_zone_distance(star_luminosity: float, 
                               inner_factor: float = 0.95,
                               outer_factor: float = 1.37) -> Tuple[float, float]:
        """
        Calculate conservative habitable zone boundaries
        
        Based on stellar luminosity and using Earth-equivalent flux
        
        Parameters:
        -----------
        star_luminosity : float
            Stellar luminosity in solar luminosities
        inner_factor : float
            Inner HZ boundary flux factor (Recent Venus = 1.77, Conservative = 0.95)
        outer_factor : float
            Outer HZ boundary flux factor (Early Mars = 0.32, Conservative = 1.37)
            
        Returns:
        --------
        tuple : (inner_distance_AU, outer_distance_AU)
        """
        # Conservative HZ (Kopparapu et al. 2013)
        inner_distance = np.sqrt(star_luminosity / inner_factor)
        outer_distance = np.sqrt(star_luminosity / outer_factor)
        
        return (inner_distance, outer_distance)
    
    @staticmethod
    def is_in_habitable_zone(semi_major_axis: float, 
                            star_luminosity: float) -> bool:
        """Check if planet is in habitable zone"""
        hz_inner, hz_outer = PlanetaryPhysics.habitable_zone_distance(star_luminosity)
        return hz_inner <= semi_major_axis <= hz_outer