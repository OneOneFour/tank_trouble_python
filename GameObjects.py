import math
from pygame import Color, Vector2
import pygame

TANK_IMAGE = "./assets/tank.png"
TANK_COLORS = {
    "red": (220, 0, 0),
    "green": (0, 220, 0),
    "blue": (0, 0, 220),
    "yellow": (220, 200, 0)
}


class GameObject:
    __all_objects = []

    @classmethod
    def destroy_all(cls):
        cls.__all_objects = []

    @classmethod
    def destroy(cls, object):
        for i, obj in enumerate(cls.__all_objects):
            if obj is object:
                object.alive = False
                del cls.__all_objects[i]

    @classmethod
    def get_all_objects(cls):
        return cls.__all_objects

    @classmethod
    def get_all_of_type(cls, type):
        return [go for go in cls.__all_objects if isinstance(go, type)]

    @classmethod
    def update_and_blit(cls, screen, dt):
        for obj in cls.__all_objects:
            obj.update(dt)
            obj.draw(screen)

    def __init__(self, x, y, v_x=0., v_y=0., ):
        self.x = x
        self.y = y
        self.v_x = v_x
        self.v_y = v_y
        self.alive = True
        GameObject.__all_objects.append(self)

    def update(self, dt):
        self.x += dt * self.v_x
        self.y += dt * self.v_y

    def mag_v(self):
        return (self.v_x ** 2 + self.v_y ** 2) ** 0.5

    def draw(self, screen):
        pass


class Wall(GameObject):
    def __init__(self, x, y, width, height):
        super().__init__(x, y)
        self.width = width
        self.height = height

    def check_tank_collision(self, tank: "Tank", dt):
        rect = tank.surface.get_rect()
        rect.center = (tank.x + tank.v_x * dt, tank.y + tank.v_y * dt)
        return rect.right > self.x and self.x + self.width > rect.left and rect.bottom > self.y and self.y + self.height > rect.top

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, 0, self.get_rect())

    def update(self, dt):
        pass


class VWall(Wall):
    def __init__(self, x, y):
        super().__init__(x, y, 6, 70)


class HWall(Wall):
    def __init__(self, x, y):
        super().__init__(x, y, 70, 6)


class Projectile(GameObject):
    lifespan = 10
    radius = 5
    speed = 230
    no_collision = 0.25

    def check_collision_tank(self, tank: "Tank"):
        # Account for rotation by moving point into LIF of the tank
        proj_x_tank = (self.x - tank.x) * math.cos(math.radians(tank.rotation)) - (self.y - tank.y) * math.sin(
            math.radians(tank.rotation))
        proj_y_tank = (self.y - tank.y) * math.cos(math.radians(tank.rotation)) + (self.x - tank.x) * math.sin(
            math.radians(tank.rotation))

        return proj_x_tank + self.radius > -tank.width / 2 and tank.width / 2 > proj_x_tank - self.radius and proj_y_tank + self.radius > -tank.height / 2 and tank.height / 2 > proj_y_tank - self.radius

    def wall_check(self, wall, dt):
        coll = wall.x + wall.width > self.x - self.radius and self.x + self.radius > wall.x and wall.y + wall.height > self.y - self.radius and self.y + self.radius > wall.y
        if coll:
            # Rewind time
            prev_x = self.x - self.v_x * dt
            prev_y = self.y - self.v_y * dt
            prev_y_col = wall.y + wall.height > prev_y - self.radius and prev_y + self.radius > wall.y
            if prev_y_col:
                return 1  # Collision in the X
            else:
                return 2
        else:
            return 0

    def __init__(self, x, y, angle, tank, launch_speed=0, ):
        v_x = -(self.speed + launch_speed) * math.sin(math.radians(angle))
        v_y = -(self.speed + launch_speed) * math.cos(math.radians(angle))
        super().__init__(x, y, v_x, v_y)
        self.t = 0
        self.tank = tank

    @property
    def left(self):
        return self.x - self.radius

    @property
    def right(self):
        return self.x + self.radius

    @property
    def top(self):
        return self.y - self.radius

    @property
    def bottom(self):
        return self.y + self.radius

    def update(self, dt):
        self.t += dt
        if self.t >= self.lifespan:
            self.tank.ammo += 1
            GameObject.destroy(self)
        if self.t > self.no_collision:
            self.check_for_collisions(dt)

        super().update(dt)

    def check_for_collisions(self, dt):
        for p in GameObject.get_all_objects():
            if isinstance(p, Tank):
                if self.check_collision_tank(p):
                    GameObject.destroy(p)
                    GameObject.destroy(self)
            if isinstance(p, Wall):
                if self.wall_check(p, dt) == 1:
                    self.v_x = -self.v_x
                if self.wall_check(p, dt) == 2:
                    self.v_y = -self.v_y

    def draw(self, screen):
        pygame.draw.circle(screen, 0, (int(self.x), int(self.y)), self.radius)


class Tank(GameObject):
    turn_speed = 90
    move_speed = 110
    reload_frames = 10
    base_ammo = 5

    @staticmethod
    def WASD(tank):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            tank.direction = 1
        elif keys[pygame.K_s]:
            tank.direction = -1
        if keys[pygame.K_a]:
            tank.omega = 1
        elif keys[pygame.K_d]:
            tank.omega = -1
        if keys[pygame.K_q]:
            tank.fire()

    @staticmethod
    def ARROWS(tank):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            tank.direction = 1
        elif keys[pygame.K_DOWN]:
            tank.direction = -1
        if keys[pygame.K_LEFT]:
            tank.omega = 1
        elif keys[pygame.K_RIGHT]:
            tank.omega = -1
        if keys[pygame.K_SPACE]:
            tank.fire()

    @classmethod
    def handle_events(cls):
        all_tanks = cls.get_all_of_type(cls)
        for tank in all_tanks:
            tank.omega = 0
            tank.direction = 0
            tank.controls(tank)

    @classmethod
    def load_tank_text(cls):
        cls.tank_texture = pygame.image.load(TANK_IMAGE)

    def __init__(self, x, y, color, controls):
        super().__init__(x, y)
        self.reload = 0
        self.rotation = 0
        self.omega = 0
        self.direction = 0
        self.ammo = self.base_ammo
        self.color = TANK_COLORS[color]
        self.surface = self.tank_texture.copy()
        self.surface.fill(self.color[0:3], None, pygame.BLEND_RGBA_MULT)
        self.controls = controls
        self.width = self.surface.get_rect().width
        self.height = self.surface.get_rect().height

    # TODO: add key_up method

    def update(self, dt):
        self.rotation += (self.turn_speed * self.omega * dt) % 360
        self.v_x = -self.direction * self.move_speed * math.sin(math.radians(self.rotation))
        self.v_y = -self.direction * self.move_speed * math.cos(math.radians(self.rotation))
        for obj in GameObject.get_all_of_type(Wall):
            if obj.check_tank_collision(self, dt):
                self.v_x = 0
                self.v_y = 0
                self.omega = 0

                # Reload
        if self.reload > 0:
            self.reload -= 1
        super().update(dt)

    def fire(self):
        if self.reload == 0 and self.ammo > 0:
            Projectile(self.x, self.y, self.rotation, self, self.mag_v())
            self.reload = self.reload_frames
            self.ammo -= 1

    def draw(self, screen):
        rot_surf = pygame.transform.rotate(self.surface, self.rotation)
        rect = rot_surf.get_rect()
        rect.center = (self.x, self.y)
        screen.blit(rot_surf, rect)
