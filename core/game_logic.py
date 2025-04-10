# core/game_logic.py
"""
Contains the core game logic: Game state, Player, Vaisseau, Factions, Totems,
turn management, and actions for a single-player high-score game.
"""
import pygame
import random
import collections  # Pour BFS
import time  # Pour le timing non bloquant de l'observer
from config import (BOARD_SIZE_X, BOARD_SIZE_Y, CELL_SIZE, MOVEMENT_POINTS_PER_TURN,
                    MAX_TOTEMS_PER_PLAYER, SYSTEM_COLORS, FACTION_NAMES,
                    STATE_RUNNING, STATE_GAME_OVER, STATE_PLAYER_TURN, STATE_WAITING_INPUT,
                    BOARD_OFFSET_X, BOARD_OFFSET_Y, MAX_TURNS, ORIGIN_MARKER_COLOR, WHITE, RED, BLACK,
                    GRAY, YELLOW, VIOLET, ORANGE, GREEN, BLUE, ROSE, GRID_WIDTH)
from core.game_board import GameBoard, SystemePlanetaireCapitale, SystemePlanetairePlanete

# --- Faction Definitions ---
FACTIONS = {
    "A": {"nom": "ACTOS", "valeur": 80, "logo": "Losange"},
    "B": {"nom": "B.O.", "valeur": 1000, "logo": "Triangle"},
    "C": {"nom": "Confrerie Cursarius", "valeur": 750, "logo": "Clepsydre"},
    "D": {"nom": "Demos Vita", "valeur": 150, "logo": "Croix"},
    "E": {"nom": "Esperio Scientus", "valeur": 300, "logo": "Cercles"},
    "F": {"nom": "Frea Totis", "valeur": 500, "logo": "Carré"},
}

# --- Totem & Faction Card Distribution ---
SYSTEM_FACTION_DATA = {
    YELLOW: {"A": 6, "B": 1},
    RED: {"C": 2, "D": 5},
    VIOLET: {"E": 4, "F": 3},
    ORANGE: {"A": 4, "B": 1, "D": 1, "F": 1},
    GREEN: {"A": 3, "C": 1, "D": 1, "E": 2},
    BLUE: {"A": 1, "B": 1, "C": 1, "D": 2, "E": 1, "F": 1},
    ROSE: {"A": 4, "D": 2, "E": 1},
}

