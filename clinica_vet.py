# Importa as classes e funções do Flask para criar a aplicação web
from flask import Flask, render_template, request, redirect, url_for, session, flash
# Importa o conectar para a base de dados MySQL
import mysql.connector
# Importa a classe datetime para datas e horas
from datetime import datetime

# --- CONFIGURAÇÃO DA BASE DE DADOS ---
# Cria um dicionário com os dados de acesso ao servidor MySQL
DB_CONFIG = {
    "host": "",      # Endereço IP do servidor da base de dados
    "user": "",           # Nome de utilizador da base de dados
    "password": "",       # Senha
    "database": "" # Nome da base de dados
}

#Uma função auxiliar para ligar à base de dados
def ligar_bd():
    # Retorna a conexão usando as configurações definidas acima 
    return mysql.connector.connect(**DB_CONFIG)

# Cria a instância da aplicação Flask
app = Flask(__name__)
# Define uma senha necessária para usar sessões e mensagens flash
app.secret_key = "chave-super-secreta-clinica"

# --- CONTROLO DE ACESSO ---
# Função para verificar se existe um utilizador logado
def esta_logado():
    # Retorna True se a chave "user_id" estiver guardada na sessão do navegador
    return "user_id" in session

# Função para verificar se o utilizador logado tem permissão para aceder à página
def tem_permissao(roles_permitidas):
    # Se não estiver logado, não tem permissão (retorna False)
    if not esta_logado(): return False
    # Verifica se o cargo ("role") do utilizador atual está na lista de cargos permitidos
    return session.get("role") in roles_permitidas

# --- ROTAS GERAIS ---
# Define a rota para a página inicial (raiz do site)
@app.route("/")
def index():
    # Renderiza (mostra) o ficheiro HTML 'index.html'
    return render_template("index.html")

# Define a rota de login, que aceita métodos GET (ver a página) e POST (enviar dados)
@app.route("/login", methods=["GET", "POST"])
def login():
    # Se o utilizador enviou o formulário (método POST)
    if request.method == "POST":
        # Captura o username do formulário e remove espaços em branco extras
        username = request.form["username"].strip()
        # Captura a password do formulário
        password = request.form["password"]

        # Abre a conexão com a base de dados
        cnx = ligar_bd()
        # Cria um cursor que devolve os resultados como dicionários (ex: {'id': 1, 'nome': 'Ana'})
        cur = cnx.cursor(dictionary=True)
        # Executa a query SQL para procurar o utilizador pelo username (usa %s para evitar injeção de SQL)
        cur.execute("SELECT id, username, password, role, cliente_id FROM users WHERE username = %s", (username,))
        # Obtém o primeiro resultado encontrado (ou None se não existir)
        user = cur.fetchone()
        # Fecha o cursor e a conexão para libertar recursos
        cur.close()
        cnx.close()

        # Verifica se o utilizador existe E se a senha coincide
        if user and user["password"] == password:
            # Guarda os dados do utilizador na sessão (mantém o login ativo)
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"] # Guarda se é admin, staff ou cliente
            session["cliente_id"] = user["cliente_id"] # Guarda o ID de cliente
            return redirect(url_for("dashboard"))  # Redireciona o utilizador para a página 'dashboard'
        
        # Se o login falhar, mostra uma mensagem temporária de erro
        flash("Credenciais inválidas.")
        # Recarrega a página de login
        return redirect(url_for("login"))

    
    return render_template("login.html") # Se for método GET, apenas mostra o formulário de login

# Rota para fazer logout
@app.route("/logout")
def logout():
    # Limpa todos os dados da sessão (desloga o utilizador)
    session.clear()
    # Redireciona para a página inicial
    return redirect(url_for("index"))

# Rota para o painel principal
@app.route("/dashboard")
def dashboard():
    # Se não estiver logado, manda para o login
    if not esta_logado(): return redirect(url_for("login"))
    # Mostra o dashboard
    return render_template("dashboard.html")

