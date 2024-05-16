from agent import Agent

# define agents:  ('name', placement: (x,y), 'color', Property, inventory)
R1 = Agent("Robot1", (6, 6), "blue", "gripper", None, "idle")
R2 = Agent("Robot2", (6, 9), "yellow", "mop", None, "idle")

robots = [R1, R2]
