import numpy as np

def board_initialize():
    #Create initial board as an 8x8 array of None
    piece_mat = [[None] * 8 for i in range(8)]
    
    #Define board as "usable or non-usable squares" and initialize starting positions
    for i in range(8):
        for j in range(8):
            if ((i % 2 != 0) & (j % 2 != 0)) | ((i % 2 == 0) & (j % 2 == 0)):
                if i in range(3):
                    piece_mat[i][j] = 1
                elif i in range(3, 5):
                    piece_mat[i][j] = 0
                elif i in range(5, 8):
                    piece_mat[i][j] = -1

    return piece_mat

def dict_depth(d):
    #Check depth of dictionary
    if isinstance(d, dict):
        return 1 + (max(map(dict_depth, d.values())) if d else 0)
    return 0

def flatten(d, dlist=None):
    #Flatten nested dictionary into a dict of lists
    if dlist is None:
        dlist = []
    for k, v in sorted(d.items()):
        dlist.append(k)
        if isinstance(v, dict):
            flatten(v, dlist)
        elif len(v) > 0:
            dlist.append(v)
    return dlist

def on_board(x, y):
    #Check if square is a valid part of the board
    if (0 <= x <= 7) & (0 <= y <= 7):
        return True
        
def valid_move(player_id, x, y, x_delta, y_delta, hop):
    #Check if anticipated square is valid and if it is occupied whether there is a valid jump
    if on_board(x + x_delta, y + y_delta):
        sq_occup = np.sign(piece_mat[x + x_delta][y + y_delta])
        #If anticipated square is empty, then valid move
        if (not hop) & (sq_occup == 0):
            return tuple([x + x_delta, y + y_delta])
        #If the square is occupied by an opposing piece, check for hop possibilities
        elif sq_occup != player_id:
            if on_board(x + 2*x_delta, y + 2*y_delta):
                sq_occup = np.sign(piece_mat[x + 2*x_delta][y + 2*y_delta])
                #If anticipated square is empty, then valid move
                if sq_occup == 0:
                    tmp_dict = {}
                    tmp_dict.setdefault(tuple([x + x_delta, y + y_delta]),{}).setdefault(tuple([x + 2*x_delta, y + 2*y_delta]),[])
                    return tmp_dict
        

def sq_action(x, y, player_id, king_id, rev=None, hop=False):
    #Predefine dictionary with current space as the base key
    move_dict = {}
    move_dict.setdefault(tuple([x, y]),[])
    mv_ct = 0
    
    #If king check both forward and reverse squares for move possibilities
    if np.abs(king_id) > 1:
        for i in [-1, 1]:
            for j in [-1, 1]:
                #If this is following a hop, skip the inverse of the hop move to avoid infinite loop
                if [i, j] != rev:
                    #Add move_sequence (including intermediate hop space) if valid
                    tmp_move = valid_move(player_id, x, y, i*player_id, j*player_id, hop)
                    (move_dict[tuple([x, y])].append(tmp_move) if tmp_move is not None else None)
    else:
        for j in [-1, 1]:
            #Add move_sequence (including intermediate hop space) if valid
            tmp_move = valid_move(player_id, x, y, player_id, j*player_id, hop)
            (move_dict[tuple([x, y])].append(tmp_move) if tmp_move is not None else None)
    
    #Check for hop moves and search for possible secondary hops
    for i, item in enumerate(move_dict[tuple([x, y])]):
        #Looks to see if there is sufficient depth to indicate a hop
        if dict_depth(item) > 1:
            mv_ct = 1
            #Grab the skipped over piece coordinates (k) and landing coordinates (l)
            for k, v in item.items():
                for l in v.keys():
                    #If player has reached the end of the board on a hop terminate the current move
                    if not (((l[0] == 7) & (player_id == 1)) | ((l[0] == 0) & (player_id == -1))):
                        #Search recursively for chained hop moves
                        move_dict[tuple([x, y])][i][k], tmp_ct = sq_action(l[0], l[1], player_id, king_id, rev=[-int((l[0] - x) / 2), -int((l[1] - y) / 2)], hop=True)
    
    #Remove non-skip moves if a skip is present (forced skip)
    move_dict[tuple([x, y])] = [i for i in move_dict[tuple([x, y])] if dict_depth(i) >= mv_ct]
    return move_dict, mv_ct

