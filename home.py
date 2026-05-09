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
    # Usuários (Com e-mail para recuperação)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE, password VARCHAR(255), email VARCHAR(255) UNIQUE)''')
    
    # Perfil do Motorista
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  estado VARCHAR(50), cidade VARCHAR(255), whatsapp VARCHAR(50), 
                  dias_semana INT, horas_dia INT, km_dia FLOAT, veiculo_ativo_id INT)''')
                  
    # Garagem (Estrutura Completa)
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), 
                  marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), 
                  codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50),
                  tipo_posse VARCHAR(50), valor_aluguel_semana FLOAT, valor_parcela FLOAT, parcelas_restantes INT)''')

    # Memória de Custos Técnicos (Unificada)
    c.execute('''CREATE TABLE IF NOT EXISTS custos_operacionais (
                  id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), veiculo_id INT,
                  cf_ipva FLOAT, cf_licenciamento FLOAT, cf_seguro_obrig FLOAT, cf_seguro_carro FLOAT,
                  cf_inss FLOAT, cf_internet FLOAT, cv_alim_dia FLOAT, cv_lavagem FLOAT,
                  preco_comb FLOAT, consumo_comb FLOAT, tipo_comb VARCHAR(50),
                  cv_manut_mensal FLOAT, cv_oleo FLOAT, cv_alinhamento FLOAT, cv_pneu FLOAT,
                  cp_iss FLOAT, cp_icms FLOAT, margem_iss FLOAT, UNIQUE KEY (user_id, veiculo_id))''')
    conn.commit()
    conn.close()

