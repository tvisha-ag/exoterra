"""
ExoTerra - Interactive Web Dashboard
A beautiful Streamlit application for planetary terraforming simulation
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime
import json

# Import our modules
from planetary_state import PlanetaryState, StateHistory
from simulation_engine import TerraformingSimulation
from interventions import *
from habitability import HabitabilityIndex
from exoplanet_data import ExoplanetDatabase
from constants import *

# Page configuration
st.set_page_config(
    page_title="ExoTerra - Planetary Terraforming Simulator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #10b981, #34d399);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        animation: pulse 2s infinite;
        margin: 1rem 0;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .warning-banner {
        background: linear-gradient(90deg, #f59e0b, #f97316);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'simulation' not in st.session_state:
        st.session_state.simulation = None
    if 'planet_initialized' not in st.session_state:
        st.session_state.planet_initialized = False
    if 'celebration_shown' not in st.session_state:
        st.session_state.celebration_shown = False
    if 'auto_run' not in st.session_state:
        st.session_state.auto_run = False
    if 'custom_planet_params' not in st.session_state:
        st.session_state.custom_planet_params = {}

init_session_state()

# Database
@st.cache_resource
def load_database():
    """Load exoplanet database"""
    return ExoplanetDatabase()

db = load_database()

def create_initial_state_from_exoplanet(planet_name: str) -> PlanetaryState:
    """Create initial state from exoplanet data"""
    planet = db.get_planet(planet_name)
    
    if planet is None:
        st.error(f"Planet {planet_name} not found!")
        return None
    
    # Calculate stellar flux
    from planetary_physics import PlanetaryPhysics
    physics = PlanetaryPhysics()
    flux = physics.stellar_flux(planet['star_luminosity'], planet['semi_major_axis'])
    
    # Initial atmospheric guess based on planet type
    if planet['radius'] < 1.5:  # Rocky planet
        if planet['semi_major_axis'] < 0.1:  # Hot, close to star
            atmosphere = {'CO2': 90000.0, 'N2': 3000.0}  # Venus-like
            temp = 600.0
        else:  # Cold, far from star
            atmosphere = {'CO2': 500.0, 'N2': 100.0, 'Ar': 20.0}  # Mars-like
            temp = 200.0
    else:  # Sub-Neptune
        atmosphere = {'H2': 50000.0, 'He': 30000.0, 'H2O': 5000.0}
        temp = 300.0
    
    total_pressure = sum(atmosphere.values())
    
    # Estimate ice masses
    water_ice_mass = planet['mass'] * EARTH_MASS * 0.001  # 0.1% of planet mass
    co2_ice_mass = water_ice_mass * 0.1
    
    return PlanetaryState(
        time_years=0.0,
        planet_mass=planet['mass'],
        planet_radius=planet['radius'],
        semi_major_axis=planet['semi_major_axis'],
        star_luminosity=planet['star_luminosity'],
        star_mass=planet['star_mass'],
        
        atmosphere=atmosphere,
        surface_temperature=temp,
        surface_pressure=total_pressure,
        albedo=planet.get('initial_albedo', 0.3),
        
        ocean_coverage=0.0,
        ice_coverage=0.3 if temp < 273 else 0.0,
        subsurface_ice_mass=water_ice_mass * 0.5,
        atmospheric_water_vapor=atmosphere.get('H2O', 100.0),
        
        co2_ice_mass=co2_ice_mass,
        water_ice_mass=water_ice_mass,
        
        magnetic_field_strength=0.0,
        has_artificial_magnetosphere=False,
        
        biomass=0.0,
        o2_production_rate=0.0,
        
        orbital_mirrors=0,
        atmospheric_processors=0,
        
        stellar_flux=flux,
        greenhouse_effect=0.0,
        equilibrium_temperature=temp,
    )

def create_custom_planet(params: dict) -> PlanetaryState:
    """Create custom planet from user parameters"""
    flux = PlanetaryPhysics().stellar_flux(
        params['star_luminosity'], 
        params['semi_major_axis']
    )
    
    atmosphere = {
        'N2': params['n2_pressure'] * 1e5,
        'O2': params['o2_pressure'] * 1e5,
        'CO2': params['co2_pressure'] * 1e5,
    }
    
    total_pressure = sum(atmosphere.values())
    
    return PlanetaryState(
        time_years=0.0,
        planet_mass=params['planet_mass'],
        planet_radius=params['planet_radius'],
        semi_major_axis=params['semi_major_axis'],
        star_luminosity=params['star_luminosity'],
        star_mass=params['star_mass'],
        
        atmosphere=atmosphere,
        surface_temperature=params['initial_temp'],
        surface_pressure=total_pressure,
        albedo=params['albedo'],
        
        ocean_coverage=params['ocean_coverage'],
        ice_coverage=params['ice_coverage'],
        subsurface_ice_mass=params['water_ice_mass'],
        atmospheric_water_vapor=atmosphere.get('H2O', 0),
        
        co2_ice_mass=params['co2_ice_mass'],
        water_ice_mass=params['water_ice_mass'],
        
        magnetic_field_strength=0.0,
        has_artificial_magnetosphere=False,
        
        biomass=0.0,
        o2_production_rate=0.0,
        
        orbital_mirrors=0,
        atmospheric_processors=0,
        
        stellar_flux=flux,
        greenhouse_effect=0.0,
        equilibrium_temperature=params['initial_temp'],
    )

def get_planet_status_emoji(state: PlanetaryState) -> str:
    """Get status emoji based on conditions"""
    temp_c = state.surface_temperature - 273.15
    
    if temp_c < -50:
        return "🥶 Frozen Wasteland"
    elif temp_c < 0:
        return "❄️ Ice World"
    elif temp_c < 100 and state.ocean_coverage > 0.1:
        return "🌊 Water World"
    elif temp_c > 100:
        return "🔥 Scorched Hell"
    elif temp_c > 50:
        return "🌋 Runaway Greenhouse"
    else:
        return "🌍 Temperate"

def create_metric_cards(state: PlanetaryState):
    """Create metric display cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    temp_c = state.surface_temperature - 273.15
    pressure_bar = state.surface_pressure / 1e5
    o2_percent = state.atmosphere.get('O2', 0) / max(state.surface_pressure, 1) * 100
    co2_ppm = state.atmosphere.get('CO2', 0) / max(state.surface_pressure, 1) * 1e6
    
    with col1:
        st.metric(
            "🌡️ Temperature",
            f"{temp_c:.1f}°C",
            delta=f"{temp_c - 15:.1f}°C from ideal" if abs(temp_c - 15) > 0.1 else "Optimal!",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "💨 Pressure",
            f"{pressure_bar:.3f} bar",
            delta=f"{pressure_bar - 1.0:.3f} from Earth" if abs(pressure_bar - 1.0) > 0.01 else "Earth-like!",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "🌬️ Oxygen",
            f"{o2_percent:.2f}%",
            delta=f"{o2_percent - 21:.2f}% from Earth" if abs(o2_percent - 21) > 0.1 else "Breathable!",
            delta_color="normal" if o2_percent < 21 else "inverse"
        )
    
    with col4:
        st.metric(
            "💧 Ocean Coverage",
            f"{state.ocean_coverage * 100:.1f}%",
            delta=f"{state.ocean_coverage * 100 - 70:.1f}% from Earth",
            delta_color="normal" if state.ocean_coverage < 0.7 else "inverse"
        )

