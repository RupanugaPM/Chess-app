# -- Libraries --
import sys
import os
import copy
import random
import pygame
import stockfish 
import chess
import json
import math

# --- Constants ---
WIDTH, HEIGHT = 1000, 800  # Increased width for eval bar
BOARD_SIZE = 800
ROWS, COLS = 8, 8
SQSIZE = BOARD_SIZE // ROWS
EVAL_BAR_WIDTH = 40
EVAL_BAR_HEIGHT = BOARD_SIZE - 80
FONT_NAME = 'Quivira.ttf'
SETTINGS_FILE = "chess_settings.json"

# --- Unicode Pieces Dictionary ---
UNICODE_PIECES = {
    'w_pawn': '♙', 'w_rook': '♖', 'w_knight': '♘', 'w_bishop': '♗', 'w_queen': '♕', 'w_king': '♔',
    'b_pawn': '♟', 'b_rook': '♜', 'b_knight': '♞', 'b_bishop': '♝', 'b_queen': '♛', 'b_king': '♚'
}
PIECE_COLORS = {'white': (255, 255, 255), 'black': (0, 0, 0)}

# --- Enhanced Colors ---
BROWN = (181, 136, 99)
LIGHT_RED = (255, 150, 150)
WHITE_SQUARE = (240, 217, 181)
HIGHLIGHT_COLOR = (100, 150, 255, 100)
LEGAL_MOVE_COLOR = (0, 0, 0, 75)
MENU_BG_COLOR = (49, 46, 43)
FONT_COLOR = (230, 230, 230)
GAME_OVER_BG_COLOR = (0, 0, 0, 150)
COORD_BG_COLOR = (60, 60, 60, 200)
EVAL_BAR_BG = (45, 45, 45)
EVAL_WHITE_COLOR = (240, 240, 240)
EVAL_BLACK_COLOR = (40, 40, 40)
EVAL_TEXT_COLOR = (255, 200, 0)
EDITOR_BG_COLOR = (70, 70, 70)
PALETTE_BG_COLOR = (50, 50, 50)

