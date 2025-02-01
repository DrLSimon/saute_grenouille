import pygame
import random

# Initialisation de Pygame
pygame.init()

# Parametres du jeu
LARGEUR, HAUTEUR = 800, 400
GRAVITE = 1
SAUT = -15
VITESSE_OBSTACLE = 5
FPS = 30

# Couleurs
BLEU = (0, 0, 255)
BLANC = (255, 255, 255)
ROUGE = (255, 0, 0)
VERT = (0, 255, 0)

# Chargement des images
grenouille_img = pygame.image.load("grenouille.png")
grenouille_img = pygame.transform.scale(grenouille_img, (40, 40))
grenouille_destroyer_img = pygame.image.load("grenouille_destroyer.png")
grenouille_destroyer_img = pygame.transform.scale(grenouille_destroyer_img, (40, 40))

coeur_plein = pygame.image.load("coeur_plein.png")
coeur_vide = pygame.image.load("coeur_vide.png")
coeur_plein = pygame.transform.scale(coeur_plein, (20, 20))
coeur_vide = pygame.transform.scale(coeur_vide, (20, 20))

# Chargement de l'image pour le bonus de destruction
destroyer_img = pygame.image.load("destroyer.png")
destroyer_img = pygame.transform.scale(destroyer_img, (20, 20))

# Chargement et mise à l'échelle des images d'obstacles
rock_images = []
for i in range(4):
    rock = pygame.image.load(f"rock_{i}.png")
    orig_width, orig_height = rock.get_size()
    scale_factor = 40 / orig_height
    new_width = int(orig_width * scale_factor)
    rock = pygame.transform.scale(rock, (new_width, 40))
    rock_images.append(rock)

# Creation de la fenetre
fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Saute-Grenouille")

# Classes
class Grenouille:
    def __init__(self):
        self.x = 100
        self.y = HAUTEUR - 50
        self.largeur = 40
        self.hauteur = 40
        self.vy = 0
        self.au_sol = True
        self.vies = 5
        self.dernier_obstacle_touche = None
        self.angle = 0
        self.vibration_frames = 0
        self.vibration_direction = 1
        self.mode_destroyeur = False
        self.destroyeur_timer = 0
        self.oscillation_counter = 0  # Compteur pour alterner les images en mode destroyer

    def sauter(self):
        if self.au_sol:
            self.vy = SAUT
            self.au_sol = False

    def mise_a_jour(self):
        self.vy += GRAVITE
        self.y += self.vy
        if self.y >= HAUTEUR - self.hauteur:
            self.y = HAUTEUR - self.hauteur
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

    def afficher(self):
        if self.mode_destroyeur:
            if (self.oscillation_counter // 5) % 2 == 0:
                image_a_afficher = grenouille_destroyer_img
            else:
                image_a_afficher = grenouille_img
        else:
            image_a_afficher = grenouille_img

        image_rotated = pygame.transform.rotate(image_a_afficher, self.angle)
        rect = image_rotated.get_rect(center=(self.x + self.largeur // 2, self.y + self.hauteur // 2))
        fenetre.blit(image_rotated, rect.topleft)

    def vibrer(self):
        self.vibration_frames = 10
        self.vibration_direction = 1

    def collision(self, obstacle):
        if self.dernier_obstacle_touche != obstacle:
            if self.mode_destroyeur:
                obstacle.detruit = True
            else:
                self.vibrer()
                self.vy = SAUT // 2
                self.vies -= 1
            self.dernier_obstacle_touche = obstacle

    def attraper_bonus(self, bonus):
        if bonus.type_bonus == "vie" and self.vies < 5:
            self.vies += 1
        elif bonus.type_bonus == "destroy":
            self.mode_destroyeur = True
            self.destroyeur_timer = FPS * 3
            self.oscillation_counter = 0

class Obstacle:
    def __init__(self):
        self.x = LARGEUR
        self.y = HAUTEUR - 40
        self.detruit = False
        self.image = rock_images[random.randint(0, len(rock_images)-1)]
        self.largeur = self.image.get_width()
        self.hauteur = 40

    def mise_a_jour(self):
        self.x -= VITESSE_OBSTACLE

    def afficher(self):
        if not self.detruit:
            fenetre.blit(self.image, (self.x, self.y))

class Bonus:
    def __init__(self, type_bonus):
        self.x = LARGEUR
        self.y = random.randint(HAUTEUR - 140, HAUTEUR - 60)
        self.type_bonus = type_bonus
        self.largeur = 20
        self.hauteur = 20

    def mise_a_jour(self):
        self.x -= VITESSE_OBSTACLE

    def afficher(self):
        if self.type_bonus == "vie":
            fenetre.blit(coeur_plein, (self.x, self.y))
        else:
            fenetre.blit(destroyer_img, (self.x, self.y))

# Affichage du HUD
def afficher_HUD(vies, score):
    for i in range(5):
        if i < vies:
            fenetre.blit(coeur_plein, (10 + i * 30, 10))
        else:
            fenetre.blit(coeur_vide, (10 + i * 30, 10))
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, BLANC)
    fenetre.blit(score_text, (LARGEUR - 120, 10))

# Ecran d'accueil
def ecran_accueil():
    font = pygame.font.Font(None, 48)
    text = font.render("Appuyez sur ESPACE pour jouer", True, BLANC)
    attente = True
    while attente:
        fenetre.fill(BLEU)
        fenetre.blit(text, (LARGEUR // 4, HAUTEUR // 2))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                attente = False

# Ecran de fin
def ecran_fin():
    font = pygame.font.Font(None, 48)
    text = font.render("Game Over", True, BLANC)
    fenetre.fill(BLEU)
    fenetre.blit(text, (LARGEUR // 3, HAUTEUR // 2))
    pygame.display.update()
    pygame.time.delay(3000)

# Boucle principale
def main():
    clock = pygame.time.Clock()
    grenouille = Grenouille()
    obstacles = []
    bonuses = []
    score = 0

    ecran_accueil()

    run = True
    while run:
        clock.tick(FPS)
        fenetre.fill(BLEU)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                grenouille.sauter()

        grenouille.mise_a_jour()
        grenouille.afficher()

        if random.randint(1, 100) < 2:
            obstacles.append(Obstacle())
        if random.randint(1, 150) < 2:
            bonuses.append(Bonus(random.choice(["vie", "destroy"])))

        for obstacle in obstacles[:]:
            obstacle.mise_a_jour()
            obstacle.afficher()
            if obstacle.x + obstacle.largeur < 0 or obstacle.detruit:
                obstacles.remove(obstacle)
                score += 1
            if (grenouille.x < obstacle.x + obstacle.largeur and
                grenouille.x + grenouille.largeur > obstacle.x and
                grenouille.y < obstacle.y + obstacle.hauteur and
                grenouille.y + grenouille.hauteur > obstacle.y):
                grenouille.collision(obstacle)

        for bonus in bonuses[:]:
            bonus.mise_a_jour()
            bonus.afficher()
            if (grenouille.x < bonus.x + bonus.largeur and
                grenouille.x + grenouille.largeur > bonus.x and
                grenouille.y < bonus.y + bonus.hauteur and
                grenouille.y + grenouille.hauteur > bonus.y):
                grenouille.attraper_bonus(bonus)
                bonuses.remove(bonus)

        if grenouille.vies <= 0:
            ecran_fin()
            run = False

        afficher_HUD(grenouille.vies, score)
        pygame.display.update()

    pygame.quit()

main()
