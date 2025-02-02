import pygame
import random
import asyncio

# Pré-initialisation du mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# === CLASSES DE CONFIGURATION ET RESSOURCES ===

class Settings:
    LARGEUR = 800
    HAUTEUR = 400
    GRAVITE = 1
    SAUT = -15
    VITESSE_OBSTACLE = 5
    FPS = 30
    ESPACE_MIN_OBSTACLES = 150  # Distance minimale entre obstacles

class Colors:
    BLEU = (0, 0, 255)
    BLANC = (255, 255, 255)
    ROUGE = (255, 0, 0)
    VERT = (0, 255, 0)

class Resources:
    # Images principales
    grenouille_img = pygame.transform.scale(pygame.image.load("grenouille.png"), (40, 40))
    grenouille_destroyer_img = pygame.transform.scale(pygame.image.load("grenouille_destroyer.png"), (40, 40))
    coeur_plein = pygame.transform.scale(pygame.image.load("coeur_plein.png"), (20, 20))
    coeur_vide = pygame.transform.scale(pygame.image.load("coeur_vide.png"), (20, 20))
    destroyer_img = pygame.transform.scale(pygame.image.load("destroyer.png"), (20, 20))
    
    # Chargement des images de roches et création de leurs masques
    rock_images = []
    rock_masks = []
    for i in range(4):
        rock = pygame.image.load(f"rock_{i}.png")
        orig_width, orig_height = rock.get_size()
        scale_factor = 40 / orig_height
        new_width = int(orig_width * scale_factor)
        rock = pygame.transform.scale(rock, (new_width, 40))
        rock_images.append(rock)
        rock_masks.append(pygame.mask.from_surface(rock))
    
    # Sons
    bonus_sound = pygame.mixer.Sound("bonus.ogg")
    collision_sound = pygame.mixer.Sound("collision.ogg")
    vie_sound = pygame.mixer.Sound("vie.ogg")
    
    @classmethod
    def play_background_music(cls):
        pygame.mixer.music.load("background.ogg")
        pygame.mixer.music.play(-1)  # Lecture en boucle

# Lancement de la musique de fond
Resources.play_background_music()

# Création de la fenêtre
fenetre = pygame.display.set_mode((Settings.LARGEUR, Settings.HAUTEUR))
pygame.display.set_caption("Saute-Grenouille")

# === CLASSES DE LOGIQUE ET DE RENDU DU JEU ===

# EffetSpecial : gère l’effet (sonore et éventuellement visuel) selon son type.
class EffetSpecial:
    def __init__(self, effect_type):
        self.effect_type = effect_type
        if effect_type == "bonus":
            self.sound = Resources.bonus_sound
        elif effect_type == "collision":
            self.sound = Resources.collision_sound
        elif effect_type == "vie":
            self.sound = Resources.vie_sound
        else:
            self.sound = None

    def play(self):
        if self.sound:
            self.sound.play()
        # Vous pouvez ajouter ici des animations spécifiques pour cet effet

# Niveau : gère obstacles, bonus et utilise les ressources pour les obstacles.
class Niveau:
    def __init__(self):
        self.obstacles = []
        self.bonuses = []
        self.dernier_obstacle_x = 0

    def ajouter_obstacle(self):
        nouvel_obstacle = Obstacle(self.dernier_obstacle_x,
                                   Resources.rock_images,
                                   Resources.rock_masks)
        self.obstacles.append(nouvel_obstacle)
        self.dernier_obstacle_x = nouvel_obstacle.x

    def ajouter_bonus(self):
        self.bonuses.append(Bonus(random.choice(["vie", "destroy"])))

    def update(self):
        score_increment = 0
        if not self.obstacles or (Settings.LARGEUR - self.obstacles[-1].x) > Settings.ESPACE_MIN_OBSTACLES:
            self.ajouter_obstacle()
        for obstacle in self.obstacles[:]:
            obstacle.update()
            if obstacle.x + obstacle.largeur < 0 or obstacle.detruit:
                self.obstacles.remove(obstacle)
                score_increment += 1
        for bonus in self.bonuses[:]:
            bonus.update()
            if bonus.x + bonus.largeur < 0:
                self.bonuses.remove(bonus)
        return score_increment

    def draw(self, surface):
        for obstacle in self.obstacles:
            obstacle.draw(surface)
        for bonus in self.bonuses:
            bonus.draw(surface)

# Obstacle (logique et rendu)
class Obstacle:
    def __init__(self, dernier_x, images, masks):
        self.x = Settings.LARGEUR if dernier_x == 0 else max(Settings.LARGEUR, dernier_x + Settings.ESPACE_MIN_OBSTACLES)
        self.y = Settings.HAUTEUR - 40
        self.detruit = False
        self.image_index = random.randint(0, len(images) - 1)
        self.image = images[self.image_index]
        self.mask = masks[self.image_index]
        self.largeur = self.image.get_width()
        self.hauteur = 40

    def update(self):
        self.x -= Settings.VITESSE_OBSTACLE

    def draw(self, surface):
        if not self.detruit:
            surface.blit(self.image, (self.x, self.y))

# Bonus (logique et rendu)
class Bonus:
    def __init__(self, type_bonus):
        self.x = Settings.LARGEUR
        self.y = random.randint(Settings.HAUTEUR - 140, Settings.HAUTEUR - 60)
        self.type_bonus = type_bonus
        self.largeur = 20
        self.hauteur = 20

    def update(self):
        self.x -= Settings.VITESSE_OBSTACLE

    def draw(self, surface):
        if self.type_bonus == "vie":
            surface.blit(Resources.coeur_plein, (self.x, self.y))
        else:
            surface.blit(Resources.destroyer_img, (self.x, self.y))

