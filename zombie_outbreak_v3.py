from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
import math
import random
import time

# --- Game Configuration ---
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
GRID_LENGTH = 800
player_pos = [0, 0, 0]
player_rot = 0.0
player_speed = 10
player_health = 100
player_jump_v = 0
is_jumping = False
last_time = time.time()
dt = 0.01  
is_first_person = False 
WINDOW_CENTER_X = WINDOW_WIDTH // 2
mouse_x = WINDOW_CENTER_X  
particles = [] 

# --- [NEW] Global Game State ---
game_started = False 
paused = False
game_over = False

# --- Special Powers State ---
powers_list = ["INVISIBILITY", "SHIELD", "LASER"]
selected_power_idx = 0     
active_power = None        
power_timer = 0            
laser_targets = []         

# Combat System
current_weapon = "AK47" 
bullets = [] 
special_charge = 0.0
last_fire_time = 0
fire_rate = 0.2 
power_ups = [] 
last_flash_time = 0

# --- RELOAD VARIABLES ---
weapon_ammo = {"AK47": 20, "SHOTGUN": 5}     
max_ammo = {"AK47": 20, "SHOTGUN": 5}        
is_reloading = False
reload_start_time = 0
RELOAD_DURATION = 1.0  

# Enemy & Wave System
zombies = [] 
wave = 1
kills = 0
boss_shockwave_active = False
boss_shockwave_timer = 0
boss_shockwave_pos = [0, 0, 0]
boss_shockwave_radius = 0
boss_last_cast_time = 0
boss_last_pos = [0, 0]
boss_stuck_timer = 0
boss_escape_sequence = 0 
boss_escape_timer = 0
last_boss_health = 1000  
boss_hit_timer = 0       
intro_timer = 0
is_intro_active = False

# --- Environment & Obstacles ---
obstacles = [
    [200, 200, 50, 100],
    [-300, 400, 60, 120],
    [400, -300, 40, 80],
    [-200, -200, 70, 150]
]

ground_tiles = []
def init_ground():
    spacing = 100 
    for x in range(-GRID_LENGTH, GRID_LENGTH, spacing):
        for y in range(-GRID_LENGTH, GRID_LENGTH, spacing):
            green = random.uniform(0.1, 0.3)
            ground_tiles.append([x, y, green])

init_ground()

# --- [NEW] RESET FUNCTION ---
def reset_game():
    """Resets all game variables to their initial state."""
    global player_pos, player_rot, bullets, zombies, kills, player_health
    global game_over, paused, current_weapon, weapon_ammo, is_reloading
    global wave, particles, power_ups, special_charge, last_fire_time
    global last_time
    global boss_shockwave_active, boss_hit_timer, is_intro_active, intro_timer
    global boss_escape_sequence, boss_stuck_timer, boss_last_cast_time, boss_shockwave_radius
    global boss_last_pos
    global active_power, power_timer, laser_targets # Power-ups reset

    # 1. Reset Player & Combat
    player_pos = [0, 0, 0] 
    player_rot = 0
    bullets = []
    particles = []
    power_ups = []
    kills = 0
    player_health = 100
    current_weapon = "AK47"
    weapon_ammo = {"AK47": 20, "SHOTGUN": 5}
    is_reloading = False
    special_charge = 0
    
    # Reset Power-ups
    active_power = None
    power_timer = 0
    laser_targets = []

    # 2. Reset Wave & Game States
    game_over = False
    paused = False
    wave = 0  # Set to 0. The idle loop sees 'no zombies', increments to 1, and spawns.
    
    # 3. Reset Zombie/Boss Logic
    zombies = []
    boss_shockwave_active = False
    boss_shockwave_radius = 0
    boss_hit_timer = 0
    is_intro_active = False
    intro_timer = 0
    boss_escape_sequence = 0
    boss_stuck_timer = 0
    boss_last_cast_time = 0      
    boss_last_pos = [0, 0]       
    
    # 4. Reset Clock
    last_time = time.time()  

# --- UI & Utilities ---
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

