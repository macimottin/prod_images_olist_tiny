import requests
import os
import time
import csv

# Configurações
TOKEN = "your-token-here"
BASE_URL = "https://api.tiny.com.br/api2"
SAVE_FOLDER = r"C:\\your\\path\\here"
WAIT_TIME = 1  # Tempo de espera entre as requisições em segundos
LOG_FILE = r"C:\\your\\path\\here"

# Criar pasta para salvar as imagens (se não existir)
os.makedirs(SAVE_FOLDER, exist_ok=True)

def obter_produtos():
    """Obtém a lista de produtos cadastrados no Tiny."""
    produtos = []
    pagina = 1
    while True:
        url = f"{BASE_URL}/produtos.pesquisa.php"
        params = {
            "token": TOKEN,
            "formato": "json",
            "pagina": pagina
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("retorno", {}).get("status") != "OK":
            print(f"Erro ao obter produtos: {data.get('retorno', {}).get('erro', 'Desconhecido')}")
            break

        produtos_page = data.get("retorno", {}).get("produtos", [])
        if not produtos_page:
            break

        produtos.extend(produtos_page)
        print(f"Página {pagina} carregada com sucesso.")
        pagina += 1
        time.sleep(WAIT_TIME)

    return produtos

def baixar_imagens(produtos):
    """Baixa as imagens dos produtos e salva na pasta local."""
    log_data = []
    for produto in produtos:
        id_produto = produto.get("produto", {}).get("id")
        nome_produto = produto.get("produto", {}).get("nome", "Desconhecido")
        if not id_produto:
            continue

        # Obter detalhes do produto para buscar as imagens
        url = f"{BASE_URL}/produto.obter.php"
        params = {
            "token": TOKEN,
            "formato": "json",
            "id": id_produto
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("retorno", {}).get("status") != "OK":
            print(f"Erro ao obter detalhes do produto {id_produto}: {data.get('retorno', {}).get('erro', 'Desconhecido')}")
            log_data.append([id_produto, nome_produto, "Erro ao obter detalhes"])
            time.sleep(WAIT_TIME)
            continue

        anexos = data.get("retorno", {}).get("produto", {}).get("anexos", [])
        if not anexos:
            print(f"Nenhuma imagem encontrada para o produto {id_produto}.")
            log_data.append([id_produto, nome_produto, "Nenhuma imagem encontrada"])
            continue

        for i, anexo in enumerate(anexos):
            url_imagem = anexo.get("anexo")
            if not url_imagem:
                continue

            # Nome do arquivo para salvar
            nome_arquivo = f"{id_produto}_{i + 1}.jpg"
            caminho_arquivo = os.path.join(SAVE_FOLDER, nome_arquivo)

            try:
                # Baixar a imagem
                img_response = requests.get(url_imagem, stream=True)
                if img_response.status_code == 200:
                    with open(caminho_arquivo, "wb") as f:
                        for chunk in img_response.iter_content(1024):
                            f.write(chunk)
                    print(f"Imagem salva: {caminho_arquivo}")
                    log_data.append([id_produto, nome_produto, "Sucesso", caminho_arquivo])
                else:
                    print(f"Erro ao baixar imagem do produto {id_produto}: {url_imagem}")
                    log_data.append([id_produto, nome_produto, "Erro ao baixar imagem"])
            except Exception as e:
                print(f"Erro ao salvar a imagem {nome_arquivo}: {e}")
                log_data.append([id_produto, nome_produto, f"Erro: {e}"])

        time.sleep(WAIT_TIME)

    # Salvar log em CSV
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        writer.writerow(["ID Produto", "Nome Produto", "Status", "Caminho da Imagem"])
        writer.writerows(log_data)
    print(f"Log de downloads salvo em {LOG_FILE}")

if __name__ == "__main__":
    print("Obtendo lista de produtos...")
    produtos = obter_produtos()

    if produtos:
        print(f"{len(produtos)} produtos encontrados. Iniciando download das imagens...")
        baixar_imagens(produtos)
        print("Download concluído.")
    else:
        print("Nenhum produto encontrado.")
