# core/game_board.py
"""
Manages the game board, systems, and their placement and drawing.
"""
import pygame
import random
from core.game_board import GameBoard, SystemePlanetaireCapitale, SystemePlanetairePlanete

from config import (CELL_SIZE, MOVEMENT_POINTS_PER_TURN,
                    WHITE, FACTIONS,
                    BOARD_OFFSET_X, BOARD_OFFSET_Y, COLOR_NAME_MAP)


class Totem:
    """Représente un totem appartenant à une faction et couleur spécifiques."""

    def __init__(self, faction_id, couleur):
        if faction_id not in FACTIONS:
            raise ValueError(f"Invalid faction ID: {faction_id}")
        self.faction_id = faction_id  # e.g., "A", "B"
        self.couleur = couleur  # Couleur du système d'où il provient
        self.valeur = FACTIONS[faction_id]["valeur"]
        self.nom = FACTIONS[faction_id]["nom"]
        self.logo = FACTIONS[faction_id]["logo"]

    def __repr__(self):
            c_repr = COLOR_NAME_MAP.get(self.couleur, str(self.couleur))
            return f"Totem({self.faction_id}, {c_repr})"


class FactionCard:
    """Représente une carte 'Relation-Faction'."""

    def __init__(self, faction_id, system_color):
        self.faction_id = faction_id
        self.system_color = system_color

    def __repr__(self):
        color_name = [k for k, v in globals().items() if v == self.system_color]
        c_repr = color_name[0] if color_name else str(self.system_color)
        return f"Card({self.faction_id}, {c_repr})"


class Vaisseau:
    """Représente le vaisseau du joueur."""

    def __init__(self, position, couleur):
        self.position = position  # Coordonnées en grille
        self.couleur = couleur
        self.movement_points_remaining = MOVEMENT_POINTS_PER_TURN

    def reset_movement_points(self):
        """Réinitialise les points de mouvement au début du tour."""
        self.movement_points_remaining = MOVEMENT_POINTS_PER_TURN

    def move_step(self, new_pos, cost, game_board):
        """
        Déplace le vaisseau d'une étape, déduit le coût,
        et vérifie l'entrée dans un système.
        Retourne True si le mouvement doit s'arrêter.
        """
        self.position = new_pos
        self.movement_points_remaining -= cost
        print(f"Moved to {self.position}. Points left: {self.movement_points_remaining}")
        system = game_board.get_system_at(self.position)
        if system:
            print(f"Entered system at {self.position}. Movement ends.")
            self.movement_points_remaining = 0
            game_board.reveal_system(self.position)
            # Révélation simultanée de la Carte Relation-Faction sera gérée par Game.
            return True
        return False

    def draw(self, surface):
        """Dessine le vaisseau sur le plateau."""
        px = BOARD_OFFSET_X + self.position[0] * CELL_SIZE + CELL_SIZE // 2
        py = BOARD_OFFSET_Y + self.position[1] * CELL_SIZE + CELL_SIZE // 2
        radius = CELL_SIZE // 2 - 2
        pygame.draw.circle(surface, self.couleur, (px, py), radius)
        pygame.draw.circle(surface, WHITE, (px, py), radius, 1)

