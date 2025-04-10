# main.py
"""
Main entry point for the Space Explore game.
Initializes Pygame, creates the Game object, and runs the main game loop.
"""
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, STATE_GAME_OVER
from core.game_logic import Game


def main():
    # Initialisation de Pygame
    pygame.init()
    pygame.font.init()  # Initialize font module

    # Paramètres de la fenêtre
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Explore MVP 1")
    clock = pygame.time.Clock()

    # Création de l'instance du jeu
    num_human_players = 1  # Mode solo
    game = Game(num_players=num_human_players)
    try:
        game.setup_game()
    except RuntimeError as e:
        print(f"Error during game setup: {e}")
        pygame.quit()
        return

    # Boucle principale du jeu
    running = True
    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Pass input events to the game logic if the game is running
            if game.game_state != STATE_GAME_OVER:
                game.handle_input(event)

        # Mise à jour de la logique du jeu
        game.update()

        # Effacer l'écran
        screen.fill(BLACK)

        # Dessiner le jeu complet
        game.draw(screen)

        # Mettre à jour l'affichage
        pygame.display.flip()

        # Limitation de la fréquence d'images
        clock.tick(30)  # 30 FPS

    pygame.quit()


if __name__ == "__main__":
    main()
