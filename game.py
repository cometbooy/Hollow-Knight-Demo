import pygame
import sys
import random
import os
import math
from pygame.locals import *
from enum import Enum

pygame.init()

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PLAYER_COLOR = (255, 255, 255)  # Белый цвет для тела
PLAYER_EYES = (0, 0, 0)  # Черный цвет для глаз
PLAYER_CLOAK = (70, 70, 90)  # Темно-серый цвет для плаща

# Путь к спрайту
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_PATH = os.path.join(GAME_DIR, "assets", "player.png")

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        try:
            self.original_image = pygame.image.load(SPRITE_PATH)
            self.original_image = pygame.transform.scale(self.original_image, (40, 60))
        except:
            self.original_image = pygame.Surface((40, 60))
            self.original_image.fill(WHITE)
        
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.velocity_y = 0
        self.jumping = False
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        
        self.attacking = False
        self.attack_cooldown = 0
        self.attack_cooldown_max = 20  # Уменьшили время атаки для большей отзывчивости
        self.attack_rect = pygame.Rect(0, 0, 70, 50)  # Область атаки как в оригинале
        self.facing_right = True
        
        # Параметры для анимации атаки в стиле Hollow Knight
        self.attack_frame = 0
        self.attack_angles = []  # Углы для дуги атаки
        for i in range(8):
            self.attack_angles.append(math.pi * i / 8)
        
        self.max_health = 5
        self.health = self.max_health
        self.invulnerable = 0
        self.invulnerable_time = 60
    
    def update(self):
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

        if self.rect.bottom > WINDOW_HEIGHT - 50:
            self.rect.bottom = WINDOW_HEIGHT - 50
            self.velocity_y = 0
            self.jumping = False

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            if self.attack_cooldown == 0:
                self.attacking = False
            
        if self.invulnerable > 0:
            self.invulnerable -= 1
            if self.invulnerable % 10 < 5:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)
            
        # Обновление позиции области атаки
        if self.facing_right:
            self.attack_rect.midleft = self.rect.midright
            self.image = self.original_image
        else:
            self.attack_rect.midright = self.rect.midleft
            self.image = pygame.transform.flip(self.original_image, True, False)
            
    def jump(self):
        if not self.jumping:
            self.velocity_y = self.jump_power
            self.jumping = True

    def move_left(self):
        self.rect.x -= self.speed
        self.facing_right = False

    def move_right(self):
        self.rect.x += self.speed
        self.facing_right = True
        
    def attack(self):
        if self.attack_cooldown == 0:
            self.attacking = True
            self.attack_cooldown = self.attack_cooldown_max
            return True
        return False
        
    def take_damage(self, amount):
        if self.invulnerable <= 0:
            self.health -= amount
            self.invulnerable = self.invulnerable_time
            return True
        return False
        
    def is_alive(self):
        return self.health > 0

    def draw_attack_effect(self, screen):
        if self.attacking and self.attack_cooldown > 5:
            # Создаем поверхность для эффекта атаки
            slash_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            
            # Вычисляем прогресс анимации
            progress = (self.attack_cooldown_max - self.attack_cooldown) / self.attack_cooldown_max
            
            # Параметры дуги
            radius = 40
            if self.facing_right:
                start_angle = -math.pi/4  # -45 градусов
                end_angle = math.pi/4     # 45 градусов
            else:
                start_angle = 3*math.pi/4  # 135 градусов
                end_angle = 5*math.pi/4    # 225 градусов
            
            # Рисуем основной след меча (яркий белый)
            points = []
            for angle in self.attack_angles:
                current_angle = start_angle + (end_angle - start_angle) * progress + angle * progress
                x = 50 + math.cos(current_angle) * radius
                y = 50 + math.sin(current_angle) * radius
                points.append((x, y))
            
            if len(points) > 2:
                # Внешнее свечение (белое, полупрозрачное)
                for i in range(4):
                    glow_radius = radius + i * 2
                    glow_points = []
                    for angle in self.attack_angles:
                        current_angle = start_angle + (end_angle - start_angle) * progress + angle * progress
                        x = 50 + math.cos(current_angle) * glow_radius
                        y = 50 + math.sin(current_angle) * glow_radius
                        glow_points.append((x, y))
                    # Рисуем слои свечения от внешнего к внутреннему
                    pygame.draw.polygon(slash_surface, (255, 255, 255, 40), glow_points)
                
                # Яркая центральная линия (чисто белая)
                pygame.draw.polygon(slash_surface, (255, 255, 255, 255), points)
            
            # Определяем позицию эффекта относительно персонажа
            if self.facing_right:
                screen.blit(slash_surface, (self.rect.centerx - 20, self.rect.centery - 50))
            else:
                screen.blit(slash_surface, (self.rect.centerx - 80, self.rect.centery - 50))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Создаем изображение врага
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.speed = 2
        self.direction = 1
        self.movement_counter = 0
        self.movement_limit = 100
        
        self.health = 3
        self.damage = 1
        self.attack_cooldown = 0
        self.attack_cooldown_max = 60
        
    def update(self):
        self.rect.x += self.speed * self.direction
        self.movement_counter += abs(self.speed)
        
        if self.movement_counter >= self.movement_limit:
            self.direction *= -1
            self.movement_counter = 0
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
    def take_damage(self):
        self.health -= 1
        return self.health <= 0
        
    def can_attack(self):
        return self.attack_cooldown == 0

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hollow Knight Clone")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.state = GameState.MENU
        self.running = True
        self.init_game()

    def init_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        
        self.player = Player(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 110)
        self.all_sprites.add(self.player)
        
        self.spawn_enemies(3)

    def spawn_enemies(self, count):
        for _ in range(count):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = WINDOW_HEIGHT - 80
            enemy = Enemy(x, y)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.state = GameState.PLAYING
                elif event.key == K_ESCAPE:
                    self.running = False

    def handle_playing_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    self.player.jump()
                elif event.key == K_x:
                    if self.player.attack():
                        self.check_attack_collision()
                elif event.key == K_ESCAPE:
                    self.state = GameState.PAUSED

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.player.move_left()
        if keys[K_RIGHT]:
            self.player.move_right()

    def handle_paused_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.state = GameState.PLAYING
                elif event.key == K_r:
                    self.init_game()
                    self.state = GameState.PLAYING

    def handle_game_over_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_r:
                    self.init_game()
                    self.state = GameState.PLAYING
                elif event.key == K_ESCAPE:
                    self.state = GameState.MENU

    def check_attack_collision(self):
        for enemy in self.enemies:
            if self.player.attack_rect.colliderect(enemy.rect):
                if enemy.take_damage():
                    enemy.kill()

    def update_playing(self):
        if not self.player.is_alive():
            self.state = GameState.GAME_OVER
            return
            
        self.all_sprites.update()
        
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for enemy in hits:
            if enemy.can_attack():
                if self.player.take_damage(enemy.damage):
                    enemy.attack_cooldown = enemy.attack_cooldown_max

    def draw_menu(self):
        self.screen.fill(BLACK)
        
        title = self.font.render("Hollow Knight Clone", True, WHITE)
        start_text = self.font.render("Нажмите ENTER для начала игры", True, YELLOW)
        exit_text = self.font.render("ESC для выхода", True, WHITE)
        
        title_rect = title.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3))
        start_rect = start_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH/2, 2*WINDOW_HEIGHT/3))
        
        self.screen.blit(title, title_rect)
        self.screen.blit(start_text, start_rect)
        self.screen.blit(exit_text, exit_rect)

    def draw_playing(self):
        self.screen.fill(BLACK)
        
        pygame.draw.rect(self.screen, BLUE, (0, WINDOW_HEIGHT - 50, WINDOW_WIDTH, 50))
        
        self.all_sprites.draw(self.screen)
        
        self.player.draw_attack_effect(self.screen)
        
        health_width = 200
        health_height = 20
        health_x = 10
        health_y = 10
        
        pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = (self.player.health / self.player.max_health) * health_width
        pygame.draw.rect(self.screen, GREEN, (health_x, health_y, current_health_width, health_height))

    def draw_paused(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font.render("ПАУЗА", True, WHITE)
        continue_text = self.font.render("ESC - Продолжить", True, WHITE)
        restart_text = self.font.render("R - Начать заново", True, WHITE)
        
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3))
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH/2, 2*WINDOW_HEIGHT/3))
        
        self.screen.blit(pause_text, pause_rect)
        self.screen.blit(continue_text, continue_rect)
        self.screen.blit(restart_text, restart_rect)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        restart_text = self.font.render("R - Начать заново", True, WHITE)
        menu_text = self.font.render("ESC - Вернуться в меню", True, WHITE)
        
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        menu_rect = menu_text.get_rect(center=(WINDOW_WIDTH/2, 2*WINDOW_HEIGHT/3))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(menu_text, menu_rect)

    def game_loop(self):
        while self.running:
            if self.state == GameState.MENU:
                self.handle_menu_events()
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                self.handle_playing_events()
                self.update_playing()
                self.draw_playing()
            elif self.state == GameState.PAUSED:
                self.handle_paused_events()
                self.draw_playing()
                self.draw_paused()
            elif self.state == GameState.GAME_OVER:
                self.handle_game_over_events()
                self.draw_playing()
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.game_loop()
    pygame.quit()
    sys.exit() 