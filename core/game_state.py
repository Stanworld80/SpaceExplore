
import pygame
import random
import collections  # Pour BFS
import time  # Pour le timing non bloquant de l'observer
from config import (STATE_GAME_OVER,BOARD_SIZE_X, BOARD_SIZE_Y, CELL_SIZE, FACTION_NAMES, WHITE,NUM_PLANET_SYSTEMS,MAX_TURNS, GREEN, GRAY,MOVEMENT_POINTS_PER_TURN,MAX_TOTEMS_PER_PLAYER,
                    BOARD_OFFSET_X, BOARD_OFFSET_Y, BLACK, RED,SYSTEM_COLORS,STATE_RUNNING,SYSTEM_FACTION_DATA,STATE_PLAYER_TURN,GRID_WIDTH)
from core.game_board import GameBoard, SystemePlanetaireCapitale, SystemePlanetairePlanete
from utils import get_color_name
from .game_entities import (Totem, FactionCard,Vaisseau )


# --- Helper Function ---
def screen_to_grid(screen_pos):
    """Convertit les coordonnées pixels en coordonnées de grille."""
    x, y = screen_pos
    grid_x = (x - BOARD_OFFSET_X) // CELL_SIZE
    grid_y = (y - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= grid_x < BOARD_SIZE_X and 0 <= grid_y < BOARD_SIZE_Y:
        return grid_x, grid_y
    return None


class Player:
    """Représente le joueur (mode solo)."""

    def __init__(self, player_id, couleur):
        self.id = player_id
        self.couleur = couleur  # Couleur du vaisseau et du joueur
        self.origin_system_color = couleur  # Système d'origine (correspond à la couleur)
        self.vaisseau = None
        self.totems = []  # Liste des totems collectés
        self.score = 5000

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
        """Calcule les points des totems + bonus, sans réinitialiser le score global."""
        score_totems = sum(t.valeur for t in self.totems)

        color_counts = {}
        faction_counts = {}
        for t in self.totems:
            color_counts[t.couleur] = color_counts.get(t.couleur, 0) + 1
            faction_counts[t.faction_id] = faction_counts.get(t.faction_id, 0) + 1

        bonus = 0
        bonus += sum(1000 for c in color_counts.values() if c >= 3)
        bonus += sum(10.0 for f in faction_counts.values() if f >= 3)

        return score_totems + bonus

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
        planet_systems = [SystemePlanetairePlanete(random.choice(SYSTEM_COLORS)) for _ in range(NUM_PLANET_SYSTEMS)]
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
        """Fin du tour du joueur : pénalité de score et passage au tour suivant."""
        if self.game_state != STATE_PLAYER_TURN:
            return
        player = self.get_player()

        # Appliquer la pénalité
        player.score = max(0, player.score - 200)
        print(f"Pénalité de fin de tour : -200 points. Score actuel : {player.score}")

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
            print("Déplacement par souris désactivé.")

    def observer_select_system(self, mouse_pos):
        """
        Mode Observer : sélection unique d’un système caché,
        affiché temporairement (2 sec), une seule fois par tour.
        """
        if self.action_observer_used:
            print("Observer: Action déjà utilisée ce tour.")
            return
        if self.observer_system is not None:
            print("Observer: Observation en cours.")
            return

        target_grid_pos = screen_to_grid(mouse_pos)
        if target_grid_pos is None:
            print("Observer: Clic hors du plateau.")
            return

        system = self.game_board.get_system_at(target_grid_pos)
        if not system or system.revealed:
            print("Observer: Système invalide ou déjà révélé.")
            return

        # Révélation temporaire
        system.revealed = True
        self.observer_system = system
        self.observer_start_time = time.time()
        self.action_observer_used = True  # Verrouille l'action pour le tour
        self.observer_mode = False  # Sort du mode observer immédiatement
        print(f"Observer: Système temporairement révélé à {target_grid_pos}.")

    def handle_input(self, event):
        """
        Traite les événements d'entrée (clavier uniquement pour le déplacement).
        La souris est désactivée pour le déplacement.
        """
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
                # Observer ne peut être exécuté qu'une seule fois par tour.
                if self.action_observer_used:
                    print("Action Observer déjà utilisée ce tour.")
                else:
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
        """Mise à jour du jeu, y compris la gestion du retour en mode caché de l'observer."""
        if self.observer_system and self.observer_start_time:
            if time.time() - self.observer_start_time >= 2:
                self.observer_system.revealed = False
                print(f"Observer: Masquage du système à {self.observer_system.position}.")
                self.observer_system = None
                self.observer_start_time = None

    def draw_ui(self, surface):
        """Dessine l'interface utilisateur avec infos détaillées pour le joueur et les systèmes révélés."""
        player = self.get_player()
        ship = player.vaisseau
        y_offset = 10
        x_offset = GRID_WIDTH + BOARD_OFFSET_X + 10  # Panneau d'information

        # Informations du joueur
        turn_text = self.font.render(f"Turn: {self.turn_count}/{MAX_TURNS}", True, WHITE)
        surface.blit(turn_text, (x_offset, y_offset))
        y_offset += 30

        coord_text = self.font.render(f"Position: ({ship.position[0]}, {ship.position[1]})", True, WHITE)
        surface.blit(coord_text, (x_offset, y_offset))
        y_offset += 20

        move_text = self.font.render(f"Move Pts: {ship.movement_points_remaining}/{MOVEMENT_POINTS_PER_TURN}", True,
                                     WHITE)
        surface.blit(move_text, (x_offset, y_offset))
        y_offset += 20

        base = player.score
        bonus = player.calculate_score()
        total_score = base + bonus
        score_text = self.font.render(f"Score: {total_score} (Base: {base}, Bonus: {bonus})", True, WHITE)
        surface.blit(score_text, (x_offset, y_offset))
        y_offset += 30

        # Affichage des totems collectés
        totem_title = self.font.render(f"Totems ({len(player.totems)}/{MAX_TOTEMS_PER_PLAYER}):", True, WHITE)
        surface.blit(totem_title, (x_offset, y_offset))
        y_offset += 20
        for i, totem in enumerate(player.totems):
            # Utilisation de la fonction get_color_name pour obtenir le nom de la couleur
            c_repr = get_color_name(totem.couleur)
            totem_repr = f" - {totem.faction_id} ({c_repr})"
            try:
                totem_surf = self.font_small.render(totem_repr, True, totem.couleur)
            except TypeError:
                totem_surf = self.font_small.render(totem_repr, True, WHITE)
            surface.blit(totem_surf, (x_offset + 5, y_offset))
            y_offset += 16
            # Limiter l'affichage si nécessaire (ici on n'affiche que les 9 premiers)
            if i >= 8: break
        y_offset += 10

        # Affichage des informations personnelles du joueur
        player_info = self.font_small.render(f"Votre Couleur: {get_color_name(player.couleur)}", True, player.couleur)
        surface.blit(player_info, (x_offset, y_offset))
        y_offset += 16

        victory_met = player.check_victory_conditions()
        victory_text = "Conditions Remplies: OUI" if victory_met else "Conditions Remplies: NON"
        victory_info = self.font_small.render(victory_text, True, GREEN if victory_met else RED)
        surface.blit(victory_info, (x_offset, y_offset))
        y_offset += 30

        # Informations sur les systèmes révélés pour chaque couleur
        header = self.font_small.render("Systèmes:", True, WHITE)
        surface.blit(header, (x_offset, y_offset))
        y_offset += 16
        for color in SYSTEM_COLORS:
            color_name = get_color_name(color)
            revealed = any(system.est_capitale and system.couleur == color and system.revealed
                           for system in self.game_board.systems)

            if revealed:
                rack = self.system_racks.get(color)
                faction_cards = rack['faction_cards'] if rack else []
                totems = rack['totems'] if rack else []

                top_faction = faction_cards[0].faction_id if faction_cards else "N/A"

                # Rendu du préfixe : "YELLOW : A -"
                prefix_text = f"{color_name}: {top_faction} - "
                prefix_surf = self.font_small.render(prefix_text, True, WHITE)
                surface.blit(prefix_surf, (x_offset + 5, y_offset))

                # Affichage de chaque lettre avec la couleur du système
                letter_x = x_offset + 5 + prefix_surf.get_width()
                for t in totems:
                    faction_letter = self.font_small.render(t.faction_id, True, t.couleur)
                    surface.blit(faction_letter, (letter_x, y_offset))
                    letter_x += faction_letter.get_width() + 1
            else:
                info_text = f"{color_name}: non-révélé"
                info_surf = self.font_small.render(info_text, True, WHITE)
                surface.blit(info_surf, (x_offset + 5, y_offset))

            y_offset += 16

        # Statut des actions utilisées ce tour
        y_start_actions = y_offset
        action_title = self.font_small.render("Actions (Utilisées):", True, WHITE)
        surface.blit(action_title, (x_offset, y_offset))
        y_offset += 16
        actions_status = [
            ("R: Recolter", self.action_recolter_used),
            ("D: Deposer", self.action_deposer_used),
            ("I: Influencer", self.action_influencer_used),
            ("O: Observer", self.action_observer_used or self.observer_mode),
            ("Move", self.movement_used),
        ]
        for text, used in actions_status:
            status_color = GRAY if used else WHITE
            status_surf = self.font_small.render(text, True, status_color)
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
            final_score = player.calculate_score() + player.score
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
