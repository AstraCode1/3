from tkinter import *
from PIL import Image, ImageTk
import numpy as np
import random

class Entity:
    def __init__(self, name, color, markedBoxColor):
        self.name = name
        self.color = color
        self.markedBoxColor = markedBoxColor
        self.score = 0

class Player(Entity):
    pass

class Agent(Entity):
    def __init__(self, name, color, markedBoxColor, numberOfDots):
        super().__init__(name, color, markedBoxColor)
        self.numberOfDots = numberOfDots

    def playMove(self, stateOfBoxes, markedBoxes, stateOfRows, stateOfColumns, stateOfBoxesLines):
        # 优先完成可以立即得分的盒子
        boxes = np.argwhere(stateOfBoxes == 3)
        for box in boxes:
            index, col = box
            b = [index, col]
            if b not in markedBoxes:
                if stateOfBoxesLines[index][col] == 1:
                    possible_cols = [
                        (col, index, 'column'),
                        (col + 1, index, 'column')
                    ]
                    for c, r, t in possible_cols:
                        if 0 <= c < stateOfColumns.shape[1] and 0 <= r < stateOfColumns.shape[0]:
                            if stateOfColumns[r][c] == 0:
                                return [c, r], t
                elif stateOfBoxesLines[index][col] == -1:
                    possible_rows = [
                        (col, index, 'row'),
                        (col, index + 1, 'row')
                    ]
                    for c, r, t in possible_rows:
                        if 0 <= c < stateOfRows.shape[1] and 0 <= r < stateOfRows.shape[0]:
                            if stateOfRows[r][c] == 0:
                                return [c, r], t

        # 收集所有合法移动
        possible_moves = []
        rows, cols = np.where(stateOfRows == 0)
        for r, c in zip(rows, cols):
            possible_moves.append(('row', (r, c)))
        rows, cols = np.where(stateOfColumns == 0)
        for r, c in zip(rows, cols):
            possible_moves.append(('column', (r, c)))

        if not possible_moves:
            return -1, -1

        # 评估每个移动的得分
        scored_moves = []
        for move_type, pos in possible_moves:
            dangerous = self.is_move_dangerous(move_type, pos, stateOfBoxes, self.numberOfDots)
            double_chances = self.count_double_chances(move_type, pos, stateOfBoxes)
            score = (not dangerous) * 100 + double_chances
            scored_moves.append((score, move_type, pos))

        # 选择最优移动
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        best_score = scored_moves[0][0]
        best_moves = [m for m in scored_moves if m[0] == best_score]
        chosen_move = random.choice(best_moves) if best_moves else scored_moves[0]

        move_type, pos = chosen_move[1], chosen_move[2]
        if move_type == 'row':
            return [pos[1], pos[0]], move_type
        else:
            return [pos[1], pos[0]], move_type

    def count_double_chances(self, move_type, pos, stateOfBoxes):
        row, col = pos
        count = 0
        if move_type == 'row':
            if row > 0:
                box_row, box_col = row - 1, col
                if stateOfBoxes[box_row][box_col] + 1 == 3:
                    count += 1
            if row < stateOfBoxes.shape[0]:
                box_row, box_col = row, col
                if stateOfBoxes[box_row][box_col] + 1 == 3:
                    count += 1
        elif move_type == 'column':
            if col > 0:
                box_row, box_col = row, col - 1
                if stateOfBoxes[box_row][box_col] + 1 == 3:
                    count += 1
            if col < stateOfBoxes.shape[1]:
                box_row, box_col = row, col
                if stateOfBoxes[box_row][box_col] + 1 == 3:
                    count += 1
        return count

    def is_move_dangerous(self, move_type, position, stateOfBoxes, numberOfDots):
        row, col = position
        dangerous = False

        if move_type == 'row':
            if row > 0:
                box_row, box_col = row - 1, col
                if stateOfBoxes[box_row][box_col] + 1 >= 3:
                    dangerous = True
            if row < numberOfDots - 1:
                box_row, box_col = row, col
                if stateOfBoxes[box_row][box_col] + 1 >= 3:
                    dangerous = True
        elif move_type == 'column':
            if col > 0:
                box_row, box_col = row, col - 1
                if stateOfBoxes[box_row][box_col] + 1 >= 3:
                    dangerous = True
            if col < numberOfDots - 1:
                box_row, box_col = row, col
                if stateOfBoxes[box_row][box_col] + 1 >= 3:
                    dangerous = True
        return dangerous

