import os
import gspread
import pandas as pd
from time import sleep
from selenium import webdriver
#from datetime import datetime,timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from oauth2client.service_account import ServiceAccountCredentials

# Configurar a conexão com a API do Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ""#prencha esse campo
client = gspread.authorize(creds)

# Abrir a planilha do Google Sheets
sheet = "" #prencha esse campo
sheet.clear()

urls = []
desconto = []
images = []
precos = []
titulo = []
desconto_real = []

options = Options()
#options.add_argument('-headless') recomendo deixar desativado
driver = webdriver.Firefox(options=options)

url_amazon = 'https://www.amazon.com.br/gp/goldbox?deals-widget=%257B%2522version%2522%253A1%252C%2522viewIndex%2522%253A0%252C%2522presetId%2522%253A%2522deals-collection-beauty%2522%252C%2522dealType%2522%253A%2522LIGHTNING_DEAL%2522%252C%2522sorting%2522%253A%2522BY_DISCOUNT_DESCENDING%2522%257D'

driver.get(url_amazon)
sleep(15)

print("Scaneando")

#container Mae/pai é apenas uma forma de assegurar que tudo vai ficar dentro do planejado
container_mae = driver.find_element(By.XPATH,
                                     ".//div[@class='Grid-module__gridDisplayGrid_2X7cDTY7pjoTwwvSRQbt9Y']")

#container filho contem todas informaçoes dos produtos
container_filho = container_mae.find_elements(By.XPATH, ".//div[@class='DealGridItem-module__dealItemDisplayGrid_e7RQVFWSOrwXBX4i24Tqg DealGridItem-module__withBorders_2jNNLI6U1oDls7Ten3Dttl DealGridItem-module__withoutActionButton_2OI8DAanWNRCagYDL2iIqN']")







#_______________________________________________TITULO_____________________________________________
# Loop para percorrer todos os elementos dentro do container filho
for elemento_filho in container_filho:
    # encontrando o titulo dentro do elemento filho
    titulo_elements = elemento_filho.find_elements(By.XPATH,
                                                    ".//div[@class='DealContent-module__truncate_sWbxETx42ZPStTc9jwySW']")

    # coletando o titulo e armazenando na lista titulo, de forma organizada e sincronizada com as fotos coletadas
    for titulo_element in titulo_elements:
        titulo.append(titulo_element.text)
#----------------------------------------------------------------------------------------------------






#_______________________________________________FOTOS________________________________________________
    # encontrando as imagens dentro do elemento filho
    img_elements = elemento_filho.find_elements(By.XPATH,
                                                ".//img[@class='DealImage-module__imageObjectFit_1G4pEkUEzo9WEnA3Wl0XFv']")

    # coletando as imagens e armazenando na lista foto
    for image_element in img_elements:
        images.append(image_element.get_attribute('src'))
#----------------------------------------------------------------------------------------------------





#_______________________________________________DESCONTO_____________________________________________
    # encontrando o desconto dentro do elemento filho
    desconto_elements = elemento_filho.find_elements(By.XPATH,
                                                    ".//div[@class='BadgeAutomatedLabel-module__badgeAutomatedLabel_2Teem9LTaUlj6gBh5R45wd']")

       # coletando o desconto e armazenando na lista desconto
    for desconto_element in desconto_elements:
        desconto.append(desconto_element.text)
    desconto = list(filter(None, desconto))
#----------------------------------------------------------------------------------------------------





#_______________________________________________PREÇOS_______________________________________________

# Inicializar uma lista para armazenar os índices dos elementos que não têm preço
indices_sem_preco = []

# Criar a lista de links_produtos para entrar em cada elemento separadamente
links_produtos = []
for elemento_filho in container_filho:
    link_produto = elemento_filho.find_element(By.XPATH, ".//a[@class='a-link-normal DealLink-module__dealLink_3v4tPYOP4qJj9bdiy0xAT a-color-base a-text-normal']").get_attribute('href')
    links_produtos.append(link_produto)


precos_inteiros = []
precos_decimais = []
precos_reais = []


# Iterar sobre os elementos para coletar os preços
for i, link_produto in enumerate(links_produtos):
    # Acessar o link da oferta
    driver.get(link_produto)
    sleep(5)

    preco_inteiro = "Nullo"  # Valor padrão caso nenhuma parte inteira seja encontrada
    preco_decimal = "Nullo"  # Valor padrão caso nenhuma parte decimal seja encontrada
    preco_real = "Nullo"     # Valor padrão caso nenhum preço real encontrado

    try:
        # Tentando encontrar o preço com desconto
        preco_element = driver.find_element(By.XPATH, ".//span[@class='a-price-whole']")
        preco_inteiro = preco_element.text

    except NoSuchElementException:
        pass

    try:
        # Tentando encontrar os centavos
        preco_decimal_element = driver.find_element(By.XPATH, ".//span[@class='a-price-fraction']")
        preco_decimal = preco_decimal_element.text
    except NoSuchElementException:
        pass

    try:

        preco_real_element = driver.find_element(By.XPATH,".//div[@class='a-section a-spacing-small aok-align-center']")
        preco_real = preco_real_element.text.replace("De:", "").replace("\n", "")
    except NoSuchElementException:
        pass

    precos_inteiros.append(preco_inteiro)
    precos_decimais.append(preco_decimal)
    precos_reais.append(preco_real)

    driver.back()
    sleep(1)

# Combinar as partes inteiras e decimais para formar a lista de preços desejada
precos = [f"{inteiro},{decimal}" for inteiro, decimal in zip(precos_inteiros, precos_decimais)]


# Remover os elementos sem preço da lista de links e de preços
for indice in reversed(indices_sem_preco):
    del links_produtos[indice]
    del precos[indice]

#----------------------------------------------------------------------------------------------------



#===============================================PRINTS
print(f"TITULOS: {titulo}")
print(f"FOTOS: {images}")
print(f"LINK: {links_produtos}")
print(f"DESCONTOS: {desconto}")
print(f"PRECOS: {precos}")
print(f"PREÇO REAL: {precos_reais}")

data = {

    'Product': titulo,
    'Image URL': images,
    'url': links_produtos,
    'Discount': desconto,
    'Price': precos,
    'Desconto Real': precos_reais,

}

df = pd.DataFrame(data)

try:
    header = df.columns.values.tolist()
    sheet.insert_rows([header], 1)

    # Adicionar os valores
    values = df.values.tolist()
    sheet.insert_rows(values, 2)

    print("Dados Enviados com Sucesso!")
except Exception as e:
    print(f"Erro no Envio de Dados: {e}")


driver.quit()


#cria uma pasta com todoas as fotos dos produtos para utilizar depois

def escrever_lista_em_txt(lista, nome_arquivo):
    caminho_pasta = 'Pasta_diaria'
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
    caminho_arquivo = os.path.join("DESCONTINUADOS/drivers", "Pasta_Mensal", "DESCONTINUADOS/Pasta_diaria", nome_arquivo)

    with open(caminho_arquivo, 'w') as arquivo:
        for item in lista:
            arquivo.write(str(item) + '\n')

escrever_lista_em_txt(images, 'img.txt')
print("Listas foram escritas na pasta diária.")




























