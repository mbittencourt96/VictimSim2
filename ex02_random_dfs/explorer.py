# EXPLORER AGENT
# @Author: Tacla, UTFPR
#
### It walks randomly in the environment looking for victims. When half of the
### exploration has gone, the explorer goes back to the base.

import sys
import os
import random
import math
from abc import ABC, abstractmethod
from vs.abstract_agent import AbstAgent
from vs.constants import VS
from astar_algorithm import AStarExplorer
from map import Map

class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
    
    def peek(self):
        if not self.is_empty():
            return self.items[-1]  # Acessa o último elemento da lista sem remove-lo

    def is_empty(self):
        return len(self.items) == 0

class Explorer(AbstAgent):
    instance_count = 0  #Class variable to keep track of the count of instances

    def __init__(self, env, config_file, resc):
        """ Construtor do agente random on-line
        @param env: a reference to the environment 
        @param config_file: the absolute path to the explorer's config file
        @param resc: a reference to the rescuer agent to invoke when exploration finishes
        """

        super().__init__(env, config_file)
        Explorer.instance_count += 1
        self.id = Explorer.instance_count  #Unique id for the explorer
        self.walk_stack = Stack()  # a stack to store the movements
        self.set_state(VS.ACTIVE)  # explorer is active since the begin
        self.resc = resc           # reference to the rescuer agent
        self.x = 0                 # current x position relative to the origin 0
        self.y = 0                 # current y position relative to the origin 0
        self.previous_x = 0        # previous x position relative to the origin 0
        self.previous_y = 0        # previous y position relative to the origin 0
        self.map = Map()           # create a map for representing the environment
        self.victims = {}          # a dictionary of found victims: (seq): ((x,y), [<vs>])
                                   # the key is the seq number of the victim,(x,y) the position, <vs> the list of vital signals
        self.action_order = {
            'N': 0,
            'NE': 1,
            'E': 2,
            'SE': 3,
            'S': 4,
            'SO': 5,
            'W': 6,
            'NO': 7,
        }
        self.backtracked = {}
        self.backtracked_loop = {}  # dicionario auxiliar para evitar o loop da oscilacao entre duas posicoes
        self.untried = {}          # dicionario de direcoes ainda nao exploradas por um posicao (x,y)
                                   # (x,y) , [0, 1, 2, 3, 4, 5, 6, 7]

        if self.id == 1:   #first agent's sequence of actions
            self.actions = ["N","S","E","W","NO","NE","SO","SE"]
        elif self.id == 2: #second agent's sequence of actions
            self.actions = ["N","E","W","S","SO","NE","NO","SE"]
        elif self.id == 3: #third agent's sequence of actions
            self.actions = ["SE","W","S","SO","E","N","NO","NE"]
        else:              #fourth agent's sequence of actions - ta meio tonto
            self.actions = ["E","W","S","N","SE","SO","NO","NE"]

        # put the current position - the base - in the map
        self.map.add((self.x, self.y), 1, VS.NO_VICTIM, self.check_walls_and_lim())

    def get_next_position(self):
        # Check the neighborhood walls and grid limits
        obstacles = self.check_walls_and_lim()
    
        # Loop until a CLEAR position is found
        while True:
            # Get a direction from the DFS algorithm
            direction = self.DFS_online()
        # Check if the corresponding position in walls_and_lim is CLEAR
            if obstacles[direction] == VS.CLEAR:
                return Explorer.AC_INCR[direction]
        
    def explore(self):
        # get an random increment for x and y       
        next_position = self.get_next_position()

        # Check if next_position is None
        if next_position is None:
            return  # Exit explore() if no available actions

        # verificar se ja nao visitou essa posicao em MAP ???

        dx, dy = next_position

        # Moves the body to another position
        rtime_bef = self.get_rtime()
        result = self.walk(dx, dy)
        rtime_aft = self.get_rtime()

        # Test the result of the walk action
        # Should never bump, but for safe functioning let's test
        if result == VS.BUMPED:
            # update the map with the wall
            print(self.x, self.y)  
            self.map.add((self.x + dx, self.y + dy), VS.OBST_WALL, VS.NO_VICTIM, self.check_walls_and_lim())
            #print(f"{self.NAME}: Wall or grid limit reached at ({self.x + dx}, {self.y + dy})")

        if result == VS.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            self.walk_stack.push((dx, dy))

            # update the agent's position relative to the origin
            self.x += dx
            self.y += dy

            # Check for victims
            seq = self.check_for_victim()
            if seq != VS.NO_VICTIM:
                vs = self.read_vital_signals()
                self.victims[vs[0]] = ((self.x, self.y), vs)
                print(f"{self.NAME} Victim found at ({self.x}, {self.y}), rtime: {self.get_rtime()}")
                #print(f"{self.NAME} Seq: {seq} Vital signals: {vs}")
            
            # Calculates the difficulty of the visited cell
            difficulty = (rtime_bef - rtime_aft)
            if dx == 0 or dy == 0:
                difficulty = difficulty / self.COST_LINE
            else:
                difficulty = difficulty / self.COST_DIAG

            # Update the map with the new cell
            self.map.add((self.x, self.y), difficulty, seq, self.check_walls_and_lim())
            #print(f"{self.NAME}:at ({self.x}, {self.y}), diffic: {difficulty:.2f} vict: {seq} rtime: {self.get_rtime()}")

        return

    def come_back(self):
        dx, dy = self.walk_stack.pop()
        dx = dx * -1
        dy = dy * -1

        result = self.walk(dx, dy)
        if result == VS.BUMPED:
            print(f"{self.NAME}: when coming back bumped at ({self.x+dx}, {self.y+dy}) , rtime: {self.get_rtime()}")
            return
        
        if result == VS.EXECUTED:
            # update the agent's position relative to the origin
            self.x += dx
            self.y += dy
            print(f"{self.NAME}: coming back at ({self.x}, {self.y}), rtime: {self.get_rtime()}")
        
    def DFS_online(self):
        pos_atual = (self.x, self.y)
        # se a posicao atual nao esta no dicionario untried
        if pos_atual not in self.untried:
            #   adiciona a posicao atual no untried com suas 8 opcoes
            self.untried[pos_atual] = list(range(8))

        # recupera posicao anterior se possivel, iremos usar depois
        pos_anterior = None
        if not self.walk_stack.is_empty():
            dx, dy = self.walk_stack.peek()
            dx = dx * -1
            dy = dy * -1
            pos_anterior = (self.x + dx, self.y + dy)

        # transformando as direcoes do agente atual em numeros de 0 a 7
        lista_direcoes_agente = [self.action_order[action] for action in self.actions]
        
        # se todas as direcoes possiveis dessa posicao ja foram exploradas
        if all(action not in lista_direcoes_agente for action in self.untried.get(pos_atual, [])):            
            # Adiciono, para a pilha de backtracked da proxima posicao, a posicao atual
            proxima_pos = self.backtracked[pos_atual].pop()
            # verifica se a posicao atual existe no dicionário backtracked
            if proxima_pos in self.backtracked:
                # Adiciona a pos_atual ao array associado à chave proxima_pos
                self.backtracked[proxima_pos].append(pos_atual)
            else:
                # Se proxima_pos não existir no dicionário, cria uma nova entrada com pos_atual como o único elemento da lista
                self.backtracked[proxima_pos] = [pos_atual]

            # agora de fato move para a proxima posicao, que na vdd era a ultima adicionada em seu backtracked
            direction = self.calcular_direcao(pos_atual, proxima_pos)
            return direction

        else:
            #  verifica qual a ordem de direcoes desse agente e pega a primeira que der match no array
            #  correspondente da posicao atual do dicionario
            for direcao in lista_direcoes_agente:
                if direcao in self.untried[pos_atual]:
                    # retira esse valor das direcoes para essa posicao     
                    self.untried[pos_atual].remove(direcao)

                    # caso nao seja a primeira execucao
                    if pos_anterior is not None:
                        # Adiciona a posicao anterior na pilha de backtracked:
                        # verifica se a posicao atual existe no dicionário backtracked
                        if pos_atual in self.backtracked:
                            # Adiciona a pos_anterior ao array associado à chave pos_atual
                            self.backtracked[pos_atual].append(pos_anterior)
                        else:
                            # Se pos_atual não existir no dicionário, cria uma nova entrada com pos_anterior como o único elemento da lista
                            self.backtracked[pos_atual] = [pos_anterior]

                    # retorna a direcao
                    return direcao
    
    def calcular_direcao(self, base, target):   
        # auxiliar para DFS online
        x_base, y_base = base
        x_target, y_target = target

        diff_x = x_target - x_base
        diff_y = y_target - y_base

        if diff_y == 0:
            if diff_x == 1:
                return 2
            elif diff_x == -1:
                return 6
        elif diff_x == 0:
            if diff_y == 1:
                return 0
            elif diff_y == -1:
                return 4
        elif diff_y == 1:
            if diff_x == 1:
                return 1
            elif diff_x == -1:
                return 7
        elif diff_y == -1:
            if diff_x == 1:
                return 3
            elif diff_x == -1:
                return 5
    
    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        consumed_time = self.TLIM - self.get_rtime()
        if consumed_time < self.get_rtime():
            self.explore()
            return True

        # time to come back to the base
        if self.walk_stack.is_empty() or (self.x == 0 and self.y == 0):
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"{self.NAME}: rtime {self.get_rtime()}, invoking the rescuer")
            #input(f"{self.NAME}: type [ENTER] to proceed")
            self.resc.go_save_victims(self.map, self.victims)
            return False

        return self.come_back_with_astar()
        

