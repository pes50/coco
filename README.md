# Game

## Controls

|  | Player 1 | Player 2 |  
|-----------|:-----------:|:-----------:|  
| Movement | A, D | Mouse |  
| Jump | W | RMB |  
| Attack | E | LMB |  

## Level Editor

Don't like our levels? You can create your own!  
Edit "template.txt" and rename it to "level" + next unused number ("level13.txt")

### Editor legend

| Character | Result | Description |  
|:-----------:|:-----------:|:-----------:|  
| '_' | **Acid** | Has random tolerance |  
| '/' | **Acid** | Has no tolerance. Will always kill player |  
| '|' | **Laser** | Turns on and of periodically, every time with new random tolerance |  
| '#' | **Wall** | The thing player stands on and can't walk through |   
| '0' - '9' | **Teleport** | If player collides with teleport, he will be moved to random teleport with same number |   
| 'P' | **Pickup** | Place where pickup might appear if collected *(Every level must have at least 3)* |  
| 'S' | **Spawnpoint** | Place where players respawn *(Every level must have at least 2 and position[x][y-1] = 'X')* |  
| 'T' | **Spike** | Always kills player |  
| 'X' | **Nothing** | Better than whitespaces |