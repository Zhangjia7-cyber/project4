import pygame as pg
import sys

WIDTH, HEIGHT = 15, 15
BLACK = 'X'
WHITE = 'O'
EMPTY = ' '

value_model_X = {
    '5': {
        '5': ('XXXXX', 10000)
    },
    '4': {
        '4p': (' XXXX ', 1000),
        '4e': (' XXXX', 500),
        '4s': ('XXXX ', 500),
        '4b': ('OXXXX ', 500),
        '4f': (' XXXXO', 500)
    },
    '3': {
        '3p': ('  XXX  ', 200),
        '3e': ('  XXX', 100),
        '3s': ('XXX  ', 100),
        '3b': ('OXXX  ', 100),
        '3f': ('  XXXO', 100),
        '3o': (' XX X ', 150),
        '3oe': (' XX X', 80),
        '3os': ('XX X ', 80),
        '3o2': (' X XX ', 150)
    },
    '2': {
        '2p': ('   XX   ', 50),
        '2e': ('   XX', 20),
        '2s': ('XX   ', 20),
        '2o': ('  X X  ', 40),
        '2oe': ('  X X', 15),
        '2os': ('X X  ', 15)
    },
    '1': {
        '1p': ('    X    ', 10),
        '1e': ('    X', 5),
        '1s': ('X    ', 5)
    }
}

value_model_O = {}
for key1, val1 in value_model_X.items():
    value_model_O[key1] = {}
    for key2, (pattern, score) in val1.items():
        new_pattern = pattern.replace('X', 'temp').replace('O', 'X').replace('temp', 'O')
        value_model_O[key1][key2] = (new_pattern, score)

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
CELL_SIZE = 40
BOARD_OFFSET = 30

BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
BOARD_COLOR = (205, 133, 63)
LINE_COLOR = (0, 0, 0)

# 弹窗配置
POPUP_WIDTH = 300
POPUP_HEIGHT = 200
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
BUTTON_GAP = 30


def draw_board(screen):
    screen.fill(BOARD_COLOR)
    for i in range(15):
        pg.draw.line(screen, LINE_COLOR,
                     (BOARD_OFFSET, BOARD_OFFSET + i * CELL_SIZE),
                     (BOARD_OFFSET + 14 * CELL_SIZE, BOARD_OFFSET + i * CELL_SIZE), 1)
        pg.draw.line(screen, LINE_COLOR,
                     (BOARD_OFFSET + i * CELL_SIZE, BOARD_OFFSET),
                     (BOARD_OFFSET + i * CELL_SIZE, BOARD_OFFSET + 14 * CELL_SIZE), 1)

    stars = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
    for x, y in stars:
        pg.draw.circle(screen, LINE_COLOR,
                       (BOARD_OFFSET + x * CELL_SIZE, BOARD_OFFSET + y * CELL_SIZE), 4)


def draw_pieces(screen, board):
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if board[y][x] != EMPTY:
                center_x = BOARD_OFFSET + x * CELL_SIZE
                center_y = BOARD_OFFSET + y * CELL_SIZE
                color = BLACK_COLOR if board[y][x] == BLACK else WHITE_COLOR
                pg.draw.circle(screen, color, (center_x, center_y), 18)
                if board[y][x] == WHITE:
                    pg.draw.circle(screen, BLACK_COLOR, (center_x, center_y), 2)
                else:
                    pg.draw.circle(screen, WHITE_COLOR, (center_x, center_y), 2)


def check_win(board_inner):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for x in range(WIDTH):
        for y in range(HEIGHT):
            if board_inner[y][x] != EMPTY:
                for dx, dy in directions:
                    count = 1
                    nx, ny = x + dx, y + dy
                    while 0 <= nx < WIDTH and 0 <= ny < HEIGHT and board_inner[ny][nx] == board_inner[y][x]:
                        count += 1
                        nx += dx
                        ny += dy
                    if count >= 5:
                        return board_inner[y][x]
    return None


def evaluate_line(line, model, chr):
    score = 0
    line_str = ''.join(line)
    for key1, val1 in model.items():
        for key2, (pattern, val_score) in val1.items():
            if pattern in line_str:
                score += val_score
                line_str = line_str.replace(pattern, ' ' * len(pattern), 1)
    return score


def evaluate_board(board_inner, model, chr):
    score = 0
    for row in board_inner:
        score += evaluate_line(row, model, chr)
    for col in range(WIDTH):
        column = [board_inner[row][col] for row in range(HEIGHT)]
        score += evaluate_line(column, model, chr)
    for diag in range(-14, 15):
        diagonal = []
        for x in range(WIDTH):
            y = x + diag
            if 0 <= y < HEIGHT:
                diagonal.append(board_inner[y][x])
        score += evaluate_line(diagonal, model, chr)
    for diag in range(28):
        diagonal = []
        for x in range(WIDTH):
            y = diag - x
            if 0 <= y < HEIGHT:
                diagonal.append(board_inner[y][x])
        score += evaluate_line(diagonal, model, chr)
    return score


