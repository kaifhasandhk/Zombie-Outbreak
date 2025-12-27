from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
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
dt = 0.01  # Initialize with a small default value
is_first_person = False # Toggle for view
WINDOW_CENTER_X = WINDOW_WIDTH // 2
mouse_x = WINDOW_CENTER_X  # Initialize at center so player starts still
particles = [] # [x, y, z, vx, vy, vz, life]

# Combat System
current_weapon = "AK47" 
bullets = [] 
special_charge = 0.0
last_fire_time = 0
fire_rate = 0.2 
power_ups = [] # [x, y, z, type]
last_flash_time = 0

# Enemy & Wave System
zombies = [] 
wave = 1
kills = 0
game_over = False
boss_shockwave_active = False
boss_shockwave_timer = 0
boss_shockwave_pos = [0, 0, 0]
boss_shockwave_radius = 0
boss_last_cast_time = 0
boss_last_pos = [0, 0]
boss_stuck_timer = 0
boss_escape_sequence = 0 # 0: Normal, 1: Back, 2: Right, 3: Forward
boss_escape_timer = 0
last_boss_health = 1000  # Must match boss spawn health
boss_hit_timer = 0       # Controls the flashing effect
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

# --- UI & Utilities ---
def draw_text(x, y, text):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --- Entity Drawing ---
def draw_player():
    global is_first_person, current_weapon
    
    glPushMatrix()
    # Position and rotate the whole character
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_rot, 0, 0, 1)

    # --- 1. First-Person vs Third-Person Logic ---
    # When in 1st person, we hide the head and torso so they don't block the camera.
    # We also shift the arms/gun to the right side of the screen.
    
    if is_first_person:
        # Shift gun to the right and down to clear the center of the screen
        view_offset_x = 15 
        view_offset_y = 12
        view_offset_z = 50 
    else:
        # Standard centered third-person positions
        view_offset_x = 0
        view_offset_y = 5
        view_offset_z = 50

        # DRAW BODY (Only in 3rd Person)
        # Torso
        glColor3f(0.1, 0.4, 0.1)
        glPushMatrix()
        glTranslatef(0, 0, 50)
        glScalef(25, 12, 30)
        glutSolidCube(1)
        glPopMatrix()

        # Head
        glColor3f(0.9, 0.7, 0.6)
        glPushMatrix()
        glTranslatef(0, 0, 75)
        glutSolidSphere(12, 16, 16)
        glPopMatrix()

        # Legs
        glColor3f(0.1, 0.1, 0.4)
        for side in [-10, 10]:
            glPushMatrix()
            glTranslatef(side, 0, 20)
            glScalef(10, 10, 40)
            glutSolidCube(1)
            glPopMatrix()

    # --- 2. ALWAYS DRAW ARMS (Viewmodel) ---
    glColor3f(0.1, 0.4, 0.1)
    # Left Arm (Support)
    glPushMatrix()
    glTranslatef(-18 + view_offset_x, view_offset_y, view_offset_z)
    glScalef(8, 15, 8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Right Arm (Trigger)
    glPushMatrix()
    glTranslatef(18 + view_offset_x, view_offset_y, view_offset_z)
    glScalef(8, 15, 8)
    glutSolidCube(1)
    glPopMatrix()

    # --- 3. THE GUN ---
    glColor3f(0.15, 0.15, 0.15) # Gun Metal Grey
    glPushMatrix()
    # Position gun relative to the arms
    glTranslatef(view_offset_x, view_offset_y + 5, view_offset_z + 5)
    
    # Rotate 90 deg around X-axis to point forward (Y-axis)
    glRotatef(90, 1, 0, 0) 
    
    if current_weapon == "AK47":
        # Barrel
        gluCylinder(gluNewQuadric(), 2.2, 2.2, 60, 12, 1)
        # Simple Iron Sights / Detail
        glPushMatrix()
        glTranslatef(0, 3, 50)
        glutSolidCube(2)
        glPopMatrix()
    else: # Shotgun
        # Shorter, wider barrel for the shotgun
        gluCylinder(gluNewQuadric(), 4.5, 3.5, 35, 12, 1)
    glPopMatrix()
    glPopMatrix()


def draw_zombie(z):
    glPushMatrix()
    glTranslatef(z[0], z[1], z[2])
    is_boss = (len(z) > 6 and z[6] == "BOSS")
    
    if is_boss:
        glRotatef(z[4], 0, 0, 1) # Use the calculated angle from z[4]
        # SLAM ANIMATION: Raise arm if casting
        arm_lift = 40 if z[5] == "CASTING" else 0
        glow = (math.sin(time.time() * 5) + 1) / 2
        # 1. Lower Body
        glColor3f(0.1, 0.0, 0.1)
        for side in [-15, 15]:
            glPushMatrix()
            glTranslatef(side, 0, 30)
            glScalef(20, 20, 60)
            glutSolidCube(1)
            glPopMatrix()

        # 2. Torso
        glColor3f(0.2, 0.0, 0.3)
        glPushMatrix()
        glTranslatef(0, 10, 80)
        glScalef(60, 40, 50)
        glutSolidCube(1)
        glPopMatrix()

        # 3. Core
        glColor3f(0.5 + (glow * 0.5), 0.0, 0.5)
        glPushMatrix()
        glTranslatef(0, 30, 85)
        glutSolidSphere(15, 12, 12)
        glPopMatrix()

        # 4. Asymmetric Arms
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix() # Left
        glTranslatef(-40, 20, 90)
        glRotatef(-30, 0, 1, 0)
        glScalef(15, 60, 15)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.5, 0.7, 0.5)
        for height in [70, 100]: # Right
            glPushMatrix()
            glTranslatef(35, 30, height)
            glRotatef(20, 0, 0, 1)
            glScalef(8, 40, 8)
            glutSolidCube(1)
            glPopMatrix()

        # 5. Head
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(0, 25, 110)
        glutSolidSphere(18, 10, 10)
        glColor3f(1.0, 0.0, 0.0) # Eyes

        for eye in [-7, 7]:
            glPushMatrix()
            glTranslatef(eye, 15, 5)
            glutSolidSphere(3, 5, 5)
            glPopMatrix()
        glPopMatrix()

    else:
        # --- FIXED: Normal Zombie is now inside this ELSE block ---
        if z[5] == "ATTACK":
            glRotatef(20, 1, 0, 0)
            skin_color = [1.0, 0.2, 0.2]
        else:
            skin_color = [0.5, 0.7, 0.5]

        # 1. Legs
        glColor3f(0.2, 0.15, 0.1)
        for side in [-5, 5]:
            glPushMatrix()
            glTranslatef(side, 0, 15)
            glScalef(6, 6, 25)
            glutSolidCube(1)
            glPopMatrix()

        # 2. Torso
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, 0, 40)
        glScalef(18, 10, 25)
        glutSolidCube(1)
        glPopMatrix()

        # 3. Arms
        glColor3f(skin_color[0], skin_color[1], skin_color[2])
        for side in [-12, 12]:
            glPushMatrix()
            glTranslatef(side, 10, 45)
            glScalef(5, 18, 5)
            glutSolidCube(1)
            glPopMatrix()

        # 4. Head

        glPushMatrix()
        glTranslatef(0, 0, 60)
        glScalef(1, 1, 1.1)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

    glPopMatrix() # Final pop for the whole zombie