# --- 2. APIs DE APOIO ---
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
            if st.button("Cadastrar", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection(); c = conn.cursor(buffered=True)
                    c.execute("INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)", (nu, ne, np))
                    conn.commit(); conn.close()
                    st.success("Cadastrado!"); st.session_state['auth_mode'] = 'login'; st.rerun()
                except: st.error("Erro: Usuário ou E-mail já existe.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

        elif st.session_state['auth_mode'] == 'reset':
            st.subheader("Recuperar Senha")
            re = st.text_input("Digite seu e-mail cadastrado")
            if st.button("Enviar link", type="primary", use_container_width=True):
                st.info("Se cadastrado, você receberá um e-mail em breve.")
            st.button("Voltar", on_click=lambda: st.session_state.update({'auth_mode': 'login'}))

# --- 4. APP PRINCIPAL ---
def main_app():
    username = st.session_state['username']
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
        p_nome = perfil['nome'] if perfil else ""
        p_email = perfil['email'] if perfil else ""
        p_estado = perfil['estado'] if perfil else "Selecione..."
        p_cidade = perfil['cidade'] if perfil else "Selecione..."

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo", value=p_nome)
            email = st.text_input("E-mail de Contato", value=p_email)
        with col2:
            estados = get_estados()
            lista_est = ["Selecione..."] + [f"{s} - {n}" for s, n in estados.items()]
            idx_e = [i for i, x in enumerate(lista_est) if p_estado in x][0] if p_estado != "Selecione..." else 0
            estado_sel = st.selectbox("Estado", options=lista_est, index=idx_e)
            
            cidade_sel = "Selecione..."
            if estado_sel != "Selecione...":
                uf = estado_sel.split(" - ")[0]
                cidades = ["Selecione..."] + get_cidades(uf)
                idx_c = cidades.index(p_cidade) if p_cidade in cidades else 0
                cidade_sel = st.selectbox("Cidade", options=cidades, index=idx_c)

        if st.button("💾 Salvar e Continuar", type="primary"):
            uf_save = estado_sel.split(" - ")[0] if estado_sel != "Selecione..." else ""
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            if perfil: c.execute("UPDATE perfil_motorista SET nome=%s, email=%s, estado=%s, cidade=%s WHERE user_id=%s", (nome, email, uf_save, cidade_sel, username))
            else: c.execute("INSERT INTO perfil_motorista (user_id, nome, email, estado, cidade, dias_semana, horas_dia, km_dia) VALUES (%s, %s, %s, %s, %s, 6, 8, 150)", (username, nome, email, uf_save, cidade_sel))
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
                labels = [f"{v['marca']} {v['modelo']} ({v['ano']}) - {v['tipo_posse']}" for v in veiculos]
                ids = [v['id'] for v in veiculos]
                idx_ini = ids.index(v_ativo_id) if v_ativo_id in ids else 0
                sel_v = st.selectbox("Com qual veículo fará a simulação?", labels, index=idx_ini)
                v_ativo_id = ids[labels.index(sel_v)]
            else: st.info("Sua garagem está vazia.")

            with st.expander("➕ Adicionar Novo Veículo"):
                tipo_p = st.radio("Tipo de Posse:", ["Próprio", "Alugado", "Financiado"])
                aluguel_sem, parcela_mens, prest_rest = 0.0, 0.0, 0
                if tipo_p == "Alugado": aluguel_sem = st.number_input("Aluguel Semanal")
                elif tipo_p == "Financiado":
                    parcela_mens = st.number_input("Parcela Mensal")
                    prest_rest = st.number_input("Prestações Restantes", min_value=0)
                
                marcas = get_marcas()
                m_sel = st.selectbox("Marca", ["Selecione..."] + [m['name'] for m in marcas])
                if m_sel != "Selecione...":
                    m_id = [m['code'] for m in marcas if m['name'] == m_sel][0]
                    modelos = get_modelos(m_id)
                    mod_sel = st.selectbox("Modelo", ["Selecione..."] + [mo['name'] for mo in modelos])
                    if mod_sel != "Selecione...":
                        mo_id = [mo['code'] for mo in modelos if mo['name'] == mod_sel][0]
                        anos = get_anos(m_id, mo_id)
                        ano_sel = st.selectbox("Ano", ["Selecione..."] + [a['name'] for a in anos])
                        if st.button("📥 Cadastrar e Selecionar"):
                            a_id = [a['code'] for a in anos if a['name'] == ano_sel][0]
                            f = get_valor_fipe(m_id, mo_id, a_id)
                            f_val = float(f['price'].replace('R$', '').replace('.', '').replace(',', '.').strip())
                            conn = get_db_connection(); c = conn.cursor(buffered=True)
                            c.execute('''INSERT INTO veiculos_motorista (user_id, marca, modelo, ano, codigo_fipe, valor_fipe, fipe_str, tipo_posse, valor_aluguel_semana, valor_parcela, parcelas_restantes) 
                                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', 
                                      (username, m_sel, mod_sel, ano_sel, f['codeFipe'], f_val, f['price'], tipo_p, aluguel_sem, parcela_mens, prest_rest))
                            c.execute("UPDATE perfil_motorista SET veiculo_ativo_id=%s WHERE user_id=%s", (c.lastrowid, username))
                            conn.commit(); conn.close(); st.rerun()

        if st.button("💾 Confirmar e Avançar", type="primary", use_container_width=True):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            c.execute("UPDATE perfil_motorista SET dias_semana=%s, horas_dia=%s, km_dia=%s, veiculo_ativo_id=%s WHERE user_id=%s", (d_sem, h_dia, k_dia, v_ativo_id, username))
            conn.commit(); conn.close()
            st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"; st.rerun()

    # --- ETAPA 3: CALCULADORA (CÉREBRO TÉCNICO COM MEMÓRIA) ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("⚙️ Lançamento de Custos Técnicos")
        v_id = perfil['veiculo_ativo_id']
        if not v_id: st.error("Selecione um veículo."); return

        conn = get_db_connection(); c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE id=%s", (v_id,))
        veiculo = c.fetchone()
        c.execute("SELECT * FROM custos_operacionais WHERE user_id=%s AND veiculo_id=%s", (username, v_id))
        salvos = c.fetchone()
        conn.close()

        def val(k, d): return salvos[k] if salvos and k in salvos else d

        fipe_v = float(veiculo['valor_fipe'])
        is_al = (veiculo['tipo_posse'] == "Alugado")

        with st.expander("📝 Custos Fixos e Mensalidades", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                ipva = st.number_input("IPVA Anual (R$)", value=val('cf_ipva', 0.0 if is_al else fipe_v * 0.04), disabled=is_al)
                licenc = st.number_input("Licenciamento Anual (R$)", value=val('cf_licenciamento', 0.0 if is_al else 160.0), disabled=is_al)
                seg_p = st.number_input("Seguro Privado Anual (R$)", value=val('cf_seguro_carro', 0.0 if is_al else 2500.0), disabled=is_al)
            with col2:
                inss = st.number_input("INSS/MEI Mensal (R$)", value=val('cf_inss', 155.32))
                internet = st.number_input("Internet Mensal (R$)", value=val('cf_internet', 60.0))
                deprec = 0.0 if is_al else (fipe_v * 0.24) / 12
                st.write(f"Depreciação Mensal (24% aa): R$ {deprec:.2f}")

        with st.expander("⛽ Operação Diária e Variáveis", expanded=True):
            col3, col4, col5 = st.columns(3)
            with col3:
                p_comb = st.number_input("Preço Combustível (R$)", value=val('preco_comb', 5.80))
                cons = st.number_input("Consumo (KM/L)", value=val('consumo_comb', 10.0))
            with col4:
                alim = st.number_input("Alimentação Dia (R$)", value=val('cv_alim_dia', 30.0))
                lavagem = st.number_input("Lavagem Mês (R$)", value=val('cv_lavagem', 120.0))
            with col5:
                manut_m = st.number_input("Manutenção/Reserva Mês (R$)", value=val('cv_manut_mensal', 0.0 if is_al else 150.0))
                oleo = st.number_input("Óleo (por 10k KM)", value=val('cv_oleo', 0.0 if is_al else 250.0))
                pneu = st.number_input("Pneus (por 30k KM)", value=val('cv_pneu', 0.0 if is_al else 1600.0))

        with st.expander("📈 Margem e Impostos", expanded=True):
            col6, col7 = st.columns(2)
            with col6: margem = st.number_input("Sua Margem %", value=val('margem_iss', 30.0))
            with col7: iss = st.number_input("Imposto/Taxa %", value=val('cp_iss', 5.0))

        if st.button("🚀 Gerar Resultados de Markup", type="primary", use_container_width=True):
            conn = get_db_connection(); c = conn.cursor(buffered=True)
            sql = '''REPLACE INTO custos_operacionais (user_id, veiculo_id, cf_ipva, cf_licenciamento, cf_seguro_carro, cf_inss, cf_internet, cv_alim_dia, cv_lavagem, preco_comb, consumo_comb, cv_manut_mensal, cv_oleo, cv_pneu, margem_iss, cp_iss) 
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            c.execute(sql, (username, v_id, ipva, licenc, seg_p, inss, internet, alim, lavagem, p_comb, cons, manut_m, oleo, pneu, margem, iss))
            conn.commit(); conn.close()
            
            dias_m = int(perfil['dias_semana']) * 4.33
            km_m = float(perfil['km_dia']) * dias_m
            
            # Rateios Mensais
            cf_m = (ipva + licenc + seg_p + 50) / 12 + inss + internet + deprec
            if veiculo['tipo_posse'] == "Alugado": cf_m += float(veiculo['valor_aluguel_semana']) * 4.33
            elif veiculo['tipo_posse'] == "Financiado": cf_m += float(veiculo['valor_parcela'])
            
            cv_m = (km_m / cons * p_comb) + (alim * dias_m) + lavagem + manut_m + (oleo/10000 * km_m) + (pneu/30000 * km_m)
            
            st.session_state['calc_data'] = {'cf': cf_m, 'cv': cv_m, 'margem': margem, 'iss': iss, 'km_m': km_m, 'h_m': int(perfil['horas_dia']) * dias_m}
            st.session_state['mudar_aba'] = "4️⃣ Painel de Metas"; st.rerun()

    # --- ETAPA 4: PAINEL DE METAS (REGRA DE OURO) ---
    elif menu_opcao == "4️⃣ Painel de Metas":
        if 'calc_data' not in st.session_state: st.error("Calcule os custos primeiro."); return
        d = st.session_state['calc_data']
        
        # Fórmula Profissional: Custo Base + IRPF (60% receita * 11% taxa)
        cp_irpf = ((d['cf'] + d['cv']) * 0.60) * 0.11
        custo_base_total = d['cf'] + d['cv'] + cp_irpf
        
        faturamento_meta = custo_base_total / (1 - (d['iss']/100) - (d['margem']/100))
        lucro_prolabore = faturamento_meta * (d['margem']/100)
        
        st.markdown("<h1 style='text-align: center;'>🎯 O SEU RESUMO NA PISTA</h1>", unsafe_allow_html=True)
        st.info(f"⏱️ **Jornada Mensal:** {d['h_m']:.0f} horas | 🛣️ **Distância Mensal:** {d['km_m']:.0f} KM")

        html_cards = f"""
        <div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center;">
            <div style="flex: 1; min-width: 280px; background-color: #ffeaea; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
                <h3 style="color: #d32f2f; margin-top: 0;">🔴 Custos de Operação</h3>
                <h2 style="color: #d32f2f; margin-bottom: 5px;">R$ {custo_base_total/d['km_m']:.2f} <span style="font-size: 16px;">/ KM</span></h2>
                <h2 style="color: #d32f2f; margin-top: 0;">R$ {custo_base_total/d['h_m']:.2f} <span style="font-size: 16px;">/ Hora</span></h2>
            </div>
            <div style="flex: 1; min-width: 280px; background-color: #eafbee; padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
                <h3 style="color: #1e7e34; margin-top: 0;">🟢 Metas de Ganho</h3>
                <h2 style="color: #1e7e34; margin-bottom: 5px;">R$ {faturamento_meta/d['km_m']:.2f} <span style="font-size: 16px;">/ KM</span></h2>
                <h2 style="color: #1e7e34; margin-top: 0;">R$ {faturamento_meta/d['h_m']:.2f} <span style="font-size: 16px;">/ Hora</span></h2>
            </div>
        </div>
        """
        st.markdown(html_cards, unsafe_allow_html=True)
        
        st.error(f"🚨 **REGRA DE OURO:** Para colocar **R$ {lucro_prolabore:.2f} limpos** no bolso, nunca aceite corridas abaixo de **R$ {faturamento_meta/d['km_m']:.2f}/KM**.")
        
        st.info(f"**Matemática do Mês:** Custo Base R$ {custo_base_total:.2f} | Meta Bruta R$ {faturamento_meta:.2f} | Lucro R$ {lucro_prolabore:.2f}")

# --- EXECUÇÃO ---
init_db()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
