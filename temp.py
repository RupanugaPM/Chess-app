# -- Libraries --
import sys
import os
import copy
import random
import pygame
import stockfish 
import chess
import json

# --- Constants ---
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQSIZE = WIDTH // ROWS
FONT_NAME = 'Quivira.ttf'
SETTINGS_FILE = "chess_settings.json"

# --- Unicode Pieces Dictionary ---
UNICODE_PIECES = {
    'w_pawn': '♙', 'w_rook': '♖', 'w_knight': '♘', 'w_bishop': '♗', 'w_queen': '♕', 'w_king': '♔',
    'b_pawn': '♟', 'b_rook': '♜', 'b_knight': '♞', 'b_bishop': '♝', 'b_queen': '♛', 'b_king': '♚'
}
PIECE_COLORS = {'white': (255, 255, 255), 'black': (0, 0, 0)}

# --- Colors ---
BROWN = (181, 136, 99)
LIGHT_RED = (255, 150, 150)
WHITE_SQUARE = (240, 217, 181)
HIGHLIGHT_COLOR = (100, 150, 255, 100)
LEGAL_MOVE_COLOR = (0, 0, 0, 75)
MENU_BG_COLOR = (49, 46, 43)
FONT_COLOR = (230, 230, 230)
GAME_OVER_BG_COLOR = (0, 0, 0, 150)

# Alternative board themes
BOARD_THEMES = {
    'classic': {'light': (240, 217, 181), 'dark': (181, 136, 99)},
    'green': {'light': (238, 238, 210), 'dark': (118, 150, 86)},
    'blue': {'light': (222, 227, 230), 'dark': (140, 162, 173)},
    'gray': {'light': (220, 220, 220), 'dark': (120, 120, 120)},
    'purple': {'light': (230, 220, 240), 'dark': (150, 120, 180)}
}

# Settings UI Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_LIGHT_GRAY = (200, 200, 200)
COLOR_GRAY = (150, 150, 150)
COLOR_DARK_GRAY = (100, 100, 100)
COLOR_BLUE = (100, 100, 255)
COLOR_GREEN = (100, 200, 100)
COLOR_GLASS_BASE = (100, 100, 200, 100)
COLOR_GLASS_BASE_HOVER = (120, 120, 220, 160)
COLOR_GLASS_HIGHLIGHT = (255, 255, 255, 50)

def rotate_matrix_index(i, j, rows, cols, times):
    """Rotate the point (i, j) in a rows×cols matrix by 90° CW 'times' times."""
    def rotate90(pi, pj, pr, pc):
        return pj, pr - 1 - pi, pc, pr

    r = times % 4
    ci, cj, cr, cc = i, j, rows, cols
    for _ in range(r):
        ci, cj, cr, cc = rotate90(ci, cj, cr, cc)
    return ci, cj

# --- Game States ---
class GameState:
    WHITE_PERSPECTIVE = 0
    BLACK_PERSPECTIVE = 1
    SETTINGS = 2
    MENU = 3
    PLAYING = 4
    PROMOTING = 5
    GAME_OVER = 6
    IN_GAME_SETTINGS = 7

# --- UI Components ---
class Slider:
    """A slider UI element that can be dragged to select a value in a range."""
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label="", font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        self.knob_radius = h // 2 + 4
        self.font = font if font else pygame.font.Font(None, 24)
        self.update_knob_pos()

    def update_knob_pos(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        knob_x = self.rect.x + ratio * self.rect.w
        self.knob_rect = pygame.Rect(0, 0, self.knob_radius * 2, self.knob_radius * 2)
        self.knob_rect.center = (knob_x, self.rect.centery)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) or self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if self.dragging and event.type == pygame.MOUSEMOTION:
            mouse_x = max(self.rect.x, min(event.pos[0], self.rect.right))
            ratio = (mouse_x - self.rect.x) / self.rect.w
            self.val = self.min_val + ratio * (self.max_val - self.min_val)
            if isinstance(self.min_val, int) and isinstance(self.max_val, int):
                self.val = round(self.val)
            self.update_knob_pos()

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_GRAY, self.rect, border_radius=5)
        fill_width = self.knob_rect.centerx - self.rect.x
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.h)
        pygame.draw.rect(screen, COLOR_BLUE, fill_rect, border_radius=5)
        pygame.draw.circle(screen, COLOR_DARK_GRAY, self.knob_rect.center, self.knob_radius)
        pygame.draw.circle(screen, COLOR_WHITE, self.knob_rect.center, self.knob_radius - 2)
        label_surface = self.font.render(self.label, True, COLOR_WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 30))
        value_text = str(self.val)
        value_surface = self.font.render(value_text, True, COLOR_WHITE)
        screen.blit(value_surface, (self.rect.right + 20, self.rect.centery - 12))
        
    def get_value(self):
        return self.val

    def set_value(self, value):
        self.val = max(self.min_val, min(self.max_val, value))
        self.update_knob_pos()

