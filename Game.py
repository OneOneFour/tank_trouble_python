import pygame
import sys
from GameObjects import GameObject, Tank, HWall, VWall
import random


class Player:
    def __init__(self, control_method, color):
        self.control_method = control_method
        self.color = color
        self.tank = None
        self.score = 0

    @property
    def alive(self):
        try:
            return self.tank.alive
        except AttributeError:
            return False

    def spawn_tank(self, x, y):
        self.tank = Tank(x, y, self.color, self.control_method)


class Level:
    ONE_PLAYER_TIMEOUT = 3

    def __init__(self, game, players):
        self.players = players
        self.game = game
        self.ticker = 0
        self.height = 10
        self.width = 15
        self.generate_maze()
        for p in players:
            p.spawn_tank(random.randint(50, 750), random.randint(50, 420))

    def generate_maze(self):
        for y in range(self.height + 1):
            for x in range(self.width + 1):
                if y < self.height:
                    if x == 0 or x == self.width:
                        VWall(x * 70, y * 70)
                    elif not random.randint(0, 2):
                        VWall(x * 70, y * 70)
                if x < self.width:
                    if y == 0 or y == self.height:
                        HWall(x * 70, y * 70)
                    elif not random.randint(0, 2):
                        HWall(x * 70, y * 70)

    def update(self, dt):
        alive_players = [p for p in self.players if p.alive]
        if len(alive_players) == 0:
            self.game.nextStage()
            print("No one wins")
        if len(alive_players) == 1:
            self.ticker += dt
            if self.ticker >= self.ONE_PLAYER_TIMEOUT:
                print(f"{alive_players[0].color} wins!")
                alive_players[0].score += 1
                self.game.nextStage()


class Game:
    def __init__(self, width: int, height: int):
        pygame.init()
        self.width = width
        self.height = height
        self.load()
        self.screen = pygame.display.set_mode((width, height))
        self.update()

    def load(self):
        Tank.load_tank_text()
        self.players = [Player(Tank.WASD, "red"), Player(Tank.ARROWS, "green")]
        self.level = Level(self, self.players)

    def nextStage(self):
        GameObject.destroy_all()
        self.level = Level(self, self.players)

    def update(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                # Process events for tanks
            Tank.handle_events()
            self.level.update(16 / 1000)
            self.screen.fill((255, 255, 255))
            GameObject.update_and_blit(self.screen, 16 / 1000)
            pygame.display.flip()
            pygame.time.delay(16)


if __name__ == "__main__":
    g = Game(1050, 700)
