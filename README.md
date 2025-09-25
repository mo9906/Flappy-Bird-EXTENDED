# Flappy Bird: **Extended Edition**

This is an extended, feature-rich clone of the classic Flappy Bird game built in **Python** with the **PyQt5** framework for graphics and the dedicated **`pygame.mixer`** library for sound management. The project aims to enhance the core gameplay with modern "Game Feel" adjustments, sophisticated visual effects, and a dynamic, high-impact random event system that radically alters gameplay on the fly. The architectural choice to combine **PyQt5** for the core application, window, and robust UI management with **`pygame.mixer`** for low-latency sound effect playback and music looping allows for an interface that is both responsive and visually appealing, moving beyond the capabilities of simpler game libraries.

## 🚀 Project Overview

The game introduces challenging new modes and physics-altering random events that ensure a constantly challenging and engaging experience. This dynamic system prevents the monotonous repetition often found in endless runners, turning each play session into a unique gauntlet that tests both reflexes and adaptation skills. High scores are saved persistently and loaded locally via JSON, ensuring player progress is tracked across sessions. Furthermore, the visual design features a smooth Day/Night cycle and complex multilayered parallax effects that contribute significantly to the game's polished look and feel. The overall design philosophy centers on injecting unpredictable chaos into a simple, precise gameplay loop.
[![Flappy Bird: EXTENDED](https://img.youtube.com/vi/XWMauWxiyX4/maxresdefault.jpg)](https://www.youtube.com/watch?v=XWMauWxiyX4)
---

## ✨ Key Features & Game Feel Enhancements

### 1. Dynamic Game Modes

| Mode | Description | Mechanic |
| :--- | :--- | :--- |
| **Adventure Mode** | The classic experience. Players tap/flap to fly through pipes. | Player controls bird's vertical movement. |
| **Pipe Control Mode** | A challenging inversion. The **bird moves randomly** up and down on it's own, and the player **controls the pipes' vertical position** with the mouse to guide the bird through the gap. | Player controls pipes' vertical movement (using the mouse cursor). |

### 2. Random Event System (Dynamic Gameplay)

Gameplay is interrupted by spontaneous, time-limited events (lasting **12 to 22 seconds**), which alter physics, visuals, and scoring.

* **Moon Gravity Event**
    * **Physics:** Gravity is drastically reduced (`0.07`), and lift is weaker (`-3.0`), resulting in **slower descent** and **'floaty' jumps**. Physics values smoothly transition in and out using an easing factor (`0.005`) for a fluid effect.
    * **Visual Feel:** The bird's rotation randomly eases towards a new angle using an easing factor (`0.02`), creating an **uncontrollable, wobbly drift** effect typical of low gravity.
    * **Level Design:** Pipe gaps are widened (`120` pixels) to compensate for the erratic movement.
* **Cloudy Sky Event**
    * **Atmosphere:** A detailed, multilayered **parallax cloud system** is generated.
    * **Visual Feel:** **Background clouds** use a **bottom-to-up easing animation** (`y_ease`) to appear on screen. **Foreground clouds** use a **rising alpha animation** (`alpha_ease`) to fade in from zero to half opacity.
    * **Ground Darkening:** A semi-transparent black overlay is drawn over the ground area (`GROUND_DARKENING_OPACITY = 0.35`) to create a darker, moodier atmosphere.
* **Size Changer Event:** The bird is scaled up by **1.5x**, and the pipe gap is proportionally increased for a challenge that requires more precise timing with a larger hitbox.
* **Double Score Event:** All points earned during the event are multiplied by **2**.

### 3. Advanced Obstacles & Scoring

* **Moving Pipes:** Pipes have a **50% chance** (`MOVING_PIPE_CHANCE = 0.5`) to spawn with a **vertical oscillating motion** (sine wave) with an amplitude of 80 pixels. A second moving pipe may also spawn with a **50% chance** (`DOUBLE_MOVING_PIPE_CHANCE = 0.5`).
* **Special Pipes (Red Pipes):** Pipes have a **20% chance** (`SPECIAL_PIPE_CHANCE = 0.2`) to spawn as a special pipe. Passing a Special Pipe rewards **5 points** instead of the standard 1 point.
* **Persistent Leaderboard:** The **Top 5** high scores are saved to a local JSON file (`data/leaderboard.json`).

### 4. Visual & Technical Polish

* **Day/Night Cycle:** The background smoothly transitions between Day and Night textures every **12 seconds** using a **12-second crossfade** (`FADE_DURATION = 12.0`).
* **Parallax Scrolling:** The main background scrolls horizontally at a slower speed (`0.5`) than the pipes, maintaining a consistent illusion of depth (`BACKGROUND_SCROLL_SPEED = 0.5`).

---

## 🕹️ Controls

| Action | Control (Key) | Game Mode |
| :--- | :--- | :--- |
| **Flap** | **Spacebar** / **Up Arrow** | Adventure Mode |
| **Control Pipes** | **Mouse Move** | Pipe Control Mode |
| **Pause/Unpause** | **P** | All Modes |
| **Toggle Debug** | **B** | All Modes |
| **Change Skin** | **S** (Main Menu) | Main Menu |
| **Change Mode** | **C** (Main Menu) | Main Menu |

---

## 💻 Installation and Setup

This project is written in Python and requires the **PyQt5** and **Pygame** libraries.

#### **1. Prerequisites**

Ensure you have **Python 3.6 or newer** installed on your system.

#### **2. Install Dependencies**

Open your terminal or command prompt and use `pip` to install the required libraries:

```pip install PyQt5 pygame```

#### **3. Running the Game**

Once the dependencies are installed, you can launch the game directly by executing the main script from your terminal:

```python main.py```
