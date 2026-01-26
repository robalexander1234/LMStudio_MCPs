# DF2 Circle Drawing Algorithm Implementation
# Based on the paper: Direct Form 2 (DF2) Circle Drawing Algorithm
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple

def df2_circle_drawing(radius: float, center_x: float = 0.0, center_y: float = 0.0, fixed_point: bool = False) -> None:
    """
    Draw a circle using the DF2 algorithm.
    
    Parameters:
        radius (float): Radius of the circle.
        center_x (float): X-coordinate of the circle's center.
        center_y (float): Y-coordinate of the circle's center.
        fixed_point (bool): If True, uses fixed-point arithmetic for stability.
    """
    # Calculate angular step
    omega = 1.0 / (1.5 * radius)
    
    # Fixed-point coefficients if needed
    if fixed_point:
        c = np.cos(omega)  # Filter coefficient
        s = -1.0 / omega   # Sine scale factor
    else:
        c = 2 * np.cos(omega)
        s = -1.0 / omega
    
    # Initial conditions
    w_prev_prev = radius * np.cos(0)  # w[n-2]
    w_prev = radius * np.cos(omega)     # w[n-1]
    
    # Number of steps for full circle
    N = int(np.ceil(2 * np.pi / omega))
    
    # Store pixels to plot later (for efficiency)
    pixels = []
    
    for i in range(N):
        x = round(w_prev)
        y = round((w_prev - w_prev_prev) * s)
        
        # Plot the pixel
        pixels.append((center_x + x, center_y + y))
        
        # Update w[n] for next iteration
        w_next = c * w_prev - w_prev_prev
        w_prev_prev, w_prev = w_prev, w_next
    
    return pixels

def plot_circle(pixels: list, title: str = "DF2 Circle Drawing Algorithm") -> None:
    """
    Plot the collected pixels as a circle.
    """
    if not pixels:
        print("No pixels to plot!")
        return
    
    # Extract coordinates
    x_coords, y_coords = zip(*pixels)
    
    plt.figure(figsize=(8, 6))
    plt.scatter(x_coords, y_coords, s=10, color='blue', alpha=0.7)
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True)
    plt.axis('equal')  # Equal aspect ratio
    plt.show()

# Example usage for different radii
radii = [10, 30, 50, 70, 90]
centers = [(0, 0)] * len(radii)  # All circles centered at origin

for radius, center in zip(radii, centers):
    print(f"\nDrawing circle with radius {radius}:")
    pixels = df2_circle_drawing(radius=radius, center_x=center[0], center_y=center[1])
    plot_circle(pixels=pixels, title=f'DF2 Circle (r={radius})')