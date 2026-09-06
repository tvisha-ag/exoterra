"""
ExoTerra - Main Simulation Engine
Time-stepping simulation with interventions and feedback loops
"""

import numpy as np
from typing import List, Optional, Callable
from planetary_state import PlanetaryState, StateHistory
from interventions import TerraformingIntervention
from feedback_loops import FeedbackProcessor
from habitability import HabitabilityIndex

class TerraformingSimulation:
    """
    Main simulation engine for planetary terraforming
    """
    
    def __init__(self, initial_state: PlanetaryState, 
                 timestep_years: float = 10.0):
        """
        Initialize simulation
        
        Parameters:
        -----------
        initial_state : PlanetaryState
            Starting conditions
        timestep_years : float
            Simulation timestep in years
        """
        self.current_state = initial_state.copy()
        self.timestep = timestep_years
        self.history = StateHistory()
        self.feedback_processor = FeedbackProcessor()
        self.habitability_assessor = HabitabilityIndex()
        
        # Record initial state
        self.history.add_state(self.current_state)
        
        # Callbacks for monitoring
        self.step_callbacks: List[Callable] = []
    
    def step(self, num_steps: int = 1) -> List[PlanetaryState]:
        """
        Advance simulation by specified number of timesteps
        
        Parameters:
        -----------
        num_steps : int
            Number of timesteps to simulate
            
        Returns:
        --------
        list : States at each timestep
        """
        states = []
        
        for _ in range(num_steps):
            # Process feedback loops
            self.current_state = self.feedback_processor.process_all_feedbacks(
                self.current_state,
                self.timestep
            )
            
            # Update time
            self.current_state.time_years += self.timestep
            
            # Record state
            self.history.add_state(self.current_state)
            states.append(self.current_state.copy())
            
            # Execute callbacks
            for callback in self.step_callbacks:
                callback(self.current_state)
        
        return states
    
    def apply_intervention(self, intervention: TerraformingIntervention) -> bool:
        """
        Apply a terraforming intervention
        
        Parameters:
        -----------
        intervention : TerraformingIntervention
            Intervention to apply
            
        Returns:
        --------
        bool : Success status
        """
        # Check if applicable
        applicable, message = intervention.is_applicable(self.current_state)
        
        if not applicable:
            print(f"❌ Cannot apply intervention: {message}")
            return False
        
        # Apply intervention
        self.current_state = intervention.apply(self.current_state)
        
        # Log event
        self.history.add_event(
            self.current_state.time_years,
            'intervention',
            intervention.name,
            {'cost': intervention.cost, 'duration': intervention.duration}
        )
        
        print(f"✅ Applied: {intervention.name}")
        
        # If intervention has duration, advance time
        if intervention.duration > 0:
            # Advance in smaller steps during construction
            construction_steps = int(intervention.duration / self.timestep)
            if construction_steps > 0:
                self.step(construction_steps)
        
        return True
    
    def run_until(self, end_time_years: float, 
                  stop_condition: Optional[Callable[[PlanetaryState], bool]] = None):
        """
        Run simulation until specified time or condition
        
        Parameters:
        -----------
        end_time_years : float
            End time in years
        stop_condition : callable, optional
            Function that returns True when simulation should stop
        """
        while self.current_state.time_years < end_time_years:
            self.step(1)
            
            if stop_condition and stop_condition(self.current_state):
                print(f"Stop condition met at t={self.current_state.time_years:.1f} years")
                break
    
    def get_habitability_score(self) -> dict:
        """Get current habitability assessment"""
        return self.habitability_assessor.calculate(self.current_state)
    
    def get_habitability_history(self) -> tuple:
        """Get habitability score over time"""
        times = []
        scores = []
        
        for state in self.history.states:
            assessment = self.habitability_assessor.calculate(state)
            times.append(state.time_years)
            scores.append(assessment['total_score'])
        
        return np.array(times), np.array(scores)
    
    def add_step_callback(self, callback: Callable):
        """Add a callback function to execute each timestep"""
        self.step_callbacks.append(callback)
    
    def get_summary(self) -> dict:
        """Get comprehensive simulation summary"""
        current_hab = self.get_habitability_score()
        
        return {
            'current_time': self.current_state.time_years,
            'current_state': self.current_state.get_summary(),
            'habitability': current_hab,
            'num_interventions': len([e for e in self.history.events if e['type'] == 'intervention']),
            'total_atmosphere_lost_kg': self.current_state.cumulative_atmosphere_lost,
        }
    
    def print_status(self):
        """Print current status"""
        summary = self.get_summary()
        hab = summary['habitability']
        state_sum = summary['current_state']
        
        print(f"\n{'='*70}")
        print(f"Simulation Status - Year {summary['current_time']:.1f}")
        print(f"{'='*70}")
        print(f"🌡️  Temperature: {state_sum['Temperature (°C)']:.1f}°C")
        print(f"💨 Pressure: {state_sum['Pressure (bar)']:.3f} bar")
        print(f"💧 Ocean Coverage: {state_sum['Ocean coverage (%)']:.1f}%")
        print(f"🧊 Ice Coverage: {state_sum['Ice coverage (%)']:.1f}%")
        print(f"🌬️  O2 Level: {state_sum['O2 level (%)']:.2f}%")
        print(f"🌫️  CO2 Level: {state_sum['CO2 (ppm)']:.1f} ppm")
        print(f"🌱 Biomass: {state_sum['Biomass (kg)']:.2e} kg")
        print(f"\n🏆 Habitability Score: {hab['total_score']:.1f}/100")
        print(f"📊 Classification: {hab['classification']}")
        print(f"🌍 Earth Similarity: {hab['earth_similarity_index']:.1f}%")
        
        if hab['limiting_factors']:
            print(f"\n⚠️  Limiting Factors: {', '.join(hab['limiting_factors'])}")
        
        print(f"{'='*70}\n")