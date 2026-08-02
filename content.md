# Navigation


## Main steps (timer_callback())

1.  waits until it has a map, pose, and goal.
2.  converts the robot and goal positions from metres into map grid cells.

3. runs A* path planning, allowing horizontal, vertical, and diagonal moves.

4. keeps clearance from obstacles by inflating them.
5. smooths the grid path to reduce zig-zag motion.

6. Every 0.2 seconds, it chooses a waypoint about 0.4 m ahead.

7. publishes a TargetVector toward that waypoint.
8. the goal is within 0.4 m, it sends zero speed and reports goal_succeeded.

## A Star 

[img/nav.png]

f(n)=g(n)+h(n)


1. Initialize A*: Initialize open list(priority queue) and Add the start cell, and initialize came_from, g_score, and closed list(set).
2.  Select the best cell: Remove the cell with the smallest estimated total cost (f(n)) from the open set.
3. Check the goal: If the selected cell is the goal, reconstruct and return the path using the stored parent cells.
4. Mark as explored: Skip the cell if already processed; otherwise, add it to the closed set.
5. Generate neighbors: Consider eight neighboring cells with cost (1) for straight movement and (\sqrt{2}) for diagonal movement while preventing corner-cutting.
6. Apply obstacle costs: Reject blocked or invalid cells and add a cost to inflated cells near obstacles.
7. Update better paths: If reaching a neighbor produces a lower cost, update its parent and scores, then add it to the open set.
8. Finish the search: Return the reconstructed path when the goal is reached, or report no_path if the open set becomes empty.

## Next Waypoint

planned path:

  A ───── B ───── C ───── D
               Robot

  The function does two main jobs:

* Find where the robot is on the rope
     It projects the robot onto every remaining path segment and selects the closest point:

  A ───── B ── P ── C ───── D
                 ↑
               Robot

  P represents the robot’s current progress along the path.

  
* Move 0.40 m forward along the rope
     Starting at P, it measures 40 cm along the path:

  A ───── B ── P ───── W ── C ───── D
                       ↑
                  next waypoint

  If the 40 cm crosses a corner, the function continues measuring on the next segment:

                    C ─── W
                    │
  A ───── B ── P ───┘

  

* path_progress prevents the selected position from jumping backward when the path passes close to itself. 
  
* If less than 40 cm of path remains, it returns the final goal point.