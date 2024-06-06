import pygame
import sys
import os
from pygame import mixer
import tkinter as tk
from tkinter import filedialog
import json
import song_generation
from utils import bpm_for_time
from threading import Thread

# Initialisation de Pygame
pygame.init()
mixer.init()

# Dimensions de la fenêtre
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Menu de démarrage - Jeu de rythme")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BUTTON_COLOR = (100, 200, 100)
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (30, 30, 30)

# Police d'écriture
title_font = pygame.font.Font(None, 100)
font = pygame.font.Font(None, 20)
font2 = pygame.font.SysFont('Arial.ttf', 30)

# Charger l'image de fond
background_image = pygame.image.load("assets/background.jpg")
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

# Liste des images a charge pour les notes
# Load images for notes
note_image_paths = [
    "assets/note.png",
    "assets/note.png",
    "assets/note.png",
    "assets/note.png"
]

# Dimensions des éléments
button_width = 220
button_height = 40

dropdown_button_width = 400
dropdown_button_height = 40

selectsong_button_width = 400
selectsong_button_height = 40

# Calcul des positions centrées
title_y = 20

button_x = (screen_width - button_width) // 2
button_y = 350

selectsong_button_x = (screen_width - dropdown_button_width) // 2
selectsong_button_y = 270

dropdown_button_x = (screen_width - dropdown_button_width) // 2
dropdown_button_y = 430

# Bouton de validation
button_box = pygame.Rect(button_x, button_y, button_width, button_height)
button_text = "Valider et jouer"

# Bouton du menu déroulant d'édition
dropdown_button_box = pygame.Rect(dropdown_button_x, dropdown_button_y, dropdown_button_width, dropdown_button_height)
dropdown_button_text = "Ajouter une musique au Jeu"

# Bouton du menu déroulant de sélection
selectsong_button_box = pygame.Rect(selectsong_button_x, selectsong_button_y, dropdown_button_width, dropdown_button_height)
selectsong_button_text = "Bibliothèque de musique"

# Function to draw text on screen
def draw_text(surface, text, rect, font, color=BLACK):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# LOADING SONG Function

