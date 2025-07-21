# -- Libraries --
import sys
import os
import copy
import random
import pygame
import stockfish 
import chess


# --- Constants ---
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQSIZE = WIDTH // COLS
FONT_NAME = 'Quivira.ttf' # Make sure this font file is in the same directory

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

# --- Game States ---
class GameState:
    MENU = 0
    PLAYING = 1
    PROMOTING = 2
    GAME_OVER = 3

# --- Piece Class (Base) ---
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

# --- Subclasses for each Piece ---
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
        self.initial = initial # pygame.math.Vector2
        self.final = final   # pygame.math.Vector2
        self.valid = self.check_valid

    def check_valid(self):
        return 0<=self.initial.x<8 and 0<=self.initial.y<8 and 0<=self.final.x<8 and 0<=self.final.y<8

    def san(self):
        return chr(97+int(self.initial.x))+str(8 - int(self.initial.y))+chr(97+int(self.final.x))+str(8 - int(self.final.y))

    def __eq__(self, other):
        return self.initial == other.initial and self.final == other.final

# --- Board Class ---
class Board:
    def __init__(self, enable_stockfish = False):
        self.squares = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.last_move = None
        self.move_list = []
        self._create_board()
        self._add_pieces('white')
        self._add_pieces('black')
        self._board = chess.Board()
        self.board_stockfish = None
        if enable_stockfish:
            self.board_stockfish = stockfish.Stockfish(path = "stockfish-windows-x86-64-avx2.exe")

    def _enable_stockfish(self):
        self.board_stockfish = stockfish.Stockfish(path = "stockfish-windows-x86-64-avx2.exe")

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

    def move(self, piece, move, making_move = True):
        if making_move and self.check_promotion(piece, move.final) == False:
            self._board.push_san(move.san())

        initial_row, initial_col = int(move.initial.y), int(move.initial.x)
        final_row, final_col = int(move.final.y), int(move.final.x)

        if isinstance(piece, Pawn) and abs(final_row - initial_row) == 1 and abs(final_col - initial_col) == 1 and not self.squares[final_row][final_col]:
            self.squares[initial_row][final_col] = 0
        if isinstance(piece, King) and abs(final_col - initial_col) == 2:
            rook_col = 0 if final_col < initial_col else 7
            new_rook_col = 3 if final_col < initial_col else 5
            rook = self.squares[initial_row][rook_col]
            self.squares[initial_row][new_rook_col] = rook
            self.squares[initial_row][rook_col] = 0
            rook.moved = True

        self.squares[initial_row][initial_col] = 0
        self.squares[final_row][final_col] = piece
        piece.moved = True
        self.last_move = move
        self.move_list.append(move)

    def check_promotion(self, piece, final_pos):
        return isinstance(piece, Pawn) and (final_pos.y == 0 or final_pos.y == 7)
    
    def promote_pawn(self, row, col, piece_name):
        color = self.squares[row][col].color
        if piece_name == 'queen': 
            self.squares[row][col] = Queen(color)
        elif piece_name == 'rook': 
            self.squares[row][col] = Rook(color)
        elif piece_name == 'bishop': 
            self.squares[row][col] = Bishop(color)
        elif piece_name == 'knight': 
            self.squares[row][col] = Knight(color)
        self._board.push_san(self.last_move.san()+piece_name[0])

    def clone(self):
        new = self.__class__.__new__(self.__class__)

        new.squares = [
            [copy.deepcopy(piece) for piece in row]
            for row in self.squares
        ]

        new.last_move = copy.deepcopy(self.last_move)

        new._board = self._board.copy()

        new.board_stockfish = None

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