class ToggleButton:
    """A toggle button for on/off settings."""
    def __init__(self, x, y, w, h, label, initial_state=False, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.state = initial_state
        self.font = font if font else pygame.font.Font(None, 24)
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.state = not self.state

    def draw(self, screen):
        # Draw label
        label_surface = self.font.render(self.label, True, COLOR_WHITE)
        screen.blit(label_surface, (self.rect.x - 250, self.rect.centery - 12))
        
        # Draw toggle background
        bg_color = COLOR_GREEN if self.state else COLOR_GRAY
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=self.rect.h // 2)
        
        # Draw toggle circle
        circle_x = self.rect.right - self.rect.h // 2 if self.state else self.rect.x + self.rect.h // 2
        pygame.draw.circle(screen, COLOR_WHITE, (circle_x, self.rect.centery), self.rect.h // 2 - 4)
        
        # Draw on/off text
        state_text = "ON" if self.state else "OFF"
        state_surface = self.font.render(state_text, True, COLOR_WHITE)
        screen.blit(state_surface, (self.rect.right + 20, self.rect.centery - 12))

    def get_value(self):
        return self.state

    def set_value(self, value):
        self.state = value

class Button:
    """A simple clickable button."""
    def __init__(self, x, y, w, h, text, callback, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.is_hovered = False
        self.font = font if font else pygame.font.Font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.callback()

    def draw(self, screen):
        color = LIGHT_RED if self.is_hovered else COLOR_GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_WHITE, self.rect, 2, border_radius=10)
        text_surface = self.font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class CycleButton:
    """A button that cycles through multiple options."""
    def __init__(self, x, y, w, h, label, options, initial_index=0, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.options = options
        self.current_index = initial_index
        self.font = font if font else pygame.font.Font(None, 24)
        self.is_hovered = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.current_index = (self.current_index + 1) % len(self.options)
    
    def draw(self, screen):
        # Draw label
        label_surface = self.font.render(self.label, True, COLOR_WHITE)
        screen.blit(label_surface, (self.rect.x - 250, self.rect.centery - 12))
        
        # Draw button
        color = LIGHT_RED if self.is_hovered else COLOR_GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_WHITE, self.rect, 2, border_radius=10)
        
        # Draw current option
        option_text = self.options[self.current_index]
        option_surface = self.font.render(option_text, True, COLOR_WHITE)
        option_rect = option_surface.get_rect(center=self.rect.center)
        screen.blit(option_surface, option_rect)
    
    def get_value(self):
        return self.options[self.current_index]
    
    def set_value(self, value):
        if value in self.options:
            self.current_index = self.options.index(value)

# --- Piece Classes (unchanged from original) ---
class Piece:
    def __init__(self, name, color, value):
        self.name = name
        self.color = color
        self.value = value * (1 if color == 'white' else -1)
        self.moves = []
        self.moved = False
        self.char = UNICODE_PIECES[f'{color[0]}_{name}']
        self.font_color = PIECE_COLORS[color]

    def add_move(self, move):
        self.moves.append(move)

    def clear_moves(self):
        self.moves = []

class Pawn(Piece):
    def __init__(self, color):
        self.dir = -1 if color == 'white' else 1
        super().__init__('pawn', color, 1.0)

class Knight(Piece):
    def __init__(self, color):
        super().__init__('knight', color, 3.0)

class Bishop(Piece):
    def __init__(self, color):
        super().__init__('bishop', color, 3.001)

class Rook(Piece):
    def __init__(self, color):
        super().__init__('rook', color, 5.0)

class Queen(Piece):
    def __init__(self, color):
        super().__init__('queen', color, 9.0)

class King(Piece):
    def __init__(self, color):
        super().__init__('king', color, 10000.0)

# --- Move Class ---
class Move:
    def __init__(self, initial, final):
        self.initial = initial
        self.final = final
        self.valid = self.check_valid()
        self.promotion_piece = None

    def check_valid(self):
        return 0 <= self.initial.x < 8 and 0 <= self.initial.y < 8 and 0 <= self.final.x < 8 and 0 <= self.final.y < 8

    def san(self):
        temp = chr(97+int(self.initial.x))+str(8 - int(self.initial.y))+chr(97+int(self.final.x))+str(8 - int(self.final.y))
        if self.promotion_piece != None:
            temp += self.promotion_piece
        return temp

    def san_to_move(san_str):
        if san_str == None:
            return None
        if len(san_str) < 4:
            raise ValueError("SAN string must be at least 4 characters long")
        initial_file = ord(san_str[0]) - ord('a')
        initial_rank = 8 - int(san_str[1])
        final_file = ord(san_str[2]) - ord('a')
        final_rank = 8 - int(san_str[3])
        initial = pygame.math.Vector2(initial_file, initial_rank)
        final = pygame.math.Vector2(final_file, final_rank)
        return [initial, final]

    def __eq__(self, other):
        return self.initial == other.initial and self.final == other.final

# --- GameSnapshot for undo/redo functionality ---
class GameSnapshot:
    """Stores the complete state of the game for undo/redo."""
    def __init__(self, board, turn, game_over_message=""):
        self.board = copy.deepcopy(board)
        self.turn = turn
        self.game_over_message = game_over_message

# --- Board Class with Stockfish improvements ---
class Board:
    def __init__(self, enable_stockfish=True, stockfish_level=10):
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.last_move = None
        self.move_list = []
        self.best_move_list_san = []
        self.best_move_list = []
        self.evaluation_list = []
        self._create_board()
        self._add_pieces('white')
        self._add_pieces('black')
        self._board = chess.Board()
        self.king_position = [[7, 4], [0, 4]]
        self.promoting = False
        self.promotion_move = None
        self.board_stockfish = None
        self.stockfish_level = stockfish_level
        if enable_stockfish:
            try:
                self.board_stockfish = stockfish.Stockfish(path="stockfish-windows-x86-64-avx2.exe")
                self.board_stockfish.set_skill_level(stockfish_level)
            except:
                print("Stockfish not found. AI features disabled.")
                self.board_stockfish = None

    def _enable_stockfish(self, level=10):
        try:
            self.board_stockfish = stockfish.Stockfish(path="stockfish-windows-x86-64-avx2.exe")
            self.stockfish_level = level
            self.board_stockfish.set_skill_level(level)
        except:
            self.board_stockfish = None

    def _disable_stockfish(self):
        self.board_stockfish = None

    def set_stockfish_level(self, level):
        self.stockfish_level = level
        if self.board_stockfish:
            self.board_stockfish.set_skill_level(level)

    def _create_board(self):
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]

    def _add_pieces(self, color):
        pawn_row, back_row = (6, 7) if color == 'white' else (1, 0)
        for col in range(COLS):
            self.squares[pawn_row][col] = Pawn(color)
        self.squares[back_row][0] = Rook(color)
        self.squares[back_row][1] = Knight(color)
        self.squares[back_row][2] = Bishop(color)
        self.squares[back_row][3] = Queen(color)
        self.squares[back_row][4] = King(color)
        self.squares[back_row][5] = Bishop(color)
        self.squares[back_row][6] = Knight(color)
        self.squares[back_row][7] = Rook(color)

    def set_stockfish(self):
        if self.board_stockfish:
            self.board_stockfish.set_fen_position(self._board.fen())

    def get_evaluation(self):
        if self.board_stockfish == None:
            return None
        if len(self.evaluation_list) == len(self.move_list) + 1:
            return self.evaluation_list[-1]
        self.set_stockfish()
        self.evaluation_list.append(self.board_stockfish.get_evaluation())
        return self.evaluation_list[-1]

    def get_best_move(self):
        if self.board_stockfish == None:
            return None
        if len(self.best_move_list) == len(self.move_list) + 1:
            return self.best_move_list[-1]
        best_move_san = self.get_best_move_san()
        if best_move_san:
            self.best_move_list.append(Move.san_to_move(best_move_san))
        else:
            self.best_move_list.append(None)
        return self.best_move_list[-1]

    def get_best_move_san(self):
        if self.board_stockfish == None:
            return None
        if len(self.best_move_list_san) == len(self.move_list) + 1:
            return self.best_move_list_san[-1]
        self.set_stockfish()
        self.best_move_list_san.append(self.board_stockfish.get_best_move())
        return self.best_move_list_san[-1]

    def push_move(self, move, making_move=True):
        self.last_move = move
        self.move_list.append(move)
        if making_move:
            self._board.push_san(move.san())
        # Clear the best move cache when a move is made
        if len(self.best_move_list) > len(self.move_list):
            self.best_move_list = self.best_move_list[:len(self.move_list)]
            self.best_move_list_san = self.best_move_list_san[:len(self.move_list)]
            self.evaluation_list = self.evaluation_list[:len(self.move_list)]

    def move(self, piece, move, making_move=True):
        if self.promoting:
            return
        self.promoting = self.check_promotion(piece, move.final)

        initial_row, initial_col = int(move.initial.y), int(move.initial.x)
        final_row, final_col = int(move.final.y), int(move.final.x)

        # En passant
        if isinstance(piece, Pawn) and abs(final_row - initial_row) == 1 and abs(final_col - initial_col) == 1 and not self.squares[final_row][final_col]:
            self.squares[initial_row][final_col] = 0
        
        # Castling
        if isinstance(piece, King) and abs(final_col - initial_col) == 2:
            rook_col = 0 if final_col < initial_col else 7
            new_rook_col = 3 if final_col < initial_col else 5
            rook = self.squares[initial_row][rook_col]
            self.squares[initial_row][new_rook_col] = rook
            self.squares[initial_row][rook_col] = 0
            rook.moved = True

        self.squares[initial_row][initial_col] = 0
        piece.moved = True
        self.squares[final_row][final_col] = piece

        if isinstance(piece, King):
            self.king_position[piece.color == "black"] = [final_row, final_col]

        if self.promoting:
            self.promotion_move = move
            return
        self.push_move(move, making_move)
    
    def promote_pawn(self, row, col, piece_name):
        color = self.squares[row][col].color
        self.promotion_move.promotion_piece = piece_name[0]
        if piece_name == 'queen': 
            self.squares[row][col] = Queen(color)
        elif piece_name == 'rook': 
            self.squares[row][col] = Rook(color)
        elif piece_name == 'bishop': 
            self.squares[row][col] = Bishop(color)
        elif piece_name == 'knight': 
            self.squares[row][col] = Knight(color)
            self.promotion_move.promotion_piece = 'n'
        self.push_move(self.promotion_move)
        self.promoting = False
        self.promotion_move = None

    def check_promotion(self, piece, final_pos):
        return isinstance(piece, Pawn) and (final_pos.y == 0 or final_pos.y == 7)

    def clone(self):
        new = self.__class__.__new__(self.__class__)
        new.move_list = copy.deepcopy(self.move_list)
        new.promoting = self.promoting
        new.promotion_move = copy.deepcopy(self.promotion_move)
        new.squares = [
            [copy.deepcopy(piece) for piece in row]
            for row in self.squares
        ]
        new.king_position = copy.deepcopy(self.king_position)
        new.last_move = copy.deepcopy(self.last_move)
        new._board = self._board.copy()
        new.board_stockfish = None
        new.best_move_list_san = copy.deepcopy(self.best_move_list_san)
        new.best_move_list = copy.deepcopy(self.best_move_list)
        new.evaluation_list = copy.deepcopy(self.evaluation_list)
        return new

    def __deepcopy__(self, memo):
        return self.clone()

class Dragger:
    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX, self.mouseY = 0, 0
        self.initial_row, self.initial_col = 0, 0
    
    def update_blit(self, surface, font):
        if self.piece:
            text_surface = font.render(self.piece.char, True, self.piece.font_color)
            text_rect = text_surface.get_rect(center=(self.mouseX, self.mouseY))
            surface.blit(text_surface, text_rect)
            
    def update_mouse(self, pos): 
        self.mouseX, self.mouseY = pos
        
    def save_initial(self, pos): 
        self.initial_row, self.initial_col = pos[1] // SQSIZE, pos[0] // SQSIZE
        
    def drag_piece(self, piece): 
        self.piece, self.dragging = piece, True
        
    def undrag_piece(self): 
        self.piece, self.dragging = None, False

# --- Main Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.clock = pygame.time.Clock()
        
        # Load fonts
        try:
            self.piece_font = pygame.font.Font(FONT_NAME, int(SQSIZE * 0.8))
            self.coord_font = pygame.font.Font(FONT_NAME, int(SQSIZE * 0.2))
        except FileNotFoundError:
            print(f"Error: Font '{FONT_NAME}' not found. Using default font.")
            self.piece_font = pygame.font.Font(None, int(SQSIZE * 0.8))
            self.coord_font = pygame.font.Font(None, int(SQSIZE * 0.2))
        
        self.menu_font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 20)
        
        # Load settings
        self.load_settings()
        
        # Game state
        self.gamestate = GameState.MENU
        self.previous_gamestate = GameState.MENU
        self.board = None
        self.mouse_position = (0, 0)
        self.dragger = Dragger()
        self.turn = 'white'
        self.promotion_pos = None
        self.promotion_pieces = ['queen', 'rook', 'bishop', 'knight'] 
        self.game_over_message = ""
        self.game_mode = None
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # Menu colors
        self.menu_font_color = FONT_COLOR
        self.menu_title_color = WHITE_SQUARE
        self.menu_background_color = MENU_BG_COLOR
        self.menu_font_animated_color = LIGHT_RED
        
        # Create settings UI
        self.create_settings_ui()

    def load_settings(self):
        """Load settings from JSON file."""
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.board_perspective = GameState.WHITE_PERSPECTIVE if settings.get("perspective") == "white" else GameState.BLACK_PERSPECTIVE
                self.show_stockfish_hints = settings.get("show_hints", True)
                self.stockfish_difficulty = settings.get("stockfish_difficulty", 10)
                self.board_theme = settings.get("board_theme", "classic")
                self.show_coordinates = settings.get("show_coordinates", True)
                self.show_last_move = settings.get("show_last_move", True)
                self.auto_promote_queen = settings.get("auto_promote_queen", False)
                self.enable_undo = settings.get("enable_undo", True)
                self.show_legal_moves = settings.get("show_legal_moves", True)
                self.animation_speed = settings.get("animation_speed", 500)
                print("Settings loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Settings file not found. Using default settings.")
            self.board_perspective = GameState.WHITE_PERSPECTIVE
            self.show_stockfish_hints = True
            self.stockfish_difficulty = 10
            self.board_theme = "classic"
            self.show_coordinates = True
            self.show_last_move = True
            self.auto_promote_queen = False
            self.enable_undo = True
            self.show_legal_moves = True
            self.animation_speed = 500

    def save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            "perspective": "white" if self.perspective_toggle.get_value() else "black",
            "show_hints": self.hints_toggle.get_value(),
            "stockfish_difficulty": self.difficulty_slider.get_value(),
            "board_theme": self.theme_button.get_value(),
            "show_coordinates": self.coord_toggle.get_value(),
            "show_last_move": self.last_move_toggle.get_value(),
            "auto_promote_queen": self.auto_promote_toggle.get_value(),
            "enable_undo": self.undo_toggle.get_value(),
            "show_legal_moves": self.legal_moves_toggle.get_value(),
            "animation_speed": self.animation_slider.get_value()
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        print("Settings saved.")

    def create_settings_ui(self):
        """Create UI elements for settings menu."""
        # Column positions
        left_col = 450
        
        # Row positions
        y_start = 120
        y_spacing = 50
        
        row = 0
        
        # Board settings
        self.perspective_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25, 
            "White Perspective", 
            self.board_perspective == GameState.WHITE_PERSPECTIVE,
            self.menu_font
        )
        row += 1
        
        self.theme_button = CycleButton(
            left_col - 50, y_start + (row * y_spacing), 150, 30,
            "Board Theme",
            list(BOARD_THEMES.keys()),
            list(BOARD_THEMES.keys()).index(self.board_theme),
            self.menu_font
        )
        row += 1
        
        self.coord_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Show Coordinates",
            self.show_coordinates,
            self.menu_font
        )
        row += 1
        
        # Visual settings
        self.hints_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Show Best Moves",
            self.show_stockfish_hints,
            self.menu_font
        )
        row += 1
        
        self.last_move_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Highlight Last Move",
            self.show_last_move,
            self.menu_font
        )
        row += 1
        
        self.legal_moves_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Show Legal Moves",
            self.show_legal_moves,
            self.menu_font
        )
        row += 1
        
        # Gameplay settings
        self.auto_promote_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Auto-Promote to Queen",
            self.auto_promote_queen,
            self.menu_font
        )
        row += 1
        
        self.undo_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Enable Undo (← →)",
            self.enable_undo,
            self.menu_font
        )
        row += 1
        
        # AI Settings
        self.difficulty_slider = Slider(
            150, y_start + (row * y_spacing) + 20, 400, 15,
            0, 20, self.stockfish_difficulty,
            "Stockfish Difficulty",
            self.menu_font
        )
        row += 2
        
        self.animation_slider = Slider(
            150, y_start + (row * y_spacing), 400, 15,
            0, 2000, self.animation_speed,
            "AI Move Delay (ms)",
            self.menu_font
        )
        row += 2
        
        # Buttons
        button_y = y_start + (row * y_spacing)
        self.save_button = Button(
            200, button_y, 120, 40,
            "Save",
            self.save_and_apply,
            self.menu_font
        )
        
        self.back_button = Button(
            340, button_y, 120, 40,
            "Back",
            self.return_from_settings,
            self.menu_font
        )
        
        self.reset_button = Button(
            480, button_y, 120, 40,
            "Reset",
            self.reset_settings,
            self.menu_font
        )
        
        self.settings_ui_elements = [
            self.perspective_toggle,
            self.theme_button,
            self.coord_toggle,
            self.hints_toggle,
            self.last_move_toggle,
            self.legal_moves_toggle,
            self.auto_promote_toggle,
            self.undo_toggle,
            self.difficulty_slider,
            self.animation_slider,
            self.save_button,
            self.back_button,
            self.reset_button
        ]

    def save_and_apply(self):
        """Save settings and apply them."""
        # Update internal settings
        self.board_perspective = GameState.WHITE_PERSPECTIVE if self.perspective_toggle.get_value() else GameState.BLACK_PERSPECTIVE
        self.show_stockfish_hints = self.hints_toggle.get_value()
        self.stockfish_difficulty = self.difficulty_slider.get_value()
        self.board_theme = self.theme_button.get_value()
        self.show_coordinates = self.coord_toggle.get_value()
        self.show_last_move = self.last_move_toggle.get_value()
        self.auto_promote_queen = self.auto_promote_toggle.get_value()
        self.enable_undo = self.undo_toggle.get_value()
        self.show_legal_moves = self.legal_moves_toggle.get_value()
        self.animation_speed = self.animation_slider.get_value()
        
        # Update board if it exists
        if self.board and self.board.board_stockfish:
            self.board.set_stockfish_level(self.stockfish_difficulty)
        
        # Save to file
        self.save_settings()
        
        # Return to previous state
        self.return_from_settings()

    def return_from_settings(self):
        """Return to previous game state."""
        if self.gamestate == GameState.IN_GAME_SETTINGS:
            self.gamestate = GameState.PLAYING
        else:
            self.gamestate = GameState.MENU

    def reset_settings(self):
        """Reset all settings to default."""
        self.perspective_toggle.set_value(True)
        self.hints_toggle.set_value(True)
        self.difficulty_slider.set_value(10)
        self.theme_button.set_value("classic")
        self.coord_toggle.set_value(True)
        self.last_move_toggle.set_value(True)
        self.auto_promote_toggle.set_value(False)
        self.undo_toggle.set_value(True)
        self.legal_moves_toggle.set_value(True)
        self.animation_slider.set_value(500)

    def save_game_state(self):
        """Save current game state to history."""
        if self.enable_undo:
            # Remove any states after current index
            self.history = self.history[:self.history_index + 1]
            
            # Add new state
            snapshot = GameSnapshot(self.board, self.turn, self.game_over_message)
            self.history.append(snapshot)
            
            # Limit history size
            if len(self.history) > self.max_history:
                self.history.pop(0)
            else:
                self.history_index += 1

    def undo_move(self):
        """Undo the last move."""
        if self.enable_undo and self.history_index > 0:
            self.history_index -= 1
            snapshot = self.history[self.history_index]
            self.board = copy.deepcopy(snapshot.board)
            self.turn = snapshot.turn
            self.game_over_message = snapshot.game_over_message
            self.gamestate = GameState.PLAYING if not self.game_over_message else GameState.GAME_OVER
            self.calc_all_valid_moves(self.turn)
            print(f"Undone move. Now at move {self.history_index}")

    def redo_move(self):
        """Redo a previously undone move."""
        if self.enable_undo and self.history_index < len(self.history) - 1:
            self.history_index += 1
            snapshot = self.history[self.history_index]
            self.board = copy.deepcopy(snapshot.board)
            self.turn = snapshot.turn
            self.game_over_message = snapshot.game_over_message
            self.gamestate = GameState.PLAYING if not self.game_over_message else GameState.GAME_OVER
            self.calc_all_valid_moves(self.turn)
            print(f"Redone move. Now at move {self.history_index}")

    def reset(self):
        """Reset the game with current settings."""
        # Initialize board
        enable_stockfish = self.show_stockfish_hints or self.game_mode == 'stockfish'
        self.board = Board(enable_stockfish=enable_stockfish, stockfish_level=self.stockfish_difficulty)
        
        if not self.show_stockfish_hints and self.game_mode != 'stockfish':
            self.board._disable_stockfish()
        
        self.dragger = Dragger()
        self.turn = 'white'
        self.promotion_pos = None
        self.game_over_message = ""
        
        # Reset history
        self.history = []
        self.history_index = -1
        
        # Save initial state
        self.save_game_state()
        
        self.calc_all_valid_moves(self.turn)

    def get_board_perspective(self):
        return 'black' if self.board_perspective == GameState.BLACK_PERSPECTIVE else 'white'

    def mainloop(self):
        while True:
            if self.gamestate == GameState.MENU:
                self.show_menu()
                self.handle_menu_animations()
                self.handle_menu_events()
            elif self.gamestate == GameState.SETTINGS:
                self.show_settings()
                self.handle_settings_events()
            elif self.gamestate == GameState.IN_GAME_SETTINGS:
                self.show_settings()
                self.handle_settings_events()
            elif self.gamestate == GameState.PLAYING:
                self.show_bg()
                if self.show_coordinates:
                    self.show_board_coordinates()
                if self.show_last_move:
                    self.show_last_move_highlight()
                if self.show_stockfish_hints and self.board.board_stockfish:
                    self.show_best_move()
                if self.show_legal_moves:
                    self.show_moves()
                self.show_pieces()
                if self.dragger.dragging:
                    self.dragger.update_blit(self.screen, self.piece_font)
                self.show_move_history()
                self.handle_playing_events()
                # Handle AI moves
                if self.game_mode == 'random' and self.turn == 'black':
                    self.random_move()
                elif self.game_mode == 'stockfish' and self.turn == 'black':
                    self.stockfish_move()
            elif self.gamestate == GameState.PROMOTING:
                self.show_bg()
                self.show_pieces()
                if not self.auto_promote_queen:
                    self.show_promotion_menu()
                    self.handle_promotion_events()
                else:
                    self.auto_promote()
            elif self.gamestate == GameState.GAME_OVER:
                self.show_bg()
                self.show_pieces()
                self.show_game_over()
                self.handle_game_over_events()
                
            pygame.display.update()
            self.clock.tick(60)

    # --- Drawing Methods ---
    def show_bg(self):
        self.screen.fill((0, 0, 0))
        theme = BOARD_THEMES[self.board_theme]
        for row in range(ROWS):
            for col in range(COLS):
                state = 0
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    state = 1
                color = theme['light'] if (row + col) % 2 == state else theme['dark']
                pygame.draw.rect(self.screen, color, (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE))

    def show_board_coordinates(self):
        """Show board coordinates (a-h, 1-8)."""
        theme = BOARD_THEMES[self.board_theme]
        
        for i in range(8):
            # File labels (a-h)
            file_label = chr(ord('a') + i)
            color = theme['dark'] if i % 2 == 0 else theme['light']
            if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                file_label = chr(ord('h') - i)
            text = self.coord_font.render(file_label, True, color)
            self.screen.blit(text, (i * SQSIZE + 5, HEIGHT - 20))
            
            # Rank labels (1-8)
            rank_label = str(8 - i)
            color = theme['dark'] if i % 2 == 0 else theme['light']
            if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                rank_label = str(i + 1)
            text = self.coord_font.render(rank_label, True, color)
            self.screen.blit(text, (WIDTH - 15, i * SQSIZE + 5))

    def show_pieces(self):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col]
                if piece != 0 and piece != self.dragger.piece:
                    text_surface = self.piece_font.render(piece.char, True, piece.font_color)
                    cur_row = row
                    cur_col = col
                    if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                        cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                    text_rect = text_surface.get_rect(center=(cur_col * SQSIZE + SQSIZE // 2, cur_row * SQSIZE + SQSIZE // 2))
                    self.screen.blit(text_surface, text_rect)

    def show_moves(self):
        if self.dragger.dragging:
            for move in self.dragger.piece.moves:
                s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                s.fill(LEGAL_MOVE_COLOR)
                cur_col = move.final.x
                cur_row = move.final.y
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                self.screen.blit(s, (cur_col * SQSIZE, cur_row * SQSIZE))

    def show_last_move_highlight(self):
        if self.board.last_move:
            for pos in [self.board.last_move.initial, self.board.last_move.final]:
                color = (200, 200, 0, 100)
                s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                s.fill(color)
                cur_col = pos.x
                cur_row = pos.y
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                self.screen.blit(s, (cur_col * SQSIZE, cur_row * SQSIZE))

    def show_best_move(self):
        if self.board.board_stockfish != None:
            best_move = self.board.get_best_move()
            if best_move:
                for pos in best_move:
                    color = (0, 200, 0, 100)
                    s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    s.fill(color)
                    cur_col = pos.x
                    cur_row = pos.y
                    if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                        cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                    self.screen.blit(s, (cur_col * SQSIZE, cur_row * SQSIZE))

    def show_move_history(self):
        """Show move counter and undo/redo hints."""
        if self.enable_undo:
            text = f"Move: {self.history_index}/{len(self.history)-1}"
            if self.history_index > 0:
                text += " [← Undo]"
            if self.history_index < len(self.history) - 1:
                text += " [Redo →]"
            
            surface = self.small_font.render(text, True, COLOR_GRAY)
            # Position in top-left corner with padding
            self.screen.blit(surface, (10, 10))

    def show_settings(self):
        """Display the settings menu."""
        self.screen.fill(MENU_BG_COLOR)
        
        # Title
        title_text = 'Game Settings' if self.gamestate == GameState.IN_GAME_SETTINGS else 'Settings'
        title = pygame.font.Font(None, 60).render(title_text, True, self.menu_title_color)
        self.screen.blit(title, (WIDTH/2 - title.get_width()/2, 30))
        
        # Instructions
        if self.gamestate == GameState.IN_GAME_SETTINGS:
            inst_text = "Press ESC to return to game"
            inst = self.small_font.render(inst_text, True, COLOR_GRAY)
            self.screen.blit(inst, (WIDTH/2 - inst.get_width()/2, 70))
        
        # Update perspective label
        persp_text = "Black Perspective" if not self.perspective_toggle.get_value() else "White Perspective"
        self.perspective_toggle.label = persp_text
        
        # Draw all UI elements
        for element in self.settings_ui_elements:
            element.draw(self.screen)
        
        # Draw difficulty level text
        diff_names = {0: "Beginner", 5: "Easy", 10: "Medium", 15: "Hard", 20: "Master"}
        diff_level = self.difficulty_slider.get_value()
        closest_key = min(diff_names.keys(), key=lambda x: abs(x - diff_level))
        diff_text = diff_names[closest_key]
        
        diff_surface = self.menu_font.render(diff_text, True, COLOR_WHITE)
        self.screen.blit(diff_surface, (self.difficulty_slider.rect.right + 80, self.difficulty_slider.rect.centery - 12))

    def handle_settings_events(self):
        """Handle events in settings menu."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.return_from_settings()
            for element in self.settings_ui_elements:
                element.handle_event(event)
    
    # --- Event Handling ---
    def handle_playing_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Open in-game settings
                    self.previous_gamestate = self.gamestate
                    self.gamestate = GameState.IN_GAME_SETTINGS
                elif event.key == pygame.K_LEFT and self.enable_undo:
                    # Undo move
                    self.undo_move()
                elif event.key == pygame.K_RIGHT and self.enable_undo:
                    # Redo move
                    self.redo_move()
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.dragger.update_mouse(event.pos)
                cur_row, cur_col = self.dragger.mouseY // SQSIZE, self.dragger.mouseX // SQSIZE
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                piece = 0 
                if 0<=cur_row<ROWS and 0<=cur_col<COLS:
                    piece = self.board.squares[cur_row][cur_col]
                if piece != 0 and piece.color == self.turn:
                    self.dragger.initial_col = cur_col
                    self.dragger.initial_row = cur_row
                    self.dragger.drag_piece(piece)
                    
            if event.type == pygame.MOUSEMOTION and self.dragger.dragging:
                self.dragger.update_mouse(event.pos)
                
            if event.type == pygame.MOUSEBUTTONUP and self.dragger.dragging:
                cur_row, cur_col = self.dragger.mouseY // SQSIZE, self.dragger.mouseX // SQSIZE
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                initial = pygame.math.Vector2(self.dragger.initial_col, self.dragger.initial_row)
                final = pygame.math.Vector2(cur_col, cur_row)
                move = Move(initial, final)
                if move in self.dragger.piece.moves: 
                    self.make_move(self.dragger.piece, move)
                self.dragger.undrag_piece()

    # --- Game Logic Methods ---
    def make_move(self, piece, move):
        self.board.move(piece, move)
        if self.board.check_promotion(piece, move.final):
            self.gamestate = GameState.PROMOTING
            self.promotion_pos = (int(move.final.y), int(move.final.x))
        else:
            self.next_turn()

    def next_turn(self):
        self.turn = 'black' if self.turn == 'white' else 'white'
        self.calc_all_valid_moves(self.turn)
        self.check_game_over()
        # Save state after each move
        self.save_game_state()

    def calc_all_valid_moves(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col]
                if piece != 0 and piece.color == color:
                    self.calc_moves(piece, row, col, self.board)

    def calc_moves(self, piece, row, col, board):
        piece.clear_moves()
        raw_moves = self._get_all_raw_moves(piece, row, col, board)
        for move in raw_moves:
            self.add_valid_move(piece, move, board)
            
    def add_valid_move(self, piece, move, board):
        temp_board = copy.deepcopy(board)
        temp_piece = temp_board.squares[int(move.initial.y)][int(move.initial.x)]
        temp_board.move(temp_piece, move, False)
        if not self.is_in_check(piece.color, temp_board):
            piece.add_move(move)

    def _get_all_raw_moves(self, piece, row, col, board):
        moves = self._get_raw_moves(piece, row, col, board)
        # Castling
        if isinstance(piece, King) and not piece.moved:
            # Queenside
            if (isinstance(board.squares[row][0], Rook) and not board.squares[row][0].moved and 
                all(board.squares[row][c] == 0 for c in [1, 2, 3]) and 
                not self.is_in_check(piece.color, board) and 
                not self.is_in_check_at(piece.color, row, col-1, board) and 
                not self.is_in_check_at(piece.color, row, col-2, board)):
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(col - 2, row)))
            # Kingside
            if (isinstance(board.squares[row][7], Rook) and not board.squares[row][7].moved and 
                all(board.squares[row][c] == 0 for c in [5, 6]) and 
                not self.is_in_check(piece.color, board) and 
                not self.is_in_check_at(piece.color, row, col+1, board) and 
                not self.is_in_check_at(piece.color, row, col+2, board)):
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(col + 2, row)))
        return moves

    def _get_raw_moves(self, piece, row, col, board):
        moves = []
        
        def add_line_moves(directions):
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < ROWS and 0 <= c < COLS:
                    dest = board.squares[r][c]
                    if dest == 0 or dest.color != piece.color:
                        moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
                        if dest != 0: 
                            break
                    else: 
                        break
                    r, c = r + dr, c + dc
        
        if isinstance(piece, Pawn):
            # Forward moves
            r, c = row + piece.dir, col
            if 0 <= r < ROWS and board.squares[r][c] == 0:
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
                # Double move from start
                if not piece.moved and 0 <= r + piece.dir < ROWS and board.squares[r + piece.dir][c] == 0:
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r + piece.dir)))
            # Captures
            for dc in [-1, 1]:
                r, c = row + piece.dir, col + dc
                if 0 <= r < ROWS and 0 <= c < COLS and board.squares[r][c] != 0 and board.squares[r][c].color != piece.color:
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
            # En passant
            if board.last_move:
                lm_final_row, lm_final_col = int(board.last_move.final.y), int(board.last_move.final.x)
                lm_initial_row = int(board.last_move.initial.y)
                if (lm_final_row == row and isinstance(board.squares[row][lm_final_col], Pawn) and 
                    abs(lm_final_row - lm_initial_row) == 2):
                    if lm_final_col == col - 1 or lm_final_col == col + 1:
                        moves.append(Move(pygame.math.Vector2(col, row), 
                                        pygame.math.Vector2(lm_final_col, row + piece.dir)))

        elif isinstance(piece, Knight):
            for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                r, c = row + dr, col + dc
                if 0 <= r < ROWS and 0 <= c < COLS and (board.squares[r][c] == 0 or board.squares[r][c].color != piece.color):
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))

        elif isinstance(piece, Bishop): 
            add_line_moves([(1,1), (1,-1), (-1,1), (-1,-1)])
            
        elif isinstance(piece, Rook): 
            add_line_moves([(1,0), (-1,0), (0,1), (0,-1)])
            
        elif isinstance(piece, Queen): 
            add_line_moves([(1,1), (1,-1), (-1,1), (-1,-1), (1,0), (-1,0), (0,1), (0,-1)])
            
        elif isinstance(piece, King):
            for dr, dc in [(dr, dc) for dr in [-1,0,1] for dc in [-1,0,1] if (dr, dc) != (0,0)]:
                r, c = row + dr, col + dc
                if 0 <= r < ROWS and 0 <= c < COLS and (board.squares[r][c] == 0 or board.squares[r][c].color != piece.color):
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
                    
        return moves

    def is_in_check(self, color, board_state):
        king_pos = self.find_king(color, board_state)
        return self.is_in_check_at(color, king_pos[0], king_pos[1], board_state) if king_pos else False

    def is_in_check_at(self, color, row, col, board_state):
        opponent_color = 'white' if color == 'black' else 'black'
        for r in range(ROWS):
            for c in range(COLS):
                piece = board_state.squares[r][c]
                if piece != 0 and piece.color == opponent_color:
                    raw_moves = self._get_raw_moves(piece, r, c, board_state)
                    for move in raw_moves:
                        if int(move.final.y) == row and int(move.final.x) == col:
                            return True
        return False

    def find_king(self, color, board_state):
        for r in range(ROWS):
            for c in range(COLS):
                if isinstance(board_state.squares[r][c], King) and board_state.squares[r][c].color == color:
                    return (r, c)
        return None
        
    def check_game_over(self):
        if not any(p.moves for row in self.board.squares for p in row if p != 0 and p.color == self.turn):
            self.gamestate = GameState.GAME_OVER
            winner = 'Black' if self.turn == 'white' else 'White'
            self.game_over_message = f"Checkmate! {winner} wins." if self.is_in_check(self.turn, self.board) else "Stalemate! It's a draw."
    
    def auto_promote(self):
        """Automatically promote to queen."""
        self.board.promote_pawn(self.promotion_pos[0], self.promotion_pos[1], 'queen')
        self.gamestate = GameState.PLAYING
        self.next_turn()

    def random_move(self):
        """Make a random move for the AI."""
        if self.turn == 'black' and not self.game_over_message:
            all_moves = [(p, m) for r in self.board.squares for p in r if p != 0 and p.color == 'black' for m in p.moves]
            if all_moves:
                pygame.time.wait(self.animation_speed)
                self.make_move(*random.choice(all_moves))
            if self.gamestate == GameState.PROMOTING:
                self.board.promote_pawn(self.promotion_pos[0], self.promotion_pos[1], random.choice(self.promotion_pieces))
                self.gamestate = GameState.PLAYING
                self.next_turn()

    def stockfish_move(self):
        """Make a move using Stockfish AI."""
        if self.turn == 'black' and not self.game_over_message:
            if not self.board.board_stockfish:
                self.board._enable_stockfish(self.stockfish_difficulty)
            
            best_move = self.board.get_best_move()
            if best_move:
                pygame.time.wait(self.animation_speed)
                
                initial_row, initial_col = int(best_move[0].y), int(best_move[0].x)
                piece = self.board.squares[initial_row][initial_col]
                
                move = Move(best_move[0], best_move[1])
                if piece and piece.color == 'black':
                    self.make_move(piece, move)
                    
                    if self.gamestate == GameState.PROMOTING:
                        self.board.promote_pawn(self.promotion_pos[0], self.promotion_pos[1], 'queen')
                        self.gamestate = GameState.PLAYING
                        self.next_turn()
    
    # --- UI and State Handlers ---
    def show_menu(self):
        self.screen.fill(MENU_BG_COLOR)
        title = pygame.font.Font(None, 74).render('Python Chess', True, self.menu_title_color)
        self.screen.blit(title, (WIDTH/2 - title.get_width()/2, 100))
       
    def handle_menu_animations(self):
        self.mouse_position = pygame.mouse.get_pos()
        self.pvp_rect = self.menu_text('1 vs 1 (Local)', (WIDTH//2, 300), 50)
        self.pve_rect = self.menu_text('1 vs Random', (WIDTH//2, 380), 50)
        self.stockfish_rect = self.menu_text('1 vs Stockfish', (WIDTH//2, 460), 50)
        self.settings_rect = self.menu_text('Settings', (WIDTH//2, 540), 50)
      
    def menu_text(self, text, center, size):
        text_rect = pygame.font.Font(None, size).render(text, True, self.menu_font_color).get_rect(center=center)
        if text_rect.collidepoint(self.mouse_position):
            self.handle_text(text, self.menu_font_animated_color, center, size)
        else:
            self.handle_text(text, self.menu_font_color, center, size)
        return text_rect

    def handle_text(self, text, color, center, size):
        text_surface = pygame.font.Font(None, size).render(text, True, color)
        text_rect = text_surface.get_rect(center=center)
        self.screen.blit(text_surface, text_rect)
        
    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.pvp_rect.collidepoint(event.pos): 
                    self.game_mode = 'pvp'
                    self.gamestate = GameState.PLAYING
                    self.reset()
                elif self.pve_rect.collidepoint(event.pos): 
                    self.game_mode = 'random'
                    self.gamestate = GameState.PLAYING
                    self.reset()
                elif self.stockfish_rect.collidepoint(event.pos):
                    self.game_mode = 'stockfish'
                    self.gamestate = GameState.PLAYING
                    self.reset()
                elif self.settings_rect.collidepoint(event.pos):
                    self.gamestate = GameState.SETTINGS

    def show_promotion_menu(self):
        cur_row, cur_col = self.promotion_pos
        if self.board_perspective == GameState.BLACK_PERSPECTIVE:
            cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
        cur_row = cur_row * SQSIZE if self.turn == self.get_board_perspective() else (cur_row - 3) * SQSIZE

        rect = pygame.Rect(cur_col * SQSIZE, cur_row, SQSIZE, SQSIZE * 4)
        pygame.draw.rect(self.screen, MENU_BG_COLOR, rect, border_radius=10)
        self.promotion_options = {}
        for i, name in enumerate(self.promotion_pieces):
            promo_rect = pygame.Rect(rect.x, rect.y + i * SQSIZE, SQSIZE, SQSIZE)
            self.promotion_options[name] = promo_rect
            char = UNICODE_PIECES[f'{self.turn[0]}_{name}']
            text_surf = self.piece_font.render(char, True, PIECE_COLORS[self.turn])
            self.screen.blit(text_surf, text_surf.get_rect(center=promo_rect.center))

    def handle_promotion_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for name, rect in self.promotion_options.items():
                    if rect.collidepoint(event.pos):
                        self.board.promote_pawn(self.promotion_pos[0], self.promotion_pos[1], name)
                        self.gamestate = GameState.PLAYING
                        self.next_turn()
                        return     

    def show_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill(GAME_OVER_BG_COLOR)
        self.screen.blit(s, (0, 0))
        text = pygame.font.Font(None, 60).render(self.game_over_message, True, FONT_COLOR)
        prompt = pygame.font.Font(None, 40).render("Click to return to menu.", True, FONT_COLOR)
        self.screen.blit(text, text.get_rect(center=(WIDTH/2, HEIGHT/2 - 20)))
        self.screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT/2 + 30)))

    def handle_game_over_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN: 
                self.gamestate = GameState.MENU
                self.reset()

if __name__ == '__main__':
    game = Game()
    game.mainloop()