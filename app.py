from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, Usuario, ONG, Voluntariado
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)

# Inicializações
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    # Tenta carregar como Usuario, depois como ONG
    user = Usuario.query.get(int(user_id))
    if user:
        return user
    return ONG.query.get(int(user_id))


# Rotas Públicas
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cadastro/usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        telefone = request.form['telefone']
        cidade = request.form['cidade']
        habilidades = request.form.getlist('habilidades')

        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('cadastro_usuario'))

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            telefone=telefone,
            cidade=cidade
        )
        usuario.set_habilidades(habilidades)

        db.session.add(usuario)
        db.session.commit()

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro_usuario.html')


@app.route('/cadastro/ong', methods=['GET', 'POST'])
def cadastro_ong():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        cnpj = request.form['cnpj']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        cidade = request.form['cidade']
        estado = request.form['estado']
        descricao = request.form['descricao']
        causas = request.form.getlist('causas')
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        if ONG.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('cadastro_ong'))

        ong = ONG(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            cnpj=cnpj,
            telefone=telefone,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            descricao=descricao,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None
        )
        ong.set_causas(causas)

        db.session.add(ong)
        db.session.commit()

        flash('ONG cadastrada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro_ong.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']

        if tipo == 'usuario':
            user = Usuario.query.filter_by(email=email).first()
        else:
            user = ONG.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            flash(f'Login realizado com sucesso!', 'success')
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


# Rotas Protegidas
@app.route('/dashboard')
@login_required
def dashboard():
    if hasattr(current_user, 'cnpj'):  # É ONG
        voluntarios = Voluntariado.query.filter_by(ong_id=current_user.id).all()
        return render_template('dashboard.html', voluntarios=voluntarios, is_ong=True)
    else:  # É Usuário
        voluntariados = Voluntariado.query.filter_by(usuario_id=current_user.id).all()
        return render_template('dashboard.html', voluntariados=voluntariados, is_ong=False)


@app.route('/buscar-ongs')
@login_required
def buscar_ongs():
    cidade = request.args.get('cidade', '')
    causa = request.args.get('causa', '')

    query = ONG.query

    if cidade:
        query = query.filter(ONG.cidade.ilike(f'%{cidade}%'))
    if causa:
        query = query.filter(ONG.causas.ilike(f'%{causa}%'))

    ongs = query.all()
    return render_template('buscar_ongs.html', ongs=ongs)


@app.route('/voluntariar/<int:ong_id>')
@login_required
def voluntariar(ong_id):
    if hasattr(current_user, 'cnpj'):  # ONG não pode se voluntariar
        flash('ONGs não podem se voluntariar!', 'error')
        return redirect(url_for('dashboard'))

    # Verifica se já existe inscrição
    existing = Voluntariado.query.filter_by(
        usuario_id=current_user.id,
        ong_id=ong_id
    ).first()

    if existing:
        flash('Você já se candidatou para esta ONG!', 'warning')
        return redirect(url_for('buscar_ongs'))

    voluntariado = Voluntariado(
        usuario_id=current_user.id,
        ong_id=ong_id
    )

    db.session.add(voluntariado)
    db.session.commit()

    flash('Candidatura enviada com sucesso!', 'success')
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)