# --- Entity Drawing ---
def draw_player():
    global active_power, is_first_person, current_weapon, player_pos, player_rot
    
    # Check if invisible to handle grayscale logic
    is_inv = (active_power == "INVISIBILITY")
    
    # Internal helper to handle color and saturation
    def apply_color(r, g, b, alpha=1.0):
        if is_inv:
            # Grayscale calculation (Saturation 0)
            avg = (r + g + b) / 3.0
            # Reduced alpha makes the player look "ghostly"
            glColor4f(avg, avg, avg, 0.4) 
        else:
            glColor4f(r, g, b, alpha)

    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_rot, 0, 0, 1)

    # --- SPECIAL POWER: SHIELD (Light Blue Bubble) ---
    if active_power == "SHIELD":
        glPushMatrix()
        glTranslatef(0, 0, 45) # Center bubble on player torso
        apply_color(0.5, 0.8, 1.0, 0.3) 
        gluSphere(gluNewQuadric(), 70, 20, 20)
        apply_color(0.7, 0.9, 1.0, 0.2)
        gluSphere(gluNewQuadric(), 75, 10, 10)
        glPopMatrix()

    if is_first_person:
        view_offset_x = 15 
        view_offset_y = 12
        view_offset_z = 50 
    else:
        view_offset_x = 0
        view_offset_y = 5
        view_offset_z = 50

        # DRAW BODY (Only in 3rd Person)
        apply_color(0.1, 0.4, 0.1)
        glPushMatrix()
        glTranslatef(0, 0, 50)
        glScalef(25, 12, 30)
        glutSolidCube(1)
        glPopMatrix()

        apply_color(0.9, 0.7, 0.6)
        glPushMatrix()
        glTranslatef(0, 0, 75)
        gluSphere(gluNewQuadric(), 12, 16, 16)
        glPopMatrix()

        apply_color(0.1, 0.1, 0.4)
        for side in [-10, 10]:
            glPushMatrix()
            glTranslatef(side, 0, 20)
            glScalef(10, 10, 40)
            glutSolidCube(1)
            glPopMatrix()

    # --- ARMS ---
    apply_color(0.1, 0.4, 0.1)
    glPushMatrix()
    glTranslatef(-18 + view_offset_x, view_offset_y, view_offset_z)
    glScalef(8, 15, 8)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(18 + view_offset_x, view_offset_y, view_offset_z)
    glScalef(8, 15, 8)
    glutSolidCube(1)
    glPopMatrix()

    # --- GUN ---
    apply_color(0.15, 0.15, 0.15) 
    glPushMatrix()
    glTranslatef(view_offset_x, view_offset_y + 5, view_offset_z + 5)
    glRotatef(90, 1, 0, 0) 
    
    if current_weapon == "AK47":
        gluCylinder(gluNewQuadric(), 2.2, 2.2, 60, 12, 1)
        glPushMatrix()
        glTranslatef(0, 3, 50)
        glutSolidCube(2)
        glPopMatrix()
    else: 
        gluCylinder(gluNewQuadric(), 4.5, 3.5, 35, 12, 1)
        
    glPopMatrix()
    glPopMatrix()

def draw_zombie(z):
    glPushMatrix()
    glTranslatef(z[0], z[1], z[2])
    is_boss = (len(z) > 6 and z[6] == "BOSS")
    
    if is_boss:
        glRotatef(z[4], 0, 0, 1)
        arm_lift = 40 if z[5] == "CASTING" else 0
        glow = (math.sin(time.time() * 5) + 1) / 2
        
        glColor3f(0.1, 0.0, 0.1)
        for side in [-15, 15]:
            glPushMatrix()
            glTranslatef(side, 0, 30)
            glScalef(20, 20, 60)
            glutSolidCube(1)
            glPopMatrix()

        glColor3f(0.2, 0.0, 0.3)
        glPushMatrix()
        glTranslatef(0, 10, 80)
        glScalef(60, 40, 50)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.5 + (glow * 0.5), 0.0, 0.5)
        glPushMatrix()
        glTranslatef(0, 30, 85)
        glutSolidSphere(15, 12, 12)
        glPopMatrix()

        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix() 
        glTranslatef(-40, 20, 90)
        glRotatef(-30, 0, 1, 0)
        glScalef(15, 60, 15)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.5, 0.7, 0.5)
        for height in [70, 100]: 
            glPushMatrix()
            glTranslatef(35, 30, height)
            glRotatef(20, 0, 0, 1)
            glScalef(8, 40, 8)
            glutSolidCube(1)
            glPopMatrix()

        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(0, 25, 110)
        glutSolidSphere(18, 10, 10)
        glColor3f(1.0, 0.0, 0.0) 

        for eye in [-7, 7]:
            glPushMatrix()
            glTranslatef(eye, 15, 5)
            glutSolidSphere(3, 5, 5)
            glPopMatrix()
        glPopMatrix()

    else:
        if z[5] == "ATTACK":
            glRotatef(20, 1, 0, 0)
            skin_color = [1.0, 0.2, 0.2]
        else:
            skin_color = [0.5, 0.7, 0.5]

        glColor3f(0.2, 0.15, 0.1)
        for side in [-5, 5]:
            glPushMatrix()
            glTranslatef(side, 0, 15)
            glScalef(6, 6, 25)
            glutSolidCube(1)
            glPopMatrix()

        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, 0, 40)
        glScalef(18, 10, 25)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(skin_color[0], skin_color[1], skin_color[2])
        for side in [-12, 12]:
            glPushMatrix()
            glTranslatef(side, 10, 45)
            glScalef(5, 18, 5)
            glutSolidCube(1)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 60)
        glScalef(1, 1, 1.1)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

    glPopMatrix() 

