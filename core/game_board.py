# core/game_board.py
"""
Manages the game board, systems, and their placement and drawing.
"""
import pygame
import random
from config import (CELL_SIZE, SYSTEM_SIZE,
                    MIN_SYSTEM_DISTANCE, WHITE, GRAY, DARK_GRAY,
                    BOARD_OFFSET_X, BOARD_OFFSET_Y, YELLOW, BLACK, RED)


class GameBoard:
    """Represents the game board grid and the systems placed on it."""

    def __init__(self, size_x, size_y):
        # La grille peut être utilisée pour des calculs futurs (pathfinding, collisions)
        self.grid = [[None for _ in range(size_y)] for _ in range(size_x)]
        self.systems = []  # Liste des objets SystemePlanetaire
        self.size_x = size_x
        self.size_y = size_y
        self.font = pygame.font.Font(None, 16)  # Pour dessiner des textes (optionnel)

    def place_system(self, systeme, position):
        """
        Place un système sur le plateau. Met à jour la position du système
        et l'ajoute à la liste des systèmes.
        """
        if self.is_position_valid(position):
            systeme.position = position
            self.systems.append(systeme)
            # Marquer la cellule en haut à gauche dans la grille (optionnel)
            self.grid[position[0]][position[1]] = systeme
            return True
        return False

    def is_position_valid(self, position):
        """Vérifie que la position est dans les limites du plateau."""
        x, y = position
        return 0 <= x < self.size_x and 0 <= y < self.size_y

    def get_system_at(self, position):
        """
        Renvoie le système occupant la case donnée, si présent.
        Puisque les systèmes sont de 2x2, on vérifie s'ils couvrent la case.
        """
        for system in self.systems:
            if system.position:
                sx, sy = system.position
                if sx <= position[0] < sx + SYSTEM_SIZE and \
                        sy <= position[1] < sy + SYSTEM_SIZE:
                    return system
        return None

    def get_all_system_positions(self):
        """Renvoie l'ensemble des cellules occupées par les systèmes."""
        occupied = set()
        for system in self.systems:
            if system.position:
                sx, sy = system.position
                for dx in range(SYSTEM_SIZE):
                    for dy in range(SYSTEM_SIZE):
                        occupied.add((sx + dx, sy + dy))
        return occupied

    def check_distance_rule(self, potential_pos):
        """
        Vérifie que le placement d'un système à potential_pos respecte la
        règle de distance minimale (distance Chebyshev entre centres >= MIN_SYSTEM_DISTANCE).
        """
        center_x1 = potential_pos[0] + SYSTEM_SIZE / 2.0
        center_y1 = potential_pos[1] + SYSTEM_SIZE / 2.0

        for existing_system in self.systems:
            if existing_system.position:
                ex, ey = existing_system.position
                center_x2 = ex + SYSTEM_SIZE / 2.0
                center_y2 = ey + SYSTEM_SIZE / 2.0
                distance = max(abs(center_x1 - center_x2), abs(center_y1 - center_y2))
                if distance < MIN_SYSTEM_DISTANCE:
                    return False
        return True

    def place_initial_systems(self, capital_systems, planet_systems):
        """
        Place les systèmes Capitale et Planète de manière aléatoire en respectant
        les règles de placement (distance et marges).
        """
        systems_to_place = capital_systems + planet_systems
        random.shuffle(systems_to_place)
        self.systems = []  # Réinitialiser la liste

        possible_positions = []
        for x in range(2, self.size_x - SYSTEM_SIZE):
            for y in range(2, self.size_y - SYSTEM_SIZE):
                possible_positions.append((x, y))
        random.shuffle(possible_positions)

        placed_count = 0
        for system in systems_to_place:
            placed = False
            current_possible = possible_positions[:]  # Copie temporaire
            while current_possible and not placed:
                position = current_possible.pop(0)
                if self.check_distance_rule(position):
                    self.place_system(system, position)
                    placed = True
                    placed_count += 1
                    if position in possible_positions:
                        possible_positions.remove(position)
            if not placed:
                print(f"Warning: Could not place system {system}.")

        print(f"Successfully placed {placed_count} out of {len(systems_to_place)} systems.")

    def reveal_system(self, position):
        """Révèle un système à la position donnée."""
        system = self.get_system_at(position)
        if system and not system.revealed:
            system.revealed = True
            print(
                f"System at {system.position} revealed: Color {system.couleur}, Type: {'Capitale' if system.est_capitale else 'Planete'}")
            return system
        return None

    def draw(self, surface):
        """Dessine les lignes de la grille et tous les systèmes placés."""
        # Dessiner la grille
        for x in range(self.size_x + 1):
            start_pos = (BOARD_OFFSET_X + x * CELL_SIZE, BOARD_OFFSET_Y)
            end_pos = (BOARD_OFFSET_X + x * CELL_SIZE, BOARD_OFFSET_Y + self.size_y * CELL_SIZE)
            pygame.draw.line(surface, GRAY, start_pos, end_pos)
        for y in range(self.size_y + 1):
            start_pos = (BOARD_OFFSET_X, BOARD_OFFSET_Y + y * CELL_SIZE)
            end_pos = (BOARD_OFFSET_X + self.size_x * CELL_SIZE, BOARD_OFFSET_Y + y * CELL_SIZE)
            pygame.draw.line(surface, GRAY, start_pos, end_pos)

        # Dessiner les systèmes
        for system in self.systems:
            system.draw(surface, self.font)