def spawn_particles(x, y, z, count=8, size=2.0):
    for _ in range(count):
        # Increased velocity range for a bigger "burst"
        vx = random.uniform(-4, 4) 
        vy = random.uniform(-4, 4)
        vz = random.uniform(3, 7) 
        # Added size (p[7]) to the particle list
        particles.append([x, y, z, vx, vy, vz, 1.0, size])

def update_particles(dt):
    global particles
    for p in particles[:]:
        p[0] += p[3] # Move X
        p[1] += p[4] # Move Y
        p[2] += p[5] # Move Z
        p[5] -= 15 * dt # Gravity pulling Z velocity down
        p[6] -= dt * 1.5 # Life fades out
        
        # If it hits the ground, stop falling
        if p[2] < 0: 
            p[2] = 0
            p[3], p[4] = 0, 0 # Stop sliding
            
        if p[6] <= 0:
            particles.remove(p)

def draw_particles():
    for p in particles:
        glPushMatrix()
        glTranslatef(p[0], p[1], p[2])
        
        # Color fades based on life (p[6])
        # p[6] starts at 1.0 (bright red) and goes to 0.0 (dark)
        glColor3f(p[6], 0, 0) 
        
        # Use the size stored at index 7
        p_size = p[7] 
        
        # IMPORTANT: glutSolidCube handles its own glBegin/glEnd
        # Just call it directly!
        glutSolidCube(p_size)
        
        glPopMatrix()

