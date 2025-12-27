# Zombie-Outbreak
A high-performance 3D Zombie Survival Arena built from scratch using Python and OpenGL (PyOpenGL). 
This project features a custom game engine architecture including Delta Time synchronization, Finite State Machine (FSM) AI, and momentum-based physics.

🚀 Core Technical Features
Engine & Physics
Delta Time Integration: Frame-rate independent gameplay ensuring consistent movement and physics across all CPUs.
AABB Collision System: Robust Axis-Aligned Bounding Box detection for environment obstacles and arena boundaries.
3D Momentum Physics: Advanced jumping mechanics with gravity constants and velocity-based movement.
Particle Physics System: 3D blood splatter effects with randomized trajectories, gravity, and life-based color interpolation.
Combat & Special Abilities
Dual Weapon System: Switch between an AK47 (high fire rate) and a Shotgun (high spread/damage).
Special Power Suite:
Orbital Laser: A devastating beam that strikes all zombies within a specific radius of the player.
Shield Sphere: A protective energy dome that negates incoming damage from zombie attacks.
Invisibility Cloak: A stealth mechanic that disrupts zombie AI tracking, allowing for strategic repositioning.
Special Attack Meter: Charge-based system that rewards aggressive play with high-powered abilities.
Artificial Intelligence
FSM Zombie AI: Enemies transition between IDLE, CHASE, and ATTACK states based on player proximity.
Elite Boss Mechanics: Bosses feature cinematic intro sequences, "stuck-detection" pathfinding to avoid obstacles, and a purple shockwave "slam" attack.
Dynamic Wave Spawning: Procedural difficulty scaling that increases zombie count, speed, and health per wave.
Visuals & UI
Dual-Perspective Camera: Toggleable First-Person (FPS) and Third-Person (TPS) modes with dynamic viewmodels.
Advanced Rendering: Multi-shaded ground tiles, atmospheric arena tinting during boss fights, and 3D muzzle flashes.
Overlay UI: A screen-space HUD rendered via depth-buffer toggling to ensure health bars and stats remain on top of the 3D scene.
🛠️ Controls
    Key                            Action
W, A, S, D         Movement (Forward, Left, Backward, Right)
   Space                            Jump
     C                 Toggle Camera (1st/3rd Person)
     F                  Switch Weapon (AK47/Shotgun)
Right Click                        Rotate
Left Click                      Fire Weapon
     Q                  Trigger Special Abilities
     T                   Toggle Special Abilities
     
📦 Installation & Requirements
Python 3.x
PyOpenGL: pip install PyOpenGL PyOpenGL_accelerate
Run the game: python zombie_outbreak.py

