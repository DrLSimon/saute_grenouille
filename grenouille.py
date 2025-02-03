import pygame
import random
import asyncio
import collections
from abc import ABC, abstractmethod

# --- SETTINGS & CONFIGURATION ---
class Settings:
    WIDTH = 800
    HEIGHT = 400
    GRAVITY = 1
    JUMP_FORCE = -15
    OBSTACLE_SPEED = 5
    FPS = 30
    MIN_OBSTACLE_SPACE = 150  # Minimum space between obstacles

# --- COLORS ---
class Colors:
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

# --- TRANSFORM CLASS ---
class Transform:
    def __init__(self, position=(0, 0), rotation=0, scale=(1, 1)):
        self.position = pygame.Vector2(position)
        self.rotation = rotation
        self.scale = pygame.Vector2(scale)
    
    def move(self, dx, dy):
        self.position.x += dx
        self.position.y += dy

    def set_position(self, x, y):
        self.position.x = x
        self.position.y = y

    def add_rotation(self, d_angle):
        self.rotation += d_angle

# --- EFFECT INTERFACE ---
class Effect(ABC):
    def __init__(self, duration: int):
        self.duration = duration  # measured in frames

    @abstractmethod
    def update(self):
        """
        Update the effect. The 'transform' parameter is provided in case
        the effect needs to modify spatial properties.
        """
        pass

    def is_finished(self) -> bool:
        return self.duration <= 0

# --- VIBRATION EFFECT ---
class VibrationEffect(Effect):
    def __init__(self, duration: int, transform: Transform, magnitude: int = 5, rotation_speed: int = 10):
        super().__init__(duration)
        self.transform = transform
        self.magnitude = magnitude
        self.rotation_speed = rotation_speed
        self.direction = 1  # alternating direction

    def update(self):
        # Oscillate the x-position and rotation.
        self.transform.move(self.magnitude * self.direction, 0)
        self.transform.add_rotation(self.rotation_speed * self.direction)
        self.direction *= -1  # alternate direction each frame
        self.duration -= 1

# --- SOUND EFFECT ---
class SoundEffect(Effect):
    def __init__(self, sound: pygame.mixer.Sound):
        super().__init__(duration=0)
        self.sound = sound
        self.played = False

    def update(self):
        if not self.played:
            self.sound.play()
            self.played = True

    def is_finished(self) -> bool:
        return self.played