# --- GESTÃO DE UTILIZADORES (ADMIN) ---
# Rota para listar utilizadores
@app.route("/users")
def users_lista():
    # Apenas administradores podem ver esta página
    if not tem_permissao(["admin"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    
    # Selecionar todos os utilizadores, ordenando especificamente: Admin, depois Staff, depois Cliente
    cur.execute("SELECT * FROM users ORDER BY FIELD(role, 'admin', 'staff', 'cliente')")
    
    # Guardar todos os resultados numa lista
    lista = cur.fetchall()
    cnx.close()
    # Envia a lista para o HTML
    return render_template("users_lista.html", users=lista)

# Rota para criar novo utilizador
@app.route("/users/novo", methods=["GET", "POST"]) # Get para obter informação do banco de dados e o Post para enviar.
def users_novo():
    # Apenas para admin
    if not tem_permissao(["admin"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    # Ve se o formulário foi submetido
    if request.method == "POST":
        # Captura os dados do formulário
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        # Se cliente_id vier vazio, guarda como None (NULL na BD)
        cliente_id = request.form.get("cliente_id") or None 

        try:
            # Tenta inserir o novo utilizador na BD
            cur.execute("INSERT INTO users (username, password, role, cliente_id) VALUES (%s, %s, %s, %s)", 
                        (username, password, role, cliente_id))
            # Confirma a gravação na BD
            cnx.commit()
            flash("Utilizador criado!")
        except Exception as e:
            # Se der erro, mostra mensagem
            flash(f"Erro: {e}")
        finally:
            cnx.close()
        return redirect(url_for("users_lista"))
    
    # Se for GET, busca a lista de clientes (caso queira associar um user a um cliente)
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    cnx.close()
    return render_template("users_form.html", user=None, clientes=clientes)

# Rota para editar utilizador (recebe o ID na URL)
@app.route("/users/editar/<int:id>", methods=["GET", "POST"]) 
def users_editar(id):
    if not tem_permissao(["admin"]): return redirect(url_for("dashboard")) 
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    if request.method == "POST":
        password = request.form["password"]
        role = request.form["role"]
        cliente_id = request.form.get("cliente_id") or None

        try:
            # Atualiza os dados do utilizador com o ID específico
            cur.execute("UPDATE users SET password=%s, role=%s, cliente_id=%s WHERE id=%s", 
                        (password, role, cliente_id, id))
            cnx.commit()
            flash("Utilizador atualizado!")
        except Exception as e:
            flash(f"Erro: {e}")
        finally:
            cnx.close()
        return redirect(url_for("users_lista"))

    # Busca os dados do utilizador atual para preencher o formulário
    cur.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cur.fetchone()
    # Busca lista de clientes para o dropdown
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    cnx.close()
    return render_template("users_form.html", user=user, clientes=clientes)

# Rota para apagar utilizador
@app.route("/users/apagar/<int:id>", methods=["POST"])
def users_apagar(id):
    if not tem_permissao(["admin"]): return redirect(url_for("dashboard"))
    # Impede que o admin se apague a si mesmo
    if session.get("user_id") == id:
        flash("Não pode apagar o seu próprio utilizador!")
        return redirect(url_for("users_lista"))
    cnx = ligar_bd()
    cur = cnx.cursor()
    # Apaga o registo
    cur.execute("DELETE FROM users WHERE id=%s", (id,))
    cnx.commit()
    cnx.close()
    flash("Utilizador apagado.")
    return redirect(url_for("users_lista"))

# --- GESTÃO DE CLIENTES (ADMIN & STAFF) ---
@app.route("/clientes")
def clientes_lista():
    # Admin e Staff podem ver
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    
    # Seleciona clientes ordenados por ID
    cur.execute("SELECT * FROM clientes ORDER BY id ASC")
    
    lista = cur.fetchall()
    cnx.close()
    return render_template("clientes_lista.html", clientes=lista)

@app.route("/clientes/novo", methods=["GET", "POST"])
def clientes_novo():
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        morada = request.form["morada"]

        cnx = ligar_bd()
        cur = cnx.cursor()
        try:
            # 1. Insere o Cliente na tabela 'clientes'
            cur.execute("INSERT INTO clientes (nome, email, telefone, morada) VALUES (%s, %s, %s, %s)",
                        (nome, email, telefone, morada))
            # Obtém o ID que acabou de ser gerado para este novo cliente
            novo_id = cur.lastrowid

            # 2. Cria AUTOMATICAMENTE um Utilizador para este cliente fazer login
            # Usa o email como username e uma senha padrão "1234"
            cur.execute("INSERT INTO users (username, password, role, cliente_id) VALUES (%s, %s, %s, %s)",
                        (email, "1234", "cliente", novo_id))
            cnx.commit()
            flash(f"Cliente criado! Login: {email} | Pass: 1234")
            return redirect(url_for("clientes_lista"))
        except mysql.connector.Error as err:
            # Se o erro for código 1062 (Duplicado), avisa que o email já existe
            if err.errno == 1062 or 'Duplicate entry' in str(err):
                flash(f"Erro: O email '{email}' já existe.")
            else:
                flash(f"Erro SQL: {err}")
        finally:
            cnx.close()
        return render_template("clientes_form.html", cliente=None)

    return render_template("clientes_form.html", cliente=None)

@app.route("/clientes/editar/<int:id>", methods=["GET", "POST"])
def clientes_editar(id):
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        morada = request.form["morada"]
        try:
            # Atualiza dados do cliente
            cur.execute("UPDATE clientes SET nome=%s, telefone=%s, morada=%s WHERE id=%s", 
                        (nome, telefone, morada, id))
            cnx.commit()
            flash("Cliente editado!")
            return redirect(url_for("clientes_lista"))
        except Exception as e:
            flash(f"Erro: {e}")
        finally:
            cnx.close()

    # Carrega dados atuais
    cur.execute("SELECT * FROM clientes WHERE id=%s", (id,))
    cliente = cur.fetchone()
    cnx.close()
    return render_template("clientes_form.html", cliente=cliente)

@app.route("/clientes/apagar/<int:id>", methods=["POST"])
def clientes_apagar(id):
    if not tem_permissao(["admin"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor()
    try:
        # Tenta apagar cliente. Se tiver animais associados, o MySQL vai dar erro (Restrição de chave estrangeira)
        cur.execute("DELETE FROM clientes WHERE id=%s", (id,))
        cnx.commit()
        flash("Cliente apagado.")
    except Exception as e:
        flash("Erro ao apagar (pode ter animais/consultas associados).")
    cnx.close()
    return redirect(url_for("clientes_lista"))

# --- GESTÃO DE ANIMAIS (ADMIN & STAFF) ---
@app.route("/animais")
def animais_lista():
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    
    # Query com JOIN: Busca dados do animal E o nome do dono (tabela clientes)
    cur.execute("""
        SELECT a.id, a.nome, a.especie, a.raca, c.nome AS dono_nome  
        FROM animais a 
        JOIN clientes c ON a.cliente_id = c.id 
        ORDER BY a.id ASC
    """)
    
    lista = cur.fetchall()
    cnx.close()
    return render_template("animais_lista.html", animais=lista)

@app.route("/animais/novo", methods=["GET", "POST"])
def animais_novo():
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    if request.method == "POST":
        try:
            # Insere novo animal associado a um cliente_id
            cur.execute("INSERT INTO animais (cliente_id, nome, especie, raca) VALUES (%s, %s, %s, %s)", 
                        (request.form["cliente_id"], request.form["nome"], request.form["especie"], request.form["raca"]))
            cnx.commit()
            flash("Animal registado!")
            return redirect(url_for("animais_lista"))
        except Exception as e:
            flash(f"Erro: {e}")
    # Busca lista de clientes para selecionar o dono
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    cnx.close()
    return render_template("animais_form.html", clientes=clientes)

@app.route("/animais/editar/<int:id>", methods=["GET", "POST"])
def animais_editar(id):
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    if request.method == "POST":
        nome = request.form["nome"]
        especie = request.form["especie"]
        raca = request.form["raca"]
        
        try:
            # Atualiza dados do animal
            cur.execute("UPDATE animais SET nome=%s, especie=%s, raca=%s WHERE id=%s", 
                        (nome, especie, raca, id))
            cnx.commit()
            flash("Animal atualizado com sucesso!")
            return redirect(url_for("animais_lista"))
        except Exception as e:
            flash(f"Erro ao editar: {e}")

    # Buscar dados do animal
    cur.execute("SELECT * FROM animais WHERE id=%s", (id,))
    animal = cur.fetchone()
    
    # Buscar clientes para o dropdown (caso queiras mudar o dono)
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    
    cnx.close()
    return render_template("animais_form.html", animal=animal, clientes=clientes)

@app.route("/animais/apagar/<int:id>", methods=["POST"])
def animais_apagar(id):
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    
    cnx = ligar_bd()
    cur = cnx.cursor()
    try:
        cur.execute("DELETE FROM animais WHERE id=%s", (id,))
        cnx.commit()
        flash("Animal apagado com sucesso.")
    except Exception as e:
        flash("Erro: Não é possível apagar este animal (pode ter consultas associadas).")
    finally:
        cnx.close()
        
    return redirect(url_for("animais_lista"))

# --- CONSULTAS (ADMIN & STAFF) ---
@app.route("/consultas/nova", methods=["GET", "POST"])
def consultas_nova():
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    if request.method == "POST":
        try:
            # Regista a consulta
            cur.execute("INSERT INTO consultas (animal_id, data_hora, motivo) VALUES (%s, %s, %s)", 
                        (request.form["animal_id"], request.form["data_hora"], request.form["motivo"]))
            cnx.commit()
            flash("Consulta marcada!")
            return redirect(url_for("dashboard"))
        except Exception as e: flash(f"Erro: {e}")
    # Busca animais e junta com nome do dono para mostrar no dropdown (ex: "Bobby - Dono: João")
    cur.execute("SELECT a.id, a.nome, c.nome as dono_nome FROM animais a JOIN clientes c ON a.cliente_id = c.id ORDER BY c.nome")
    animais = cur.fetchall()
    cnx.close()
    return render_template("consultas_form.html", animais=animais)

@app.route("/consultas")
def consultas_lista():
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    
    # Query base que junta Consultas, Animais e Clientes
    sql_base = """SELECT c.id, c.data_hora, c.motivo, a.nome AS animal_nome, cl.nome AS dono_nome
                  FROM consultas c JOIN animais a ON c.animal_id = a.id JOIN clientes cl ON a.cliente_id = cl.id"""
    
    # Busca consultas FUTURAS (data_hora maior que agora)
    cur.execute(sql_base + " WHERE c.data_hora >= NOW() ORDER BY c.data_hora ASC")
    futuras = cur.fetchall()
    
    # Busca consultas PASSADAS (data_hora menor que agora)
    cur.execute(sql_base + " WHERE c.data_hora < NOW() ORDER BY c.data_hora DESC")
    passadas = cur.fetchall()
    
    cnx.close()
    return render_template("consultas_lista.html", futuras=futuras, passadas=passadas)

@app.route("/consultas/editar/<int:id>", methods=["GET", "POST"])
def consultas_editar(id):
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    if request.method == "POST":
        data_hora = request.form["data_hora"]
        motivo = request.form["motivo"]
        
        try:
            cur.execute("UPDATE consultas SET data_hora=%s, motivo=%s WHERE id=%s", 
                        (data_hora, motivo, id))
            cnx.commit()
            flash("Consulta atualizada!")
            return redirect(url_for("consultas_lista"))
        except Exception as e:
            flash(f"Erro ao editar: {e}")

    # Buscar dados da consulta
    cur.execute("SELECT * FROM consultas WHERE id=%s", (id,))
    consulta = cur.fetchone()
    
    # Buscar animais para o dropdown
    cur.execute("SELECT a.id, a.nome, c.nome as dono_nome FROM animais a JOIN clientes c ON a.cliente_id = c.id ORDER BY c.nome")
    animais = cur.fetchall()
    
    cnx.close()
    return render_template("consultas_form.html", consulta=consulta, animais=animais)

@app.route("/consultas/apagar/<int:id>", methods=["POST"])
def consultas_apagar(id):
    if not tem_permissao(["admin", "staff"]): return redirect(url_for("dashboard"))
    
    cnx = ligar_bd()
    cur = cnx.cursor()
    try:
        cur.execute("DELETE FROM consultas WHERE id=%s", (id,))
        cnx.commit()
        flash("Consulta cancelada/apagada.")
    except Exception as e:
        flash(f"Erro ao apagar: {e}")
    finally:
        cnx.close()
        
    return redirect(url_for("consultas_lista"))

# --- ÁREA DO CLIENTE (ROTAS SEPARADAS) ---

# 1. Ver Perfil (Menu Principal do Cliente)
@app.route("/minha-conta")
def minha_conta():
    # Apenas clientes podem ver
    if not tem_permissao(["cliente"]): return redirect(url_for("login"))
    # Obtém o ID do cliente guardado na sessão
    cid = session.get("cliente_id")
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    
    # Busca apenas os dados DESTE cliente
    cur.execute("SELECT * FROM clientes WHERE id = %s", (cid,))
    meus_dados = cur.fetchone()
    
    cnx.close()
    return render_template("minha_conta.html", dados=meus_dados)

# 2. Editar Dados e Senha do Cliente
@app.route("/minha-conta/editar", methods=["GET", "POST"])
def minha_conta_editar():
    if not tem_permissao(["cliente"]): return redirect(url_for("login"))
    
    cid = session.get("cliente_id")
    uid = session.get("user_id")
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)

    if request.method == "POST":
        acao = request.form.get("acao")
        # Se a ação for editar informações pessoais
        if acao == "editar_info":
            morada = request.form["morada"]
            telefone = request.form["telefone"]
            try:
                cur.execute("UPDATE clientes SET morada=%s, telefone=%s WHERE id=%s", (morada, telefone, cid))
                cnx.commit()
                flash("Informações atualizadas com sucesso!")
            except Exception as e:
                flash(f"Erro: {e}")  
        # Se a ação for mudar senha
        elif acao == "mudar_senha":
            senha_atual = request.form["senha_atual"]
            nova_senha = request.form["nova_senha"]
            confirmar_senha = request.form["confirmar_senha"]
            
            # Verifica a senha atual na tabela Users
            cur.execute("SELECT password FROM users WHERE id = %s", (uid,))
            user_db = cur.fetchone()
            
            if user_db and user_db["password"] == senha_atual:
                if nova_senha == confirmar_senha:
                    # Atualiza a senha
                    cur.execute("UPDATE users SET password=%s WHERE id=%s", (nova_senha, uid))
                    cnx.commit()
                    flash("Senha alterada com sucesso!")
                else:
                    flash("Erro: A confirmação da senha não coincide.")
            else:
                flash("Erro: A senha atual está errada.")
    
    # Carregar dados para mostrar no formulário
    cur.execute("SELECT * FROM clientes WHERE id = %s", (cid,))
    meus_dados = cur.fetchone()
    cnx.close()
    return render_template("minha_conta_editar.html", dados=meus_dados)

# 3. Ver Meus Animais (Apenas animais do cliente logado)
@app.route("/meus-animais")
def meus_animais():
    if not tem_permissao(["cliente"]): return redirect(url_for("login"))
    cid = session.get("cliente_id")
    
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    # Filtra WHERE cliente_id = ID da sessão
    cur.execute("SELECT * FROM animais WHERE cliente_id = %s", (cid,))
    animais = cur.fetchall()
    cnx.close()
    
    return render_template("meus_animais.html", animais=animais)

# 4. Ver Minhas Consultas
@app.route("/minhas-consultas")
def minhas_consultas():
    if not tem_permissao(["cliente"]): return redirect(url_for("login"))
    cid = session.get("cliente_id")
    cnx = ligar_bd()
    cur = cnx.cursor(dictionary=True)
    # JOIN complexo para garantir que só mostramos consultas dos animais DESTE cliente
    cur.execute("""
        SELECT c.data_hora, c.motivo, c.notas, a.nome as animal_nome 
        FROM consultas c JOIN animais a ON c.animal_id = a.id
        WHERE a.cliente_id = %s ORDER BY c.data_hora DESC""", (cid,))
    consultas = cur.fetchall()
    cnx.close()
    return render_template("minhas_consultas.html", consultas=consultas)

# Inicia o servidor Flask se este ficheiro for executado diretamente
if __name__ == "__main__":
    app.run(debug=True) # debug=True reinicia o servidor automaticamente se houver mudanças no código