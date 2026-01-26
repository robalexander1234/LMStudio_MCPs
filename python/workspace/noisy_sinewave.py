# Generate and plot a noisy sine wave
import numpy as np
import matplotlib.pyplot as plt

# Parameters
frequency = 5  # Hz
duration = 2   # seconds
sample_rate = 1000  # Hz
noise_stddev = 0.1  # Standard deviation for Gaussian noise

# Generate time array
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Create sine wave signal
signal = np.sin(2 * np.pi * frequency * t)

# Add Gaussian noise
noise = np.random.normal(0, noise_stddev, len(t))
noisy_signal = signal + noise

# Plot the signals
plt.figure(figsize=(10, 6))

# Plot the clean sine wave (optional)
plt.plot(t, signal, label='Clean Sine Wave', alpha=0.7)

# Plot the noisy signal
plt.plot(t, noisy_signal, label='Noisy Signal', color='red')

# Add labels and legend
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title(f'Sine Wave (5 Hz) with Gaussian Noise')
plt.legend()
plt.grid(True)
plt.show()