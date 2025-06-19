from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)

def load_recipes():
    try:
        recipes = pd.read_csv('РК.csv', sep=';', encoding='utf-8', usecols=range(19), skiprows=10)
        recipes.drop(columns=['Масса', 'Вес ингр-тов', 'Траты всего', 'Ссылка ПК', 'г'], inplace=True)
        
        # Обработка числовых колонок
        for col in ['р', 'Цена за 1 кг', 'ЧП']:
            recipes[col] = (
                recipes[col]
                .astype(str)
                .str.replace('₽', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            recipes[col] = pd.to_numeric(recipes[col], errors='coerce')
        
        # Обработка процентных колонок
        percent_cols = ['%', 'Потери, %', 'Маржа']
        for col in percent_cols:
            recipes[col] = (
                recipes[col]
                .astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.replace(' ', '', regex=False)
            )
            recipes[col] = pd.to_numeric(recipes[col], errors='coerce')
        
        return recipes
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()

recipes_df = load_recipes()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    dish_list = sorted(recipes_df['Название'].unique().tolist()) if not recipes_df.empty else []
    
    if request.method == 'POST':
        try:
            dish = request.form['dish']
            weight = int(request.form['weight'])
            
            if dish not in recipes_df['Название'].values:
                error = f"Блюдо '{dish}' не найдено в базе"
            else:
                filtered = recipes_df.loc[recipes_df['Название'] == dish, ['Состав', '%']].copy()
                filtered['г'] = filtered['%'] * weight / 100
                filtered = filtered[['Состав', 'г']]  # Убираем колонку с процентами
                result = filtered.sort_values('г', ascending=False).to_html(
                    classes='table table-striped', 
                    border=0,
                    index=False  # Убираем индексы
                )
        except ValueError:
            error = "Пожалуйста, введите корректный вес (целое число)"
        except Exception as e:
            error = f"Произошла ошибка: {str(e)}"

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Калькулятор рецептов</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
                select, input, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; }
                button { background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #45a049; }
                .table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .table th { background-color: #f2f2f2; }
                .error { color: red; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>Расчет состава блюда</h1>
            <form method="POST">
                <select name="dish" required>
                    <option value="" disabled selected>Выберите блюдо</option>
                    {% for dish in dish_list %}
                        <option value="{{ dish }}">{{ dish }}</option>
                    {% endfor %}
                </select>
                <input type="number" name="weight" placeholder="Вес (г)" required min="1">
                <button type="submit">Рассчитать</button>
            </form>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            {% if result %}
                <h2>Результат:</h2>
                <div class="table-container">{{ result|safe }}</div>
            {% endif %}
        </body>
        </html>
    ''', result=result, error=error, dish_list=dish_list)

if __name__ == '__main__':
    app.run(debug=True)