# --- Helper Function ---
def screen_to_grid(screen_pos):
    """Convertit les coordonnées pixels en coordonnées de grille."""
    x, y = screen_pos
    grid_x = (x - BOARD_OFFSET_X) // CELL_SIZE
    grid_y = (y - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= grid_x < BOARD_SIZE_X and 0 <= grid_y < BOARD_SIZE_Y:
        return (grid_x, grid_y)
    return None

# --- Classes ---
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
        color_name = [k for k, v in globals().items() if v == self.couleur]
        c_repr = color_name[0] if color_name else str(self.couleur)
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

class Player:
    """Représente le joueur (mode solo)."""
    def __init__(self, player_id, couleur):
        self.id = player_id
        self.couleur = couleur  # Couleur du vaisseau et du joueur
        self.origin_system_color = couleur  # Système d'origine (correspond à la couleur)
        self.vaisseau = None
        self.totems = []  # Liste des totems collectés
        self.score = 0

    def add_totem(self, totem):
        """Ajoute un totem à l'inventaire du joueur s'il y a de la place."""
        if len(self.totems) < MAX_TOTEMS_PER_PLAYER:
            self.totems.append(totem)
            print(f"Player collected {totem}")
            return True
        else:
            print("Inventory full.")
            return False

    def remove_totem(self, totem_to_remove):
        """Enlève un totem spécifique de l'inventaire du joueur."""
        if totem_to_remove in self.totems:
            self.totems.remove(totem_to_remove)
            print(f"Player deposited {totem_to_remove}")
            return True
        else:
            print("Totem not found in inventory.")
            return False

    def calculate_score(self):
        """Calcule le score du joueur en fonction des totems collectés et des bonus."""
        self.score = sum(totem.valeur for totem in self.totems)
        color_counts = {}
        faction_counts = {}
        for totem in self.totems:
            color_counts[totem.couleur] = color_counts.get(totem.couleur, 0) + 1
            faction_counts[totem.faction_id] = faction_counts.get(totem.faction_id, 0) + 1
        for count in color_counts.values():
            if count >= 3:
                self.score += 100
        for count in faction_counts.values():
            if count >= 3:
                self.score += 100
        return self.score

    def check_victory_conditions(self):
        """
        Vérifie si l'une des conditions de victoire est remplie.
        Retourne True si l'une des conditions est satisfaite.
        """
        if not self.totems:
            return False
        # Condition 1: Au moins un totem de chaque faction (A-F)
        collected_factions = {t.faction_id for t in self.totems}
        if len(collected_factions) == len(FACTION_NAMES):
            return True
        # Condition 2: Au moins un totem de chaque couleur (7 couleurs)
        collected_colors = {t.couleur for t in self.totems}
        if len(collected_colors) == len(SYSTEM_COLORS):
            return True
        # Condition 3: 3 totems de la même couleur, mais de 3 factions différentes
        color_groups = {}
        for totem in self.totems:
            color_groups.setdefault(totem.couleur, []).append(totem.faction_id)
        for factions in color_groups.values():
            if len(factions) >= 3 and len(set(factions)) >= 3:
                return True
        # Condition 4: 3 totems de la même faction, mais de 3 couleurs différentes
        faction_groups = {}
        for totem in self.totems:
            faction_groups.setdefault(totem.faction_id, []).append(totem.couleur)
        for colors in faction_groups.values():
            if len(colors) >= 3 and len(set(colors)) >= 3:
                return True
        return False

class Game:
    """Gère l'état global du jeu, les tours et les interactions."""
    def __init__(self, num_players=1):
        self.num_players = 1  # Mode solo
        self.game_board = GameBoard(BOARD_SIZE_X, BOARD_SIZE_Y)
        self.players = []
        self.game_state = STATE_RUNNING
        self.winner = None
        self.turn_count = 0

        # Flags pour actions par tour
        self.action_recolter_used = False
        self.action_deposer_used = False
        self.action_influencer_used = False
        self.action_observer_used = False
        self.movement_used = False

        # Mode Observer non bloquant
        self.observer_mode = False
        self.observer_system = None
        self.observer_start_time = None

        # Racks pour totems et cartes faction
        self.system_racks = {}
        self._initialize_racks()

        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.player_origin_system_pos = None

    def _initialize_racks(self):
        """Initialise les racks pour chaque couleur avec totems et cartes faction."""
        self.system_racks = {color: {'totems': [], 'faction_cards': []} for color in SYSTEM_COLORS}
        for color, faction_data in SYSTEM_FACTION_DATA.items():
            for faction_id in faction_data.keys():
                for _ in range(3):
                    self.system_racks[color]['totems'].append(Totem(faction_id, color))
            for faction_id, count in faction_data.items():
                for _ in range(count):
                    self.system_racks[color]['faction_cards'].append(FactionCard(faction_id, color))
            random.shuffle(self.system_racks[color]['faction_cards'])

    def setup_game(self):
        """Initialise le plateau, le joueur et le positionnement de départ."""
        print("Setting up game (Single Player)...")
        # Choix aléatoire de la couleur du joueur parmi SYSTEM_COLORS
        player_color = random.choice(SYSTEM_COLORS)
        # Création des systèmes Capitale et marquage du système d'origine
        capital_systems = []
        for color in SYSTEM_COLORS:
            sys = SystemePlanetaireCapitale(color)
            if color == player_color:
                sys.is_player_origin = True
                print(f"Marked {color} as player origin.")
            capital_systems.append(sys)
        planet_systems = [SystemePlanetairePlanete(random.choice(SYSTEM_COLORS)) for _ in range(8)]
        # Placement des systèmes sur le plateau
        self.game_board.place_initial_systems(capital_systems, planet_systems)
        for sys in self.game_board.systems:
            if getattr(sys, 'is_player_origin', False):
                self.player_origin_system_pos = sys.position
                print(f"Player origin system located at {self.player_origin_system_pos}")
                break
        # Création du joueur
        self.players = [Player(0, player_color)]
        # Placement initial du vaisseau sur un système choisi aléatoirement
        available_systems = self.game_board.systems[:]
        random.shuffle(available_systems)
        if not available_systems:
            raise RuntimeError("Not enough systems placed to assign starting position.")
        player = self.get_player()
        start_system = available_systems.pop(0)
        start_pos = start_system.position
        player.vaisseau = Vaisseau(start_pos, player.couleur)
        print(f"Player ({player.couleur}) starts at system {start_system.position} (Color: {start_system.couleur})")
        self.game_board.reveal_system(start_pos)
        self._reveal_faction_card(start_system.couleur)
        self.start_turn()
        print(f"\nGame setup complete. Turn {self.turn_count}.")

    def _reveal_faction_card(self, system_color):
        """Révèle la carte Relation-Faction du rack correspondant à la couleur donnée."""
        rack = self.system_racks.get(system_color)
        if rack and rack['faction_cards']:
            card = rack['faction_cards'][0]
            print(f"  Rack {system_color}: Top Faction Card revealed -> {card.faction_id}")
        else:
            print(f"  Rack {system_color}: No faction cards to reveal.")

    def get_player(self):
        """Retourne l'objet joueur (mode solo)."""
        return self.players[0]

    def start_turn(self):
        """Prépare le début du tour en réinitialisant les états."""
        self.turn_count += 1
        player = self.get_player()
        player.vaisseau.reset_movement_points()
        self.action_recolter_used = False
        self.action_deposer_used = False
        self.action_influencer_used = False
        self.action_observer_used = False
        self.movement_used = False
        self.observer_mode = False
        self.observer_system = None
        self.observer_start_time = None
        self.game_state = STATE_PLAYER_TURN
        print(f"\n--- Turn {self.turn_count}/{MAX_TURNS} ---")
        if self.check_game_over():
            return

    def end_turn(self):
        """Termine le tour courant et en débute un nouveau."""
        if self.game_state != STATE_PLAYER_TURN:
            return
        print("Ending turn.")
        self.start_turn()

    def find_path(self, start_pos, end_pos, max_dist):
        """
        Recherche un chemin entre start_pos et end_pos en utilisant BFS.
        Refuse les déplacements qui restent à l'intérieur des 4 cases d'un même système.
        """
        # Vérifier si start et end appartiennent au même système
        start_system = self.game_board.get_system_at(start_pos)
        end_system = self.game_board.get_system_at(end_pos)
        if start_system and end_system and start_system == end_system:
            print("Déplacement interne au même système interdit. Ignoré.")
            return None

        if start_pos == end_pos:
            return [start_pos]

        q = collections.deque([(start_pos, [start_pos])])
        visited = {start_pos}
        while q:
            (current_pos, path) = q.popleft()
            current_dist = len(path) - 1
            if current_dist >= max_dist:
                continue
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    next_pos = (current_pos[0] + dx, current_pos[1] + dy)
                    # Refuser le déplacement interne si next_pos appartient au même système que start_pos
                    if start_system and self.game_board.get_system_at(next_pos) == start_system:
                        continue
                    if next_pos == end_pos:
                        return path + [next_pos]
                    if self.game_board.is_position_valid(next_pos) and next_pos not in visited:
                        visited.add(next_pos)
                        q.append((next_pos, path + [next_pos]))
        return None

    def handle_mouse_click(self, mouse_pos):
        """
        Désactivation du déplacement par souris.
        Seul le mode Observer (sélection d'un système caché) reste actif.
        """
        if self.observer_mode:
            self.observer_select_system(mouse_pos)
        else:
            # Ignorer les clics de souris pour le déplacement.
            print("Déplacement par souris désactivé.")

    def observer_select_system(self, mouse_pos):
        """
        Sélectionne un système caché en mode Observer.
        La révélation est temporaire (2 secondes) via un système non bloquant.
        """
        target_grid_pos = screen_to_grid(mouse_pos)
        if target_grid_pos is None:
            print("Observer: Click outside board.")
            return
        system = self.game_board.get_system_at(target_grid_pos)
        if not system:
            print("Observer: No system at clicked position.")
            return
        if system.revealed:
            print("Observer: System already revealed.")
            return
        system.revealed = True
        self.observer_system = system
        self.observer_start_time = time.time()
        print(f"Observer: Revealing system at {target_grid_pos} temporarily.")

    def handle_input(self, event):
        """Traite les événements d'entrée (clavier uniquement pour le déplacement)."""
        if self.game_state != STATE_PLAYER_TURN:
            return
        player = self.get_player()
        ship = player.vaisseau
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Désactivation de la gestion du clic pour le déplacement
            if event.button == 1:
                self.handle_mouse_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            movement_keys = {
                pygame.K_UP: (0, -1),
                pygame.K_DOWN: (0, 1),
                pygame.K_LEFT: (-1, 0),
                pygame.K_RIGHT: (1, 0),
                pygame.K_KP1: (-1, 1),
                pygame.K_KP2: (0, 1),
                pygame.K_KP3: (1, 1),
                pygame.K_KP4: (-1, 0),
                pygame.K_KP6: (1, 0),
                pygame.K_KP7: (-1, -1),
                pygame.K_KP8: (0, -1),
                pygame.K_KP9: (1, -1),
            }
            if event.key in movement_keys:
                dx, dy = movement_keys[event.key]
                if not self.movement_used:
                    cost = 1
                    target_pos = (ship.position[0] + dx, ship.position[1] + dy)
                    # Vérifier que le déplacement ne reste pas dans le même système
                    if self.game_board.get_system_at(ship.position) and \
                       self.game_board.get_system_at(target_pos) == self.game_board.get_system_at(ship.position):
                        print("Déplacement interne au même système interdit. Ignoré.")
                    elif ship.movement_points_remaining >= cost and self.game_board.is_position_valid(target_pos):
                        stop_early = ship.move_step(target_pos, cost, self.game_board)
                        if stop_early:
                            system = self.game_board.get_system_at(ship.position)
                            if system:
                                self._reveal_faction_card(system.couleur)
                            self.movement_used = True
                    else:
                        print("Invalid step (boundary or insufficient points).")
                else:
                    print("Already moved this turn.")
            elif event.key == pygame.K_r:
                if not self.action_recolter_used and self.action_recolter(player):
                    self.action_recolter_used = True
                else:
                    print("Action Récolter déjà utilisée ce tour.")
            elif event.key == pygame.K_d:
                if player.totems:
                    if not self.action_deposer_used and self.action_deposer(player, player.totems[0]):
                        self.action_deposer_used = True
                    else:
                        print("Action Déposer déjà utilisée ce tour.")
                else:
                    print("No totems to deposit.")
            elif event.key == pygame.K_i:
                if not self.action_influencer_used and self.action_influencer(player):
                    self.action_influencer_used = True
                else:
                    print("Action Influencer déjà utilisée ce tour.")
            elif event.key == pygame.K_o:
                hidden_systems = [s for s in self.game_board.systems if not s.revealed]
                if not hidden_systems:
                    print("Observer: Aucun système caché disponible.")
                else:
                    print("Mode Observer activé : Cliquez sur un système caché.")
                    self.observer_mode = True
            elif event.key == pygame.K_SPACE:
                self.end_turn()

    def action_recolter(self, player):
        """Permet au joueur de récolter un totem sur le système courant."""
        ship_pos = player.vaisseau.position
        system = self.game_board.get_system_at(ship_pos)
        if not system or not system.revealed:
            print("Action Récolter: Not on a revealed system.")
            return False
        rack = self.system_racks.get(system.couleur)
        if not rack or not rack['faction_cards']:
            print(f"Action Récolter: No faction cards in rack for color {system.couleur}.")
            return False
        current_faction_id = rack['faction_cards'][0].faction_id
        totem_to_collect = next((t for t in rack['totems'] if t.faction_id == current_faction_id), None)
        if not totem_to_collect:
            print(f"Action Récolter: No totems of faction {current_faction_id} available in rack {system.couleur}.")
            return False
        if player.add_totem(totem_to_collect):
            rack['totems'].remove(totem_to_collect)
            print(f"Action Récolter successful: Player took {totem_to_collect} from rack {system.couleur}")
            return True
        return False

    def action_deposer(self, player, totem_to_deposit):
        """Permet au joueur de déposer un totem sur le système courant."""
        ship_pos = player.vaisseau.position
        system = self.game_board.get_system_at(ship_pos)
        if not system or not system.revealed:
            print("Action Déposer: Not on a revealed system.")
            return False
        rack = self.system_racks.get(system.couleur)
        if rack is None:
            return False
        if player.remove_totem(totem_to_deposit):
            rack['totems'].append(totem_to_deposit)
            print(f"Action Déposer successful: Player deposited {totem_to_deposit} into rack {system.couleur}")
            return True
        return False

    def action_influencer(self, player):
        """Permet au joueur d'influencer la carte Relation-Faction sur un système capitale révélé."""
        ship_pos = player.vaisseau.position
        system = self.game_board.get_system_at(ship_pos)
        if not system or not system.revealed or not system.est_capitale:
            print("Action Influencer: Not on a revealed Capital system.")
            return False
        rack = self.system_racks.get(system.couleur)
        if not rack or len(rack['faction_cards']) <= 1:
            print(f"Action Influencer: Not enough cards in rack {system.couleur} to cycle.")
            return False
        top_card = rack['faction_cards'].pop(0)
        rack['faction_cards'].append(top_card)
        new_top_faction = rack['faction_cards'][0].faction_id
        print(f"Action Influencer successful: New top faction for {system.couleur}: {new_top_faction}")
        self._reveal_faction_card(system.couleur)
        return True

    def update(self):
        """Mets à jour l'état du jeu et gère le mode Observer non bloquant."""
        if self.observer_mode and self.observer_system and self.observer_start_time:
            if time.time() - self.observer_start_time >= 2:
                self.observer_system.revealed = False
                print(f"Observer: Hiding system at {self.observer_system.position} after temporary reveal.")
                self.observer_mode = False
                self.action_observer_used = True
                self.observer_system = None
                self.observer_start_time = None

    def draw_ui(self, surface):
        """Dessine l'interface utilisateur avec infos détaillées pour le joueur."""
        player = self.get_player()
        ship = player.vaisseau
        y_offset = 10
        x_offset = GRID_WIDTH + BOARD_OFFSET_X + 10  # Début du panneau d'information

        turn_text = self.font.render(f"Turn: {self.turn_count}/{MAX_TURNS}", True, WHITE)
        surface.blit(turn_text, (x_offset, y_offset))
        y_offset += 30

        coord_text = self.font.render(f"Position: ({ship.position[0]}, {ship.position[1]})", True, WHITE)
        surface.blit(coord_text, (x_offset, y_offset))
        y_offset += 20

        move_text = self.font.render(f"Move Pts: {ship.movement_points_remaining}/{MOVEMENT_POINTS_PER_TURN}", True, WHITE)
        surface.blit(move_text, (x_offset, y_offset))
        y_offset += 20

        total_value = sum(totem.valeur for totem in player.totems)
        score_text = self.font.render(f"Score: {player.calculate_score()} (Totems: {total_value})", True, WHITE)
        surface.blit(score_text, (x_offset, y_offset))
        y_offset += 30

        totem_title = self.font.render(f"Totems ({len(player.totems)}/{MAX_TOTEMS_PER_PLAYER}):", True, WHITE)
        surface.blit(totem_title, (x_offset, y_offset))
        y_offset += 20
        for i, totem in enumerate(player.totems):
            color_name = [k for k, v in globals().items() if v == totem.couleur]
            c_repr = color_name[0] if color_name else f"C{totem.couleur}"
            totem_repr = f" - {totem.faction_id} ({c_repr})"
            try:
                totem_surf = self.font_small.render(totem_repr, True, totem.couleur)
            except TypeError:
                totem_surf = self.font_small.render(totem_repr, True, WHITE)
            surface.blit(totem_surf, (x_offset + 5, y_offset))
            y_offset += 16
            if i >= 8: break
        y_offset += 10

        player_info = self.font_small.render(f"Votre Couleur: {player.couleur}", True, WHITE)
        surface.blit(player_info, (x_offset, y_offset))
        y_offset += 16
        victory_met = player.check_victory_conditions()
        victory_text = "Conditions Remplies: OUI" if victory_met else "Conditions Remplies: NON"
        victory_info = self.font_small.render(victory_text, True, GREEN if victory_met else RED)
        surface.blit(victory_info, (x_offset, y_offset))
        y_offset += 30

        y_start_actions = y_offset
        action_title = self.font_small.render("Actions (Utilisées):", True, WHITE)
        surface.blit(action_title, (x_offset, y_offset))
        y_offset += 16
        actions_status = [
            (f"R: Recolter", self.action_recolter_used),
            (f"D: Deposer", self.action_deposer_used),
            (f"I: Influencer", self.action_influencer_used),
            (f"O: Observer", self.action_observer_used or self.observer_mode),
            (f"Move", self.movement_used),
        ]
        for text, used in actions_status:
            color = GRAY if used else WHITE
            status_surf = self.font_small.render(text, True, color)
            surface.blit(status_surf, (x_offset + 5, y_offset))
            y_offset += 16

        y_offset = y_start_actions
        x_offset_help = x_offset + 100
        help_text = [
            "Contrôles:",
            " Clavier: Déplacement",
            " R/D/I/O: Actions",
            " ESPACE: Fin Tour"
        ]
        for line in help_text:
            help_surf = self.font_small.render(line, True, GRAY)
            surface.blit(help_surf, (x_offset_help, y_offset))
            y_offset += 16

        if self.game_state == STATE_GAME_OVER:
            go_font = pygame.font.Font(None, 50)
            go_text_1 = go_font.render("GAME OVER", True, RED)
            score_font = pygame.font.Font(None, 40)
            final_score = player.calculate_score()
            go_text_2 = score_font.render(f"Score Final: {final_score}", True, WHITE)
            center_x = BOARD_OFFSET_X + (BOARD_SIZE_X * CELL_SIZE) // 2
            center_y = BOARD_OFFSET_Y + (BOARD_SIZE_Y * CELL_SIZE) // 2
            rect1 = go_text_1.get_rect(center=(center_x, center_y - 20))
            rect2 = go_text_2.get_rect(center=(center_x, center_y + 20))
            bg_rect = rect1.union(rect2).inflate(40, 40)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, WHITE, bg_rect, 2)
            surface.blit(go_text_1, rect1)
            surface.blit(go_text_2, rect2)

    def draw(self, surface):
        """Dessine l'ensemble de l'état du jeu."""
        self.game_board.draw(surface)
        player = self.get_player()
        if player.vaisseau:
            player.vaisseau.draw(surface)
        self.draw_ui(surface)

    def check_game_over(self):
        """
        Vérifie les conditions de fin de partie.
        Fin automatique si le tour maximal est dépassé
        ou si le joueur est sur son système d'origine et remplit une condition de victoire.
        """
        if self.turn_count > MAX_TURNS:
            if self.game_state != STATE_GAME_OVER:
                self.game_state = STATE_GAME_OVER
                print(f"\n!!! GAME OVER !!! Turn limit ({MAX_TURNS}) reached!")
                self._calculate_final_scores()
            return True
        player = self.get_player()
        ship_pos = player.vaisseau.position
        system = self.game_board.get_system_at(ship_pos)
        if system and system.est_capitale and system.couleur == player.origin_system_color:
            if player.check_victory_conditions():
                self.game_state = STATE_GAME_OVER
                print(f"\n!!! VICTORY CONDITION MET !!! Player reached Origin System with winning totems!")
                self._calculate_final_scores()
                return True
        return False

    def _calculate_final_scores(self):
        """Calcule et affiche le score final du joueur."""
        print("\n--- Final Score ---")
        player = self.get_player()
        score = player.calculate_score()
        print(f"Player {player.id}: {score} points in {self.turn_count - 1} turns.")
