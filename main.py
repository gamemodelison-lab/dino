import random
import array
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Canvas
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader
from kivy.uix.button import Button

# Матрицы графики
dino_body = ["000001111110", "000001101111", "000001111111", "000001110000", "011111111100", "111111111100", "111111111100", "111111111000", "011111110000"]
dino_legs1 = ["001100110000", "001100011000"]
dino_legs2 = ["000110110000", "001100001100"]
cactus_matrix = ["00011000", "00111100", "01111110", "11011011", "11011011", "01111110", "00011000", "00011000", "00011000", "00011000"]
cloud_matrix = ["0001111000", "0111111110", "1111111111", "0111111110"]

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.init_game)
        
    def init_game(self, *args):
        self.canvas.clear()
        self.bg_color = (0.97, 0.97, 0.97, 1)
        self.fg_color = (0.32, 0.32, 0.34, 1)
        self.cactus_color = (0.13, 0.69, 0.3, 1)
        
        self.state, self.score, self.last_beep, self.game_speed, self.spawn_timer = 1, 0, 0, 6, 0
        self.next_spawn = random.randint(60, 110)
        self.dino_y, self.dino_vy, self.is_jumping, self.leg_frame, self.anim_cnt = 150, 0, False, 1, 0
        
        self.clouds = [{"x": random.randint(100, 400), "y": random.randint(500, 700), "s": random.uniform(0.5, 1.2), "w": random.randint(50, 80)} for _ in range(3)]
        self.stars = [{"x": random.randint(10, 440), "y": random.randint(500, 750), "a": 0.0} for _ in range(15)]
        self.cacti = []
        
        self.score_label = Label(text="Счет: 0", font_size=20, color=self.fg_color, pos=(20, self.height - 60), size_hint=(None, None))
        self.add_widget(self.score_label)
        
        self.game_loop = Clock.schedule_interval(self.update, 1.0/60.0)

    def draw_pixel_matrix(self, matrix, start_x, start_y, size, color):
        Color(*color)
        rows = len(matrix)
        for r in range(rows):
            for c in range(len(matrix[r])):
                if matrix[r][c] == '1':
                    Rectangle(pos=(start_x + c * size, start_y + (rows - 1 - r) * size), size=(size, size))

    def on_touch_down(self, touch):
        if self.state == 1 and not self.is_jumping:
            self.dino_vy = 15
            self.is_jumping = True

    def update(self, dt):
        self.canvas.clear()
        
        # Смена дня и ночи каждые 500 очков
        is_night = (self.score // 500) % 2 == 1
        if is_night:
            self.bg_color = (0.12, 0.13, 0.14, 1)
            self.fg_color = (0.94, 0.95, 0.96, 1)
            self.cactus_color = (0.5, 0.78, 0.58, 1)
        else:
            self.bg_color = (0.97, 0.97, 0.97, 1)
            self.fg_color = (0.32, 0.32, 0.34, 1)
            self.cactus_color = (0.13, 0.69, 0.3, 1)
            
        Window.clearcolor = self.bg_color
        self.score_label.color = self.fg_color
        
        with self.canvas:
            # Отрисовка звезд ночью
            for s in self.stars:
                s["a"] = min(1.0, s["a"] + 0.02) if is_night else max(0.0, s["a"] - 0.02)
                if s["a"] > 0:
                    Color(self.fg_color[0], self.fg_color[1], self.fg_color[2], s["a"] * random.uniform(0.5, 1.0))
                    Rectangle(pos=(s["x"], s["y"]), size=(3, 3))
                    
            # Отрисовка облаков днем
            if not is_night:
                for cl in self.clouds:
                    cl["x"] -= cl["s"]
                    if cl["x"] < -100: cl["x"] = self.width + random.randint(10, 200)
                    self.draw_pixel_matrix(cloud_matrix, cl["x"], cl["y"], 4, (self.fg_color[0], self.fg_color[1], self.fg_color[2], 0.5))

            # Земля
            Color(*self.fg_color)
            Line(points=[0, 150, self.width, 150], width=2)
            
            # Динозаврик
            self.dino_vy -= 0.6
            self.dino_y += self.dino_vy
            if self.dino_y <= 150:
                self.dino_y, self.dino_vy, self.is_jumping = 150, 0, False
                
            if not self.is_jumping:
                self.anim_cnt += 1
                if self.anim_cnt >= 8:
                    self.leg_frame = 2 if self.leg_frame == 1 else 1
                    self.anim_cnt = 0
            else: self.leg_frame = 1
            
            full_matrix = dino_body + (dino_legs1 if self.leg_frame == 1 else dino_legs2)
            self.draw_pixel_matrix(full_matrix, 50, self.dino_y, 5, self.fg_color)
            
            # Кактусы
            self.spawn_timer += 1
            if self.spawn_timer > self.next_spawn:
                self.cacti.append({"x": self.width + 50, "h": random.randint(45, 70), "w": random.randint(24, 34)})
                self.spawn_timer, self.next_spawn = 0, random.randint(65, 115)
                
            self.game_speed += 0.001
            self.score += 1
            self.score_label.text = f"Счет: {self.score // 5}"
            
            for c in self.cacti[:]:
                c["x"] -= self.game_speed
                self.draw_pixel_matrix(cactus_matrix, c["x"], 150, 4, self.cactus_color)
                
                # Коллизия
                if c["x"] > 30 and c["x"] < 110 and self.dino_y < 150 + c["h"]:
                    self.state = 2
                    Clock.unschedule(self.game_loop)
                    self.parent.show_game_over(self.score // 5)
                if c["x"] < -50: self.cacti.remove(c)

class DinoApp(App):
    def build(self):
        self.main_layout = BoxLayout()
        self.game_widget = GameWidget()
        self.main_layout.add_widget(self.game_widget)
        return self.main_layout
    def show_game_over(self, final_score):
        self.main_layout.clear_widgets()
        go = BoxLayout(orientation='vertical', padding=50, spacing=20)
        go.add_widget(Label(text="ИГРА ОКОНЧЕНА", font_size=36, color=(0.9,0.1,0.1,1)))
        go.add_widget(Label(text=f"Результат: {final_score}", font_size=24, color=(0.3,0.3,0.3,1)))
        btn = Button(text="ЗАНОВО", background_color=(0.3,0.3,0.3,1))
        btn.bind(on_press=lambda x: self.restart())
        go.add_widget(btn)
        self.main_layout.add_widget(go)
    def restart(self):
        self.main_layout.clear_widgets()
        self.game_widget = GameWidget()
        self.main_layout.add_widget(self.game_widget)

if __name__ == "__main__":
    DinoApp().run()