# Alternative board themes
BOARD_THEMES = {
    'classic': {'light': (240, 217, 181), 'dark': (181, 136, 99)},
    'green': {'light': (238, 238, 210), 'dark': (118, 150, 86)},
    'blue': {'light': (222, 227, 230), 'dark': (140, 162, 173)},
    'gray': {'light': (220, 220, 220), 'dark': (120, 120, 120)},
    'purple': {'light': (230, 220, 240), 'dark': (150, 120, 180)},
    'ocean': {'light': (180, 220, 255), 'dark': (70, 130, 180)},
    'coral': {'light': (255, 220, 200), 'dark': (200, 120, 100)}
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
    POSITION_EDITOR = 8

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
        # Draw track with gradient
        track_surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        for i in range(self.rect.w):
            color_intensity = int(100 + (i / self.rect.w) * 50)
            pygame.draw.line(track_surface, (color_intensity, color_intensity, color_intensity), 
                           (i, 0), (i, self.rect.h))
        screen.blit(track_surface, self.rect)
        
        # Draw filled portion
        fill_width = self.knob_rect.centerx - self.rect.x
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.h)
        pygame.draw.rect(screen, COLOR_BLUE, fill_rect, border_radius=5)
        
        # Draw knob with shadow
        shadow_rect = self.knob_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.circle(screen, (30, 30, 30, 100), shadow_rect.center, self.knob_radius)
        pygame.draw.circle(screen, COLOR_DARK_GRAY, self.knob_rect.center, self.knob_radius)
        pygame.draw.circle(screen, COLOR_WHITE, self.knob_rect.center, self.knob_radius - 2)
        
        # Draw label
        label_surface = self.font.render(self.label, True, COLOR_WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 30))
        
        # Draw value
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
        self.animation_progress = 1.0 if initial_state else 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.state = not self.state

    def draw(self, screen):
        # Smooth animation
        target = 1.0 if self.state else 0.0
        self.animation_progress += (target - self.animation_progress) * 0.2
        
        # Draw label
        label_surface = self.font.render(self.label, True, COLOR_WHITE)
        screen.blit(label_surface, (self.rect.x - 250, self.rect.centery - 12))
        
        # Draw toggle background with gradient
        bg_color = tuple(int(COLOR_GRAY[i] + (COLOR_GREEN[i] - COLOR_GRAY[i]) * self.animation_progress) 
                        for i in range(3))
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=self.rect.h // 2)
        
        # Draw toggle circle with animation
        circle_x = int(self.rect.x + self.rect.h // 2 + (self.rect.w - self.rect.h) * self.animation_progress)
        pygame.draw.circle(screen, COLOR_WHITE, (circle_x, self.rect.centery), self.rect.h // 2 - 4)
        
        # Draw on/off text
        state_text = "ON" if self.state else "OFF"
        state_surface = self.font.render(state_text, True, COLOR_WHITE)
        screen.blit(state_surface, (self.rect.right + 20, self.rect.centery - 12))

    def get_value(self):
        return self.state

    def set_value(self, value):
        self.state = value
        self.animation_progress = 1.0 if value else 0.0

class Button:
    """A simple clickable button with hover effects."""
    def __init__(self, x, y, w, h, text, callback, font=None, color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.is_hovered = False
        self.font = font if font else pygame.font.Font(None, 24)
        self.color = color if color else COLOR_GRAY
        self.hover_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.callback()

    def draw(self, screen):
        # Animate hover
        target_offset = -3 if self.is_hovered else 0
        self.hover_offset += (target_offset - self.hover_offset) * 0.3
        
        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3 - self.hover_offset
        pygame.draw.rect(screen, (30, 30, 30, 100), shadow_rect, border_radius=10)
        
        # Draw button
        button_rect = self.rect.copy()
        button_rect.y += self.hover_offset
        color = LIGHT_RED if self.is_hovered else self.color
        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_WHITE, button_rect, 2, border_radius=10)
        
        # Draw text
        text_surface = self.font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surface.get_rect(center=button_rect.center)
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
        
        # Draw button with gradient
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

# --- Evaluation Bar Component ---
class EvaluationBar:
    """Visual evaluation bar showing position advantage."""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.evaluation = 0.0  # Centipawns
        self.target_eval = 0.0
        self.animation_speed = 0.1
        self.show_numeric = True
        
    def update(self, evaluation_dict):
        """Update evaluation from Stockfish output."""
        if evaluation_dict:
            if evaluation_dict['type'] == 'cp':
                self.target_eval = evaluation_dict['value'] / 100.0  # Convert to pawns
            elif evaluation_dict['type'] == 'mate':
                # Mate in N moves - show as large advantage
                mate_moves = evaluation_dict['value']
                self.target_eval = 20.0 if mate_moves > 0 else -20.0
    
    def draw(self, screen, font):
        # Animate evaluation
        self.evaluation += (self.target_eval - self.evaluation) * self.animation_speed
        
        # Draw background
        pygame.draw.rect(screen, EVAL_BAR_BG, self.rect, border_radius=5)
        
        # Calculate white percentage (50% = equal, 100% = white winning, 0% = black winning)
        # Cap evaluation display between -10 and +10 for visual clarity
        display_eval = max(-10, min(10, self.evaluation))
        white_percentage = 50 + (display_eval * 5)  # 5% per pawn
        white_percentage = max(0, min(100, white_percentage))
        
        # Draw white advantage
        white_height = int(self.rect.height * (white_percentage / 100))
        white_rect = pygame.Rect(self.rect.x, self.rect.bottom - white_height, 
                                self.rect.width, white_height)
        
        # Draw with gradient effect
        for i in range(white_rect.height):
            intensity = 240 - (i / max(1, white_rect.height)) * 40
            color = (intensity, intensity, intensity)
            pygame.draw.line(screen, color, 
                           (white_rect.x, white_rect.bottom - i),
                           (white_rect.right, white_rect.bottom - i))
        
        # Draw black advantage
        black_rect = pygame.Rect(self.rect.x, self.rect.y, 
                                self.rect.width, self.rect.height - white_height)
        for i in range(black_rect.height):
            intensity = 40 + (i / max(1, black_rect.height)) * 40
            color = (intensity, intensity, intensity)
            pygame.draw.line(screen, color,
                           (black_rect.x, black_rect.y + i),
                           (black_rect.right, black_rect.y + i))
        
        # Draw center line
        center_y = self.rect.centery
        pygame.draw.line(screen, (150, 150, 150), 
                        (self.rect.x, center_y), (self.rect.right, center_y), 2)
        
        # Draw evaluation text
        if self.show_numeric:
            if abs(self.target_eval) >= 20:
                eval_text = "M" + str(int(abs(self.target_eval)))
            else:
                eval_text = f"{self.evaluation:+.1f}"
            
            # Draw text background
            text_surface = font.render(eval_text, True, EVAL_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top - 20))
            bg_rect = text_rect.inflate(10, 5)
            pygame.draw.rect(screen, (40, 40, 40, 200), bg_rect, border_radius=3)
            screen.blit(text_surface, text_rect)
        
        # Draw border
        pygame.draw.rect(screen, COLOR_WHITE, self.rect, 2, border_radius=5)

# --- Piece Classes ---
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
    def __init__(self, board, turn, game_over_message="", gamestate=GameState.PLAYING):
        self.board = copy.deepcopy(board)
        self.turn = turn
        self.game_over_message = game_over_message
        self.gamestate = gamestate
        # Store FEN for Stockfish synchronization
        self.fen = board._board.fen() if board else None

# --- Board Class with Stockfish improvements ---
class Board:
    def __init__(self, enable_stockfish=True, stockfish_level=10, stockfish_path="stockfish-windows-x86-64-avx2.exe"):
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
        self.stockfish_path = stockfish_path
        self.stockfish_enabled = enable_stockfish
        if enable_stockfish:
            self._enable_stockfish(stockfish_level)

    def _enable_stockfish(self, level=10):
        try:
            self.board_stockfish = stockfish.Stockfish(path=self.stockfish_path)
            self.stockfish_level = level
            self.board_stockfish.set_skill_level(level)
            self.stockfish_enabled = True
        except:
            print("Stockfish not found. AI features disabled.")
            self.board_stockfish = None
            self.stockfish_enabled = False

    def _disable_stockfish(self):
        self.board_stockfish = None
        self.stockfish_enabled = False

    def restore_stockfish(self):
        """Restore Stockfish if it was enabled before."""
        if self.stockfish_enabled and not self.board_stockfish:
            self._enable_stockfish(self.stockfish_level)

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

    def clear_board(self):
        """Clear all pieces from the board."""
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.move_list = []
        self.last_move = None
        self._board = chess.Board()
        self._board.clear_board()

    def set_piece(self, row, col, piece_type, color):
        """Set a specific piece at a position."""
        piece_map = {
            'pawn': Pawn, 'knight': Knight, 'bishop': Bishop,
            'rook': Rook, 'queen': Queen, 'king': King
        }
        if piece_type in piece_map:
            self.squares[row][col] = piece_map[piece_type](color)
            if piece_type == 'king':
                self.king_position[color == 'black'] = [row, col]

    def remove_piece(self, row, col):
        """Remove a piece from a position."""
        self.squares[row][col] = 0

    def get_fen(self):
        """Get current position as FEN."""
        return self._board.fen()

    def set_from_fen(self, fen):
        """Set position from FEN string."""
        try:
            self._board = chess.Board(fen)
            self.sync_from_python_chess()
            return True
        except:
            return False

    def sync_from_python_chess(self):
        """Sync internal board from python-chess board."""
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self._board.piece_at(square)
                if piece:
                    color = 'white' if piece.color else 'black'
                    piece_map = {
                        chess.PAWN: Pawn, chess.KNIGHT: Knight, chess.BISHOP: Bishop,
                        chess.ROOK: Rook, chess.QUEEN: Queen, chess.KING: King
                    }
                    if piece.piece_type in piece_map:
                        self.squares[row][col] = piece_map[piece.piece_type](color)
                        if piece.piece_type == chess.KING:
                            self.king_position[color == 'black'] = [row, col]

    def set_stockfish(self):
        if self.board_stockfish:
            self.board_stockfish.set_fen_position(self._board.fen())

    def clear_stockfish_cache(self):
        """Clear Stockfish evaluation and best move cache."""
        current_moves = len(self.move_list)
        self.best_move_list_san = self.best_move_list_san[:current_moves]
        self.best_move_list = self.best_move_list[:current_moves]
        self.evaluation_list = self.evaluation_list[:current_moves]

    def sync_from_fen(self, fen):
        """Synchronize the internal chess board from a FEN string."""
        self._board = chess.Board(fen)
        self.clear_stockfish_cache()

    def get_evaluation(self):
        if self.board_stockfish == None:
            return None
        if len(self.evaluation_list) == len(self.move_list) + 1:
            return self.evaluation_list[-1]
        self.set_stockfish()
        try:
            self.evaluation_list.append(self.board_stockfish.get_evaluation())
        except:
            self.evaluation_list.append(None)
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
        try:
            self.best_move_list_san.append(self.board_stockfish.get_best_move())
        except:
            self.best_move_list_san.append(None)
        return self.best_move_list_san[-1]

    def push_move(self, move, making_move=True):
        self.last_move = move
        self.move_list.append(move)
        if making_move:
            self._board.push_san(move.san())
        # Clear the best move cache when a move is made
        self.clear_stockfish_cache()

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
        new.stockfish_enabled = self.stockfish_enabled
        new.stockfish_level = self.stockfish_level
        new.stockfish_path = self.stockfish_path
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

# --- Position Editor ---
class PositionEditor:
    """Custom position editor for setting up chess positions."""
    def __init__(self):
        self.selected_piece = None
        self.selected_color = 'white'
        self.turn = 'white'
        self.editing_board = Board(enable_stockfish=False)
        self.editing_board.clear_board()
        
    def get_piece_types(self):
        return ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
    
    def place_piece(self, row, col):
        """Place selected piece at position."""
        if self.selected_piece:
            self.editing_board.set_piece(row, col, self.selected_piece, self.selected_color)
    
    def remove_piece(self, row, col):
        """Remove piece from position."""
        self.editing_board.remove_piece(row, col)
    
    def clear_board(self):
        """Clear all pieces."""
        self.editing_board.clear_board()
    
    def set_starting_position(self):
        """Set standard starting position."""
        self.editing_board = Board(enable_stockfish=False)
    
    def get_fen(self):
        """Get FEN of current position."""
        # Build FEN from current board state
        fen_rows = []
        for row in range(8):
            empty_count = 0
            row_str = ""
            for col in range(8):
                piece = self.editing_board.squares[row][col]
                if piece == 0:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    piece_char_map = {
                        'pawn': 'p', 'knight': 'n', 'bishop': 'b',
                        'rook': 'r', 'queen': 'q', 'king': 'k'
                    }
                    char = piece_char_map[piece.name]
                    if piece.color == 'white':
                        char = char.upper()
                    row_str += char
            if empty_count > 0:
                row_str += str(empty_count)
            fen_rows.append(row_str)
        
        fen = '/'.join(fen_rows)
        fen += f" {'w' if self.turn == 'white' else 'b'} KQkq - 0 1"
        return fen

# --- Main Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Enhanced Chess')
        self.clock = pygame.time.Clock()
        
        # Load fonts
        try:
            self.piece_font = pygame.font.Font(FONT_NAME, int(SQSIZE * 0.8))
            self.coord_font = pygame.font.Font(FONT_NAME, int(SQSIZE * 0.25))
        except FileNotFoundError:
            print(f"Error: Font '{FONT_NAME}' not found. Using default font.")
            self.piece_font = pygame.font.Font(None, int(SQSIZE * 0.8))
            self.coord_font = pygame.font.Font(None, int(SQSIZE * 0.25))
        
        self.menu_font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 60)
        
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
        
        # Evaluation bar
        self.eval_bar = EvaluationBar(WIDTH - EVAL_BAR_WIDTH - 20, 40, EVAL_BAR_WIDTH, EVAL_BAR_HEIGHT)
        
        # Position editor
        self.position_editor = PositionEditor()
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 100
        
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
                self.show_evaluation_bar = settings.get("show_evaluation_bar", True)
                self.stockfish_difficulty = settings.get("stockfish_difficulty", 10)
                self.board_theme = settings.get("board_theme", "classic")
                self.show_coordinates = settings.get("show_coordinates", True)
                self.show_last_move = settings.get("show_last_move", True)
                self.auto_promote_queen = settings.get("auto_promote_queen", False)
                self.enable_undo = settings.get("enable_undo", True)
                self.permanent_undo = settings.get("permanent_undo", True)
                self.show_legal_moves = settings.get("show_legal_moves", True)
                self.animation_speed = settings.get("animation_speed", 500)
                print("Settings loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Settings file not found. Using default settings.")
            self.board_perspective = GameState.WHITE_PERSPECTIVE
            self.show_stockfish_hints = True
            self.show_evaluation_bar = True
            self.stockfish_difficulty = 10
            self.board_theme = "classic"
            self.show_coordinates = True
            self.show_last_move = True
            self.auto_promote_queen = False
            self.enable_undo = True
            self.permanent_undo = True
            self.show_legal_moves = True
            self.animation_speed = 500

    def save_settings(self):
        """Save current settings to JSON file."""
        settings = {
            "perspective": "white" if self.perspective_toggle.get_value() else "black",
            "show_hints": self.hints_toggle.get_value(),
            "show_evaluation_bar": self.eval_bar_toggle.get_value(),
            "stockfish_difficulty": self.difficulty_slider.get_value(),
            "board_theme": self.theme_button.get_value(),
            "show_coordinates": self.coord_toggle.get_value(),
            "show_last_move": self.last_move_toggle.get_value(),
            "auto_promote_queen": self.auto_promote_toggle.get_value(),
            "enable_undo": self.undo_toggle.get_value(),
            "permanent_undo": self.permanent_undo_toggle.get_value(),
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
        y_spacing = 45
        
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
        self.eval_bar_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Show Evaluation Bar",
            self.show_evaluation_bar,
            self.menu_font
        )
        row += 1
        
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
        
        self.permanent_undo_toggle = ToggleButton(
            left_col, y_start + (row * y_spacing), 60, 25,
            "Permanent Undo",
            self.permanent_undo,
            self.menu_font
        )
        row += 1
        
        # AI Settings
        self.difficulty_slider = Slider(
            150, y_start + (row * y_spacing) + 15, 400, 15,
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
            self.eval_bar_toggle,
            self.hints_toggle,
            self.last_move_toggle,
            self.legal_moves_toggle,
            self.auto_promote_toggle,
            self.undo_toggle,
            self.permanent_undo_toggle,
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
        self.show_evaluation_bar = self.eval_bar_toggle.get_value()
        self.stockfish_difficulty = self.difficulty_slider.get_value()
        self.board_theme = self.theme_button.get_value()
        self.show_coordinates = self.coord_toggle.get_value()
        self.show_last_move = self.last_move_toggle.get_value()
        self.auto_promote_queen = self.auto_promote_toggle.get_value()
        self.enable_undo = self.undo_toggle.get_value()
        self.permanent_undo = self.permanent_undo_toggle.get_value()
        self.show_legal_moves = self.legal_moves_toggle.get_value()
        self.animation_speed = self.animation_slider.get_value()
        
        # Update board if it exists
        if self.board:
            if self.board.board_stockfish:
                self.board.set_stockfish_level(self.stockfish_difficulty)
            
            # Update Stockfish state based on settings
            if self.show_stockfish_hints or self.show_evaluation_bar or self.game_mode == 'stockfish':
                if not self.board.board_stockfish:
                    self.board._enable_stockfish(self.stockfish_difficulty)
            else:
                if self.game_mode != 'stockfish':
                    self.board._disable_stockfish()
        
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
        self.eval_bar_toggle.set_value(True)
        self.hints_toggle.set_value(True)
        self.difficulty_slider.set_value(10)
        self.theme_button.set_value("classic")
        self.coord_toggle.set_value(True)
        self.last_move_toggle.set_value(True)
        self.auto_promote_toggle.set_value(False)
        self.undo_toggle.set_value(True)
        self.permanent_undo_toggle.set_value(True)
        self.legal_moves_toggle.set_value(True)
        self.animation_slider.set_value(500)

    def save_game_state(self):
        """Save current game state to history."""
        if self.enable_undo:
            # If permanent undo is enabled, remove future states when making a new move
            if self.permanent_undo and self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            
            # Add new state
            snapshot = GameSnapshot(self.board, self.turn, self.game_over_message, self.gamestate)
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
            self.restore_game_state(self.history_index)
            print(f"Undone move. Now at move {self.history_index}")

    def redo_move(self):
        """Redo a previously undone move."""
        if self.enable_undo and not self.permanent_undo and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore_game_state(self.history_index)
            print(f"Redone move. Now at move {self.history_index}")

    def restore_game_state(self, index):
        """Restore game state from history at given index."""
        if 0 <= index < len(self.history):
            snapshot = self.history[index]
            self.board = copy.deepcopy(snapshot.board)
            self.turn = snapshot.turn
            self.game_over_message = snapshot.game_over_message
            
            # Restore gamestate (allow undoing from game over)
            if snapshot.game_over_message:
                self.gamestate = GameState.GAME_OVER
            else:
                self.gamestate = GameState.PLAYING
            
            # Restore Stockfish connection if needed
            if (self.show_stockfish_hints or self.show_evaluation_bar or self.game_mode == 'stockfish') and self.board:
                self.board.restore_stockfish()
                # Sync Stockfish with the restored FEN position
                if snapshot.fen and self.board.board_stockfish:
                    self.board.sync_from_fen(snapshot.fen)
                    self.board.set_stockfish()
            
            # Recalculate valid moves for the current position
            self.calc_all_valid_moves(self.turn)

    def reset(self):
        """Reset the game with current settings."""
        # Initialize board
        enable_stockfish = self.show_stockfish_hints or self.show_evaluation_bar or self.game_mode == 'stockfish'
        self.board = Board(enable_stockfish=enable_stockfish, stockfish_level=self.stockfish_difficulty)
        
        if not (self.show_stockfish_hints or self.show_evaluation_bar) and self.game_mode != 'stockfish':
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
            elif self.gamestate == GameState.POSITION_EDITOR:
                self.show_position_editor()
                self.handle_position_editor_events()
            elif self.gamestate == GameState.PLAYING:
                self.show_bg()
                if self.show_coordinates:
                    self.show_board_coordinates()
                if self.show_last_move:
                    self.show_last_move_highlight()
                if self.show_stockfish_hints and self.board and self.board.board_stockfish:
                    self.show_best_move()
                if self.show_legal_moves:
                    self.show_moves()
                self.show_pieces()
                if self.dragger.dragging:
                    self.dragger.update_blit(self.screen, self.piece_font)
                if self.show_evaluation_bar and self.board and self.board.board_stockfish:
                    self.update_and_show_eval_bar()
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
                if self.show_evaluation_bar and self.board and self.board.board_stockfish:
                    self.update_and_show_eval_bar()
                self.show_game_over()
                self.handle_game_over_events()
                
            pygame.display.update()
            self.clock.tick(60)

    # --- Drawing Methods ---
    def show_bg(self):
        self.screen.fill((0, 0, 0))
        theme = BOARD_THEMES[self.board_theme]
        
        # Draw board with gradient effect
        for row in range(ROWS):
            for col in range(COLS):
                state = 0
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    state = 1
                base_color = theme['light'] if (row + col) % 2 == state else theme['dark']
                
                # Create gradient effect
                rect = pygame.Rect(col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(self.screen, base_color, rect)
                
                # Add subtle gradient overlay
                overlay = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                for i in range(SQSIZE // 4):
                    alpha = 20 - (i * 2)
                    rect = pygame.Rect(i, i, SQSIZE - 2*i, SQSIZE - 2*i)
                    pygame.draw.rect(overlay, (255, 255, 255), 
                                   rect)
                self.screen.blit(overlay, rect)

    def show_board_coordinates(self):
        """Show enhanced board coordinates with backgrounds."""
        theme = BOARD_THEMES[self.board_theme]
        
        # Draw coordinate backgrounds
        coord_bg = pygame.Surface((BOARD_SIZE, 30), pygame.SRCALPHA)
        coord_bg.fill(COORD_BG_COLOR)
        self.screen.blit(coord_bg, (0, BOARD_SIZE - 30))
        
        side_bg = pygame.Surface((30, BOARD_SIZE - 30), pygame.SRCALPHA)
        side_bg.fill(COORD_BG_COLOR)
        self.screen.blit(side_bg, (BOARD_SIZE - 30, 0))
        
        for i in range(8):
            # File labels (a-h)
            file_label = chr(ord('a') + i)
            if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                file_label = chr(ord('h') - i)
            
            # Draw file label with background
            text = self.coord_font.render(file_label, True, COLOR_WHITE)
            text_rect = text.get_rect(center=(i * SQSIZE + SQSIZE // 2, BOARD_SIZE - 15))
            self.screen.blit(text, text_rect)
            
            # Rank labels (1-8)
            rank_label = str(8 - i)
            if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                rank_label = str(i + 1)
            
            # Draw rank label with background
            text = self.coord_font.render(rank_label, True, COLOR_WHITE)
            text_rect = text.get_rect(center=(BOARD_SIZE - 15, i * SQSIZE + SQSIZE // 2))
            self.screen.blit(text, text_rect)

    def show_pieces(self):
        if not self.board:
            return
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col]
                if piece != 0 and piece != self.dragger.piece:
                    text_surface = self.piece_font.render(piece.char, True, piece.font_color)
                    cur_row = row
                    cur_col = col
                    if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                        cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                    
                    # Add shadow for pieces
                    shadow_surface = self.piece_font.render(piece.char, True, (50, 50, 50, 100))
                    shadow_rect = shadow_surface.get_rect(center=(cur_col * SQSIZE + SQSIZE // 2 + 2, 
                                                                 cur_row * SQSIZE + SQSIZE // 2 + 2))
                    self.screen.blit(shadow_surface, shadow_rect)
                    
                    text_rect = text_surface.get_rect(center=(cur_col * SQSIZE + SQSIZE // 2, 
                                                             cur_row * SQSIZE + SQSIZE // 2))
                    self.screen.blit(text_surface, text_rect)

    def show_moves(self):
        if self.dragger.dragging:
            for move in self.dragger.piece.moves:
                cur_col = move.final.x
                cur_row = move.final.y
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                
                # Draw circle for legal moves
                center = (cur_col * SQSIZE + SQSIZE // 2, cur_row * SQSIZE + SQSIZE // 2)
                if self.board.squares[int(move.final.y)][int(move.final.x)] != 0:
                    # Capture move - draw ring
                    pygame.draw.circle(self.screen, (200, 50, 50, 150), center, SQSIZE // 3, 4)
                else:
                    # Normal move - draw dot
                    pygame.draw.circle(self.screen, (100, 100, 100, 150), center, SQSIZE // 6)

    def show_last_move_highlight(self):
        if self.board and self.board.last_move:
            for pos in [self.board.last_move.initial, self.board.last_move.final]:
                color = (255, 220, 0, 80)
                s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                s.fill(color)
                cur_col = pos.x
                cur_row = pos.y
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                self.screen.blit(s, (cur_col * SQSIZE, cur_row * SQSIZE))

    def show_best_move(self):
        if self.board and self.board.board_stockfish != None:
            best_move = self.board.get_best_move()
            if best_move:
                # Draw arrow for best move
                start_pos = best_move[0]
                end_pos = best_move[1]
                
                start_col, start_row = start_pos.x, start_pos.y
                end_col, end_row = end_pos.x, end_pos.y
                
                if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                    start_row, start_col = rotate_matrix_index(start_row, start_col, ROWS, COLS, 2)
                    end_row, end_col = rotate_matrix_index(end_row, end_col, ROWS, COLS, 2)
                
                start_center = (start_col * SQSIZE + SQSIZE // 2, start_row * SQSIZE + SQSIZE // 2)
                end_center = (end_col * SQSIZE + SQSIZE // 2, end_row * SQSIZE + SQSIZE // 2)
                
                # Draw arrow
                pygame.draw.line(self.screen, (0, 200, 0, 150), start_center, end_center, 5)
                
                # Draw arrowhead
                angle = math.atan2(end_center[1] - start_center[1], end_center[0] - start_center[0])
                arrow_length = 20
                arrow_angle = math.pi / 6
                
                point1 = (end_center[0] - arrow_length * math.cos(angle - arrow_angle),
                         end_center[1] - arrow_length * math.sin(angle - arrow_angle))
                point2 = (end_center[0] - arrow_length * math.cos(angle + arrow_angle),
                         end_center[1] - arrow_length * math.sin(angle + arrow_angle))
                
                pygame.draw.polygon(self.screen, (0, 200, 0, 150), [end_center, point1, point2])

    def update_and_show_eval_bar(self):
        """Update and display the evaluation bar."""
        if self.board and self.board.board_stockfish:
            evaluation = self.board.get_evaluation()
            self.eval_bar.update(evaluation)
            self.eval_bar.draw(self.screen, self.small_font)

    def show_move_history(self):
        """Show move counter and undo/redo hints."""
        if self.enable_undo:
            text = f"Move: {self.history_index}/{len(self.history)-1}"
            if self.history_index > 0:
                text += " [← Undo]"
            if not self.permanent_undo and self.history_index < len(self.history) - 1:
                text += " [Redo →]"
            
            # Draw background for text
            surface = self.small_font.render(text, True, COLOR_WHITE)
            text_rect = surface.get_rect(topleft=(10, 10))
            bg_rect = text_rect.inflate(10, 5)
            pygame.draw.rect(self.screen, (40, 40, 40, 200), bg_rect, border_radius=3)
            self.screen.blit(surface, text_rect)
            
            # Show permanent undo status
            if self.permanent_undo:
                perm_text = "Permanent Undo ON"
                perm_surface = self.small_font.render(perm_text, True, COLOR_GREEN)
                perm_rect = perm_surface.get_rect(topleft=(10, 35))
                bg_rect = perm_rect.inflate(10, 5)
                pygame.draw.rect(self.screen, (40, 40, 40, 200), bg_rect, border_radius=3)
                self.screen.blit(perm_surface, perm_rect)

    def show_position_editor(self):
        """Display the position editor interface."""
        self.screen.fill(EDITOR_BG_COLOR)
        
        # Title
        title = self.title_font.render('Position Editor', True, COLOR_WHITE)
        self.screen.blit(title, (WIDTH/2 - title.get_width()/2, 20))
        
        # Draw board
        board_offset_x = 150
        board_offset_y = 100
        
        # Draw board background
        for row in range(8):
            for col in range(8):
                color = WHITE_SQUARE if (row + col) % 2 == 0 else BROWN
                rect = pygame.Rect(board_offset_x + col * 70, board_offset_y + row * 70, 70, 70)
                pygame.draw.rect(self.screen, color, rect)
        
        # Draw pieces on editor board
        for row in range(8):
            for col in range(8):
                piece = self.position_editor.editing_board.squares[row][col]
                if piece != 0:
                    piece_font = pygame.font.Font(None, 60)
                    text = piece_font.render(piece.char, True, piece.font_color)
                    text_rect = text.get_rect(center=(board_offset_x + col * 70 + 35, 
                                                     board_offset_y + row * 70 + 35))
                    self.screen.blit(text, text_rect)
        
        # Draw piece palette
        palette_x = 750
        palette_y = 100
        pygame.draw.rect(self.screen, PALETTE_BG_COLOR, 
                        (palette_x - 10, palette_y - 10, 180, 400), border_radius=10)
        
        palette_title = self.menu_font.render("Pieces", True, COLOR_WHITE)
        self.screen.blit(palette_title, (palette_x + 50, palette_y - 5))
        
        # Color selector
        colors = ['white', 'black']
        for i, color in enumerate(colors):
            y = palette_y + 40 + i * 40
            color_rect = pygame.Rect(palette_x, y, 160, 35)
            if self.position_editor.selected_color == color:
                pygame.draw.rect(self.screen, COLOR_GREEN, color_rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, COLOR_GRAY, color_rect, border_radius=5)
            
            text = self.menu_font.render(color.capitalize(), True, COLOR_WHITE)
            text_rect = text.get_rect(center=color_rect.center)
            self.screen.blit(text, text_rect)
        
        # Piece selector
        piece_types = self.position_editor.get_piece_types()
        for i, piece_type in enumerate(piece_types):
            row = i // 2
            col = i % 2
            x = palette_x + col * 80
            y = palette_y + 130 + row * 60
            
            piece_rect = pygame.Rect(x, y, 70, 50)
            if self.position_editor.selected_piece == piece_type:
                pygame.draw.rect(self.screen, COLOR_BLUE, piece_rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, COLOR_DARK_GRAY, piece_rect, border_radius=5)
            
            # Draw piece symbol
            char = UNICODE_PIECES[f'{self.position_editor.selected_color[0]}_{piece_type}']
            piece_font = pygame.font.Font(None, 40)
            text = piece_font.render(char, True, PIECE_COLORS[self.position_editor.selected_color])
            text_rect = text.get_rect(center=piece_rect.center)
            self.screen.blit(text, text_rect)
        
        # Turn selector
        turn_y = 680
        turn_text = self.menu_font.render("Turn to move:", True, COLOR_WHITE)
        self.screen.blit(turn_text, (board_offset_x, turn_y))
        
        for i, color in enumerate(['white', 'black']):
            x = board_offset_x + 150 + i * 100
            turn_rect = pygame.Rect(x, turn_y - 5, 80, 35)
            if self.position_editor.turn == color:
                pygame.draw.rect(self.screen, COLOR_GREEN, turn_rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, COLOR_GRAY, turn_rect, border_radius=5)
            
            text = self.menu_font.render(color.capitalize(), True, COLOR_WHITE)
            text_rect = text.get_rect(center=turn_rect.center)
            self.screen.blit(text, text_rect)
        
        # Control buttons
        button_y = 730
        
        clear_btn = Button(board_offset_x, button_y, 100, 40, "Clear", 
                          self.position_editor.clear_board, self.menu_font, COLOR_DARK_GRAY)
        clear_btn.draw(self.screen)
        
        start_btn = Button(board_offset_x + 110, button_y, 120, 40, "Start Pos", 
                          self.position_editor.set_starting_position, self.menu_font, COLOR_DARK_GRAY)
        start_btn.draw(self.screen)
        
        analyze_btn = Button(board_offset_x + 240, button_y, 120, 40, "Analyze", 
                            self.analyze_position, self.menu_font, COLOR_BLUE)
        analyze_btn.draw(self.screen)
        
        back_btn = Button(board_offset_x + 370, button_y, 100, 40, "Back", 
                         lambda: setattr(self, 'gamestate', GameState.MENU), 
                         self.menu_font, COLOR_GRAY)
        back_btn.draw(self.screen)
        
        # FEN display
        fen_y = 720
        fen_text = self.small_font.render("FEN: " + self.position_editor.get_fen()[:50], True, COLOR_WHITE)
        self.screen.blit(fen_text, (palette_x - 50, fen_y))
        
        # Instructions
        inst_text = "Left click: Place piece | Right click: Remove piece"
        inst = self.small_font.render(inst_text, True, COLOR_LIGHT_GRAY)
        self.screen.blit(inst, (WIDTH/2 - inst.get_width()/2, 70))

    def analyze_position(self):
        """Analyze the custom position."""
        fen = self.position_editor.get_fen()
        self.board = Board(enable_stockfish=True, stockfish_level=self.stockfish_difficulty)
        if self.board.set_from_fen(fen):
            self.turn = self.position_editor.turn
            self.gamestate = GameState.PLAYING
            self.game_mode = 'analysis'
            self.calc_all_valid_moves(self.turn)
            self.save_game_state()
        else:
            print("Invalid position")

    def handle_position_editor_events(self):
        """Handle events in position editor."""
        board_offset_x = 150
        board_offset_y = 100
        palette_x = 750
        palette_y = 100
        turn_y = 680
        button_y = 730
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.gamestate = GameState.MENU
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                
                # Check board clicks
                if (board_offset_x <= mouse_x < board_offset_x + 560 and 
                    board_offset_y <= mouse_y < board_offset_y + 560):
                    col = (mouse_x - board_offset_x) // 70
                    row = (mouse_y - board_offset_y) // 70
                    
                    if event.button == 1:  # Left click - place piece
                        self.position_editor.place_piece(row, col)
                    elif event.button == 3:  # Right click - remove piece
                        self.position_editor.remove_piece(row, col)
                
                # Check color selector
                for i, color in enumerate(['white', 'black']):
                    y = palette_y + 40 + i * 40
                    color_rect = pygame.Rect(palette_x, y, 160, 35)
                    if color_rect.collidepoint(event.pos):
                        self.position_editor.selected_color = color
                
                # Check piece selector
                piece_types = self.position_editor.get_piece_types()
                for i, piece_type in enumerate(piece_types):
                    row = i // 2
                    col = i % 2
                    x = palette_x + col * 80
                    y = palette_y + 130 + row * 60
                    piece_rect = pygame.Rect(x, y, 70, 50)
                    if piece_rect.collidepoint(event.pos):
                        self.position_editor.selected_piece = piece_type
                
                # Check turn selector
                for i, color in enumerate(['white', 'black']):
                    x = board_offset_x + 150 + i * 100
                    turn_rect = pygame.Rect(x, turn_y - 5, 80, 35)
                    if turn_rect.collidepoint(event.pos):
                        self.position_editor.turn = color
                
                # Check buttons
                buttons = [
                    (board_offset_x, button_y, 100, 40, self.position_editor.clear_board),
                    (board_offset_x + 110, button_y, 120, 40, self.position_editor.set_starting_position),
                    (board_offset_x + 240, button_y, 120, 40, self.analyze_position),
                    (board_offset_x + 370, button_y, 100, 40, lambda: setattr(self, 'gamestate', GameState.MENU))
                ]
                
                for x, y, w, h, callback in buttons:
                    if pygame.Rect(x, y, w, h).collidepoint(event.pos):
                        callback()

    def show_settings(self):
        """Display the settings menu."""
        self.screen.fill(MENU_BG_COLOR)
        
        # Draw gradient background
        for i in range(HEIGHT):
            color_intensity = int(49 + (i / HEIGHT) * 20)
            pygame.draw.line(self.screen, (color_intensity, color_intensity - 3, color_intensity - 6), 
                           (0, i), (WIDTH, i))
        
        # Title
        title_text = 'Game Settings' if self.gamestate == GameState.IN_GAME_SETTINGS else 'Settings'
        title = self.title_font.render(title_text, True, self.menu_title_color)
        title_rect = title.get_rect(center=(WIDTH/2, 50))
        
        # Draw title with shadow
        shadow = self.title_font.render(title_text, True, (30, 30, 30))
        shadow_rect = shadow.get_rect(center=(WIDTH/2 + 3, 53))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        # Instructions
        if self.gamestate == GameState.IN_GAME_SETTINGS:
            inst_text = "Press ESC to return to game"
            inst = self.small_font.render(inst_text, True, COLOR_GRAY)
            self.screen.blit(inst, (WIDTH/2 - inst.get_width()/2, 85))
        
        # Update perspective label
        persp_text = "Black Perspective" if not self.perspective_toggle.get_value() else "White Perspective"
        self.perspective_toggle.label = persp_text
        
        # Draw all UI elements
        for element in self.settings_ui_elements:
            element.draw(self.screen)
        
        # Draw difficulty level text with background
        diff_names = {0: "Beginner", 5: "Easy", 10: "Medium", 15: "Hard", 20: "Master"}
        diff_level = self.difficulty_slider.get_value()
        closest_key = min(diff_names.keys(), key=lambda x: abs(x - diff_level))
        diff_text = diff_names[closest_key]
        
        diff_surface = self.menu_font.render(diff_text, True, COLOR_WHITE)
        diff_rect = diff_surface.get_rect(center=(self.difficulty_slider.rect.right + 100, 
                                                  self.difficulty_slider.rect.centery))
        bg_rect = diff_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (60, 60, 60, 200), bg_rect, border_radius=5)
        self.screen.blit(diff_surface, diff_rect)

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
                elif event.key == pygame.K_RIGHT and self.enable_undo and not self.permanent_undo:
                    # Redo move (only if permanent undo is off)
                    self.redo_move()
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.dragger.update_mouse(event.pos)
                if event.pos[0] < BOARD_SIZE:  # Only interact with board area
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
                if event.pos[0] < BOARD_SIZE:  # Only if released on board
                    cur_row, cur_col = self.dragger.mouseY // SQSIZE, self.dragger.mouseX // SQSIZE
                    if self.board_perspective == GameState.BLACK_PERSPECTIVE:
                        cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
                    initial = pygame.math.Vector2(self.dragger.initial_col, self.dragger.initial_row)
                    final = pygame.math.Vector2(cur_col, cur_row)
                    move = Move(initial, final)
                    if move in self.dragger.piece.moves: 
                        self.make_move(self.dragger.piece, move)
                self.dragger.undrag_piece()
    
    def handle_game_over_events(self):
        """Handle events when game is over."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and self.enable_undo:
                    # Allow undoing even from game over state
                    self.undo_move()
                elif event.key == pygame.K_ESCAPE:
                    self.gamestate = GameState.MENU
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN: 
                self.gamestate = GameState.MENU
                self.reset()

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
        if not self.board:
            return
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
        """Display enhanced main menu."""
        # Animated gradient background
        for i in range(HEIGHT):
            time_offset = pygame.time.get_ticks() * 0.001
            color_intensity = int(49 + math.sin(time_offset + i * 0.01) * 10)
            pygame.draw.line(self.screen, (color_intensity, color_intensity - 3, color_intensity - 6), 
                           (0, i), (WIDTH, i))
        
        # Title with glow effect
        glow_intensity = int(128 + math.sin(pygame.time.get_ticks() * 0.003) * 127)
        glow_color = (glow_intensity, glow_intensity, glow_intensity // 2)
        
        # Draw title glow
        for offset in range(5, 0, -1):
            alpha = 50 - offset * 10
            glow_surf = pygame.font.Font(None, 74 + offset * 2).render('Enhanced Chess', True, (*glow_color, alpha))
            glow_rect = glow_surf.get_rect(center=(WIDTH/2, 100))
            self.screen.blit(glow_surf, glow_rect)
        
        # Main title
        title = pygame.font.Font(None, 74).render('Enhanced Chess', True, self.menu_title_color)
        title_rect = title.get_rect(center=(WIDTH/2, 100))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.menu_font.render('Professional Edition', True, COLOR_GRAY)
        subtitle_rect = subtitle.get_rect(center=(WIDTH/2, 150))
        self.screen.blit(subtitle, subtitle_rect)
       
    def handle_menu_animations(self):
        """Handle menu button animations."""
        self.mouse_position = pygame.mouse.get_pos()
        
        # Create animated menu items with icons
        menu_items = [
            ('♔ 1 vs 1 (Local)', (WIDTH//2, 250)),
            ('🎲 1 vs Random', (WIDTH//2, 320)),
            ('🤖 1 vs Stockfish', (WIDTH//2, 390)),
            ('✏️ Position Editor', (WIDTH//2, 460)),
            ('⚙️ Settings', (WIDTH//2, 530)),
            ('❌ Exit', (WIDTH//2, 600))
        ]
        
        self.menu_rects = []
        for text, pos in menu_items:
            rect = self.menu_text(text, pos, 45)
            self.menu_rects.append(rect)
      
    def menu_text(self, text, center, size):
        """Draw menu text with hover effects."""
        text_rect = pygame.font.Font(None, size).render(text, True, self.menu_font_color).get_rect(center=center)
        
        if text_rect.collidepoint(self.mouse_position):
            # Draw hover background
            bg_rect = text_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (255, 255, 255, 30), bg_surface.get_rect(), border_radius=10)
            self.screen.blit(bg_surface, bg_rect)
            
            # Draw text with animation
            offset = math.sin(pygame.time.get_ticks() * 0.005) * 3
            self.handle_text(text, self.menu_font_animated_color, (center[0] + offset, center[1]), size)
        else:
            self.handle_text(text, self.menu_font_color, center, size)
        
        return text_rect

    def handle_text(self, text, color, center, size):
        """Draw text with shadow."""
        # Draw shadow
        shadow = pygame.font.Font(None, size).render(text, True, (30, 30, 30))
        shadow_rect = shadow.get_rect(center=(center[0] + 2, center[1] + 2))
        self.screen.blit(shadow, shadow_rect)
        
        # Draw main text
        text_surface = pygame.font.Font(None, size).render(text, True, color)
        text_rect = text_surface.get_rect(center=center)
        self.screen.blit(text_surface, text_rect)
        
    def handle_menu_events(self):
        """Handle menu click events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if len(self.menu_rects) >= 6:
                    if self.menu_rects[0].collidepoint(event.pos):  # 1 vs 1
                        self.game_mode = 'pvp'
                        self.gamestate = GameState.PLAYING
                        self.reset()
                    elif self.menu_rects[1].collidepoint(event.pos):  # vs Random
                        self.game_mode = 'random'
                        self.gamestate = GameState.PLAYING
                        self.reset()
                    elif self.menu_rects[2].collidepoint(event.pos):  # vs Stockfish
                        self.game_mode = 'stockfish'
                        self.gamestate = GameState.PLAYING
                        self.reset()
                    elif self.menu_rects[3].collidepoint(event.pos):  # Position Editor
                        self.gamestate = GameState.POSITION_EDITOR
                    elif self.menu_rects[4].collidepoint(event.pos):  # Settings
                        self.gamestate = GameState.SETTINGS
                    elif self.menu_rects[5].collidepoint(event.pos):  # Exit
                        pygame.quit()
                        sys.exit()

    def show_promotion_menu(self):
        """Display promotion menu with enhanced visuals."""
        cur_row, cur_col = self.promotion_pos
        if self.board_perspective == GameState.BLACK_PERSPECTIVE:
            cur_row, cur_col = rotate_matrix_index(cur_row, cur_col, ROWS, COLS, 2)
        cur_row = cur_row * SQSIZE if self.turn == self.get_board_perspective() else (cur_row - 3) * SQSIZE

        # Draw background with transparency
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Draw promotion panel
        rect = pygame.Rect(cur_col * SQSIZE - 10, cur_row - 10, SQSIZE + 20, SQSIZE * 4 + 20)
        pygame.draw.rect(self.screen, MENU_BG_COLOR, rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 3, border_radius=15)
        
        self.promotion_options = {}
        for i, name in enumerate(self.promotion_pieces):
            promo_rect = pygame.Rect(cur_col * SQSIZE, cur_row + i * SQSIZE, SQSIZE, SQSIZE)
            self.promotion_options[name] = promo_rect
            
            # Hover effect
            if promo_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (100, 100, 200, 100), promo_rect, border_radius=5)
            
            char = UNICODE_PIECES[f'{self.turn[0]}_{name}']
            text_surf = self.piece_font.render(char, True, PIECE_COLORS[self.turn])
            self.screen.blit(text_surf, text_surf.get_rect(center=promo_rect.center))

    def handle_promotion_events(self):
        """Handle promotion selection."""
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
        """Display enhanced game over screen."""
        # Dark overlay with gradient
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(HEIGHT):
            alpha = int(150 * (1 - abs(i - HEIGHT/2) / (HEIGHT/2)))
            pygame.draw.line(overlay, (0, 0, 0, alpha), (0, i), (WIDTH, i))
        self.screen.blit(overlay, (0, 0))
        
        # Main message with glow
        for offset in range(5, 0, -1):
            glow_alpha = 100 - offset * 20
            glow_surf = pygame.font.Font(None, 60 + offset * 2).render(
                self.game_over_message, True, (255, 255, 255, glow_alpha))
            glow_rect = glow_surf.get_rect(center=(WIDTH/2, HEIGHT/2 - 20))
            self.screen.blit(glow_surf, glow_rect)
        
        text = pygame.font.Font(None, 60).render(self.game_over_message, True, FONT_COLOR)
        text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 - 20))
        self.screen.blit(text, text_rect)
        
        # Instructions
        prompt = pygame.font.Font(None, 35).render("Click to return to menu | ← to undo", True, COLOR_LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(WIDTH/2, HEIGHT/2 + 40))
        self.screen.blit(prompt, prompt_rect)
        
        # Display final evaluation if available
        if self.board and self.board.board_stockfish and self.show_evaluation_bar:
            eval_text = "Final Position: "
            evaluation = self.board.get_evaluation()
            if evaluation:
                if evaluation['type'] == 'mate':
                    eval_text += f"Mate in {abs(evaluation['value'])}"
                else:
                    eval_text += f"{evaluation['value']/100:+.2f}"
            
            eval_surface = self.menu_font.render(eval_text, True, EVAL_TEXT_COLOR)
            eval_rect = eval_surface.get_rect(center=(WIDTH/2, HEIGHT/2 + 90))
            self.screen.blit(eval_surface, eval_rect)

if __name__ == '__main__':
    game = Game()
    game.mainloop()