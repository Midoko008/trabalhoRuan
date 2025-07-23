from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Corredor(db.Model):
    __tablename__ = 'corredor'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    cep = db.Column(db.String(9))
    cpf = db.Column(db.String(14))
    data_nascimento = db.Column(db.Date)
    idade = db.Column(db.Integer)
    senha_hash = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='comum')

    tenis = db.relationship('Tenis', backref='corredor')

    @staticmethod
    def calcular_idade(data_nascimento):
        hoje = date.today()
        return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

    def to_dict_completo(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'cep': self.cep,
            'cpf': self.cpf,
            'data_nascimento': self.data_nascimento.strftime('%Y-%m-%d') if self.data_nascimento else None,
            'idade': self.idade,
            'tipo': self.tipo
        }

    def to_dict_publico(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'idade': self.idade
        }

class Estilo(db.Model):
    __tablename__ = 'estilo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

    tenis = db.relationship('Tenis', back_populates='estilo', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Estilo {self.nome}>'

class Tenis(db.Model):
    __tablename__ = 'tenis'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    imagem_url = db.Column(db.String(255))
    estoque = db.Column(db.Integer, nullable=False)
    tamanho = db.Column(db.Float, nullable=False)

    corredor_id = db.Column(db.Integer, db.ForeignKey('corredor.id'), nullable=False)
    estilo_id = db.Column(db.Integer, db.ForeignKey('estilo.id'), nullable=True)

    estilo = db.relationship('Estilo', back_populates='tenis')
    armario_items = db.relationship('Armario', back_populates='tenis', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tenis {self.nome}>'

class Armario(db.Model):
    __tablename__ = 'armario'

    id = db.Column(db.Integer, primary_key=True)
    tenis_id = db.Column(db.Integer, db.ForeignKey('tenis.id'), nullable=False)

    tenis = db.relationship('Tenis', back_populates='armario_items')

    def __repr__(self):
        return f'<Armario tenis_id={self.tenis_id}>'
