from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for
from json import dumps as json_dumps
import requests
import json
import os

app = Flask(__name__)

# Directory to store JSON files
JSON_DIR = os.path.join(os.path.dirname(__file__), 'JSON_Files')

# Ensure JSON_DIR exists
os.makedirs(JSON_DIR, exist_ok=True)

def read_from_json(filename):
    import json
    with open(os.path.join(JSON_DIR, filename)) as f:
        data = json.load(f)
    return data

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
def save_to_json(data, filename):
    with open(os.path.join(JSON_DIR, filename), 'w') as f:
        json.dump(data, f, indent=4)

def fetch_and_save_categories():
    url = 'https://www.themealdb.com/api/json/v1/1/list.php?c=list'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    }
    try:
        #print("Fetching categories...")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            save_to_json(data, 'categories.json')  # Save the JSON data to 'categories.json'
            #print("Categories downloaded and saved successfully.")
        else:
            print(f"Failed to fetch categories. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching categories: {e}")

def fetch_and_save_meals_by_category(category):
    recipe_url = f'http://www.themealdb.com/api/json/v1/1/filter.php?c={category}'
    try:
        response = requests.get(recipe_url)
        if response.status_code == 200:
            data = response.json()
            save_to_json(data, f'{category}_Meals.json')  # Save the JSON data to '{category}_Meals.json'
            #print(f"Meals for category '{category}' downloaded and saved successfully.")
        else:
            print(f"Failed to fetch meals for category '{category}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching meals for category '{category}': {e}")

# Fetch and save categories if not already saved
categories_file = os.path.join(JSON_DIR, 'categories.json')
if not os.path.exists(categories_file):
    fetch_and_save_categories()

# Load categories from categories.json
with open(categories_file, 'r') as f:
    categories_data = json.load(f)
    if 'meals' in categories_data:
        categories = [category['strCategory'] for category in categories_data['meals']]

        # Generate routes for each category
        for category in categories:
            fetch_and_save_meals_by_category(category)

def save_random_recipe():
    url = 'https://www.themealdb.com/api/json/v1/1/random.php'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            with open(os.path.join(JSON_DIR, 'random.json'), 'w') as f:
                f.write(json.dumps(data, indent=4))
        else:
            print(f"Failed to fetch random recipe. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching random recipe: {e}")

# Download random recipe if not already saved
random_recipe_file = os.path.join(JSON_DIR, 'random.json')
if not os.path.exists(random_recipe_file):
    save_random_recipe()

@app.route('/')
def index():
    # Fetch a random recipe from the API
    response = requests.get('https://www.themealdb.com/api/json/v1/1/random.php')
    if response.status_code == 200:
        random_recipe = response.json()['meals'][0]

        # Write the fetched recipe data to random.json
        with open('JSON_Files/random.json', 'w') as f:
            json.dump(random_recipe, f, indent=4)

        # Pass the random recipe data to the template
        return render_template('index.html', random_recipe=random_recipe)
    else:
        return 'Error fetching random recipe from API'


@app.route('/list_by_first_letter')
def list_by_first_letter():
    all_meals = []

    for letter in 'abcdefghijklmnopqrstuvwxyz':
        filename = f'{letter}_Meals.json'
        if os.path.exists(os.path.join(JSON_DIR, filename)):
            data = read_from_json(filename)
            if data is not None and 'meals' in data and isinstance(data['meals'], list):
                all_meals.extend(data['meals'])

    return render_template('meals_list.html', meals=all_meals)

@app.route('/list_categories')
def list_categories():
    categories = []

    with open(os.path.join(JSON_DIR, 'categories.json'), 'r') as f:
        data = json.load(f)
        if 'meals' in data:
            categories = [category['strCategory'] for category in data['meals']]

    return render_template('categories_list.html', categories=categories)

@app.route('/category/<category>')
def category_recipes(category):
    # Extracting the category name from the filename
    category_name = category.split('_')[0]

    filename = f'{category_name}_Meals.json'
    filepath = os.path.join(JSON_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            meals = json.load(file)
        return render_template('category_recipes.html', category=category_name, filepath=filepath, load_json=load_json, meals=meals)
    else:
        return render_template('category_recipes.html', category=category_name, filepath=filepath, load_json=load_json, meals=None)


@app.route('/recipe/<meal_id>')
def recipe_details(meal_id):
    if meal_id:
        recipe_url = f'http://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}'
        response = requests.get(recipe_url)
        if response.status_code == 200:
            recipe_data = response.json()
            save_to_json(recipe_data, 'recipe.json')
            return render_template('recipe_details.html', recipe=recipe_data['meals'][0])
        else:
            return 'Failed to fetch recipe details', 500
    else:
        return 'Invalid meal ID', 404

if __name__ == '__main__':
    app.run(debug=True)