# **************
#  A-star
# *************

    # Chama o algoritmo do a* para achar o menor caminho
    def find_shortest_path(self, graph, start, goal):
        astar = AStarExplorer(graph, start, goal, self.COST_DIAG, self.COST_LINE, self.map)
        path = list(astar.find_path())
        return path

    # Retorna um objeto adjacency_matrix[i][j], que vale 1 se há uma aresta entre os vértices i e j, e 0 caso contrário. 
    # Cada vértice na matriz corresponde a uma posição visitada pelo agente no mapa.
    def build_adjacency_matrix(self):
        adjacency_matrix = [[0] * len(self.map.map_data) for _ in range(len(self.map.map_data))]

        # Mapeia as coordenadas visitadas para seus índices na matriz
        coord_to_index = {}
        index = 0
        for coord in self.map.map_data.keys():
            coord_to_index[coord] = index
            index += 1

        # Preenche a matriz de adjacências
        for coord, data in self.map.map_data.items():
            x, y = coord
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue  # Ignora a própria posição
                    neighbor_coord = (x + dx, y + dy)
                    if self.map.in_map(neighbor_coord):
                        # Se a vizinhança foi visitada, atualize a matriz de adjacências
                        if data[0] != VS.WALL and self.map.map_data[neighbor_coord][0] != VS.WALL:
                            adjacency_matrix[coord_to_index[coord]][coord_to_index[neighbor_coord]] = 1

        return adjacency_matrix

    def come_back_with_astar(self):
        # monta grafo com as posicoes exploradas (o mapa) usando matriz de adjacencias
        adjacency_matrix = self.build_adjacency_matrix()

        # Uso do A* para achar o caminho mais curto de volta
        shortest_path = self.find_shortest_path(adjacency_matrix, (self.x, self.y), (0, 0))
        
        # Verificar se o caminho foi encontrado
        if len(shortest_path) >= 2:
            # O próximo movimento será a próxima posição no caminho mais curto
            next_position = shortest_path[1]  # A primeira posição é a atual
            dx = next_position[0] - self.x
            dy = next_position[1] - self.y

            # Executar o movimento
            result = self.walk(dx, dy)

            # Verificar se o movimento foi bem-sucedido
            if result == VS.EXECUTED:
                # Atualizar a posição do agente
                self.x = next_position[0]
                self.y = next_position[1]
                return True
            elif result == VS.BUMPED:
                print(f"{self.NAME}: when coming back bumped at ({self.x+dx}, {self.y+dy}) , rtime: {self.get_rtime()}")
                return False
        else:
            # Se o caminho não foi encontrado, não há ação a ser tomada
            print("Caminho não encontrado.")
            return False