def create_timeline_plot(sim: TerraformingSimulation):
    """Create interactive timeline plot"""
    
    # Extract data
    times = [s.time_years for s in sim.history.states]
    temps = [(s.surface_temperature - 273.15) for s in sim.history.states]
    pressures = [s.surface_pressure / 1e5 for s in sim.history.states]
    oceans = [s.ocean_coverage * 100 for s in sim.history.states]
    o2_levels = [s.atmosphere.get('O2', 0) / max(s.surface_pressure, 1) * 100 
                 for s in sim.history.states]
    
    # Get habitability scores
    hab_times = []
    hab_scores = []
    for state in sim.history.states:
        hab_assessment = HabitabilityIndex().calculate(state)
        hab_times.append(state.time_years)
        hab_scores.append(hab_assessment['total_score'])
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Surface Temperature', 'Atmospheric Pressure',
            'Ocean Coverage', 'Oxygen Concentration',
            'Habitability Score', 'Biomass Growth'
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": True}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Temperature
    fig.add_trace(
        go.Scatter(x=times, y=temps, mode='lines', name='Temperature',
                   line=dict(color='#ef4444', width=3),
                   fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)'),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="blue", opacity=0.5,
                  annotation_text="Freezing", row=1, col=1)
    fig.add_hline(y=15, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="Earth avg", row=1, col=1)
    
    # Pressure
    fig.add_trace(
        go.Scatter(x=times, y=pressures, mode='lines', name='Pressure',
                   line=dict(color='#3b82f6', width=3),
                   fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'),
        row=1, col=2
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="Earth pressure", row=1, col=2)
    
    # Ocean coverage
    fig.add_trace(
        go.Scatter(x=times, y=oceans, mode='lines', name='Ocean',
                   line=dict(color='#06b6d4', width=3),
                   fill='tozeroy', fillcolor='rgba(6, 182, 212, 0.1)'),
        row=2, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="blue", opacity=0.5,
                  annotation_text="Earth oceans", row=2, col=1)
    
    # O2 levels
    fig.add_trace(
        go.Scatter(x=times, y=o2_levels, mode='lines', name='O₂',
                   line=dict(color='#f59e0b', width=3),
                   fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.1)'),
        row=2, col=2
    )
    fig.add_hline(y=21, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="Earth O₂", row=2, col=2)
    fig.add_hline(y=10, line_dash="dash", line_color="red", opacity=0.5,
                  annotation_text="Min breathable", row=2, col=2)
    
    # Habitability score
    fig.add_trace(
        go.Scatter(x=hab_times, y=hab_scores, mode='lines', name='Habitability',
                   line=dict(color='#8b5cf6', width=3),
                   fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.1)'),
        row=3, col=1
    )
    fig.add_hline(y=80, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="Highly habitable", row=3, col=1)
    fig.add_hline(y=60, line_dash="dash", line_color="orange", opacity=0.5,
                  annotation_text="Habitable", row=3, col=1)
    
    # Biomass (log scale)
    biomass_values = [max(s.biomass, 1) for s in sim.history.states]
    fig.add_trace(
        go.Scatter(x=times, y=biomass_values, mode='lines', name='Biomass',
                   line=dict(color='#10b981', width=3)),
        row=3, col=2
    )
    
    # Update axes
    fig.update_xaxes(title_text="Time (years)", row=3, col=1)
    fig.update_xaxes(title_text="Time (years)", row=3, col=2)
    
    fig.update_yaxes(title_text="°C", row=1, col=1)
    fig.update_yaxes(title_text="bar", row=1, col=2)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_yaxes(title_text="%", row=2, col=2)
    fig.update_yaxes(title_text="Score (0-100)", row=3, col=1)
    fig.update_yaxes(title_text="kg (log scale)", type="log", row=3, col=2)
    
    # Update layout
    fig.update_layout(
        height=900,
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    # Add event markers
    for event in sim.history.events:
        if event['type'] == 'intervention':
            for i in range(1, 4):
                for j in range(1, 3):
                    fig.add_vline(
                        x=event['time'],
                        line_dash="dot",
                        line_color="purple",
                        opacity=0.3,
                        row=i, col=j
                    )
    
    return fig

def create_current_state_visualization(state: PlanetaryState):
    """Create radial/gauge visualization of current state"""
    
    hab_assessment = HabitabilityIndex().calculate(state)
    component_scores = hab_assessment['component_scores']
    
    fig = go.Figure()
    
    categories = list(component_scores.keys())
    values = list(component_scores.values())
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.3)',
        line=dict(color='rgb(99, 102, 241)', width=3),
        name='Current State'
    ))
    
    # Add ideal state (100 for all)
    fig.add_trace(go.Scatterpolar(
        r=[100] * len(categories),
        theta=categories,
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.1)',
        line=dict(color='rgb(16, 185, 129)', width=2, dash='dash'),
        name='Earth-like Target'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=400,
        title=dict(
            text=f"Habitability Profile<br><sub>Overall Score: {hab_assessment['total_score']:.1f}/100</sub>",
            x=0.5,
            xanchor='center'
        )
    )
    
    return fig