def draw_player_ui():
    # Using your specific variable names: active_power and special_charge
    global player_health, special_charge, active_power, WINDOW_WIDTH, WINDOW_HEIGHT
    
    # 1. Switch to 2D Projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test so UI stays on top of the 3D world
    glDisable(GL_DEPTH_TEST)

    # --- UI LAYOUT SETTINGS ---
    bar_w, bar_h = 200, 20
    hx, hy = 50, 50         # Health Bar Position
    sx, sy = 50, 90         # Special Bar Position (placed slightly higher)

    # --- DRAW HEALTH BAR ---
    # Dark Background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(hx, hy); glVertex2f(hx + bar_w, hy)
    glVertex2f(hx + bar_w, hy + bar_h); glVertex2f(hx, hy + bar_h)
    glEnd()

    # Health Fill (Green to Red transition)
    hp_ratio = max(0, min(1, player_health / 100.0))
    glColor3f(1.0 - hp_ratio, hp_ratio, 0.2) 
    glBegin(GL_QUADS)
    glVertex2f(hx, hy); glVertex2f(hx + (bar_w * hp_ratio), hy)
    glVertex2f(hx + (bar_w * hp_ratio), hy + bar_h); glVertex2f(hx, hy + bar_h)
    glEnd()

    # --- DRAW SPECIAL METER ---
    # Dark Background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(sx, sy); glVertex2f(sx + bar_w, sy)
    glVertex2f(sx + bar_w, sy + bar_h); glVertex2f(sx, sy + bar_h)
    glEnd()

    # Special Fill
    sp_ratio = max(0, min(1, special_charge / 100.0))
    if sp_ratio >= 1.0:
        glColor3f(1.0, 1.0, 1.0) # White glow when 100% charged
    else:
        glColor3f(0.2, 0.3, 0.9) # blue
        
    glBegin(GL_QUADS)
    glVertex2f(sx, sy); glVertex2f(sx + (bar_w * sp_ratio), sy)
    glVertex2f(sx + (bar_w * sp_ratio), sy + bar_h); glVertex2f(sx, sy + bar_h)
    glEnd()

    # --- WHITE BORDERS (For Polish) ---
    glColor3f(1, 1, 1)
    for x, y in [(hx, hy), (sx, sy)]:
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y); glVertex2f(x + bar_w, y)
        glVertex2f(x + bar_w, y + bar_h); glVertex2f(x, y + bar_h)
        glEnd()

    # --- UI TEXT ---
    draw_text(hx, hy + bar_h + 5, f"HEALTH: {int(player_health)}")
    # Shows your current active_power mode (Shield, Laser, or Invisibility)
    draw_text(sx, sy + bar_h + 5, f"{powers_list[selected_power_idx]} {int(special_charge)}%")

    # Re-enable Depth and Restore Matrices
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_lasers():
    global active_power, laser_targets, player_pos
    if active_power != "LASER" or not laser_targets:
        return

    for target in laser_targets:
        x1, y1, z1 = player_pos[0], player_pos[1], player_pos[2] + 50
        x2, y2, z2 = target[0], target[1], target[2]
        
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        if distance == 0: continue

        angle_z = math.degrees(math.atan2(dy, dx))
        angle_y = -math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

        glPushMatrix()
        glTranslatef(x1, y1, z1)
        glRotatef(angle_z, 0, 0, 1)
        glRotatef(angle_y, 0, 1, 0)
        glTranslatef(distance/2, 0, 0) 

        # --- 1. Outer Red Lasers (Left and Right) ---
        # Increased offset to 3.0 so they don't hide inside the thicker yellow core
        # Increased thickness from 0.5 to 1.5
        glColor3f(1, 0, 0)
        for offset in [-3.0, 3.0]: 
            glPushMatrix()
            glTranslatef(0, offset, 0)
            glScalef(distance, 4.5, 4.5) 
            glutSolidCube(1)
            glPopMatrix()

        # --- 2. Middle Yellow Core ---
        # Increased thickness from 1.2 to 3.5
        glColor3f(1, 1, 0)
        glPushMatrix()
        glScalef(distance, 3.5, 3.5) 
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()

def draw_boss_ui(dt):
    global zombies, last_boss_health, boss_hit_timer

    boss_z = None
    for z in zombies:
        if len(z) > 6 and z[6] == "BOSS":
            boss_z = z
            break
    
    if not boss_z:
        return

    # 1. Calculate HP
    current_hp = float(boss_z[3])
    max_hp = 1000.0
    hp_ratio = max(0.0, min(1.0, current_hp / max_hp))

    # Flash logic
    if current_hp < last_boss_health:
        boss_hit_timer = 0.2
    last_boss_health = current_hp
    if boss_hit_timer > 0: boss_hit_timer -= dt

    # 2. Switch to 2D UI Mode
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # --- THE FIX: Disable Depth Test so UI is ALWAYS on top ---
    glDisable(GL_DEPTH_TEST) 

    x_pos, y_pos = WINDOW_WIDTH - 250, WINDOW_HEIGHT - 60
    bar_w, bar_h = 200, 15

    # 3. Draw Background (Dark Grey)
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x_pos, y_pos)
    glVertex2f(x_pos + bar_w, y_pos)
    glVertex2f(x_pos + bar_w, y_pos + bar_h)
    glVertex2f(x_pos, y_pos + bar_h)
    glEnd()

    # 4. Draw Health Fill (The Green/Red part)
    if hp_ratio > 0:
        fill_w = bar_w * hp_ratio
        # Color transition: Green -> Red
        glColor3f(1.0 - hp_ratio, hp_ratio, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(x_pos, y_pos)
        glVertex2f(x_pos + fill_w, y_pos)
        glVertex2f(x_pos + fill_w, y_pos + bar_h)
        glVertex2f(x_pos, y_pos + bar_h)
        glEnd()

    # 5. Draw Text and Flash Outline
    # Set color to white for text and outline
    flash_color = [1.0, 1.0, 1.0] if boss_hit_timer > 0 else [0.8, 0.8, 0.8]
    glColor3f(flash_color[0], flash_color[1], flash_color[2])
    
    draw_text(x_pos, y_pos + 20, "BOSS ZOMBIE")

    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x_pos, y_pos)
    glVertex2f(x_pos + bar_w, y_pos)
    glVertex2f(x_pos + bar_w, y_pos + bar_h)
    glVertex2f(x_pos, y_pos + bar_h)
    glEnd()

    # 6. Re-enable Depth Test for the rest of the 3D world
    glEnable(GL_DEPTH_TEST) 

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_lasers():
    global active_power, laser_targets, player_pos
    if active_power != "LASER" or not laser_targets:
        return

    for target in laser_targets:
        x1, y1, z1 = player_pos[0], player_pos[1], player_pos[2] + 50
        x2, y2, z2 = target[0], target[1], target[2]
        
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        if distance == 0: continue

        angle_z = math.degrees(math.atan2(dy, dx))
        angle_y = -math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

        glPushMatrix()
        glTranslatef(x1, y1, z1)
        glRotatef(angle_z, 0, 0, 1)
        glRotatef(angle_y, 0, 1, 0)
        glTranslatef(distance/2, 0, 0) 

        glColor3f(1, 0, 0)
        for offset in [-3.0, 3.0]: 
            glPushMatrix()
            glTranslatef(0, offset, 0)
            glScalef(distance, 4.5, 4.5) 
            glutSolidCube(1)
            glPopMatrix()

        glColor3f(1, 1, 0)
        glPushMatrix()
        glScalef(distance, 3.5, 3.5) 
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()

