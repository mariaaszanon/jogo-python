import math
import random
import pygame
from pygame import Rect

# Game constants
WIDTH = 800
HEIGHT = 600
TITLE = "Calabouço Sombrio"

# Game states
MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"
INSTRUCTIONS = "instructions"

# Initialize game state
game_state = MENU
music_enabled = True
sound_enabled = True
level = 1
score = 0
treasures_collected = 0
treasures_needed = 5
music_initialized = False
background_music_sound = None
show_pause_menu = False

def initialize_music():
    """Initialize background music using sounds system"""
    global music_initialized, background_music_sound
    if not music_initialized and music_enabled:
        try:
            # Try using sounds system instead of music system
            background_music_sound = sounds.background
            background_music_sound.play(-1)  # Loop indefinitely
            music_initialized = True
        except Exception as e:
            # Fallback to music system
            try:
                music.play('background')
                music_initialized = True
            except Exception as e2:
                pass

class AnimatedSprite:
    """Base class for animated sprites with movement and animation"""
    
    def __init__(self, x, y, images, animation_speed=0.2):
        self.x = x
        self.y = y
        self.images = images
        self.animation_speed = animation_speed
        self.animation_timer = 0
        self.current_frame = 0
        self.target_x = x
        self.target_y = y
        self.speed = 50
        self.moving = False
        
    def update(self, dt):
        # Update animation
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.images)
        
        # Update movement with wall collision
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
            else:
                move_distance = self.speed * dt
                new_x = self.x + (dx / distance) * move_distance
                new_y = self.y + (dy / distance) * move_distance
                
                # Check wall collision before moving
                if not point_in_wall(new_x, new_y):
                    self.x = new_x
                    self.y = new_y
                else:
                    # Stop movement if hitting wall
                    self.moving = False
    
    def move_to(self, x, y):
        self.target_x = x
        self.target_y = y
        self.moving = True
    
    def get_rect(self):
        return Rect(self.x - 16, self.y - 16, 32, 32)
    
    def draw(self):
        screen.blit(self.images[self.current_frame], (self.x - 16, self.y - 16))

class Hero(AnimatedSprite):
    """Player character with click-to-move controls"""
    
    def __init__(self, x, y):
        hero_images = ['hero1', 'hero2', 'hero3', 'hero2']
        super().__init__(x, y, hero_images, 0.3)
        self.health = 3
        self.invincible_timer = 0
        
    def update(self, dt):
        super().update(dt)
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
    
    def take_damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 2.0
            if sound_enabled:
                try:
                    sounds.hurt.play()
                except:
                    pass  # Handle missing sound file gracefully
            return True
        return False
    
    def draw(self):
        if self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2:
            return  # Flashing effect when invincible
        super().draw()