def turn(pos):
    #Decompose space into co-ordinates
    x = pos[0]
    y = pos[1]
    
    #For a given square see what the available actions are on a turn
    player_id = np.sign(piece_mat[x][y])
    if player_id != 0:   
        move_dict, ctr = sq_action(x, y, player_id, piece_mat[x][y])
        return move_dict, ctr

def player_moves(piece_mat, player_id):
    #Get current positions and possible moves for a player
    player_dict = {}
    #Predefine whether a move includes a hop or not
    move_ctr = {}
    move_ctr.setdefault(0,[])
    move_ctr.setdefault(1,[])
    
    #Find all moves from positions
    for i in range(0, np.shape(piece_mat)[0]):
        for j in range(0, np.shape(piece_mat)[1]):
            if piece_mat[i][j]:
                if np.sign(piece_mat[i][j]) == player_id:
                    mv, ctr = turn(tuple([i,j]))
                    player_dict.update(mv)
                    move_ctr[ctr].append(tuple([i,j]))
                    
    #Store all positions
    pos_list = list(player_dict.keys())
    
    #If hop move then only keep possible hops and clean up dict to format (node): [[move1], [move2]]
    if len(move_ctr[1]) > 0:
        player_dict = {k: v for k, v in player_dict.items() if k in move_ctr[1]}
        ptmp = {}
        for k in player_dict.keys():
            ptmp.setdefault(k,[])
            for v in player_dict[k]:
                ptmp[k].append(flatten(v))
        player_dict = ptmp
    #Otherwise remove stationary pieces
    else:
        player_dict = {k: v for k, v in player_dict.items() if len(v) > 0}
    
    return player_dict, pos_list

def move_explorer(piece_mat, player_move, player_pos, player_id):
    for k in player_move[player_id].keys():
        assert(k in player_pos[player_id])
        assert(np.sign(piece_mat[k[0]][k[1]]) == player_id)
        
        for i in player_move[player_id][k]:
            update_board(piece_mat, player_pos, player_id, k, i)
            
def update_board(piece_mat, player_pos, player_id, start, move_list):
    new = move_list[-1]
    tmp = move_list[:-1]

    #Update ending position of current player
    player_pos[player_id].remove(start)
    player_pos[player_id].append(new)
    #King pieces that have crossed the board
    if (((new[0] == 7) & (player_id == 1)) | ((new[0] == 0) & (player_id == -1))):
        piece_mat[new[0]][new[1]] = 2*player_id
    else:
        piece_mat[new[0]][new[1]] = piece_mat[start[0]][start[1]]
    piece_mat[start[0]][start[1]] = 0
            
    #Remove hopped over opposing pieces            
    player_pos[-player_id] = list(set(player_pos[-player_id]) - set(tmp))
    for t in tmp:
        piece_mat[t[0]][t[1]] = 0

    return piece_mat, player_pos

def score(piece_mat, player_pos, player_score):
    #Score function of board state currently given as sum of pieces (reg=1, king=2)
    for k in player_score.keys():
        player_score[k] = 0
        for i in player_pos[k]:
            player_score[k] += abs(piece_mat[i[0]][i[1]])

    return player_score
    
#### Main Script ####
 
if __name__ == '__main__':    

    piece_mat = board_initialize()
    
    player_score = {}
    player_score.setdefault(1,[])
    player_score.setdefault(-1,[])
    
    player_pos = {}
    player_pos.setdefault(1,[])
    player_pos.setdefault(-1,[])

    player_move = {}
    player_move.setdefault(1,[])
    player_move.setdefault(-1,[])

    for i in [-1, 1]:
        player_id = i
        player_move[player_id], player_pos[player_id] = player_moves(piece_mat, player_id)
