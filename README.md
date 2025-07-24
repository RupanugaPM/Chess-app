# Python Pygame Chess ♟️

A complete, feature-rich chess game built from the ground up using Python and the Pygame library. This project provides a clean user interface, full implementation of chess rules, and a playable AI opponent through a simple native engine or the powerful Stockfish engine.

<!-- 
IMPORTANT: Take a screenshot of your game and save it in your project folder. 
Then, replace the link below with the path to your image! 
-->
 
*(Example screenshot)*

---

## ✨ Features

*   **Game Modes:**
    *   **Player vs. Player:** Play locally against a friend.
    *   **Player vs. AI:** Challenge a computer opponent.
*   **Complete Chess Logic:**
    *   **Full Move Sets:** All pieces move according to official FIDE rules.
    *   **Check, Checkmate, and Stalemate:** The game correctly detects all end-of-game scenarios.
    *   **Special Moves:** Castling (both kingside and queenside), En Passant, and Pawn Promotion are fully implemented.
*   **User Interface:**
    *   Clean, intuitive main menu.
    *   Smooth drag-and-drop piece movement.
    *   Visual highlighting of the selected piece and all its legal moves.
    *   Clear game-over screen displaying the winner or a draw.
*   **Graphics:**
    *   Elegant, font-based rendering for chess pieces (no image assets required!).
    *   Classic and easy-to-read board colors.
*   **Optional Stockfish Integration:**
    *   Plug in the world's most powerful chess engine to play against a truly formidable AI.

---

## 🔧 Installation & Setup

Follow these steps to get the game running on your local machine.

### Prerequisites

*   Python 3.8+
*   Pygame
*   Stockfish (optional, for advanced AI)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### Step 2: Install Required Libraries

It's recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install libraries from requirements.txt
pip install -r requirements.txt
```

### Step 3: Get the Chess Font

This project uses a font file (`.ttf`) that contains the chess piece characters.

1.  Download a font with chess symbols. The one used during development was [Quivira](http://www.quivis.de/quivira.html).
2.  Place the `Quivira.ttf` file (or your chosen font file) in the **root directory** of the project, next to `main.py`.
3.  If you use a different font, make sure to update the `FONT_NAME` constant in the Python script.

### Step 4: Setup Stockfish (Optional)

To play against the Stockfish AI, you need to install the engine and make it accessible to the program.

1.  **Download Stockfish:** Get the latest version from the [official Stockfish website](https://stockfishchess.org/download/). Download the version appropriate for your operating system (Windows, macOS, Linux).

2.  **Unzip the file:** Extract the downloaded archive. You will find an executable file inside (e.g., `stockfish.exe` on Windows).

3.  **Add to PATH Environment Variable:** This is the most crucial step. The Python script needs to be able to find the Stockfish executable. You must add the folder containing `stockfish.exe` to your system's PATH.

    *   **Windows:**
        1.  Search for "Edit the system environment variables" in the Start Menu and open it.
        2.  Click the `Environment Variables...` button.
        3.  Under "System variables", find the `Path` variable, select it, and click `Edit...`.
        4.  Click `New` and paste the full path to the folder where you unzipped Stockfish (e.g., `C:\Users\YourUser\Downloads\stockfish_15_win_x64_avx2`).
        5.  Click OK on all windows to save. **You may need to restart your terminal or computer for the change to take effect.**

    *   **macOS/Linux:**
        1.  Move the Stockfish executable to a common location like `/usr/local/bin/`.
        2.  Alternatively, open your shell profile file (e.g., `~/.bash_profile`, `~/.zshrc`) in a text editor.
        3.  Add the following line at the end, replacing the path with the actual path to your Stockfish folder:
            ```bash
            export PATH="$PATH:/path/to/your/stockfish_folder"
            ```
        4.  Save the file and restart your terminal or run `source ~/.bash_profile` (or your respective profile file).

---

## ▶️ How to Play

Once everything is installed, run the main script from the project's root directory:

```bash
python main.py
```

1.  The main menu will appear.
2.  Choose your desired game mode: `1 vs 1 (Local)` or `1 vs AI`.
3.  **Controls:**
    *   Click and hold a piece to pick it up.
    *   All legal moves for that piece will be highlighted.
    *   Drag the piece to a valid square and release the mouse button to make a move.
4.  The game will automatically announce checkmate or stalemate.
5.  After a game ends, click the screen to return to the main menu.

---

## 🚀 Future Improvements

This project is a solid foundation, and here are some ideas for future enhancements:

*   [ ] **Network Play:** Implement online multiplayer using sockets.
*   [ ] **Move History:** Display a log of all moves made in the game (PGN format).
*   [ ] **Custom Themes:** Allow players to change board and piece colors.
*   [ ] **Timed Games:** Add chess clocks for blitz and rapid games.
*   [ ] **More AI Levels:** Implement a native AI with varying difficulty (e.g., using the Minimax algorithm).

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