def load(map):
    mixer.music.load(map+".mp3")

    with open(map+'.txt', 'r') as file:
        lines = file.readlines()
    
    start_time = None
    bpms = []
    beatmap = []
    beats_in_measure = []

    # Parse START_TIME
    index = 0
    while index < len(lines) and lines[index].strip() != "START_TIME:":
        index += 1
    index += 1  # Move to the value line
    if index < len(lines):
        start_time = int(lines[index].strip())
    
    # Parse BPMS
    index += 1  # Move past START_TIME value line
    while index < len(lines) and lines[index].strip() != "BPMS:":
        index += 1
    index += 1  # Move to the first BPM line
    while index < len(lines) and lines[index].strip() and lines[index].strip() != "NOTES:":
        line = lines[index].strip().rstrip(',')
        time, bpm = line.split(':')
        bpms.append([int(bpm), int(time)])
        index += 1
    
    # Parse NOTES
    index += 1  # Move past the BPMS section header
    while index < len(lines):
        stripped_line = lines[index].strip()
        if stripped_line:
            if "," in stripped_line:
                if beats_in_measure:
                    beatmap.append(beats_in_measure)
                    beats_in_measure = []
            else:
                beat = [int(block) for block in stripped_line]
                beats_in_measure.append(beat)
        index += 1
    
    if beats_in_measure:
        beatmap.append(beats_in_measure)
    
    #print(start_time)
    #print(bpms)
    #print(beatmap)
    #print(len(beatmap))
    bpm = bpm_for_time(bpms, start_time)
    measure_time = int(240000 / bpm)
    #print(f"measure_time: {measure_time}")
    current_time = start_time

    res = []
    for beats_per_mesure in beatmap:
        #print(f"measure_time: {measure_time}")
        for i in range(len(beats_per_mesure)):
            # Calculate the time for the current beat by adding the time for the previous beat
            beats_per_mesure[i] = (beats_per_mesure[i], (current_time + ((measure_time // (len(beats_per_mesure))) * (i))))
            # Update the previous time for the next iteration
        current_time += measure_time
        #print(current_time)
        bpm = bpm_for_time(bpms, current_time)
        #print(f"for bpm: {bpm}")
        measure_time = int(240000 / bpm)
        res.append(beats_per_mesure)

    # print(res)
    # [[([1, 0, 0, 0], 250.0), ([0, 0, 0, 0], 500.0), ([0, 0, 0, 0], 750.0), ([0, 0, 0, 0], 1000.0)], [([0, 1, 0, 0], 1333.3333333333333), ([0, 0, 0, 1], 1666.6666666666665), ([1, 0, 0, 0], 1999.9999999999998)], [([0, 0, 0, 0], 2250.0), ([1, 0, 0, 0], 2500.0), ([0, 0, 0, 0], 2750.0), ([0, 0, 0, 0], 3000.0)]]
    notes = []
    for beats in res:
        for beat, time in beats:
            for key_index in range(len(beat)):
                if beat[key_index] == 1:
                    #notes.append((pygame.Rect(keys[key_index].rect.centerx - 25,0,50,25), time))
                    notes.append((Note(key_index), time))
    
    return notes

song_path = 0

# custom thread
# credit goes to : https://superfastpython.com/thread-return-values/
class CustomThread(Thread):
    # constructor
    def __init__(self):
        # execute the base constructor
        Thread.__init__(self)
        # set a default value
        self.value = None
 
    # function executed in a new thread
    def run(self):
        # store data in an instance variable
        self.value = song_generation.generate_chart(song_path)

def run_loading_screen():

    clock = pygame.time.Clock()

    # Load background image
    background_image = pygame.image.load("assets/background.jpg")
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

    # Text font
    font = pygame.font.SysFont(None, 36)

    # Variables for loading bar
    bar_width = 600
    bar_height = 50
    x_bar = (screen_width - bar_width) // 2
    y_bar = (screen_height - bar_height) // 2
    fill_width = 0

    # Progress bar update interval (in milliseconds)
    update_interval = 2000  # 20 seconds

    # Current step status
    current_step = 0

    # Step texts
    step_texts = [
        "Loading audio file...",
        "Filtering audio...",
        "Detecting onsets...",
        "Finding tempo...",
        "Calculating RMS...",
        "Analyzing musical segments..."
    ]

    # Start the process
    global song_path
    song_path = "Music+Beatmaps/sink.mp3" 
    custom_thread = CustomThread()

    # Start the song generation
    # Create and start the thread
    custom_thread.start()

    # Time of the last progress update
    last_update_time = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Check if it's time to update the progress
        current_time = pygame.time.get_ticks()
        if current_time - last_update_time >= update_interval:
            # Update current step
            current_step += 1
            # Reset last update time
            last_update_time = current_time
        # Update loading bar
        fill_width = min(bar_width * (current_step / 6), fill_width + 1)
        # Display loading screen
        screen.blit(background_image, (0, 0))
        pygame.draw.rect(screen, WHITE, (x_bar, y_bar, bar_width, bar_height))
        pygame.draw.rect(screen, GRAY, (x_bar, y_bar, fill_width, bar_height))
        # Display current step text
        if current_step < len(step_texts):
            current_step_text = step_texts[current_step]
            text_surface = font.render(current_step_text, True, pygame.Color('white'))
            screen.blit(text_surface, (x_bar, y_bar - 40))
        else:
            running = False
        
        pygame.display.flip()
        clock.tick(30)
        
        

    custom_thread.join()
    value = custom_thread.value  # Ensure the task completes

# Systeme de recuperer la bibliotheque de musique
song_list_file_name = 'config.json'

def save_song_list(song_list):
    existing_songs = load_song_list()
    combined_songs = list(set(existing_songs + song_list))  # Combine and remove duplicates
    with open(song_list_file_name, 'w') as config_file:
        json.dump(combined_songs, config_file)

def load_song_list():
    if os.path.exists(song_list_file_name):
        with open(song_list_file_name, 'r') as song_list_file:
            return json.load(song_list_file)
    return []

def select_file_for_editor(song_list):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
    if file_path and file_path not in song_list:
        song_list.append(file_path)
        save_song_list(song_list)
        return file_path
    return None

# Initial list of MP3 files
mp3_files = load_song_list()

menu = {
    'selectsong_button_text': selectsong_button_text
}

# Class for managing the music library
class MusicLibrary:
    def __init__(self) -> None:
        self.music_chosen = self.run()

    def run(self):
        file_list = load_song_list()
        file_rects = []
        selected_file = None
        while not selected_file:
            # Event handling inside the main loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for file_rect, file in file_rects:  # Iterate over file rects and corresponding files
                        if file_rect.collidepoint(event.pos):
                            selected_file = file
                            break
                    if return_button.collidepoint(event.pos):
                        selected_file = "Select a music file"

            screen.fill(BG_COLOR)
            draw_text(screen, "Select a music file", pygame.Rect(0, 50, screen_width, 50), font, WHITE)
            y_offset = 150
            return_button = pygame.Rect(50, 50, 200, 50)
            draw_text(screen, "return", return_button, font, TEXT_COLOR)
            for idx, file in enumerate(file_list):
                file_rect = pygame.Rect(50, y_offset + idx * 50, screen_width - 100, 50)
                pygame.draw.rect(screen, GRAY, file_rect)
                draw_text(screen, file, file_rect, font, BLACK)
                file_rects.append((file_rect, file))

            pygame.display.flip()
        return selected_file

class Gameplay():
    def __init__(self):
        #self.map = selectsong_button_text[:-4]
        self.beatmap = load("Music+Beatmaps/sink")
        self.note_speed = 1
        self.BPM = 0
        self.notes = []
        self.note_index = 0
        self.run()
        
    def run(self):
        # Initialize a dictionary to store key press times
        key_press_times = {key.key: [] for key in keys}
        # Reset game variables
        start_time = pygame.time.get_ticks()
        current_time = start_time
        score = 0
        music_started = False
        clock = pygame.time.Clock()
        speed = 500

        running = True
        while running:
            screen.fill((255, 255, 255))

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in key_press_times:
                        key_press_times[event.key].append(current_time - start_time - 1000)
                        print(f"Key {event.key} pressed at {current_time - start_time - 1000}")

            # Update the current time
            dt = clock.tick(60)  # Get the time passed since the last frame in milliseconds
            current_time += dt  # Update current time

            # Check if the music hasn't started yet and the elapsed time is greater than or equal to 1000 milliseconds (1 second)
            if not music_started and current_time - start_time >= 1000 + 69 - 175:
                # Start playing the music
                pygame.mixer.music.play()
                music_started = True

            # Check key presses
            k = pygame.key.get_pressed()
            for key in keys:
                if k[key.key]:
                    pygame.draw.rect(screen, key.coloridle, key.rect)
                    key.handled = False
                else:
                    pygame.draw.rect(screen, key.coloractive, key.rect)
                    key.handled = True

            # Spawn and move notes
            for note, time_frame in self.beatmap[:]:
                if current_time - start_time >= time_frame:
                    if not note.dissolving:
                        note.update((speed / 1000) * dt)  # Move the note down
                    else:
                        note.dissolve()
                        if note.alpha == 0:
                            self.beatmap.remove((note, time_frame))
    
                    note.draw(screen)
    
                # Check if the note should be hit based on the key press times
                if not note.dissolving:
                    for key in keys:
                        if note.key_index == keys.index(key):
                            texte_score_time = 0
                            for press_time in key_press_times[key.key]:
                                if abs(press_time - time_frame) < 30:  # SCORING SYSTEM
                                    note.dissolving = True  # Start the dissolve effect
                                    key_press_times[key.key].remove(press_time)  # Remove the handled key press time
                                    score += 2  # Increment the score when a note is hit
                                    texte_score_time = current_time
                                    #print(f'1 {texte_score_time}')

                                    # Créer une surface contenant le texte
                                    texte = "Perfect"
                                    image_texte = font2.render(texte, True, GRAY)

                                    # Obtenir le rectangle de l'image du texte pour le positionnement
                                    rect_texte = image_texte.get_rect()

                                    # Centrer le texte au milieu de la fenêtre
                                    rect_texte.center = (400, 300)
                                    screen.blit(image_texte, rect_texte) 

                                    '''if abs(texte_score_time-current_time)>1000:
                                        print(f'2 {texte_score_time-current_time}')
                                        print(current_time)

                                        screen.blit(" ", rect_texte) 
                                    '''

                                elif abs(press_time - time_frame) < 50:  # SCORING SYSTEM
                                    note.dissolving = True  # Start the dissolve effect
                                    key_press_times[key.key].remove(press_time)  # Remove the handled key press time
                                    score += 1  # Increment the score when a note is hit
                                    texte_score_time = current_time
                                    #print(f'1 {texte_score_time}')
                                    # Créer une surface contenant le texte
                                    texte = "Good"
                                    image_texte = font2.render(texte, True, GRAY)

                                    # Obtenir le rectangle de l'image du texte pour le positionnement
                                    rect_texte = image_texte.get_rect()

                                    # Centrer le texte au milieu de la fenêtre
                                    rect_texte.center = (400, 300)
                                    screen.blit(image_texte, rect_texte) 

                                    '''if abs(texte_score_time-current_time)>1000:
                                        print(f'2 {texte_score_time-current_time}')
                                        print(current_time)

                                        screen.blit(" ", rect_texte)    
                                    '''

            # Display the score on the screen
            score_text = font.render(f"Score: {score}", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
    
            # Update the display
            pygame.display.update()
                
            if not running:
                break


class Note():
    def __init__(self, key_index):
        self.key_index = key_index
        self.x = keys[key_index].rect.centerx - 45
        self.y = 0
        self.rect = pygame.Rect(self.x, self.y, 90, 20)
        self.image = pygame.image.load(note_image_paths[key_index]).convert_alpha()  # Assign the image based on key index
        self.alpha = 255  # Initial alpha value
        self.dissolving = False
    
    def update(self, speed):
        self.y += speed
        self.rect.y = self.y

    def dissolve(self):
        if self.alpha > 0:
            self.alpha -= 20  # Adjust the decrement to control dissolve speed
            if self.alpha < 0:
                self.alpha = 0
            self.image.set_alpha(self.alpha)

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

class Key():
    def __init__(self,x,y,coloridle,coloractive,key):
        self.x = x
        self.y = y
        self.coloridle = coloridle
        self.coloractive = coloractive
        self.key = key
        self.rect = pygame.Rect(self.x,self.y,90,40)
        self.handled = False

# initialising keys
keys = [
    Key(100,500,(255,0,0),(220,0,0),pygame.K_z),
    Key(200,500,(0,255,0),(0,220,0),pygame.K_x),
    Key(300,500,(0,0,255),(0,0,220),pygame.K_m),
    Key(400,500,(255,255,0),(220,220,0),pygame.K_COMMA),
]

def main():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if button_box.collidepoint(mouse_pos):
                    if menu['selectsong_button_text'] != 'Select Song':  # Update this condition as needed
                        song_path = menu['selectsong_button_text']
                        run_loading_screen()
                        Gameplay()
                elif dropdown_button_box.collidepoint(mouse_pos):
                    selected_file = select_file_for_editor(mp3_files)
                    if selected_file and selected_file not in mp3_files:
                        mp3_files.append(selected_file)
                elif selectsong_button_box.collidepoint(mouse_pos):
                    music_library = MusicLibrary()
                    selected_file = music_library.music_chosen
                    if selected_file:
                        menu['selectsong_button_text'] = selected_file

        screen.blit(background_image, (0, 0))

        # Display title and buttons
        title_text = title_font.render("SolarSound", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(screen_width // 2, title_y))
        screen.blit(title_text, title_rect)

        pygame.draw.rect(screen, BUTTON_COLOR, button_box)
        draw_text(screen, button_text, button_box, font, TEXT_COLOR)

        pygame.draw.rect(screen, GRAY, dropdown_button_box)
        draw_text(screen, dropdown_button_text, dropdown_button_box, font, TEXT_COLOR)
        
        pygame.draw.rect(screen, GRAY, selectsong_button_box)
        draw_text(screen, menu['selectsong_button_text'], selectsong_button_box, font, TEXT_COLOR)

        pygame.display.update()

if __name__ == "__main__":
    # Run the main function
    main()