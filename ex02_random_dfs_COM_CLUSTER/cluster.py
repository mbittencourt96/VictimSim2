import os
import csv
import numpy as np
from sklearn.cluster import KMeans

def categorize_victims(victims_data):
    # Categorizar as vítimas com base nos sinais vitais
    for key, value in victims_data.items():
        vital_sign = value[1]
        if vital_sign == 0:
            category = 'Morto'
        elif vital_sign <= 25:
            category = 'Crítico'
        elif vital_sign <= 50:
            category = 'Grave'
        else:
            category = 'OK'
        value.append(category)

    return victims_data

def cluster_victims(victims_data):
    # Extrair os sinais vitais para clustering
    vital_signs = [value[1] for value in victims_data.values()]
    X = np.array(vital_signs).reshape(-1, 1)

    # Clusterizar os sinais vitais usando KMeans
    kmeans = KMeans(n_clusters=4, random_state=0)
    kmeans.fit(X)
    labels = kmeans.labels_

    # Adicionar os rótulos de cluster aos dados das vítimas
    for i, (key, value) in enumerate(victims_data.items()):
        value.append(labels[i])

    return victims_data

def export_category_data(victims_data, output_folder):
    # Verificar se a pasta de saída existe, senão, criar
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Exportar os dados de categorização para um arquivo CSV
    csv_file = os.path.join(output_folder, 'categorizacao.csv')
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Coordenadas', 'Sinais Vitais', 'Categoria', 'Cluster'])
        for key, value in victims_data.items():
            writer.writerow([key, value[0], value[1], value[2], value[3]])

    print(f"Os dados de categorização foram exportados para {csv_file}")

if __name__ == "__main__":
    # Exemplo de uso
    victims_data = {
        1: [(1, 2), 80],
        2: [(3, 4), 30],
        3: [(5, 6), 60],
        # Adicione mais dados conforme necessário
    }

    # Categorizar os dados das vítimas
    categorized_victims_data = categorize_victims(victims_data)

    # Clusterizar os dados das vítimas
    clustered_victims_data = cluster_victims(categorized_victims_data)

    # Exportar os dados de categorização
    output_folder = 'output'
    export_category_data(clustered_victims_data, output_folder)