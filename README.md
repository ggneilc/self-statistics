**Digital Fitness Twin**

# Abstract

until we have sensors implanted in our bodies, or near perfect readings from smart watched, manually data entry (or semi-passive entry) will be a requirement for creating the best dataset to train a model on your own personal metrics.

> Mission Statement
> 
> Enable robust tracking and prediction models for core health metrics. Additional focal point is making the data entry enjoyable, and aggregating/viewing/processing information as seemless as possible



> [!error] Post-Research:  Dataset Issue
> 
> The pre requisite of using machine learning is having a large, organized data source readily available. There is no dataset that tracks (calories eaten per day | bodyweight). The **only availble metric dataset** is on calories burned during a workout session from fitbit.  

Therefore, the primary responsibility of this application needs to be
1. The creation & management of a health metric dataset
2. The training and inference of the above



---
# Download

`git clone https://github.com/ggneilc/self-statistics.git`

`cd self-statistics/`

`python -m venv env`

`. ./env/bin/activate`

`pip install -r requirements.txt`

`. ./load_env dev`

`python manage.py migrate` (test to see if any changes to database has been made with most recent commit) 

You can now run the development server from `self-statistics/` with `python manage.py runserver`. 

Keep in mind the database file (`db.sqlite3`) is only tracked for the initial repository upload so that dummy data could exist. 

---
# Implementation

The implementation is going to be simple to ease a single developer flow: **Django** REST - HATEOS backend server that utilizes a simple **sqlite3** database and connects to a browser client written with vanilla html, css, and htmx as a javascript library.

Every related to the ML models will be a self contained python module `predictions` that is imported by the respective django app. `graphs` will import health metrics, `calcounter` imports food scanner, etc.  

## Model

The purpose of self statistics is to be able to run simulated tests on your own fitness metrics and see projected outcomes. The numerical model estimation could use time series forecasting, or a ML approach; utilize an autoregressive MLP to continually take in its estimate and provide another guess to show a 6-week training split result of either a diet or workout plan.

The following modeling schemes depict **the most simple possible** data vectors and prediction targets.

#### Diet Modeling

Given a daily caloric intake $x_{1}$, total volume lifted $x_{2}$, and current bodyweight $x_{3}$, predict tomorrow's bodyweight $y$. 

#### Strength Modeling

Given a daily caloric intake $x_{1}$, current bodyweight $x_{2}$, predict total volume lifted $y$. 

### Calorie needs modeling

Given a total volume lifted $x_{1}$, current bodyweight $x_{2}$, predict caloric intake $y$ 

## Data Aggregation and Training Targets

#### Eating

| Category               | Data Points                                                         | Why It Matters                                                                                 |
| ---------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Calories**           | Total daily calories                                                | Core for energy balance (deficit/surplus).                                                     |
| **Macronutrients**     | Protein (g), Carbs (g), Fat (g), Fiber (g)                          | Protein = muscle synthesis, carbs = fuel, fat = hormones, fiber = gut health.                  |
| **Micronutrients**     | Sodium, Potassium, Calcium, Magnesium, Iron, Vitamins D/C/B-complex | Key for recovery, performance, and health (optional but valuable if you’re optimizing deeply). |
| **Meal Timing**        | Timestamp of each meal/snack                                        | Can reveal patterns in energy levels, performance, sleep quality.                              |
| **Hydration**          | Liters per day                                                      | Affects training output and recovery.                                                          |
| **Subjective Metrics** | Hunger rating (1-10), satiety, mood                                 | Allows your model to learn about your personal response to food patterns.                      |

#### Weight Lifting

| Category                | Data Points                                              | Why It Matters                                  |
| ----------------------- | -------------------------------------------------------- | ----------------------------------------------- |
| **Workout Date & Time** | Timestamp                                                | Needed for recovery modeling & habit tracking.  |
| **Exercise Name**       | Squat, Bench Press, Deadlift, etc.                       | Key for per-lift performance curves.            |
| **Sets/Reps/Load**      | e.g., 3x8 @ 225 lbs                                      | Core training stimulus data.                    |
| **RPE/RIR**             | Subjective intensity (0–10) or reps in reserve           | Allows modeling of fatigue and effort.          |
| **Tempo & Rest**        | Optional, but good for advanced training modeling.       |                                                 |
| **Volume Load**         | (Sets × Reps × Weight) – can be calculated automatically | Useful for trend analysis.                      |
| **Body Weight**         | Daily or weekly                                          | Needed to normalize strength metrics.           |
| **Recovery Metrics**    | Sleep (h), soreness rating, HRV (if available)           | Helps predict readiness and avoid overtraining. |



## Client-Server  

We are implementing HTMX in order to have server side rendering and increase our SEO and reduce overall code size by simply passing around templates. 

The website is split into **3 core columns**, where each column has a **head, list, entry** sections:
1. Weights
2. Graphs
3. Meals

