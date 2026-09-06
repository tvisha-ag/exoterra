"""
ExoTerra - Atmospheric Model Module
Handles atmospheric composition, greenhouse effects, and pressure calculations
"""

import numpy as np
from typing import Dict, Tuple
from constants import *

class AtmosphereModel:
    """
    Models atmospheric composition and radiative transfer
    Uses simplified but physically-motivated approaches
    """
    
    def __init__(self, composition: Dict[str, float], 
                 total_pressure: float = 101325.0):
        """
        Initialize atmosphere
        
        Parameters:
        -----------
        composition : dict
            Gas partial pressures {gas_name: pressure_Pa}
        total_pressure : float
            Total surface pressure in Pascals
        """
        self.composition = composition
        self.total_pressure = total_pressure
        self._normalize_composition()
    
    def _normalize_composition(self):
        """Ensure composition sums to total pressure"""
        current_total = sum(self.composition.values())
        if current_total > 0:
            scale = self.total_pressure / current_total
            self.composition = {
                gas: pressure * scale 
                for gas, pressure in self.composition.items()
            }
    
    def mean_molecular_weight(self) -> float:
        """
        Calculate mean molecular weight of atmosphere
        
        Returns:
        --------
        float : Mean molecular weight in kg/mol
        """
        total_moles = 0
        total_mass = 0
        
        for gas, pressure in self.composition.items():
            if gas in MOLECULAR_WEIGHTS:
                # Partial pressure proportional to mole fraction
                mole_fraction = pressure / self.total_pressure
                mol_weight = MOLECULAR_WEIGHTS[gas]
                
                total_moles += mole_fraction
                total_mass += mole_fraction * mol_weight
        
        if total_moles > 0:
            return (total_mass / total_moles) / 1000  # Convert g/mol to kg/mol
        return 0.029  # Default to Earth-like (N2/O2 mix)
    
    def scale_height(self, surface_temp: float, gravity: float) -> float:
        """
        Calculate atmospheric scale height
        
        H = kT / (μg)
        
        Parameters:
        -----------
        surface_temp : float
            Surface temperature in K
        gravity : float
            Surface gravity in m/s^2
            
        Returns:
        --------
        float : Scale height in meters
        """
        mmw = self.mean_molecular_weight()
        return (BOLTZMANN_CONSTANT * surface_temp) / (mmw * gravity / AVOGADRO)
    
    def greenhouse_effect(self, equilibrium_temp: float) -> float:
        """
        Calculate greenhouse warming using enhanced Stefan-Boltzmann
        
        Uses optical depth approximation:
        ΔT = T_eq * τ^0.25 - T_eq
        
        Where τ is optical depth from greenhouse gases
        
        Parameters:
        -----------
        equilibrium_temp : float
            Equilibrium temperature without atmosphere (K)
            
        Returns:
        --------
        float : Greenhouse warming in K
        """
        optical_depth = self._calculate_optical_depth()
        
        # Enhanced greenhouse effect
        # Based on simplified radiative-convective model
        if optical_depth > 0:
            # T_surf = T_eq * (1 + τ)^0.25
            surface_temp = equilibrium_temp * (1 + optical_depth) ** 0.25
            greenhouse_warming = surface_temp - equilibrium_temp
        else:
            greenhouse_warming = 0
        
        return greenhouse_warming
    
    def _calculate_optical_depth(self) -> float:
        """
        Calculate atmospheric optical depth from greenhouse gases
        
        Simplified model: τ = Σ (P_i * GWP_i) / P_ref
        
        Returns:
        --------
        float : Dimensionless optical depth
        """
        tau = 0
        
        # Reference: Earth's CO2 contribution (~280 ppm historical)
        p_ref_co2 = 28.3  # Pa (280 ppm at 1 atm)
        
        for gas, pressure in self.composition.items():
            if gas in GREENHOUSE_POTENTIALS:
                # Normalize by reference and scale by potential
                contribution = (pressure / p_ref_co2) * GREENHOUSE_POTENTIALS[gas]
                tau += contribution
        
        # Apply logarithmic saturation (prevents runaway at high concentrations)
        tau_effective = np.log1p(tau)
        
        return tau_effective
    
    def emissivity(self) -> float:
        """
        Calculate atmospheric emissivity (0-1)
        
        Returns:
        --------
        float : Atmospheric emissivity
        """
        tau = self._calculate_optical_depth()
        # Approximate emissivity from optical depth
        return 1 - np.exp(-tau)
    
    def update_composition(self, gas: str, pressure: float):
        """Update partial pressure of a gas"""
        self.composition[gas] = pressure
        self.total_pressure = sum(self.composition.values())
    
    def add_gas(self, gas: str, pressure: float):
        """Add or update a gas in the atmosphere"""
        if gas not in MOLECULAR_WEIGHTS:
            raise ValueError(f"Unknown gas: {gas}")
        self.update_composition(gas, pressure)