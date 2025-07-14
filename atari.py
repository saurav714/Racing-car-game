import pygame as pg
import sys
import random
import os

# Initialize pygame
pg.init()
pg.mixer.init()

# Game settings
WIDTH, HEIGHT = 800, 600
FPS = 60
BASE_SPEED = 5

# Colors
BLACK = (10, 10, 10)
WHITE = (240, 240, 240)
GRAY = (100, 100, 100)
RED = (230, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 120, 220)
YELLOW = (240, 220, 50)
CYAN = (50, 220, 220)
BUTTON_COLOR = (50, 180, 80)
ROAD_COLOR = (40, 40, 45)
SHOULDER_COLOR = (70, 70, 75)

# Music setup
def load_music():
    music_folder = "music"
    try:
        if not os.path.exists(music_folder):
            os.makedirs(music_folder)
            print(f"Created '{music_folder}' folder. Please add your music files there.")
            return None
        
        music_files = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav', '.ogg'))]
        
        if not music_files:
            print(f"No music files found in '{music_folder}' folder.")
            return None
            
        selected_music = os.path.join(music_folder, random.choice(music_files))
        pg.mixer.music.load(selected_music)
        pg.mixer.music.set_volume(0.5)
        return selected_music
    except Exception as e:
        print(f"Error loading music: {e}")
        return None

