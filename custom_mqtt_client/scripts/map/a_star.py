import numpy as np
import heapq
import matplotlib.pyplot as plt


def astar(grid, start, goal):
    """A* pathfinding in a 2D grid."""
    rows, cols = grid.shape
    open_set = []
    heapq.heappush(open_set, (0, start))
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: np.linalg.norm(np.array(start) - np.array(goal))}
    
    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        
        neighbors = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and grid[neighbor] == 0:
                tentative_g_score = g_score[current] + np.linalg.norm(np.array(neighbor) - np.array(current))
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + np.linalg.norm(np.array(neighbor) - np.array(goal))
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None  # No path found

# Example Usage
grid = np.zeros((20, 20))  # 20x20 empty map
grid[10, 5:15] = 1  # Add an obstacle

start = (2, 2)
goal = (18, 18)
path = astar(grid, start, goal)

# Visualize
plt.imshow(grid.T, origin="lower", cmap="gray_r")
plt.plot(*zip(*path), marker="o", color="blue", markersize=3, linestyle="-")
plt.scatter(*start, color="green", marker="o", label="Start")
plt.scatter(*goal, color="red", marker="x", label="Goal")
plt.legend()
plt.show()
