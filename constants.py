"""
ExoTerra - Physical Constants Module
Contains all physical constants in SI units
"""

import numpy as np

# Universal Constants
STEFAN_BOLTZMANN = 5.670374419e-8  # W m^-2 K^-4
GRAVITATIONAL_CONSTANT = 6.67430e-11  # m^3 kg^-1 s^-2
BOLTZMANN_CONSTANT = 1.380649e-23  # J K^-1
AVOGADRO = 6.02214076e23  # mol^-1
GAS_CONSTANT = 8.314462618  # J mol^-1 K^-1

# Solar/Earth Reference Values
SOLAR_LUMINOSITY = 3.828e26  # W
SOLAR_MASS = 1.989e30  # kg
SOLAR_RADIUS = 6.96e8  # m
SOLAR_TEMPERATURE = 5778  # K

EARTH_MASS = 5.972e24  # kg
EARTH_RADIUS = 6.371e6  # m
EARTH_GRAVITY = 9.81  # m s^-2
EARTH_ALBEDO = 0.30  # Bond albedo
EARTH_TEMPERATURE = 288  # K (surface)
EARTH_EQUILIBRIUM_TEMP = 255  # K (without greenhouse)
EARTH_GREENHOUSE_EFFECT = 33  # K

AU = 1.496e11  # m (Astronomical Unit)

# Atmospheric Molecular Weights (g/mol)
MOLECULAR_WEIGHTS = {
    'H2': 2.016,
    'He': 4.003,
    'N2': 28.014,
    'O2': 31.998,
    'CO2': 44.009,
    'CH4': 16.043,
    'H2O': 18.015,
    'NH3': 17.031,
    'Ar': 39.948,
}

# Greenhouse Gas Properties (simplified radiative efficiency)
GREENHOUSE_POTENTIALS = {
    'CO2': 1.0,
    'CH4': 28.0,
    'H2O': 0.1,
    'N2O': 265.0,
    'O3': 2000.0,
    'NH3': 0.5,
}

# Atmospheric Escape Constants
JEANS_PARAMETER_THRESHOLD = 6.0
EXOSPHERE_FRACTION = 0.5

# Habitable Zone Criteria
HABITABLE_TEMP_MIN = 273  # K
HABITABLE_TEMP_MAX = 373  # K
HABITABLE_PRESSURE_MIN = 0.01e5  # Pa
HABITABLE_PRESSURE_MAX = 100e5  # Pa