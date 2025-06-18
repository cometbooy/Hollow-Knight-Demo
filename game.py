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
PLAYER_COLOR = (255, 255, 255)  
PLAYER_EYES = (0, 0, 0)  
PLAYER_CLOAK = (70, 70, 90) 


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
        
        self.velocity_x = 0
        self.velocity_y = 0
        self.jumping = False
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        
        self.attacking = False
        self.attack_cooldown = 0
        self.attack_cooldown_max = 20  
        self.attack_rect = pygame.Rect(0, 0, 70, 50)  
        self.facing_right = True
        
        # Параметры для анимации атаки
        self.attack_frame = 0
        self.attack_angles = []  # Углы для дуги атаки
        for i in range(8):
            self.attack_angles.append(math.pi * i / 8)
        
        self.max_health = 5
        self.health = self.max_health
        self.invulnerable = 0
        self.invulnerable_time = 60

    def update(self):
        # Горизонтальное движение
        self.rect.x += self.velocity_x
        
        # Вертикальное движение
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
        self.velocity_x = -self.speed
        self.facing_right = False
        
    def move_right(self):
        self.velocity_x = self.speed
        self.facing_right = True
        
    def stop(self):
        self.velocity_x = 0
        
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
            slash_surface = pygame.Surface((100, 100), pygame.SRCALPHA)

            progress = (self.attack_cooldown_max - self.attack_cooldown) / self.attack_cooldown_max
            
            # Параметры дуги
            radius = 40
            if self.facing_right:
                start_angle = -math.pi/4  # -45 градусов
                end_angle = math.pi/4     # 45 градусов
            else:
                start_angle = 3*math.pi/4  # 135 градусов
                end_angle = 5*math.pi/4    # 225 градусов
            
           
            points = []
            for angle in self.attack_angles:
                current_angle = start_angle + (end_angle - start_angle) * progress + angle * progress
                x = 50 + math.cos(current_angle) * radius
                y = 50 + math.sin(current_angle) * radius
                points.append((x, y))
            
            if len(points) > 2:
                
                for i in range(4):
                    glow_radius = radius + i * 2
                    glow_points = []
                    for angle in self.attack_angles:
                        current_angle = start_angle + (end_angle - start_angle) * progress + angle * progress
                        x = 50 + math.cos(current_angle) * glow_radius
                        y = 50 + math.sin(current_angle) * glow_radius
                        glow_points.append((x, y))
                    
                    pygame.draw.polygon(slash_surface, (255, 255, 255, 40), glow_points)
                
                
                pygame.draw.polygon(slash_surface, (255, 255, 255, 255), points)

           
            if self.facing_right:
                screen.blit(slash_surface, (self.rect.centerx - 20, self.rect.centery - 50))
            else:
                screen.blit(slash_surface, (self.rect.centerx - 80, self.rect.centery - 50))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
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

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        boss_image_path = os.path.join(GAME_DIR, "assets", "pngwing.com.png")

        self.image = pygame.image.load(boss_image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (140, 140))
         

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
          
        self.max_health = 20 
        self.health = self.max_health 
        self.damage = 2  
        self.attack_cooldown = 0
        self.attack_cooldown_max = 60 
        
        
    def update(self):
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
    def should_attack(self):
        return self.attack_cooldown == 0
        
    def reset_attack_cooldown(self):
        self.attack_cooldown = self.attack_cooldown_max

    def get_attack_target(self, player_rect):
       
        return self.rect.centerx, self.rect.centery, player_rect.centerx, player_rect.centery

    def take_damage(self):
        self.health -= 1
        return self.health <= 0
        
    def can_attack(self):
        return self.attack_cooldown == 0
        
    def is_alive(self):
        return self.health > 0

    def spawn_boss(self):
       
        x = WINDOW_WIDTH // 2 - (120 // 2) 
        y = WINDOW_HEIGHT // 2 - (120 // 2) 
        self.boss = Boss(x, y)
        self.all_sprites.add(self.boss)
        self.enemies.add(self.boss) 
        
    def boss_spawn_projectile(self):
    
        pass

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        self.image.fill(YELLOW) 
        pygame.draw.circle(self.image, WHITE, (7, 7), 5) 
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.speed = 5
        
      
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            self.velocity_x = (dx / distance) * self.speed
            self.velocity_y = (dy / distance) * self.speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
            
    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
       
        if self.rect.x < -50 or self.rect.x > WINDOW_WIDTH + 50 or \
           self.rect.y < -50 or self.rect.y > WINDOW_HEIGHT + 50:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((100, 70, 50))  
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        
        main_color = (100, 70, 50)
        highlight_color = (130, 100, 80)
        shadow_color = (70, 40, 30)
        
      
        pygame.draw.rect(self.image, main_color, (0, 0, width, height))
        
        pygame.draw.rect(self.image, highlight_color, (0, 0, width, 5))
        
       
        pygame.draw.rect(self.image, shadow_color, (0, height - 5, width, 5))
        
      
        pygame.draw.rect(self.image, shadow_color, (0, 0, 5, height))
        pygame.draw.rect(self.image, shadow_color, (width - 5, 0, 5, height))
        
      
        center_x = width // 2
        center_y = height // 2
        
     
        pygame.draw.polygon(self.image, highlight_color, [
            (center_x, center_y - 10),
            (center_x + 10, center_y),
            (center_x, center_y + 10),
            (center_x - 10, center_y)
        ])
        
        
        pygame.draw.circle(self.image, shadow_color, (center_x, center_y), 3)
        
     
        pygame.draw.rect(self.image, highlight_color, (10, center_y - 2, 10, 4))
        pygame.draw.rect(self.image, highlight_color, (width - 20, center_y - 2, 10, 4))

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
        self.platforms = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group() 
        
        self.player = Player(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 110)
        self.all_sprites.add(self.player)
        
       
        self.create_level_platforms()
        
        
        self.spawn_boss()

    def spawn_boss(self):
       
        x = WINDOW_WIDTH // 2 - (120 // 2) 
        y = WINDOW_HEIGHT // 2 - (120 // 2) 
        self.boss = Boss(x, y)
        self.all_sprites.add(self.boss)
        self.enemies.add(self.boss)
    

    def boss_spawn_projectile(self):
        pass

    def create_level_platforms(self):
       
        ground = Platform(0, WINDOW_HEIGHT - 50, WINDOW_WIDTH, 50)
        self.all_sprites.add(ground)
        self.platforms.add(ground)
        
       
        self.add_platform(50, WINDOW_HEIGHT - 180, 100, 20)
        self.add_platform(WINDOW_WIDTH / 2 - 75, WINDOW_HEIGHT - 180, 150, 20) 
        self.add_platform(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 180, 150, 20) 
        
       
        self.add_platform(200, WINDOW_HEIGHT - 300, 120, 20) 
        self.add_platform(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 300, 120, 20) 

        self.add_platform(100, WINDOW_HEIGHT - 420, 80, 20) 
        self.add_platform(WINDOW_WIDTH / 2 - 40, WINDOW_HEIGHT - 420, 80, 20) 
        self.add_platform(WINDOW_WIDTH - 180, WINDOW_HEIGHT - 420, 80, 20)

        self.add_platform(50, WINDOW_HEIGHT - 300, 100, 60) 

    def add_platform(self, x, y, width, height):
        platform = Platform(x, y, width, height)
        self.all_sprites.add(platform)
        self.platforms.add(platform)

    def spawn_enemies(self, count):
       
        pass

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
                       
                        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
                        for enemy in hits:
                            if isinstance(enemy, Boss):
                                enemy.take_damage()
                            else:
                                enemy.kill()
                elif event.key == K_ESCAPE:
                    self.state = GameState.PAUSED
            elif event.type == KEYUP:  
                if event.key in [K_LEFT, K_RIGHT, K_a, K_d]:  
                    self.player.stop() 

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
                elif event.type == K_ESCAPE:
                    self.state = GameState.MENU

    def check_attack_collision(self):
        
        for entity in self.enemies: 
            if self.player.attack_rect.colliderect(entity.rect):
                if isinstance(entity, Boss): 
                    if entity.take_damage():
                        entity.kill()
                        
                        print("Босс побежден!")
                        
                        self.state = GameState.GAME_OVER 

    def update_playing(self):
        if not self.player.is_alive():
            self.state = GameState.GAME_OVER
            return
            
        self.all_sprites.update()
        
    
        if self.boss.is_alive() and self.boss.should_attack():
            bx, by, tx, ty = self.boss.get_attack_target(self.player.rect)
            projectile = Projectile(bx, by, tx, ty)
            self.all_sprites.add(projectile)
            self.projectiles.add(projectile)
            self.boss.reset_attack_cooldown()

      
        player_on_ground = False
        player_hits_platforms = pygame.sprite.spritecollide(self.player, self.platforms, False)
        for platform in player_hits_platforms:
      
            if self.player.velocity_y > 0 and self.player.rect.bottom <= platform.rect.bottom:
                self.player.rect.bottom = platform.rect.top
                self.player.velocity_y = 0
                self.player.jumping = False
                player_on_ground = True
        
    
        if not player_on_ground and not self.player.jumping and self.player.velocity_y == 0:
            self.player.velocity_y += self.player.gravity 


        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for entity in hits:
            if entity.can_attack():
                if self.player.take_damage(entity.damage):
                    entity.attack_cooldown = entity.attack_cooldown_max

     
        for entity in self.enemies:
            pass
        projectile_hits = pygame.sprite.spritecollide(self.player, self.projectiles, True)
        for projectile in projectile_hits:
            self.player.take_damage(1)

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
        # Градиентный фон (от светлого к темному)
        for y in range(WINDOW_HEIGHT):
            r = int(200 - 150 * (y / WINDOW_HEIGHT))
            g = int(180 - 100 * (y / WINDOW_HEIGHT))
            b = int(220 - 120 * (y / WINDOW_HEIGHT))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))
            
        # Отрисовка имитации облаков (нижняя часть)
        for i in range(5):
            alpha = 100 - i * 15 # Чем ниже, тем прозрачнее
            cloud_color = (150, 150, 170, alpha)
            cloud_rect = pygame.Rect(0, WINDOW_HEIGHT - 150 + i * 20, WINDOW_WIDTH, 50)
            s = pygame.Surface((cloud_rect.width, cloud_rect.height), pygame.SRCALPHA)
            s.fill(cloud_color)
            self.screen.blit(s, (cloud_rect.x, cloud_rect.y))

        self.all_sprites.draw(self.screen)
        
        self.player.draw_attack_effect(self.screen)
        
        # Отрисовка полоски здоровья босса
        if hasattr(self, 'boss') and self.boss.is_alive():
            boss_health_width = 300
            boss_health_height = 25
            boss_health_x = WINDOW_WIDTH // 2 - boss_health_width // 2
            boss_health_y = 20
            
            pygame.draw.rect(self.screen, RED, (boss_health_x, boss_health_y, boss_health_width, boss_health_height))
            current_boss_health_width = (self.boss.health / self.boss.max_health) * boss_health_width
            pygame.draw.rect(self.screen, GREEN, (boss_health_x, boss_health_y, current_boss_health_width, boss_health_height))
            
            boss_hp_text = self.font.render(f"Босс: {self.boss.health}/{self.boss.max_health}", True, WHITE)
            text_rect = boss_hp_text.get_rect(center=(WINDOW_WIDTH/2, boss_health_y + boss_health_height/2))
            self.screen.blit(boss_hp_text, text_rect)
        
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