"""
ExoTerra Elite - Advanced Computational Physics Module
Research-grade astrophysical modeling for planetary atmospheres

Module A: JWST Transmission Spectroscopy & Technosignatures
Module B: MHD Stellar Wind & Atmospheric Stripping  
Module C: Latitudinal Energy Balance & Snowball Bifurcation
"""

import numpy as np
from typing import Dict, Tuple, List
from scipy.integrate import odeint
from scipy.optimize import fsolve
from planetary_state import PlanetaryState
from constants import *

# ============================================================================
# MODULE A: JWST Transmission Spectroscopy & Technosignatures
# ============================================================================

class TransmissionSpectroscopy:
    """
    Calculate mid-infrared transmission spectrum for exoplanet atmospheres
    Simulates JWST MIRI observations (5-28 μm)
    
    References:
    - Kreidberg et al. (2014) - Transmission spectroscopy technique
    - Lustig-Yaeger et al. (2019) - Biosignature detectability
    """
    
    def __init__(self):
        # Wavelength range for MIRI (micrometers)
        self.wavelengths = np.linspace(5.0, 28.0, 500)  # μm
        
        # Absorption cross-sections (simplified Lorentzian profiles)
        # In reality, use HITRAN database
        self.absorption_bands = {
            'CO2': [(15.0, 0.5, 1e-18)],  # (center_μm, width_μm, strength_cm²)
            'H2O': [(6.3, 0.4, 8e-19), (20.0, 3.0, 5e-19)],
            'CH4': [(7.7, 0.3, 6e-19), (12.0, 0.5, 4e-19)],
            'O3': [(9.6, 0.6, 1.2e-18)],
            'N2O': [(7.8, 0.3, 3e-18), (17.0, 0.8, 2e-18)],
            # Technosignature gases (anthropogenic)
            'SF6': [(10.5, 0.2, 5e-17)],  # Sulfur hexafluoride (very strong)
            'CF4': [(7.8, 0.3, 2e-18)],   # Tetrafluoromethane
            'CCl4': [(13.0, 0.5, 8e-18)], # Carbon tetrachloride
        }
    
    def lorentzian_profile(self, wavelength: float, center: float, 
                          width: float, strength: float) -> float:
        """Lorentzian absorption line profile"""
        return strength * (width**2) / ((wavelength - center)**2 + width**2)
    
    def calculate_optical_depth(self, state: PlanetaryState, 
                               wavelength: float) -> float:
        """
        Calculate atmospheric optical depth at given wavelength
        
        τ(λ) = Σ n_i * σ_i(λ) * H
        
        where:
        - n_i: number density of species i
        - σ_i(λ): absorption cross-section
        - H: atmospheric scale height
        """
        # Calculate scale height
        temp = state.surface_temperature
        gravity = GRAVITATIONAL_CONSTANT * (state.planet_mass * EARTH_MASS) / \
                 (state.planet_radius * EARTH_RADIUS) ** 2
        
        from atmosphere_model import AtmosphereModel
        atm = AtmosphereModel(state.atmosphere, state.surface_pressure)
        scale_height = atm.scale_height(temp, gravity)
        
        # Total optical depth
        tau = 0.0
        
        for gas, pressure_pa in state.atmosphere.items():
            if gas not in self.absorption_bands:
                continue
            
            # Number density (ideal gas law)
            n = pressure_pa / (BOLTZMANN_CONSTANT * temp)  # molecules/m³
            
            # Sum over all absorption bands for this gas
            for center, width, strength in self.absorption_bands[gas]:
                sigma = self.lorentzian_profile(wavelength, center, width, strength)
                tau += n * sigma * scale_height
        
        return tau
    
    def calculate_transmission_spectrum(self, state: PlanetaryState) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate full transmission spectrum
        
        Returns:
        --------
        wavelengths : array
            Wavelength grid (μm)
        transit_depth : array
            Relative transit depth (Rp/Rs)² * (1 + τ_eff)
        """
        transit_depths = np.zeros_like(self.wavelengths)
        
        planet_radius = state.planet_radius * EARTH_RADIUS
        star_radius = state.star_mass ** 0.8 * SOLAR_RADIUS  # Mass-radius relation
        
        baseline_depth = (planet_radius / star_radius) ** 2
        
        for i, wavelength in enumerate(self.wavelengths):
            tau = self.calculate_optical_depth(state, wavelength)
            
            # Effective radius increase from atmosphere
            # ΔR/R ≈ H * τ / R_p
            temp = state.surface_temperature
            gravity = GRAVITATIONAL_CONSTANT * (state.planet_mass * EARTH_MASS) / \
                     (state.planet_radius * EARTH_RADIUS) ** 2
            
            from atmosphere_model import AtmosphereModel
            atm = AtmosphereModel(state.atmosphere, state.surface_pressure)
            scale_height = atm.scale_height(temp, gravity)
            
            delta_r = scale_height * np.tanh(tau)  # Saturates at high optical depth
            effective_radius = planet_radius + delta_r
            
            transit_depths[i] = (effective_radius / star_radius) ** 2
        
        # Convert to parts per million (ppm)
        transit_depths_ppm = (transit_depths - baseline_depth) * 1e6
        
        return self.wavelengths, transit_depths_ppm
    
    def identify_technosignatures(self, state: PlanetaryState) -> Dict[str, float]:
        """
        Identify and quantify artificial atmospheric technosignatures
        
        Returns:
        --------
        dict: {gas_name: detection_confidence_score}
        """
        technosigs = {}
        
        artificial_gases = ['SF6', 'CF4', 'CCl4']
        
        for gas in artificial_gases:
            if gas in state.atmosphere:
                pressure = state.atmosphere[gas]
                # Detection threshold: ~1 ppb at 1 bar for SF6 with JWST
                threshold_pa = 1e-9 * state.surface_pressure
                
                if pressure > threshold_pa:
                    # Confidence score (0-1)
                    confidence = min(1.0, np.log10(pressure / threshold_pa) / 3)
                    technosigs[gas] = confidence
        
        return technosigs


# ============================================================================
# MODULE B: MHD Stellar Wind & Atmospheric Stripping
# ============================================================================

class StellarWindModel:
    """
    Magnetohydrodynamic stellar wind and atmospheric erosion model
    
    Implements:
    - Parker solar wind solution
    - Magnetic dipole shielding
    - Ion pickup and sputtering
    - Stellar flare events
    
    References:
    - Parker (1958) - Solar wind theory
    - Brain et al. (2013) - Mars atmospheric loss
    - Dong et al. (2018) - Exoplanet magnetospheres
    """
    
    def __init__(self):
        self.flare_frequency = 0.1  # flares per year for active M-dwarf
        self.base_wind_density = 5e6  # particles/m³ at 1 AU for Sun
        self.base_wind_velocity = 400e3  # m/s
    
    def stellar_wind_properties(self, star_mass: float, 
                                star_luminosity: float,
                                orbital_distance: float) -> Tuple[float, float, float]:
        """
        Calculate stellar wind density, velocity, and dynamic pressure
        
        Scales with stellar parameters using empirical relations
        
        Returns:
        --------
        density : float
            Wind particle density at planet (particles/m³)
        velocity : float  
            Wind velocity (m/s)
        dynamic_pressure : float
            Ram pressure (Pa)
        """
        # Stellar wind scales with X-ray luminosity
        # L_X ~ L_bol^1.5 for active stars (Wright et al. 2011)
        activity_factor = star_luminosity ** 0.5
        
        # Mass loss rate scales with luminosity
        # Mdot ~ L^1.3 (Suzuki 2013)
        mass_loss_ratio = (star_luminosity) ** 1.3
        
        # Wind velocity (relatively constant ~escape velocity)
        v_wind = self.base_wind_velocity * np.sqrt(star_mass)
        
        # Density at orbital distance (1/r² dilution)
        n_wind = (self.base_wind_density * mass_loss_ratio * activity_factor) / \
                 (orbital_distance ** 2)
        
        # Dynamic pressure: P_dyn = ρ v²
        # Use proton mass for density
        rho_wind = n_wind * 1.67e-27  # kg/m³
        p_dyn = rho_wind * v_wind ** 2
        
        return n_wind, v_wind, p_dyn
    
    def magnetospheric_standoff_distance(self, state: PlanetaryState,
                                         dynamic_pressure: float) -> float:
        """
        Calculate magnetopause standoff distance
        
        Pressure balance:
        B²/(2μ₀) = P_dyn
        
        Returns:
        --------
        standoff_distance : float
            Magnetopause distance in planetary radii
        """
        if not state.has_artificial_magnetosphere or state.magnetic_field_strength == 0:
            # No magnetic protection - atmosphere directly exposed
            return 1.0  # Surface
        
        # Magnetic field strength at equator
        # Dipole: B = B_0 (R_p/r)³
        # Earth's surface field: 3.05e-5 T
        b_surface = 3.05e-5 * state.magnetic_field_strength
        
        # Standoff distance from pressure balance
        # r_mp = R_p * (B²/(2μ₀ P_dyn))^(1/6)
        mu_0 = 4 * np.pi * 1e-7
        
        r_mp_ratio = ((b_surface ** 2) / (2 * mu_0 * dynamic_pressure)) ** (1/6)
        
        return r_mp_ratio
    
    def atmospheric_loss_rate(self, state: PlanetaryState,
                              n_wind: float, v_wind: float,
                              p_dyn: float) -> float:
        """
        Calculate total atmospheric loss rate from all mechanisms
        
        Mechanisms:
        1. Jeans thermal escape (already in feedback_loops.py)
        2. Ion pickup (ionosphere interaction)
        3. Sputtering (energetic particle impact)
        
        Returns:
        --------
        loss_rate : float
            Total atmospheric mass loss (kg/s)
        """
        planet_radius = state.planet_radius * EARTH_RADIUS
        
        # 1. Jeans escape (use existing calculation)
        from planetary_physics import PlanetaryPhysics
        physics = PlanetaryPhysics()
        
        jeans_loss = 0
        for gas in ['H2', 'He', 'H2O']:
            if gas in state.atmosphere:
                molecular_mass = MOLECULAR_WEIGHTS[gas] / 1000
                jeans_rate = physics.jeans_escape_rate(
                    state.planet_mass, state.planet_radius,
                    state.surface_temperature, molecular_mass,
                    state.atmosphere[gas]
                )
                jeans_loss += jeans_rate
        
        # 2. Ion pickup loss
        # Ions in ionosphere get swept away by stellar wind
        r_mp = self.magnetospheric_standoff_distance(state, p_dyn)
        
        if r_mp < 2.0:  # Magnetosphere compressed - significant loss
            # Cross-sectional area exposed to wind
            area_exposed = np.pi * (r_mp * planet_radius) ** 2
            
            # Ion production rate from EUV ionization
            # Scales with EUV flux ~ L_star/d²
            euv_flux = (state.star_luminosity * SOLAR_LUMINOSITY * 0.01) / \
                      (4 * np.pi * (state.semi_major_axis * AU) ** 2)
            
            ionization_rate = euv_flux * area_exposed / (13.6 * 1.6e-19)  # ions/s
            
            # Mass loss (assume average molecular weight)
            from atmosphere_model import AtmosphereModel
            atm = AtmosphereModel(state.atmosphere, state.surface_pressure)
            mmw = atm.mean_molecular_weight()
            
            ion_pickup_loss = ionization_rate * mmw / AVOGADRO
        else:
            ion_pickup_loss = 0
        
        # 3. Sputtering
        # Energetic particles knock off atmospheric atoms
        if r_mp < 1.5:
            # Sputtering yield ~ 0.1 atoms per incident ion
            sputtering_flux = n_wind * v_wind * 0.1  # atoms/m²/s
            surface_area = 4 * np.pi * planet_radius ** 2
            
            from atmosphere_model import AtmosphereModel
            atm = AtmosphereModel(state.atmosphere, state.surface_pressure)
            mmw = atm.mean_molecular_weight()
            
            sputtering_loss = sputtering_flux * surface_area * mmw / AVOGADRO
        else:
            sputtering_loss = 0
        
        # Total loss (Jeans usually dominates for light species)
        total_loss = jeans_loss + ion_pickup_loss + sputtering_loss
        
        # Magnetic field reduces non-thermal losses
        if state.has_artificial_magnetosphere:
            protection_factor = min(1.0, state.magnetic_field_strength)
            ion_pickup_loss *= (1 - protection_factor)
            sputtering_loss *= (1 - protection_factor)
        
        return total_loss
    
    def simulate_stellar_flare(self, state: PlanetaryState) -> float:
        """
        Simulate atmospheric loss during stellar flare event
        
        M-dwarfs can have superflares 100-10000x solar flares
        
        Returns:
        --------
        mass_lost : float
            Atmospheric mass stripped during flare (kg)
        """
        # Flare energy (erg) - X-class equivalent
        flare_energy = 1e32 * (2 - state.star_mass)  # Stronger for low-mass stars
        
        # Convert to particle flux enhancement
        flux_multiplier = 100  # 100x normal during flare
        
        # Duration (hours)
        duration = 3600 * np.random.uniform(1, 10)
        
        n_wind, v_wind, p_dyn = self.stellar_wind_properties(
            state.star_mass, state.star_luminosity, state.semi_major_axis
        )
        
        # Enhanced loss during flare
        normal_loss = self.atmospheric_loss_rate(state, n_wind, v_wind, p_dyn)
        flare_loss = normal_loss * flux_multiplier * duration
        
        # Magnetic field provides significant protection
        if state.has_artificial_magnetosphere:
            protection = state.magnetic_field_strength
            flare_loss *= (1 - 0.9 * protection)  # Up to 90% protection
        
        return flare_loss


# ============================================================================
# MODULE C: Latitudinal Energy Balance & Snowball Bifurcation
# ============================================================================

class LatitudinalEnergyBalance:
    """
    1D Energy Balance Model with ice-albedo feedback
    
    Solves the latitudinal temperature distribution:
    C(dT/dt) = Q(φ) - IR_out + D(d²T/dφ²)
    
    Where:
    - φ: latitude
    - Q(φ): absorbed stellar radiation
    - IR_out: outgoing infrared
    - D: horizontal heat diffusion
    
    Can exhibit bistability (ice-free vs. snowball states)
    
    References:
    - Budyko (1969) - Energy balance climate model
    - Sellers (1969) - Albedo feedback
    - North (1975) - Analytical EBM solutions
    - Hoffman & Schrag (2002) - Snowball Earth
    """
    
    def __init__(self, num_latitude_bands: int = 50):
        """
        Initialize 1D EBM
        
        Parameters:
        -----------
        num_latitude_bands : int
            Number of latitude bands (resolution)
        """
        self.n_lat = num_latitude_bands
        
        # Latitude grid (degrees)
        self.latitudes = np.linspace(-90, 90, num_latitude_bands)
        
        # Convert to radians
        self.phi = np.deg2rad(self.latitudes)
        
        # Grid spacing
        self.dphi = self.phi[1] - self.phi[0]
        
        # Climate parameters
        self.heat_capacity = 4e8  # J/m²/K (ocean mixed layer ~100m)
        self.diffusion_coeff = 0.6  # W/m²/K (heat transport)
        
        # Ice line (critical temperature for ice formation)
        self.ice_temperature = 273.15  # K
        
        # Albedo parameters
        self.albedo_ice = 0.6  # Ice-covered
        self.albedo_ocean = 0.2  # Ice-free ocean
        self.albedo_land = 0.3  # Ice-free land
    
    def solar_distribution(self, phi: np.ndarray, stellar_flux: float,
                          obliquity: float = 23.5) -> np.ndarray:
        """
        Calculate latitudinal distribution of absorbed stellar radiation
        
        Annual mean insolation with obliquity:
        Q(φ) = (S/4) * P(φ, ε)
        
        where P is the distribution function
        
        Parameters:
        -----------
        phi : array
            Latitude in radians
        stellar_flux : float
            Total stellar flux at planet (W/m²)
        obliquity : float
            Axial tilt in degrees
            
        Returns:
        --------
        Q : array
            Absorbed radiation at each latitude (W/m²)
        """
        eps = np.deg2rad(obliquity)
        
        # Distribution function (annual mean)
        # Simplified: P(φ) ≈ 1 + 0.5*P₂(sin φ)
        # where P₂ is the Legendre polynomial
        
        sin_phi = np.sin(phi)
        P2 = 0.5 * (3 * sin_phi**2 - 1)
        
        # Equator-to-pole gradient
        P = 1 - 0.482 * P2
        
        # Total insolation (factor of 4 from geometry)
        Q = (stellar_flux / 4) * P
        
        return Q
    
    def calculate_albedo(self, temperature: np.ndarray,
                        ice_coverage: float = 0.0) -> np.ndarray:
        """
        Calculate latitude-dependent albedo with ice-albedo feedback
        
        Parameters:
        -----------
        temperature : array
            Temperature at each latitude (K)
        ice_coverage : float
            Current global ice coverage fraction
            
        Returns:
        --------
        albedo : array
            Albedo at each latitude
        """
        albedo = np.zeros_like(temperature)
        
        for i, T in enumerate(temperature):
            if T < self.ice_temperature:
                # Ice-covered (high albedo)
                albedo[i] = self.albedo_ice
            else:
                # Ice-free (low albedo)
                # Mix of ocean and land
                albedo[i] = 0.7 * self.albedo_ocean + 0.3 * self.albedo_land
        
        return albedo
    
    def outgoing_radiation(self, temperature: np.ndarray,
                          emissivity: float = 0.6) -> np.ndarray:
        """
        Calculate outgoing longwave radiation
        
        Linearized around reference temperature:
        OLR = A + B*T
        
        Parameters:
        -----------
        temperature : array
            Surface temperature (K)
        emissivity : float
            Atmospheric emissivity
            
        Returns:
        --------
        OLR : array
            Outgoing radiation (W/m²)
        """
        # Empirical linearization (Sellers 1969)
        A = 202  # W/m²
        B = 1.9  # W/m²/K
        
        # With greenhouse effect
        effective_emissivity = 1 - emissivity
        
        OLR = effective_emissivity * (A + B * (temperature - 273))
        
        return OLR
    
    def heat_diffusion(self, temperature: np.ndarray) -> np.ndarray:
        """
        Calculate horizontal heat transport (diffusion)
        
        Flux: F = -D * dT/dφ
        Convergence: ∇·F = D * d²T/dφ²
        
        Parameters:
        -----------
        temperature : array
            Temperature distribution
            
        Returns:
        --------
        diffusion : array
            Heat transport convergence (W/m²)
        """
        # Second derivative (finite difference)
        d2T = np.zeros_like(temperature)
        
        for i in range(1, len(temperature) - 1):
            d2T[i] = (temperature[i+1] - 2*temperature[i] + temperature[i-1]) / self.dphi**2
        
        # Boundary conditions (no flux at poles)
        d2T[0] = 0
        d2T[-1] = 0
        
        diffusion = self.diffusion_coeff * d2T
        
        return diffusion
    
    def compute_equilibrium_temperature(self, state: PlanetaryState,
                                       initial_guess: np.ndarray = None,
                                       max_iterations: int = 1000,
                                       tolerance: float = 0.1) -> Tuple[np.ndarray, bool]:
        """
        Solve for equilibrium temperature distribution
        
        Iteratively solve energy balance until convergence
        
        Parameters:
        -----------
        state : PlanetaryState
            Current planetary state
        initial_guess : array, optional
            Initial temperature distribution
        max_iterations : int
            Maximum iterations
        tolerance : float
            Convergence criterion (K)
            
        Returns:
        --------
        temperature : array
            Equilibrium temperature distribution (K)
        snowball : bool
            Whether planet is in snowball state
        """
        if initial_guess is None:
            # Start from global mean temperature
            temperature = np.full(self.n_lat, state.surface_temperature)
        else:
            temperature = initial_guess.copy()
        
        # Greenhouse emissivity
        from atmosphere_model import AtmosphereModel
        atm = AtmosphereModel(state.atmosphere, state.surface_pressure)
        emissivity = atm.emissivity()
        
        # Stellar flux distribution
        Q_solar = self.solar_distribution(self.phi, state.stellar_flux)
        
        # Iteration
        for iteration in range(max_iterations):
            temperature_old = temperature.copy()
            
            # Calculate albedo (depends on temperature via ice)
            albedo = self.calculate_albedo(temperature)
            
            # Absorbed radiation
            Q_absorbed = Q_solar * (1 - albedo)
            
            # Outgoing radiation
            Q_out = self.outgoing_radiation(temperature, emissivity)
            
            # Heat transport
            Q_diffusion = self.heat_diffusion(temperature)
            
            # Energy balance
            dQ = Q_absorbed - Q_out + Q_diffusion
            
            # Update temperature (semi-implicit with damping)
            dt_eff = 86400 * 365 * 10  # 10 years
            dT = dQ * dt_eff / self.heat_capacity
            
            # Damping factor for stability
            damping = 0.3
            temperature = temperature_old + damping * dT
            
            # Check convergence
            max_change = np.max(np.abs(temperature - temperature_old))
            
            if max_change < tolerance:
                break
        
        # Detect snowball state (ice-covered poles extend to equator)
        ice_latitude = self.latitudes[temperature < self.ice_temperature]
        
        if len(ice_latitude) > 0:
            max_ice_extent = np.max(np.abs(ice_latitude))
            snowball = max_ice_extent > 60  # Ice beyond 60° latitude
        else:
            snowball = False
        
        return temperature, snowball
    
    def calculate_ice_line_latitude(self, temperature: np.ndarray) -> float:
        """
        Find latitude of ice edge
        
        Returns:
        --------
        ice_line : float
            Latitude where ice begins (degrees)
            or 90 if no ice, 0 if full snowball
        """
        ice_mask = temperature < self.ice_temperature
        
        if not np.any(ice_mask):
            return 90.0  # No ice
        
        if np.all(ice_mask):
            return 0.0  # Full snowball
        
        # Find transition
        for i in range(len(temperature)):
            if ice_mask[i]:
                # Interpolate to find exact ice line
                if i > 0:
                    ice_line = self.latitudes[i-1] + \
                              (self.ice_temperature - temperature[i-1]) / \
                              (temperature[i] - temperature[i-1]) * \
                              (self.latitudes[i] - self.latitudes[i-1])
                else:
                    ice_line = self.latitudes[i]
                
                return abs(ice_line)
        
        return 90.0


# ============================================================================
# INTEGRATION MODULE: Enhanced Simulation Engine
# ============================================================================

class EliteSimulationEngine:
    """
    Enhanced simulation engine integrating advanced physics modules
    """
    
    def __init__(self, state: PlanetaryState):
        self.state = state
        
        # Initialize advanced modules
        self.spectroscopy = TransmissionSpectroscopy()
        self.stellar_wind = StellarWindModel()
        self.energy_balance = LatitudinalEnergyBalance()
        
        # Storage for advanced diagnostics
        self.transmission_spectrum = None
        self.latitudinal_temps = None
        self.ice_line_history = []
        self.technosignature_detections = {}
    
    def update_advanced_physics(self):
        """Run all advanced physics calculations"""
        
        # Module A: Transmission spectroscopy
        wavelengths, transit_depth = self.spectroscopy.calculate_transmission_spectrum(self.state)
        self.transmission_spectrum = (wavelengths, transit_depth)
        
        # Check for technosignatures
        self.technosignature_detections = self.spectroscopy.identify_technosignatures(self.state)
        
        # Module B: Stellar wind
        n_wind, v_wind, p_dyn = self.stellar_wind.stellar_wind_properties(
            self.state.star_mass,
            self.state.star_luminosity,
            self.state.semi_major_axis
        )
        
        self.stellar_wind_params = {
            'density': n_wind,
            'velocity': v_wind,
            'pressure': p_dyn,
        }
        
        # Module C: Latitudinal energy balance
        temps, snowball = self.energy_balance.compute_equilibrium_temperature(self.state)
        self.latitudinal_temps = temps
        self.is_snowball = snowball
        
        ice_line = self.energy_balance.calculate_ice_line_latitude(temps)
        self.ice_line_history.append(ice_line)
        
        # Update global average in state
        self.state.surface_temperature = np.mean(temps)
    
    def get_diagnostics(self) -> Dict:
        """Get all advanced diagnostics"""
        return {
            'transmission_spectrum': self.transmission_spectrum,
            'technosignatures': self.technosignature_detections,
            'stellar_wind': self.stellar_wind_params,
            'latitudinal_temps': self.latitudinal_temps,
            'snowball_state': self.is_snowball,
            'ice_line': self.ice_line_history[-1] if self.ice_line_history else 90.0,
        }