import pygame
import neat
import time
import os
import random

#Screen size
WIN_WIDTH = 500
WIN_HEIGHT = 800

#Color
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)      # Bird color
GREEN = (0, 255, 0)    # Pipe color
BLUE = (135, 206, 235) # Sky Background (Sky Blue)

pygame.font.init()

# BIRD
class Bird:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel = 0
        self.tick_count = 0
        self.height = self.y
        self.width = 20 
        self.rect = pygame.Rect(self.x, self.y, self.width, self.width)

    def jump(self):
        self.vel = -8.0
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2

        if d >= 16: d = 16 # Bird falling speed
        if d < 0: d -= 2

        self.y = self.y + d
        self.rect.y = int(self.y)

    def draw(self, win):
        pygame.draw.rect(win, RED, self.rect)

# PIPE
class Pipe:
    GAP = 100 # Gap of pipe
    VEL = 10 # Velocity of pipe
       

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_WIDTH = 70
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - 800
        self.bottom = self.height + self.GAP
        self.top_rect = pygame.Rect(self.x, self.top, self.PIPE_WIDTH, 800)
        self.bottom_rect = pygame.Rect(self.x, self.bottom, self.PIPE_WIDTH, 800)

    def move(self):
        self.x -= self.VEL
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, win):
        pygame.draw.rect(win, GREEN, self.top_rect)
        pygame.draw.rect(win, GREEN, self.bottom_rect)

    def collide(self, bird):
        if bird.rect.colliderect(self.top_rect) or bird.rect.colliderect(self.bottom_rect):
            return True
        return False

# Main draw
def draw_window(win, birds, pipes, score, gen=None):
    win.fill(BLUE)

    for pipe in pipes:
        pipe.draw(win)

    for bird in birds:
        bird.draw(win)

    # Score
    font = pygame.font.SysFont("comicsans", 30)
    text = font.render(f"Score: {score}", 1, WHITE)
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    # Gen Score
    if gen is not None:
        text_gen = font.render(f"Gen: {gen}", 1, WHITE)
        win.blit(text_gen, (10, 10))

    pygame.display.update()

#AI play
def eval_genomes(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        genome.fitness = 0
        ge.append(genome)

    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True
    
    while run and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_WIDTH:
                pipe_ind = 1

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and bird.x > pipe.x:
                    pipe.passed = True
                    add_pipe = True
            pipe.move()
            if pipe.x + pipe.PIPE_WIDTH < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.width >= 800 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        draw_window(win, birds, pipes, score, GEN)

# Player play
def play_game_human():
    bird = Bird(230, 350)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            # Space to Jump
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

        bird.move()

        # Pipe processing
        add_pipe = False
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):
                print(f"GAME OVER! Score: {score}")
                run = False # Die = pause game
            
            if not pipe.passed and bird.x > pipe.x:
                pipe.passed = True
                add_pipe = True
            
            pipe.move()
            if pipe.x + pipe.PIPE_WIDTH < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        # hit the ground or fly too high
        if bird.y + bird.width >= 800 or bird.y < 0:
            print(f"GAME OVER! Score: {score}")
            run = False

        draw_window(win, [bird], pipes, score) # no transmission Gen

    # If end game, wait a momment and return to menu
    time.sleep(1)

# Main menu
def main_menu():
    global GEN
    GEN = 0
    
    # Load config AI
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    run = True
    font = pygame.font.SysFont("comicsans", 40)
    title_font = pygame.font.SysFont("comicsans", 60)

    while run:
        win.fill(BLACK)
        
        title = title_font.render("FLAPPY BIRD AI", 1, RED)
        text1 = font.render("Press 1: Train AI", 1, WHITE)
        text2 = font.render("Press 2: Play Game", 1, WHITE)
        
        win.blit(title, (WIN_WIDTH/2 - title.get_width()/2, 100))
        win.blit(text1, (WIN_WIDTH/2 - text1.get_width()/2, 300))
        win.blit(text2, (WIN_WIDTH/2 - text2.get_width()/2, 400))
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # AI Mode
                    p = neat.Population(config)
                    p.add_reporter(neat.StdOutReporter(True))
                    p.add_reporter(neat.StatisticsReporter())
                    p.run(eval_genomes, 50)
                
                if event.key == pygame.K_2:
                    # Player Mode
                    play_game_human()

if __name__ == "__main__":

    main_menu()