# --- DESTROYER EFFECT ---
class DestroyerEffect(Effect):
    def __init__(self, duration: int, target):
        super().__init__(duration)
        self.oscillation_counter = 0
        self.target = target


    def update(self):
        self.oscillation_counter += 1
        self.duration -= 1
        self.target.display_destroyed = (self.oscillation_counter//5)%2
        if self.is_finished():
            self.target.in_destroy_mode = False

# --- EFFECT MANAGER ---
class EffectManager:
    def __init__(self):
        self.active_effects: list[Effect] = []

    def add_effect(self, effect: Effect):
        self.active_effects.append(effect)

    def update(self):
        # Update all active effects.
        for effect in self.active_effects:
            effect.update()
        # Remove completed effects.
        self.active_effects = [e for e in self.active_effects if not e.is_finished()]


# --- RESOURCE MANAGER ---
class Resources:
    def __init__(self):
        # Load images and sounds.
        self.grenouille_img = pygame.transform.scale(pygame.image.load("grenouille.png"), (40, 40))
        self.grenouille_destroyer_img = pygame.transform.scale(pygame.image.load("grenouille_destroyer.png"), (40, 40))
        self.coeur_plein = pygame.transform.scale(pygame.image.load("coeur_plein.png"), (20, 20))
        self.coeur_vide = pygame.transform.scale(pygame.image.load("coeur_vide.png"), (20, 20))
        self.destroyer_img = pygame.transform.scale(pygame.image.load("destroyer.png"), (20, 20))
        
        self.rock_images = []
        self.rock_masks = []
        for i in range(4):
            rock = pygame.image.load(f"rock_{i}.png")
            orig_width, orig_height = rock.get_size()
            scale_factor = 40 / orig_height
            new_width = int(orig_width * scale_factor)
            rock = pygame.transform.scale(rock, (new_width, 40))
            self.rock_images.append(rock)
            self.rock_masks.append(pygame.mask.from_surface(rock))
        
        self.bonus_sound = pygame.mixer.Sound("bonus.ogg")
        self.collision_sound = pygame.mixer.Sound("collision.ogg")
        self.life_sound = pygame.mixer.Sound("vie.ogg")
    
    def play_background_music(self):
        pygame.mixer.music.load("background.ogg")
        pygame.mixer.music.play(-1)

# --- ABSTRACT BASE CLASS FOR GAME OBJECTS ---
class GameObject(ABC):
    def __init__(self):
        self.transform = Transform()

    @abstractmethod
    def update(self, effect_manager):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

# --- OBSTACLE ---
class Obstacle(GameObject):
    def __init__(self, last_x: int, resources: Resources):
        super().__init__()
        # Set initial position via transform.
        self.transform.set_position(
            Settings.WIDTH if last_x == 0 else max(Settings.WIDTH, last_x + Settings.MIN_OBSTACLE_SPACE),
            Settings.HEIGHT - 40
        )
        self.destroyed = False
        self.image_index = random.randint(0, len(resources.rock_images) - 1)
        self.image = resources.rock_images[self.image_index]
        self.mask = resources.rock_masks[self.image_index]
        self.width = self.image.get_width()
        self.height = 40

    def update(self, effect_manager):
        self.transform.move(-Settings.OBSTACLE_SPEED, 0)

    def draw(self, surface):
        if not self.destroyed:
            surface.blit(self.image, (self.transform.position.x, self.transform.position.y))

# --- BONUS ---
class Bonus(GameObject):
    def __init__(self, bonus_type: str, resources: Resources):
        super().__init__()
        self.transform.set_position(Settings.WIDTH, random.randint(Settings.HEIGHT - 140, Settings.HEIGHT - 60))
        self.bonus_type = bonus_type
        self.width = 20
        self.height = 20
        self.resources = resources

    def update(self, effect_manager):
        self.transform.move(-Settings.OBSTACLE_SPEED, 0)

    def draw(self, surface):
        if self.bonus_type == "vie":
            surface.blit(self.resources.coeur_plein, (self.transform.position.x, self.transform.position.y))
        else:
            surface.blit(self.resources.destroyer_img, (self.transform.position.x, self.transform.position.y))

# --- LEVEL MANAGER ---
class Level:
    def __init__(self, resources: Resources):
        self.resources = resources
        self.obstacles = collections.deque([],10)
        self.bonuses = collections.deque([],10)
        self.last_obstacle_x = 0

    def add_obstacle(self):
        obstacle = Obstacle(self.last_obstacle_x, self.resources)
        self.obstacles.append(obstacle)
        self.last_obstacle_x = obstacle.transform.position.x

    def add_bonus(self):
        bonus_type = random.choice(["vie", "destroy"])
        self.bonuses.append(Bonus(bonus_type, self.resources))

    def update(self, effect_manager) -> int:
        effect_manager.update()
        score_increment = 0
        if not self.obstacles or (Settings.WIDTH - self.obstacles[-1].transform.position.x) > Settings.MIN_OBSTACLE_SPACE:
            self.add_obstacle()
        for obstacle in list(self.obstacles):
            obstacle.update(effect_manager)
            if obstacle.transform.position.x + obstacle.width < 0 or obstacle.destroyed:
                self.obstacles.remove(obstacle)
                score_increment += 1
        for bonus in list(self.bonuses):
            bonus.update(effect_manager)
            if bonus.transform.position.x + bonus.width < 0:
                self.bonuses.remove(bonus)
        return score_increment

    def draw(self, surface):
        for obstacle in self.obstacles:
            obstacle.draw(surface)
        for bonus in self.bonuses:
            bonus.draw(surface)

# --- PLAYER (Grenouille) ---
class Grenouille(GameObject):
    def __init__(self, resources: Resources):
        super().__init__()
        self.transform.set_position(100, Settings.HEIGHT - 50)
        self.width = 40
        self.height = 40
        self.vy = 0
        self.on_ground = True
        self.lives = 5
        self.last_collided_obstacle = None
        self.resources = resources
        self.image = self.resources.grenouille_img
        self.image_destroyed = self.resources.grenouille_destroyer_img
        self.mask = pygame.mask.from_surface(resources.grenouille_img)
        self.in_destroy_mode = False
        self.display_destroyed = False


    def jump(self):
        if self.on_ground:
            self.vy = Settings.JUMP_FORCE
            self.on_ground = False

    def update(self, effect_manager):
        self.effect_manager = effect_manager
        # Apply physics for vertical movement.
        self.vy += Settings.GRAVITY
        self.transform.move(0, self.vy)
        if self.transform.position.y >= Settings.HEIGHT - self.height:
            self.transform.position.y = Settings.HEIGHT - self.height
            self.on_ground = True

    def draw(self, surface):
        image = self.image
        if self.display_destroyed:
            image = self.image_destroyed

        rotated = pygame.transform.rotate(image, self.transform.rotation)
        rect = rotated.get_rect(center=(self.transform.position.x + self.width // 2,
                                        self.transform.position.y + self.height // 2))
        surface.blit(rotated, rect.topleft)

    def trigger_vibration(self):
        # Delegate vibration as an effect.
        self.effect_manager.add_effect(VibrationEffect(transform=self.transform, duration=10))

    def play_sound(self, sound: pygame.mixer.Sound):
        self.effect_manager.add_effect(SoundEffect(sound))

    def activate_destroyer_mode(self):
        # Activate destroyer mode by adding a destroyer effect.
        self.effect_manager.add_effect(DestroyerEffect(target=self, duration=Settings.FPS * 3))
        self.in_destroy_mode = True
    
    def handle_collision(self, obstacle: Obstacle):
        offset = (int(obstacle.transform.position.x - self.transform.position.x),
                  int(obstacle.transform.position.y - self.transform.position.y))
        if self.mask.overlap(obstacle.mask, offset):
            if self.last_collided_obstacle != obstacle:
                # If a destroyer effect is active, destroy the obstacle.
                if self.in_destroy_mode:
                    obstacle.destroyed = True
                else:
                    self.trigger_vibration()
                    self.vy = Settings.JUMP_FORCE // 2
                    self.lives -= 1
                    self.play_sound(self.resources.collision_sound)
                self.last_collided_obstacle = obstacle

    def catch_bonus(self, bonus: Bonus):
        if not (self.transform.position.x < bonus.transform.position.x + bonus.width and
            self.transform.position.x + self.width > bonus.transform.position.x and
            self.transform.position.y < bonus.transform.position.y + bonus.height and
            self.transform.position.y + self.height > bonus.transform.position.y):
            return False
        if bonus.bonus_type == "vie" and self.lives < 5:
            self.lives += 1
            self.effect_manager.add_effect(SoundEffect(self.resources.life_sound))
            return True
        elif bonus.bonus_type == "destroy":
            # Activate destroyer mode via an effect and play the bonus sound.
            self.activate_destroyer_mode()
            self.effect_manager.add_effect(SoundEffect(self.resources.bonus_sound))
            return True
        return False

# --- RENDERER (Handles HUD and static screens) ---
class Renderer:
    def __init__(self, surface, resources: Resources):
        self.surface = surface
        self.font = pygame.font.Font(None, 36)
        self.resources = resources

    def draw_HUD(self, lives: int, score: int):
        for i in range(5):
            img = self.resources.coeur_plein if i < lives else self.resources.coeur_vide
            self.surface.blit(img, (10 + i * 30, 10))
        score_text = self.font.render(f"Score: {score}", True, Colors.WHITE)
        self.surface.blit(score_text, (Settings.WIDTH - 120, 10))

    def draw_start_screen(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Press SPACE to play", True, Colors.WHITE)
        self.surface.fill(Colors.BLUE)
        self.surface.blit(text, (Settings.WIDTH // 4, Settings.HEIGHT // 2))
        pygame.display.update()

    def draw_game_over(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Game Over", True, Colors.WHITE)
        self.surface.fill(Colors.BLUE)
        self.surface.blit(text, (Settings.WIDTH // 3, Settings.HEIGHT // 2))
        pygame.display.update()
        pygame.time.delay(3000)

# --- GAME CLASS (Coordinates everything) ---
class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pygame.display.set_caption("Saute-Grenouille")
        self.clock = pygame.time.Clock()
        self.resources = Resources()
        self.resources.play_background_music()
        self.renderer = Renderer(self.screen, self.resources)
        self.player = Grenouille(self.resources)
        self.level = Level(self.resources)
        self.score = 0
        self.effect_manager = EffectManager()

    async def start_screen(self):
        waiting = True
        while waiting:
            self.renderer.draw_start_screen()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            await asyncio.sleep(0)

    def game_over_screen(self):
        self.renderer.draw_game_over()

    async def run(self):
        await self.start_screen()
        running = True
        while running:
            self.clock.tick(Settings.FPS)
            self.screen.fill(Colors.BLUE)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.player.jump()
            self.player.update(self.effect_manager)

            # Randomly add bonus.
            if random.randint(1, 150) < 2:
                self.level.add_bonus()

            self.score += self.level.update(self.effect_manager)
            self.level.draw(self.screen)

            # Check collisions for obstacles.
            for obstacle in self.level.obstacles:
                self.player.handle_collision(obstacle)

            # Check collisions for bonuses.
            for bonus in list(self.level.bonuses):
                caught_it = self.player.catch_bonus(bonus)
                if caught_it:
                    self.level.bonuses.remove(bonus)

            self.player.draw(self.screen)

            if self.player.lives <= 0:
                self.game_over_screen()
                running = False

            self.renderer.draw_HUD(self.player.lives, self.score)
            pygame.display.update()
            await asyncio.sleep(0)
        pygame.quit()

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    asyncio.run(Game().run())


