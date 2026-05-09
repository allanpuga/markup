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
    
    c.execute('''CREATE TABLE IF NOT EXISTS perfil_motorista 
                 (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) UNIQUE, nome VARCHAR(255), email VARCHAR(255), 
                  estado VARCHAR(50), cidade VARCHAR(255), whatsapp VARCHAR(50), 
                  dias_semana INT, horas_dia INT, km_dia FLOAT, 
                  tipo_posse VARCHAR(50), valor_aluguel_semana FLOAT, valor_parcela FLOAT, parcelas_restantes INT,
                  marca VARCHAR(100), modelo VARCHAR(100), ano VARCHAR(50), codigo_fipe VARCHAR(50), valor_fipe FLOAT, fipe_str VARCHAR(50))''')
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
            except Exception as e: 
                st.error(f"Erro de conexão com o banco: {e}")

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
                except mysql.connector.IntegrityError: 
                    st.error("Este nome de usuário já existe ou ocorreu um erro.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else: st.warning("Preencha todos os campos para se cadastrar.")

# 4. Interface Principal
def main_app():
    username = st.session_state['username']
    
    st.sidebar.title("Navegação")
    st.sidebar.write(f"👤 Olá, **{username}**!")
    
    if 'mudar_aba' in st.session_state:
        st.session_state['menu_opcao'] = st.session_state['mudar_aba']
        del st.session_state['mudar_aba']
        
    menu_opcao = st.sidebar.radio("Etapas:", ["1️⃣ Meu Perfil", "2️⃣ Veículo e Jornada", "3️⃣ Calculadora de Markup"], key="menu_opcao")
    
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
                    c.execute("INSERT INTO perfil_motorista (user_id, nome, email, whatsapp, estado, cidade) VALUES (%s, %s, %s, %s, %s, %s)",
                              (username, nome, email, whatsapp, uf_salvar, cidade_selecionada))
                conn.commit()
                conn.close()
                st.success("✅ Perfil salvo! Avançando para a próxima etapa...")
                time.sleep(1.5)
                st.session_state['mudar_aba'] = "2️⃣ Veículo e Jornada"
                st.rerun()

    # --- TELA 2: VEÍCULO E JORNADA ---
    elif menu_opcao == "2️⃣ Veículo e Jornada":
        st.title("🚘 Veículo e Jornada")
        if not perfil or not perfil['nome']:
            st.warning("⚠️ Preencha seu Perfil na etapa 1 antes de continuar!")
            return

        p_ds = int(perfil['dias_semana']) if perfil and perfil['dias_semana'] else 6
        p_hd = int(perfil['horas_dia']) if perfil and perfil['horas_dia'] else 8
        p_km = float(perfil['km_dia']) if perfil and perfil['km_dia'] else 150.0
        p_tipo_posse = perfil['tipo_posse'] if perfil and perfil['tipo_posse'] else "Próprio"
        p_valor_aluguel = float(perfil['valor_aluguel_semana']) if perfil and perfil['valor_aluguel_semana'] else 0.0
        p_valor_parcela = float(perfil['valor_parcela']) if perfil and perfil['valor_parcela'] else 0.0
        p_parcelas_rest = int(perfil['parcelas_restantes']) if perfil and perfil['parcelas_restantes'] else 0

        with st.container(border=True):
            st.markdown("### 🕒 Como é a sua rotina na pista?")
            dias_semana = st.slider("Quantos dias você trabalha por semana?", 1, 7, p_ds)
            horas_dia = st.slider("Em média, quantas horas por dia?", 1, 24, p_hd)
            km_dia = st.number_input("Qual a média de KM rodados por dia?", min_value=10, max_value=800, value=int(p_km))

        with st.container(border=True):
            st.markdown("### 🔑 Posse do Veículo")
            tipo_posse = st.radio("O veículo que você utiliza é:", ["Próprio", "Alugado", "Financiado"], 
                                  index=["Próprio", "Alugado", "Financiado"].index(p_tipo_posse))
            
            valor_aluguel, valor_parcela, parcelas_restantes = p_valor_aluguel, p_valor_parcela, p_parcelas_rest

            if tipo_posse == "Alugado":
                st.info("💡 Lembrete: Carros alugados não sofrem depreciação e não pagam IPVA/Licenciamento.")
                valor_aluguel = st.number_input("Quanto você paga de aluguel por semana? (R$)", min_value=0.0, value=valor_aluguel)
            elif tipo_posse == "Financiado":
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    valor_parcela = st.number_input("Qual o valor da parcela mensal? (R$)", min_value=0.0, value=valor_parcela)
                with col_f2:
                    parcelas_restantes = st.number_input("Quantas parcelas faltam?", min_value=0, value=parcelas_restantes)
            else:
                st.success("✅ Veículo quitado! Todo o lucro sobre a posse é seu.")

        with st.container(border=True):
            st.markdown("### 🚗 Dados Técnicos (FIPE)")
            p_marca = perfil['marca'] if perfil else ""
            p_modelo = perfil['modelo'] if perfil else ""
            p_fipe_val = float(perfil['valor_fipe']) if perfil and perfil['valor_fipe'] else 0.0
            
            if p_fipe_val > 0: st.write(f"🚘 **Veículo Atual:** {p_marca} {p_modelo} | **FIPE:** {perfil['fipe_str']}")

            marcas = get_marcas()
            marca_dict = {m['name']: str(m['code']) for m in marcas} if marcas else {}
            marca_selecionada = st.selectbox("Trocar Marca (Opcional)", ["Selecione..."] + list(marca_dict.keys()))

            modelo_selecionado, ano_selecionado, ano_id = "Selecione...", "Selecione...", None

            if marca_selecionada != "Selecione...":
                marca_id = marca_dict[marca_selecionada]
                modelos = get_modelos(marca_id)
                if modelos:
                    modelo_dict = {m['name']: str(m['code']) for m in modelos}
                    modelo_selecionado = st.selectbox("Modelo", ["Selecione..."] + list(modelo_dict.keys()))
                    if modelo_selecionado != "Selecione...":
                        modelo_id = modelo_dict[modelo_selecionado]
                        anos = get_anos(marca_id, modelo_id)
                        if anos:
                            ano_dict = {a['name']: str(a['code']) for a in anos}
                            ano_selecionado = st.selectbox("Ano", ["Selecione..."] + list(ano_dict.keys()))
                            ano_id = ano_dict[ano_selecionado] if ano_selecionado != "Selecione..." else None

        st.markdown("---")
        if st.button("💾 Salvar Jornada e Avançar para Cálculos", type="primary", use_container_width=True):
            conn = get_db_connection()
            c = conn.cursor()
            
            if marca_selecionada != "Selecione..." and ano_id:
                with st.spinner("Atualizando base FIPE..."):
                    dados_veiculo = get_valor_fipe(marca_id, modelo_id, ano_id)
                    if dados_veiculo:
                        fipe_str = dados_veiculo['price']
                        codigo_fipe_real = dados_veiculo['codeFipe']
                        fipe_float = float(fipe_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
                        
                        c.execute('''UPDATE perfil_motorista SET 
                                     dias_semana=%s, horas_dia=%s, km_dia=%s, tipo_posse=%s, valor_aluguel_semana=%s, valor_parcela=%s, parcelas_restantes=%s,
                                     marca=%s, modelo=%s, ano=%s, codigo_fipe=%s, valor_fipe=%s, fipe_str=%s WHERE user_id=%s''',
                                  (dias_semana, horas_dia, km_dia, tipo_posse, valor_aluguel, valor_parcela, parcelas_restantes,
                                   marca_selecionada, modelo_selecionado, ano_selecionado, codigo_fipe_real, fipe_float, fipe_str, username))
                        st.session_state['fipe_float'] = fipe_float
                        st.success("✅ Tudo salvo! Abrindo a Calculadora de Markup...")
                        time.sleep(1.5)
                        st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"
                        st.rerun()
            else:
                c.execute('''UPDATE perfil_motorista SET 
                             dias_semana=%s, horas_dia=%s, km_dia=%s, tipo_posse=%s, valor_aluguel_semana=%s, valor_parcela=%s, parcelas_restantes=%s 
                             WHERE user_id=%s''', 
                          (dias_semana, horas_dia, km_dia, tipo_posse, valor_aluguel, valor_parcela, parcelas_restantes, username))
                st.session_state['fipe_float'] = p_fipe_val
                st.success("✅ Jornada atualizada! Abrindo a Calculadora de Markup...")
                time.sleep(1.5)
                st.session_state['mudar_aba'] = "3️⃣ Calculadora de Markup"
                st.rerun()
                
            conn.commit()
            conn.close()

    # --- TELA 3: CALCULADORA DE MARKUP ---
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        st.title("📊 Painel Financeiro Mestre")
        if not perfil or not perfil['marca']:
            st.warning("⚠️ Preencha as etapas 1 e 2 antes de abrir a Calculadora!")
            return
            
        fipe_atual = float(perfil['valor_fipe'])
        tipo_posse = perfil['tipo_posse']
        horas_dia_trabalho = int(perfil['horas_dia'])
        dias_semana_trabalho = int(perfil['dias_semana'])
        
        dias_mensais = dias_semana_trabalho * 4.33
        km_mensal = float(perfil['km_dia']) * dias_mensais
        horas_trabalhadas_mes = horas_dia_trabalho * dias_mensais

        # ---------------------------------------------------------
        # BLOCO 1: CUSTOS FIXOS (Anuais e Mensais)
        # ---------------------------------------------------------
        with st.expander("📝 Custo Fixo (Rateio Anual e Mensal)", expanded=True):
            st.markdown("#### 📅 Despesas Anuais do Veículo")
            is_alugado = (tipo_posse == "Alugado")
            is_financiado = (tipo_posse == "Financiado")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                cf_ipva = st.number_input("IPVA (Total Anual R$)", value=0.0 if is_alugado else fipe_atual * 0.04, disabled=is_alugado)
                cf_licenciamento = st.number_input("Licenciamento (Total Anual R$)", value=0.0 if is_alugado else 160.0, disabled=is_alugado)
            with col_a2:
                cf_seguro_obrig = st.number_input("Seguro Obrigatório/DPVAT (Anual R$)", value=0.0 if is_alugado else 50.0, disabled=is_alugado)
                
                if is_alugado:
                    st.info("🚗 **Carro Alugado:** Isento de Seguro Próprio.")
                    cf_seguro_carro = 0.0
                else:
                    tem_seguro = st.radio("Paga Seguro Privado / Proteção Veicular?", ["Sim", "Não"])
                    cf_seguro_carro = st.number_input("Valor do Seguro (Total Anual R$)", value=2500.0) if tem_seguro == "Sim" else 0.0
                
            cf_anuais_mensalizado = (cf_ipva + cf_licenciamento + cf_seguro_obrig + cf_seguro_carro) / 12
            if not is_alugado: st.info(f"🔄 **Rateio Mensal dos custos anuais:** R$ {cf_anuais_mensalizado:.2f} / mês")

            st.markdown("#### 🗓️ Despesas Mensais Fixas")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                # Removido o campo de Salário Fixo. INSS/MEI mantido.
                cf_inss = st.number_input("Contribuição INSS / MEI (Mensal R$)", value=155.32)
                cf_internet = st.number_input("Plano de Internet Celular (Mensal R$)", value=60.0)
            
            with col_f2:
                mensalidade_carro = 0.0
                cf_aluguel_extra = 0.0
                
                if is_alugado:
                    mensalidade_carro = float(perfil['valor_aluguel_semana']) * 4.33
                    st.write(f"**Aluguel Mensal Base:** R$ {mensalidade_carro:.2f}")
                    cf_aluguel_extra = st.number_input("Custos Extras Locadora (Mensal R$)", value=0.0, help="Caução, etc.")
                elif is_financiado:
                    mensalidade_carro = float(perfil['valor_parcela'])
                    parcelas_rest = int(perfil['parcelas_restantes'])
                    cf_parcela = st.number_input("Parcela do Financiamento (Mensal R$)", value=mensalidade_carro)
                    st.caption(f"Faltam **{parcelas_rest} parcelas**.")
                    mensalidade_carro = cf_parcela 
                else:
                    st.success("✅ Carro quitado! Nenhuma mensalidade devida.")
                
            cf_depreciacao_mensal = 0.0 if is_alugado else (fipe_atual * 0.24) / 12
            if not is_alugado: st.info(f"📉 **Depreciação Automática:** R$ {cf_depreciacao_mensal:.2f} / mês")
            
            total_cf_mensal = cf_anuais_mensalizado + cf_inss + cf_internet + mensalidade_carro + cf_aluguel_extra + cf_depreciacao_mensal

        # ---------------------------------------------------------
        # BLOCO 2: CUSTOS VARIÁVEIS 
        # ---------------------------------------------------------
        with st.expander("⛽ Custo Variável (Rotina e Operação)", expanded=True):
            st.markdown("#### 🍽️ Alimentação e Rotina")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                cv_alim_dia = st.number_input("Gasto com Alimentação (Por Dia R$)", value=30.0)
                st.caption(f"Gasto Mensal: R$ {cv_alim_dia * dias_mensais:.2f}")
            with col_r2:
                cv_lavagem = st.number_input("Lavagem do Carro (Mensal R$)", value=120.0)

            st.markdown("#### ⛽ Inteligência de Combustível")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                tipo_comb = st.selectbox("Combustível", ["Gasolina", "Etanol", "GNV (m³)", "Elétrico (kWh)"])
            with col_c2:
                preco_comb = st.number_input("Preço na Bomba (R$)", value=5.80)
            with col_c3:
                medida = "m³" if tipo_comb == "GNV (m³)" else "kWh" if tipo_comb == "Elétrico (kWh)" else "Litro"
                consumo_comb = st.number_input(f"Faz quantos KM por {medida}?", value=10.0)
            
            cv_comb_dia = (float(perfil['km_dia']) / consumo_comb) * preco_comb if consumo_comb > 0 else 0
            cv_comb_mensal = cv_comb_dia * dias_mensais
            st.success(f"🚦 Combustível: **R$ {cv_comb_dia:.2f} por dia** (Total: R$ {cv_comb_mensal:.2f}/mês).")

            st.markdown("#### 🔧 Manutenção Mecânica")
            if is_alugado: st.info("💡 Carros alugados têm manutenção inclusa pela locadora.")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1: cv_manut_mensal = st.number_input("Manutenção Média (Mensal R$)", value=0.0 if is_alugado else 150.0)
            with col_m2:
                cv_oleo = st.number_input("Troca de Óleo (Por 10k KM)", value=0.0 if is_alugado else 250.0)
                cv_alinhamento = st.number_input("Alinhamento (Por 10k KM)", value=0.0 if is_alugado else 100.0)
            with col_m3: cv_pneu = st.number_input("Jogo de Pneus (Por 30k KM)", value=0.0 if is_alugado else 1600.0)

            total_cv_mensal = (cv_alim_dia * dias_mensais) + cv_comb_mensal + cv_lavagem + cv_manut_mensal + \
                              (cv_oleo / 10000 * km_mensal) + (cv_alinhamento / 10000 * km_mensal) + (cv_pneu / 30000 * km_mensal)

        # ---------------------------------------------------------
        # BLOCO 3: IMPOSTOS E MARGEM (PRÓ-LABORE)
        # ---------------------------------------------------------
        with st.expander("📈 Impostos e Margem (Pró-labore)"):
            ipca_atual = get_ipca()
            st.write(f"**Inflação IPCA (Automático BCB):** {ipca_atual}%")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                cp_iss = st.number_input("Imposto Municipal / Federal (%)", value=5.0)
                margem_iss = st.number_input("Sua Margem de Lucro / Pró-labore (%)", value=30.0, help="Esta margem será o seu salário (dinheiro limpo) no fim do mês.")
            with col_p2:
                cp_icms = st.number_input("ICMS / Outras Taxas (%)", value=0.0)

        if st.button("Gerar Relatório de Faturamento Ideal", type="primary", use_container_width=True):
            st.markdown("### 🏆 Sua Meta Financeira")
            cp_irpf = ((total_cf_mensal + total_cv_mensal) * 0.60) * 0.11
            
            custo_base_total = total_cf_mensal + total_cv_mensal + cp_irpf
            
            try:
                faturamento_meta_iss = custo_base_total / (1 - (cp_iss/100) - (cp_icms/100) - (margem_iss/100))
                prolabore_real = faturamento_meta_iss * (margem_iss / 100)
                valor_hora_motorista = prolabore_real / horas_trabalhadas_mes if horas_trabalhadas_mes > 0 else 0
                
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Custo Fixo Total", f"R$ {total_cf_mensal:.2f} /mês")
                col_r2.metric("Custo Variável Total", f"R$ {total_cv_mensal:.2f} /mês")
                col_r3.metric("Faturamento Necessário", f"R$ {faturamento_meta_iss:.2f} /mês")
                
                st.markdown("---")
                st.markdown("### 💼 Inteligência de Pró-labore (O seu dinheiro)")
                st.info(f"Ao faturar a meta acima, após pagar todos os custos e impostos da operação, sobrarão **R$ {prolabore_real:.2f} livres** para você ({margem_iss}%).")
                
                # Análise CLT
                col_clt1, col_clt2 = st.columns(2)
                with col_clt1:
                    st.write(f"**Sua Jornada:** {horas_trabalhadas_mes:.0f} horas / mês")
                    st.write(f"**Padrão CLT:** 220 horas / mês")
                with col_clt2:
                    st.write(f"**Sua Hora Trabalhada (Livre):** R$ {valor_hora_motorista:.2f}")
                    
                if horas_trabalhadas_mes > 220:
                    st.warning("⚠️ Atenção: Sua carga horária está superior ao limite saudável estipulado pela CLT (44h semanais).")
                else:
                    st.success("✅ Sua carga horária está dentro do padrão saudável da CLT.")
                    
            except ZeroDivisionError:
                st.error("Erro matemático: A soma dos percentuais de imposto e margem não pode ser 100% ou maior.")

try: init_db()
except: pass

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_app()
