from core.models import RDA_LOOKUP

NUTRIENT_MAP = {
    # Macros
    "Energy":        "208",   # calories
    "Protein":       "203",
    "Fat":           "204",
    "Carbohydrates": "205",
    "Sugar":         "269",
    "Fiber":         "291",
    "Cholesterol":   "601",
    # Minerals
    "Calcium":       "301",
    "Iron":          "303",
    "Magnesium":     "304",
    "Potassium":     "306",
    "Sodium":        "307",
    "Zinc":          "309",
    # Vitamins (A-E Complex)
    "Vitamin A":     "320",
    "Vitamin B-6":   "415",
    "Vitamin B-12":  "418",
    "Vitamin C":     "401",
    "Vitamin D":     "328",
    "Vitamin E":     "323",
    # Branded food alternate vitamin IDs (IU instead of µg)
    "Vitamin A (IU)": "318",
    "Vitamin D (IU)": "324",
    # Alcohol: 221
    # Caffiene: 262
}
MACRO = ["208", "203", "204", "205", "269", "291", "601"]
MINERAL = ["301", "303", "304", "306", "307", "309"]
VITAMIN = ["320", "415", "418", "401", "328", "323"]

# Branded foods report some vitamins in IU with different nutrient IDs.
# Map branded IDs to their standard IDs and provide conversion to µg.
BRANDED_VITAMIN_FALLBACKS = {
    "318": {"standard_id": "320", "convert": lambda iu: iu * 0.3},    # Vitamin A: IU -> µg RAE
    "324": {"standard_id": "328", "convert": lambda iu: iu * 0.025},  # Vitamin D: IU -> µg
}

def food_fingerprint(user, pantry_item):
    gender = user.profile.gender  # 'M' or 'F'
    age = user.profile.age  # integer
    gender_str = 'Male' if gender == 'M' else 'Female'
    if age < 19:
        goal_type = 'Young ' + gender_str
    else:
        goal_type = 'Adult ' + gender_str
    goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        goals[mineral] = values[goal_type]
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        goals[vitamin] = values[goal_type]
 
    def get_ratio(value, goal):
        if not goal or goal == 0: return 0
        return min(float(value) / float(goal), 1.0) 

    if pantry_item.unit.name == "grams":
        serving = 100
    else:
        serving = float(pantry_item.unit.gram_weight)
    data = pantry_item.food.get_nutrition_consumed(serving)
    pantry_item.nutrients = data
    pantry_item.badges = pantry_item.food.get_badges()
    macros = [
        {"name": "Protein", "value": round(data['protein'])},
        {"name": "Fat",     "value": round(data['fat'])},
        {"name": "Carbs",   "value": round(data['carb']),
        "sugar": round(data['sugar']),
        "fiber": round(data['fiber'])},
    ]
    minerals = [
        {"name": "Na",     "ratio": get_ratio(data['sodium'],       goals['sodium']), "value": round(data['sodium'])},
        {"name": "K",  "ratio": get_ratio(data['potassium'],    goals['potassium']), "value": round(data['potassium'])},
        {"name": "Ca",    "ratio": get_ratio(data['calcium'],      goals['calcium']), "value": round(data['calcium'])},
        {"name": "Mg",  "ratio": get_ratio(data['magnesium'],    goals['magnesium']), "value": round(data['magnesium'])},
        {"name": "Zn",       "ratio": get_ratio(data['zinc'],         goals['zinc']), "value": round(data['zinc'])},
        {"name": "Fe",       "ratio": get_ratio(data['iron'],         goals['iron']), "value": round(data['iron'])},
    ]
    vitamins = [
        {"name": "A",   "ratio": get_ratio(data['vitamin_a'],   goals['A']), "value": round(data['vitamin_a'], 1)},
        {"name": "B6",  "ratio": get_ratio(data['vitamin_b6'],  goals['B6']), "value": round(data['vitamin_b6'], 1)},
        {"name": "B12", "ratio": get_ratio(data['vitamin_b12'], goals['B12']), "value": round(data['vitamin_b12'], 1)},
        {"name": "C",   "ratio": get_ratio(data['vitamin_c'],   goals['C']), "value": round(data['vitamin_c'], 1)},
        {"name": "D",   "ratio": get_ratio(data['vitamin_d'],   goals['D']), "value": round(data['vitamin_d'], 1)},
        {"name": "E",   "ratio": get_ratio(data['vitamin_e'],   goals['E']), "value": round(data['vitamin_e'], 1)},
    ]
    return macros, minerals, vitamins

