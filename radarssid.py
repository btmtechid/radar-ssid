import pygame
import math
import sys
import subprocess
import re
import random

# --- Fungsi scan WiFi ---
def scan_wifi_windows():
    try:
        result = subprocess.check_output(
            ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
            shell=True, encoding='utf-8')

        networks = []
        ssid = ''
        freq = '2.4 GHz'  # Default
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                match = re.match(r"SSID\s+\d+\s+:\s(.+)", line)
                if match:
                    ssid = match.group(1)
            elif "Radio type" in line:
                freq = "5 GHz" if "a" in line.lower() or "ac" in line.lower() or "ax" in line.lower() else "2.4 GHz"
            elif "Signal" in line:
                match = re.search(r"Signal\s*:\s*(\d+)%", line)
                if match and ssid:
                    signal_percent = int(match.group(1))
                    rssi = (signal_percent / 2) - 100
                    distance = rssi_to_distance(rssi)
                    angle = ssid_angle_map.get(ssid, random.uniform(0, 360))
                    ssid_angle_map[ssid] = angle
                    networks.append((ssid, rssi, angle, distance, freq))
        return networks

    except Exception as e:
        print(f"Scan gagal: {e}")
        return []

# Estimasi jarak dari RSSI
def rssi_to_distance(rssi):
    tx_power = -40
    n = 2.5
    distance = 10 ** ((tx_power - rssi) / (10 * n))
    return min(distance * 10, 250)

# --- Pygame Init ---
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar WiFi Real-Time + RSSI Terminal")

BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)

CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 250
angle = 90
speed = 0.5
font = pygame.font.SysFont(None, 20)

# Menyimpan sudut tetap untuk setiap SSID
ssid_angle_map = {}

# Filter tampilan SSID
filter_mode = "All"  # Pilihan: All, 2.4 GHz, 5 GHz

def draw_radar(targets, filter_mode):
    screen.fill(BLACK)

    for r in range(50, RADIUS + 1, 50):
        pygame.draw.circle(screen, DARK_GREEN, CENTER, r, 1)

    for i in range(0, 360, 30):
        rad = math.radians(i)
        x = CENTER[0] + RADIUS * math.cos(rad)
        y = CENTER[1] + RADIUS * math.sin(rad)
        pygame.draw.line(screen, DARK_GREEN, CENTER, (x, y), 1)

    rad_angle = math.radians(angle)
    x_end = CENTER[0] + RADIUS * math.cos(rad_angle)
    y_end = CENTER[1] + RADIUS * math.sin(rad_angle)
    pygame.draw.line(screen, GREEN, CENTER, (x_end, y_end), 2)

    for fade in range(1, 20):
        fade_angle = rad_angle - math.radians(fade)
        x_fade = CENTER[0] + RADIUS * math.cos(fade_angle)
        y_fade = CENTER[1] + RADIUS * math.sin(fade_angle)
        color_fade = (0, max(0, 255 - fade * 10), 0)
        pygame.draw.line(screen, color_fade, CENTER, (x_fade, y_fade), 1)

    for ssid, rssi, ang, dist, freq in targets:
        if filter_mode == "All" or freq == filter_mode:
            rad = math.radians(ang)
            x = CENTER[0] + dist * math.cos(rad)
            y = CENTER[1] + dist * math.sin(rad)
            pygame.draw.circle(screen, GREEN, (int(x), int(y)), 4)
            label = font.render(f"{ssid}", True, GREEN)
            #(f"{ssid} ({rssi} dBm)"
            screen.blit(label, (x + 5, y - 10))

    filter_label = font.render(f"Filter: {filter_mode}", True, GREEN)
    screen.blit(filter_label, (10, 10))

# --- Loop utama ---
running = True
clock = pygame.time.Clock()
targets = []
scan_interval = 5000  # 5 detik
last_scan_time = pygame.time.get_ticks()
targets = scan_wifi_windows()

def print_terminal_log(targets):
    print("\n====== WiFi Detected ======")
    for ssid, rssi, _, _, freq in targets:
        print(f"SSID: {ssid:25} | RSSI: {rssi:>4} dBm | {freq}")
    print("===========================\n")

print_terminal_log(targets)

while running:
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                filter_mode = "All"
            elif event.key == pygame.K_2:
                filter_mode = "2.4 GHz"
            elif event.key == pygame.K_3:
                filter_mode = "5 GHz"

    if now - last_scan_time > scan_interval:
        targets = scan_wifi_windows()
        print_terminal_log(targets)
        last_scan_time = now

    draw_radar(targets, filter_mode)
    angle = (angle + speed) % 360
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
