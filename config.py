# config.py
"""
Central configuration file for game constants.
"""
import pygame

# --- Colors ---
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
VIOLET = (128, 0, 128)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ROSE = (255, 192, 203)  # Adjusted Rose color
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)

# --- Colors for systems (and possible player token colors) ---
SYSTEM_COLORS = [YELLOW, RED, VIOLET, ORANGE, GREEN, BLUE, ROSE]

# --- Screen Dimensions ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
INFO_PANEL_WIDTH = 200  # Largeur du panneau d'information

# --- Game Board ---
BOARD_SIZE_X = 24
BOARD_SIZE_Y = 24
CELL_SIZE = 25  # Taille de chaque cellule en pixels
GRID_WIDTH = BOARD_SIZE_X * CELL_SIZE
GRID_HEIGHT = BOARD_SIZE_Y * CELL_SIZE
BOARD_OFFSET_X = 50  # Décalage par rapport au bord gauche
BOARD_OFFSET_Y = 50  # Décalage par rapport au bord supérieur

# --- Systems ---
SYSTEM_SIZE = 2  # Les systèmes occupent 2x2 cellules
MIN_SYSTEM_DISTANCE = 3  # Distance minimale (en cellules, Chebyshev) entre centres de systèmes
NUM_CAPITAL_SYSTEMS = 7
NUM_PLANET_SYSTEMS = 8

# --- Player & Movement ---
MAX_TOTEMS_PER_PLAYER = 9
MOVEMENT_POINTS_PER_TURN = 4

# --- Factions & Totems ---
FACTION_NAMES = ["A", "B", "C", "D", "E", "F"]

# --- Game Rules ---
MAX_TURNS = 40  # Fin du jeu après ce nombre de tours

# --- Game States ---
STATE_RUNNING = "RUNNING"
STATE_GAME_OVER = "GAME_OVER"
STATE_PLAYER_TURN = "PLAYER_TURN"
STATE_WAITING_INPUT = "WAITING_INPUT"
STATE_MOVING = "MOVING"
