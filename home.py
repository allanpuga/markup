import streamlit as st
import mysql.connector
import requests
import time

# 1. Configuração de Conexão MySQL
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE, password VARCHAR(255))''')
    
    # Nova estrutura de Perfil (Focada apenas no Motorista)
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  estado VARCHAR(50), cidade VARCHAR(255), whatsapp VARCHAR(50), 
                  dias_semana INT, horas_dia INT, km_dia FLOAT, veiculo_ativo_id INT)''')
                  
    # Nova Tabela: A Garagem (Focada apenas nos Veículos)
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), 
                  marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), 
                  codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50),
                  tipo_posse VARCHAR(50), valor_aluguel_semana FLOAT, valor_parcela FLOAT, parcelas_restantes INT)''')
    conn.commit()
    conn.close()

# 2. APIs (IBGE, FIPE e IPCA)
headers = {'User-Agent': 'Mozilla/5.0'}

@st.cache_data(ttl=86400)
def get_estados():
    try:
        res = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome")
        return {e['sigla']: e['nome'] for e in res.json()}
    except: return {}

@st.cache_data(ttl=86400)
def get_cidades(uf):
    try:
        res = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios")
        return [c['nome'] for c in res.json()]
    except: return []

@st.cache_data(ttl=3600)
def get_marcas():
    try: return requests.get("https://fipe.parallelum.com.br/api/v2/cars/brands", headers=headers).json()
    except: return []

@st.cache_data(ttl=3600)
def get_modelos(marca_id):
    try: return requests.get(f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models", headers=headers).json()
    except: return []

@st.cache_data(ttl=3600)
def get_anos(marca_id, modelo_id):
    try: return requests.get(f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models/{modelo_id}/years", headers=headers).json()
    except: return []

def get_valor_fipe(marca_id, modelo_id, ano_id):
    try: return requests.get(f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models/{modelo_id}/years/{ano_id}", headers=headers).json()
    except: return None

@st.cache_data(ttl=86400)
def get_ipca():
    try:
        res = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1")
        return float(res.json()[0]['valor'])
    except: return 4.50

# 3. Tela de Login
def login_page():
    st.title("🚗 Sistema de Gestão e Markup")
    st.markdown("Gerencie seus custos reais como motorista de aplicativo.")
    
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])
    
    with aba_login:
        st.subheader("Faça seu Login")
        username = st.text_input("Usuário", key="log_user")
        password = st.text_input("Senha", type="password", key="log_pass")
        
        if st.button("Entrar", type="primary"):
            try:
                conn = get_db_connection()
                c = conn.cursor(dictionary=True)
                c.execute("SELECT * FROM usuarios WHERE username=%s AND password=%s", (username, password))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
            except Exception as e: st.error(f"Erro de conexão com o banco: {e}")

    with aba_cadastro:
        st.subheader("Novo Cadastro")
        new_user = st.text_input("Escolha um Usuário", key="cad_user")
        new_pass = st.text_input("Escolha uma Senha", type="password", key="cad_pass")
        if st.button("Cadastrar Usuário"):
            if new_user and new_pass:
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (new_user, new_pass))
                    conn.commit()
                    conn.close()
                    st.success("Conta criada! Volte na aba 'Entrar' para acessar o sistema.")
                except mysql.connector.IntegrityError: st.error("Este nome de usuário já existe.")
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.warning("Preencha todos os campos para se cadastrar.")

# 4. Interface Principal
def main_app():
    username = st.session_state['username']
    
    st.sidebar.title("Navegação")
    st.sidebar.write(f"👤 Olá, **{username}**!")
    
    if 'mudar_aba' in st.session_state:
        st.session_state['menu_opcao'] = st.session_state['mudar_aba']
        del st.session_state['mudar_aba']
        
    menu_opcao = st.sidebar.radio("Etapas:", ["1️⃣ Meu Perfil", "2️⃣ Veículos e Jornada", "3️⃣ Calculadora de Markup", "4️⃣ Painel de Metas"], key="menu_opcao")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Sair (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
    perfil = c.fetchone()
    conn.close()

    # --- TELA 1: MEU PERFIL ---
    if menu_opcao == "1️⃣ Meu Perfil":
        st.title("👤 Seu Perfil Pessoal")
        
        p_nome = perfil['nome'] if perfil else ""
        p_email = perfil['email'] if perfil else ""
        p_whatsapp = perfil['whatsapp'] if perfil else ""
        p_estado = perfil['estado'] if perfil else "Selecione..."
        p_cidade = perfil['cidade'] if perfil else "Selecione..."

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo", value=p_nome)
            email = st.text_input("E-mail", value=p_email)
        with col2:
            whatsapp = st.text_input("WhatsApp", value=p_whatsapp)
            estados = get_estados()
            lista_estados = ["Selecione..."] + [f"{sigla} - {nome}" for sigla, nome in estados.items()]
            
            index_estado = 0
            if p_estado != "Selecione...":
                for i, e in enumerate(lista_estados):
                    if p_estado in e: index_estado = i; break
            
            estado_selecionado = st.selectbox("Estado", options=lista_estados, index=index_estado)
            
            cidade_selecionada = "Selecione..."
            if estado_selecionado != "Selecione...":
                uf = estado_selecionado.split(" - ")[0]
                cidades = ["Selecione..."] + get_cidades(uf)
                index_cidade = cidades.index(p_cidade) if p_cidade in cidades else 0
                cidade_selecionada = st.selectbox("Cidade", options=cidades, index=index_cidade)

        st.markdown("---")
        if st.button("💾 Salvar Perfil e Avançar", type="primary"):
            if estado_selecionado == "Selecione..." or cidade_selecionada == "Selecione...":
                st.warning("Selecione seu Estado e Cidade.")
            else:
                uf_salvar = estado_selecionado.split(" - ")[0]
                conn = get_db_connection()
                c = conn.cursor()
                if perfil:
                    c.execute("UPDATE perfil_motorista SET nome=%s, email=%s, whatsapp=%s, estado=%s, cidade=%s WHERE user_id=%s",
                              (nome, email, whatsapp, uf_salvar, cidade_selecionada, username))
                else:
                    c.execute("INSERT INTO perfil_motorista (user_id, nome, email, whatsapp, estado, cidade, dias_semana, horas_dia, km_dia) VALUES (%s, %s, %s, %s, %s, %s, 6, 8, 150)",
                              (username, nome, email, whatsapp, uf_salvar, cidade_selecionada))
                conn.commit()
                conn.close()
                st.success("✅ Perfil salvo! Avançando para a próxima etapa...")
                time.sleep(1.5)
                st.session_state['mudar_aba'] = "2️⃣ Veículos e Jornada"
                st.rerun()

    # --- TELA 2: VEÍCULOS E JORNADA (A GARAGEM) ---
    elif menu_opcao == "2️⃣ Veículos e Jornada":
        st.title("🚘 Sua Garagem e Jornada")
        if not perfil or not perfil['nome']:
            st.warning("⚠️ Preencha seu Perfil na etapa 1 antes de continuar!")
            return

        p_ds = int(perfil['dias_semana']) if perfil and perfil['dias_semana'] else 6
        p_hd = int(perfil['horas_dia']) if perfil and perfil['horas_dia'] else 8
        p_km = float(perfil['km_dia']) if perfil and perfil['km_dia'] else 150.0
        v_ativo_id = perfil['veiculo_ativo_id'] if perfil else None

        # PARTE 1: JORNADA
        with st.container(border=True):
            st.markdown("### 🕒 Como é a sua rotina na pista?")
            dias_semana = st.slider("Quantos dias você trabalha por semana?", 1, 7, p_ds)
            horas_dia = st.slider("Em média, quantas horas por dia?", 1, 24, p_hd)
            km_dia = st.number_input("Qual a média de KM rodados por dia?", min_value=10, max_value=800, value=int(p_km))

        # PARTE 2: A GARAGEM (Veículos Cadastrados)
        st.markdown("### 🚗 Selecione o Veículo da Operação")
        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE user_id=%s", (username,))
        meus_veiculos = c.fetchall()
        conn.close()

        veiculo_escolhido_id = None

        if meus_veiculos:
            opcoes_nomes = [f"{v['marca']} {v['modelo']} ({v['ano']}) - {v['tipo_posse']}" for v in meus_veiculos]
            opcoes_ids = [v['id'] for v in meus_veiculos]
            
            index_selecionado = 0
            if v_ativo_id in opcoes_ids:
                index_selecionado = opcoes_ids.index(v_ativo_id)
                
            veiculo_escolhido_nome = st.selectbox("Qual veículo você vai usar na pista hoje?", options=opcoes_nomes, index=index_selecionado)
            veiculo_escolhido_id = opcoes_ids[opcoes_nomes.index(veiculo_escolhido_nome)]
        else:
            st.info("Sua garagem está vazia! Adicione o seu primeiro veículo no botão abaixo.")

        # FORMULÁRIO DE ADICIONAR NOVO VEÍCULO
        with st.expander("➕ Adicionar Novo Veículo na Garagem", expanded=not meus_veiculos):
            tipo_posse = st.radio("Este novo veículo é:", ["Próprio", "Alugado", "Financiado"], key="new_posse")
            
            valor_aluguel, valor_parcela, parcelas_restantes = 0.0, 0.0, 0
            if tipo_posse == "Alugado":
                valor_aluguel = st.number_input("Aluguel semanal (R$)", min_value=0.0, key="new_alug")
            elif tipo_posse == "Financiado":
                col_f1, col_f2 = st.columns(2)
                with col_f1: valor_parcela = st.number_input("Valor da parcela mensal (R$)", min_value=0.0, key="new_parc")
                with col_f2: parcelas_restantes = st.number_input("Quantas parcelas faltam?", min_value=0, key="new_prest")
                
            marcas = get_marcas()
            marca_dict = {m['name']: str(m['code']) for m in marcas} if marcas else {}
            marca_selecionada = st.selectbox("Selecione a Marca", ["Selecione..."] + list(marca_dict.keys()), key="new_marca")
            
            modelo_selecionado, ano_selecionado, ano_id = "Selecione...", "Selecione...", None
            
            if marca_selecionada != "Selecione...":
                marca_id = marca_dict[marca_selecionada]
                modelos = get_modelos(marca_id)
                if modelos:
                    modelo_dict = {m['name']: str(m['code']) for m in modelos}
                    modelo_selecionado = st.selectbox("Selecione o Modelo", ["Selecione..."] + list(modelo_dict.keys()), key="new_mod")
                    if modelo_selecionado != "Selecione...":
                        modelo_id = modelo_dict[modelo_selecionado]
                        anos = get_anos(marca_id, modelo_id)
                        if anos:
                            ano_dict = {a['name']: str(a['code']) for a in anos}
                            ano_selecionado = st.selectbox("Selecione o Ano", ["Selecione..."] + list(ano_dict.keys()), key="new_ano")
                            ano_id = ano_dict[ano_selecionado] if ano_selecionado != "Selecione..." else None
                            
            if st.button("📥 Salvar Veículo na Garagem"):
                if marca_selecionada != "Selecione..." and ano_id:
                    with st.spinner("Buscando FIPE e guardando na garagem..."):
                        dados_veiculo = get_valor_fipe(marca_id, modelo_id, ano_id)
                        if dados_veiculo:
                            fipe_str = dados_veiculo['price']
                            codigo_fipe_real = dados_veiculo['codeFipe']
                            fipe_float = float(fipe_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
                            
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute('''INSERT INTO veiculos_motorista 
                                         (user_id, marca, modelo, ano, codigo_fipe, valor_fipe, fipe_str, tipo_posse, valor_aluguel_semana, valor_parcela, parcelas_restantes)
                                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                                      (username, marca_selecionada, modelo_selecionado, ano_selecionado, codigo_fipe_real, fipe_float, fipe_str,
                                       tipo_posse, valor_aluguel, valor_parcela, parcelas_restantes))
                            novo_veiculo_id = c.lastrowid
                            c.execute("UPDATE perfil_motorista SET veiculo_ativo_id=%s WHERE user_id=%s", (novo_veiculo_id, username))
                            conn.commit()
                            conn.close()
                            
                            st.success("🚗 Novo veículo adicionado com sucesso e selecionado para o cálculo!")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("Erro ao buscar a FIPE. Tente novamente.")
                else:
                    st.warning("Preencha Marca, Modelo e Ano para adicionar o veículo.")

        # BOTÃO PRINCIPAL DE AVANÇO
        st.markdown("---")
        if st.button("💾 Salvar Escolha e Avançar para Cálculos", type="primary", use_container_width=True):
            if not veiculo_escolhido_id:
                st.error("⚠️ Você precisa adicionar e selecionar um veículo na garagem para continuar!")
            else:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''UPDATE perfil_motorista SET 
                             dias_semana=%s, horas_dia=%s, km_dia=%s, veiculo_ativo_id=%s 
                             WHERE user_id=%s''', 
                          (dias_semana, horas_dia, km_dia, veiculo_escolhido_id, username))
                conn.commit()
                conn.close()
                st.success("✅ Jornada e veículo atualizados! Abrindo a Calculadora de Markup...")
                time.sleep(1.5)
                st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"
                st.rerun()

    # --- TELA 3: CALCULADORA DE MARKUP ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("⚙️ Lançamento de Custos (Markup)")
        
        v_ativo_id = perfil['veiculo_ativo_id'] if perfil else None
        if not v_ativo_id:
            st.warning("⚠️ Vá na Etapa 2, cadastre e selecione um veículo primeiro!")
            return

        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE id=%s", (v_ativo_id,))
        veiculo = c.fetchone()
        conn.close()

        if not veiculo:
            st.error("Erro: Veículo selecionado não encontrado na garagem.")
            return

        st.info(f"🚘 **Veículo em Operação:** {veiculo['marca']} {veiculo['modelo']} ({veiculo['ano']}) - FIPE: {veiculo['fipe_str']}")
            
        fipe_atual = float(veiculo['valor_fipe'])
        tipo_posse = veiculo['tipo_posse']
        dias_mensais = int(perfil['dias_semana']) * 4.33
        km_dia = float(perfil['km_dia'])

        with st.expander("📝 Custo Fixo (Rateio Anual e Mensal)", expanded=True):
            is_alugado = (tipo_posse == "Alugado")
            is_financiado = (tipo_posse == "Financiado")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                cf_ipva = st.number_input("IPVA (Total Anual R$)", value=0.0 if is_alugado else fipe_atual * 0.04, disabled=is_alugado)
                cf_licenciamento = st.number_input("Licenciamento (Total Anual R$)", value=0.0 if is_alugado else 160.0, disabled=is_alugado)
            with col_a2:
                cf_seguro_obrig = st.number_input("Seguro Obrigatório/DPVAT (Anual R$)", value=0.0 if is_alugado else 50.0, disabled=is_alugado)
                if is_alugado: cf_seguro_carro = 0.0
                else:
                    tem_seguro = st.radio("Paga Seguro Privado / Proteção Veicular?", ["Sim", "Não"])
                    cf_seguro_carro = st.number_input("Valor do Seguro (Total Anual R$)", value=2500.0) if tem_seguro == "Sim" else 0.0
                
            cf_anuais_mensalizado = (cf_ipva + cf_licenciamento + cf_seguro_obrig + cf_seguro_carro) / 12

            st.markdown("#### 🗓️ Despesas Mensais Fixas")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                cf_inss = st.number_input("Contribuição INSS / MEI (Mensal R$)", value=155.32)
                cf_internet = st.number_input("Plano de Internet Celular (Mensal R$)", value=60.0)
            
            with col_f2:
                mensalidade_carro = 0.0
                cf_aluguel_extra = 0.0
                if is_alugado:
                    mensalidade_carro = float(veiculo['valor_aluguel_semana']) * 4.33
                    cf_aluguel_extra = st.number_input("Custos Extras Locadora (Mensal R$)", value=0.0)
                elif is_financiado:
                    mensalidade_carro = st.number_input("Parcela do Financiamento (Mensal R$)", value=float(veiculo['valor_parcela']))
                
            cf_depreciacao_mensal = 0.0 if is_alugado else (fipe_atual * 0.24) / 12
            total_cf_mensal = cf_anuais_mensalizado + cf_inss + cf_internet + mensalidade_carro + cf_aluguel_extra + cf_depreciacao_mensal

        with st.expander("⛽ Custo Variável (Rotina e Operação)", expanded=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1: cv_alim_dia = st.number_input("Gasto com Alimentação (Por Dia R$)", value=30.0)
            with col_r2: cv_lavagem = st.number_input("Lavagem do Carro (Mensal R$)", value=120.0)

            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: tipo_comb = st.selectbox("Combustível", ["Gasolina", "Etanol", "GNV (m³)", "Elétrico (kWh)"])
            with col_c2: preco_comb = st.number_input("Preço na Bomba (R$)", value=5.80)
            with col_c3:
                medida = "m³" if tipo_comb == "GNV (m³)" else "kWh" if tipo_comb == "Elétrico (kWh)" else "Litro"
                consumo_comb = st.number_input(f"Faz quantos KM por {medida}?", value=10.0)
            
            cv_comb_dia = (km_dia / consumo_comb) * preco_comb if consumo_comb > 0 else 0
            cv_comb_mensal = cv_comb_dia * dias_mensais

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1: cv_manut_mensal = st.number_input("Manutenção Média (Mensal R$)", value=0.0 if is_alugado else 150.0)
            with col_m2:
                cv_oleo = st.number_input("Troca de Óleo (Por 10k KM)", value=0.0 if is_alugado else 250.0)
                cv_alinhamento = st.number_input("Alinhamento (Por 10k KM)", value=0.0 if is_alugado else 100.0)
            with col_m3: cv_pneu = st.number_input("Jogo de Pneus (Por 30k KM)", value=0.0 if is_alugado else 1600.0)

            km_mensal = km_dia * dias_mensais
            total_cv_mensal = (cv_alim_dia * dias_mensais) + cv_comb_mensal + cv_lavagem + cv_manut_mensal + \
                              (cv_oleo / 10000 * km_mensal) + (cv_alinhamento / 10000 * km_mensal) + (cv_pneu / 30000 * km_mensal)

        with st.expander("📈 Impostos e Margem (Pró-labore)", expanded=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                cp_iss = st.number_input("Imposto Municipal / Federal (%)", value=5.0)
                margem_iss = st.number_input("Sua Margem de Lucro / Pró-labore (%)", value=30.0, help="Será o seu salário livre.")
            with col_p2:
                cp_icms = st.number_input("ICMS / Outras Taxas (%)", value=0.0)

        st.markdown("---")
        if st.button("🚀 Gerar Painel de Metas e Resultados", type="primary", use_container_width=True):
            st.session_state['calc_data'] = {
                'total_cf_mensal': total_cf_mensal,
                'total_cv_mensal': total_cv_mensal,
                'cp_iss': cp_iss,
                'cp_icms': cp_icms,
                'margem_iss': margem_iss
            }
            st.success("✅ Custos processados! Construindo o seu Painel de Metas...")
            time.sleep(1.5)
            st.session_state['mudar_aba'] = "4️⃣ Painel de Metas"
            st.rerun()

    # --- TELA 4: PAINEL DE METAS (O GRANDE DESTAQUE) ---
    elif menu_opcao == "4️⃣ Painel de Metas":
        if 'calc_data' not in st.session_state or not perfil:
            st.error("⚠️ Atenção: Você precisa preencher a aba '3️⃣ Calculadora de Markup' e clicar em 'Gerar Painel' primeiro.")
            return

        dados = st.session_state['calc_data']
        horas_dia_trabalho = int(perfil['horas_dia'])
        dias_semana_trabalho = int(perfil['dias_semana'])
        km_dia = float(perfil['km_dia'])
        
        dias_mensais = dias_semana_trabalho * 4.33
        km_mensal = km_dia * dias_mensais
        horas_trabalhadas_semana = horas_dia_trabalho * dias_semana_trabalho
        horas_trabalhadas_mes = horas_dia_trabalho * dias_mensais

        cp_irpf = ((dados['total_cf_mensal'] + dados['total_cv_mensal']) * 0.60) * 0.11
        custo_base_total = dados['total_cf_mensal'] + dados['total_cv_mensal'] + cp_irpf
        
        try:
            faturamento_meta_iss = custo_base_total / (1 - (dados['cp_iss']/100) - (dados['cp_icms']/100) - (dados['margem_iss']/100))
            prolabore_real = faturamento_meta_iss * (dados['margem_iss'] / 100)
            
            custo_km = custo_base_total / km_mensal if km_mensal > 0 else 0
            custo_hora = custo_base_total / horas_trabalhadas_mes if horas_trabalhadas_mes > 0 else 0
            meta_km = faturamento_meta_iss / km_mensal if km_mensal > 0 else 0
            meta_hora = faturamento_meta_iss / horas_trabalhadas_mes if horas_trabalhadas_mes > 0 else 0

            st.markdown("<h1 style='text-align: center;'>🎯 O SEU RESUMO NA PISTA</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Este é o raio-x da sua operação. Fixe estes números na cabeça.</p>", unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("### 📋 Lembrete da Sua Jornada Planejada")
            st.info(f"⏱️ **Tempo:** {horas_dia_trabalho}h/dia | {horas_trabalhadas_semana}h/semana | {horas_trabalhadas_mes:.0f}h/mês \n\n 🛣️ **Distância:** {km_dia:.0f} km/dia | {km_mensal:.0f} km/mês")

            st.markdown("### 🚦 Custos vs. Metas (Foque no Verde)")
            
            html_cards = f"""
<div style="display: flex; gap: 20px; flex-wrap: wrap;">
<div style="flex: 1; background-color: #ffeaea; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
<h3 style="color: #d32f2f; margin-top: 0;">🔴 Custos de Operação</h3>
<p style="color: #d32f2f; font-size: 14px;">Isso é o quanto o seu carro gasta para rodar. Se ganhar isso, você empata.</p>
<h2 style="color: #d32f2f; margin-bottom: 5px;">R$ {custo_km:.2f} <span style="font-size: 16px;">/ KM</span></h2>
<h2 style="color: #d32f2f; margin-top: 0;">R$ {custo_hora:.2f} <span style="font-size: 16px;">/ Hora</span></h2>
</div>
<div style="flex: 1; background-color: #eafbee; padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
<h3 style="color: #1e7e34; margin-top: 0;">🟢 Metas de Ganho (Mínimo)</h3>
<p style="color: #1e7e34; font-size: 14px;">Isso é o mínimo que deve aceitar para atingir seu Pró-labore estipulado.</p>
<h2 style="color: #1e7e34; margin-bottom: 5px;">R$ {meta_km:.2f} <span style="font-size: 16px;">/ KM</span></h2>
<h2 style="color: #1e7e34; margin-top: 0;">R$ {meta_hora:.2f} <span style="font-size: 16px;">/ Hora</span></h2>
</div>
</div>
"""
            st.markdown(html_cards, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.error(f"🚨 **REGRA DE OURO:** Para colocar os seus **R$ {prolabore_real:.2f} limpos no bolso**, cumpra as horas acima e **NUNCA ACEITE** corridas que paguem menos de **R$ {meta_km:.2f} por KM** ou rendam menos de **R$ {meta_hora:.2f} por Hora**. Fazer menos do que isso é pagar para trabalhar!")

            st.markdown("---")
            st.markdown("### 📊 O Resumo do Seu Mês (Caixa do Carro)")
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("1. Custos da Operação", f"R$ {custo_base_total:.2f}", "Fixo + Variável + IRPF", delta_color="inverse")
            col_r2.metric("2. Meta de Faturamento Bruto", f"R$ {faturamento_meta_iss:.2f}", "O que o App tem que pagar")
            col_r3.metric("3. Seu Pró-labore (Lucro)", f"R$ {prolabore_real:.2f}", f"Margem de {dados['margem_iss']}%")

        except ZeroDivisionError:
            st.error("Erro matemático: A soma dos percentuais de imposto e margem não pode ser 100% ou maior.")

try: init_db()
except: pass

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