def spawn_particles(x, y, z, count=8, size=2.0):
    for _ in range(count):
        vx = random.uniform(-4, 4) 
        vy = random.uniform(-4, 4)
        vz = random.uniform(3, 7) 
        particles.append([x, y, z, vx, vy, vz, 1.0, size])

def update_particles(dt):
    global particles
    for p in particles[:]:
        p[0] += p[3] 
        p[1] += p[4] 
        p[2] += p[5] 
        p[5] -= 15 * dt 
        p[6] -= dt * 1.5 
        
        if p[2] < 0: 
            p[2] = 0
            p[3], p[4] = 0, 0 
            
        if p[6] <= 0:
            particles.remove(p)

def draw_particles():
    for p in particles:
        glPushMatrix()
        glTranslatef(p[0], p[1], p[2])
        glColor3f(p[6], 0, 0) 
        p_size = p[7] 
        glutSolidCube(p_size)
        glPopMatrix()

def draw_shockwave():
    if not boss_shockwave_active: return
    
    glPushMatrix()
    glTranslatef(boss_shockwave_pos[0], boss_shockwave_pos[1], 2)
    
    glColor3f(0.6, 0.0, 0.8) 
    glLineWidth(5)
    glBegin(GL_LINE_LOOP)
    for i in range(36):
        angle = math.radians(i * 10)
        r = boss_shockwave_radius + (random.randint(-5, 5))
        glVertex3f(math.cos(angle) * r, math.sin(angle) * r, 0)
    glEnd()
    
    glColor4f(0.4, 0.0, 0.6, 0.5)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0) 
    for i in range(37):
        angle = math.radians(i * 10)
        glVertex3f(math.cos(angle) * (boss_shockwave_radius-10), 
                   math.sin(angle) * (boss_shockwave_radius-10), 0)
    glEnd()
    glPopMatrix()

def draw_muzzle_flash():
    global last_flash_time
    if time.time() - last_flash_time > 0.04: return

    glPushMatrix()
    view_offset_x = 12 if is_first_person else 0
    view_offset_z = 45 if is_first_person else 55 
    
    glTranslatef(player_pos[0], player_pos[1], player_pos[2] + view_offset_z + 5)
    glRotatef(player_rot, 0, 0, 1)
    
    dist_to_tip = 70 if current_weapon == "AK47" else 45
    glTranslatef(view_offset_x, dist_to_tip, 0)
    
    glColor3f(1.0, 0.5, 0.0)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()