def draw_shockwave():
    if not boss_shockwave_active: return
    
    glPushMatrix()
    glTranslatef(boss_shockwave_pos[0], boss_shockwave_pos[1], 2)
    
    # Draw a ring of spikes
    glColor3f(0.6, 0.0, 0.8) # Evil Purple
    glLineWidth(5)
    glBegin(GL_LINE_LOOP)
    for i in range(36):
        angle = math.radians(i * 10)
        # Add a little "jaggedness" to the ring
        r = boss_shockwave_radius + (random.randint(-5, 5))
        glVertex3f(math.cos(angle) * r, math.sin(angle) * r, 0)
    glEnd()
    
    # Optional: Inner Glow
    glColor4f(0.4, 0.0, 0.6, 0.5)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0) # Center
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
    # Apply the same offsets as the gun
    view_offset_x = 12 if is_first_person else 0
    view_offset_z = 45 if is_first_person else 55 
    
    glTranslatef(player_pos[0], player_pos[1], player_pos[2] + view_offset_z + 5)
    glRotatef(player_rot, 0, 0, 1)
    
    # Move the flash to the right side (X) and forward (Y)
    dist_to_tip = 70 if current_weapon == "AK47" else 45
    glTranslatef(view_offset_x, dist_to_tip, 0)
    
    glColor3f(1.0, 0.5, 0.0)
    glutSolidSphere(4, 10, 10)
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

def draw_deadzone_markers():
    # Switch to 2D projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glLineWidth(2)
    glBegin(GL_LINES)
    # Use a semi-transparent or subtle color (Grey/White)
    glColor3f(0.5, 0.5, 0.5) 
    
    # Left Boundary (Center - Deadzone)
    glVertex2f(300, 0)
    glVertex2f(300, WINDOW_HEIGHT)
    
    # Right Boundary (Center + Deadzone)
    glVertex2f(700, 0)
    glVertex2f(700, WINDOW_HEIGHT)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

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
    if wave % 2 == 0:
        zombies.append([700, 700, 0, 1000, 0.8, "IDLE", "BOSS"])
        is_intro_active = True
        intro_timer = 3.0 # 3 seconds of intro
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
    global last_fire_time, last_flash_time, bullets, special_charge
    # ... fire rate checks ...
    last_flash_time = time.time() # Ensure this updates global

    rad = math.radians(player_rot + 90)
    dist = 70 # Bullets spawn further out to clear the long barrel
    spawn_x = player_pos[0] + math.cos(rad) * dist
    spawn_y = player_pos[1] + math.sin(rad) * dist
    spawn_z = player_pos[2] + 55 # Gun height in the new model
    

    vx = math.cos(rad) * 25
    vy = math.sin(rad) * 25
    is_sp = special_charge >= 100
    
    if current_weapon == "AK47":
        bullets.append([spawn_x, spawn_y, spawn_z, vx, vy, 15, 1000, 0, is_sp])
    else: 
        # Shotgun pellets
        for angle in [-15, 0, 15]:
            s_rad = math.radians(player_rot + 90 + angle)
            # Increased speed to 22 so they feel punchier
            bullets.append([spawn_x, spawn_y, spawn_z, math.cos(s_rad)*22, math.sin(s_rad)*22, 30, 350, 0, is_sp])
    
    if is_sp: 
        special_charge = 0 # Now works because of the global declaration above

