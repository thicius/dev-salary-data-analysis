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

# Configurações do Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless") # Infelizmente não consegui fazer o código rodar com ("--headless"), i.e., com a janela de fundo
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-notifications')

def coletar_salarios(profissao):
    """Coleta dados de salários do Salário Transparente"""
    
    driver = webdriver.Chrome(options=chrome_options)
    dados_coletados = []
    
    try:
        print("Acessando o site Salário Transparente...")
        driver.get("https://salariotransparente.com.br/salarios")
        time.sleep(1)
        
        # Localiza e preenche a barra de pesquisa
        print(f"Pesquisando por: {profissao}")
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Buscar por cargo']"))
        )
        
        search_input.clear()
        search_input.send_keys(profissao)
        search_input.send_keys(Keys.RETURN)
        
        # Espera os resultados
        time.sleep(1)
        
        print("Scrollando a página para carregar todos os resultados disponíveis...")
        # Rolar a página lentamente para carregar todos os resultados
        ultima_mensagem = None  
        tentativas = 0
        max_tentativas = 50  # Aumentei o número máximo de tentativas
        
        while tentativas < max_tentativas:
            # Verifica se encontrou a mensagem de fim
            try:
                ultima_mensagem = driver.find_element(By.XPATH, "//div[contains(text(), 'Não há mais resultados para mostrar')]")
                print("Todos os resultados carregados!")
                break
            except:
                pass
            
            # Rolar para baixo lentamente
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Originalmente tava no 4, tentei tirar mas deu problema, vai depender da velocidade da internet
            tentativas += 1
            
            # Verifica o progresso
            cards = driver.find_elements(By.CSS_SELECTOR, "div.salary-card")
            print(f"Scroll {tentativas}: {len(cards)} cards encontrados")
            
            if tentativas >= max_tentativas:
                print("Limite de tentativas atingido")
                break
        
        # Coletar todos os cards finais
        cards = driver.find_elements(By.CSS_SELECTOR, "div.salary-card")
        print(f"Total de {len(cards)} cards encontrados")
        
        for i, card in enumerate(cards):
                
            try:
                html = card.get_attribute('outerHTML')
                dados = extrair_dados_card(html)
                if dados:
                    dados_coletados.append(dados)
                    print(f"Coletado {len(dados_coletados)}: {dados['cargo']} - {dados['empresa']}")
            
            except Exception as e:
                print(f"Erro ao processar card {i+1}: {e}")
                continue
        
        return dados_coletados
        
    except Exception as e:
        print(f"Erro durante a coleta: {e}")
        return dados_coletados
    
    finally:
        driver.quit()

