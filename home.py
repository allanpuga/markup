import streamlit as st
import pandas as pd
import sqlite3

# Configuração do Banco de Dados
def init_db():
    conn = sqlite3.connect('markup_motoristas.db')
    c = conn.cursor()
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, regiao TEXT)''')
    # Tabela de dados de markup
    c.execute('''CREATE TABLE IF NOT EXISTS dados_markup 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, data TEXT, 
                  ganho_bruto REAL, km_rodado REAL, custos_totais REAL, regiao TEXT)''')
    conn.commit()
    conn.close()

# Interface de Login
def login_page():
    st.header("Login do Motorista")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Aqui futuramente verificaremos no banco de dados
        if username == "admin" and password == "123": # Exemplo simples
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

# Se não houver estado de login, mostra a página de login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()