def idle():
    global player_pos, player_rot, mouse_x, player_jump_v, is_jumping, bullets, zombies, dt, particles
    global player_health, kills, wave, game_over, last_time, special_charge, power_ups
    global boss_shockwave_active, boss_shockwave_radius, boss_last_cast_time, boss_shockwave_pos
    global boss_last_pos, boss_stuck_timer, boss_escape_sequence, boss_escape_timer
    global is_intro_active, intro_timer  # Added for Boss Sequence

    if game_over:
        glutPostRedisplay()
        return

    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    if dt > 0.1: dt = 0.1 

    # --- 1. Update Particles ---
    update_particles(dt)

    # --- 2. Handle Boss Intro Sequence ---
    if is_intro_active:
        intro_timer -= dt
        if intro_timer <= 0:
            is_intro_active = False
        glutPostRedisplay()
        return  # Lock movement/logic during intro

    # --- Rotation & Physics ---
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

    # --- Bullets ---
    for b in bullets[:]:
        b[0] += b[3] * (dt * 60)
        b[1] += b[4] * (dt * 60)
        b[7] += math.sqrt((b[3]*(dt*60))**2 + (b[4]*(dt*60))**2)
        if check_collision(b[0], b[1], 5) or b[7] > b[6]:
            if b in bullets: bullets.remove(b)

    if not zombies: 
        wave += 1
        spawn_wave()

    # --- Shockwave Logic ---
    if boss_shockwave_active:
        boss_shockwave_radius += 250 * dt
        if boss_shockwave_radius > 600:
            boss_shockwave_active = False
        
        dx_wave = player_pos[0] - boss_shockwave_pos[0]
        dy_wave = player_pos[1] - boss_shockwave_pos[1]
        dist_wave = math.sqrt(dx_wave**2 + dy_wave**2)
        
        if abs(dist_wave - boss_shockwave_radius) < 40:
            player_health -= 60 * dt
            if dist_wave > 0:
                kx, ky = (dx_wave / dist_wave) * 15, (dy_wave / dist_wave) * 15
                if not check_collision(player_pos[0] + kx, player_pos[1] + ky, 15):
                    player_pos[0] += kx
                    player_pos[1] += ky
                else:
                    player_pos[0] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[0]))
                    player_pos[1] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[1]))

    # --- Zombie AI Loop ---
    for z in zombies[:]:
        is_boss = (len(z) > 6 and z[6] == "BOSS")
        hitbox_size = 120 if is_boss else 45
        dx = player_pos[0] - z[0]
        dy = player_pos[1] - z[1]
        dist = math.sqrt(dx**2 + dy**2)
        
        if is_boss:
            z[4] = math.degrees(math.atan2(dy, dx)) - 90 
            if dist < 600 and not boss_shockwave_active and (current_time - boss_last_cast_time > 7):
                boss_shockwave_active = True
                boss_shockwave_radius = 0
                boss_shockwave_pos = [z[0], z[1], 0]
                boss_last_cast_time = current_time
                z[5] = "ATTACK"

            if z[5] != "ATTACK":
                z[5] = "CHASE"
                move_speed = 2.2
                dist_moved = math.sqrt((z[0] - boss_last_pos[0])**2 + (z[1] - boss_last_pos[1])**2)
                boss_last_pos = [z[0], z[1]]
                
                if dist_moved < 0.1:
                    boss_stuck_timer += dt
                else:
                    boss_stuck_timer = 0

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
                    elif elapsed_escape < 3.0:
                        z[0] += math.cos(math.atan2(dy, dx)) * move_speed * (dt * 60)
                        z[1] += math.sin(math.atan2(dy, dx)) * move_speed * (dt * 60)
                    else:
                        boss_escape_sequence = 0
                        boss_stuck_timer = 0
                else:
                    base_angle = math.atan2(dy, dx)
                    for scan_angle in [0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5]:
                        check_angle = base_angle + scan_angle
                        vx = math.cos(check_angle) * move_speed * (dt * 60)
                        vy = math.sin(check_angle) * move_speed * (dt * 60)
                        if not check_collision(z[0] + vx, z[1] + vy, 40):
                            z[0] += vx
                            z[1] += vy
                            break
            elif current_time - boss_last_cast_time > 1.5:
                z[5] = "CHASE"
        else:
            if dist < hitbox_size: 
                z[5] = "ATTACK"
                player_health -= 15 * dt
            elif dist < 800:
                z[5] = "CHASE"
                step_x = (dx/dist) * z[4] * (dt * 60)
                step_y = (dy/dist) * z[4] * (dt * 60)
                if not check_collision(z[0] + step_x, z[1] + step_y, hitbox_size/2):
                    z[0] += step_x
                    z[1] += step_y
            else:
                z[5] = "IDLE"

        # --- Combat, Damage & Particle Spawning ---
        for b in bullets[:]:
            if math.sqrt((z[0]-b[0])**2 + (z[1]-b[1])**2) < hitbox_size:
                z[3] -= b[5] * (2.5 if b[8] else 1.0)
                special_charge = min(100, special_charge + (2 if is_boss else 5))
                if b in bullets: bullets.remove(b)
                
                # Inside the zombie death check in idle():
                if z[3] <= 0:
                    if is_boss:
                        # 40 particles, size 8.0 (Big chunks)
                        spawn_particles(z[0], z[1], 50, 40, 10.0)
                    else:
                        # 12 particles, size 3.0 (Standard droplets)
                        spawn_particles(z[0], z[1], 40, 12, 4.0)
                    
                    if is_boss or random.random() < 0.2:
                        power_ups.append([z[0], z[1], 10, "HEALTH"])
                    if z in zombies: zombies.remove(z)
                    kills += 1 if not is_boss else 10

    # --- Power-ups & Health ---
    for p in power_ups[:]:
        if math.sqrt((player_pos[0]-p[0])**2 + (player_pos[1]-p[1])**2) < 50:
            player_health = min(100, player_health + 30)
            power_ups.remove(p)

    if player_health <= 0:
        game_over = True
        
    glutPostRedisplay()

