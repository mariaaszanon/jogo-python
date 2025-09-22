# Simple colored rectangles for game sprites
# These will be created as PNG files by the game engine

# Hero sprites (blue character with animation frames)
hero1 = Surface((32, 32))
hero1.fill((100, 150, 255))

hero2 = Surface((32, 32))
hero2.fill((120, 170, 255))

hero3 = Surface((32, 32))
hero3.fill((80, 130, 255))

# Enemy sprites (red characters with animation frames)
enemy1 = Surface((32, 32))
enemy1.fill((255, 100, 100))

enemy2 = Surface((32, 32))
enemy2.fill((255, 120, 120))

enemy3 = Surface((32, 32))
enemy3.fill((255, 80, 80))

# Treasure sprite (golden)
treasure = Surface((24, 24))
treasure.fill((255, 215, 0))
