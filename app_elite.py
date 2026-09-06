"""
ExoTerra - Professional Planetary Terraforming Simulator
Clean, production-grade UI with 3D planet visualization
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from typing import Dict, Tuple

# Core modules
from planetary_state import PlanetaryState, StateHistory
from simulation_engine import TerraformingSimulation
from interventions import *
from habitability import HabitabilityIndex
from exoplanet_data import ExoplanetDatabase
from constants import *
from advanced_physics import (
    TransmissionSpectroscopy,
    StellarWindModel,
    LatitudinalEnergyBalance,
    EliteSimulationEngine
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="ExoTerra | Planetary Terraforming",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CLEAN, PROFESSIONAL CSS
# ============================================================================

st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global reset and theme */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #0a0e27;
        color: #e2e8f0;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main header */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid #1e293b;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e293b;
    }
    
    /* Clean metric cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    
    .metric-card:hover {
        border-color: #475569;
    }
    
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.25rem;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        color: #64748b;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-optimal {
        background: #065f46;
        color: #6ee7b7;
        border: 1px solid #047857;
    }
    
    .badge-nominal {
        background: #1e40af;
        color: #93c5fd;
        border: 1px solid #1d4ed8;
    }
    
    .badge-warning {
        background: #78350f;
        color: #fbbf24;
        border: 1px solid #92400e;
    }
    
    .badge-critical {
        background: #7f1d1d;
        color: #fca5a5;
        border: 1px solid #991b1b;
    }
    
    /* Buttons */
    .stButton > button {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #f1f5f9;
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #334155;
        border-color: #475569;
    }
    
    .stButton > button:active {
        background: #0f172a;
    }
    
    .stButton > button[kind="primary"] {
        background: #0ea5e9;
        border: 1px solid #0284c7;
        color: #ffffff;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #0284c7;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #1e293b;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: #64748b;
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.75rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #94a3b8;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #f1f5f9;
        border-bottom: 2px solid #0ea5e9;
    }
    
    /* Form elements */
    .stSelectbox label,
    .stSlider label,
    .stNumberInput label {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }
    
    .stSelectbox > div > div,
    .stNumberInput > div > div {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        color: #f1f5f9 !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0ea5e9, #06b6d4);
        border-radius: 4px;
    }
    
    /* Section containers */
    .section-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1rem;
    }
    
    /* Alert boxes */
    .alert {
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        border-left: 3px solid;
    }
    
    .alert-success {
        background: #064e3b;
        border-color: #10b981;
        color: #6ee7b7;
    }
    
    .alert-warning {
        background: #78350f;
        border-color: #f59e0b;
        color: #fbbf24;
    }
    
    .alert-info {
        background: #1e3a8a;
        border-color: #3b82f6;
        color: #93c5fd;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }
    
    /* Hide empty elements */
    .element-container:has(> .stMarkdown > div:empty) {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

def init_session_state():
    defaults = {
        'simulation': None,
        'elite_engine': None,
        'initialized': False,
        'selected_planet': 'TRAPPIST-1e',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# LOAD DATABASE
# ============================================================================

@st.cache_resource
def load_database():
    return ExoplanetDatabase()

db = load_database()

# ============================================================================
# PLANET INITIALIZATION
# ============================================================================

def create_initial_state(planet_name: str) -> PlanetaryState:
    planet = db.get_planet(planet_name)
    if planet is None:
        return None
    
    from planetary_physics import PlanetaryPhysics
    physics = PlanetaryPhysics()
    flux = physics.stellar_flux(planet['star_luminosity'], planet['semi_major_axis'])
    
    # Classify and set initial conditions
    if planet['radius'] < 1.5:
        if flux > 2000:
            atmosphere = {'CO2': 90000.0, 'N2': 3000.0}
            temp = 700.0
            ice_cov = 0.0
        elif flux < 500:
            atmosphere = {'CO2': 600.0, 'N2': 100.0, 'Ar': 20.0}
            temp = 200.0
            ice_cov = 0.8
        else:
            atmosphere = {'N2': 50000.0, 'CO2': 1000.0, 'H2O': 500.0}
            temp = 250.0
            ice_cov = 0.3
    else:
        atmosphere = {'H2': 50000.0, 'He': 30000.0, 'H2O': 10000.0}
        temp = 300.0
        ice_cov = 0.0
    
    total_pressure = sum(atmosphere.values())
    water_ice = planet['mass'] * EARTH_MASS * 0.005
    co2_ice = water_ice * 0.1
    
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
        albedo=0.3,
        ocean_coverage=0.0,
        ice_coverage=ice_cov,
        subsurface_ice_mass=water_ice * 0.5,
        atmospheric_water_vapor=atmosphere.get('H2O', 100.0),
        co2_ice_mass=co2_ice,
        water_ice_mass=water_ice,
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

# ============================================================================
# VISUALIZATION: 3D PLANET
# ============================================================================

@st.cache_data
def create_3d_planet(_state: PlanetaryState) -> go.Figure:
    """Create 3D globe visualization that updates with planet state"""
    
    # Create sphere
    theta = np.linspace(0, 2 * np.pi, 100)
    phi = np.linspace(0, np.pi, 100)
    
    x = np.outer(np.cos(theta), np.sin(phi))
    y = np.outer(np.sin(theta), np.sin(phi))
    z = np.outer(np.ones(100), np.cos(phi))
    
    # Color based on planet state
    temp_c = _state.surface_temperature - 273.15
    
    if temp_c < -50:
        color = '#a5f3fc'  # Frozen - cyan
    elif temp_c < 0:
        color = '#7dd3fc'  # Cold - light blue
    elif temp_c < 50:
        color = '#4ade80'  # Temperate - green
    elif temp_c < 100:
        color = '#fb923c'  # Warm - orange
    else:
        color = '#f87171'  # Hot - red
    
    # Ice caps if present
    if _state.ice_coverage > 0.1:
        ice_color = '#f0f9ff'
    else:
        ice_color = color
    
    fig = go.Figure(data=[go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, ice_color], [0.3, ice_color], [0.7, color], [1, color]],
        showscale=False,
        hoverinfo='skip'
    )])
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='rgba(10, 14, 39, 0)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        paper_bgcolor='rgba(10, 14, 39, 0)',
        plot_bgcolor='rgba(10, 14, 39, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    
    return fig

# ============================================================================
# VISUALIZATION: CHARTS
# ============================================================================

def create_evolution_chart(sim: TerraformingSimulation) -> go.Figure:
    """Simple, clean evolution chart"""
    
    times = [s.time_years for s in sim.history.states]
    temps = [(s.surface_temperature - 273.15) for s in sim.history.states]
    pressures = [s.surface_pressure / 1e5 for s in sim.history.states]
    o2 = [s.atmosphere.get('O2', 0) / max(s.surface_pressure, 1) * 100 
          for s in sim.history.states]
    
    # Habitability
    hab_scores = []
    for state in sim.history.states:
        hab = HabitabilityIndex().calculate(state)
        hab_scores.append(hab['total_score'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=times, y=temps,
        name='Temperature (°C)',
        line=dict(color='#f87171', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=times, y=pressures,
        name='Pressure (bar)',
        line=dict(color='#60a5fa', width=2),
        yaxis='y2'
    ))
    
    fig.add_trace(go.Scatter(
        x=times, y=o2,
        name='O₂ (%)',
        line=dict(color='#34d399', width=2),
        yaxis='y3'
    ))
    
    fig.add_trace(go.Scatter(
        x=times, y=hab_scores,
        name='Habitability',
        line=dict(color='#a78bfa', width=2),
        yaxis='y4'
    ))
    
    fig.update_layout(
        xaxis=dict(title='Time (years)', color='#94a3b8', gridcolor='#1e293b'),
        yaxis=dict(title='Temp (°C)', color='#f87171', gridcolor='#1e293b'),
        yaxis2=dict(title='Pressure', overlaying='y', side='right', color='#60a5fa'),
        yaxis3=dict(overlaying='y', side='right', position=0.85, color='#34d399'),
        yaxis4=dict(overlaying='y', side='right', position=0.92, color='#a78bfa'),
        plot_bgcolor='#0f172a',
        paper_bgcolor='rgba(10, 14, 39, 0)',
        font=dict(family='Inter', color='#e2e8f0'),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(30, 41, 59, 0.8)'),
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_spectrum_chart(wavelengths, depths, technosigs) -> go.Figure:
    """Transmission spectrum visualization"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=wavelengths,
        y=depths,
        mode='lines',
        line=dict(color='#0ea5e9', width=2),
        fill='tozeroy',
        fillcolor='rgba(14, 165, 233, 0.1)',
        name='Spectrum'
    ))
    
    # Mark technosignatures
    if technosigs:
        for gas in technosigs:
            if gas == 'SF6':
                x = 10.5
            elif gas == 'CF4':
                x = 7.8
            else:
                x = 13.0
            
            fig.add_vline(x=x, line_dash="dot", line_color="#fbbf24", 
                         annotation_text=gas, annotation_position="top")
    
    fig.update_layout(
        xaxis=dict(title='Wavelength (μm)', color='#94a3b8', gridcolor='#1e293b'),
        yaxis=dict(title='Transit Depth (ppm)', color='#94a3b8', gridcolor='#1e293b'),
        plot_bgcolor='#0f172a',
        paper_bgcolor='rgba(10, 14, 39, 0)',
        font=dict(family='Inter', color='#e2e8f0'),
        height=300,
        margin=dict(l=60, r=20, t=40, b=60)
    )
    
    return fig

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_metric_card(label: str, value: str, delta: str = None, status: str = "nominal"):
    """Clean metric card"""
    
    status_colors = {
        'optimal': '#10b981',
        'nominal': '#3b82f6',
        'warning': '#f59e0b',
        'critical': '#ef4444'
    }
    
    color = status_colors.get(status, '#64748b')
    
    st.markdown(f"""
    <div class="metric-card" style="border-left: 3px solid {color};">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-delta">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

def get_status_badge(score: float) -> Tuple[str, str]:
    """Get status badge HTML"""
    if score >= 80:
        badge_class = "badge-optimal"
        text = "EARTH-LIKE"
    elif score >= 60:
        badge_class = "badge-nominal"
        text = "HABITABLE"
    elif score >= 40:
        badge_class = "badge-warning"
        text = "MARGINAL"
    else:
        badge_class = "badge-critical"
        text = "HOSTILE"
    
    return f'<span class="status-badge {badge_class}">{text}</span>'

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    
    # ========================================
    # SIDEBAR
    # ========================================
    
    with st.sidebar:
        st.markdown("### Planet Selection")
        
        planets = db.planets['name'].tolist()
        selected = st.selectbox(
            "Choose exoplanet",
            planets,
            index=planets.index(st.session_state.selected_planet) if st.session_state.selected_planet in planets else 0,
            label_visibility="collapsed"
        )
        
        if selected != st.session_state.selected_planet:
            st.session_state.selected_planet = selected
            st.session_state.initialized = False
        
        planet_info = db.get_planet(selected)
        
        # Planet details in clean format
        with st.expander("📊 Planet Data", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mass", f"{planet_info['mass']:.2f} M⊕")
                st.metric("Radius", f"{planet_info['radius']:.2f} R⊕")
            with col2:
                st.metric("Distance", f"{planet_info['semi_major_axis']:.3f} AU")
                st.metric("Gravity", f"{planet_info['gravity']:.1f} m/s²")
        
        with st.expander("⭐ Star Data", expanded=False):
            st.text(f"Type: {planet_info['star_temperature']:.0f} K")
            st.text(f"Luminosity: {planet_info['star_luminosity']:.4f} L☉")
            st.text(f"Discovery: {planet_info['discovery_year']}")
        
        st.markdown("---")
        
        # Initialize button
        if not st.session_state.initialized:
            if st.button("🚀 Initialize Mission", type="primary", use_container_width=True):
                with st.spinner("Initializing..."):
                    initial_state = create_initial_state(selected)
                    
                    if initial_state:
                        st.session_state.simulation = TerraformingSimulation(initial_state, 10.0)
                        st.session_state.elite_engine = EliteSimulationEngine(initial_state)
                        st.session_state.elite_engine.update_advanced_physics()
                        st.session_state.initialized = True
                        st.rerun()
        else:
            # Simulation controls
            st.markdown("### Simulation")
            
            sim = st.session_state.simulation
            
            st.text(f"Time: {sim.current_state.time_years:.0f} years")
            
            timestep = st.select_slider(
                "Step size",
                options=[1, 10, 50, 100, 500],
                value=10,
                format_func=lambda x: f"{x}y"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶ Step", use_container_width=True):
                    sim.timestep = timestep
                    sim.step(1)
                    st.session_state.elite_engine.state = sim.current_state
                    st.session_state.elite_engine.update_advanced_physics()
                    st.rerun()
            
            with col2:
                if st.button("⏩ Fast", use_container_width=True):
                    sim.timestep = timestep
                    sim.step(10)
                    st.session_state.elite_engine.state = sim.current_state
                    st.session_state.elite_engine.update_advanced_physics()
                    st.rerun()
            
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.initialized = False
                st.rerun()
    
    # ========================================
    # MAIN CONTENT
    # ========================================
    
    if not st.session_state.initialized:
        # Welcome screen
        st.markdown('<h1 class="main-header">ExoTerra</h1>', unsafe_allow_html=True)
        st.markdown('<p class="main-subtitle">Planetary Terraforming Simulator</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="alert alert-info">
        <b>Getting Started</b><br>
        Select an exoplanet from the sidebar and click "Initialize Mission" to begin.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="section-container">
            <div class="section-title">TRAPPIST-1e</div>
            <p style="font-size: 0.875rem; color: #94a3b8;">
            Cold ice world with high water content. Medium difficulty.
            </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="section-container">
            <div class="section-title">Proxima Centauri b</div>
            <p style="font-size: 0.875rem; color: #94a3b8;">
            Closest exoplanet. Tidally locked. High difficulty.
            </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="section-container">
            <div class="section-title">Kepler-442b</div>
            <p style="font-size: 0.875rem; color: #94a3b8;">
            Super-Earth in habitable zone. Easy mode.
            </p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Active simulation
        sim = st.session_state.simulation
        elite = st.session_state.elite_engine
        state = sim.current_state
        
        # Header with status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<h1 class="main-header">{st.session_state.selected_planet}</h1>', unsafe_allow_html=True)
        with col2:
            hab = HabitabilityIndex().calculate(state)
            st.markdown(get_status_badge(hab['total_score']), unsafe_allow_html=True)
        
        st.markdown(f'<p class="main-subtitle">Mission Time: {state.time_years:.0f} years</p>', unsafe_allow_html=True)
        
        # Check for success
        if hab['total_score'] >= 60:
            st.markdown("""
            <div class="alert alert-success">
            ✓ Mission Success: Planet is now habitable for human life!
            </div>
            """, unsafe_allow_html=True)
        
        # Main layout: Planet view + Metrics
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 3D Planet visualization
            st.markdown('<div class="section-title">Planet View</div>', unsafe_allow_html=True)
            planet_fig = create_3d_planet(state)
            st.plotly_chart(planet_fig, use_container_width=True, config={'displayModeBar': False})
            
            # Quick stats under planet
            temp_c = state.surface_temperature - 273.15
            pressure_bar = state.surface_pressure / 1e5
            
            st.markdown(f"""
            <div style="text-align: center; margin-top: -1rem;">
                <p style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.25rem;">SURFACE TEMPERATURE</p>
                <p style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0;">{temp_c:.1f}°C</p>
                <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 1rem; margin-bottom: 0.25rem;">ATMOSPHERIC PRESSURE</p>
                <p style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0;">{pressure_bar:.2f} bar</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Key metrics
            st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)
            
            mcol1, mcol2, mcol3 = st.columns(3)
            
            with mcol1:
                o2 = state.atmosphere.get('O2', 0) / max(state.surface_pressure, 1) * 100
                o2_status = "optimal" if 15 <= o2 <= 25 else ("nominal" if 10 <= o2 <= 30 else "warning")
                st.markdown(f"""
                <div class="metric-card" style="border-left: 3px solid {'#10b981' if o2_status == 'optimal' else '#f59e0b'};">
                    <div class="metric-label">OXYGEN</div>
                    <div class="metric-value">{o2:.1f}%</div>
                    <div class="metric-delta">Target: 21%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with mcol2:
                ocean = state.ocean_coverage * 100
                ocean_status = "optimal" if 30 <= ocean <= 70 else "warning"
                st.markdown(f"""
                <div class="metric-card" style="border-left: 3px solid {'#10b981' if ocean_status == 'optimal' else '#f59e0b'};">
                    <div class="metric-label">OCEAN COVERAGE</div>
                    <div class="metric-value">{ocean:.1f}%</div>
                    <div class="metric-delta">Target: 70%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with mcol3:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 3px solid #3b82f6;">
                    <div class="metric-label">HABITABILITY</div>
                    <div class="metric-value">{hab['total_score']:.0f}/100</div>
                    <div class="metric-delta">{hab['classification'].split('(')[0].strip()}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Additional metrics
            mcol1, mcol2, mcol3 = st.columns(3)
            
            with mcol1:
                st.metric("Ice Coverage", f"{state.ice_coverage * 100:.1f}%")
            with mcol2:
                st.metric("Biomass", f"{state.biomass:.2e} kg")
            with mcol3:
                mag = "Active" if state.has_artificial_magnetosphere else "None"
                st.metric("Magnetic Field", mag)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Evolution", "Advanced Physics", "Interventions", "Details"])
        
        with tab1:
            if len(sim.history.states) > 1:
                st.plotly_chart(create_evolution_chart(sim), use_container_width=True)
            else:
                st.info("Run simulation to see evolution data")
        
        with tab2:
            # Transmission spectrum
            if elite.transmission_spectrum:
                st.markdown("#### JWST Transmission Spectrum")
                wavelengths, depths = elite.transmission_spectrum
                spec_fig = create_spectrum_chart(wavelengths, depths, elite.technosignature_detections)
                st.plotly_chart(spec_fig, use_container_width=True)
                
                if elite.technosignature_detections:
                    st.markdown('<div class="alert alert-warning">⚠ Artificial gases detected</div>', unsafe_allow_html=True)
            
            # Latitudinal temperature
            if elite.latitudinal_temps is not None:
                st.markdown("#### Temperature Distribution")
                lats = elite.energy_balance.latitudes
                temps_c = elite.latitudinal_temps - 273.15
                
                lat_fig = go.Figure()
                lat_fig.add_trace(go.Scatter(
                    x=lats, y=temps_c,
                    fill='tozeroy',
                    line=dict(color='#f87171', width=2)
                ))
                lat_fig.add_hline(y=0, line_dash="dash", line_color="#60a5fa")
                lat_fig.update_layout(
                    xaxis=dict(title='Latitude', color='#94a3b8', gridcolor='#1e293b'),
                    yaxis=dict(title='Temperature (°C)', color='#94a3b8', gridcolor='#1e293b'),
                    plot_bgcolor='#0f172a',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#e2e8f0'),
                    height=300,
                    margin=dict(l=60, r=20, t=20, b=60)
                )
                st.plotly_chart(lat_fig, use_container_width=True)
                
                if elite.is_snowball:
                    st.markdown('<div class="alert alert-warning">⚠ Snowball state detected</div>', unsafe_allow_html=True)
        
        with tab3:
            # Intervention buttons organized by category
            st.markdown("#### Climate Control")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("☀ Heat Mirrors", use_container_width=True):
                    sim.apply_intervention(DeployOrbitalMirrors(20, 'heating'))
                    elite.state = sim.current_state
                    elite.update_advanced_physics()
                    st.rerun()
            
            with col2:
                if st.button("🌫 Release CO₂", use_container_width=True):
                    sim.apply_intervention(ReleaseGreenhouseGas('CO2', 1e15))
                    elite.state = sim.current_state
                    elite.update_advanced_physics()
                    st.rerun()
            
            with col3:
                if st.button("❄ Melt Ice Caps", use_container_width=True):
                    intervention = VaporizeIceCap('H2O', 0.2)
                    if intervention.is_applicable(state)[0]:
                        sim.apply_intervention(intervention)
                        elite.state = sim.current_state
                        elite.update_advanced_physics()
                        st.rerun()
            
            st.markdown("#### Biological")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🦠 Seed Bacteria", use_container_width=True):
                    intervention = SeedMicroorganisms('cyanobacteria', 1e10)
                    if intervention.is_applicable(state)[0]:
                        sim.apply_intervention(intervention)
                        elite.state = sim.current_state
                        elite.update_advanced_physics()
                        st.rerun()
            
            with col2:
                if st.button("🏭 Build Processors", use_container_width=True):
                    sim.apply_intervention(BuildAtmosphericProcessor(10, 1e12))
                    elite.state = sim.current_state
                    elite.update_advanced_physics()
                    st.rerun()
            
            with col3:
                if st.button("🧲 Magnetic Shield", use_container_width=True):
                    intervention = ActivateMagneticFieldGenerator(1.0)
                    if intervention.is_applicable(state)[0]:
                        sim.apply_intervention(intervention)
                        elite.state = sim.current_state
                        elite.update_advanced_physics()
                        st.rerun()
        
        with tab4:
            # Detailed atmospheric composition
            st.markdown("#### Atmospheric Composition")
            comp = state.atmospheric_composition_fractions()
            
            comp_data = []
            for gas, fraction in sorted(comp.items(), key=lambda x: x[1], reverse=True):
                ppm = fraction * 1e6
                percent = fraction * 100
                if percent > 0.01:
                    comp_data.append({'Gas': gas, 'Percentage': f'{percent:.2f}%', 'PPM': f'{ppm:.0f}'})
            
            if comp_data:
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
            
            # Physical properties
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Physical Properties")
                st.text(f"Mass: {state.planet_mass:.3f} M⊕")
                st.text(f"Radius: {state.planet_radius:.3f} R⊕")
                st.text(f"Density: {state.planet_mass / (state.planet_radius**3) * 5.51:.2f} g/cm³")
            
            with col2:
                st.markdown("#### Energy Budget")
                st.text(f"Stellar Flux: {state.stellar_flux:.0f} W/m²")
                st.text(f"Albedo: {state.albedo:.2f}")
                st.text(f"Greenhouse: {state.greenhouse_effect:.1f} K")

if __name__ == "__main__":
    main()