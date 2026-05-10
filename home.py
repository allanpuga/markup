"""
Gestão Markup — Versão Refatorada
Correções aplicadas:
  - Senhas com hash bcrypt (segurança crítica)
  - Conexões DB protegidas com try/finally
  - Resultados recalculados do banco (sem dependência exclusiva de session_state)
  - Tratamento de erro nas APIs externas (FIPE, IBGE)
  - km_dia mantido como float sem truncamento
  - Recuperação de senha marcada como "em breve" com clareza
  - Feedback de veículo ativo fora do expander
  - Validações de campos obrigatórios antes de salvar
"""

import streamlit as st
import mysql.connector
import requests
import bcrypt

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÃO DE CONEXÃO
# ─────────────────────────────────────────────

def get_db_connection():
    """Retorna uma conexão MySQL usando segredos do Streamlit."""
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        connection_timeout=10,
    )


def init_db():
    """Cria as tabelas necessárias e migra schema legado caso necessário."""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(buffered=True)

        # Cria tabela de usuários com schema novo
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL DEFAULT '',
                email VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        # Migração: coluna legado 'password' -> 'password_hash'
        c.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'usuarios'
              AND COLUMN_NAME  = 'password'
        """)
        has_legacy_col = c.fetchone()[0] > 0

        if has_legacy_col:
            # Garante que password_hash existe
            c.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'usuarios'
                  AND COLUMN_NAME  = 'password_hash'
            """)
            if c.fetchone()[0] == 0:
                c.execute(
                    "ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''"
                )
            # Copia senhas antigas com prefixo para serem migradas no 1o login
            c.execute("""
                UPDATE usuarios
                SET password_hash = CONCAT('__LEGACY__', `password`)
                WHERE password_hash = '' OR password_hash IS NULL
            """)
            conn.commit()

        # ── Migração: coluna legado 'password' → 'password_hash' ──────────
        # Verifica se a coluna antiga ainda existe
        c.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'usuarios'
              AND COLUMN_NAME  = 'password'
        """)
        if c.fetchone()[0] > 0:
            # Adiciona password_hash se ainda não existir
            c.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'usuarios'
                  AND COLUMN_NAME  = 'password_hash'
            """)
            if c.fetchone()[0] == 0:
                c.execute("ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''")

            # Marca usuários legado com prefixo especial para forçar redefinição
            c.execute("""
                UPDATE usuarios
                SET password_hash = CONCAT('__LEGACY__', `password`)
                WHERE password_hash = '' OR password_hash IS NULL
            """)
            conn.commit()
        # ──────────────────────────────────────────────────────────────────

        c.execute("""
            CREATE TABLE IF NOT EXISTS perfil_motorista (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                nome VARCHAR(255),
                email VARCHAR(255),
                estado VARCHAR(50),
                cidade VARCHAR(255),
                whatsapp VARCHAR(50),
                dias_semana INT DEFAULT 6,
                horas_dia INT DEFAULT 8,
                km_dia FLOAT DEFAULT 150.0,
                veiculo_ativo_id INT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS veiculos_motorista (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                marca VARCHAR(100),
                modelo VARCHAR(100),
                ano VARCHAR(50),
                codigo_fipe VARCHAR(50),
                valor_fipe FLOAT,
                fipe_str VARCHAR(50),
                tipo_posse VARCHAR(50),
                valor_aluguel_semana FLOAT DEFAULT 0,
                valor_parcela FLOAT DEFAULT 0,
                parcelas_restantes INT DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS custos_operacionais (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                veiculo_id INT NOT NULL,
                cf_ipva FLOAT DEFAULT 0,
                cf_licenciamento FLOAT DEFAULT 0,
                cf_seguro_obrig FLOAT DEFAULT 0,
                cf_seguro_carro FLOAT DEFAULT 0,
                cf_inss FLOAT DEFAULT 155.32,
                cf_internet FLOAT DEFAULT 60.0,
                cv_alim_dia FLOAT DEFAULT 30.0,
                cv_lavagem FLOAT DEFAULT 120.0,
                preco_comb FLOAT DEFAULT 5.80,
                consumo_comb FLOAT DEFAULT 10.0,
                tipo_comb VARCHAR(50),
                cv_manut_mensal FLOAT DEFAULT 150.0,
                cv_oleo FLOAT DEFAULT 250.0,
                cv_alinhamento FLOAT DEFAULT 0,
                cv_pneu FLOAT DEFAULT 1600.0,
                cp_iss FLOAT DEFAULT 5.0,
                cp_icms FLOAT DEFAULT 0,
                margem_iss FLOAT DEFAULT 30.0,
                UNIQUE KEY uq_user_veiculo (user_id, veiculo_id)
            )
        """)

        conn.commit()
    except mysql.connector.Error as e:
        st.error(f"Erro ao inicializar banco de dados: {e}")
    finally:
        if conn:
            conn.close()


