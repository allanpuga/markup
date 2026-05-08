import streamlit as st
import mysql.connector
import requests

# 1. Configuração de Conexão MySQL (Puxando do Cofre/Secrets)
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  cidade VARCHAR(255), whatsapp VARCHAR(50), dias_semana INT, horas_dia INT, 
                  km_dia FLOAT, marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50))''')
    conn.commit()
    conn.close()

# 2. APIs (FIPE e IPCA)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

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

# 3. Tela de Login e Cadastro
def login_page():
    st.title("🚗 Sistema de Markup")
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
                else:
                    st.error("Usuário ou senha incorretos.")
            except Exception as e:
                st.error(f"Erro de conexão com o banco de dados. Configure os Secrets no Streamlit. Detalhe: {e}")

    with aba_cadastro:
        st.subheader("Novo Cadastro")
        new_user = st.text_input("Escolha um Usuário", key="cad_user")
        new_pass = st.text_input("Escolha uma Senha", type="password", key="cad_pass")
        
        if st.button("Cadastrar e Criar Perfil"):
            if new_user and new_pass:
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (new_user, new_pass))
                    conn.commit()
                    conn.close()
                    st.success("Conta criada com sucesso! Volte na aba 'Entrar' para acessar o sistema.")
                except mysql.connector.IntegrityError:
                    st.error("Este nome de usuário já existe. Por favor, escolha outro.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha todos os campos para se cadastrar.")

# 4. Interface Principal (Perfil e Calculadora)
def main_app():
    username = st.session_state['username']
    
    st.sidebar.title("Menu")
    st.sidebar.write(f"👤 Olá, **{username}**!")
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("📊 Seu Perfil e Markup")

    # BUSCAR DADOS
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
    perfil = c.fetchone()
    conn.close()

    p_nome = perfil['nome'] if perfil else ""
    p_email = perfil['email'] if perfil else ""
    p_cidade = perfil['cidade'] if perfil else ""
    p_whatsapp = perfil['whatsapp'] if perfil else ""
    p_ds = int(perfil['dias_semana']) if perfil else 6
    p_hd = int(perfil['horas_dia']) if perfil else 8
    p_km = float(perfil['km_dia']) if perfil else 150.0
    
    p_marca = perfil['marca'] if perfil else ""
    p_modelo = perfil['modelo'] if perfil else ""
    p_fipe_val = float(perfil['valor_fipe']) if perfil and perfil['valor_fipe'] else 0.0
    p_fipe_str = perfil['fipe_str'] if perfil and perfil['fipe_str'] else ""

    st.subheader("1. Informações Pessoais")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        nome = st.text_input("Nome Completo", value=p_nome)
        email = st.text_input("E-mail", value=p_email)
    with col_p2:
        cidade = st.text_input("Cidade/Estado", value=p_cidade)
        whatsapp = st.text_input("WhatsApp", value=p_whatsapp)

    st.subheader("2. Jornada de Trabalho")
    col1, col2, col3 = st.columns(3)
    with col1:
        dias_semana = st.number_input("Dias na semana (DS)", min_value=1, max_value=7, value=p_ds)
    with col2:
        horas_dia = st.number_input("Horas por dia (HD)", min_value=1, max_value=24, value=p_hd)
    with col3:
        km_dia = st.number_input("KM Médio por dia", min_value=10, max_value=800, value=int(p_km))

    st.subheader("3. Dados do Veículo")
    if p_fipe_val > 0:
        st.info(f"🚘 **Veículo Atual:** {p_marca} {p_modelo} | **Valor FIPE:** {p_fipe_str}")

    marcas = get_marcas()
    if not marcas: return
        
    marca_dict = {m['name']: str(m['code']) for m in marcas}
    marca_selecionada = st.selectbox("Trocar Marca (Opcional)", ["Selecione..."] + list(marca_dict.keys()))

    modelo_selecionado = "Selecione..."
    ano_selecionado = "Selecione..."
    codigo_fipe_real = ""
    fipe_float = 0.0
    fipe_str = ""

    if marca_selecionada != "Selecione...":
        marca_id = marca_dict[marca_selecionada]
        modelos = get_modelos(marca_id)
        if modelos:
            modelo_dict = {m['name']: str(m['code']) for m in modelos}
            modelo_selecionado = st.selectbox("Trocar Modelo", ["Selecione..."] + list(modelo_dict.keys()))
            
            if modelo_selecionado != "Selecione...":
                modelo_id = modelo_dict[modelo_selecionado]
                anos = get_anos(marca_id, modelo_id)
                if anos:
                    ano_dict = {a['name']: str(a['code']) for a in anos}
                    ano_selecionado = st.selectbox("Trocar Ano", ["Selecione..."] + list(ano_dict.keys()))
                    ano_id = ano_dict[ano_selecionado] if ano_selecionado != "Selecione..." else None

    # BOTÃO SALVAR
    st.markdown("---")
    if st.button("💾 Salvar Perfil e Abrir Calculadora", type="primary"):
        conn = get_db_connection()
        c = conn.cursor()
        
        if marca_selecionada != "Selecione..." and modelo_selecionado != "Selecione..." and ano_selecionado != "Selecione...":
            with st.spinner("Atualizando FIPE e salvando perfil..."):
                dados_veiculo = get_valor_fipe(marca_id, modelo_id, ano_id)
                if dados_veiculo:
                    fipe_str = dados_veiculo['price']
                    codigo_fipe_real = dados_veiculo['codeFipe']
                    fipe_float = float(fipe_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
                    
                    if perfil:
                        c.execute('''UPDATE perfil_motorista SET 
                                     nome=%s, email=%s, cidade=%s, whatsapp=%s, dias_semana=%s, horas_dia=%s, km_dia=%s, 
                                     marca=%s, modelo=%s, ano=%s, codigo_fipe=%s, valor_fipe=%s, fipe_str=%s WHERE user_id=%s''',
                                  (nome, email, cidade, whatsapp, dias_semana, horas_dia, km_dia, 
                                   marca_selecionada, modelo_selecionado, ano_selecionado, codigo_fipe_real, fipe_float, fipe_str, username))
                    else:
                        c.execute('''INSERT INTO perfil_motorista 
                                     (user_id, nome, email, cidade, whatsapp, dias_semana, horas_dia, km_dia, marca, modelo, ano, codigo_fipe, valor_fipe, fipe_str)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                                  (username, nome, email, cidade, whatsapp, dias_semana, horas_dia, km_dia,
                                   marca_selecionada, modelo_selecionado, ano_selecionado, codigo_fipe_real, fipe_float, fipe_str))
                    st.session_state['fipe_float'] = fipe_float
                    st.success("Perfil e Veículo atualizados com sucesso!")
        else:
            if p_fipe_val > 0:
                if perfil:
                    c.execute('''UPDATE perfil_motorista SET 
                                 nome=%s, email=%s, cidade=%s, whatsapp=%s, dias_semana=%s, horas_dia=%s, km_dia=%s WHERE user_id=%s''',
                              (nome, email, cidade, whatsapp, dias_semana, horas_dia, km_dia, username))
                st.session_state['fipe_float'] = p_fipe_val
                st.success("Informações pessoais atualizadas!")
            else:
                st.error("Selecione um veículo na base FIPE!")
        
        conn.commit()
        conn.close()

    # CALCULADORA
    if 'fipe_float' in st.session_state:
        st.markdown("---")
        st.header("⚙️ Custos Operacionais")
        
        with st.expander("📝 Custo Fixo (CF)", expanded=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                cf_ipva = st.number_input("CF2 - IPVA (Anual R$)", value=st.session_state['fipe_float'] * 0.04)
                cf_licenciamento = st.number_input("CF3 - Licenciamento (Anual R$)", value=160.0)
                cf_seguro_obrig = st.number_input("CF4 - Seguro Obrigatório (Anual R$)", value=50.0)
                cf_seguro_carro = st.number_input("CF5 - Seguro do Carro (Anual R$)", value=2500.0)
            with col_f2:
                cf_parcela = st.number_input("CF6 - Parcela Fin. / Aluguel (Mensal R$)", value=0.0)
                cf_salario = st.number_input("CF7 - Salário DIEESE (Mensal R$)", value=7200.0)
                cf_inss = st.number_input("CF8 - INSS (11% Salário Mín Mensal R$)", value=155.32)
                cf_internet = st.number_input("CF9 - Internet Celular (Mensal R$)", value=60.0)
                
            cf_depreciacao_mensal = (st.session_state['fipe_float'] * 0.24) / 12
            total_cf_mensal = (cf_ipva/12) + (cf_licenciamento/12) + (cf_seguro_obrig/12) + (cf_seguro_carro/12) + cf_parcela + cf_salario + cf_inss + cf_internet + cf_depreciacao_mensal
            st.info(f"Depreciação Automática (24% aa): R$ {cf_depreciacao_mensal:.2f}/mês")

        with st.expander("⛽ Custo Variável (CV)"):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                cv_alim_dia = st.number_input("CV1 - Alimentação (Por Dia R$)", value=30.0)
                cv_comb_dia = st.number_input("CV2 - Combustível (Por Dia R$)", value=100.0)
                cv_oleo = st.number_input("CV3 - Troca de Óleo/Filtro (Valor por 10k KM R$)", value=250.0)
                cv_pneu = st.number_input("CV4 - Jogo de Pneus (Valor por 30k KM R$)", value=1600.0)
            with col_v2:
                cv_manut_mensal = st.number_input("CV5 - Manutenção Preventiva Básica (Mensal R$)", value=150.0)
                cv_lavagem = st.number_input("CV6 - Lavagem (Mensal R$)", value=120.0)
                cv_alinhamento = st.number_input("CV7 - Alinhamento/Balanceamento (Por 10k KM R$)", value=100.0)
            
            dias_mensais = dias_semana * 4.33
            km_mensal = km_dia * dias_mensais
            
            total_cv_mensal = (cv_alim_dia * dias_mensais) + (cv_comb_dia * dias_mensais) + cv_manut_mensal + cv_lavagem + (cv_oleo / 10000 * km_mensal) + (cv_pneu / 30000 * km_mensal) + (cv_alinhamento / 10000 * km_mensal)

        with st.expander("📈 Custo Percentual (CP)"):
            ipca_atual = get_ipca()
            st.write(f"**CP4 - Inflação IPCA (Automático BCB):** {ipca_atual}%")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                cp_iss = st.number_input("CP2 - ISS / IBS (%)", value=5.0)
                margem_iss = st.number_input("Margem de Lucro Base ISS (%)", value=20.0)
            with col_p2:
                cp_icms = st.number_input("CP3 - ICMS / IBS (%)", value=0.0)
                margem_icms = st.number_input("Margem de Lucro Base ICMS (%)", value=20.0)

        if st.button("Gerar Relatório de Markup", type="primary", use_container_width=True):
            st.markdown("### 🏆 Seu Markup Mensal")
            
            cp_irpf = ((total_cf_mensal + total_cv_mensal) * 0.60) * 0.11
            
            col_r1, col_r2 = st.columns(2)
            col_r1.metric("Total Custo Fixo (Mensal)", f"R$ {total_cf_mensal:.2f}")
            col_r2.metric("Total Custo Variável (Mensal)", f"R$ {total_cv_mensal:.2f}")
            col_r1.metric("IRPF (11% sobre 60% CF+CV)", f"R$ {cp_irpf:.2f}")
            
            custo_base_total = total_cf_mensal + total_cv_mensal + cp_irpf
            
            try:
                faturamento_meta_iss = custo_base_total / (1 - (cp_iss/100) - (margem_iss/100))
                st.success(f"🎯 Faturamento Meta (Com ISS e {margem_iss}% Lucro): **R$ {faturamento_meta_iss:.2f} / mês**")
                st.info(f"💵 Valor Mínimo por KM Rodado: **R$ {faturamento_meta_iss / km_mensal:.2f}**")
            except ZeroDivisionError:
                st.error("A soma dos percentuais não pode ser 100% ou maior.")

try:
    init_db()
except Exception as e:
    pass # Inicializado no Workbench

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
