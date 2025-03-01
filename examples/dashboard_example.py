#!/usr/bin/env python
"""
Example script demonstrating the use of the status dashboard in BankCraft.
"""

import datetime
from bankcraft.model import BankCraftModelBuilder

def main():
    # Create a model with some agents
    model = BankCraftModelBuilder.build_model(
        num_people=20,
        initial_money=1000,
        num_banks=2,
        width=20,
        height=20
    )
    
    print("Model created with:")
    print(f"- {len(model.get_people())} people")
    print(f"- {len([a for a in model.agents if hasattr(a, 'type') and a.type == 'employer'])} employers")
    print(f"- {len([a for a in model.agents if hasattr(a, 'type') and a.type == 'business'])} businesses")
    print()
    
    # Example 1: Run for a specific number of steps with dashboard
    print("Example 1: Running for 100 steps with dashboard")
    model.run(steps=100, show_dashboard=True)
    print("Run completed\n")
    
    # Example 2: Run for a specific duration with dashboard
    print("Example 2: Running for 2 days with dashboard")
    model.run(duration="2 days", show_dashboard=True)
    print("Run completed\n")
    
    # Example 3: Run until a specific date with dashboard
    end_date = model.current_time + datetime.timedelta(days=5)
    print(f"Example 3: Running until {end_date} with dashboard")
    model.run_until(end_date=end_date, show_dashboard=True)
    print("Run completed\n")
    
    # Example 4: Run without dashboard
    print("Example 4: Running for 50 steps without dashboard")
    model.run(steps=50, show_dashboard=False)
    print("Run completed without dashboard\n")
    
    # Example 5: Run with custom dashboard update frequency
    print("Example 5: Running for 100 steps with dashboard updating every step")
    model.run(steps=100, show_dashboard=True, dashboard_update_frequency=1)
    print("Run completed\n")

if __name__ == "__main__":
    main() 