class Setup:
    boardSize = 600
    dotColor = '#CCCCCC'
    lineColor = '#6A889C'
    backgroundColor = '#2A4E6C'

    def setup(self, numberOfDots):
        self.numberOfDots = numberOfDots
        self.dotWidth = 0.15 * self.boardSize / numberOfDots
        self.markedLineWidth = 0.1 * self.boardSize / numberOfDots
        self.distanceBetweenDots = self.boardSize / numberOfDots

class Game:
    def __init__(self, player_first=True, player_color='red', ai_color='blue'):
        self.window = Tk()
        self.window.configure(bg=Setup.backgroundColor)
        self.window.title('Dots and Boxes')
        self.canvas = Canvas(self.window, width=Setup.boardSize, height=Setup.boardSize, highlightthickness=0)
        self.canvas.pack()
        self.canvas.configure(bg=Setup.backgroundColor)
        self.window.bind('<Button-1>', self.click)
        self.playerStarts = player_first
        self.player_color = player_color
        self.ai_color = ai_color
        self.undo_stack = []
        self.initialize()

    def initialize(self):
        global player, agent
        player = Player(player_name,
                        '#FF0000' if self.player_color == 'red' else '#0000FF',
                        '#FF9999' if self.player_color == 'red' else '#9999FF')
        agent = Agent('AI',
                      '#FF0000' if self.ai_color == 'red' else '#0000FF',
                      '#FF9999' if self.ai_color == 'red' else '#9999FF',
                      Setup.numberOfDots)
        agent.score, player.score = 0, 0
        self.refreshScreen(True)
        self.stateOfBoxes = np.zeros(shape=(Setup.numberOfDots - 1, Setup.numberOfDots - 1))
        self.stateOfBoxesLines = np.zeros(shape=(Setup.numberOfDots - 1, Setup.numberOfDots - 1))
        self.stateOfRows = np.zeros(shape=(Setup.numberOfDots, Setup.numberOfDots - 1))
        self.stateOfColumns = np.zeros(shape=(Setup.numberOfDots - 1, Setup.numberOfDots))
        self.row_owners = np.zeros_like(self.stateOfRows, dtype=object)
        self.column_owners = np.zeros_like(self.stateOfColumns, dtype=object)
        self.playerStarts = not self.playerStarts
        self.playerTurn = not self.playerStarts
        self.gameRestart = False
        self.score = []
        self.markedBoxes = []
        self.box_owners = {}
        self.showGameState()
        self.canvas.create_text(Setup.boardSize - 20, 10, font='Helvetica 10 bold', text='v2.0', fill='white')
        self.welcome = self.canvas.create_text(10, 15, font='Helvetica 12 bold', text='', anchor=NW)

        text = 'Good luck!'
        delay = 0
        for i in range(len(text) + 1):
            newText = lambda s=text[:i]: self.canvas.itemconfigure(self.welcome, text=s, fill='white')
            self.canvas.after(delay, newText)
            delay += 100

        try:
            image = Image.open("restart.png")
            image = ImageTk.PhotoImage(image)
            label = Label(image=image, highlightthickness=0, borderwidth=0)
            label.image = image
            label.place(x=0, y=Setup.boardSize - 40)
            label.bind('<Button-1>', self.restartGame)
        except:
            Button(self.window, text="Restart", command=self.restartGame).place(x=0, y=Setup.boardSize - 40)

        self.undo_button = Button(self.window, text="Undo", command=self.undo)
        self.undo_button.place(x=60, y=Setup.boardSize - 40)

        if not self.playerTurn:
            self.playAgentMove()

    def save_state(self):
        state = {
            'stateOfRows': np.copy(self.stateOfRows),
            'stateOfColumns': np.copy(self.stateOfColumns),
            'stateOfBoxes': np.copy(self.stateOfBoxes),
            'stateOfBoxesLines': np.copy(self.stateOfBoxesLines),
            'row_owners': np.copy(self.row_owners),
            'column_owners': np.copy(self.column_owners),
            'markedBoxes': list(self.markedBoxes),
            'box_owners': dict(self.box_owners),
            'player_score': player.score,
            'agent_score': agent.score,
            'playerTurn': self.playerTurn,
        }
        self.undo_stack.append(state)

    def undo(self):
        if len(self.undo_stack) > 0:
            prev_state = self.undo_stack.pop()
            self.stateOfRows = prev_state['stateOfRows']
            self.stateOfColumns = prev_state['stateOfColumns']
            self.stateOfBoxes = prev_state['stateOfBoxes']
            self.stateOfBoxesLines = prev_state['stateOfBoxesLines']
            self.row_owners = prev_state['row_owners']
            self.column_owners = prev_state['column_owners']
            self.markedBoxes = prev_state['markedBoxes']
            self.box_owners = prev_state['box_owners']
            player.score = prev_state['player_score']
            agent.score = prev_state['agent_score']
            self.playerTurn = prev_state['playerTurn']
            self.canvas.delete('all')
            self.refreshScreen(True)
            self.redraw_all_lines_and_boxes()
            self.showGameState()

    def redraw_all_lines_and_boxes(self):
        for row in range(self.stateOfRows.shape[0]):
            for col in range(self.stateOfRows.shape[1]):
                if self.stateOfRows[row][col] == 1:
                    owner = self.row_owners[row][col]
                    linePosition = [col, row]
                    self.markLine('row', linePosition, owner)
        for row in range(self.stateOfColumns.shape[0]):
            for col in range(self.stateOfColumns.shape[1]):
                if self.stateOfColumns[row][col] == 1:
                    owner = self.column_owners[row][col]
                    linePosition = [col, row]
                    self.markLine('column', linePosition, owner)
        for box_coord in self.markedBoxes:
            owner = self.box_owners.get(tuple(box_coord))
            if owner:
                self.fillBox(box_coord, owner.markedBoxColor)

    def start(self):
        self.window.mainloop()

    def restartGame(self, event=None):
        self.canvas.delete('all')
        self.initialize()

    def findLinePosition(self, clickPosition):
        clickPosition = np.array(clickPosition)
        position = (clickPosition - Setup.distanceBetweenDots / 4) // (Setup.distanceBetweenDots / 2)

        typ = False
        linePosition = []

        if self.hasValueLessThan(position, 0):
            if position[1] % 2 == 0 and (position[0] - 1) % 2 == 0:
                column = int((position[0] - 1) // 2)
                row = int(position[1] // 2)
                linePosition = [column, row]
                typ = 'row'
            elif position[0] % 2 == 0 and (position[1] - 1) % 2 == 0:
                column = int(position[0] // 2)
                row = int((position[1] - 1) // 2)
                linePosition = [column, row]
                typ = 'column'

        return linePosition, typ

    def hasValueLessThan(self, position, value):
        for i in position:
            if i < value:
                return False
        return True

    def lineAlreadyDrawn(self, linePosition, typ):
        row = linePosition[0]
        column = linePosition[1]
        drawn = True
        try:
            if typ == 'row' and self.stateOfRows[column][row] == 0:
                drawn = False
            if typ == 'column' and self.stateOfColumns[column][row] == 0:
                drawn = False
        except:
            return drawn
        return drawn

    def updateStates(self, typ, linePosition, entity):
        column = linePosition[0]
        row = linePosition[1]

        if row < (Setup.numberOfDots - 1) and column < (Setup.numberOfDots - 1):
            self.stateOfBoxes[row][column] += 1
            if typ == 'row':
                self.stateOfBoxesLines[row][column] += 1
            else:
                self.stateOfBoxesLines[row][column] -= 1

        if typ == 'row':
            self.stateOfRows[row][column] = 1
            self.row_owners[row][column] = entity
            if row >= 1:
                self.stateOfBoxes[row - 1][column] += 1
                self.stateOfBoxesLines[row - 1][column] += 1
        elif typ == 'column':
            self.stateOfColumns[row][column] = 1
            self.column_owners[row][column] = entity
            if column >= 1:
                self.stateOfBoxes[row][column - 1] += 1
                self.stateOfBoxesLines[row][column - 1] -= 1

    def markLine(self, typ, linePosition, owner):
        color = owner.color
        if typ == 'row':
            xCoordStart = Setup.distanceBetweenDots / 2 + linePosition[0] * Setup.distanceBetweenDots
            xCoordEnd = xCoordStart + Setup.distanceBetweenDots
            yCoordStart = Setup.distanceBetweenDots / 2 + linePosition[1] * Setup.distanceBetweenDots
            yCoordEnd = yCoordStart
        elif typ == 'column':
            yCoordStart = Setup.distanceBetweenDots / 2 + linePosition[1] * Setup.distanceBetweenDots
            yCoordEnd = yCoordStart + Setup.distanceBetweenDots
            xCoordStart = Setup.distanceBetweenDots / 2 + linePosition[0] * Setup.distanceBetweenDots
            xCoordEnd = xCoordStart

        self.canvas.create_line(xCoordStart, yCoordStart, xCoordEnd, yCoordEnd, fill=color, width=Setup.markedLineWidth)

    def checkBox(self):
        boxes = np.argwhere(self.stateOfBoxes == 4)
        changePlayer = True
        current_entity = player if self.playerTurn else agent

        for box in boxes:
            box_coord = tuple(box)
            if box_coord not in self.markedBoxes:
                self.markedBoxes.append(box_coord)
                self.box_owners[box_coord] = current_entity
                self.fillBox(box, current_entity.markedBoxColor)
                current_entity.score += 1
                changePlayer = False

        if changePlayer:
            self.playerTurn = not self.playerTurn

    def fillBox(self, box, color):
        xCoordStart = Setup.distanceBetweenDots / 2 + box[1] * Setup.distanceBetweenDots + Setup.markedLineWidth / 2
        yCoordStart = Setup.distanceBetweenDots / 2 + box[0] * Setup.distanceBetweenDots + Setup.markedLineWidth / 2
        xCoordEnd = xCoordStart + Setup.distanceBetweenDots - Setup.markedLineWidth
        yCoordEnd = yCoordStart + Setup.distanceBetweenDots - Setup.markedLineWidth
        self.canvas.create_rectangle(xCoordStart, yCoordStart, xCoordEnd, yCoordEnd, fill=color, outline='')

    def refreshScreen(self, gameStart):
        if gameStart:
            for i in range(Setup.numberOfDots):
                x = i * Setup.distanceBetweenDots + Setup.distanceBetweenDots / 2
                self.canvas.create_line(x, Setup.distanceBetweenDots / 2, x,
                                        Setup.boardSize - Setup.distanceBetweenDots / 2, fill=Setup.lineColor,
                                        width=Setup.markedLineWidth)
                self.canvas.create_line(Setup.distanceBetweenDots / 2, x,
                                        Setup.boardSize - Setup.distanceBetweenDots / 2, x, fill=Setup.lineColor,
                                        width=Setup.markedLineWidth)
        for i in range(Setup.numberOfDots):
            for j in range(Setup.numberOfDots):
                xCoordStart = i * Setup.distanceBetweenDots + Setup.distanceBetweenDots / 2
                xCoordEnd = j * Setup.distanceBetweenDots + Setup.distanceBetweenDots / 2
                self.canvas.create_oval(xCoordStart - Setup.dotWidth / 2, xCoordEnd - Setup.dotWidth / 2,
                                        xCoordStart + Setup.dotWidth / 2, xCoordEnd + Setup.dotWidth / 2,
                                        fill=Setup.dotColor, outline=Setup.dotColor)

    def showGameState(self):
        if len(self.score):
            self.canvas.delete(self.score[0])
            self.canvas.delete(self.score[1])
            self.score = []
        self.score.append(self.canvas.create_text(Setup.boardSize / 2 - 100, 20, font='Helvetica 15 bold',
                                                  text=player.name + ': ' + str(player.score),
                                                  fill=player.markedBoxColor))
        self.score.append(self.canvas.create_text(100 + Setup.boardSize / 2, 20, font='Helvetica 15 bold',
                                                  text=agent.name + ': ' + str(agent.score), fill=agent.color))

    def showScore(self):
        victory = True
        winner = None
        if player.score > agent.score:
            winner = player
            text = 'You beat ' + agent.name + '!'
        elif agent.score > player.score:
            winner = agent
            text = agent.name + ' won.'
        else:
            victory = False
        if not victory:
            text = 'It\'s a tie. Click anywhere for a new game.'
        else:
            text += ' Click anywhere to start a new game.'
        self.canvas.create_text(Setup.boardSize / 2, Setup.boardSize - Setup.distanceBetweenDots / 8,
                                font='Helvetica 12 bold', text=text, fill='white')
        self.gameRestart = True

    def click(self, event):
        if not self.gameRestart:
            clickPosition = [event.x, event.y]
            linePosition, typ = self.findLinePosition(clickPosition)
            if typ and not self.lineAlreadyDrawn(linePosition, typ):
                current_entity = player if self.playerTurn else agent
                self.save_state()
                self.updateStates(typ, linePosition, current_entity)
                self.markLine(typ, linePosition, current_entity)
                self.checkBox()
                self.refreshScreen(False)
                self.showGameState()
                if self.gameOver():
                    self.showScore()
                else:
                    if not self.playerTurn:
                        self.playAgentMove()
        else:
            self.canvas.delete('all')
            self.initialize()
            self.gameRestart = False

    def playMove(self, typ, linePosition):
        current_entity = player if self.playerTurn else agent
        self.updateStates(typ, linePosition, current_entity)
        self.markLine(typ, linePosition, current_entity)
        self.checkBox()
        self.refreshScreen(False)
        self.showGameState()
        self.save_state()
        if not self.playerTurn:
            self.playAgentMove()

    def playAgentMove(self):
        linePosition, typ = agent.playMove(self.stateOfBoxes, self.markedBoxes, self.stateOfRows, self.stateOfColumns,
                                           self.stateOfBoxesLines)
        if linePosition != -1 and typ != -1:
            self.playMove(typ, linePosition)

    def gameOver(self):
        return (self.stateOfRows == 1).all() and (self.stateOfColumns == 1).all()


if __name__ == '__main__':
    # 获取玩家名称
    while True:
        player_name = input('你的名字: ').strip()
        if 0 < len(player_name) <= 10:
            break
        print("请重新输入")

    # 获取游戏尺寸
    size=6

    # 选择先手玩家
    while True:
        first = input('选择先手 (1) Player (2) AI [1/2]: ').strip()
        if first in ['1', '2']:
            player_first = (first == '1')
            break
        print("Invalid choice!")

    # 选择玩家颜色
    # 选择玩家颜色
    while True:
        player_color_input = input('选择颜色: (1) Red (2) Blue [1/2]: ').strip()
        if player_color_input in ['1', '2']:
            player_color = 'red' if player_color_input == '1' else 'blue'
            break
        print("Invalid choice!")

    # 自动为AI分配相反颜色（玩家选1则AI选2，玩家选2则AI选1）
    ai_color = 'blue' if player_color == 'red' else 'red'
    print(f"AI 自动选择颜色: {ai_color.capitalize()}")

    # 初始化游戏设置
    Setup.setup(Setup, size)

    # 创建游戏实例
    game = Game(
        player_first=player_first,
        player_color=player_color,
        ai_color=ai_color
    )
    game.start()