# --- System Classes ---

class SystemePlanetaire:
    """Classe de base pour les systèmes planétaires."""

    def __init__(self, couleur):
        self.position = None  # Position en haut à gauche sur la grille
        self.couleur = couleur
        self.size = (SYSTEM_SIZE, SYSTEM_SIZE)
        self.revealed = False
        self.est_capitale = False  # Par défaut, pas une capitale

    def draw(self, surface, font):
        """Dessine le système."""
        if self.position:
            px = BOARD_OFFSET_X + self.position[0] * CELL_SIZE
            py = BOARD_OFFSET_Y + self.position[1] * CELL_SIZE
            width = self.size[0] * CELL_SIZE
            height = self.size[1] * CELL_SIZE
            rect = pygame.Rect(px, py, width, height)

            if self.revealed:
                pygame.draw.rect(surface, self.couleur, rect)
                pygame.draw.rect(surface, WHITE, rect, 1)
            else:
                pygame.draw.rect(surface, DARK_GRAY, rect)
                pygame.draw.rect(surface, GRAY, rect, 1)


class SystemePlanetaireCapitale(SystemePlanetaire):
    """Représente un système planétaire Capitale."""

    def __init__(self, couleur):
        super().__init__(couleur)
        self.est_capitale = True
        self.is_player_origin = False  # Sera marqué si c'est le système d'origine du joueur

    def draw(self, surface, font):
        """Dessine le système Capitale avec un marqueur spécial si c'est l'origine du joueur."""
        super().draw(surface, font)
        if self.position and self.revealed:
            px = BOARD_OFFSET_X + self.position[0] * CELL_SIZE
            py = BOARD_OFFSET_Y + self.position[1] * CELL_SIZE
            center_x = px + SYSTEM_SIZE * CELL_SIZE // 2
            center_y = py + SYSTEM_SIZE * CELL_SIZE // 2
            # Marqueur de base : une étoile jaune
            pygame.draw.circle(surface, YELLOW, (center_x, center_y), CELL_SIZE // 3)
            pygame.draw.circle(surface, BLACK, (center_x, center_y), CELL_SIZE // 3, 1)
            # Si c'est le système d'origine du joueur, ajouter un signe distinctif (ex. double encadrement rouge)
            if getattr(self, 'is_player_origin', False):
                outline_rect = pygame.Rect(px - 2, py - 2, SYSTEM_SIZE * CELL_SIZE + 4, SYSTEM_SIZE * CELL_SIZE + 4)
                pygame.draw.rect(surface, RED, outline_rect, 3)


class SystemePlanetairePlanete(SystemePlanetaire):
    """Représente un système planétaire non-capitale."""

    def __init__(self, couleur):
        super().__init__(couleur)
        self.est_capitale = False

    def draw(self, surface, font):
        """Dessine un système Planète."""
        super().draw(surface, font)