class Enemy(AnimatedSprite):
    """Smart enemy that patrols and chases the hero"""
    
    def __init__(self, x, y, waypoints, level):
        enemy_images = ['enemy1', 'enemy2', 'enemy3', 'enemy2']
        super().__init__(x, y, enemy_images, 0.25)
        self.waypoints = waypoints
        self.current_waypoint = 0
        self.patrol_timer = 0
        self.patrol_delay = random.uniform(1.0, 3.0)
        self.speed = random.uniform(25, 45)  # Slower base speed
        
        # More aggressive scaling from level 2 onwards
        if level == 1:
            self.chase_range = 80  # Very small range
            self.chase_speed = 55  # Slow chase
            self.attack_delay = 3.0  # Full 3 second delay
        elif level == 2:
            self.chase_range = 110  # Bigger jump in aggression
            self.chase_speed = 75   # Much faster
            self.attack_delay = 1.5  # Much shorter delay
        else:
            self.chase_range = 100 + (level * 15)  # Grows faster
            self.chase_speed = 70 + (level * 12)   # Faster scaling
            self.attack_delay = max(0.5, 2.0 - (level * 0.4))  # Minimum 0.5s delay
        
        self.is_chasing = False
        self.lost_hero_timer = 0
        self.attack_timer = self.attack_delay
        self.level = level
        
    def update(self, dt, hero_x, hero_y):
        super().update(dt)
        
        # Attack delay timer for early levels
        if self.attack_timer > 0:
            self.attack_timer -= dt
            # Don't chase during attack delay
            if self.attack_timer > 0:
                self.is_chasing = False
                # Continue normal patrol with level-appropriate delays
                if not self.moving:
                    self.patrol_timer += dt
                    if self.patrol_timer >= self.patrol_delay:
                        self.patrol_timer = 0
                        # More aggressive patrol timing from level 2
                        if self.level == 1:
                            self.patrol_delay = random.uniform(1.5, 3.5)  # Slow patrol
                        else:
                            self.patrol_delay = random.uniform(0.8, 2.0)  # Much faster patrol
                        self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
                        next_point = self.waypoints[self.current_waypoint]
                        self.move_to(next_point[0], next_point[1])
                return
        
        # Calculate distance to hero
        dx = hero_x - self.x
        dy = hero_y - self.y
        distance_to_hero = math.sqrt(dx*dx + dy*dy)
        
        # Check if hero is in chase range (only after attack delay)
        if distance_to_hero <= self.chase_range:
            self.is_chasing = True
            self.lost_hero_timer = 0
            # Chase the hero with level-appropriate speed
            old_speed = self.speed
            self.speed = self.chase_speed
            self.move_to(hero_x, hero_y)
            self.speed = old_speed
        else:
            # If was chasing, give some time before returning to patrol
            if self.is_chasing:
                self.lost_hero_timer += dt
                # More persistent chasing from level 2
                give_up_time = 2.0 if self.level == 1 else 1.0  # Less time to escape from level 2+
                if self.lost_hero_timer > give_up_time:
                    self.is_chasing = False
                    self.lost_hero_timer = 0
            
            # Regular patrol behavior when not chasing
            if not self.is_chasing and not self.moving:
                self.patrol_timer += dt
                if self.patrol_timer >= self.patrol_delay:
                    self.patrol_timer = 0
                    # More aggressive patrol timing from level 2
                    if self.level == 1:
                        self.patrol_delay = random.uniform(1.5, 3.5)  # Slow patrol
                    else:
                        self.patrol_delay = random.uniform(0.8, 2.0)  # Much faster patrol
                    self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
                    next_point = self.waypoints[self.current_waypoint]
                    self.move_to(next_point[0], next_point[1])