def intervention_control_panel(sim: TerraformingSimulation):
    """Create intervention control panel"""
    
    st.subheader("🛠️ Terraforming Interventions")
    
    # Organize interventions by category
    tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Climate", "💧 Hydrosphere", "🌱 Biosphere", "🧲 Protection"])
    
    with tab1:
        st.markdown("#### Climate Modification")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔆 Deploy Heating Mirrors (+20)", key="heat_mirrors"):
                intervention = DeployOrbitalMirrors(20, 'heating')
                if sim.apply_intervention(intervention):
                    st.success("✅ Orbital mirrors deployed!")
                    st.rerun()
            
            if st.button("🌫️ Release CO₂ (1×10¹⁵ kg)", key="co2_small"):
                intervention = ReleaseGreenhouseGas('CO2', 1e15)
                if sim.apply_intervention(intervention):
                    st.success("✅ CO₂ released!")
                    st.rerun()
            
            if st.button("💨 Release CH₄ (1×10¹⁴ kg)", key="ch4"):
                intervention = ReleaseGreenhouseGas('CH4', 1e14)
                if sim.apply_intervention(intervention):
                    st.success("✅ Methane released!")
                    st.rerun()
        
        with col2:
            if st.button("☀️ Deploy Shading Mirrors (-20)", key="shade_mirrors"):
                intervention = DeployOrbitalMirrors(20, 'shading')
                if sim.apply_intervention(intervention):
                    st.success("✅ Solar shades deployed!")
                    st.rerun()
            
            if st.button("🌫️ Release CO₂ (1×10¹⁶ kg)", key="co2_large"):
                intervention = ReleaseGreenhouseGas('CO2', 1e16)
                if sim.apply_intervention(intervention):
                    st.success("✅ Large CO₂ release!")
                    st.rerun()
            
            if st.button("🧊 Vaporize CO₂ Ice (10%)", key="vaporize_co2"):
                intervention = VaporizeIceCap('CO2', 0.1)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ CO₂ ice vaporized!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    with tab2:
        st.markdown("#### Water Cycle Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💧 Vaporize Water Ice (10%)", key="vaporize_water_10"):
                intervention = VaporizeIceCap('H2O', 0.1)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Water ice vaporized!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
            
            if st.button("🌊 Vaporize Water Ice (30%)", key="vaporize_water_30"):
                intervention = VaporizeIceCap('H2O', 0.3)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Large water release!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    with tab3:
        st.markdown("#### Biological Terraforming")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🦠 Seed Cyanobacteria (1×10⁹ kg)", key="seed_cyano"):
                intervention = SeedMicroorganisms('cyanobacteria', 1e9)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Cyanobacteria seeded!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
            
            if st.button("🌊 Seed Algae (1×10⁹ kg)", key="seed_algae"):
                intervention = SeedMicroorganisms('algae', 1e9)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Algae seeded!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
        
        with col2:
            if st.button("🌿 Seed Cyanobacteria (1×10¹¹ kg)", key="seed_cyano_large"):
                intervention = SeedMicroorganisms('cyanobacteria', 1e11)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Large-scale seeding!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
            
            if st.button("🏭 Build Atmospheric Processors (×10)", key="processors_10"):
                intervention = BuildAtmosphericProcessor(10, 1e12)
                if sim.apply_intervention(intervention):
                    st.success("✅ Processors built!")
                    st.rerun()
    
    with tab4:
        st.markdown("#### Planetary Protection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧲 Activate Magnetic Field (0.5× Earth)", key="mag_05"):
                intervention = ActivateMagneticFieldGenerator(0.5)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Magnetic field activated!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")
        
        with col2:
            if st.button("🧲 Activate Magnetic Field (1.0× Earth)", key="mag_10"):
                intervention = ActivateMagneticFieldGenerator(1.0)
                applicable, msg = intervention.is_applicable(sim.current_state)
                if applicable:
                    if sim.apply_intervention(intervention):
                        st.success("✅ Full magnetic shield active!")
                        st.rerun()
                else:
                    st.error(f"❌ {msg}")