def get_ai_move(board_inner):
    best_score = -float('inf')
    best_move = (7, 7)

    for x in range(WIDTH):
        for y in range(HEIGHT):
            if board_inner[y][x] == EMPTY:
                board_inner[y][x] = BLACK
                score = evaluate_board(board_inner, value_model_X, BLACK)
                score -= evaluate_board(board_inner, value_model_O, WHITE)
                board_inner[y][x] = EMPTY

                if score > best_score:
                    best_score = score
                    best_move = (x, y)

    return best_move


def draw_popup(screen, is_victory):
    # 计算弹窗位置（居中）
    popup_x = (SCREEN_WIDTH - POPUP_WIDTH) // 2
    popup_y = (SCREEN_HEIGHT - POPUP_HEIGHT) // 2

    # 绘制半透明遮罩
    overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))

    # 绘制弹窗背景
    pg.draw.rect(screen, (255, 255, 255), (popup_x, popup_y, POPUP_WIDTH, POPUP_HEIGHT))
    pg.draw.rect(screen, BLACK_COLOR, (popup_x, popup_y, POPUP_WIDTH, POPUP_HEIGHT), 3)

    # 绘制标题文字
    font_title = pg.font.Font(None, 52)
    if is_victory:
        title_text = font_title.render("Victory!", True, (0, 180, 0))  # 绿色
    else:
        title_text = font_title.render("Failure!", True, (255, 0, 0))  # 红色

    title_rect = title_text.get_rect(center=(popup_x + POPUP_WIDTH // 2, popup_y + 50))
    screen.blit(title_text, title_rect)

    # 计算按钮位置
    total_buttons_width = BUTTON_WIDTH * 2 + BUTTON_GAP
    button_start_x = (SCREEN_WIDTH - total_buttons_width) // 2
    button_y = popup_y + 110

    # 绘制按钮
    # 退出按钮
    quit_button_rect = pg.Rect(button_start_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    pg.draw.rect(screen, (180, 180, 180), quit_button_rect)
    pg.draw.rect(screen, BLACK_COLOR, quit_button_rect, 2)
    font_button = pg.font.Font(None, 36)
    quit_text = font_button.render("Quit", True, BLACK_COLOR)
    quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
    screen.blit(quit_text, quit_text_rect)

    # 再来按钮
    again_button_rect = pg.Rect(button_start_x + BUTTON_WIDTH + BUTTON_GAP, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    pg.draw.rect(screen, (100, 200, 100), again_button_rect)
    pg.draw.rect(screen, BLACK_COLOR, again_button_rect, 2)
    again_text = font_button.render("Again", True, BLACK_COLOR)
    again_text_rect = again_text.get_rect(center=again_button_rect.center)
    screen.blit(again_text, again_text_rect)

    return quit_button_rect, again_button_rect


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("五子棋人机对战")

    board_inner = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
    player_turn = True
    game_over = False
    winner = None
    popup_buttons = None

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                if game_over and popup_buttons:
                    quit_btn, again_btn = popup_buttons

                    # 检查是否点击了退出按钮
                    if quit_btn.collidepoint(mouse_x, mouse_y):
                        pg.quit()
                        sys.exit()

                    # 检查是否点击了再来按钮
                    if again_btn.collidepoint(mouse_x, mouse_y):
                        board_inner = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
                        player_turn = True
                        game_over = False
                        winner = None
                        popup_buttons = None
                        pg.time.wait(200)
                        break

                # 玩家回合点击棋盘
                if not game_over and player_turn:
                    board_x = (mouse_x - BOARD_OFFSET + CELL_SIZE // 2) // CELL_SIZE
                    board_y = (mouse_y - BOARD_OFFSET + CELL_SIZE // 2) // CELL_SIZE

                    if 0 <= board_x < WIDTH and 0 <= board_y < HEIGHT and board_inner[board_y][board_x] == EMPTY:
                        board_inner[board_y][board_x] = WHITE
                        player_turn = False

                        winner = check_win(board_inner)
                        if winner:
                            game_over = True

        if not game_over and not player_turn:
            ai_x, ai_y = get_ai_move(board_inner)
            board_inner[ai_y][ai_x] = BLACK
            player_turn = True

            winner = check_win(board_inner)
            if winner:
                game_over = True

        draw_board(screen)
        draw_pieces(screen, board_inner)

        if game_over:
            # 判断是胜利还是失败（玩家执白棋，AI执黑棋）
            is_victory = (winner == WHITE)
            popup_buttons = draw_popup(screen, is_victory)

        pg.display.update()


if __name__ == '__main__':
    main()
