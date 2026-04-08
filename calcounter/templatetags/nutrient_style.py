from django import template

register = template.Library()

# Keys must match Food.to_formatted_dict() labels (MACRO_MAP, MINERAL_MAP, VITAMIN_MAP).
_NUTRIENT_GOAL_COLORS = {
    "Energy": "var(--calorie-color)",
    "Protein": "var(--protein-color)",
    "Total lipid (fat)": "var(--fat-color)",
    "Carbohydrate, by difference": "var(--carb-color)",
    "Sugars, total including NLEA": "var(--sugar-color)",
    "Fiber, total dietary": "var(--fiber-color)",
    "Cholesterol": "var(--cholesterol-color)",
    "Calcium, Ca": "var(--calcium-color)",
    "Iron, Fe": "var(--iron-color)",
    "Magnesium, Mg": "var(--magnesium-color)",
    "Potassium, K": "var(--potassium-color)",
    "Sodium, Na": "var(--sodium-color)",
    "Zinc, Zn": "var(--zinc-color)",
    "Vitamin A, RAE": "var(--vitamin-a-color)",
    "Vitamin B-6": "var(--vitamin-b6-color)",
    "Vitamin B-12": "var(--vitamin-b12-color)",
    "Vitamin C, total ascorbic acid": "var(--vitamin-c-color)",
    "Vitamin D (D2 + D3)": "var(--vitamin-d-color)",
    "Vitamin E (alpha-tocopherol)": "var(--vitamin-e-color)",
}


@register.filter
def nutrient_goal_color(name):
    return _NUTRIENT_GOAL_COLORS.get(str(name), "var(--pico-muted-color)")
