import pygame
import random
import sys
import array

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 450, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Google Dino: Day & Night")

DAY_BG, DAY_FG, DAY_CACTUS = (247, 247, 247), (83, 83, 83), (34, 177, 76)
NIGHT_BG, NIGHT_FG, NIGHT_CACTUS = (32, 33, 36), (241, 243, 244), (129, 201, 149)
RED = (237, 28, 36)

state, score, last_beep_score, game_speed, spawn_timer, next_spawn_time, color_progress, score_timer = 0, 0, 0, 6.0, 0, 100, 0.0, 0
font_large = pygame.font.SysFont("sans", 40, bold=True)
font_small = pygame.font.SysFont("sans", 24)
clock = pygame.time.Clock()

def generate_beep_sound():
    sample_rate = 44100
    freq1, freq2, duration = 988, 1318, 0.07
    samples = array.array('h')
    for i in range(int(sample_rate * duration)):
        t = float(i) / sample_rate
        samples.append(int(32767 * 0.3 * (1.0 - t/duration) * (1.0 if (t * freq1) % 1.0 < 0.5 else -1.0)))
    for _ in range(int(sample_rate * 0.02)): samples.append(0)
    for i in range(int(sample_rate * duration)):
        t = float(i) / sample_rate
        samples.append(int(32767 * 0.3 * (1.0 - t/duration) * (1.0 if (t * freq2) % 1.0 < 0.5 else -1.0)))
    return pygame.mixer.Sound(buffer=samples)

beep_sound = generate_beep_sound()

def blend_color(c1, c2, p):
    r = int(c1[0] + (c2[0] - c1[0]) * p)
    g = int(c1[1] + (c2[1] - c1[1]) * p)
    b = int(c1[2] + (c2[2] - c1[2]) * p)
    return (r, g, b)

def create_pixel_sprite(matrix, color_map, pixel_size=4):
    rows, cols = len(matrix), len(matrix[0])
    surf = pygame.Surface((cols * pixel_size, rows * pixel_size), pygame.SRCALPHA)
    for r in range(rows):
        for c in range(cols):
            char = matrix[r][c]
            if char in color_map: pygame.draw.rect(surf, color_map[char], (c * pixel_size, r * pixel_size, pixel_size, pixel_size))
    return surf

dino_body = ["000001111110", "000001101111", "000001111111", "000001110000", "011111111100", "111111111100", "111111111100", "111111111000", "011111110000"]
dino_legs1 = ["001100110000", "001100011000"]
dino_legs2 = ["000110110000", "001100001100"]
cactus_matrix = ["00011000", "00111100", "01111110", "11011011", "11011011", "01111110", "00011000", "00011000", "00011000", "00011000"]
cloud_matrix = ["0001111000", "0111111110", "1111111111", "0111111110"]

class Dino:
    def __init__(self):
        self.x, self.y, self.vy, self.gravity, self.jump_height, self.is_jumping, self.animation_counter, self.current_leg_frame = 50, 585, 0, 0.75, -15.5, False, 0, 1
    def jump(self):
        if not self.is_jumping: self.vy, self.is_jumping = self.jump_height, True
    def update(self):
        self.vy += self.gravity
        self.y += self.vy
        if self.y >= 585: self.y, self.vy, self.is_jumping = 585, 0, False
        if not self.is_jumping:
            self.animation_counter += 1
            if self.animation_counter >= 8:
                self.current_leg_frame = 2 if self.current_leg_frame == 1 else 1
                self.animation_counter = 0
        else: self.current_leg_frame = 1
    def draw(self, surface, current_fg):
        full_matrix = dino_body + (dino_legs1 if self.current_leg_frame == 1 else dino_legs2)
        surface.blit(create_pixel_sprite(full_matrix, {'1': current_fg}, pixel_size=5), (self.x, self.y))

class CactusGroup:
    def __init__(self, speed):
        self.x, self.y, self.speed, self.cacti = 450 + random.randint(50, 150), 610, speed, []
        for _ in range(random.randint(1, 3)):
            width, height = random.randint(24, 36), random.randint(50, 75)
            self.cacti.append({"rel_x": (self.cacti[-1]["rel_x"] + self.cacti[-1]["width"] + random.randint(6, 14)) if self.cacti else 0, "width": width, "height": height})
    def update(self, current_speed): self.x -= current_speed
    def is_out_of_screen(self): return (self.x + self.cacti[-1]["rel_x"] + self.cacti[-1]["width"]) < 0 if self.cacti else True
    def check_collision(self, dino_rect):
        for c in self.cacti:
            if dino_rect.colliderect(pygame.Rect(self.x + c["rel_x"], self.y - c["height"] + 40, c["width"], c["height"])): return True
        return False
    def draw(self, surface, current_cactus_color):
        sprite = create_pixel_sprite(cactus_matrix, {'1': current_cactus_color}, pixel_size=4)
        for c in self.cacti: surface.blit(pygame.transform.scale(sprite, (c["width"], c["height"])), (self.x + c["rel_x"], self.y - c["height"] + 40))

