from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-super-secreta-aqui'

# Configuração do Banco - SIMPLIFICADA
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///voluntariado.db')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializações
db = SQLAlchemy(app)
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
        return str(self.id)

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
        return str(self.id)

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
    user = Usuario.query.get(int(user_id))
    if user:
        return user
    return ONG.query.get(int(user_id))


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

        user = Usuario.query.filter_by(email=email).first() if tipo == 'usuario' else ONG.query.filter_by(
            email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
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
        if hasattr(current_user, 'cnpj'):
            voluntarios = Voluntariado.query.filter_by(ong_id=current_user.id).all()
            return render_template('dashboard.html', voluntarios=voluntarios, is_ong=True)
        else:
            voluntariados = Voluntariado.query.filter_by(usuario_id=current_user.id).all()
            return render_template('dashboard.html', voluntariados=voluntariados, is_ong=False)
    except Exception as e:
        return f"<h1>Erro no Dashboard</h1><p>{e}</p>"


@app.route('/buscar-ongs')
@login_required
def buscar_ongs():
    ongs = ONG.query.all()
    return render_template('buscar_ongs.html', ongs=ongs)


@app.route('/voluntariar/<int:ong_id>')
@login_required
def voluntariar(ong_id):
    if hasattr(current_user, 'cnpj'):
        flash('ONGs não podem se voluntariar!', 'error')
        return redirect(url_for('dashboard'))

    voluntariado = Voluntariado(usuario_id=current_user.id, ong_id=ong_id)
    db.session.add(voluntariado)
    db.session.commit()
    flash('Candidatura enviada!', 'success')
    return redirect(url_for('dashboard'))


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)