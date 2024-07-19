import sys

from time import sleep

import pygame

from settings import Settings

from game_stats import GameStats

from scoreboard import Scoreboard

from button import Button

from ship import Ship

from bullet import Bullet

from alien import Alien

from random import choice

from laser import Laser

import obsticle

class AlienInvasion:
    #Overall class to manage game assets and behavior.
    
    def __init__(self):
        #Initialize the game, and create game resource.
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((self.settings.screen_width,self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        #Obsticle set up
        self.shape = obsticle.shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.create_multiple_obsticles(40,670,125,325,525,725,925)

        #Create an instance to store game statistics.
        #Create scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.ready = True
        self.bullet_time = 0
        self.bullet_cooldown = 600
        

        self._create_fleet()

        #Start alien invasion in an active state.
        self.game_active = False

        #Make the Play button.
        self.play_button = Button(self, "Play")

        #Audio
        music = pygame.mixer.Sound('audio/music1.mp3')
        music.set_volume(.5)
        music.play(loops = -1)
        self.laser_sound = pygame.mixer.Sound('audio/laser27.wav')
        self.laser_sound.set_volume(0.1)
        self.explosion_sound = pygame.mixer.Sound('audio/boom.wav')
        self.explosion_sound.set_volume(0.3)

    def run_game(self):
        #Start the main loop for the game.
        while True:
            self._check_events()

            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
              

            self._update_screen()
            self.clock.tick(60)
            
    def _check_events(self):
        ALIENLASER = pygame.USEREVENT + 1
        pygame.time.set_timer(ALIENLASER,17)
        #Watch for keyboard and mouse event.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == ALIENLASER:
                self.alien_shoot()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def collision_checks(self):
        if self.bullets:
            for bullet in self.bullets:
                if pygame.sprite.spritecollide(bullet,self.blocks,True):
                    bullet.kill()
        
        if self.alien_lasers:
            for laser in self.alien_lasers:
                if pygame.sprite.spritecollide(laser,self.blocks,True):
                    laser.kill()
                
                if pygame.sprite.spritecollideany(self.ship,self.alien_lasers):
                    self._ship_hit()

    def _check_play_button(self, mouse_pos):
        #Start a new game when the Player clicks Play.
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            #Reset the game statistics.
            self.settings.initialize_dynamic_settings()
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.game_active = True

            #Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()

            #Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()
            
            #Hide the mouse cursor.
            pygame.mouse.set_visible(False)

    def create_obsticle(self, x_start, y_start,offset_x):
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * self.block_size + offset_x
                    y = y_start + row_index * self.block_size
                    block = obsticle.Block(self.block_size,(241,79,80),x,y)
                    self.blocks.add(block)

    def create_multiple_obsticles(self,x_start,y_start,*offset):
        for offset_x in offset:
            self.create_obsticle(x_start,y_start,offset_x)
        
    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE and self.ready:
            self._fire_bullet()
            self.laser_sound.play()
            self.ready = False
            self.bullet_time = pygame.time.get_ticks()
                     
    def recharge(self):
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.bullet_time >= self.bullet_cooldown:
                self.ready = True

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        #Create a new bullet and add it to the bullets group.
        if len(self.bullets) < self.settings.bullets_allowed: 
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_screen(self):
        #Redraw the screen during each pass through the loop.
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        
        self.ship.blitme()
        self.aliens.draw(self.screen)
        self.blocks.draw(self.screen)
        self.alien_lasers.update()
        self.alien_lasers.draw(self.screen)
        self.collision_checks()

        #Draw the score information.
        self.sb.show_score()

        #Draw the play button if the game is inactive.
        if not self.game_active:
            self.play_button.draw_button()

            #Make the most recently drawn screen visible.
        pygame.display.flip()
            
    def _update_bullets(self):
        self.bullets.update()
        self.recharge()

        #Get rid of bullets that have disappeard.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def alien_shoot(self):
        if self.aliens.sprites():
            random_alien = choice(self.aliens.sprites())
            laser_sprite = Laser(random_alien.rect.center,4,self.settings.screen_height)
            self.alien_lasers.add(laser_sprite)

    def _check_bullet_alien_collisions(self):
        #Respond to bullet-alien collisions.
        #Remove any bullet and aliens that have collided
        #Check for any bullets that have hit aliens.
        #If so , get rid of the bullet and the alien.
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self. settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
            self.explosion_sound.play()
             
        if not self.aliens:
            #Destroy existing bullets and creat new fleet.
            self.bullets.empty()
            self._create_fleet()  
            self.settings.increase_speed() 

            #Increase level
            self.stats.level += 1
            self.sb.prep_level()         

    def _update_aliens(self):
        #Update the positions of all aliens in the fleet.
        self._check_fleet_edges()
        self.aliens.update()    

        #Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()   

        #Look for aliens hitting the bottom of the screen.
            self._check_aliens_bottom() 

    def _check_fleet_edges(self):
        #Respond appropriatetly if any aliens have reached an edge.
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        #Drop the entire fleet and change the fleet's direction.
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _create_fleet(self):
        #Creat the fleet of aliens.
        #Create an alien and keep adding aliens until there's no room left
        #Spacing between aliens is one alien width and one alien height.
        #Make an alien.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        
        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 6 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            #Finished a row; reset x value, and increment y value.
            current_x = alien_width
            current_y += 2 * alien_height
    
    def _create_alien(self, x_position, y_position):
            #Create an alien and place it in the fleet.
            new_alien = Alien(self)
            new_alien.x = x_position
            new_alien.rect.x = x_position
            new_alien.rect.y = y_position
            self.aliens.add(new_alien)

    def _ship_hit(self):
        #Respond to the ship being hit by an alien.
        if self.stats.ships_left > 0:
            #Decrement ships_left, and update scoreboard
            #Decrement ship_left.
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            #Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()

            #Create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()
            #Pause
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        #Check if any aliens have reached the bottome of the screen.
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                #Treat this the same as if the ship got hit.
                self._ship_hit()
                break

if __name__ == '__main__':
    #Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()