class Treasure:
    """Collectible treasure"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.float_timer = 0
        self.base_y = y
        
    def update(self, dt):
        self.float_timer += dt * 3
        self.y = self.base_y + math.sin(self.float_timer) * 3
        
    def get_rect(self):
        return Rect(self.x - 12, self.y - 12, 24, 24)
        
    def draw(self):
        if not self.collected:
            screen.blit('treasure', (self.x - 12, self.y - 12))

# Game objects
hero = None
enemies = []
treasures = []
walls = []

def reset_game():
    """Initialize/reset game objects"""
    global hero, enemies, treasures, walls, score, treasures_collected, treasures_needed
    
    enemies.clear()
    treasures.clear()
    walls.clear()
    
    # Create walls around the border
    for x in range(0, WIDTH, 32):
        walls.append(Rect(x, 0, 32, 32))
        walls.append(Rect(x, HEIGHT-32, 32, 32))
    for y in range(32, HEIGHT-32, 32):
        walls.append(Rect(0, y, 32, 32))
        walls.append(Rect(WIDTH-32, y, 32, 32))
    
    # Add some internal walls for complexity
    for i in range(level * 3):
        wall_x = random.randint(2, (WIDTH//32) - 3) * 32
        wall_y = random.randint(2, (HEIGHT//32) - 3) * 32
        walls.append(Rect(wall_x, wall_y, 32, 32))
    
    # Find a safe starting position for the hero
    safe_position_found = False
    attempts = 0
    hero_x, hero_y = 100, 100  # Default position
    
    while not safe_position_found and attempts < 50:
        # Try random positions in the safe zone (avoiding borders)
        hero_x = random.randint(64, WIDTH - 64)
        hero_y = random.randint(64, HEIGHT - 64)
        
        if not point_in_wall(hero_x, hero_y):
            safe_position_found = True
        attempts += 1
    
    # If no safe position found after 50 attempts, use a guaranteed safe spot
    if not safe_position_found:
        hero_x, hero_y = 64, 64  # Top-left safe area
    
    hero = Hero(hero_x, hero_y)
    
    # Create enemies with patrol routes - progressive difficulty
    if level == 1:
        enemy_count = 2  # Very easy start
    elif level == 2:
        enemy_count = 3  # Still manageable
    elif level == 3:
        enemy_count = 4  # Getting harder
    else:
        enemy_count = min(3 + level, 10)  # Normal scaling after level 3
        
    for i in range(enemy_count):
        # Generate random patrol waypoints that cover more area
        waypoints = []
        for j in range(3 + random.randint(0, 2)):  # Fewer waypoints for easier predictability
            wx = random.randint(32, WIDTH - 32)
            wy = random.randint(32, HEIGHT - 32)
            # Avoid placing waypoints in walls
            attempts = 0
            while point_in_wall(wx, wy) and attempts < 10:
                wx = random.randint(32, WIDTH - 32)
                wy = random.randint(32, HEIGHT - 32)
                attempts += 1
            waypoints.append((wx, wy))
        
        start_point = waypoints[0]
        enemy = Enemy(start_point[0], start_point[1], waypoints, level)
        enemies.append(enemy)
    
    # Create treasures
    treasures_needed = 5 + level
    for i in range(treasures_needed):
        tx = random.randint(50, WIDTH - 50)
        ty = random.randint(50, HEIGHT - 50)
        treasures.append(Treasure(tx, ty))
    
    treasures_collected = 0

def point_in_wall(x, y):
    """Check if a point collides with any wall"""
    point_rect = Rect(x - 16, y - 16, 32, 32)
    for wall in walls:
        if point_rect.colliderect(wall):
            return True
    return False

def on_mouse_down(pos):
    """Handle mouse clicks"""
    global game_state, level, show_pause_menu
    
    if game_state == MENU:
        # Menu button areas
        if 300 <= pos[0] <= 500:
            if 180 <= pos[1] <= 220:  # Iniciar Jogo
                game_state = PLAYING
                reset_game()
                if music_enabled and not music_initialized:
                    initialize_music()
            elif 240 <= pos[1] <= 280:  # Instruções
                game_state = INSTRUCTIONS
            elif 300 <= pos[1] <= 340:  # Toggle Music
                toggle_music()
            elif 360 <= pos[1] <= 400:  # Toggle Sound
                toggle_sound()
            elif 420 <= pos[1] <= 460:  # Sair
                quit()
                
    elif game_state == INSTRUCTIONS:
        # Qualquer clique volta ao menu
        if 300 <= pos[0] <= 500 and 500 <= pos[1] <= 540:  # Botão Voltar
            game_state = MENU
        
    elif game_state == PLAYING:
        # Verificar se clicou no botão de pausa (canto superior direito)
        if 750 <= pos[0] <= 790 and 10 <= pos[1] <= 50:
            show_pause_menu = not show_pause_menu
        # Verificar se clicou em botões do menu de pausa
        elif show_pause_menu:
            if 300 <= pos[0] <= 500:
                if 250 <= pos[1] <= 290:  # Continuar
                    show_pause_menu = False
                elif 310 <= pos[1] <= 350:  # Menu Principal
                    game_state = MENU
                    show_pause_menu = False
                elif 370 <= pos[1] <= 410:  # Sair
                    quit()
        else:
            # Move hero to clicked position if not in wall
            if not point_in_wall(pos[0], pos[1]):
                hero.move_to(pos[0], pos[1])
                if sound_enabled:
                    try:
                        sounds.move.play()
                    except:
                        pass  # Handle missing sound file gracefully
                
    elif game_state == GAME_OVER:
        # Restart on click
        if 250 <= pos[0] <= 550 and 400 <= pos[1] <= 450:
            game_state = MENU
            level = 1

def toggle_music():
    """Toggle background music"""
    global music_enabled, music_initialized, background_music_sound
    music_enabled = not music_enabled
    
    if music_enabled:
        try:
            # Try sounds system first
            if background_music_sound is None:
                background_music_sound = sounds.background
            background_music_sound.play(-1)  # Loop indefinitely
            music_initialized = True
        except Exception as e:
            # Fallback to music system
            try:
                music.play('background')
                music_initialized = True
            except Exception as e2:
                music_initialized = False
    else:
        try:
            # Stop both systems
            if background_music_sound:
                background_music_sound.stop()
            music.stop()
            music_initialized = False
        except Exception as e:
            pass

def toggle_sound():
    """Toggle sound effects"""
    global sound_enabled
    sound_enabled = not sound_enabled

def update(dt):
    """Main game update loop"""
    global game_state, level, score, treasures_collected
    
    if game_state == PLAYING:
        # Update hero
        hero.update(dt)
        
        # Update enemies with hero position for smart chasing
        for enemy in enemies:
            enemy.update(dt, hero.x, hero.y)
            
            # Check enemy-hero collision
            if enemy.get_rect().colliderect(hero.get_rect()):
                if hero.take_damage():
                        if hero.health <= 0:
                            game_state = GAME_OVER
                            try:
                                music.stop()
                            except:
                                pass
                            if sound_enabled:
                                try:
                                    sounds.game_over.play()
                                except:
                                    pass        # Update treasures
        for treasure in treasures:
            treasure.update(dt)
            
            # Check treasure collection
            if not treasure.collected and treasure.get_rect().colliderect(hero.get_rect()):
                treasure.collected = True
                treasures_collected += 1
                score += 100 * level
                if sound_enabled:
                    try:
                        sounds.treasure.play()
                    except:
                        pass
                
                # Check level completion
                if treasures_collected >= treasures_needed:
                    level += 1
                    reset_game()
                    if sound_enabled:
                        try:
                            sounds.level_up.play()
                        except:
                            pass

def draw():
    """Main drawing function"""
    screen.clear()
    
    if game_state == MENU:
        draw_menu()
    elif game_state == INSTRUCTIONS:
        draw_instructions()
    elif game_state == PLAYING:
        draw_game()
    elif game_state == GAME_OVER:
        draw_game_over()

def draw_menu():
    """Draw main menu"""
    # Initialize music when menu is first displayed
    initialize_music()
    
    screen.fill((20, 20, 40))
    
    # Title
    screen.draw.text("CALABOUCO SOMBRIO", center=(WIDTH//2, 100), 
                    fontsize=42, color="gold")
    
    # Menu buttons
    button_color = (60, 60, 100)
    hover_color = (80, 80, 120)
    text_color = "white"
    
    # Iniciar Jogo
    screen.draw.filled_rect(Rect(300, 180, 200, 40), button_color)
    screen.draw.text("INICIAR JOGO", center=(400, 200), fontsize=20, color=text_color)
    
    # Instruções
    screen.draw.filled_rect(Rect(300, 240, 200, 40), button_color)
    screen.draw.text("INSTRUCOES", center=(400, 260), fontsize=20, color=text_color)
    
    # Music toggle
    music_text = f"MUSICA: {'LIGADA' if music_enabled else 'DESLIGADA'}"
    screen.draw.filled_rect(Rect(300, 300, 200, 40), button_color)
    screen.draw.text(music_text, center=(400, 320), fontsize=18, color=text_color)
    
    # Sound toggle
    sound_text = f"SONS: {'LIGADOS' if sound_enabled else 'DESLIGADOS'}"
    screen.draw.filled_rect(Rect(300, 360, 200, 40), button_color)
    screen.draw.text(sound_text, center=(400, 380), fontsize=18, color=text_color)
    
    # Sair
    screen.draw.filled_rect(Rect(300, 420, 200, 40), button_color)
    screen.draw.text("SAIR", center=(400, 440), fontsize=20, color=text_color)
    
    # Instructions at bottom
    screen.draw.text("Clique para mover o heroi e colete tesouros!", 
                    center=(WIDTH//2, 480), fontsize=16, color="cyan")
    screen.draw.text("Evite os inimigos vermelhos que patrulham!", 
                    center=(WIDTH//2, 500), fontsize=16, color="orange")
    screen.draw.text("Use ESC para pausar durante o jogo", 
                    center=(WIDTH//2, 520), fontsize=14, color="lightgray")

def draw_game():
    """Draw game screen"""
    screen.fill((40, 60, 40))
    
    # Draw walls
    for wall in walls:
        screen.draw.filled_rect(wall, (100, 100, 100))
    
    # Draw treasures
    for treasure in treasures:
        treasure.draw()
    
    # Draw enemies
    for enemy in enemies:
        enemy.draw()
    
    # Draw hero
    hero.draw()
    
    # Draw UI em português
    screen.draw.text(f"Nivel: {level}", topleft=(10, 10), fontsize=22, color="white")
    screen.draw.text(f"Pontos: {score}", topleft=(10, 35), fontsize=22, color="white")
    screen.draw.text(f"Vidas: {hero.health}", topleft=(10, 60), fontsize=22, color="red")
    screen.draw.text(f"Tesouros: {treasures_collected}/{treasures_needed}", 
                    topleft=(10, 85), fontsize=22, color="gold")
    
    # Botão de pausa (canto superior direito)
    pause_color = (80, 80, 120) if show_pause_menu else (60, 60, 100)
    screen.draw.filled_rect(Rect(750, 10, 40, 40), pause_color)
    screen.draw.text("II", center=(770, 30), fontsize=20, color="white")
    
    # Menu de pausa
    if show_pause_menu:
        # Overlay escuro
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Menu de pausa
        menu_rect = Rect(250, 200, 300, 250)
        screen.draw.filled_rect(menu_rect, (40, 40, 60))
        screen.draw.rect(menu_rect, "white")
        
        screen.draw.text("JOGO PAUSADO", center=(400, 230), fontsize=24, color="white")
        
        # Botões do menu de pausa
        button_color = (60, 60, 100)
        
        # Continuar
        screen.draw.filled_rect(Rect(300, 250, 200, 40), button_color)
        screen.draw.text("CONTINUAR", center=(400, 270), fontsize=18, color="white")
        
        # Menu Principal
        screen.draw.filled_rect(Rect(300, 310, 200, 40), button_color)
        screen.draw.text("MENU PRINCIPAL", center=(400, 330), fontsize=18, color="white")
        
        # Sair
        screen.draw.filled_rect(Rect(300, 370, 200, 40), button_color)
        screen.draw.text("SAIR DO JOGO", center=(400, 390), fontsize=18, color="white")

def draw_game_over():
    """Draw game over screen"""
    screen.fill((40, 20, 20))
    
    screen.draw.text("FIM DE JOGO", center=(WIDTH//2, 200), 
                    fontsize=48, color="red")
    screen.draw.text(f"Pontuacao Final: {score}", center=(WIDTH//2, 280), 
                    fontsize=28, color="white")
    screen.draw.text(f"Nivel Alcancado: {level}", center=(WIDTH//2, 320), 
                    fontsize=28, color="white")
    
    # Return to menu button
    screen.draw.filled_rect(Rect(250, 400, 300, 50), (60, 60, 100))
    screen.draw.text("VOLTAR AO MENU", center=(400, 425), 
                    fontsize=22, color="white")

def draw_instructions():
    """Draw instructions screen"""
    screen.fill((30, 30, 50))
    
    # Title
    screen.draw.text("COMO JOGAR", center=(WIDTH//2, 50), 
                    fontsize=36, color="gold")
    
    # Instructions text
    instructions = [
        "OBJETIVO:",
        " Colete todos os tesouros dourados para passar de nivel",
        " Evite os inimigos vermelhos que patrulham o mapa",
        "",
        "CONTROLES:",
        " Clique com o mouse para mover seu heroi (quadrado azul)",
        " ESC ou botao de pausa para pausar o jogo",
        "",
        "MECANICAS:",
        " Voce tem 3 vidas - pisca quando invencivel",
        " Inimigos se tornam mais agressivos nos niveis altos",
        " Paredes cinzas bloqueiam o movimento",
        "",
        "DICAS:",
        " Observe os padroes de movimento dos inimigos",
        " Use as paredes como protecao",
        " Planeje sua rota antes de se mover",
        "",
        "ESC ou clique VOLTAR para retornar"
    ]
    
    y_start = 100
    for i, line in enumerate(instructions):
        if line.startswith("•"):
            color = "lightblue"
            fontsize = 16
        elif line == "":
            continue
        elif line.endswith(":"):
            color = "yellow"
            fontsize = 20
        else:
            color = "white"
            fontsize = 18
            
        screen.draw.text(line, topleft=(50, y_start + i * 22), 
                        fontsize=fontsize, color=color)
    
    # Botão Voltar
    screen.draw.filled_rect(Rect(300, 500, 200, 40), (60, 60, 100))
    screen.draw.text("VOLTAR", center=(400, 520), fontsize=20, color="white")

def on_key_down(key):
    """Handle key presses"""
    global show_pause_menu, game_state
    
    if game_state == PLAYING and key == keys.ESCAPE:
        show_pause_menu = not show_pause_menu
    elif game_state == INSTRUCTIONS and key == keys.ESCAPE:
        game_state = MENU