def keyboardListener(key, x, y):
    global player_pos, player_rot, is_jumping, player_jump_v, current_weapon, is_first_person
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
    if key == b'f':
        current_weapon = "SHOTGUN" if current_weapon == "AK47" else "AK47"
    if key == b'q': fire_bullet()

def mouseListener(button, state, x, y):
    global mouse_x
    
    if state == GLUT_DOWN:
        # RIGHT CLICK: Sets the rotation target/speed
        if button == GLUT_RIGHT_BUTTON:
            mouse_x = x
            
        # LEFT CLICK: Fires the weapon (does NOT change mouse_x)
        elif button == GLUT_LEFT_BUTTON:
            fire_bullet()

def mouse_motion(x, y):
    global mouse_x
    mouse_x = x

def showScreen():
    global is_intro_active, intro_timer, dt
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glLoadIdentity()
    
    gluPerspective(90, 1.25, 0.1, 3000)
    cam_rad = math.radians(player_rot + 90)

    # --- 1. Camera Logic (Intro vs. Normal) ---
    if is_intro_active:
        # Find the boss to look at it
        boss_z = next((z for z in zombies if len(z) > 6 and z[6] == "BOSS"), None)
        if boss_z:
            # Cinematic Camera: Positioned high up, looking at the boss
            gluLookAt(player_pos[0], player_pos[1] - 300, 250, 
                      boss_z[0], boss_z[1], 100, 
                      0, 0, 1)
        else:
            # Fallback if boss is missing
            gluLookAt(player_pos[0], player_pos[1] - 250, 180, player_pos[0], player_pos[1], 60, 0, 0, 1)
    else:
        # Normal Gameplay Camera
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

    # --- 2. 3D Drawing Section ---
    draw_deadzone_markers()
    
    # Boss Arena Atmosphere: Tint the floor red if a boss exists
    boss_exists = any(len(z) > 6 and z[6] == "BOSS" for z in zombies)
    if boss_exists:
        glColor3f(0.6, 0.2, 0.2) # Dim red tint
    else:
        glColor3f(1.0, 1.0, 1.0) # Normal lighting
        
    draw_environment()
    
    # Reset color for other objects
    glColor3f(1, 1, 1)
    draw_shockwave()
    draw_player()
    draw_particles() # Blood splatter
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

    # --- 3. 2D UI Section ---
    # Draw warnings and standard UI
    if is_intro_active:
        # Warning text in the middle of the screen
        glColor3f(1, 0, 0) # Bright Red
        draw_text(WINDOW_WIDTH//2 - 180, WINDOW_HEIGHT//2 + 50, "WARNING: BOSS ZOMBIE HAS BEEN SUMMONED")
        glColor3f(1, 1, 1)
    
    draw_text(10, 770, f"Health: {int(player_health)} | Weapon: {current_weapon} | View: {'1st' if is_first_person else '3rd'}")
    draw_text(10, 740, f"Wave: {wave} | Kills: {kills} | Special: {int(special_charge)}%")
    
    draw_boss_ui(dt)
    
    if game_over: 
        draw_text(WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2, "GAME OVER")
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Zombie Outbreak 3D")

    glEnable(GL_DEPTH_TEST)
    spawn_wave()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle) 
    glutMainLoop()

if __name__ == "__main__":
    main()