import streamlit as st
import mysql.connector
import requests
import time

# --- 1. CONFIGURAÇÃO DE CONEXÃO ---
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
    # Usuários (com E-mail para recuperação)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INT AUTO_INCREMENT PRIMARY KEY, 
                  username VARCHAR(255) UNIQUE, 
                  password VARCHAR(255),
                  email VARCHAR(255) UNIQUE)''')
    
    # Perfil
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  estado VARCHAR(50), cidade VARCHAR(255), whatsapp VARCHAR(50), 
                  dias_semana INT, horas_dia INT, km_dia FLOAT, veiculo_ativo_id INT)''')
                  
    # Garagem
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), 
                  marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), 
                  codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50),
                  tipo_posse VARCHAR(50), valor_aluguel_semana FLOAT, valor_parcela FLOAT, parcelas_restantes INT)''')

    # Memória de Custos
    c.execute('''CREATE TABLE IF NOT EXISTS custos_operacionais (
                  id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), veiculo_id INT,
                  cf_ipva FLOAT, cf_licenciamento FLOAT, cf_seguro_obrig FLOAT, cf_seguro_carro FLOAT,
                  cf_inss FLOAT, cf_internet FLOAT, cv_alim_dia FLOAT, cv_lavagem FLOAT,
                  preco_comb FLOAT, consumo_comb FLOAT, tipo_comb VARCHAR(50),
                  cv_manut_mensal FLOAT, cv_oleo FLOAT, cv_alinhamento FLOAT, cv_pneu FLOAT,
                  cp_iss FLOAT, cp_icms FLOAT, margem_iss FLOAT, UNIQUE KEY (user_id, veiculo_id))''')
    conn.commit()
    conn.close()

# --- 2. APIs EXTERNAS (FIPE E IBGE) ---
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

# --- 3. LÓGICA DE AUTENTICAÇÃO ---
def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM usuarios WHERE (username=%s OR email=%s) AND password=%s", (username, username, password))
    user = c.fetchone()
    conn.close()
    return user

# --- 4. TELAS DE ACESSO (LOGIN/CADASTRO/RESET) ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🚗 Gestão Markup</h1>", unsafe_allow_html=True)
    
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    col_center, _ = st.columns([2, 1])
    
    with col_center:
        # TELA DE LOGIN
        if st.session_state['auth_mode'] == 'login':
            st.subheader("Acesse sua conta")
            u_input = st.text_input("Usuário ou E-mail")
            p_input = st.text_input("Senha", type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Entrar", type="primary", use_container_width=True):
                    user = login_user(u_input, p_input)
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user['username']
                        st.rerun()
                    else: st.error("Acesso negado.")
            with c2:
                if st.button("Criar Conta", use_container_width=True):
                    st.session_state['auth_mode'] = 'signup'; st.rerun()
            
            st.button("Esqueci minha senha", on_click=lambda: st.session_state.update({'auth_mode': 'reset'}))
            
            st.markdown("---")
            st.markdown("""
                <button style='width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; background: white; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;'>
                    <img src='https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png' width='20px'>
                    Entrar com Google (Simulado)
                </button>
            """, unsafe_allow_html=True)

        # TELA DE CADASTRO
        elif st.session_state['auth_mode'] == 'signup':
            st.subheader("Novo Cadastro")
            nu = st.text_input("Usuário desejado")
            ne = st.text_input("E-mail real")
            np = st.text_input("Senha", type="password")
            if st.button("Cadastrar", type="primary"):
                try:
                    conn = get_db_connection(); c = conn.cursor()
                    c.execute("INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)", (nu, ne, np))
                    conn.commit(); conn.close()
                    st.success("Sucesso! Faça login.")
                    st.session_state['auth_mode'] = 'login'; st.rerun()
                except: st.error("Usuário ou e-mail já em uso.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

        # TELA DE RECUPERAÇÃO
        elif st.session_state['auth_mode'] == 'reset':
            st.subheader("Recuperar Senha")
            re = st.text_input("Digite seu e-mail cadastrado")
            if st.button("Enviar Instruções"):
                st.info(f"Se o e-mail {re} estiver no sistema, você receberá um link em breve.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

# --- 5. APLICATIVO PRINCIPAL ---
def main_app():
    username = st.session_state['username']
    st.sidebar.title("Navegação")
    if 'mudar_aba' in st.session_state:
        st.session_state['menu_opcao'] = st.session_state['mudar_aba']
        del st.session_state['mudar_aba']
    
    menu_opcao = st.sidebar.radio("Etapas:", ["1️⃣ Meu Perfil", "2️⃣ Veículos e Jornada", "3️⃣ Calculadora de Markup", "4️⃣ Painel de Metas"], key="menu_opcao")
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False; st.rerun()

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
    perfil = c.fetchone()
    conn.close()

    # --- ETAPA 1: PERFIL ---
    if menu_opcao == "1️⃣ Meu Perfil":
        st.title("👤 Meu Perfil")
        nome = st.text_input("Nome Completo", value=perfil['nome'] if perfil else "")
        email = st.text_input("E-mail para Contato", value=perfil['email'] if perfil else "")
        if st.button("💾 Salvar e Próximo"):
            conn = get_db_connection(); c = conn.cursor()
            if perfil: c.execute("UPDATE perfil_motorista SET nome=%s, email=%s WHERE user_id=%s", (nome, email, username))
            else: c.execute("INSERT INTO perfil_motorista (user_id, nome, email, dias_semana, horas_dia, km_dia) VALUES (%s, %s, %s, 6, 8, 150)", (username, nome, email))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "2️⃣ Veículos e Jornada"; st.rerun()

    # --- ETAPA 2: GARAGEM ---
    elif menu_opcao == "2️⃣ Veículos e Jornada":
        st.title("🚘 Minha Garagem")
        if not perfil: st.warning("Preencha o perfil primeiro."); return
        
        d_sem = st.slider("Dias de Trabalho/Semana", 1, 7, int(perfil['dias_semana']))
        k_dia = st.number_input("KM Médio/Dia", value=int(perfil['km_dia']))
        
        conn = get_db_connection(); c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE user_id=%s", (username,))
        veiculos = c.fetchall(); conn.close()

        v_ativo = perfil['veiculo_ativo_id']
        if veiculos:
            labels = [f"{v['marca']} {v['modelo']}" for v in veiculos]
            ids = [v['id'] for v in veiculos]
            idx = ids.index(v_ativo) if v_ativo in ids else 0
            escolha = st.selectbox("Veículo que vai para a pista hoje:", labels, index=idx)
            v_ativo = ids[labels.index(escolha)]

        with st.expander("➕ Adicionar Novo Veículo"):
            m_list = get_marcas()
            m_sel = st.selectbox("Marca", [m['name'] for m in m_list])
            if st.button("Cadastrar Veículo"):
                conn = get_db_connection(); c = conn.cursor()
                c.execute("INSERT INTO veiculos_motorista (user_id, marca, modelo, valor_fipe) VALUES (%s, %s, 'Modelo Padrão', 50000)", (username, m_sel))
                conn.commit(); conn.close(); st.rerun()

        if st.button("💾 Salvar Escolha"):
            conn = get_db_connection(); c = conn.cursor()
            c.execute("UPDATE perfil_motorista SET dias_semana=%s, km_dia=%s, veiculo_ativo_id=%s WHERE user_id=%s", (d_sem, k_dia, v_ativo, username))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"; st.rerun()

    # --- ETAPA 3: CALCULADORA ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("⚙️ Lançamento de Custos")
        v_id = perfil['veiculo_ativo_id']
        if not v_id: st.error("Selecione um veículo na Etapa 2."); return

        conn = get_db_connection(); c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM custos_operacionais WHERE user_id=%s AND veiculo_id=%s", (username, v_id))
        custos = c.fetchone(); conn.close()

        def val(k, d): return custos[k] if custos and k in custos else d

        c1, c2 = st.columns(2)
        with c1:
            p_comb = st.number_input("Preço Combustível", value=val('preco_comb', 5.80))
            margem = st.number_input("Sua Margem %", value=val('margem_iss', 30.0))
        with c2:
            cons = st.number_input("KM/L", value=val('consumo_comb', 10.0))
            inss = st.number_input("INSS Mensal", value=val('cf_inss', 155.32))

        if st.button("🚀 Gerar Resultados", type="primary"):
            conn = get_db_connection(); c = conn.cursor()
            sql = "REPLACE INTO custos_operacionais (user_id, veiculo_id, preco_comb, margem_iss, consumo_comb, cf_inss) VALUES (%s, %s, %s, %s, %s, %s)"
            c.execute(sql, (username, v_id, p_comb, margem, cons, inss))
            conn.commit(); conn.close()
            
            km_mes = float(perfil['km_dia']) * int(perfil['dias_semana']) * 4.33
            comb_mes = (km_mes / cons) * p_comb
            total_custo = comb_mes + inss
            
            st.session_state['calc_data'] = {'total': total_custo, 'margem': margem, 'km_mes': km_mes}
            st.session_state['mudar_aba'] = "4️⃣ Painel de Metas"; st.rerun()

    # --- ETAPA 4: RESULTADOS ---
    elif menu_opcao == "4️⃣ Painel de Metas":
        if 'calc_data' not in st.session_state: st.error("Calcule os custos primeiro."); return
        d = st.session_state['calc_data']
        faturamento = d['total'] / (1 - (d['margem']/100))
        lucro = faturamento - d['total']

        st.markdown(f"<h1 style='text-align: center;'>Meta Mensal: R$ {faturamento:.2f}</h1>", unsafe_allow_html=True)
        
        # Cards Responsivos
        html = f"""
        <div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center;">
            <div style="flex: 1; min-width: 280px; background-color: #ffeaea; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
                <h3 style="color: #d32f2f;">🔴 Custos de Operação</h3>
                <h2 style="color: #d32f2f;">R$ {d['total']:.2f}</h2>
            </div>
            <div style="flex: 1; min-width: 280px; background-color: #eafbee; padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
                <h3 style="color: #1e7e34;">🟢 Seu Lucro Líquido</h3>
                <h2 style="color: #1e7e34;">R$ {lucro:.2f}</h2>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        st.info(f"Para sobrar R$ {lucro:.2f} no seu bolso, você precisa faturar R$ {faturamento:.2f} no mês.")

# --- EXECUÇÃO PRINCIPAL ---
init_db()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