def check_habitability_celebration(hab_score: dict):
    """Check if planet is habitable and show celebration"""
    
    if hab_score['total_score'] >= 60 and not st.session_state.celebration_shown:
        st.balloons()
        st.session_state.celebration_shown = True
        
        st.markdown("""
        <div class="success-banner">
            🎉 CONGRATULATIONS! 🎉<br>
            Your planet is now HABITABLE!<br>
            🌍 Colonization can begin! 🚀
        </div>
        """, unsafe_allow_html=True)
        
        # Play success sound (if browser supports)
        st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)
    
    elif hab_score['total_score'] >= 80 and st.session_state.celebration_shown:
        st.markdown("""
        <div class="success-banner">
            ✨ EARTH-LIKE PARADISE ACHIEVED! ✨<br>
            🌟 Perfect conditions for human life! 🌟
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🌍 ExoTerra</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #64748b;">Alien World Terraforming Simulator</p>', 
                unsafe_allow_html=True)
    
    # ========================================================================
    # SIDEBAR - Planet Selection
    # ========================================================================
    
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/000000/planet.png", width=150)
        st.title("🪐 Planet Selection")
        
        planet_source = st.radio(
            "Choose planet source:",
            ["Real Exoplanet", "Custom Planet"]
        )
        
        if planet_source == "Real Exoplanet":
            planet_names = db.planets['name'].tolist()
            selected_planet = st.selectbox(
                "Select exoplanet:",
                planet_names,
                index=0
            )
            
            # Show planet info
            planet_info = db.get_planet(selected_planet)
            
            with st.expander("📊 Planet Details", expanded=True):
                st.metric("Mass", f"{planet_info['mass']:.2f} M⊕")
                st.metric("Radius", f"{planet_info['radius']:.2f} R⊕")
                st.metric("Distance", f"{planet_info['semi_major_axis']:.3f} AU")
                st.metric("Star Type", f"{planet_info['star_temperature']:.0f} K")
                st.metric("Discovery", f"{planet_info['discovery_year']}")
            
            if st.button("🚀 Initialize Planet", type="primary"):
                with st.spinner("Creating planetary simulation..."):
                    initial_state = create_initial_state_from_exoplanet(selected_planet)
                    if initial_state:
                        st.session_state.simulation = TerraformingSimulation(
                            initial_state, 
                            timestep_years=10.0
                        )
                        st.session_state.planet_initialized = True
                        st.session_state.celebration_shown = False
                        st.success(f"✅ {selected_planet} loaded!")
                        st.rerun()
        
        else:  # Custom Planet
            st.markdown("#### 🛠️ Custom Planet Builder")
            
            with st.form("custom_planet_form"):
                st.markdown("**Planetary Properties**")
                mass = st.slider("Mass (Earth masses)", 0.1, 10.0, 1.0, 0.1)
                radius = st.slider("Radius (Earth radii)", 0.3, 3.0, 1.0, 0.1)
                
                st.markdown("**Orbital Properties**")
                sma = st.slider("Distance from Star (AU)", 0.1, 5.0, 1.0, 0.1)
                star_lum = st.slider("Star Luminosity (Solar)", 0.01, 3.0, 1.0, 0.01)
                star_mass_val = st.slider("Star Mass (Solar)", 0.08, 2.0, 1.0, 0.01)
                
                st.markdown("**Initial Conditions**")
                temp = st.slider("Initial Temperature (K)", 100, 600, 250, 10)
                albedo_val = st.slider("Albedo", 0.05, 0.95, 0.3, 0.05)
                
                st.markdown("**Atmosphere (bar)**")
                n2_p = st.slider("N₂ Pressure", 0.0, 5.0, 0.5, 0.1)
                o2_p = st.slider("O₂ Pressure", 0.0, 2.0, 0.0, 0.1)
                co2_p = st.slider("CO₂ Pressure", 0.0, 2.0, 0.01, 0.01)
                
                st.markdown("**Surface Features**")
                ocean_cov = st.slider("Ocean Coverage (%)", 0, 100, 0, 5) / 100
                ice_cov = st.slider("Ice Coverage (%)", 0, 100, 30, 5) / 100
                
                st.markdown("**Ice Reservoirs (kg)**")
                water_ice = st.number_input("Water Ice", 0, int(1e20), int(1e18), format="%d")
                co2_ice = st.number_input("CO₂ Ice", 0, int(1e18), int(1e15), format="%d")
                
                submit = st.form_submit_button("🚀 Create Custom Planet", type="primary")
                
                if submit:
                    custom_params = {
                        'planet_mass': mass,
                        'planet_radius': radius,
                        'semi_major_axis': sma,
                        'star_luminosity': star_lum,
                        'star_mass': star_mass_val,
                        'initial_temp': temp,
                        'albedo': albedo_val,
                        'n2_pressure': n2_p,
                        'o2_pressure': o2_p,
                        'co2_pressure': co2_p,
                        'ocean_coverage': ocean_cov,
                        'ice_coverage': ice_cov,
                        'water_ice_mass': float(water_ice),
                        'co2_ice_mass': float(co2_ice),
                    }
                    
                    initial_state = create_custom_planet(custom_params)
                    st.session_state.simulation = TerraformingSimulation(
                        initial_state,
                        timestep_years=10.0
                    )
                    st.session_state.planet_initialized = True
                    st.session_state.celebration_shown = False
                    st.success("✅ Custom planet created!")
                    st.rerun()
        
        st.divider()
        
        # Simulation controls
        if st.session_state.planet_initialized:
            st.markdown("#### ⏱️ Simulation Controls")
            
            timestep_options = {
                "1 year": 1,
                "10 years": 10,
                "50 years": 50,
                "100 years": 100,
                "500 years": 500,
            }
            
            selected_timestep = st.select_slider(
                "Time step:",
                options=list(timestep_options.keys()),
                value="10 years"
            )
            
            num_steps = st.number_input(
                "Number of steps:",
                min_value=1,
                max_value=1000,
                value=1,
                step=1
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("▶️ Step", type="primary"):
                    years = timestep_options[selected_timestep]
                    st.session_state.simulation.timestep = years
                    st.session_state.simulation.step(num_steps)
                    st.rerun()
            
            with col2:
                if st.button("⏭️ Fast Forward"):
                    years = timestep_options[selected_timestep]
                    st.session_state.simulation.timestep = years
                    st.session_state.simulation.step(num_steps * 10)
                    st.rerun()
            
            if st.button("🔄 Reset Simulation"):
                st.session_state.planet_initialized = False
                st.session_state.simulation = None
                st.session_state.celebration_shown = False
                st.rerun()
    
    # ========================================================================
    # MAIN CONTENT
    # ========================================================================
    
    if not st.session_state.planet_initialized:
        # Welcome screen
        st.markdown("""
        <div class="info-box">
        <h2>👋 Welcome to ExoTerra!</h2>
        <p>Transform hostile alien worlds into habitable paradises through advanced terraforming.</p>
        
        <h3>🎮 How to Play:</h3>
        <ol>
            <li>Select a real exoplanet or create a custom world from the sidebar</li>
            <li>Click "Initialize Planet" to begin</li>
            <li>Use terraforming interventions to modify the planet</li>
            <li>Watch the simulation evolve over centuries</li>
            <li>Achieve a Habitability Score of 60+ to win!</li>
        </ol>
        
        <h3>🛠️ Available Technologies:</h3>
        <ul>
            <li>🔆 <b>Orbital Mirrors</b> - Adjust stellar flux for heating or cooling</li>
            <li>🌫️ <b>Greenhouse Gases</b> - Warm the planet with CO₂ or CH₄</li>
            <li>💧 <b>Ice Vaporization</b> - Release trapped water and CO₂</li>
            <li>🦠 <b>Biological Seeding</b> - Introduce oxygen-producing organisms</li>
            <li>🧲 <b>Magnetic Shield</b> - Protect atmosphere from stellar wind</li>
            <li>🏭 <b>Atmospheric Processors</b> - Convert CO₂ to breathable O₂</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Show example planets
        st.markdown("### 🌟 Featured Exoplanets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **TRAPPIST-1e**
            - 🌡️ Cold ice world
            - 💧 Potential water
            - ⭐ Red dwarf star
            - 🎯 Promising candidate
            """)
        
        with col2:
            st.markdown("""
            **Proxima Centauri b**
            - 🌍 Earth-sized
            - 📏 Closest exoplanet
            - 🌋 Tidally locked
            - 🎯 Challenging target
            """)
        
        with col3:
            st.markdown("""
            **Kepler-442b**
            - 🌊 Super-Earth
            - ☀️ In habitable zone
            - 🌡️ Moderate temperature
            - 🎯 Easy mode
            """)
    
    else:
        # Active simulation
        sim = st.session_state.simulation
        current_state = sim.current_state
        
        # Status banner
        status_emoji = get_planet_status_emoji(current_state)
        st.markdown(f"### {status_emoji}")
        
        # Time display
        st.markdown(f"**⏱️ Simulation Time:** {current_state.time_years:.1f} years")
        
        # Key metrics
        create_metric_cards(current_state)
        
        # Habitability assessment
        hab_score = sim.get_habitability_score()
        
        # Check for celebration
        check_habitability_celebration(hab_score)
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "📈 Timeline",
            "🛠️ Interventions",
            "📋 Detailed Stats"
        ])
        
        with tab1:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 🎯 Habitability Assessment")
                
                # Score gauge
                score = hab_score['total_score']
                
                if score >= 80:
                    color = "green"
                    status = "🌟 Earth-like"
                elif score >= 60:
                    color = "lightgreen"
                    status = "✅ Habitable"
                elif score >= 40:
                    color = "orange"
                    status = "⚠️ Marginal"
                elif score >= 20:
                    color = "orangered"
                    status = "🔧 Pre-habitable"
                else:
                    color = "red"
                    status = "❌ Uninhabitable"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {color}22, {color}44); border-radius: 15px; margin: 1rem 0;">
                    <h1 style="font-size: 4rem; margin: 0; color: {color};">{score:.1f}</h1>
                    <p style="font-size: 1.5rem; margin: 0;">{status}</p>
                    <p style="color: #666; margin-top: 1rem;">{hab_score['classification']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Component scores
                st.markdown("#### 📊 Component Scores")
                for component, value in hab_score['component_scores'].items():
                    label = component.replace('_', ' ').title()
                    st.progress(value / 100, text=f"{label}: {value:.1f}%")
                
                # Limiting factors
                if hab_score['limiting_factors']:
                    st.markdown("#### ⚠️ Limiting Factors")
                    for factor in hab_score['limiting_factors']:
                        st.warning(f"• {factor.replace('_', ' ').title()}")
                
                # Recommendations
                recommendations = HabitabilityIndex().get_recommendations(
                    current_state, hab_score
                )
                if recommendations:
                    st.markdown("#### 💡 Recommended Actions")
                    for rec in recommendations:
                        st.info(rec)
            
            with col2:
                # Radar chart
                st.plotly_chart(
                    create_current_state_visualization(current_state),
                    use_container_width=True
                )
                
                # Additional info
                st.markdown("#### 🌍 Earth Similarity Index")
                esi = hab_score['earth_similarity_index']
                st.progress(esi / 100, text=f"{esi:.1f}%")
                
                # Infrastructure
                st.markdown("#### 🏗️ Infrastructure")
                st.metric("Orbital Mirrors", current_state.orbital_mirrors)
                st.metric("Atmospheric Processors", current_state.atmospheric_processors)
                st.metric("Magnetic Field", 
                         f"{current_state.magnetic_field_strength:.1f}× Earth" if current_state.has_artificial_magnetosphere else "None")
                
                # Atmospheric escape
                st.markdown("#### 💨 Atmospheric Loss")
                st.metric("Cumulative Loss", f"{current_state.cumulative_atmosphere_lost:.2e} kg")
        
        with tab2:
            st.markdown("#### 📈 Evolution Over Time")
            
            if len(sim.history.states) > 1:
                fig = create_timeline_plot(sim)
                st.plotly_chart(fig, use_container_width=True)
                
                # Event log
                if sim.history.events:
                    st.markdown("#### 📜 Event History")
                    
                    events_df = pd.DataFrame([
                        {
                            'Time (years)': e['time'],
                            'Event': e['description'],
                            'Type': e['type']
                        }
                        for e in sim.history.events
                    ])
                    
                    st.dataframe(events_df, use_container_width=True, hide_index=True)
            else:
                st.info("Run the simulation to see timeline data")
        
        with tab3:
            intervention_control_panel(sim)
        
        with tab4:
            st.markdown("#### 📋 Detailed Planetary Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Physical Properties**")
                st.text(f"Mass: {current_state.planet_mass:.3f} M⊕")
                st.text(f"Radius: {current_state.planet_radius:.3f} R⊕")
                st.text(f"Surface Gravity: {current_state.planet_mass / (current_state.planet_radius**2) * 9.81:.2f} m/s²")
                st.text(f"Density: {current_state.planet_mass / (current_state.planet_radius**3) * 5.51:.2f} g/cm³")
                
                st.markdown("**Orbital Properties**")
                st.text(f"Semi-major Axis: {current_state.semi_major_axis:.4f} AU")
                st.text(f"Stellar Flux: {current_state.stellar_flux:.1f} W/m²")
                st.text(f"Star Luminosity: {current_state.star_luminosity:.4f} L☉")
                
                st.markdown("**Temperature**")
                st.text(f"Surface: {current_state.surface_temperature - 273.15:.1f}°C")
                st.text(f"Equilibrium: {current_state.equilibrium_temperature - 273.15:.1f}°C")
                st.text(f"Greenhouse Effect: {current_state.greenhouse_effect:.1f} K")
                st.text(f"Albedo: {current_state.albedo:.3f}")
            
            with col2:
                st.markdown("**Atmospheric Composition**")
                comp_fractions = current_state.atmospheric_composition_fractions()
                for gas, fraction in comp_fractions.items():
                    ppm = fraction * 1e6
                    percent = fraction * 100
                    if percent > 0.1:
                        st.text(f"{gas}: {percent:.2f}%")
                    else:
                        st.text(f"{gas}: {ppm:.1f} ppm")
                
                st.markdown("**Hydrosphere**")
                st.text(f"Ocean Coverage: {current_state.ocean_coverage * 100:.1f}%")
                st.text(f"Ice Coverage: {current_state.ice_coverage * 100:.1f}%")
                st.text(f"Water Ice Mass: {current_state.water_ice_mass:.2e} kg")
                st.text(f"CO₂ Ice Mass: {current_state.co2_ice_mass:.2e} kg")
                st.text(f"Total Water: {current_state.total_water_mass():.2e} kg")
                
                st.markdown("**Biosphere**")
                st.text(f"Biomass: {current_state.biomass:.2e} kg")
                st.text(f"O₂ Production: {current_state.o2_production_rate:.2e} kg/year")

if __name__ == "__main__":
    main()