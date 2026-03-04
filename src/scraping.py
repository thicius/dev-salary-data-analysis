from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Executa as tarefas no plano de fundo, sem aparecer na tela no computador.
    chrome_options.add_argument('--no-sandbox') # Necessário por causa das restrições do Google Colab
    chrome_options.add_argument('--disable-dev-shm-usage') # Força o Chrome a usar a memória RAM normal em vez da memória compartilhada.
    chrome_options.add_argument('--window-size=1920,1080') # Evita certos problemas definindo uma resolução normal pra tela virtual.

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fechar_modais_e_avisos(driver):
    botao_ja_adicionei = driver.find_elements(By.XPATH, "//button[contains(., 'Já adicionei')]")
    if botao_ja_adicionei:
        botao_ja_adicionei[0].click()
        print("Pop-up do 'Já adicionei' fechado")
        time.sleep(1) # Dá um intervalo de 1 segundo antes de ir para a próxima linha

def extrair_dados_card(html_card):
    soup = BeautifulSoup(html_card, 'html.parser')
    dados = {}

    try:
        cargo = soup.find('h3', class_='font-semibold')
        dados['cargo'] = cargo.get_text(strip=True) if cargo else "Não informado"

        empresa = soup.find('span', class_='truncate')
        dados['empresa'] = empresa.get_text(strip=True) if empresa else "Não informado"

        salario = soup.find('div', class_='text-xl font-bold text-[#008000]')
        if salario:
            salario_texto = salario.get_text(strip=True)
            dados['salario_base'] = re.sub(r'[^\d.]', '', salario_texto)
        else:
            dados['salario_base'] = "Não informado"

        return dados
    except:
        return None

def coletar_salarios(profissao):
    # Configura o driver
    try:
        driver = configurar_driver()
    except Exception as e:
        print(f"Erro ao iniciar o Chrome: {e}")
        return []

    dados_coletados = []

    try:
        # Busca diretamente a URL abaixo
        print("Acessando o site Salário Transparente...")
        driver.get("https://salariotransparente.com.br/salarios")
        time.sleep(2)

        # Encontra o input "barra de pesquisa", como já explicado acima
        print(f"Pesquisando por: {profissao}")
        search_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Buscar por cargo']"))
        )

        # Digita cada letra da string em profissão e dá um enter 
        search_input.clear()
        search_input.send_keys(profissao)
        search_input.send_keys(Keys.RETURN)

        time.sleep(3) # Tempo para o site processar a busca

        print("Iniciando scroll...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        tentativas = 0
        max_tentativas = 100 # É apenas quantas vezes totais ele pode scrollar

        while tentativas < max_tentativas:
            # Olhando pro site notei que geralmente é aqui que aparecem os pop-ups
            fechar_modais_e_avisos(driver)

            # Como nossa página carrega aos poucos, aqui estamos scrollando até o ponto mais baixo da tela
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) # Para que dê tempo dos cards carregarem

            # Verificando se scrollar fez que encontrássemos novos cards
            new_height = driver.execute_script("return document.body.scrollHeight")
            # Agora contaremos quantos cards temos
            cards = driver.find_elements(By.CSS_SELECTOR, "div.salary-card")
            print(f"Scroll {tentativas+1}: {len(cards)} cards encontrados")

            if new_height == last_height:
                # Se parou de crescer, pode ser o fim da página ou um pop-up bloqueando
                fechar_modais_e_avisos(driver) # Tenta fechar mais uma vez por garantia
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    # Nesse caso não temos mais cards
                    print("Fim dos resultados.")
                    break

            last_height = new_height
            tentativas += 1
            # Aqui o scroll já chegou ao fim

        # Coletar todos os cards finais
        cards = driver.find_elements(By.CSS_SELECTOR, "div.salary-card")
        print(f"Total final de {len(cards)} cards para processar.")

        # Aplica o extrair_dados_card em todos os cards que encontramos acima
        for i, card in enumerate(cards):
            try:
                html = card.get_attribute('outerHTML')
                dados = extrair_dados_card(html)
                if dados:
                    dados_coletados.append(dados)
            except Exception as e:
                # Silencia erros individuais
                continue

        return dados_coletados

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        return dados_coletados

    # Fecha todas as janelas do chrome caso o código falhe no meio
    finally:
        if 'driver' in locals():
            driver.quit()

def salvar_csv(dados, profissao):
    if not dados:
        print("Não conseguimos coletar nenhum dado")
        return
    df = pd.DataFrame(dados)
    filename = f'salario_transparente_{profissao}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Os dados foram salvos em {filename}")

# Execução principal
if __name__ == "__main__":
    profissao = "Enfermeiro"
    dados = coletar_salarios(profissao)

    if dados:
        salvar_csv(dados, profissao)
        print(f"Processo finalizado. Coletamos {len(dados)} dados.")
    else:
        print("Falha na coleta.")