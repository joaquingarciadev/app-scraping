from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        columns = request.form.getlist('column_name[]')
        selectors = request.form.getlist('selector[]')
        types = request.form.getlist('type[]')

        deep_scrape = request.form.get('deep_scrape')
        link_selector = request.form.get('link_selector')
        
        pagination_enabled = request.form.get('pagination_enabled')
        pagination_params = request.form.get('pagination_params')
        pagination_limit = request.form.get('pagination_limit')
        # pagination_limit = request.form.get('pagination_limit', '0')  # Default to '0' as a string
        # try:
            # pagination_limit = int(pagination_limit)
        # except ValueError:
            # pagination_limit = 0  # Handle the case where the input is not a valid integer

        results = []

        if pagination_enabled and pagination_params:
            for page_num in range(1, pagination_limit + 1):
                paginated_url = url + pagination_params.replace('PAGENUM', str(page_num))
                
                response = requests.get(paginated_url)
                soup = BeautifulSoup(response.text, 'html.parser')

                if deep_scrape and link_selector:
                    links = [a['href'] for a in soup.select(link_selector)]
                    for link in links:
                        link_response = requests.get(link)
                        link_soup = BeautifulSoup(link_response.text, 'html.parser')
                        result = {}
                        for i in range(len(columns)):
                            column_name = columns[i]
                            selector = selectors[i]
                            element_type = types[i]
                            
                            result[column_name] = extract_data(link_soup, selector, element_type)
                        results.append(result)
                else:
                    result = {}
                    for i in range(len(columns)):
                        column_name = columns[i]
                        selector = selectors[i]
                        element_type = types[i]
                        
                        result[column_name] = extract_data(soup, selector, element_type)
                    results.append(result)
            results = [merge_data(results)]
            
            return render_template('index.html', results=results, zip=zip, list=list)
        else:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if deep_scrape and link_selector:
                # Modo de scraping profundo
                links = [a['href'] for a in soup.select(link_selector)]
                for link in links:
                    link_response = requests.get(link)
                    link_soup = BeautifulSoup(link_response.text, 'html.parser')
                    result = {}
                    for i in range(len(columns)):
                        column_name = columns[i]
                        selector = selectors[i]
                        element_type = types[i]
                        
                        result[column_name] = extract_data(link_soup, selector, element_type)
                    results.append(result)
            else:
                # Scraping normal
                result = {}
                for i in range(len(columns)):
                    column_name = columns[i]
                    selector = selectors[i]
                    element_type = types[i]
                    
                    result[column_name] = extract_data(soup, selector, element_type)
                results.append(result)
            results = [merge_data(results)]
            
            # Exportar a CSV
            # if request.form.get('export_csv'):
            #     return export_to_csv(results, columns)
            
            return render_template('index.html', results=results, zip=zip, list=list)
    if request.method == 'GET':
        return render_template('index.html', zip=zip, list=list)

def extract_data(soup, selector, element_type):
    if element_type == 'text':
        return [element.text for element in soup.select(selector)]
    elif element_type == 'href':
        return [element['href'] for element in soup.select(selector)]
    elif element_type == 'src':
        return [element['src'] for element in soup.select(selector)]
    elif element_type == 'html':
        return [element.prettify() for element in soup.select(selector)]
    else:
        return [str(element) for element in soup.select(selector)]

def merge_data(dict_list):
    merged_data = {}

    for item in dict_list:
        for key, value in item.items():
            if key in merged_data:
                merged_data[key].extend(value)
            else:
                merged_data[key] = value

    return merged_data

# def export_to_csv(results, columns):
#     df = pd.DataFrame(results)
#     csv_buffer = io.StringIO()
#     df.to_csv(csv_buffer, index=False)
#     csv_buffer.seek(0)
    
#     return send_file(io.BytesIO(csv_buffer.getvalue().encode()), attachment_filename='results.csv', as_attachment=True)

# @app.route('/csv', methods=['POST'])
# def export_csv():
#     results = request.form.getlist('results[]')
#     columns = request.form.getlist('columns[]')
    
#     return export_to_csv(results, columns)

if __name__ == '__main__':
    app.run(debug=True)