# Enhanced car class with better collision bounds and lane system
class Car:
    def __init__(self, x, y, color, player=False):
        self.width = 45
        self.height = 80 if player else random.choice([75, 80, 85])
        self.x = x
        self.y = y
        self.speed = BASE_SPEED if player else random.randint(2, 4)  # Slower enemy cars
        self.original_speed = self.speed  # Store original speed for recovery
        self.color = color
        self.player = player
        self.window_color = CYAN if player else WHITE
        self.type = "player" if player else random.choice(["sedan", "truck", "suv"])
        
        # Better road boundaries with lanes
        self.road_left = 175
        self.road_right = WIDTH - 225
        self.lane_width = (self.road_right - self.road_left) // 3
        
    def get_rect(self):
        """Return collision rectangle for proper collision detection"""
        return pg.Rect(self.x, self.y, self.width, self.height)
        
    def get_lane(self):
        """Get current lane (0, 1, or 2)"""
        center_x = self.x + self.width // 2
        relative_pos = center_x - self.road_left
        return max(0, min(2, int(relative_pos // self.lane_width)))
        
    def draw(self, screen):
        # Car body with subtle shading
        pg.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pg.draw.rect(screen, (min(self.color[0]+20, 255), min(self.color[1]+20, 255), 
                             min(self.color[2]+20, 255)), (self.x+2, self.y+2, self.width-4, 8))
        
        # Windows based on car type
        if self.type == "sedan":
            pg.draw.rect(screen, self.window_color, (self.x + 4, self.y + 8, self.width - 8, 20))
            pg.draw.rect(screen, self.window_color, (self.x + 4, self.y + 32, self.width - 8, 20))
            pg.draw.rect(screen, BLACK, (self.x + 4, self.y + 8, self.width - 8, 20), 1)
            pg.draw.rect(screen, BLACK, (self.x + 4, self.y + 32, self.width - 8, 20), 1)
        elif self.type == "truck":
            pg.draw.rect(screen, self.window_color, (self.x + 8, self.y + 8, 25, 18))
            pg.draw.rect(screen, BLACK, (self.x + 8, self.y + 8, 25, 18), 1)
        else:  # SUV
            pg.draw.rect(screen, self.window_color, (self.x + 4, self.y + 8, self.width - 8, 35))
            pg.draw.rect(screen, BLACK, (self.x + 4, self.y + 8, self.width - 8, 35), 1)
            
        # Wheels
        wheel_color = (20, 20, 20)
        rim_color = (80, 80, 80)
        wheel_positions = [(4, 5), (self.width-16, 5), (4, self.height-17), (self.width-16, self.height-17)]
        for wheel_pos in wheel_positions:
            pg.draw.ellipse(screen, wheel_color, (self.x + wheel_pos[0], self.y + wheel_pos[1], 12, 12))
            pg.draw.ellipse(screen, rim_color, (self.x + wheel_pos[0]+2, self.y + wheel_pos[1]+2, 8, 8))
        
    def move(self, direction=None, obstacles=None, player_car=None):
        if self.player:
            if direction == "left":
                new_x = max(self.road_left, self.x - self.speed)
                self.x = new_x
            elif direction == "right":
                new_x = min(self.road_right - self.width, self.x + self.speed)
                self.x = new_x
        else:
            # For enemy cars, check collision with other cars before moving
            original_y = self.y
            new_y = self.y + self.speed
            
            # Create temporary rect for collision testing
            temp_rect = pg.Rect(self.x, new_y, self.width, self.height)
            can_move = True
            
            # Check collision with other enemy cars
            if obstacles:
                for other_car in obstacles:
                    if other_car != self:
                        other_rect = other_car.get_rect()
                        if temp_rect.colliderect(other_rect):
                            # Calculate safe distance (car height + buffer)
                            safe_distance = self.height + 15
                            
                            if new_y + self.height > other_car.y:  # This car is behind/overlapping
                                # Position this car safely behind the other car
                                self.y = max(original_y, other_car.y - safe_distance)
                                # Slow down when following
                                self.speed = max(1, min(self.speed, other_car.speed - 0.5))
                                can_move = False
                            break
            
            # Check collision with player car
            if player_car and can_move:
                player_rect = player_car.get_rect()
                if temp_rect.colliderect(player_rect):
                    # Don't move into player, but don't slow down dramatically
                    can_move = False
            
            # Only move if safe
            if can_move:
                self.y = new_y
                # Gradually return to normal speed when not blocked
                if self.speed < self.original_speed:
                    self.speed = min(self.original_speed, self.speed + 0.1)
            
            return self.y > HEIGHT + 50  # Give some buffer before removal

# Enhanced Road class
class Road:
    def __init__(self):
        self.road_width = 450
        self.road_x = (WIDTH - self.road_width) // 2
        self.stripes = []
        for i in range(12):
            self.stripes.append({
                'y': i * 100 - 200,
                'width': 50,
                'height': 30,
                'speed': BASE_SPEED + 1
            })
            
    def draw(self, screen):
        # Draw shoulders
        pg.draw.rect(screen, SHOULDER_COLOR, (0, 0, self.road_x, HEIGHT))
        pg.draw.rect(screen, SHOULDER_COLOR, (self.road_x + self.road_width, 0, WIDTH, HEIGHT))
        
        # Road surface
        pg.draw.rect(screen, ROAD_COLOR, (self.road_x, 0, self.road_width, HEIGHT))
        
        # Lane dividers (dashed lines)
        lane_width = self.road_width // 3
        for lane in range(1, 3):  # Draw 2 lane dividers
            lane_x = self.road_x + lane * lane_width
            for stripe in self.stripes:
                if stripe['y'] > -50 and stripe['y'] < HEIGHT:
                    pg.draw.rect(screen, WHITE, (lane_x - 25, stripe['y'], 50, stripe['height']))
        
        # Road edges
        pg.draw.line(screen, WHITE, (self.road_x, 0), (self.road_x, HEIGHT), 3)
        pg.draw.line(screen, WHITE, (self.road_x + self.road_width, 0), (self.road_x + self.road_width, HEIGHT), 3)
            
    def update(self):
        for stripe in self.stripes:
            stripe['y'] += stripe['speed']
            if stripe['y'] > HEIGHT:
                stripe['y'] = -stripe['height'] - 50

# Game class with improved logic
class Game:
    def __init__(self):
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Sleek Street Racer")
        self.clock = pg.time.Clock()
        self.font = pg.font.Font(None, 42)
        self.small_font = pg.font.Font(None, 28)
        self.player = Car(WIDTH // 2 - 22, HEIGHT - 120, BLUE, True)
        self.obstacles = []
        self.road = Road()
        self.score = 0
        self.level = 1
        self.game_over = False
        self.in_menu = True
        self.last_obstacle_time = 0
        self.obstacle_frequency = 2000  # Increased spawn time
        self.play_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 60, "START RACE")
        self.min_obstacle_distance = 120  # Minimum distance between obstacles
        
        # Load and play music
        self.current_music = load_music()
        if self.current_music:
            pg.mixer.music.play(-1)
            
    def can_spawn_obstacle(self, new_x, new_y):
        """Check if we can spawn an obstacle at the given position"""
        new_rect = pg.Rect(new_x, new_y, 45, 80)
        
        # Check distance from existing obstacles
        for obstacle in self.obstacles:
            obstacle_rect = obstacle.get_rect()
            # Check if too close vertically (increased distance for better spacing)
            if abs(new_y - obstacle.y) < self.min_obstacle_distance:
                # Check if in same or adjacent lane
                new_lane = self.get_lane_from_x(new_x)
                obstacle_lane = obstacle.get_lane()
                if abs(new_lane - obstacle_lane) <= 1:
                    return False
                    
            # Also check if directly overlapping
            if new_rect.colliderect(obstacle_rect):
                return False
        
        return True
    
    def get_lane_from_x(self, x):
        """Get lane number from x position"""
        road_left = 175
        road_right = WIDTH - 225
        lane_width = (road_right - road_left) // 3
        center_x = x + 22  # Half car width
        relative_pos = center_x - road_left
        return max(0, min(2, int(relative_pos // lane_width)))
    
    def get_safe_spawn_position(self):
        """Find a safe position to spawn a new obstacle"""
        road_left = 175
        road_right = WIDTH - 225
        lane_width = (road_right - road_left) // 3
        
        # Try each lane
        lanes = [0, 1, 2]
        random.shuffle(lanes)
        
        for lane in lanes:
            lane_center = road_left + lane * lane_width + lane_width // 2
            spawn_x = lane_center - 22  # Half car width
            spawn_y = -100
            
            if self.can_spawn_obstacle(spawn_x, spawn_y):
                return spawn_x, spawn_y
        
        return None, None
            
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.current_music:
                    pg.mixer.music.stop()
                pg.quit()
                sys.exit()
                
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if self.in_menu and self.play_button.is_clicked(event.pos):
                    self.in_menu = False
                    
            if event.type == pg.KEYDOWN and self.game_over:
                if event.key == pg.K_r:
                    self.reset_game()
                    
    def update(self):
        if self.game_over or self.in_menu:
            return
            
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.player.move("left")
        if keys[pg.K_RIGHT]:
            self.player.move("right")
            
        # Spawn obstacles with better logic
        current_time = pg.time.get_ticks()
        if current_time - self.last_obstacle_time > self.obstacle_frequency:
            spawn_x, spawn_y = self.get_safe_spawn_position()
            
            if spawn_x is not None:
                color = random.choice([
                    (220, 60, 60),   # Red
                    (60, 180, 60),   # Green
                    (220, 140, 60),  # Orange
                    (180, 60, 180),  # Purple
                    (60, 60, 220)    # Blue
                ])
                
                new_obstacle = Car(spawn_x, spawn_y, color)
                new_obstacle.speed = random.randint(2, 4)  # Slower than player
                new_obstacle.original_speed = new_obstacle.speed
                self.obstacles.append(new_obstacle)
                self.last_obstacle_time = current_time
                
                # Gradually increase difficulty
                if self.score > 0 and self.score % 5 == 0:
                    self.obstacle_frequency = max(800, self.obstacle_frequency - 50)
                    self.level = (self.score // 5) + 1
                    self.min_obstacle_distance = max(100, self.min_obstacle_distance - 5)
                
        # Move obstacles and remove off-screen ones
        for obstacle in self.obstacles[:]:
            if obstacle.move(obstacles=self.obstacles, player_car=self.player):
                self.obstacles.remove(obstacle)
                self.score += 1
                
            # Improved collision detection
            player_rect = self.player.get_rect()
            obstacle_rect = obstacle.get_rect()
            
            # Add small buffer to make collision feel more fair
            buffer = 3
            collision_rect = pg.Rect(
                player_rect.x + buffer,
                player_rect.y + buffer,
                player_rect.width - 2 * buffer,
                player_rect.height - 2 * buffer
            )
            
            if collision_rect.colliderect(obstacle_rect):
                self.game_over = True
                if self.current_music:
                    pg.mixer.music.fadeout(2000)
        
        self.road.update()
        
    def draw(self):
        # Gradient background
        for y in range(HEIGHT):
            shade = 10 + int(15 * (y / HEIGHT))
            pg.draw.line(self.screen, (shade, shade, shade), (0, y), (WIDTH, y))
        
        if self.in_menu:
            # Menu title with shadow
            title = self.font.render("SLEEK STREET RACER", True, (200, 200, 0))
            shadow = self.font.render("SLEEK STREET RACER", True, (80, 80, 0))
            self.screen.blit(shadow, (WIDTH//2 - title.get_width()//2 + 3, 103))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            # Instructions
            instructions = [
                "Use LEFT/RIGHT arrows to steer your car",
                "Avoid other vehicles on the road",
                f"Current high score: {self.get_high_score()}"
            ]
            
            for i, line in enumerate(instructions):
                text = self.small_font.render(line, True, WHITE)
                self.screen.blit(text, (WIDTH//2 - text.get_width()//2, 180 + i*40))
            
            self.play_button.draw(self.screen, self.font)
        else:
            self.road.draw(self.screen)
            
            # Draw all cars
            all_cars = [self.player] + self.obstacles
            for car in all_cars:
                car.draw(self.screen)
                
            # HUD
            hud_bg = pg.Surface((280, 120), pg.SRCALPHA)
            hud_bg.fill((0, 0, 0, 150))
            pg.draw.rect(hud_bg, (255, 255, 255, 30), (0, 0, 280, 120), 2, border_radius=5)
            self.screen.blit(hud_bg, (10, 10))
            
            texts = [
                f"Score: {self.score}",
                f"Level: {self.level}",
                f"Cars on road: {len(self.obstacles)}"
            ]
            
            for i, text in enumerate(texts):
                rendered = self.small_font.render(text, True, WHITE)
                self.screen.blit(rendered, (20, 20 + i*30))
            
            if self.game_over:
                self.draw_game_over()
                
        pg.display.flip()
        
    def draw_game_over(self):
        # Dark overlay
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Game over box
        box = pg.Surface((400, 200), pg.SRCALPHA)
        box.fill((0, 0, 0, 200))
        pg.draw.rect(box, (255, 255, 255, 30), (0, 0, 400, 200), 2)
        self.screen.blit(box, (WIDTH//2 - 200, HEIGHT//2 - 100))
        
        # Game over text
        title = self.font.render("GAME OVER", True, RED)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
        
        score = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
        self.screen.blit(score, (WIDTH//2 - score.get_width()//2, HEIGHT//2 - 30))
        
        restart = self.small_font.render("Press R to restart", True, YELLOW)
        self.screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 20))
        
    def get_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0
            
    def save_high_score(self):
        with open("highscore.txt", "w") as f:
            f.write(str(max(self.score, self.get_high_score())))
        
    def reset_game(self):
        self.save_high_score()
        self.player = Car(WIDTH // 2 - 22, HEIGHT - 120, BLUE, True)
        self.obstacles = []
        self.road = Road()
        self.score = 0
        self.level = 1
        self.game_over = False
        self.last_obstacle_time = pg.time.get_ticks()
        self.obstacle_frequency = 2000
        self.min_obstacle_distance = 120
        
        # Restart music if it was playing before
        if self.current_music:
            pg.mixer.music.play(-1)
        
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

# Enhanced Button class
class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.color = (50, 180, 80)
        self.hover_color = (80, 220, 100)
        self.shadow = pg.Surface((width, height), pg.SRCALPHA)
        self.shadow.fill((0, 0, 0, 50))
        
    def draw(self, screen, font):
        mouse_pos = pg.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        
        # Button shadow
        screen.blit(self.shadow, (self.rect.x + 3, self.rect.y + 3))
        
        # Button body
        pg.draw.rect(screen, color, self.rect, border_radius=8)
        pg.draw.rect(screen, (255, 255, 255, 80), self.rect, 2, border_radius=8)
        
        # Button text with shadow
        text_shadow = font.render(self.text, True, (0, 0, 0, 100))
        text = font.render(self.text, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()