# ─────────────────────────────────────────────
# 2. HELPERS DE SENHA
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Gera hash bcrypt para a senha fornecida."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifica se a senha bate com o hash armazenado."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─────────────────────────────────────────────
# 3. APIS EXTERNAS COM TRATAMENTO DE ERRO
# ─────────────────────────────────────────────

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = 8  # segundos


@st.cache_data(ttl=86400, show_spinner=False)
def get_estados() -> dict:
    try:
        res = requests.get(
            "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome",
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return {e["sigla"]: e["nome"] for e in res.json()}
    except Exception:
        st.warning("⚠️ Não foi possível carregar os estados. Verifique sua conexão.")
        return {}


@st.cache_data(ttl=86400, show_spinner=False)
def get_cidades(uf: str) -> list:
    try:
        res = requests.get(
            f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios",
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return [c["nome"] for c in res.json()]
    except Exception:
        st.warning("⚠️ Não foi possível carregar as cidades.")
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def get_marcas() -> list:
    try:
        res = requests.get(
            "https://fipe.parallelum.com.br/api/v2/cars/brands",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        st.warning("⚠️ API FIPE indisponível. Tente novamente mais tarde.")
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def get_modelos(marca_id: str) -> list:
    try:
        res = requests.get(
            f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        st.warning("⚠️ Não foi possível carregar os modelos.")
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def get_anos(marca_id: str, modelo_id: str) -> list:
    try:
        res = requests.get(
            f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models/{modelo_id}/years",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        st.warning("⚠️ Não foi possível carregar os anos.")
        return []


def get_valor_fipe(marca_id: str, modelo_id: str, ano_id: str) -> dict | None:
    try:
        res = requests.get(
            f"https://fipe.parallelum.com.br/api/v2/cars/brands/{marca_id}/models/{modelo_id}/years/{ano_id}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        st.error("❌ Erro ao consultar valor FIPE. Tente novamente.")
        return None


# ─────────────────────────────────────────────
# 4. ACESSO / AUTENTICAÇÃO
# ─────────────────────────────────────────────

def login_user(identifier: str, password: str) -> dict | None:
    """
    Autentica por username ou e-mail.
    Suporta dois casos:
      1. Hash bcrypt normal  -> verifica com bcrypt
      2. Conta legado        -> senha em texto puro prefixada com '__LEGACY__'
         Ao autenticar com sucesso, migra automaticamente para bcrypt.
    """
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True, buffered=True)
        c.execute(
            "SELECT * FROM usuarios WHERE username=%s OR email=%s",
            (identifier, identifier),
        )
        user = c.fetchone()
        if not user:
            return None

        stored = user.get("password_hash", "")

        # Conta legado (senha plain-text marcada com prefixo)
        if stored.startswith("__LEGACY__"):
            plain_stored = stored[len("__LEGACY__"):]
            if password != plain_stored:
                return None
            # Migra para bcrypt agora que sabemos a senha correta
            new_hash = hash_password(password)
            try:
                upd = conn.cursor(buffered=True)
                upd.execute(
                    "UPDATE usuarios SET password_hash=%s WHERE id=%s",
                    (new_hash, user["id"]),
                )
                conn.commit()
            except mysql.connector.Error:
                pass  # falha silenciosa; na proxima tentativa repete
            return user

        # Conta normal com bcrypt
        if verify_password(password, stored):
            return user

        return None

    except mysql.connector.Error as e:
        st.error(f"Erro de banco ao autenticar: {e}")
        return None
    finally:
        if conn:
            conn.close()


def login_page():
    st.markdown("<h1 style='text-align:center;'>🚗 Gestão Markup</h1>", unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:

        # ── LOGIN ──────────────────────────────
        if st.session_state["auth_mode"] == "login":
            u = st.text_input("Usuário ou E-mail")
            p = st.text_input("Senha", type="password")

            if st.button("Entrar", type="primary", use_container_width=True):
                if not u or not p:
                    st.warning("Preencha usuário e senha.")
                else:
                    user = login_user(u, p)
                    if user:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = user["username"]
                        st.rerun()
                    else:
                        st.error("Usuário/senha incorretos.")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Criar Conta", use_container_width=True):
                    st.session_state["auth_mode"] = "signup"
                    st.rerun()
            with c2:
                if st.button("Esqueci a Senha", use_container_width=True):
                    st.session_state["auth_mode"] = "reset"
                    st.rerun()

        # ── CADASTRO ───────────────────────────
        elif st.session_state["auth_mode"] == "signup":
            nu = st.text_input("Usuário")
            ne = st.text_input("E-mail")
            np_ = st.text_input("Senha", type="password")
            np2 = st.text_input("Confirmar Senha", type="password")

            if st.button("Cadastrar", type="primary", use_container_width=True):
                if not all([nu, ne, np_, np2]):
                    st.warning("Preencha todos os campos.")
                elif np_ != np2:
                    st.error("As senhas não conferem.")
                elif len(np_) < 6:
                    st.warning("A senha deve ter pelo menos 6 caracteres.")
                else:
                    conn = None
                    try:
                        conn = get_db_connection()
                        c = conn.cursor(buffered=True)
                        c.execute(
                            "INSERT INTO usuarios (username, email, password_hash) VALUES (%s, %s, %s)",
                            (nu, ne, hash_password(np_)),
                        )
                        conn.commit()
                        st.success("✅ Conta criada com sucesso! Faça login.")
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("Usuário ou e-mail já cadastrado.")
                    except mysql.connector.Error as e:
                        st.error(f"Erro ao cadastrar: {e}")
                    finally:
                        if conn:
                            conn.close()

            st.button("← Voltar", on_click=lambda: st.session_state.update({"auth_mode": "login"}))

        # ── RECUPERAÇÃO (aviso honesto) ─────────
        elif st.session_state["auth_mode"] == "reset":
            st.subheader("Recuperar Senha")
            st.info(
                "🚧 A recuperação de senha por e-mail ainda não está disponível nesta versão. "
                "Entre em contato com o administrador do sistema."
            )
            st.button("← Voltar", on_click=lambda: st.session_state.update({"auth_mode": "login"}))


# ─────────────────────────────────────────────
# 5. APP PRINCIPAL
# ─────────────────────────────────────────────

def main_app():
    username = st.session_state["username"]

    # Redireciona aba se solicitado por outra etapa
    if "mudar_aba" in st.session_state:
        st.session_state["menu_opcao"] = st.session_state.pop("mudar_aba")

    opcoes = [
        "1️⃣ Meu Perfil",
        "2️⃣ Veículos e Jornada",
        "3️⃣ Calculadora de Markup",
        "4️⃣ Painel de Metas",
    ]

    st.sidebar.title("Navegação")
    menu_opcao = st.sidebar.radio("Etapas:", opcoes, key="menu_opcao")

    idx_p = opcoes.index(menu_opcao) + 1
    st.sidebar.markdown(f"**Progresso: {idx_p}/4**")
    st.sidebar.progress(idx_p * 25)

    if st.sidebar.button("Sair"):
        st.session_state["logged_in"] = False
        st.rerun()

    # Carrega perfil do banco
    perfil = _carregar_perfil(username)

    # ── ETAPA 1: PERFIL ─────────────────────────
    if menu_opcao == "1️⃣ Meu Perfil":
        _pagina_perfil(username, perfil)

    # ── ETAPA 2: GARAGEM ────────────────────────
    elif menu_opcao == "2️⃣ Veículos e Jornada":
        _pagina_garagem(username, perfil)

    # ── ETAPA 3: CALCULADORA ────────────────────
    elif menu_opcao == "3️⃣ Calculadora de Markup":
        _pagina_calculadora(username, perfil)

    # ── ETAPA 4: METAS ──────────────────────────
    elif menu_opcao == "4️⃣ Painel de Metas":
        _pagina_metas(username, perfil)


# ─────────────────────────────────────────────
# 6. PÁGINAS INDIVIDUAIS
# ─────────────────────────────────────────────

def _carregar_perfil(username: str) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM perfil_motorista WHERE user_id=%s", (username,))
        return c.fetchone()
    except mysql.connector.Error:
        return None
    finally:
        if conn:
            conn.close()


def _pagina_perfil(username: str, perfil: dict | None):
    st.title("👤 Configuração de Perfil")

    p_nome   = perfil["nome"]   if perfil else ""
    p_email  = perfil["email"]  if perfil else ""
    p_estado = perfil["estado"] if perfil else "Selecione..."
    p_cidade = perfil["cidade"] if perfil else "Selecione..."

    col1, col2 = st.columns(2)
    with col1:
        nome  = st.text_input("Nome Completo", value=p_nome)
        email = st.text_input("E-mail de Contato", value=p_email)
    with col2:
        estados   = get_estados()
        lista_est = ["Selecione..."] + [f"{s} - {n}" for s, n in estados.items()]
        idx_e     = next((i for i, x in enumerate(lista_est) if p_estado in x), 0)
        estado_sel = st.selectbox("Estado", options=lista_est, index=idx_e)

        cidade_sel = "Selecione..."
        if estado_sel != "Selecione...":
            uf      = estado_sel.split(" - ")[0]
            cidades = ["Selecione..."] + get_cidades(uf)
            idx_c   = cidades.index(p_cidade) if p_cidade in cidades else 0
            cidade_sel = st.selectbox("Cidade", options=cidades, index=idx_c)

    if st.button("💾 Salvar e Continuar", type="primary"):
        if not nome or not email:
            st.warning("Nome e e-mail são obrigatórios.")
            return
        if estado_sel == "Selecione..." or cidade_sel == "Selecione...":
            st.warning("Selecione estado e cidade.")
            return

        uf_save = estado_sel.split(" - ")[0]
        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor(buffered=True)
            if perfil:
                c.execute(
                    "UPDATE perfil_motorista SET nome=%s, email=%s, estado=%s, cidade=%s WHERE user_id=%s",
                    (nome, email, uf_save, cidade_sel, username),
                )
            else:
                c.execute(
                    "INSERT INTO perfil_motorista (user_id, nome, email, estado, cidade, dias_semana, horas_dia, km_dia) "
                    "VALUES (%s,%s,%s,%s,%s,6,8,150)",
                    (username, nome, email, uf_save, cidade_sel),
                )
            conn.commit()
            st.session_state["mudar_aba"] = "2️⃣ Veículos e Jornada"
            st.rerun()
        except mysql.connector.Error as e:
            st.error(f"Erro ao salvar perfil: {e}")
        finally:
            if conn:
                conn.close()


def _pagina_garagem(username: str, perfil: dict | None):
    st.title("🚘 Minha Garagem e Jornada")

    if not perfil:
        st.warning("⚠️ Preencha o Perfil antes de continuar.")
        return

    # ── Rotina ──────────────────────────────────
    with st.container(border=True):
        st.markdown("### 🕒 Sua Rotina na Pista")
        d_sem = st.slider("Dias por Semana", 1, 7,  int(perfil["dias_semana"]))
        h_dia = st.slider("Horas por Dia",   1, 24, int(perfil["horas_dia"]))
        # Mantido como float sem truncamento
        k_dia = st.number_input("KM Médio por Dia", value=float(perfil["km_dia"]), min_value=0.0, step=0.5)

    # ── Garagem ─────────────────────────────────
    with st.container(border=True):
        st.markdown("### 🚗 Meus Veículos")

        veiculos   = _listar_veiculos(username)
        v_ativo_id = perfil["veiculo_ativo_id"]

        if veiculos:
            labels = [
                f"{v['marca']} {v['modelo']} ({v['ano']}) — {v['tipo_posse']}"
                for v in veiculos
            ]
            ids    = [v["id"] for v in veiculos]
            idx_ini = ids.index(v_ativo_id) if v_ativo_id in ids else 0
            sel_v   = st.selectbox("Com qual veículo fará a simulação?", labels, index=idx_ini)
            v_ativo_id = ids[labels.index(sel_v)]

            # Destaque do veículo ativo
            v_atual = veiculos[ids.index(v_ativo_id)]
            st.info(
                f"🔑 **Veículo ativo:** {v_atual['marca']} {v_atual['modelo']} "
                f"({v_atual['ano']}) | Posse: {v_atual['tipo_posse']} | "
                f"FIPE: {v_atual['fipe_str']}"
            )
        else:
            st.info("Sua garagem está vazia. Adicione um veículo abaixo.")
            v_ativo_id = None

        # ── Adicionar veículo ───────────────────
        with st.expander("➕ Adicionar Novo Veículo"):
            tipo_p = st.radio("Tipo de Posse:", ["Próprio", "Alugado", "Financiado"])

            aluguel_sem = parcela_mens = prest_rest = 0.0
            if tipo_p == "Alugado":
                aluguel_sem = st.number_input("Aluguel Semanal (R$)", min_value=0.0)
            elif tipo_p == "Financiado":
                parcela_mens = st.number_input("Parcela Mensal (R$)", min_value=0.0)
                prest_rest   = st.number_input("Prestações Restantes", min_value=0, step=1)

            marcas = get_marcas()
            if not marcas:
                st.warning("API FIPE indisponível. Não é possível cadastrar veículo agora.")
            else:
                m_sel = st.selectbox("Marca", ["Selecione..."] + [m["name"] for m in marcas])
                if m_sel != "Selecione...":
                    m_id    = next(m["code"] for m in marcas if m["name"] == m_sel)
                    modelos = get_modelos(m_id)

                    if modelos:
                        mod_sel = st.selectbox("Modelo", ["Selecione..."] + [mo["name"] for mo in modelos])
                        if mod_sel != "Selecione...":
                            mo_id = next(mo["code"] for mo in modelos if mo["name"] == mod_sel)
                            anos  = get_anos(m_id, mo_id)

                            if anos:
                                ano_sel = st.selectbox("Ano", ["Selecione..."] + [a["name"] for a in anos])
                                if st.button("📥 Cadastrar e Selecionar"):
                                    if ano_sel == "Selecione...":
                                        st.warning("Selecione o ano do veículo.")
                                    else:
                                        a_id = next(a["code"] for a in anos if a["name"] == ano_sel)
                                        fipe = get_valor_fipe(m_id, mo_id, a_id)
                                        if fipe:
                                            try:
                                                f_val = float(
                                                    fipe["price"]
                                                    .replace("R$", "")
                                                    .replace(".", "")
                                                    .replace(",", ".")
                                                    .strip()
                                                )
                                            except (ValueError, KeyError):
                                                st.error("Não foi possível interpretar o valor FIPE.")
                                                return

                                            conn = None
                                            try:
                                                conn = get_db_connection()
                                                c = conn.cursor(buffered=True)
                                                c.execute(
                                                    """INSERT INTO veiculos_motorista
                                                       (user_id, marca, modelo, ano, codigo_fipe,
                                                        valor_fipe, fipe_str, tipo_posse,
                                                        valor_aluguel_semana, valor_parcela, parcelas_restantes)
                                                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                                    (
                                                        username, m_sel, mod_sel, ano_sel,
                                                        fipe["codeFipe"], f_val, fipe["price"],
                                                        tipo_p, aluguel_sem, parcela_mens, int(prest_rest),
                                                    ),
                                                )
                                                novo_id = c.lastrowid
                                                c.execute(
                                                    "UPDATE perfil_motorista SET veiculo_ativo_id=%s WHERE user_id=%s",
                                                    (novo_id, username),
                                                )
                                                conn.commit()
                                                st.success("✅ Veículo cadastrado!")
                                                st.rerun()
                                            except mysql.connector.Error as e:
                                                st.error(f"Erro ao salvar veículo: {e}")
                                            finally:
                                                if conn:
                                                    conn.close()

    # ── Confirmar jornada ───────────────────────
    if st.button("💾 Confirmar e Avançar", type="primary", use_container_width=True):
        if not v_ativo_id:
            st.warning("Adicione e selecione um veículo antes de continuar.")
            return
        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor(buffered=True)
            c.execute(
                "UPDATE perfil_motorista SET dias_semana=%s, horas_dia=%s, km_dia=%s, veiculo_ativo_id=%s WHERE user_id=%s",
                (d_sem, h_dia, k_dia, v_ativo_id, username),
            )
            conn.commit()
            st.session_state["mudar_aba"] = "3️⃣ Calculadora de Markup"
            st.rerun()
        except mysql.connector.Error as e:
            st.error(f"Erro ao salvar jornada: {e}")
        finally:
            if conn:
                conn.close()


def _listar_veiculos(username: str) -> list:
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE user_id=%s", (username,))
        return c.fetchall()
    except mysql.connector.Error:
        return []
    finally:
        if conn:
            conn.close()


def _pagina_calculadora(username: str, perfil: dict | None):
    st.title("⚙️ Lançamento de Custos Técnicos")

    if not perfil or not perfil.get("veiculo_ativo_id"):
        st.error("Selecione um veículo na etapa anterior antes de continuar.")
        return

    v_id    = perfil["veiculo_ativo_id"]
    veiculo = _carregar_veiculo(v_id)
    salvos  = _carregar_custos(username, v_id)

    if not veiculo:
        st.error("Veículo não encontrado. Volte e selecione novamente.")
        return

    def val(k, default):
        """Retorna valor salvo no banco ou o padrão."""
        return salvos[k] if salvos and salvos.get(k) is not None else default

    fipe_v = float(veiculo["valor_fipe"])
    is_al  = veiculo["tipo_posse"] == "Alugado"

    st.info(
        f"🚗 Calculando para: **{veiculo['marca']} {veiculo['modelo']} ({veiculo['ano']})** "
        f"| Posse: {veiculo['tipo_posse']} | FIPE: {veiculo['fipe_str']}"
    )

    with st.expander("📝 Custos Fixos e Mensalidades", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            ipva  = st.number_input("IPVA Anual (R$)",              value=val("cf_ipva",         0.0 if is_al else round(fipe_v * 0.04, 2)), disabled=is_al)
            licenc = st.number_input("Licenciamento Anual (R$)",    value=val("cf_licenciamento", 0.0 if is_al else 160.0),                  disabled=is_al)
            seg_p  = st.number_input("Seguro Privado Anual (R$)",   value=val("cf_seguro_carro",  0.0 if is_al else 2500.0),                 disabled=is_al)
        with col2:
            inss    = st.number_input("INSS/MEI Mensal (R$)",       value=val("cf_inss",    155.32))
            internet = st.number_input("Internet Mensal (R$)",      value=val("cf_internet",  60.0))
            deprec   = 0.0 if is_al else round((fipe_v * 0.24) / 12, 2)
            st.metric("Depreciação Mensal (24% aa)", f"R$ {deprec:.2f}")

    with st.expander("⛽ Operação Diária e Variáveis", expanded=True):
        col3, col4, col5 = st.columns(3)
        with col3:
            p_comb = st.number_input("Preço Combustível (R$/L)", value=val("preco_comb",   5.80), step=0.10)
            cons   = st.number_input("Consumo (KM/L)",           value=val("consumo_comb", 10.0), step=0.5)
        with col4:
            alim   = st.number_input("Alimentação/Dia (R$)",     value=val("cv_alim_dia",  30.0))
            lavagem = st.number_input("Lavagem/Mês (R$)",        value=val("cv_lavagem",  120.0))
        with col5:
            manut_m = st.number_input("Manutenção/Reserva Mês (R$)", value=val("cv_manut_mensal", 0.0 if is_al else 150.0))
            oleo    = st.number_input("Troca de Óleo (por 10k KM)",  value=val("cv_oleo",          0.0 if is_al else 250.0))
            pneu    = st.number_input("Pneus (por 30k KM)",          value=val("cv_pneu",          0.0 if is_al else 1600.0))

    with st.expander("📈 Margem e Impostos", expanded=True):
        col6, col7 = st.columns(2)
        with col6:
            margem = st.number_input("Sua Margem de Lucro (%)", value=val("margem_iss", 30.0), min_value=0.0, max_value=99.0)
        with col7:
            iss    = st.number_input("Imposto/Taxa (%)",        value=val("cp_iss",       5.0), min_value=0.0, max_value=99.0)

        if margem + iss >= 100:
            st.error("⚠️ Margem + Imposto não pode atingir 100%. Ajuste os valores.")
            return

    if st.button("🚀 Gerar Resultados de Markup", type="primary", use_container_width=True):
        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor(buffered=True)
            c.execute(
                """REPLACE INTO custos_operacionais
                   (user_id, veiculo_id, cf_ipva, cf_licenciamento, cf_seguro_carro,
                    cf_inss, cf_internet, cv_alim_dia, cv_lavagem,
                    preco_comb, consumo_comb, cv_manut_mensal, cv_oleo, cv_pneu,
                    margem_iss, cp_iss)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    username, v_id, ipva, licenc, seg_p, inss, internet,
                    alim, lavagem, p_comb, cons, manut_m, oleo, pneu, margem, iss,
                ),
            )
            conn.commit()
        except mysql.connector.Error as e:
            st.error(f"Erro ao salvar custos: {e}")
            return
        finally:
            if conn:
                conn.close()

        # Calcula e armazena no session_state para o painel
        dias_m = float(perfil["dias_semana"]) * 4.33
        km_m   = float(perfil["km_dia"]) * dias_m
        h_m    = float(perfil["horas_dia"]) * dias_m

        cf_m = (ipva + licenc + seg_p + 50) / 12 + inss + internet + deprec
        if veiculo["tipo_posse"] == "Alugado":
            cf_m += float(veiculo["valor_aluguel_semana"]) * 4.33
        elif veiculo["tipo_posse"] == "Financiado":
            cf_m += float(veiculo["valor_parcela"])

        cv_m = (
            (km_m / cons * p_comb)
            + (alim * dias_m)
            + lavagem
            + manut_m
            + (oleo / 10000 * km_m)
            + (pneu / 30000 * km_m)
        )

        st.session_state["calc_data"] = {
            "cf": cf_m, "cv": cv_m,
            "margem": margem, "iss": iss,
            "km_m": km_m, "h_m": h_m,
        }
        st.session_state["mudar_aba"] = "4️⃣ Painel de Metas"
        st.rerun()


def _carregar_veiculo(v_id: int) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True, buffered=True)
        c.execute("SELECT * FROM veiculos_motorista WHERE id=%s", (v_id,))
        return c.fetchone()
    except mysql.connector.Error:
        return None
    finally:
        if conn:
            conn.close()


def _carregar_custos(username: str, v_id: int) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True, buffered=True)
        c.execute(
            "SELECT * FROM custos_operacionais WHERE user_id=%s AND veiculo_id=%s",
            (username, v_id),
        )
        return c.fetchone()
    except mysql.connector.Error:
        return None
    finally:
        if conn:
            conn.close()


def _recalcular_do_banco(username: str, perfil: dict) -> dict | None:
    """
    Reconstrói os dados de cálculo diretamente do banco,
    eliminando dependência exclusiva do session_state entre sessões.
    """
    v_id    = perfil.get("veiculo_ativo_id")
    if not v_id:
        return None

    veiculo = _carregar_veiculo(v_id)
    salvos  = _carregar_custos(username, v_id)

    if not veiculo or not salvos:
        return None

    fipe_v  = float(veiculo["valor_fipe"])
    is_al   = veiculo["tipo_posse"] == "Alugado"
    deprec  = 0.0 if is_al else (fipe_v * 0.24) / 12

    ipva    = salvos["cf_ipva"]
    licenc  = salvos["cf_licenciamento"]
    seg_p   = salvos["cf_seguro_carro"]
    inss    = salvos["cf_inss"]
    internet = salvos["cf_internet"]
    alim    = salvos["cv_alim_dia"]
    lavagem = salvos["cv_lavagem"]
    p_comb  = salvos["preco_comb"]
    cons    = salvos["consumo_comb"]
    manut_m = salvos["cv_manut_mensal"]
    oleo    = salvos["cv_oleo"]
    pneu    = salvos["cv_pneu"]
    margem  = salvos["margem_iss"]
    iss     = salvos["cp_iss"]

    dias_m  = float(perfil["dias_semana"]) * 4.33
    km_m    = float(perfil["km_dia"]) * dias_m
    h_m     = float(perfil["horas_dia"]) * dias_m

    cf_m    = (ipva + licenc + seg_p + 50) / 12 + inss + internet + deprec
    if veiculo["tipo_posse"] == "Alugado":
        cf_m += float(veiculo["valor_aluguel_semana"]) * 4.33
    elif veiculo["tipo_posse"] == "Financiado":
        cf_m += float(veiculo["valor_parcela"])

    if cons <= 0:
        return None

    cv_m = (
        (km_m / cons * p_comb)
        + (alim * dias_m)
        + lavagem
        + manut_m
        + (oleo / 10000 * km_m)
        + (pneu / 30000 * km_m)
    )

    return {
        "cf": cf_m, "cv": cv_m,
        "margem": margem, "iss": iss,
        "km_m": km_m, "h_m": h_m,
    }


def _pagina_metas(username: str, perfil: dict | None):
    st.title("🎯 Painel de Metas")

    if not perfil:
        st.error("Preencha seu perfil antes de acessar o painel.")
        return

    # Prefere session_state (calculado agora); fallback = banco (sessão anterior)
    d = st.session_state.get("calc_data") or _recalcular_do_banco(username, perfil)

    if not d:
        st.error("Nenhum cálculo encontrado. Preencha a Calculadora de Markup primeiro.")
        if st.button("Ir para a Calculadora"):
            st.session_state["mudar_aba"] = "3️⃣ Calculadora de Markup"
            st.rerun()
        return

    # Guarda no session_state caso tenha vindo do banco
    st.session_state["calc_data"] = d

    # ── Fórmula profissional ─────────────────────
    cp_irpf          = ((d["cf"] + d["cv"]) * 0.60) * 0.11
    custo_base_total = d["cf"] + d["cv"] + cp_irpf
    faturamento_meta = custo_base_total / (1 - (d["iss"] / 100) - (d["margem"] / 100))
    lucro_prolabore  = faturamento_meta * (d["margem"] / 100)

    st.markdown(
        "<h2 style='text-align:center;'>🎯 O SEU RESUMO NA PISTA</h2>",
        unsafe_allow_html=True,
    )
    st.info(
        f"⏱️ **Jornada Mensal:** {d['h_m']:.0f} horas &nbsp;|&nbsp; "
        f"🛣️ **Distância Mensal:** {d['km_m']:.0f} KM"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("### 🔴 Custo de Operação")
            st.metric("Por KM",   f"R$ {custo_base_total / d['km_m']:.2f}")
            st.metric("Por Hora", f"R$ {custo_base_total / d['h_m']:.2f}")
            st.caption(
                f"Fixo: R$ {d['cf']:.2f} | Variável: R$ {d['cv']:.2f} | "
                f"IRPF est.: R$ {cp_irpf:.2f}"
            )

    with col_b:
        with st.container(border=True):
            st.markdown("### 🟢 Meta de Ganho")
            st.metric("Por KM",   f"R$ {faturamento_meta / d['km_m']:.2f}")
            st.metric("Por Hora", f"R$ {faturamento_meta / d['h_m']:.2f}")
            st.caption(
                f"Faturamento bruto: R$ {faturamento_meta:.2f} | "
                f"Lucro (pró-labore): R$ {lucro_prolabore:.2f}"
            )

    st.error(
        f"🚨 **REGRA DE OURO:** Para colocar **R$ {lucro_prolabore:.2f}** "
        f"limpos no bolso, nunca aceite corridas abaixo de "
        f"**R$ {faturamento_meta / d['km_m']:.2f}/KM**."
    )

    st.markdown("---")
    st.markdown("### 📊 Detalhamento Mensal")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Custo Fixo",    f"R$ {d['cf']:.2f}")
    col2.metric("Custo Variável", f"R$ {d['cv']:.2f}")
    col3.metric("IRPF Estimado", f"R$ {cp_irpf:.2f}")
    col4.metric("Meta Bruta",    f"R$ {faturamento_meta:.2f}")


# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────

init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()