The Weights sections is clearly defined for tracking workouts: the head shows 'energy levels' (calories & water consumed), with the list showing a 'match history' of workouts, and the entry taking over the entire column to be filled out as you work out.

The Graphs section is a more typical 'home screen dashboard' column. The head shows your profile, current health score/streak information, and the selected date. The 'list' shows the current graph or information about the day. The 'Entry' section will be where you can select what kind of view you are interested in seeing statistics about (currently commented out)

The Meals section is functionally complete and the most straightforward: the head depicts total nutrients eaten, the entry is where new meals/template are added, and the list shows the meals eaten for that particular day. 

### Reactive HTMX, Robust Django


Each one of the columns is *self-contained in a django application*, with shared components being stored in `core`; such as the base webpage, everything related to a user, and `Day` model. 

The current HTMX standard practice being used across the website is that there is a single `selected_date` state for the current day being viewed, stored in a date picker in the `graph_head`, with a js script that appends the selected date to each request.

Each feature which relies on the current day, e.g. `meal list` will have a listener for the selected date with a simple `hx-trigger="load, change from:#hidden-date"`. This creates a centralized, reactive style. 


> [!NOTE] 'Reactive' HTMX
> 
> The only adverse side-effect is with `hx-swap-oob`: this is when one returned request can update multiple parts of the html; the user deletes a meal, which would update both the list and the totals. The `hx-swap-oob` attribute does not allow the piggy-packed template (i.e., `totals.html`) to be animated in directly $\to$ it needs to be caught with javascript and have its transition applied.



## Meals

'Meals' referred to all things *consumed* in a day; food, vitamins, water, alcohol, nicotine. 

*User flow:*

User sees a list of each thing consumed during the day, sorted by time, with the color of each list element corresponding to the type (generic for food, green for vitamins, blue for water, red for alcohol/nicotine/thc.) When hovered, shows small in-line information regarding most important breakdown; food: total cals/protein, water: oz drank, vitamins: largest contributor (i.e. if 'multivitamin', display largest vitamin present), bad substance: amt consumed.

expanded meals show information regarding its entered macros. A meal can be edited, where each value for each macro becomes an editible number and can be resubmitted.

Users sees a ghost button at the top similar to the workouts, due to the newest meal being added being appended to the top. 

#### User wants to add a new food:
$$
\begin{align}
\text{Presses + button}  & \to \text{list : food, water, vitamin} \\
 & \to \text{select 'food'} \\
 & \to \text{sees saved templates or 'new food'} \\
 & \to \text{selects new food} \\
 & \to \text{form :} \\
\text{main info } & \mid \text{Meal name }n\text{ cals }c \text{ protein }p  \\
\text{additional (optional)}  & \mid \text{fat }f\text{ carbs } b \text{ fiber } r \text{ sodium } s  \\
 & \text{submit / save template / back }
\end{align}
$$

The time and date for added food can be automatically computed from the selected global date and input time. If the user is going back to input past meals, the timing does not necessarily matter, however the edit screen can allow for corrections, but not change the date.



> [!fire] Cal AI / Barcode Scanner
> 
> Instead of utilizing the research project for creating the predictive health metric engine, we can utilize a trained CNN (or more advanced visual classifier) on the Food101 dataset to lay the grounds for food - image - tracking


#### User wants to add a supplement:
$$
\begin{align}
\text{Presses + button}  & \to \text{list : food, water, vitamin} \\
 & \to \text{select 'vitamin'} \\
 & \to \text{sees saved templates or 'new vitamin'} \\
 & \to \text{selects new vitamin} \\
 & \to \text{form :} \\
\text{main info } & \mid \text{name }n\text{ cals }c \text{ protein }p  \\
\text{additional (optional)}  & \mid \text{fat }f\text{ carbs } b \text{ fiber } r \text{ sodium } s  \\
 & \text{submit / save template / back }
\end{align}
$$


WIP

## Workouts

*User flow:*

User sees 'match history' of workouts, with current day's workout highlighted (already expanded) if done, otherwise the add button glows. Either way, the add button is outline at the top to act as a remindar.

Each workout when hovered display small inline stats about that workout; small circles that scale with number of lifts done, total volume lifted, \# of PRs. If a workout is expanded, it shows the date, each lift done that day in a horizonal list, along with the total volume lifted, optionally a note attached to the workout, and buttons to edit/delete the workout. 

Each lift displays; the $\text{sets } \times \text{ reps }\times \text{ weight}$, tempo, RIR, recovery time

#### When the user wants to start a new workout:
$$
\begin{align}
\text{Presses Add workout}  & \to \text{sees list of types} : \text{'Push', 'Pull', 'Legs', etc}  \\
 & \to \text{User can select workout type or add/delete/cancel} \\  
 & \to \text{Select 'Pull'} \\
 & \to\text{ Active workout expands, option to add lift, end workout, exit} \\
 & \to \text{ user goes back} : \text{active workout is highlighted to be resumed} \\
 & \to \text{workout is resumed, option to add lifts} \\
