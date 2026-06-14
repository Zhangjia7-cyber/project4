import streamlit as st
import numpy as np
import random
import time

# 游戏配置
BOARD_SIZE = 15
WIN_CONDITION = 5
INITIAL_TIME = 60
MESSAGE_COOLDOWN = 15
AI_MESSAGE_INTERVAL = 10

# 快捷消息列表
QUICK_MESSAGES = [
    ("快点啊", "⏰"),
    ("你下的真好", "👍"),
    ("看我操作吧", "🎯"),
    ("承让承让", "🙏"),
    ("失误失误", "😅")
]

def init_board():
    return np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

@st.cache_data
def check_win(board, row, col, player):
    board_np = np.array(board) if isinstance(board, list) else board
    directions = [[1, 0], [0, 1], [1, 1], [1, -1]]
    for dx, dy in directions:
        count = 1
        for step in range(1, WIN_CONDITION):
            nx, ny = col + dx * step, row + dy * step
            if nx < 0 or ny < 0 or nx >= BOARD_SIZE or ny >= BOARD_SIZE:
                break
            if board_np[ny][nx] == player:
                count += 1
            else:
                break
        for step in range(1, WIN_CONDITION):
            nx, ny = col - dx * step, row - dy * step
            if nx < 0 or ny < 0 or nx >= BOARD_SIZE or ny >= BOARD_SIZE:
                break
            if board_np[ny][nx] == player:
                count += 1
            else:
                break
        if count >= WIN_CONDITION:
            return True
    return False

@st.cache_data
def check_draw(board):
    board_np = np.array(board) if isinstance(board, list) else board
    return np.all(board_np != 0)

