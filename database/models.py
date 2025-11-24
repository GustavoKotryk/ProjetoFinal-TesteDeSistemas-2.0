from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    cidade = db.Column(db.String(50), nullable=False)
    habilidades = db.Column(db.Text)  # JSON como string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_habilidades(self):
        return json.loads(self.habilidades) if self.habilidades else []

    def set_habilidades(self, habilidades_list):
        self.habilidades = json.dumps(habilidades_list)


class ONG(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True)
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    descricao = db.Column(db.Text)
    causas = db.Column(db.Text)  # JSON como string
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_causas(self):
        return json.loads(self.causas) if self.causas else []

    def set_causas(self, causas_list):
        self.causas = json.dumps(causas_list)


class Voluntariado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    ong_id = db.Column(db.Integer, db.ForeignKey('ong.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')  # pendente, aceito, recusado

    usuario = db.relationship('Usuario', backref=db.backref('voluntariados', lazy=True))
    ong = db.relationship('ONG', backref=db.backref('voluntarios', lazy=True))