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
        # 1. Cargo
        cargo = soup.find('h3', class_='font-semibold')
        dados['cargo'] = cargo.get_text(strip=True) if cargo else "Não informado"
        
        # 2. Empresa
        empresa = soup.find('span', class_='truncate')
        dados['empresa'] = empresa.get_text(strip=True) if empresa else "Não informado"
        
        # 3. Salário base mensal
        salario = soup.find('div', class_='text-xl font-bold text-[#008000]')
        if salario:
            salario_texto = salario.get_text(strip=True)
            dados['salario_base'] = re.sub(r'[^\d.]', '', salario_texto)
        else:
            dados['salario_base'] = "Não informado"
            
        # 4. Informações detalhadas: localizacao, modalidade_trabalho, nivel, experiencia, tipo_contrato
        details_container = soup.find('div', class_='flex flex-wrap items-center gap-x-4 text-sm text-muted-foreground')
        if details_container:
            details_items = details_container.find_all('div', class_='flex items-center')
            detalhes = []
            for item in details_items:
                span = item.find('span')
                if span:
                    detalhes.append(span.get_text(strip=True))
            
            # Garante que não dê erro de index out of range caso falte algum detalhe
            dados['localizacao'] = detalhes[0] if len(detalhes) > 0 else "Não informado"
            dados['modalidade_trabalho'] = detalhes[1] if len(detalhes) > 1 else "Não informado"
            dados['nivel'] = detalhes[2] if len(detalhes) > 2 else "Não informado"
            dados['experiencia'] = detalhes[3] if len(detalhes) > 3 else "Não informado"
            dados['tipo_contrato'] = detalhes[4] if len(detalhes) > 4 else "Não informado"
        
        # 5. Remuneração total anual e equivalente mensal
        remuneracao_container = soup.find('div', class_='flex justify-between items-start mb-3')
        if remuneracao_container:
            valor_anual = remuneracao_container.find('div', class_='text-xl font-bold text-primary/85')
            valor_mensal = remuneracao_container.find('div', class_='text-[14px] text-[#6C757D]')
            
            dados['remuneracao_total_anual'] = re.sub(r'[^\d.]', '', valor_anual.get_text(strip=True)) if valor_anual else "Não informado"
            dados['remuneracao_total_mensal'] = re.sub(r'[^\d.]', '', valor_mensal.get_text(strip=True)) if valor_mensal else "Não informado"
        
        # 6. O que inclui na remuneração total
        inclui_div = soup.find('div', class_='text-xs text-muted-foreground')
        dados['remuneracao_inclui'] = inclui_div.get_text(" ", strip=True) if inclui_div else "Não informado"
        
        # 7. Detalhes do salário base e bônus
        detalhes_remuneracao = []
        items_remuneracao = soup.find_all('div', class_='flex items-center text-xs')
        for item in items_remuneracao:
            if item.find('span'):
                detalhes_remuneracao.append(item.find('span').get_text(strip=True))
        
        salario_base_val = "Não informado"
        bonus_val = "Não informado"
        for item in detalhes_remuneracao:
            if 'Salário base:' in item:
                salario_base_val = re.sub(r'[^\d.]', '', item.replace('Salário base:', ''))
            elif 'Bônus Anual' in item:
                bonus_val = re.sub(r'[^\d.]', '', item.replace('Bônus Anual & PLR:', '').replace('Bônus Anual &amp; PLR:', ''))
        
        dados['salario_base_detalhado'] = salario_base_val
        dados['bonus_anual'] = bonus_val
        
        # 8. Relação com a empresa
        relacao_div = soup.find('div', string='Relação com a empresa')
        if relacao_div:
            relacao_container = relacao_div.find_next('div', class_='flex items-center text-sm text-muted-foreground')
            dados['relacao_empresa'] = relacao_container.get_text(strip=True) if relacao_container else "Não informado"
        else:
            dados['relacao_empresa'] = "Não informado"
        
        # 9. Área de especialização
        area_div = soup.find('div', string='Área de especialização')
        if area_div:
            area_container = area_div.find_next('div', class_='flex items-center text-sm text-muted-foreground')
            dados['area_especializacao'] = area_container.get_text(strip=True) if area_container else "Não informado"
        else:
            dados['area_especializacao'] = "Não informado"
        
        # 10. Benefícios
        beneficios = []
        beneficios_container = soup.find('div', class_='flex flex-wrap gap-1')
        if beneficios_container:
            benefit_divs = beneficios_container.find_all('div', class_='border')
            for benefit in benefit_divs:
                texto = benefit.get_text(strip=True)
                # Remover emojis e caracteres especiais, mantendo apenas texto legível
                texto_limpo = re.sub(r'[^\w\s\(\)\/\-&]', '', texto).strip()
                if texto_limpo:
                    beneficios.append(texto_limpo)
        
        dados['beneficios'] = " | ".join(beneficios) if beneficios else "Não informado"
        
        return dados
    
    except Exception as e:
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
    
    # Reordena as colunas em uma ordem boa para visualizar
    colunas_ordenadas = [
        'cargo', 'empresa', 'salario_base', 'localizacao', 'modalidade_trabalho', 
        'nivel', 'experiencia', 'tipo_contrato', 'remuneracao_total_anual', 
        'remuneracao_total_mensal', 'remuneracao_inclui', 'salario_base_detalhado', 
        'bonus_anual', 'relacao_empresa', 'area_especializacao', 'beneficios'
    ]
    
    # Manter apenas colunas existentes para evitar erros de KeyError
    colunas_existentes = [col for col in colunas_ordenadas if col in df.columns]
    colunas_restantes = [col for col in df.columns if col not in colunas_existentes]
    
    df = df[colunas_existentes + colunas_restantes]
    
    filename = f'salario_transparente_{profissao}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Os dados foram salvos em {filename}")

# Execução principal
if __name__ == "__main__":
    profissao = "Cientista de Dados"
    dados = coletar_salarios(profissao)
    if dados:
        salvar_csv(dados, profissao)
        print(f"Processo finalizado. Coletamos {len(dados)} dados.")
    else:
        print("Falha na coleta.")