def ai_move(board):
    empty = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:
                empty.append((i, j))
    
    if not empty:
        return None
    
    center = (BOARD_SIZE - 1) / 2
    best = empty[0]
    best_score = -float('inf')
    
    for pos in empty:
        score = -abs(pos[0] - center) - abs(pos[1] - center)
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = pos[1] + dx, pos[0] + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] != 0:
                    score += 3
        
        for dx, dy in [[1, 0], [0, 1], [1, 1], [1, -1]]:
            my_count = 1
            for step in range(1, WIN_CONDITION):
                nx, ny = pos[1] + dx * step, pos[0] + dy * step
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == 2:
                    my_count += 1
                else:
                    break
            score += my_count * 10
            
            opp_count = 1
            for step in range(1, WIN_CONDITION):
                nx, ny = pos[1] + dx * step, pos[0] + dy * step
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == 1:
                    opp_count += 1
                else:
                    break
            score += opp_count * 8
        
        if score > best_score:
            best_score = score
            best = pos
    
    return best

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def main():
    st.set_page_config(page_title="五子棋", layout="wide")
    
    # 初始化状态（只执行一次）
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.game_state = 'menu'
        st.session_state.game_mode = None
        st.session_state.board = init_board().tolist()
        st.session_state.current_player = 1
        st.session_state.game_over = False
        st.session_state.winner = None
        st.session_state.black_time = INITIAL_TIME
        st.session_state.white_time = INITIAL_TIME
        st.session_state.messages = []
        st.session_state.last_message_time = {1: 0, 2: 0}
        st.session_state.last_ai_message_time = 0
        st.session_state.history = []
        st.session_state.music_volume = 50
        st.session_state.music_on = True
        st.session_state.last_time_update = time.time()
        st.session_state.move_key = 0
    
    # 主菜单
    if st.session_state.game_state == 'menu':
        st.title('♟️ 五子棋')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button('🎮 开始游戏', use_container_width=True, key='menu_start'):
                st.session_state.game_state = 'mode_select'
        
        with col2:
            if st.button('🚪 退出游戏', use_container_width=True, key='menu_exit'):
                st.stop()
        
        st.sidebar.title('🔊 音效设置')
        st.session_state.music_volume = st.sidebar.slider('音量', 0, 100, st.session_state.music_volume)
        st.session_state.music_on = st.sidebar.checkbox('开启音乐', st.session_state.music_on)
        
        if st.session_state.music_on:
            st.sidebar.write('音乐已开启')
        
        if st.session_state.game_state == 'mode_select':
            st.rerun()
        return
    
    # 模式选择
    if st.session_state.game_state == 'mode_select':
        st.title('♟️ 选择游戏模式')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button('🤖 人机对战', use_container_width=True, key='mode_ai'):
                st.session_state.game_mode = 'ai'
                reset_game()
                st.session_state.game_state = 'game'
        
        with col2:
            if st.button('👥 双人对战', use_container_width=True, key='mode_vs'):
                st.session_state.game_mode = 'vs'
                reset_game()
                st.session_state.game_state = 'game'
        
        if st.button('🔙 返回主菜单', key='mode_back'):
            st.session_state.game_state = 'menu'
        
        if st.session_state.game_state == 'game':
            st.rerun()
        return
    
    # 游戏界面
    if st.session_state.game_state == 'game':
        board = np.array(st.session_state.board)
        current_player = st.session_state.current_player
        game_over = st.session_state.game_over
        winner = st.session_state.winner
        
        # 顶部状态栏
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown("**黑棋剩余时间**")
            black_time_str = format_time(st.session_state.black_time)
            if st.session_state.black_time <= 10 and st.session_state.black_time > 0:
                st.markdown(f"<span style='color:red; font-size:28px;'>{black_time_str}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{black_time_str}**")
        
        with col2:
            st.markdown("**当前回合**")
            if not game_over:
                st.markdown(f"**{'黑棋 ●' if current_player == 1 else '白棋 ○'}**")
            else:
                if winner == 'draw':
                    st.markdown("**🤝 平局**")
                else:
                    st.markdown(f"**{'黑棋 ● 获胜！' if winner == 1 else '白棋 ○ 获胜！'}**")
        
        with col3:
            st.markdown("**白棋剩余时间**")
            white_time_str = format_time(st.session_state.white_time)
            if st.session_state.white_time <= 10 and st.session_state.white_time > 0:
                st.markdown(f"<span style='color:red; font-size:28px;'>{white_time_str}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{white_time_str}**")
        
        # 时间更新（优化：只在需要时刷新）
        if not game_over:
            current_time = time.time()
            if current_time - st.session_state.last_time_update >= 1:
                if current_player == 1:
                    st.session_state.black_time -= 1
                    if st.session_state.black_time <= 0:
                        st.session_state.game_over = True
                        st.session_state.winner = 2
                else:
                    st.session_state.white_time -= 1
                    if st.session_state.white_time <= 0:
                        st.session_state.game_over = True
                        st.session_state.winner = 1
                st.session_state.last_time_update = current_time
                st.rerun()
        
        # 游戏结果显示
        if game_over:
            st.write('')
            if winner == 'draw':
                st.success('🤝 平局！')
            elif winner == 1:
                st.success('🎉 黑棋获胜！')
            else:
                st.success('🎉 白棋获胜！')
            
            col_play, col_menu = st.columns(2)
            with col_play:
                if st.button('🔄 再来一局', key='result_play'):
                    reset_game()
                    st.rerun()
            
            with col_menu:
                if st.button('🏠 返回主菜单', key='result_menu'):
                    st.session_state.game_state = 'menu'
                    st.rerun()
            return
        
        # 创建棋盘（使用单个按钮组减少渲染开销）
        st.write('---')
        board_placeholder = st.empty()
        
        with board_placeholder.container():
            for i in range(BOARD_SIZE):
                cols = st.columns(BOARD_SIZE)
                for j in range(BOARD_SIZE):
                    with cols[j]:
                        if board[i][j] == 0:
                            key = f'board-{i}-{j}-{st.session_state.move_key}'
                            if st.button(' ', key=key, 
                                       use_container_width=True,
                                       help=f'落子于 ({i+1}, {j+1})'):
                                make_move(i, j)
                                st.session_state.move_key += 1
                        elif board[i][j] == 1:
                            st.button('●', key=f'black-{i}-{j}', 
                                     disabled=True, use_container_width=True)
                        else:
                            st.button('○', key=f'white-{i}-{j}', 
                                     disabled=True, use_container_width=True)
        
        # 快捷消息
        st.write('---')
        st.markdown("**💬 快捷消息：**")
        
        msg_cols = st.columns(len(QUICK_MESSAGES))
        for idx, (msg, emoji) in enumerate(QUICK_MESSAGES):
            with msg_cols[idx]:
                can_send = time.time() - st.session_state.last_message_time[current_player] >= MESSAGE_COOLDOWN
                if st.button(f'{emoji} {msg}', key=f'msg-{idx}', 
                           use_container_width=True, disabled=not can_send):
                    send_message(msg)
        
        cooldown_left = MESSAGE_COOLDOWN - (time.time() - st.session_state.last_message_time[current_player])
        if cooldown_left > 0:
            st.write(f"⏳ 消息冷却：{int(cooldown_left)}秒")
        
        # 消息展示
        st.markdown("**📝 聊天记录：**")
        messages_container = st.container()
        with messages_container:
            for msg in st.session_state.messages[-10:]:
                sender = "黑棋" if msg['player'] == 1 else "白棋"
                if msg.get('is_ai'):
                    sender = "🤖 AI"
                st.write(f"【{sender}】{msg['emoji']} {msg['text']}")
        
        # 菜单按钮
        st.write('---')
        menu_cols = st.columns(5)
        with menu_cols[0]:
            if st.button('🏳️ 投降', key='menu_surrender'):
                st.session_state.game_over = True
                st.session_state.winner = 2 if current_player == 1 else 1
                st.rerun()
        
        with menu_cols[1]:
            can_undo = len(st.session_state.history) > 0 and st.session_state.game_mode == 'vs'
            if st.button('↩️ 悔棋', key='menu_undo', disabled=not can_undo):
                undo_move()
        
        with menu_cols[2]:
            if st.button('🗑️ 清空聊天', key='menu_clear_chat'):
                st.session_state.messages = []
        
        with menu_cols[3]:
            if st.button('🏠 返回菜单', key='menu_back'):
                st.session_state.game_state = 'menu'
                st.rerun()
        
        with menu_cols[4]:
            if st.button('🚪 退出游戏', key='menu_exit_game'):
                st.stop()
        
        # AI回合（使用st.spinner但不阻塞）
        if st.session_state.game_mode == 'ai' and current_player == 2 and not game_over:
            with st.spinner('AI思考中...'):
                time.sleep(0.3)  # 减少AI思考时间
                move = ai_move(board)
                if move:
                    row, col = move
                    make_move(row, col, is_ai=True)
                    
                    now = time.time()
                    if now - st.session_state.last_ai_message_time >= AI_MESSAGE_INTERVAL:
                        ai_msg = random.choice(QUICK_MESSAGES)
                        send_message(ai_msg[0], is_ai=True)
                        st.session_state.last_ai_message_time = now
                st.rerun()