def draw_boss_ui(dt):
    global zombies, last_boss_health, boss_hit_timer, WINDOW_WIDTH, WINDOW_HEIGHT

    # 1. Find the Boss Zombie in the list
    boss_z = None
    for z in zombies:
        if len(z) > 6 and z[6] == "BOSS":
            boss_z = z
            break
    
    if not boss_z:
        return

    # 2. Calculate HP Ratio
    # In your code, z[3] is the health (initialized to 1000 for BOSS)
    current_hp = float(boss_z[3])
    max_hp = 1000.0
    hp_ratio = max(0.0, min(1.0, current_hp / max_hp))

    # Flash logic for when the boss takes damage
    if current_hp < last_boss_health:
        boss_hit_timer = 0.2
    last_boss_health = current_hp
    if boss_hit_timer > 0: 
        boss_hit_timer -= dt

    # 3. Switch to 2D UI Mode
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Disable Depth Test to ensure it draws over 3D objects
    glDisable(GL_DEPTH_TEST) 

    # Position: Top Right
    x_pos, y_pos = WINDOW_WIDTH - 250, WINDOW_HEIGHT - 60
    bar_w, bar_h = 200, 15

    # 4. Draw Background (Dark Grey)
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x_pos, y_pos)
    glVertex2f(x_pos + bar_w, y_pos)
    glVertex2f(x_pos + bar_w, y_pos + bar_h)
    glVertex2f(x_pos, y_pos + bar_h)
    glEnd()

    # 5. Draw Health Fill (Red/Yellow transition)
    if hp_ratio > 0:
        fill_w = bar_w * hp_ratio
        # Changes color from Green (High HP) to Red (Low HP)
        glColor3f(1.0 - hp_ratio, hp_ratio, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(x_pos, y_pos)
        glVertex2f(x_pos + fill_w, y_pos)
        glVertex2f(x_pos + fill_w, y_pos + bar_h)
        glVertex2f(x_pos, y_pos + bar_h)
        glEnd()

    # 6. Draw Text and White Outline
    # Outline flashes white when hit
    if boss_hit_timer > 0:
        glColor3f(1.0, 1.0, 1.0)
    else:
        glColor3f(0.7, 0.7, 0.7)
    
    draw_text(x_pos, y_pos + 20, "BOSS ZOMBIE")

    glBegin(GL_LINE_LOOP)
    glVertex2f(x_pos, y_pos)
    glVertex2f(x_pos + bar_w, y_pos)
    glVertex2f(x_pos + bar_w, y_pos + bar_h)
    glVertex2f(x_pos, y_pos + bar_h)
    glEnd()

    # 7. Restore State
    glEnable(GL_DEPTH_TEST) 
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_deadzone_markers():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glLineWidth(2)
    glBegin(GL_LINES)
    glColor3f(0.5, 0.5, 0.5) 
    glVertex2f(300, 0)
    glVertex2f(300, WINDOW_HEIGHT)
    glVertex2f(700, 0)
    glVertex2f(700, WINDOW_HEIGHT)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_floor():
    glColor3f(0.2, 0.2, 0.2) 
    glBegin(GL_QUADS)
    glVertex3f(-3000, -3000, -1)
    glVertex3f(3000, -3000, -1)
    glVertex3f(3000, 3000, -1)
    glVertex3f(-3000, 3000, -1)
    glEnd()

def draw_environment():
    for tile in ground_tiles:
        glColor3f(0.05, tile[2], 0.05)
        glBegin(GL_QUADS)
        size = 100
        glVertex3f(tile[0], tile[1], 0)
        glVertex3f(tile[0] + size, tile[1], 0)
        glVertex3f(tile[0] + size, tile[1] + size, 0)
        glVertex3f(tile[0], tile[1] + size, 0)
        glEnd()

    for obs in obstacles:
        glPushMatrix()
        glTranslatef(obs[0], obs[1], obs[3]/2)
        glScalef(obs[2]/30, obs[2]/30, obs[3]/30)
        glColor3f(0.4, 0.4, 0.4)
        glutSolidCube(30)
        glPopMatrix()

def draw_start_screen():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    glColor3f(1.0, 0.0, 0.0) 
    title_text = "ZOMBIE OUTBREAK"
    base_x, base_y = 360, 550
    
    for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
        glRasterPos2f(base_x + offset[0], base_y + offset[1])
        for ch in title_text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    glColor3f(1, 1, 1)
    glRasterPos2f(base_x, base_y)
    for ch in title_text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

    glColor3f(0.0, 0.6, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(400, 300) 
    glVertex2f(600, 300)
    glVertex2f(600, 380)
    glVertex2f(400, 380)
    glEnd()

    glColor3f(1, 1, 1)
    text = "START GAME"
    glRasterPos2f(425, 332) 
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --- Collision Logic ---
def check_collision(nx, ny, radius):
    if abs(nx) > GRID_LENGTH - 20 or abs(ny) > GRID_LENGTH - 20:
        return True
    for obs in obstacles:
        ox, oy, osize = obs[0], obs[1], obs[2]
        if (nx + radius > ox - osize/2 and nx - radius < ox + osize/2 and
            ny + radius > oy - osize/2 and ny - radius < oy + osize/2):
            return True
    return False

# --- Game Logic ---
def spawn_wave():
    global wave, intro_timer, is_intro_active
    if wave > 0 and wave % 2 == 0:
        zombies.append([700, 700, 0, 1000, 0.8, "IDLE", "BOSS"])
        is_intro_active = True
        intro_timer = 3.0 
        count = 3 
    else:
        count = 4 + (wave * 2)

    speed = 1.0 + (wave * 0.1)
    for _ in range(count):
        side = random.choice(['N', 'S', 'E', 'W'])
        if side == 'N': z_pos = [random.randint(-700, 700), 700, 0]
        else: z_pos = [random.randint(-700, 700), -700, 0]
        zombies.append([z_pos[0], z_pos[1], 0, 50, speed, "IDLE", "NORMAL"])

def fire_bullet():
    global last_fire_time, last_flash_time, bullets, special_charge, is_reloading, reload_start_time
    
    # Reload check
    if weapon_ammo[current_weapon] <= 0:
        if not is_reloading:
            is_reloading = True
            reload_start_time = time.time()
        return

    last_flash_time = time.time() 
    weapon_ammo[current_weapon] -= 1

    rad = math.radians(player_rot + 90)
    dist = 70 
    spawn_x = player_pos[0] + math.cos(rad) * dist
    spawn_y = player_pos[1] + math.sin(rad) * dist
    spawn_z = player_pos[2] + 55 
    
    vx = math.cos(rad) * 25
    vy = math.sin(rad) * 25
    
    if current_weapon == "AK47":
        bullets.append([spawn_x, spawn_y, spawn_z, vx, vy, 15, 1000, 0, False])
    else: 
        for angle in [-15, 0, 15]:
            s_rad = math.radians(player_rot + 90 + angle)
            bullets.append([spawn_x, spawn_y, spawn_z, math.cos(s_rad)*22, math.sin(s_rad)*22, 30, 350, 0, False])
    
def idle():
    # --- [NEW] Start Screen Check ---
    if not game_started:
        glutPostRedisplay()
        return
    
    global player_pos, player_rot, mouse_x, player_jump_v, is_jumping, bullets, zombies, dt, particles
    global player_health, kills, wave, game_over, last_time, special_charge, power_ups
    global boss_shockwave_active, boss_shockwave_radius, boss_last_cast_time, boss_shockwave_pos
    global boss_last_pos, boss_stuck_timer, boss_escape_sequence, boss_escape_timer
    global is_intro_active, intro_timer
    global active_power, power_timer, laser_targets
    global is_reloading, reload_start_time, max_ammo, weapon_ammo

    if paused or game_over:
        glutPostRedisplay()
        return

    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    if dt > 0.1: dt = 0.1 

    # --- Reload Logic ---
    if is_reloading:
        if time.time() - reload_start_time >= RELOAD_DURATION:
            is_reloading = False
            weapon_ammo[current_weapon] = max_ammo[current_weapon]

    update_particles(dt)
    
    if active_power:
        power_timer -= dt
        if power_timer <= 0:
            active_power = None
            laser_targets = []

    if is_intro_active:
        intro_timer -= dt
        if intro_timer <= 0:
            is_intro_active = False
        glutPostRedisplay()
        return 

    diff_x = mouse_x - WINDOW_CENTER_X
    if abs(diff_x) > 200:
        speed_multiplier = diff_x / 1700 
        player_rot -= speed_multiplier * (150 * dt)

    if is_jumping:
        player_pos[2] += player_jump_v * (dt * 60) 
        player_jump_v -= 40 * dt
        if player_pos[2] <= 0:
            player_pos[2] = 0
            is_jumping = False

    for b in bullets[:]:
        b[0] += b[3] * (dt * 60)
        b[1] += b[4] * (dt * 60)
        b[7] += math.sqrt((b[3]*(dt*60))**2 + (b[4]*(dt*60))**2)
        if check_collision(b[0], b[1], 5) or b[7] > b[6]:
            if b in bullets: bullets.remove(b)

    if not zombies: 
        wave += 1
        spawn_wave()

    if boss_shockwave_active:
        boss_shockwave_radius += 350 * dt
        if boss_shockwave_radius > 700:
            boss_shockwave_active = False
        
        dx_wave = player_pos[0] - boss_shockwave_pos[0]
        dy_wave = player_pos[1] - boss_shockwave_pos[1]
        dist_wave = math.sqrt(dx_wave**2 + dy_wave**2)
        
        if abs(dist_wave - boss_shockwave_radius) < 50:
            if active_power != "SHIELD" and active_power != "INVISIBILITY":
                player_health -= 60 * dt
            
            if dist_wave > 0:
                kx, ky = (dx_wave / dist_wave) * 15, (dy_wave / dist_wave) * 15
                if not check_collision(player_pos[0] + kx, player_pos[1] + ky, 15):
                    player_pos[0] += kx
                    player_pos[1] += ky

    laser_targets = [] 
    for z in zombies[:]:
        is_boss = (len(z) > 6 and z[6] == "BOSS")
        hitbox_size = 130 if is_boss else 45
        dx = player_pos[0] - z[0]
        dy = player_pos[1] - z[1]
        dist = math.sqrt(dx**2 + dy**2)
        
        if active_power == "INVISIBILITY":
            z[5] = "IDLE"
        else:
            if is_boss:
                z[4] = math.degrees(math.atan2(dy, dx)) - 90 
                if dist < 600 and not boss_shockwave_active and (current_time - boss_last_cast_time > 8):
                    boss_shockwave_active = True
                    boss_shockwave_radius = 0
                    boss_shockwave_pos = [z[0], z[1], 0]
                    boss_last_cast_time = current_time
                    z[5] = "CASTING"
                
                elif dist < 130:
                    z[5] = "ATTACK"
                    if active_power != "SHIELD":
                         player_health -= 50 * dt

                else: 
                    z[5] = "CHASE"
                    move_speed = 2.4
                    dist_moved = math.sqrt((z[0] - boss_last_pos[0])**2 + (z[1] - boss_last_pos[1])**2)
                    boss_last_pos = [z[0], z[1]]
                    
                    if dist_moved < 0.1: boss_stuck_timer += dt
                    else: boss_stuck_timer = 0

                    if boss_stuck_timer > 2.0 and boss_escape_sequence == 0:
                        boss_escape_sequence = 1
                        boss_escape_timer = current_time

                    if boss_escape_sequence > 0:
                        elapsed_escape = current_time - boss_escape_timer
                        if elapsed_escape < 1.0:
                            z[0] -= math.cos(math.atan2(dy, dx)) * move_speed * (dt * 60)
                            z[1] -= math.sin(math.atan2(dy, dx)) * move_speed * (dt * 60)
                        elif elapsed_escape < 2.0:
                            side_angle = math.atan2(dy, dx) + (math.pi / 2)
                            z[0] += math.cos(side_angle) * move_speed * (dt * 60)
                            z[1] += math.sin(side_angle) * move_speed * (dt * 60)
                        else:
                            boss_escape_sequence = 0
                            boss_stuck_timer = 0
                    else:
                        vx = math.cos(math.atan2(dy, dx)) * move_speed * (dt * 60)
                        vy = math.sin(math.atan2(dy, dx)) * move_speed * (dt * 60)
                        if not check_collision(z[0] + vx, z[1] + vy, 100):
                            z[0] += vx
                            z[1] += vy
            else:
                if dist < hitbox_size: 
                    z[5] = "ATTACK"
                    if active_power != "SHIELD":
                        player_health -= 20 * dt
                elif dist < 900:
                    z[5] = "CHASE"
                    step_x = (dx/dist) * z[4] * (dt * 60)
                    step_y = (dy/dist) * z[4] * (dt * 60)
                    if not check_collision(z[0] + step_x, z[1] + step_y, hitbox_size/2):
                        z[0] += step_x
                        z[1] += step_y
                else:
                    z[5] = "IDLE"

        if active_power == "LASER" and dist < 350:
            z[3] -= 50 * dt 
            laser_targets.append([z[0], z[1], z[2] + (80 if is_boss else 40)])

        for b in bullets[:]:
            if math.sqrt((z[0]-b[0])**2 + (z[1]-b[1])**2) < hitbox_size:
                damage = 15 * (2.5 if b[8] else 1.0)
                z[3] -= damage 
                special_charge = min(100, special_charge + (2 if is_boss else 5))
                if b in bullets: bullets.remove(b)
                
        if z[3] <= 0:
            if is_boss:
                spawn_particles(z[0], z[1], 50, 40, 10.0)
                kills += 10
            else:
                spawn_particles(z[0], z[1], 40, 12, 4.0)
            
            if is_boss or random.random() < 0.2:
                power_ups.append([z[0], z[1], 10, "HEALTH"])
            if z in zombies: zombies.remove(z)
            kills += 1

    for p in power_ups[:]:
        if math.sqrt((player_pos[0]-p[0])**2 + (player_pos[1]-p[1])**2) < 50:
            player_health = min(100, player_health + 30)
            power_ups.remove(p)

    if player_health <= 0:
        game_over = True
        
    glutPostRedisplay()

def keyboardListener(key, x, y):
    global player_pos, player_rot, is_jumping, player_jump_v, current_weapon, is_first_person
    global selected_power_idx, active_power, power_timer, special_charge, is_reloading, reload_start_time
    global paused, game_over

    # --- [NEW] Pause Toggle ---
    if key == b'\x1b':  
        if not game_over:
            paused = not paused
        return 

    if paused or game_over:
        return

    # Trigger selected power (Q)
    if key == b'q':
        if special_charge >= 100 and active_power is None:
            active_power = powers_list[selected_power_idx]
            special_charge = 0
            if active_power == "LASER": power_timer = 10.0
            else: power_timer = 10.0 
        else:
            fire_bullet()

    rad_forward = math.radians(player_rot + 90)
    rad_strafe = math.radians(player_rot)
    nx, ny = player_pos[0], player_pos[1]
    
    if key == b'w':
        nx += math.cos(rad_forward) * player_speed
        ny += math.sin(rad_forward) * player_speed
    if key == b's':
        nx -= math.cos(rad_forward) * player_speed
        ny -= math.sin(rad_forward) * player_speed
    if key == b'd':
        nx += math.cos(rad_strafe) * player_speed
        ny += math.sin(rad_strafe) * player_speed
    if key == b'a':
        nx -= math.cos(rad_strafe) * player_speed
        ny -= math.sin(rad_strafe) * player_speed
    
    if not check_collision(nx, ny, 15):
        player_pos[0], player_pos[1] = nx, ny

    if key == b'c': is_first_person = not is_first_person
    if key == b' ': 
        if not is_jumping:
            is_jumping = True; player_jump_v = 15
    if key == b't':
        selected_power_idx = (selected_power_idx + 1) % len(powers_list)
    if key == b'f':
        current_weapon = "SHOTGUN" if current_weapon == "AK47" else "AK47"
        is_reloading = False 
    if key == b'r':
        if not is_reloading and weapon_ammo[current_weapon] < max_ammo[current_weapon]:
            is_reloading = True
            reload_start_time = time.time()

def mouseListener(button, state, x, y):
    global mouse_x, paused, game_over, game_started
    global active_power, bullets, player_pos, player_rot    

    click_x = x
    click_y = 800 - y

    # --- [NEW] START SCREEN CLICK ---
    if not game_started:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if 400 <= click_x <= 600 and 280 <= click_y <= 450:
                print("Game Started!")
                game_started = True
                spawn_wave()
                glutPostRedisplay()
        return

    # --- [NEW] GAME OVER RESTART CLICK ---
    if game_over:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if 400 <= click_x <= 600 and 100 <= click_y <= 300:
                print("Restarting Game...") 
                reset_game()
                glutPostRedisplay()
        return # Block other input if Game Over

    if paused:
        return

    if state == GLUT_DOWN:
        if button == GLUT_RIGHT_BUTTON:
            mouse_x = x
            
        elif button == GLUT_LEFT_BUTTON:
            if active_power == "INVISIBILITY":
                pass
            else:
                fire_bullet()

def mouse_motion(x, y):
    global mouse_x
    mouse_x = x

def showScreen():
    global is_intro_active, intro_timer, dt, game_started
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glLoadIdentity()
    
    gluPerspective(90, 1.25, 0.1, 3000)
    cam_rad = math.radians(player_rot + 90)

    # --- 1. Camera Logic ---
    if is_intro_active:
        boss_z = next((z for z in zombies if len(z) > 6 and z[6] == "BOSS"), None)
        if boss_z:
            gluLookAt(player_pos[0], player_pos[1] - 300, 250, 
                      boss_z[0], boss_z[1], 100, 
                      0, 0, 1)
        else:
            gluLookAt(player_pos[0], player_pos[1] - 250, 180, player_pos[0], player_pos[1], 60, 0, 0, 1)
    else:
        if is_first_person:
            eye_z = player_pos[2] + 75 
            look_x = player_pos[0] + math.cos(cam_rad) * 100
            look_y = player_pos[1] + math.sin(cam_rad) * 100
            gluLookAt(player_pos[0], player_pos[1], eye_z, 
                      look_x, look_y, eye_z, 0, 0, 1)
        else:
            cx = player_pos[0] - math.cos(cam_rad) * 250
            cy = player_pos[1] - math.sin(cam_rad) * 250
            gluLookAt(cx, cy, 180, player_pos[0], player_pos[1], 60, 0, 0, 1)

    # --- [NEW] START SCREEN RENDER ---
    if not game_started:
        draw_floor() 
        draw_start_screen()
        glutSwapBuffers()
        return

    # --- 2. 3D World Rendering ---
    draw_deadzone_markers()
    
    boss_exists = any(len(z) > 6 and z[6] == "BOSS" for z in zombies)
    if boss_exists:
        glColor3f(0.6, 0.2, 0.2) 
    else:
        glColor3f(1.0, 1.0, 1.0) 
        
    draw_environment()
    
    glColor3f(1, 1, 1)
    draw_shockwave()
    draw_player()
    draw_lasers()
    draw_particles() 
    draw_muzzle_flash()

    for z in zombies: 
        draw_zombie(z)
    
    for b in bullets:
        glPushMatrix()
        glTranslatef(b[0], b[1], b[2])
        if b[8]: glColor3f(1, 0, 1)
        else: glColor3f(1, 1, 0)
        glutSolidSphere(6, 8, 8)
        glPopMatrix()

    for p in power_ups:
        glPushMatrix()
        glTranslatef(p[0], p[1], p[2])
        glColor3f(0, 1, 0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

    # --- 3. 2D UI Section (FIXED LAYERING) ---
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST) # CRITICAL for UI visibility

    # WARNINGS
    if is_intro_active:
        glColor3f(1, 0, 0) 
        draw_text(WINDOW_WIDTH//2 - 180, WINDOW_HEIGHT//2 + 50, "WARNING: BOSS ZOMBIE HAS BEEN SUMMONED")
        glColor3f(1, 1, 1)

    # HUD
    selection_text = f"Selected: {powers_list[selected_power_idx]}"
    draw_text(10, 710, selection_text)
    if active_power:
        glColor3f(0, 1, 1) 
        draw_text(WINDOW_WIDTH//2 - 50, 710, f"ACTIVE: {active_power} ({int(power_timer)}s)")
        glColor3f(1, 1, 1)
    
    ammo_display = f"{weapon_ammo[current_weapon]}/{max_ammo[current_weapon]}"
    if is_reloading:
        ammo_display = "RELOADING..."
        glColor3f(1, 1, 0)
        draw_text(WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2, "RELOADING")
        glColor3f(1, 1, 1)

    draw_text(10, 770, f"Health: {int(player_health)} | Weapon: {current_weapon} | Ammo: {ammo_display} | View: {'1st' if is_first_person else '3rd'}")
    draw_text(10, 740, f"Wave: {wave} | Kills: {kills} | Special: {int(special_charge)}%")
    draw_boss_ui(dt)
    draw_player_ui()

    # --- [NEW] PAUSE MENU ---
    if paused and not game_over:
        glColor3f(1, 1, 0) 
        draw_text(420, 500, "GAME PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(400, 460, "Press ESC to Resume", GLUT_BITMAP_HELVETICA_18)

    # --- [NEW] GAME OVER SCREEN ---
    if game_over:
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glDisable(GL_FOG)
        glDisable(GL_CULL_FACE)
        glDisable(GL_ALPHA_TEST)

        glColor3f(1.0, 0.0, 0.0) 
        base_x = WINDOW_WIDTH//2 - 90
        base_y = WINDOW_HEIGHT//2 + 50
        
        offsets = [(-1,-1), (-1,1), (1,-1), (1,1), (0,0)]
        for dx, dy in offsets:
            glRasterPos2f(base_x + dx, base_y + dy)
            for ch in "GAME OVER":
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

        glColor4f(1.0, 1.0, 1.0, 1.0) 
        msg1 = "You have been infected"
        glRasterPos2f(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2)
        for ch in msg1: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        msg2 = f"Number of Zombies killed: {kills}"
        glRasterPos2f(WINDOW_WIDTH//2 - 110, WINDOW_HEIGHT//2 - 30)
        for ch in msg2: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

        glColor3f(0.0, 0.5, 0.0) 
        glBegin(GL_QUADS)
        glVertex2f(400, 120)  
        glVertex2f(600, 120)  
        glVertex2f(600, 180)  
        glVertex2f(400, 180)  
        glEnd()

        glColor4f(1.0, 1.0, 1.0, 1.0) 
        glRasterPos3f(455, 140, 0) 
        for ch in "RESTART":
             glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Zombie Outbreak 3D")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle) 
    glutMainLoop()

if __name__ == "__main__":
    main()