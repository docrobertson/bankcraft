import time
import datetime
import sys
import shutil
from IPython.display import clear_output, display
import ipywidgets as widgets
from bankcraft.agent.person import Person

class StatusDashboard:
    """
    A dashboard for displaying the status of a BankCraft model execution.
    
    This dashboard shows:
    - Progress bar
    - Start date and time in the simulation
    - Current date and time in the simulation
    - Anticipated end date and time in the simulation
    - Number of people, businesses, employers
    - Elapsed real-world execution time
    """
    
    def __init__(self, model, total_steps=None, end_date=None):
        """
        Initialize the dashboard.
        
        Args:
            model: The BankCraft model instance
            total_steps (int, optional): Total number of steps to run
            end_date (datetime.datetime, optional): End date of the simulation
        """
        self.model = model
        self.total_steps = total_steps
        self.end_date = end_date
        self.start_time = time.time()
        self.start_step = 0
        self.current_step = 0
        self.simulation_start_time = model.current_time
        self.is_notebook = self._is_notebook()
        
        # Initialize widgets for notebook environment
        if self.is_notebook:
            self.progress_widget = widgets.FloatProgress(
                value=0,
                min=0,
                max=100,
                description='Progress:',
                bar_style='info',
                style={'bar_color': '#1a75ff'},
                orientation='horizontal'
            )
            self.info_widget = widgets.HTML(value="Initializing...")
            self.dashboard = widgets.VBox([self.progress_widget, self.info_widget])
            display(self.dashboard)
    
    def _is_notebook(self):
        """Check if code is running in a Jupyter notebook."""
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                return True  # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                return False  # Terminal running IPython
            else:
                return False  # Other type
        except NameError:
            return False  # Standard Python interpreter
    
    def _get_terminal_width(self):
        """Get the width of the terminal."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def _format_progress_bar(self, percent, width=None):
        """Format a progress bar string."""
        if width is None:
            width = self._get_terminal_width() - 10
        
        filled_length = int(width * percent // 100)
        bar = '█' * filled_length + '-' * (width - filled_length)
        return f"[{bar}] {percent:.1f}%"
    
    def _calculate_progress(self):
        """Calculate the current progress percentage."""
        if self.total_steps:
            steps_done = self.current_step - self.start_step
            return min(100.0, (steps_done / self.total_steps) * 100)
        elif self.end_date:
            total_time = (self.end_date - self.simulation_start_time).total_seconds()
            elapsed_time = (self.model.current_time - self.simulation_start_time).total_seconds()
            return min(100.0, (elapsed_time / total_time) * 100 if total_time > 0 else 100)
        return 0.0
    
    def _format_time(self, seconds):
        """Format time in seconds to a readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def _estimate_end_simulation_time(self):
        """Estimate the end simulation time based on current progress."""
        if self.end_date:
            return self.end_date
            
        progress = self._calculate_progress()
        if progress <= 0:
            return "Unknown"
        
        if self.total_steps:
            # Calculate based on steps
            steps_done = self.current_step - self.start_step
            steps_remaining = self.total_steps - steps_done
            time_per_step = self.model._one_step_time
            return self.model.current_time + (time_per_step * steps_remaining)
        
        return "Unknown"
    
    def update(self, current_step):
        """
        Update the dashboard with the current status.
        
        Args:
            current_step (int): Current step number
        """
        self.current_step = current_step
        progress = self._calculate_progress()
        
        # Count agents - count only active people
        num_people = len([a for a in self.model.agents if isinstance(a, Person) and getattr(a, 'active', True)])
        num_businesses = len([a for a in self.model.agents if hasattr(a, 'type') and a.type == 'business'])
        num_employers = len([a for a in self.model.agents if hasattr(a, 'type') and a.type == 'employer'])
        
        # Calculate times
        elapsed_time = time.time() - self.start_time
        estimated_end_time = self._estimate_end_simulation_time()
        
        if self.is_notebook:
            # Update widgets for notebook environment
            self.progress_widget.value = progress
            
            info_html = f"""
            <div style='font-family: monospace; margin: 10px;'>
                <p><b>Simulation Status:</b></p>
                <p>Simulation start: {self.simulation_start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Current simulation time: {self.model.current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Anticipated simulation end: {estimated_end_time if isinstance(estimated_end_time, str) else estimated_end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Elapsed real-world time: {self._format_time(elapsed_time)}</p>
                <p>Agents: {num_people} people, {num_businesses} businesses, {num_employers} employers</p>
            </div>
            """
            self.info_widget.value = info_html
        else:
            # Clear terminal and print status
            clear_output(wait=True)
            terminal_width = self._get_terminal_width()
            
            print("=" * terminal_width)
            print("BANKCRAFT SIMULATION STATUS")
            print("=" * terminal_width)
            print(f"Progress: {self._format_progress_bar(progress)}")
            print(f"Simulation start: {self.simulation_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Current simulation time: {self.model.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Anticipated simulation end: {estimated_end_time if isinstance(estimated_end_time, str) else estimated_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Elapsed real-world time: {self._format_time(elapsed_time)}")
            print(f"Agents: {num_people} people, {num_businesses} businesses, {num_employers} employers")
            print("=" * terminal_width)
            
            # Flush to ensure output is displayed immediately
            sys.stdout.flush()
    
    def finalize(self):
        """Display the final status when the simulation is complete."""
        # Force progress to 100% for the final update
        self.current_step = self.start_step + (self.total_steps if self.total_steps else 1)
        self.update(self.current_step)
        
        if not self.is_notebook:
            print("\nSimulation completed!") 