def meal_fingerprint(user, data):
    gender = user.profile.gender  # 'M' or 'F'
    age = user.profile.age  # integer
    gender_str = 'Male' if gender == 'M' else 'Female'
    if age < 19:
        goal_type = 'Young ' + gender_str
    else:
        goal_type = 'Adult ' + gender_str
    goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        goals[mineral] = values[goal_type]
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        goals[vitamin] = values[goal_type]
 
    def get_ratio(value, goal):
        if not goal or goal == 0: return 0
        return min(float(value) / float(goal), 1.0) 

    total_macros = {
        'protein': 0,
        'fat': 0,
        'carb': 0,
        'sugar': 0,
        'fiber': 0,
    }
    total_minerals = {
        'sodium': 0,
        'potassium': 0,
        'calcium': 0,
        'magnesium': 0,
        'zinc': 0,
        'iron': 0,
    }
    total_vitamins = {
        'vitamin_a': 0,
        'vitamin_b6': 0,
        'vitamin_b12': 0,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_e': 0,
    }
    total_macros['protein'] += data['protein']
    total_macros['fat'] += data['fat']
    total_macros['carb'] += data['carb']
    total_macros['sugar'] += data['sugar']
    total_macros['fiber'] += data['fiber']
    total_minerals['sodium'] += data['sodium']
    total_minerals['potassium'] += data['potassium']
    total_minerals['calcium'] += data['calcium']
    total_minerals['magnesium'] += data['magnesium']
    total_minerals['zinc'] += data['zinc']
    total_minerals['iron'] += data['iron']
    total_vitamins['vitamin_a'] += data['vitamin_a']
    total_vitamins['vitamin_b6'] += data['vitamin_b6']
    total_vitamins['vitamin_b12'] += data['vitamin_b12']
    total_vitamins['vitamin_c'] += data['vitamin_c']
    total_vitamins['vitamin_d'] += data['vitamin_d']
    total_vitamins['vitamin_e'] += data['vitamin_e']
    macros = [
        {"name": "Protein", "value": round(total_macros['protein'])},
        {"name": "Fat",     "value": round(total_macros['fat'])},
        {"name": "Carbs",   "value": round(total_macros['carb']),
        "sugar": round(total_macros['sugar']),
        "fiber": round(total_macros['fiber'])},
    ]
    minerals = [
        {"name": "Na",     "ratio": get_ratio(total_minerals['sodium'],       goals['sodium']), "value": round(total_minerals['sodium'])},
        {"name": "K",  "ratio": get_ratio(total_minerals['potassium'],    goals['potassium']), "value": round(total_minerals['potassium'])},
        {"name": "Ca",    "ratio": get_ratio(total_minerals['calcium'],      goals['calcium']), "value": round(total_minerals['calcium'])},
        {"name": "Mg",  "ratio": get_ratio(total_minerals['magnesium'],    goals['magnesium']), "value": round(total_minerals['magnesium'])},
        {"name": "Zn",       "ratio": get_ratio(total_minerals['zinc'],         goals['zinc']), "value": round(total_minerals['zinc'])},
        {"name": "Fe",       "ratio": get_ratio(total_minerals['iron'],         goals['iron']), "value": round(total_minerals['iron'])},
    ]
    vitamins = [
        {"name": "A",   "ratio": get_ratio(total_vitamins['vitamin_a'],   goals['A']), "value": round(total_vitamins['vitamin_a'], 1)},
        {"name": "B6",  "ratio": get_ratio(total_vitamins['vitamin_b6'],  goals['B6']), "value": round(total_vitamins['vitamin_b6'], 1)},
        {"name": "B12", "ratio": get_ratio(total_vitamins['vitamin_b12'], goals['B12']), "value": round(total_vitamins['vitamin_b12'], 1)},
        {"name": "C",   "ratio": get_ratio(total_vitamins['vitamin_c'],   goals['C']), "value": round(total_vitamins['vitamin_c'], 1)},
        {"name": "D",   "ratio": get_ratio(total_vitamins['vitamin_d'],   goals['D']), "value": round(total_vitamins['vitamin_d'], 1)},
        {"name": "E",   "ratio": get_ratio(total_vitamins['vitamin_e'],   goals['E']), "value": round(total_vitamins['vitamin_e'], 1)},
    ]
    return macros, minerals, vitamins

