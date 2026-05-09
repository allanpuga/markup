import streamlit as st
import mysql.connector
import requests
import time
import pandas as pd

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
    c = conn.cursor(buffered=True)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE, password VARCHAR(255), email VARCHAR(255) UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  estado VARCHAR(50), cidade VARCHAR(255), whatsapp VARCHAR(50), 
                  dias_semana INT, horas_dia INT, km_dia FLOAT, veiculo_ativo_id INT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), 
                  marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), 
                  codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50),
                  tipo_posse VARCHAR(50), valor_aluguel_semana FLOAT, valor_parcela FLOAT, parcelas_restantes INT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custos_operacionais (
                  id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), veiculo_id INT,
                  cf_inss FLOAT, preco_comb FLOAT, consumo_comb FLOAT, margem_iss FLOAT, UNIQUE KEY (user_id, veiculo_id))''')
    conn.commit()
    conn.close()

# --- 2. APIs EXTERNAS ---
@st.cache_data(ttl=86400)
def get_marcas():
    try: return requests.get("https://fipe.parallelum.com.br/api/v2/cars/brands", headers={'User-Agent': 'Mozilla/5.0'}).json()
    except: return []

# --- 3. TELAS DE ACESSO ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🚗 Gestão Markup</h1>", unsafe_allow_html=True)
    if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.session_state['auth_mode'] == 'login':
            u = st.text_input("Usuário ou E-mail")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                conn = get_db_connection()
                c = conn.cursor(dictionary=True, buffered=True)
                c.execute("SELECT * FROM usuarios WHERE (username=%s OR email=%s) AND password=%s", (u, u, p))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['logged_in'], st.session_state['username'] = True, user['username']
                    st.rerun()
                else: st.error("Acesso negado.")
            if st.button("Criar Nova Conta"): st.session_state['auth_mode'] = 'signup'; st.rerun()
        
        elif st.session_state['auth_mode'] == 'signup':
            nu, ne, np = st.text_input("Usuário"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.button("Cadastrar"):
                try:
                    conn = get_db_connection(); c = conn.cursor(buffered=True)
                    c.execute("INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)", (nu, ne, np))
                    conn.commit(); conn.close()
                    st.success("Cadastrado!"); st.session_state['auth_mode'] = 'login'; st.rerun()
                except: st.error("Erro no cadastro.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

# --- 4. APP PRINCIPAL ---
def main_app():
    username = st.session_state['username']
    
    # Barra Lateral com Progresso
    st.sidebar.title("Navegação")
    if 'mudar_aba' in st.session_state:
        st.session_state['menu_opcao'] = st.session_state['mudar_aba']
        del st.session_state['mudar_aba']
    
    opcoes = ["1️⃣ Meu Perfil", "2️⃣ Veículos e Jornada", "3️⃣ Calculadora de Markup", "4️⃣ Painel de Metas"]
    menu_opcao = st.sidebar.radio("Etapas:", opcoes, key="menu_opcao")
    
    # Indicador de Progresso
    idx_progresso = opcoes.index(menu_opcao) + 1
    st.sidebar.markdown(f"**Progresso: {idx_progresso}/4**")
    st.sidebar.progress(idx_progresso * 25)

    if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

    conn = get_db_connection()
    c = conn.cursor(dictionary=True, buffered=True)
    c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
    perfil = c.fetchone()
    conn.close()

    # --- TELA 1: PERFIL ---
    if menu_opcao == "1️⃣ Meu Perfil":
        st.title("👤 Meu Perfil")
        nome = st.text_input("Nome", value=perfil['nome'] if perfil else "")
        email = st.text_input("E-mail", value=perfil['email'] if perfil else "")
        if st.button("💾 Salvar e Continuar", type="primary"):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            if perfil: c.execute("UPDATE perfil_motorista SET nome=%s, email=%s WHERE user_id=%s", (nome, email, username))
            else: c.execute("INSERT INTO perfil_motorista (user_id, nome, email, dias_semana, horas_dia, km_dia) VALUES (%s, %s, %s, 6, 8, 150)", (username, nome, email))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "2️⃣ Veículos e Jornada"; st.rerun()

    # --- TELA 2: GARAGEM ---
    elif menu_opcao == "2️⃣ Veículos e Jornada":
        st.title("🚘 Minha Garagem")
        if not perfil: st.warning("Complete o perfil."); return
        d_sem = st.slider("Dias/Semana", 1, 7, int(perfil['dias_semana']))
        k_dia = st.number_input("KM Médio/Dia", value=int(perfil['km_dia']))
        
        conn = get_db_connection(); c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE user_id=%s", (username,))
        veiculos = c.fetchall(); conn.close()

        v_ativo = perfil['veiculo_ativo_id']
        if veiculos:
            escolha = st.selectbox("Veículo Ativo:", [f"{v['marca']} {v['modelo']}" for v in veiculos])
            v_ativo = veiculos[[f"{v['marca']} {v['modelo']}" for v in veiculos].index(escolha)]['id']

        with st.expander("➕ Novo Veículo"):
            m = st.selectbox("Marca", [ma['name'] for ma in get_marcas()])
            if st.button("Cadastrar"):
                conn = get_db_connection(); c = conn.cursor(buffered=True)
                c.execute("INSERT INTO veiculos_motorista (user_id, marca, modelo, valor_fipe) VALUES (%s, %s, 'Padrao', 50000)", (username, m))
                conn.commit(); conn.close(); st.rerun()

        if st.button("💾 Confirmar e Avançar", type="primary"):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            c.execute("UPDATE perfil_motorista SET dias_semana=%s, km_dia=%s, veiculo_ativo_id=%s WHERE user_id=%s", (d_sem, k_dia, v_ativo, username))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"; st.rerun()

    # --- TELA 3: CALCULADORA ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("⚙️ Lançamento de Custos")
        v_id = perfil['veiculo_ativo_id']
        if not v_id: st.error("Selecione um veículo na Etapa 2."); return

        conn = get_db_connection(); c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM custos_operacionais WHERE user_id=%s AND veiculo_id=%s", (username, v_id))
        salvos = c.fetchone(); conn.close()

        def val(k, p): return salvos[k] if salvos and k in salvos else p

        p_comb = st.number_input("Preço Combustível", value=val('preco_comb', 5.80))
        cons = st.number_input("Consumo (KM/L)", value=val('consumo_comb', 10.0))
        margem = st.number_input("Margem de Lucro %", value=val('margem_iss', 30.0))
        inss = st.number_input("Custos Fixos/INSS", value=val('cf_inss', 155.32))

        if st.button("🚀 Gerar Resultados", type="primary"):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            c.execute("REPLACE INTO custos_operacionais (user_id, veiculo_id, preco_comb, margem_iss, consumo_comb, cf_inss) VALUES (%s, %s, %s, %s, %s, %s)", (username, v_id, p_comb, margem, cons, inss))
            conn.commit(); conn.close()
            
            km_mes = float(perfil['km_dia']) * int(perfil['dias_semana']) * 4.33
            custo_total = (km_mes / cons) * p_comb + inss
            st.session_state['calc_data'] = {'total': custo_total, 'margem': margem, 'km_mes': km_mes, 'horas': int(perfil['horas_dia'])}
            st.session_state['mudar_aba'] = "4️⃣ Painel de Metas"; st.rerun()

    # --- TELA 4: PAINEL DE METAS ---
    elif menu_opcao == "4️⃣ Painel de Metas":
        if 'calc_data' not in st.session_state: st.error("Calcule primeiro."); return
        d = st.session_state['calc_data']
        faturamento = d['total'] / (1 - (d['margem']/100))
        lucro = faturamento - d['total']

        st.markdown(f"<h1 style='text-align: center;'>Meta Mensal: R$ {faturamento:.2f}</h1>", unsafe_allow_html=True)
        
        # Gráfico de Pizza
        df_chart = pd.DataFrame({'Categoria': ['Custos', 'Lucro'], 'Valor': [d['total'], lucro]})
        st.write("### 📊 Divisão do Faturamento")
        st.pie_chart(df_chart, x='Categoria', y='Valor')

        # Cards Responsivos
        html_cards = f"""
        <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
            <div style="flex: 1; min-width: 280px; background-color: #ffeaea; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
                <h3 style="color: #d32f2f;">🔴 Custos Totais</h3>
                <h2>R$ {d['total']:.2f}</h2>
            </div>
            <div style="flex: 1; min-width: 280px; background-color: #eafbee; padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
                <h3 style="color: #1e7e34;">🟢 Seu Lucro Líquido</h3>
                <h2>R$ {lucro:.2f}</h2>
            </div>
        </div>
        """
        st.markdown(html_cards, unsafe_allow_html=True)
        
        # Texto para WhatsApp
        msg_zap = f"Minha Meta no App:\nFaturamento: R$ {faturamento:.2f}\nCustos: R$ {d['total']:.2f}\nLucro Limpo: R$ {lucro:.2f}"
        st.text_area("Copiando para o WhatsApp:", msg_zap)
        st.info("💡 Dica: Mantenha sua meta fixa por hora em R$ {:.2f}".format(faturamento / (d['horas'] * 25)))

# --- EXECUÇÃO ---
init_db()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