# Grenouille (logique et rendu)
class Grenouille:
    def __init__(self):
        self.x = 100
        self.y = Settings.HAUTEUR - 50
        self.largeur = 40
        self.hauteur = 40
        self.vy = 0
        self.au_sol = True
        self.vies = 5
        self.dernier_obstacle_touche = None
        self.mask = pygame.mask.from_surface(Resources.grenouille_img)
        self.angle = 0
        self.vibration_frames = 0
        self.vibration_direction = 1
        self.mode_destroyeur = False
        self.destroyeur_timer = 0
        self.oscillation_counter = 0

    def sauter(self):
        if self.au_sol:
            self.vy = Settings.SAUT
            self.au_sol = False

    def update(self):
        self.vy += Settings.GRAVITE
        self.y += self.vy
        if self.y >= Settings.HAUTEUR - self.hauteur:
            self.y = Settings.HAUTEUR - self.hauteur
            self.au_sol = True

        if self.vibration_frames > 0:
            self.x += 5 * self.vibration_direction
            self.angle += 10 * self.vibration_direction
            self.vibration_direction *= -1
            self.vibration_frames -= 1

        if self.mode_destroyeur:
            self.destroyeur_timer -= 1
            self.oscillation_counter += 1
            if self.destroyeur_timer <= 0:
                self.mode_destroyeur = False
                self.oscillation_counter = 0

    def draw(self, surface):
        if self.mode_destroyeur:
            if (self.oscillation_counter // 5) % 2 == 0:
                image_a_afficher = Resources.grenouille_destroyer_img
            else:
                image_a_afficher = Resources.grenouille_img
        else:
            image_a_afficher = Resources.grenouille_img

        image_rotated = pygame.transform.rotate(image_a_afficher, self.angle)
        rect = image_rotated.get_rect(center=(self.x + self.largeur // 2, self.y + self.hauteur // 2))
        surface.blit(image_rotated, rect.topleft)

    def vibrer(self):
        self.vibration_frames = 10
        self.vibration_direction = 1

    def collision(self, obstacle):
        offset_x = obstacle.x - self.x
        offset_y = obstacle.y - self.y
        if self.mask.overlap(obstacle.mask, (offset_x, offset_y)):
            if self.dernier_obstacle_touche != obstacle:
                if self.mode_destroyeur:
                    obstacle.detruit = True
                else:
                    self.vibrer()
                    self.vy = Settings.SAUT // 2
                    self.vies -= 1
                    EffetSpecial("collision").play()
                self.dernier_obstacle_touche = obstacle

    def attraper_bonus(self, bonus):
        if bonus.type_bonus == "vie" and self.vies < 5:
            self.vies += 1
            EffetSpecial("vie").play()
        elif bonus.type_bonus == "destroy":
            self.mode_destroyeur = True
            self.destroyeur_timer = Settings.FPS * 3
            self.oscillation_counter = 0
            EffetSpecial("bonus").play()

# Renderer : gère le rendu du HUD, des écrans d'accueil et de fin.
class Renderer:
    def __init__(self, surface):
        self.surface = surface
        self.font = pygame.font.Font(None, 36)

    def draw_HUD(self, vies, score):
        for i in range(5):
            if i < vies:
                self.surface.blit(Resources.coeur_plein, (10 + i * 30, 10))
            else:
                self.surface.blit(Resources.coeur_vide, (10 + i * 30, 10))
        score_text = self.font.render(f"Score: {score}", True, Colors.BLANC)
        self.surface.blit(score_text, (Settings.LARGEUR - 120, 10))

    def draw_accueil(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Appuyez sur ESPACE pour jouer", True, Colors.BLANC)
        self.surface.fill(Colors.BLEU)
        self.surface.blit(text, (Settings.LARGEUR // 4, Settings.HAUTEUR // 2))
        pygame.display.update()

    def draw_fin(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Game Over", True, Colors.BLANC)
        self.surface.fill(Colors.BLEU)
        self.surface.blit(text, (Settings.LARGEUR // 3, Settings.HAUTEUR // 2))
        pygame.display.update()
        pygame.time.delay(3000)

# Écran d'accueil (async pour pygbag)
async def ecran_accueil(renderer):
    attente = True
    while attente:
        renderer.draw_accueil()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                attente = False
        await asyncio.sleep(0)

# Écran de fin
def ecran_fin(renderer):
    renderer.draw_fin()

# Boucle principale (async pour pygbag)
async def main():
    clock = pygame.time.Clock()
    player = Grenouille()
    niveau = Niveau()
    renderer = Renderer(fenetre)
    score = 0

    await ecran_accueil(renderer)

    run = True
    while run:
        clock.tick(Settings.FPS)
        fenetre.fill(Colors.BLEU)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.sauter()

        player.update()
        player.draw(fenetre)

        # Apparition aléatoire de bonus
        if random.randint(1, 150) < 2:
            niveau.ajouter_bonus()

        score += niveau.update()
        niveau.draw(fenetre)

        # Gestion des collisions
        for obstacle in niveau.obstacles:
            player.collision(obstacle)
        for bonus in niveau.bonuses[:]:
            if (player.x < bonus.x + bonus.largeur and
                player.x + player.largeur > bonus.x and
                player.y < bonus.y + bonus.hauteur and
                player.y + player.hauteur > bonus.y):
                player.attraper_bonus(bonus)
                niveau.bonuses.remove(bonus)

        if player.vies <= 0:
            ecran_fin(renderer)
            run = False

        renderer.draw_HUD(player.vies, score)
        pygame.display.update()
        await asyncio.sleep(0)
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