\dots \\
 & \to \text{ end workout} \\
 & \to \text{active workout screen is replaced with workout history} \\
 &  (\text{option to add summary screen})\\
 & \to \text{ just finished workout is automatically expanded}
\end{align}
$$

#### When the user wants to add a new lift:

Assuming user has default workout types "Push", "Pull", "Legs" where the bodyparts for each type consist of:
- Push : Chest, Shoulders, Triceps
- Pull : Traps, Lats, Biceps
- Legs: Hamstring, Quads, Glutes, Calves

$$
\begin{align}
\text{Presses Add lift}  & \to \text{list : body parts that correspond to workout type} \\
 & \to \text{presses 'chest'} \\
 & \to \text{list : dumbbell / machine / barbell} \\
 & \to \text{presses 'dumbbell'} \\
 & \to \text{form : } \\
 & \text{workout name} \\
\text{add sets individually} & \to \text{set 1 : reps } x \text{ weight} f \\ 
 & \text{tempo } t\text{ RIR }p  \text{ rest } s\\
 & \text{ghost button to add another set} \\
 & \text{button to finish lift}
\end{align}
$$

Grouping Workouts by dumbbell / machine / barbell allows for the background of each lift to correspond to a db/machine/bb photo. 




> [!fact] Lift Templates
> 
> When hovering over the workout history and inspecting a particular lift, 'turn lift into template' can be an option, and templates are inserted into the user flow after selecting the dumbbell/machine/barbell, and once the user has a template saved, instead of immediately returning a form, it returns a list of templates, with a ghost button to access the new lift form.


> [!fact] Supersets, Dropsets
> 
> Supersets can be included by allowing two active lifts to be open at once.
>
> Dropsets can be recognized as two individual sets with 0 rest time between.



> [!warning] Set Entries
> 
> RIR/RPE is abstract; come up with semi-definitive labels, can be recognized as a multinomial variable.
> Ideally, the flow of the set entry is that after your set, you enter the reps/weight/rir and then the recovery time field is a timer that immediately starts counting up until you start your next set with the '+' button. The issue is that this may break up the set into two submit forms, which complicates the UI and template returns.


## Users

##### Goals

The user is assigned daily goals that need to be met that align with the data aggregation chart to faciliate efficient model prediction and ease of thinking when it comes to having a good day (a good day = meets all goals $\to$ I am saying that the user needs goals to meet to have a prediction target and the website needs to make meeting that goal easy; use template calorie totals to create meal plan, use autoregressive model to estimate time needed to hit a certain bodyweight.)

Goals are not directly handled inside of each column display, and therefore need to be visible on the navbar so the user can always get the jist of what they need to do *today* by just looking at the navbar. 

Most important goals:
- Caloric / Protein
- Went to the gym

##### Profile Screen - currently vibe coded

When the user clicks on their username/profile, it should display a model overlay that depicts their settings. This user profile screen is where the user can customize their 'types' for various features on the website; workout types (push/pull/legs), lift types (machine/bodyweight/banded), or their binary task reminders (brush teeth/trash day/clean room).

## Graphs

##### Time Series Trends

Every variable $x$ should be toggable over any given time period $t$ where
- $\{ x \mid x \in \text{weight, volume, calories, protein, }\dots \}$
- $\{ t \mid t \in \text{daily, weekly, monthly, (hourly)} \}$

therefore I can simply check (average) weekly bodyweight, or see the fluctations with daily bodyweight (as well as any other number.) Hourly would show the 24h breakdown which would require hour and minute to be tracked on meals/workouts.

##### Autoregressive Model

User is presented with a slider for the following variables:
- Calories
- Bodyweight
- Volume

And they are able to forecast a 6 week trend of how an increase/decrease of their choosen variable would effect the others; the user can slide calories to -50 and forecast how 50 less calories a day will impact their expected bodyweight and workout volume.


#### Calendar Heatmap - currently vibe coded

This will be the default display loaded into the `graph_display__container` upon page load, as it depicts the best overall view of your selected timeframe. 

There will be different views depending on the timeframe:
- AMDAP - As Many Days As Possible $\to$ whats currently implemented, roughly a year
- 3 Month
- 1 Month
- 1 Week

1 week will be the shortest as a singular 'day view' is what happens when the user clicks a day on the calendar. 


---
# Future Ideas

1. break down total calorie goal $x$ into $n$ meals that consist of your saved templates 
	1. can add meal classification (breakfast/lunch/dinner) and create timed mealplan
2. barcode scanning for faster meal entry, ai calorie photo prediction
3. Smart watch integration for additional biometrics & sleep
4. Food camera ; manual 2 camera setup in kitchen similar to smart scale

---
# Todo
 - [ ] `hx-swap-oob` animations on meal add / delete 


---
