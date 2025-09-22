import pygame
import math

pygame.mixer.init()

def create_simple_sound(filename, frequency, duration):
    """Create a simple beep sound"""
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Create sound data
    sound_data = []
    for i in range(frames):
        time = float(i) / sample_rate
        amplitude = 0.3 * math.sin(frequency * 2 * math.pi * time)
        amplitude *= max(0, 1 - (i / frames))  # Fade out
        sound_data.append([int(amplitude * 32767), int(amplitude * 32767)])
    
    # Save as WAV
    import wave
    with wave.open(f'sounds/{filename}.wav', 'w') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for frame in sound_data:
            wav_file.writeframes(frame[0].to_bytes(2, 'little', signed=True))
            wav_file.writeframes(frame[1].to_bytes(2, 'little', signed=True))

# Create sound effects
sounds_to_create = [
    ('move', 300, 0.1),
    ('treasure', 800, 0.3),
    ('hurt', 150, 0.5),
    ('game_over', 100, 1.0),
    ('level_up', 1200, 0.8),
    ('background', 440, 4.0)
]

for name, freq, duration in sounds_to_create:
    create_simple_sound(name, freq, duration)
    print(f'Created {name}.wav')

print('All sound files created successfully!')