def reset_game():
    st.session_state.board = init_board().tolist()
    st.session_state.current_player = 1
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.black_time = INITIAL_TIME
    st.session_state.white_time = INITIAL_TIME
    st.session_state.messages = []
    st.session_state.last_message_time = {1: 0, 2: 0}
    st.session_state.last_ai_message_time = 0
    st.session_state.history = []
    st.session_state.last_time_update = time.time()
    st.session_state.move_key = 0

def make_move(row, col, is_ai=False):
    board = np.array(st.session_state.board)
    current_player = st.session_state.current_player
    
    if board[row][col] != 0:
        return
    
    st.session_state.history.append({
        'board': st.session_state.board.copy(),
        'current_player': current_player,
        'black_time': st.session_state.black_time,
        'white_time': st.session_state.white_time
    })
    
    board[row][col] = current_player
    st.session_state.board = board.tolist()
    
    if check_win(board, row, col, current_player):
        st.session_state.game_over = True
        st.session_state.winner = current_player
    elif check_draw(board):
        st.session_state.game_over = True
        st.session_state.winner = 'draw'
    else:
        st.session_state.current_player = 2 if current_player == 1 else 1
        st.session_state.last_time_update = time.time()

def undo_move():
    if not st.session_state.history:
        return
    
    last_state = st.session_state.history.pop()
    st.session_state.board = last_state['board']
    st.session_state.current_player = last_state['current_player']
    st.session_state.black_time = last_state['black_time']
    st.session_state.white_time = last_state['white_time']
    st.session_state.last_time_update = time.time()

def send_message(text, is_ai=False):
    player = 2 if is_ai else st.session_state.current_player
    
    emoji = ""
    for msg, em in QUICK_MESSAGES:
        if msg == text:
            emoji = em
            break
    
    st.session_state.messages.append({
        'player': player,
        'text': text,
        'emoji': emoji,
        'is_ai': is_ai,
        'time': time.time()
    })
    
    if not is_ai:
        st.session_state.last_message_time[player] = time.time()

if __name__ == '__main__':
    main()