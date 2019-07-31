import sys
import random
import time
import copy
import traceback


class Team55:

    def __init__(self):
        """initialise Agent variables"""
        self.pos_weight = ((4,6,4),(6,3,6),(4,6,4)) # weight of winning position[i][j]
        self.available_moves = []
        self.randHashes = [[[[long(0) for i in range(9)] for j in range(9)] for k in range(2) ] for m in range(2)]
        self.make_randHashes()
        self.cnt = 0
        self.bm = 1
        self.end = 23
        self.inf = 10**20
        self.flagger = 0
        self.winflg = 0
        self.start_time = time.time()
        self.boardHeuriStore = {} # store calculated board heuristics
        self.blockHeuriStore = {}
        self.boardHash = long(0)
        self.blockHash = [ [[long(0) for i in range(3)] for j in range(3)] for k in range(2) ]   
        self.wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)] 
      


    def big_board_heuristic(self, board, board_no, player, multiplier):
        total = 0
        for seq in self.wins:
            points = 0
            for num in seq:
                cell = board.small_boards_status[board_no][num/3][num%3]
                if cell == player:
                    points += 1
                elif cell == self.negate_flag(player):
                    points = 0
                    break

            if points != 0:
                total += (10**(points - 1))*100*multiplier

        for j in range(3):
            for k in range(3):
                cell = board.small_boards_status[board_no][j][k]
                if cell == player:
                    total += self.pos_weight[j][k] * 150 

        return total

      

    def heuristic(self, board, player):

        ter_state = board.find_terminal_state()
        if ter_state[0] == player:
            return 10**20
        if (self.boardHash, player) in self.boardHeuriStore:
            return self.boardHeuriStore[(self.boardHash, player)]


        total = 0
        for j in range(2):
            total += self.single_board_cost(board, j, player)

        self.boardHeuriStore[(self.boardHash, player)] = total

        return total
    
    def single_board_cost(self, board, board_no, player):

        total = 0
        cnt = 9
        for j in range(3):
            for k in range(3):
                if board.small_boards_status[board_no][j][k] == '-':
                    cnt -= 1

        for j in range(3):
            for k in range(3):
                total += self.small_board_heuristic(board, (board_no, j, k), player)

        total += self.big_board_heuristic(board, board_no, player, (cnt ** 2) * 0.3  + 1)

        return total

    def small_board_heuristic(self, board, block, player):
        if (self.blockHash[block[0]][block[1]][block[2]], player) in self.blockHeuriStore:
            return self.blockHeuriStore[(self.blockHash[block[0]][block[1]][block[2]], player)]

        total = 0
        for seq in self.wins:
            points = 0
            for num in seq:
                cell = board.big_boards_status[block[0]][block[1]*3 + num/3][block[2]*3 + num%3]
                if cell == player:
                    points += 1
                elif cell == self.negate_flag(player):
                    points = 0
                    break
            if points != 0:
                total += 10**(points - 1)
        
        self.blockHeuriStore[(self.blockHash[block[0]][block[1]][block[2]], player)] = total       
        return total



    def addMovetoHash(self, cell, player):
		# player -> 0: opponent, 1: us
        w = cell[0]
        x = cell[1]
        y = cell[2]
        self.boardHash ^= self.randHashes[player][w][x][y]
        self.blockHash[w][x/3][y/3] ^= self.randHashes[player][w][x][y]

    def negate_flag(self, flag):
        if flag == 'x':
            return 'o'
        else:
            return 'x'

    def move(self, board, old_move, flag):
        """give best possible move"""

        if old_move == (-1, -1, -1):
            self.addMovetoHash((0,1,1),1)
            return (0,1,1)
        else:
            self.addMovetoHash(old_move,0)

        self.bm = flag
        self.start_time = time.time()

        self.available_moves = self.give_availabe_moves(board, old_move)
        alpha = -self.inf
        beta = self.inf

        bd = copy.deepcopy(board)
        
        depth = 2
        self.flagger = 0
        best_move_final = (-self.inf,self.available_moves[random.randint(0,len(self.available_moves)-1)])
        
        for depth in range(1,200):
            best_move = (-self.inf,self.available_moves[random.randint(0,len(self.available_moves)-1)])
            val = best_move
            self.flagger = 0
            if time.time() - self.start_time > self.end:
                self.flagger = 1
                break
            for s in self.available_moves:
                if time.time() - self.start_time > self.end:
                    self.flagger = 1
                    break
                
                self.addMovetoHash(s,1)

                bd.update(old_move, s, flag)
                if bd.small_boards_status[s[0]][s[1]/3][s[2]/3] == flag and self.winflg == 0:
                    val = self.max_turn(bd, s, depth - 1,alpha, beta, flag, 1)
                else:
                    val = self.min_turn(bd, s, depth - 1, alpha, beta,self.negate_flag(flag), 0)
                
                if val > best_move[0]:
                    best_move = (val, s)

                
                self.addMovetoHash(s,1)

                bd.big_boards_status[s[0]][s[1]][s[2]] = '-'   #reset the big board    
                bd.small_boards_status[s[0]][s[1]/3][s[2]/3] = '-' #reset small board
            if self.flagger == 0:
                best_move_final = best_move
                # print depth, best_move_final
        
        
        if bd.small_boards_status[best_move_final[1][0]][best_move_final[1][1]/3][best_move_final[1][2]/3] == flag:
            self.winflg = 1
        else:
            self.winflg = 0
        self.addMovetoHash(best_move_final[1],1)
        # print self.blockHash
        return best_move_final[1]

    def min_turn(self, board, old_move, depth, alpha, beta, flag, winflag):

        valid_moves = self.give_availabe_moves(board, old_move)
        if depth <= 0 or len(valid_moves) == 0:
            return self.heuristic(board, self.bm) - self.heuristic(board, self.negate_flag(self.bm))*1.5

            
        best_move = (self.inf, None)
        val = best_move
        bd = board
        bst = bd
        for mv in valid_moves:
            if time.time() - self.start_time > self.end:
                self.flagger = 1
                break

            self.addMovetoHash(mv,0)

            bd.update(old_move, mv, flag)
            if bd.small_boards_status[mv[0]][mv[1]/3][mv[2]/3] == flag and winflag == 0:
                val = self.min_turn(bd, mv, depth - 1,alpha, beta, flag, (winflag+1)%2)
            else:
                val = self.max_turn(bd, mv, depth - 1,alpha, beta, self.negate_flag(flag), 0)
     
            if val < best_move[0]:
                best_move = (val,mv)
            beta = min(beta,val)
            self.addMovetoHash(mv,0)
            bd.big_boards_status[mv[0]][mv[1]][mv[2]] = '-'  #reset the board    
            bd.small_boards_status[mv[0]][mv[1]/3][mv[2]/3] = '-' #reset small board
            if beta <= alpha:
                break
        return best_move[0]



    def max_turn(self, board, old_move, depth, alpha, beta, flag, winflag):

        valid_moves = self.give_availabe_moves(board, old_move)
        if depth <=  0 or len(valid_moves) == 0:
            return self.heuristic(board, self.bm) - self.heuristic(board, self.negate_flag(self.bm))*1.5

            # return self.heuristic(board, self.bm)

            
        best_move = (-self.inf, None)
        val = best_move
        bd = board  
        
        for mv in valid_moves:

            if time.time() - self.start_time > self.end:
                self.flagger = 1
                break
            
            self.addMovetoHash(mv,1)

            bd.update(old_move, mv, flag)
            if bd.small_boards_status[mv[0]][mv[1]/3][mv[2]/3] == flag and winflag == 0:
                val = self.max_turn(bd, mv, depth - 1,alpha, beta, flag, (winflag + 1)%2)
            else:
                val = self.min_turn(bd, mv, depth - 1, alpha, beta,self.negate_flag(flag), 0)
            alpha = max(val,alpha)
            if val > best_move[0]:
                best_move = (val,mv)


            self.addMovetoHash(mv,1)
            bd.big_boards_status[mv[0]][mv[1]][mv[2]] = '-'  #reset the board    
            bd.small_boards_status[mv[0]][mv[1]/3][mv[2]/3] = '-' #reset small board
            if beta <= alpha:
                break
        return best_move[0]
        
    
    def give_availabe_moves(self, board, old_move):
        """return available moves on modified board"""
        return board.find_valid_move_cells(old_move)

    def make_randHashes(self):
        """generating table to be used in xobrist hash"""
        for i in range(9):
            for j in range(9):
                for k in range(2):
                    for m in range(2):
                        self.randHashes[m][k][i][j] = long(random.randint(1,2**63))
