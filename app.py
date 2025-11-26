from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from flask_mail import Mail, Message
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-super-secreta-aqui'

# Configuração do Banco
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///voluntariado.db')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'apikey')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'gustavokotryk@gmail.com')


# Inicializações
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# MODELOS DIRETO NO APP.PY (pra evitar import circular)
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    cidade = db.Column(db.String(50), nullable=False)
    habilidades = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"user_{self.id}"

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_habilidades(self):
        return json.loads(self.habilidades) if self.habilidades else []


class ONG(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    descricao = db.Column(db.Text)
    causas = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"ong_{self.id}"

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_causas(self):
        return json.loads(self.causas) if self.causas else []


class Voluntariado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    ong_id = db.Column(db.Integer, db.ForeignKey('ong.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')

    usuario = db.relationship('Usuario', backref='voluntariados')
    ong = db.relationship('ONG', backref='voluntarios')


@login_manager.user_loader
def load_user(user_id):
    print(f"🔍 LOAD_USER chamado com ID: {user_id}")

    # Verifica se tem prefixo
    if user_id.startswith('user_'):
        # É um usuário - remove o prefixo
        id_num = int(user_id.replace('user_', ''))
        user = Usuario.query.get(id_num)
        if user:
            print(f"✅ Carregado como USUARIO: {user.nome}")
            return user

    elif user_id.startswith('ong_'):
        # É uma ONG - remove o prefixo
        id_num = int(user_id.replace('ong_', ''))
        ong = ONG.query.get(id_num)
        if ong:
            print(f"✅ Carregado como ONG: {ong.nome}")
            return ong

    print("❌ Nenhum usuário/ONG encontrado com este ID")
    return None


# ⚠️ **CRIA AS TABELAS AUTOMATICAMENTE NO RENDER** ⚠️
with app.app_context():
    try:
        print("🔄 Verificando/Criando tabelas no banco...")
        db.create_all()
        print("✅ Tabelas prontas!")

        # Verifica se tem dados de exemplo
        if not Usuario.query.first():
            print("📝 Criando dados de exemplo...")
            usuario = Usuario(
                nome="João Exemplo",
                email="joao@exemplo.com",
                senha=generate_password_hash("123456"),
                cidade="São Paulo"
            )
            db.session.add(usuario)

            ong = ONG(
                nome="ONG Teste",
                email="ong@exemplo.com",
                senha=generate_password_hash("123456"),
                cidade="São Paulo",
                estado="SP",
                latitude=-23.5505,
                longitude=-46.6333
            )
            db.session.add(ong)
            db.session.commit()
            print("✅ Dados de exemplo criados!")

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")


# ROTAS
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cadastro/usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        try:
            usuario = Usuario(
                nome=request.form['nome'],
                email=request.form['email'],
                senha=generate_password_hash(request.form['senha']),
                telefone=request.form.get('telefone', ''),
                cidade=request.form['cidade']
            )
            usuario.habilidades = json.dumps(request.form.getlist('habilidades'))

            db.session.add(usuario)
            db.session.commit()
            flash('Cadastro realizado! Faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Erro no cadastro! Tente novamente.', 'error')

    return render_template('cadastro_usuario.html')


@app.route('/cadastro/ong', methods=['GET', 'POST'])
def cadastro_ong():
    if request.method == 'POST':
        try:
            ong = ONG(
                nome=request.form['nome'],
                email=request.form['email'],
                senha=generate_password_hash(request.form['senha']),
                cnpj=request.form.get('cnpj', ''),
                telefone=request.form.get('telefone', ''),
                endereco=request.form.get('endereco', ''),
                cidade=request.form['cidade'],
                estado=request.form['estado'],
                descricao=request.form.get('descricao', ''),
                latitude=float(request.form['latitude']) if request.form['latitude'] else None,
                longitude=float(request.form['longitude']) if request.form['longitude'] else None
            )
            ong.causas = json.dumps(request.form.getlist('causas'))

            db.session.add(ong)
            db.session.commit()
            flash('ONG cadastrada! Faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Erro no cadastro! Tente novamente.', 'error')

    return render_template('cadastro_ong.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']

        print(f"🔍 LOGIN ORIGINAL: Email={email}, Tipo={tipo}")

        if tipo == 'usuario':
            user = Usuario.query.filter_by(email=email).first()
            user_type = "USUARIO"
        else:
            user = ONG.query.filter_by(email=email).first()
            user_type = "ONG"

        if user:
            print(f"✅ {user_type} ENCONTRADO: {user.nome}")
            print(f"   ID: {user.id}, Classe: {user.__class__.__name__}")

            if check_password_hash(user.senha, senha):
                login_user(user)
                print(f"🎯 LOGIN REALIZADO: {user.nome} como {user_type}")
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                print("❌ SENHA INCORRETA")
        else:
            print(f"❌ {user_type} NÃO ENCONTRADO")

        flash('Email ou senha incorretos!', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Verifica se é ONG (tem CNPJ) ou Usuário
        if hasattr(current_user, 'cnpj') and current_user.cnpj:
            # É uma ONG
            voluntarios = Voluntariado.query.filter_by(ong_id=current_user.id).all()
            return render_template('dashboard.html', voluntarios=voluntarios, is_ong=True)
        else:
            # É um Usuário
            voluntariados = Voluntariado.query.filter_by(usuario_id=current_user.id).all()
            return render_template('dashboard.html', voluntariados=voluntariados, is_ong=False)
    except Exception as e:
        print(f"❌ ERRO NO DASHBOARD: {e}")
        return f"<h1>Erro no Dashboard</h1><p>{e}</p>"


@app.route('/buscar-ongs')
@login_required
def buscar_ongs():
    try:
        ongs = ONG.query.all()
        is_ong = hasattr(current_user, 'cnpj')
        return render_template('buscar_ongs.html', ongs=ongs, is_ong=is_ong)
    except Exception as e:
        print(f"❌ ERRO NA BUSCA DE ONGs: {e}")
        return f"""
        <h1>Erro na Busca de ONGs</h1>
        <p><strong>Erro:</strong> {e}</p>
        <p><strong>Tipo:</strong> {type(e).__name__}</p>
        <a href="/dashboard">Voltar ao Dashboard</a>
        """, 500


@app.route('/voluntariar/<int:ong_id>')
@login_required
def voluntariar(ong_id):
    try:
        if hasattr(current_user, 'cnpj'):
            flash('ONGs não podem se voluntariar!', 'error')
            return redirect(url_for('dashboard'))

        # Verifica se a ONG existe
        ong = ONG.query.get(ong_id)
        if not ong:
            flash('ONG não encontrada!', 'error')
            return redirect(url_for('buscar_ongs'))

        # Verifica se já existe candidatura
        existing = Voluntariado.query.filter_by(
            usuario_id=current_user.id,
            ong_id=ong_id
        ).first()

        if existing:
            flash('Você já se candidatou para esta ONG!', 'warning')
            return redirect(url_for('buscar_ongs'))

        # Cria nova candidatura
        voluntariado = Voluntariado(
            usuario_id=current_user.id,
            ong_id=ong_id
        )

        db.session.add(voluntariado)
        db.session.commit()

        flash(f'Candidatura enviada para {ong.nome}!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash('Erro ao enviar candidatura!', 'error')
        return redirect(url_for('buscar_ongs'))


@app.route('/api/ongs')
def api_ongs():
    ongs = ONG.query.all()
    ongs_data = []
    for ong in ongs:
        if ong.latitude and ong.longitude:
            ongs_data.append({
                'id': ong.id,
                'nome': ong.nome,
                'cidade': ong.cidade,
                'descricao': ong.descricao,
                'lat': ong.latitude,
                'lng': ong.longitude,
                'causas': ong.get_causas()
            })
    return jsonify(ongs_data)


# Rota para forçar criação de tabelas
@app.route('/create-tables')
def create_tables():
    try:
        db.create_all()
        return """
        <h1>✅ Tabelas criadas com sucesso!</h1>
        <p>As tabelas foram criadas no PostgreSQL do Render.</p>
        <p><a href="/">Voltar para Home</a></p>
        """
    except Exception as e:
        return f"""
        <h1>❌ Erro ao criar tabelas</h1>
        <p><strong>Erro:</strong> {e}</p>
        <p><a href="/">Voltar para Home</a></p>
        """


def enviar_email(destinatario, assunto, corpo):
    try:
        print(f"🔄 Tentando enviar email para: {destinatario}")

        msg = Message(
            assunto,
            recipients=[destinatario],
            html=corpo
        )
        mail.send(msg)
        print(f"✅ EMAIL ENVIADO COM SUCESSO para: {destinatario}")
        return True

    except Exception as e:
        print(f"❌ ERRO AO ENVIAR EMAIL: {e}")

        # Modo de fallback - mostra detalhes no log
        print("🔍 DETALHES DO EMAIL QUE FALHOU:")
        print(f"   De: {app.config['MAIL_DEFAULT_SENDER']}")
        print(f"   Para: {destinatario}")
        print(f"   Assunto: {assunto}")
        print(f"   Servidor: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")

        return False


@app.route('/aceitar-voluntario/<int:voluntariado_id>')
@login_required
def aceitar_voluntario(voluntariado_id):
    try:
        if not hasattr(current_user, 'cnpj'):  # Só ONG pode aceitar
            flash('Acesso não autorizado!', 'error')
            return redirect(url_for('dashboard'))

        voluntariado = Voluntariado.query.get_or_404(voluntariado_id)
        if voluntariado.ong_id != current_user.id:
            flash('Acesso não autorizado!', 'error')
            return redirect(url_for('dashboard'))

        voluntariado.status = 'aceito'
        db.session.commit()

        assunto = "🎉 Parabéns! Você foi aceito como voluntário!"
        corpo = f"""
        <h2>Parabéns, {voluntariado.usuario.nome}!</h2>
        <p>Você foi <strong>aceito</strong> como voluntário na <strong>{current_user.nome}</strong>!</p>
        <p><strong>Próximos passos:</strong></p>
        <ul>
            <li>Entre em contato com a ONG: {current_user.telefone or 'A combinar'}</li>
            <li>Email da ONG: {current_user.email}</li>
            <li>Endereço: {current_user.endereco or 'A combinar'}, {current_user.cidade}</li>
        </ul>
        <p>Seja bem-vindo à nossa equipe! 🌟</p>
        """

        # ⚠️ ENVIA EMAIL EM BACKGROUND - NÃO TRAVA A PÁGINA
        thread = threading.Thread(
            target=enviar_email,
            args=(voluntariado.usuario.email, assunto, corpo)
        )
        thread.start()

        flash('Voluntário aceito! Notificação sendo enviada.', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Erro ao aceitar voluntário: {e}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/recusar-voluntario/<int:voluntariado_id>')
@login_required
def recusar_voluntario(voluntariado_id):
    try:
        if not hasattr(current_user, 'cnpj'):
            flash('Acesso não autorizado!', 'error')
            return redirect(url_for('dashboard'))

        voluntariado = Voluntariado.query.get_or_404(voluntariado_id)
        if voluntariado.ong_id != current_user.id:
            flash('Acesso não autorizado!', 'error')
            return redirect(url_for('dashboard'))

        voluntariado.status = 'recusado'
        db.session.commit()

        # EMAIL EM BACKGROUND (não trava a página)
        assunto = "Atualização sobre sua candidatura como voluntário"
        corpo = f"""
        <h2>Olá, {voluntariado.usuario.nome}!</h2>
        <p>Obrigado pelo seu interesse em ser voluntário na <strong>{current_user.nome}</strong>.</p>
        <p>Infelizmente, no momento <strong>não estamos precisando de pessoas com suas habilidades específicas</strong>.</p>
        <p>Mas não desanime! Continue buscando oportunidades - outras ONGs certamente precisarão do seu talento! 💪</p>
        <p>Atenciosamente,<br>Equipe {current_user.nome}</p>
        """

        # ⚠️ ENVIA EMAIL EM BACKGROUND - NÃO TRAVA A PÁGINA
        thread = threading.Thread(
            target=enviar_email,
            args=(voluntariado.usuario.email, assunto, corpo)
        )
        thread.start()

        flash('Voluntário recusado! Notificação sendo enviada.', 'info')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Erro ao recusar voluntário: {e}', 'error')
        return redirect(url_for('dashboard'))


# 🔽🔽🔽 ADICIONE ESTAS ROTAS DE DEBUG 🔽🔽🔽

@app.route('/debug-login', methods=['POST'])
def debug_login():
    """Rota para debug do login"""
    email = request.form['email']
    senha = request.form['senha']
    tipo = request.form['tipo']

    print(f"🔍 DEBUG LOGIN: Email={email}, Tipo={tipo}")

    if tipo == 'usuario':
        user = Usuario.query.filter_by(email=email).first()
        user_type = "Usuario"
    else:
        user = ONG.query.filter_by(email=email).first()
        user_type = "ONG"

    if user:
        print(f"✅ USUÁRIO ENCONTRADO: {user.nome} (Tipo: {user_type})")
        print(f"   ID: {user.id}, Tem CNPJ: {hasattr(user, 'cnpj')}")

        if check_password_hash(user.senha, senha):
            login_user(user)
            print(f"🎯 LOGIN BEM SUCEDIDO: {user.nome}")
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'nome': user.nome,
                    'tipo': user_type,
                    'tem_cnpj': hasattr(user, 'cnpj')
                }
            })
        else:
            print("❌ SENHA INCORRETA")
    else:
        print("❌ USUÁRIO NÃO ENCONTRADO")

    return jsonify({'success': False})


@app.route('/debug-current-user')
@login_required
def debug_current_user():
    """Mostra informações do usuário atual"""
    user_info = {
        'id': current_user.id,
        'nome': current_user.nome,
        'email': current_user.email,
        'classe': current_user.__class__.__name__,
        'tem_cnpj': hasattr(current_user, 'cnpj'),
        'cnpj': getattr(current_user, 'cnpj', 'N/A'),
        'is_authenticated': current_user.is_authenticated
    }
    print(f"🔍 CURRENT USER: {user_info}")
    return jsonify(user_info)


@app.route('/teste-login')
def teste_login():
    """Página de teste de login"""
    return '''
    <h1>Teste de Login</h1>
    <form action="/debug-login" method="post">
        <input type="email" name="email" placeholder="Email" required><br>
        <input type="password" name="senha" placeholder="Senha" required><br>
        <select name="tipo">
            <option value="usuario">Usuário</option>
            <option value="ong">ONG</option>
        </select><br>
        <button type="submit">Login Debug</button>
    </form>
    <p><a href="/debug-current-user">Ver usuário atual</a></p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)