import streamlit as st
import sqlite3
import requests

# 1. Configuração do Banco de Dados
def init_db():
    conn = sqlite3.connect('markup_motoristas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INTEGER PRIMARY KEY, user_id TEXT, nome TEXT, email TEXT, 
                  cidade TEXT, whatsapp TEXT, dias_semana INTEGER, horas_dia INTEGER, 
                  marca TEXT, modelo TEXT, ano TEXT, codigo_fipe TEXT, valor_fipe TEXT)''')
    conn.commit()
    conn.close()

# 2. Novas Funções da API da FIPE (Com Cache para ficar ultrarrápido)
@st.cache_data
def get_marcas():
    # Adicionamos o verify=False no final
    resposta = requests.get("https://parallelum.com.br/fipe/api/v1/carros/marcas", verify=False)
    return resposta.json() if resposta.status_code == 200 else []

@st.cache_data
def get_modelos(marca_id):
    resposta = requests.get(f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{marca_id}/modelos", verify=False)
    return resposta.json()['modelos'] if resposta.status_code == 200 else []

@st.cache_data
def get_anos(marca_id, modelo_id):
    resposta = requests.get(f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{marca_id}/modelos/{modelo_id}/anos", verify=False)
    return resposta.json() if resposta.status_code == 200 else []

def get_valor_fipe(marca_id, modelo_id, ano_id):
    resposta = requests.get(f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_id}", verify=False)
    return resposta.json() if resposta.status_code == 200 else None

# 3. Interface de Login
def login_page():
    st.header("Login do Motorista")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if username == "admin" and password == "123": 
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

# 4. Interface Principal (Totalmente Dinâmica)
def main_app():
    st.sidebar.title("Menu")
    st.sidebar.write(f"Usuário logado: {st.session_state['username']}")
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("📝 Formulário de Captação e Markup")
    st.markdown("Preencha seus dados para calcularmos o seu custo operacional real.")

    # Removido o "st.form" para permitir que as caixas de seleção atualizem em tempo real
    st.subheader("1. Informações Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail")
    with col2:
        cidade = st.text_input("Cidade/Estado")
        whatsapp = st.text_input("WhatsApp")

    st.subheader("2. Jornada de Trabalho")
    col3, col4 = st.columns(2)
    with col3:
        dias_semana = st.number_input("Dias trabalhados na semana (DS)", min_value=1, max_value=7, value=6)
    with col4:
        horas_dia = st.number_input("Horas trabalhadas por dia (HD)", min_value=1, max_value=24, value=8)

    st.subheader("3. Dados do Veículo (Busca Automática)")
    
    # --- LÓGICA DINÂMICA DA FIPE EM TRÊS PASSOS ---
    marcas = get_marcas()
    marca_dict = {m['nome']: m['codigo'] for m in marcas}
    marca_selecionada = st.selectbox("Selecione a Marca", options=["Selecione..."] + list(marca_dict.keys()))

    if marca_selecionada != "Selecione...":
        marca_id = marca_dict[marca_selecionada]
        modelos = get_modelos(marca_id)
        modelo_dict = {m['nome']: m['codigo'] for m in modelos}
        modelo_selecionado = st.selectbox("Selecione o Modelo", options=["Selecione..."] + list(modelo_dict.keys()))
        
        if modelo_selecionado != "Selecione...":
            modelo_id = modelo_dict[modelo_selecionado]
            anos = get_anos(marca_id, modelo_id)
            ano_dict = {a['nome']: a['codigo'] for a in anos}
            ano_selecionado = st.selectbox("Selecione o Ano de Fabricação", options=["Selecione..."] + list(ano_dict.keys()))
            
            if ano_selecionado != "Selecione...":
                ano_id = ano_dict[ano_selecionado]
                
                # Quando o motorista preenche a última etapa (Ano), o botão de salvar aparece
                st.markdown("---")
                if st.button("Salvar e Consultar Preço Real"):
                    with st.spinner("Buscando valor oficial na base FIPE..."):
                        dados_veiculo = get_valor_fipe(marca_id, modelo_id, ano_id)
                        
                        if dados_veiculo:
                            valor = dados_veiculo['Valor']
                            codigo_fipe_real = dados_veiculo['CodigoFipe']
                            mes_ref = dados_veiculo['MesReferencia']
                            
                            st.success(f"Veículo encontrado! Valor: **{valor}** (Código Fipe Oculto: {codigo_fipe_real} - Ref: {mes_ref})")
                            
                            # Salvando no Banco de Dados
                            conn = sqlite3.connect('markup_motoristas.db')
                            c = conn.cursor()
                            c.execute('''INSERT INTO perfil_motorista 
                                         (user_id, nome, email, cidade, whatsapp, dias_semana, horas_dia, marca, modelo, ano, codigo_fipe, valor_fipe)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                      (st.session_state['username'], nome, email, cidade, whatsapp, dias_semana, horas_dia, 
                                       marca_selecionada, modelo_selecionado, ano_selecionado, codigo_fipe_real, valor))
                            conn.commit()
                            conn.close()
                            st.info("Dados salvos com sucesso na base!")
                        else:
                            st.error("Erro ao buscar o valor final na FIPE. Tente novamente.")

# 5. Controle de Fluxo da Aplicação
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()