# --- Game Class (Main Controller) ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.clock = pygame.time.Clock()
        try:
            self.piece_font = pygame.font.Font(FONT_NAME, int(SQSIZE * 0.8))
        except FileNotFoundError:
            print(f"Error: Font '{FONT_NAME}' not found. Using default font.")
            self.piece_font = pygame.font.Font(None, int(SQSIZE * 0.8))

        self.gamestate = GameState.MENU
        self.board = None
        self.mouse_position = (0, 0)
        self.dragger = Dragger()
        self.turn = 'white'
        self.promotion_pos = None
        self.game_over_message = ""
        self.random_mode = False
        self.menu_font_color = FONT_COLOR
        self.menu_title_color = WHITE_SQUARE
        self.menu_background_color = MENU_BG_COLOR
        self.menu_font_animated_color = LIGHT_RED  # Highlight color for menu buttons

    def reset(self):
        self.board = Board()
        self.dragger = Dragger()
        self.turn = 'white'
        self.promotion_pos = None
        self.game_over_message = ""
        self.calc_all_valid_moves(self.turn)

    def mainloop(self):
        while True:
            if self.gamestate == GameState.MENU:
                self.show_menu()
                self.handle_menu_animations()
                self.handle_menu_events()
            elif self.gamestate == GameState.PLAYING:
                self.show_bg()
                self.show_last_move()
                self.show_moves()
                self.show_pieces()
                if self.dragger.dragging:
                    self.dragger.update_blit(self.screen, self.piece_font)
                self.handle_playing_events()
                if self.random_mode and self.turn == 'black':
                    self.random_move()
            elif self.gamestate == GameState.PROMOTING:
                self.show_bg()
                self.show_pieces()
                self.show_promotion_menu()
                self.handle_promotion_events()
            elif self.gamestate == GameState.GAME_OVER:
                self.show_bg()
                self.show_pieces()
                self.show_game_over()
                self.handle_game_over_events()
            pygame.display.update()
            self.clock.tick(60)

    # --- Drawing Methods ---
    def show_bg(self):
        for row in range(ROWS):
            for col in range(COLS):
                color = WHITE_SQUARE if (row + col) % 2 == 0 else BROWN
                pygame.draw.rect(self.screen, color, (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE))

    def show_pieces(self):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col]
                if piece != 0 and piece != self.dragger.piece:
                    text_surface = self.piece_font.render(piece.char, True, piece.font_color)
                    text_rect = text_surface.get_rect(center=(col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2))
                    self.screen.blit(text_surface, text_rect)

    def show_moves(self):
        if self.dragger.dragging:
            for move in self.dragger.piece.moves:
                s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                s.fill(LEGAL_MOVE_COLOR)
                self.screen.blit(s, (move.final.x * SQSIZE, move.final.y * SQSIZE))

    def show_last_move(self):
        if self.board.last_move:
            for pos in [self.board.last_move.initial, self.board.last_move.final]:
                color = (200, 200, 0, 100)
                s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, (pos.x * SQSIZE, pos.y * SQSIZE))
    
    # --- Event Handling ---
    def handle_playing_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.dragger.update_mouse(event.pos)
                clicked_row, clicked_col = self.dragger.mouseY // SQSIZE, self.dragger.mouseX // SQSIZE
                piece = 0 
                if 0<=clicked_row<8 and 0<=clicked_col<8:
                    piece = self.board.squares[clicked_row][clicked_col]
                if piece != 0 and piece.color == self.turn:
                    self.dragger.save_initial(event.pos)
                    self.dragger.drag_piece(piece)
            if event.type == pygame.MOUSEMOTION and self.dragger.dragging:
                self.dragger.update_mouse(event.pos)
            if event.type == pygame.MOUSEBUTTONUP and self.dragger.dragging:
                released_row, released_col = self.dragger.mouseY // SQSIZE, self.dragger.mouseX // SQSIZE
                initial = pygame.math.Vector2(self.dragger.initial_col, self.dragger.initial_row)
                final = pygame.math.Vector2(released_col, released_row)
                move = Move(initial, final)
                if move in self.dragger.piece.moves: 
                    self.make_move(self.dragger.piece, move)
                self.dragger.undrag_piece()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
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
        moves=self._get_raw_moves(piece, row, col, board)
        if isinstance(piece, King) and not piece.moved:
            if isinstance(board.squares[row][0], Rook) and not board.squares[row][0].moved and all(board.squares[row][c] == 0 for c in [1, 2, 3]) and not self.is_in_check(piece.color, board) and not self.is_in_check_at(piece.color, row, col-1, board) and not self.is_in_check_at(piece.color, row, col-2, board):
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(col - 2, row)))
            if isinstance(board.squares[row][7], Rook) and not board.squares[row][7].moved and all(board.squares[row][c] == 0 for c in [5, 6]) and not self.is_in_check(piece.color, board) and not self.is_in_check_at(piece.color, row, col+1, board) and not self.is_in_check_at(piece.color, row, col+2, board):
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(col + 2, row)))
        return moves

    # This method is without castling logic
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
            r, c = row + piece.dir, col
            if 0 <= r < ROWS and board.squares[r][c] == 0:
                moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
                if not piece.moved and 0 <= r + piece.dir < ROWS and board.squares[r + piece.dir][c] == 0:
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r + piece.dir)))
            for dc in [-1, 1]:
                r, c = row + piece.dir, col + dc
                if 0 <= r < ROWS and 0 <= c < COLS and board.squares[r][c] != 0 and board.squares[r][c].color != piece.color:
                    moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(c, r)))
            if board.last_move:
                lm_final_row, lm_final_col = int(board.last_move.final.y), int(board.last_move.final.x)
                lm_initial_row = int(board.last_move.initial.y)
                if lm_final_row == row and isinstance(board.squares[row][lm_final_col], Pawn) and abs(lm_final_row - lm_initial_row) == 2:
                    if lm_final_col == col - 1 or lm_final_col == col + 1:
                        moves.append(Move(pygame.math.Vector2(col, row), pygame.math.Vector2(lm_final_col, row + piece.dir)))

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
    
    def random_move(self):
        if self.turn == 'black' and not self.game_over_message:
            all_moves = [(p, m) for r in self.board.squares for p in r if p != 0 and p.color == 'black' for m in p.moves]
            if all_moves:
                self.make_move(*random.choice(all_moves))
    
    # --- UI and State Handlers ---
    def show_menu(self):
        self.screen.fill(MENU_BG_COLOR)
        title = pygame.font.Font(None, 74).render('Python Chess', True, self.menu_title_color)
        self.screen.blit(title, (WIDTH/2 - title.get_width()/2, 150))
       
        
    def handle_menu_animations(self):
        self.mouse_position = pygame.mouse.get_pos()
        self.pvp_rect = self.menu_text('1 vs 1 (Local)', (WIDTH//2, 350), 50)
        self.pve_rect = self.menu_text('1 vs Random', (WIDTH//2, 450), 50)
      
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
                    self.random_mode, self.gamestate = False, GameState.PLAYING
                    self.reset()
                elif self.pve_rect.collidepoint(event.pos): 
                    self.random_mode, self.gamestate = True, GameState.PLAYING
                    self.reset()

    def show_promotion_menu(self):
        row, col = self.promotion_pos
        y_start = row * SQSIZE if self.turn == 'white' else (row - 3) * SQSIZE
        rect = pygame.Rect(col * SQSIZE, y_start, SQSIZE, SQSIZE * 4)
        pygame.draw.rect(self.screen, MENU_BG_COLOR, rect, border_radius=10)
        self.promotion_options = {}
        for i, name in enumerate(['queen', 'rook', 'bishop', 'knight']):
            promo_rect = pygame.Rect(rect.x, rect.y + i * SQSIZE, SQSIZE, SQSIZE)
            self.promotion_options[name] = promo_rect
            char = UNICODE_PIECES[f'{self.turn[0]}_{name}']
            text_surf = self.piece_font.render(char, True, PIECE_COLORS[self.turn])
            self.screen.blit(text_surf, text_surf.get_rect(center=promo_rect.center))

    def handle_promotion_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(), sys.exit()
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