class Cloud:
    def __init__(self): self.x, self.y, self.speed, self.width = 450 + random.randint(10, 200), random.randint(100, 250), random.uniform(0.5, 1.2), random.randint(50, 80)
    def update(self): self.x -= self.speed
    def draw(self, surface, current_fg, opacity): surface.blit(pygame.transform.scale(create_pixel_sprite(cloud_matrix, {'1': (current_fg[0], current_fg[1], current_fg[2], opacity)}, pixel_size=6), (self.width, int(self.width * 0.4))), (self.x, self.y))

class Star:
    def __init__(self): self.x, self.y, self.size, self.alpha = random.randint(10, 440), random.randint(50, 300), random.randint(2, 4), 0.0
    def update(self, is_night): self.alpha = min(1.0, self.alpha + 0.02) if is_night else max(0.0, self.alpha - 0.02)
    def draw(self, surface, current_fg):
        if self.alpha > 0:
            star_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(star_surf, (current_fg[0], current_fg[1], current_fg[2], abs(int(255 * self.alpha * (0.4 + 0.6 * random.random())))), (0, 0, self.size, self.size))
            surface.blit(star_surf, (self.x, self.y))

def reset_game():
    global dino, cactus_groups, clouds, stars, score, last_beep_score, game_speed, spawn_timer, next_spawn_time, color_progress, score_timer
    dino, cactus_groups, clouds, stars, score, last_beep_score, game_speed, spawn_timer, next_spawn_time, color_progress, score_timer = Dino(), [], [Cloud(), Cloud(), Cloud()], [Star() for _ in range(25)], 0, 0, 6.0, 0, random.randint(70, 120), 0.0, 0

reset_game()
running = True
while running:
    clock.tick(60)
    is_night = (score // 500) % 2 == 1
    target_progress = 1.0 if is_night else 0.0
    color_progress = min(1.0, color_progress + 0.01) if color_progress < target_progress else max(0.0, color_progress - 0.01)
    current_bg, current_fg, current_cactus = blend_color(DAY_BG, NIGHT_BG, color_progress), blend_color(DAY_FG, NIGHT_FG, color_progress), blend_color(DAY_CACTUS, NIGHT_CACTUS, color_progress)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if state == 0 and 125 <= mx <= 325 and 400 <= my <= 460: reset_game(); state = 1
            elif state == 1: dino.jump()
            elif state == 2:
                if 50 <= mx <= 210 and 500 <= my <= 560: reset_game(); state = 1
                elif 240 <= mx <= 400 and 500 <= my <= 560: state = 0

    screen.fill(current_bg)
    if state == 0:
        t = font_large.render("GOOGLE DINO", True, DAY_FG); screen.blit(t, (225 - t.get_width() // 2, 200))
        pygame.draw.rect(screen, DAY_FG, (125, 400, 200, 60), 0, 12)
        bt = font_small.render("ИГРАТЬ", True, DAY_BG); screen.blit(bt, (225 - bt.get_width() // 2, 415))
    elif state == 1:
        for star in stars: star.update(is_night); star.draw(screen, current_fg)
        co = int(120 * (1.0 - color_progress))
        if random.random() < 0.005 and len(clouds) < 4 and not is_night: clouds.append(Cloud())
        for cl in clouds[:]:
            cl.update()
            if co > 0: cl.draw(screen, current_fg, co)
            if cl.x < -100: clouds.remove(cl)
        dino.update(); spawn_timer += 1
        if spawn_timer > next_spawn_time: cactus_groups.append(CactusGroup(game_speed)); spawn_timer, next_spawn_time = 0, random.randint(65, 115)
        game_speed += 0.0025; score_timer += 1
        if score_timer >= 5: score, score_timer = score + 1, 0
        if score > 0 and score % 100 == 0 and score != last_beep_score: beep_sound.play(); last_beep_score = score
        pygame.draw.line(screen, current_fg, (0, 650), (450, 650), 3)
        dr = pygame.Rect(dino.x, dino.y, 60, 70)
        for group in cactus_groups[:]:
            group.update(game_speed); group.draw(screen, current_cactus)
            if group.check_collision(dr): state = 2
            if group.is_out_of_screen(): cactus_groups.remove(group)
        dino.draw(screen, current_fg)
        st_txt = font_small.render(f"Счет: {score}", True, current_fg); screen.blit(st_txt, (20, 20))
    elif state == 2:
        gt = font_large.render("ИГРА ОКОНЧЕНА", True, RED); screen.blit(gt, (225 - gt.get_width() // 2, 250))
        rt = font_small.render(f"Ваш результат: {score}", True, current_fg); screen.blit(rt, (225 - rt.get_width() // 2, 320))
        pygame.draw.rect(screen, current_fg, (50, 500, 160, 60), 0, 12)
        ret = font_small.render("ЗАНОВО", True, current_bg); screen.blit(ret, (130 - ret.get_width() // 2, 515))
        pygame.draw.rect(screen, DAY_FG, (240, 500, 160, 60), 0, 12)
        et = font_small.render("В МЕНЮ", True, DAY_BG); screen.blit(et, (320 - et.get_width() // 2, 515))
    pygame.display.flip()
pygame.quit()
sys.exit()