def extrair_dados_card(html):
    """Extrai dados de um card individual de salário"""
    soup = BeautifulSoup(html, 'html.parser')
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
            salario_texto_limpo = re.sub(r'[^\d.]', '', salario_texto)
            dados['salario_base'] = salario_texto_limpo
        else:
            dados['salario_base'] = "Não informado"

        # 4. Informações detalhadas: localizacao, modalidade_trabalh, nivel, experiencia, tipo_contrato
        details_container = soup.find('div', class_='flex flex-wrap items-center gap-x-4 text-sm text-muted-foreground')
        if details_container:
            details_items = details_container.find_all('div', class_='flex items-center')
            detalhes = []

            for item in details_items:
                span = item.find('span')
                texto = span.get_text(strip=True)
                detalhes.append(texto)
            
            dados['localizacao'] = detalhes[0]
            dados['modalidade_trabalho'] = detalhes[1]
            dados['nivel'] = detalhes[2]
            dados['experiencia'] = detalhes[3]
            dados['tipo_contrato'] = detalhes[4]
        
        # 5. Remuneração total anual e equivalente mensal
        remuneracao_container = soup.find('div', class_='flex justify-between items-start mb-3')
        if remuneracao_container:
            valor_anual = remuneracao_container.find('div', class_='text-xl font-bold text-primary/85')
            valor_mensal = remuneracao_container.find('div', class_='text-[14px] text-[#6C757D]')
            if valor_anual:
                # dados['remuneracao_total_anual'] = valor_anual.get_text(strip=True) # Se quiser o número com cifrão e ponto
                dados['remuneracao_total_anual'] = re.sub(r'[^\d.]', '', valor_anual.get_text(strip=True)) # Se quiser só o número sem R$
            else:
                dados['remuneracao_total_anual'] = "Não informado"
            if valor_mensal:
                # dados['equivalente_mensal'] = valor_mensal.get_text(strip=True) # Idem
                dados['remuneracao_total_mensal'] = re.sub(r'[^\d.]', '', valor_mensal.get_text(strip=True)) # Idem
            else:
                dados['equivalente_mensal'] = "Não informado"
        
        # 6. O que inclui na remuneração total
        inclui_div = soup.find('div', class_='text-xs text-muted-foreground')
        if inclui_div:
            dados['remuneracao_inclui'] = inclui_div.get_text(" ", strip=True)
        else:
            dados['remuneracao_inclui'] = "Não informado"
        
        # 7. Detalhes do salário base e bônus
        detalhes_remuneracao = []
        items_remuneracao = soup.find_all('div', class_='flex items-center text-xs')
        
        for item in items_remuneracao:
            if item.find('span'):
                texto = item.find('span').get_text(strip=True)
                detalhes_remuneracao.append(texto)
        
        # Extrair valores individuais de salário base e bônus
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
            # Usamos find_next ao invés de find porque dentro desse container tem dois 'divs' com a mesma classe
            relacao_container = relacao_div.find_next('div', class_='flex items-center text-sm text-muted-foreground')
            if relacao_container:
                dados['relacao_empresa'] = relacao_container.get_text(strip=True)
            else:
                dados['relacao_empresa'] = "Não informado"
        else:
            dados['relacao_empresa'] = "Não informado"
        
        # 9. Área de especialização
        area_div = soup.find('div', string='Área de especialização')
        if area_div:
            area_container = area_div.find_next('div', class_='flex items-center text-sm text-muted-foreground')
            if area_container:
                dados['area_especializacao'] = area_container.get_text(strip=True)
            else:
                dados['area_especializacao'] = "Não informado"
        else:
            dados['area_especializacao'] = "Não informado"
        
        # 10. Benefícios
        beneficios = []
        beneficios_container = soup.find('div', class_='flex flex-wrap gap-1')
        
        if beneficios_container:
            benefit_divs = beneficios_container.find_all('div', class_='border')
            for benefit in benefit_divs:
                # Extrair apenas o texto, ignorando emojis
                texto = benefit.get_text(strip=True)
                # Remover emojis e caracteres especiais, mantendo apenas texto
                texto_limpo = re.sub(r'[^\w\s\(\)\/\-&]', '', texto).strip()
                if texto_limpo:
                    beneficios.append(texto_limpo)
        
        dados['beneficios'] = " | ".join(beneficios) if beneficios else "Não informado"
        
        return dados
        
    except Exception as e:
        print(f"Erro ao extrair dados do card: {e}")
        return None

def salvar_csv(dados, profissao):
    """Salva os dados coletados em CSV"""
    if not dados:
        print("Nenhum dado para salvar")
        return
    
    df = pd.DataFrame(dados)
    
    # Reordenar colunas para melhor visualização
    colunas_ordenadas = [
        'cargo', 'empresa', 'salario_base', 'localizacao', 'modalidade_trabalho', 
        'nivel', 'experiencia', 'tipo_contrato', 'remuneracao_total_anual', 
        'equivalente_mensal', 'remuneracao_inclui', 'salario_base_detalhado', 
        'bonus_anual', 'relacao_empresa', 'area_especializacao', 'beneficios'
    ]
    
    # Manter apenas colunas existentes
    colunas_existentes = [col for col in colunas_ordenadas if col in df.columns]
    colunas_restantes = [col for col in df.columns if col not in colunas_existentes]
    
    df = df[colunas_existentes + colunas_restantes]
    df.to_csv(f'salario_transparente_{profissao}.csv', index=False, encoding='utf-8-sig')
    print(f"Dados salvos em salario_transparente_{profissao}.csv")
    
    return df

if __name__ == "__main__":
    print("Iniciando coleta de dados do Salário Transparente...")
    
    # Se quiser buscar por outra profissão, modifique a string abaixo
    profissao = "Enfermeiro"

    dados = coletar_salarios(profissao)

    if dados:
        print(f"\nColeta concluída! {len(dados)} salários coletados.")
        df = salvar_csv(dados, profissao)
    else:
        print("Nenhum dado foi coletado.")