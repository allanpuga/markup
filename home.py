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
                  cf_ipva FLOAT, cf_licenciamento FLOAT, cf_seguro_obrig FLOAT, cf_seguro_carro FLOAT,
                  cf_inss FLOAT, cf_internet FLOAT, cv_alim_dia FLOAT, cv_lavagem FLOAT,
                  preco_comb FLOAT, consumo_comb FLOAT, tipo_comb VARCHAR(50),
                  cv_manut_mensal FLOAT, cv_oleo FLOAT, cv_alinhamento FLOAT, cv_pneu FLOAT,
                  cp_iss FLOAT, cp_icms FLOAT, margem_iss FLOAT, UNIQUE KEY (user_id, veiculo_id))''')
    conn.commit()
    conn.close()

# --- 2. APIs EXTERNAS ---
@st.cache_data(ttl=86400)
def get_marcas():
    try: return requests.get("https://fipe.parallelum.com.br/api/v2/cars/brands", headers={'User-Agent': 'Mozilla/5.0'}).json()
    except: return []

# --- 3. LÓGICA DE ACESSO ---
def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor(dictionary=True, buffered=True)
    c.execute("SELECT * FROM usuarios WHERE (username=%s OR email=%s) AND password=%s", (username, username, password))
    user = c.fetchone()
    conn.close()
    return user

def login_page():
    st.markdown("<h1 style='text-align: center;'>🚗 Gestão Markup</h1>", unsafe_allow_html=True)
    if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.session_state['auth_mode'] == 'login':
            u = st.text_input("Usuário ou E-mail")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                user = login_user(u, p)
                if user:
                    st.session_state['logged_in'], st.session_state['username'] = True, user['username']
                    st.rerun()
                else: st.error("Acesso negado.")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Criar Conta", use_container_width=True): st.session_state['auth_mode'] = 'signup'; st.rerun()
            with c2:
                if st.button("Esqueci a Senha", use_container_width=True): st.session_state['auth_mode'] = 'reset'; st.rerun()

        elif st.session_state['auth_mode'] == 'signup':
            nu, ne, np = st.text_input("Usuário"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.button("Finalizar Cadastro", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection(); c = conn.cursor(buffered=True)
                    c.execute("INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)", (nu, ne, np))
                    conn.commit(); conn.close()
                    st.success("Cadastrado!"); st.session_state['auth_mode'] = 'login'; st.rerun()
                except: st.error("Usuário ou E-mail já existe.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

        elif st.session_state['auth_mode'] == 'reset':
            st.subheader("Recuperar Senha")
            re = st.text_input("E-mail cadastrado")
            if st.button("Enviar link", type="primary", use_container_width=True):
                st.info("Instruções enviadas se o e-mail existir.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

# --- 4. APP PRINCIPAL ---
def main_app():
    username = st.session_state['username']
    
    # Navegação com Barra de Progresso
    st.sidebar.title("Navegação")
    if 'mudar_aba' in st.session_state:
        st.session_state['menu_opcao'] = st.session_state['mudar_aba']
        del st.session_state['mudar_aba']
    
    opcoes = ["1️⃣ Meu Perfil", "2️⃣ Veículos e Jornada", "3️⃣ Calculadora de Markup", "4️⃣ Painel de Metas"]
    menu_opcao = st.sidebar.radio("Etapas:", opcoes, key="menu_opcao")
    
    idx_p = opcoes.index(menu_opcao) + 1
    st.sidebar.markdown(f"**Progresso: {idx_p}/4**")
    st.sidebar.progress(idx_p * 25)

    if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

    conn = get_db_connection()
    c = conn.cursor(dictionary=True, buffered=True)
    c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
    perfil = c.fetchone()
    conn.close()

    # --- ETAPA 1: PERFIL ---
    if menu_opcao == "1️⃣ Meu Perfil":
        st.title("👤 Configuração de Perfil")
        nome = st.text_input("Nome Completo", value=perfil['nome'] if perfil else "")
        email = st.text_input("E-mail de Contato", value=perfil['email'] if perfil else "")
        if st.button("💾 Salvar e Avançar", type="primary"):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            if perfil: c.execute("UPDATE perfil_motorista SET nome=%s, email=%s WHERE user_id=%s", (nome, email, username))
            else: c.execute("INSERT INTO perfil_motorista (user_id, nome, email, dias_semana, horas_dia, km_dia) VALUES (%s, %s, %s, 6, 8, 150)", (username, nome, email))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "2️⃣ Veículos e Jornada"; st.rerun()

    # --- ETAPA 2: GARAGEM E JORNADA ---
    elif menu_opcao == "2️⃣ Veículos e Jornada":
        st.title("🚘 Minha Garagem e Jornada")
        if not perfil: st.warning("Preencha o perfil primeiro."); return
        
        with st.container(border=True):
            st.markdown("### 🕒 Sua Rotina na Pista")
            d_sem = st.slider("Dias/Semana", 1, 7, int(perfil['dias_semana']))
            h_dia = st.slider("Horas/Dia", 1, 24, int(perfil['horas_dia']))
            k_dia = st.number_input("KM Médio/Dia", value=int(perfil['km_dia']))

        with st.container(border=True):
            st.markdown("### 🚗 Seleção de Veículo")
            conn = get_db_connection(); c = conn.cursor(dictionary=True, buffered=True)
            c.execute("SELECT * FROM veiculos_motorista WHERE user_id=%s", (username,))
            veiculos = c.fetchall(); conn.close()

            v_ativo_id = perfil['veiculo_ativo_id']
            if veiculos:
                labels = [f"{v['marca']} {v['modelo']} ({v['ano']})" for v in veiculos]
                ids = [v['id'] for v in veiculos]
                idx_ini = ids.index(v_ativo_id) if v_ativo_id in ids else 0
                sel_l = st.selectbox("Com qual veículo fará a simulação?", labels, index=idx_ini)
                v_ativo_id = ids[labels.index(sel_l)]
            else: st.info("Sua garagem está vazia.")

            with st.expander("➕ Adicionar Veículo à Garagem"):
                tipo_p = st.radio("Tipo:", ["Próprio", "Alugado", "Financiado"])
                m_sel = st.selectbox("Marca", [m['name'] for m in get_marcas()])
                mod_t = st.text_input("Modelo")
                ano_t = st.text_input("Ano")
                if st.button("📥 Cadastrar"):
                    conn = get_db_connection(); c = conn.cursor(buffered=True)
                    c.execute("INSERT INTO veiculos_motorista (user_id, marca, modelo, ano, tipo_posse, valor_fipe) VALUES (%s, %s, %s, %s, %s, 50000)", (username, m_sel, mod_t, ano_t, tipo_p))
                    c.execute("UPDATE perfil_motorista SET veiculo_ativo_id=%s WHERE user_id=%s", (c.lastrowid, username))
                    conn.commit(); conn.close(); st.rerun()

        if st.button("💾 Confirmar e Avançar", type="primary", use_container_width=True):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            c.execute("UPDATE perfil_motorista SET dias_semana=%s, horas_dia=%s, km_dia=%s, veiculo_ativo_id=%s WHERE user_id=%s", (d_sem, h_dia, k_dia, v_ativo_id, username))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"; st.rerun()

    # --- ETAPA 3: CALCULADORA (O CÉREBRO) ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("⚙️ Lançamento de Custos Operacionais")
        v_id = perfil['veiculo_ativo_id']
        if not v_id: st.error("Selecione um veículo."); return

        conn = get_db_connection(); c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE id=%s", (v_id,))
        veiculo = c.fetchone()
        c.execute("SELECT * FROM custos_operacionais WHERE user_id=%s AND veiculo_id=%s", (username, v_id))
        salvos = c.fetchone()
        conn.close()

        def val(k, d): return salvos[k] if salvos and k in salvos else d

        fipe_atual = float(veiculo['valor_fipe'])
        is_alugado = (veiculo['tipo_posse'] == "Alugado")

        with st.expander("📝 Custos Fixos e Rateios", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                ipva = st.number_input("IPVA Anual", value=val('cf_ipva', 0.0 if is_alugado else fipe_atual * 0.04))
                seguro = st.number_input("Seguro Anual", value=val('cf_seguro_carro', 0.0 if is_alugado else 2500.0))
            with col2:
                inss = st.number_input("INSS/MEI Mensal", value=val('cf_inss', 155.32))
                internet = st.number_input("Internet Mensal", value=val('cf_internet', 60.0))

        with st.expander("⛽ Custos Variáveis e Manutenção", expanded=True):
            col3, col4 = st.columns(2)
            with col3:
                p_comb = st.number_input("Preço Combustível", value=val('preco_comb', 5.80))
                cons = st.number_input("Consumo (KM/L)", value=val('consumo_comb', 10.0))
            with col4:
                alim = st.number_input("Alimentação/Dia", value=val('cv_alim_dia', 30.0))
                manut = st.number_input("Manutenção Mês", value=val('cv_manut_mensal', 0.0 if is_alugado else 150.0))

        with st.expander("📈 Impostos e Margem", expanded=True):
            margem = st.number_input("Margem de Lucro %", value=val('margem_iss', 30.0))
            iss = st.number_input("Impostos %", value=val('cp_iss', 5.0))

        if st.button("🚀 Gerar Painel de Metas", type="primary", use_container_width=True):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            sql = '''REPLACE INTO custos_operacionais (user_id, veiculo_id, cf_ipva, cf_seguro_carro, cf_inss, cf_internet, 
                     preco_comb, consumo_comb, cv_alim_dia, cv_manut_mensal, margem_iss, cp_iss) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            c.execute(sql, (username, v_id, ipva, seguro, inss, internet, p_comb, cons, alim, manut, margem, iss))
            conn.commit(); conn.close()
            
            # Cálculos Técnicos (O Cérebro)
            dias_m = int(perfil['dias_semana']) * 4.33
            km_m = float(perfil['km_dia']) * dias_m
            
            c_fixo_m = (ipva + seguro + 160 + 50) / 12 + inss + internet + (0 if is_alugado else (fipe_atual * 0.24)/12)
            c_var_m = (km_m / cons * p_comb) + (alim * dias_m) + manut + (120 if not is_alugado else 0)
            
            st.session_state['calc_data'] = {'cf': c_fixo_m, 'cv': c_var_m, 'margem': margem, 'iss': iss, 'km_m': km_m, 'h_m': int(perfil['horas_dia']) * dias_m}
            st.session_state['mudar_aba'] = "4️⃣ Painel de Metas"; st.rerun()

    # --- ETAPA 4: PAINEL DE METAS ---
    elif menu_opcao == "4️⃣ Painel de Metas":
        if 'calc_data' not in st.session_state: st.error("Calcule primeiro."); return
        d = st.session_state['calc_data']
        
        cp_irpf = ((d['cf'] + d['cv']) * 0.60) * 0.11
        custo_base = d['cf'] + d['cv'] + cp_irpf
        faturamento = custo_base / (1 - (d['iss']/100) - (d['margem']/100))
        lucro = faturamento * (d['margem']/100)
        
        st.markdown(f"<h1 style='text-align: center;'>🎯 Meta Mensal: R$ {faturamento:.2f}</h1>", unsafe_allow_html=True)
        
        html_cards = f"""
        <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
            <div style="flex: 1; min-width: 280px; background-color: #ffeaea; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
                <h3 style="color: #d32f2f;">🔴 Custos + Impostos</h3>
                <h2>R$ {custo_base:.2f}</h2>
            </div>
            <div style="flex: 1; min-width: 280px; background-color: #eafbee; padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
                <h3 style="color: #1e7e34;">🟢 Seu Lucro (Pró-labore)</h3>
                <h2>R$ {lucro:.2f}</h2>
            </div>
        </div>
        """
        st.markdown(html_cards, unsafe_allow_html=True)
        
        st.info(f"🛣️ **Meta por KM:** R$ {faturamento/d['km_m']:.2f} | ⏱️ **Meta por Hora:** R$ {faturamento/d['h_m']:.2f}")
        st.error(f"🚨 **Regra de Ouro:** Para garantir seu lucro de R$ {lucro:.2f}, nunca aceite corridas abaixo de R$ {faturamento/d['km_m']:.2f}/KM.")

# --- EXECUÇÃO ---
init_db()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
