from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Corredor, Tenis, Armario, Estilo
from datetime import datetime
import bcrypt

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://ruantopzera:RuanOBrabo2025@localhost/tenisTops'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Função para obter o corredor logado a partir do header Authorization (Bearer <user_id>)
def get_corredor_logado():
    auth = request.headers.get('Authorization')
    if not auth:
        return None
    try:
        token_type, user_id = auth.split()
        if token_type.lower() != 'bearer':
            return None
        user_id_int = int(user_id)
        return Corredor.query.get(user_id_int)
    except Exception:
        return None

# --- Rotas Corredor ---

@app.route('/cadastro', methods=['POST'])
def cadastrar_corredor():
    dados = request.json
    try:
        nascimento = datetime.strptime(dados['data_nascimento'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        return jsonify({'erro': 'Data de nascimento inválida ou não informada'}), 400

    idade = Corredor.calcular_idade(nascimento)
    senha = dados.get('senha', '')
    if not senha:
        return jsonify({'erro': 'Senha não informada'}), 400

    senha_bytes = senha.encode('utf-8')
    senha_criptografada = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())

    novo_corredor = Corredor(
        nome=dados.get('nome'),
        email=dados.get('email'),
        cep=dados.get('cep'),
        cpf=dados.get('cpf'),
        data_nascimento=nascimento,
        idade=idade,
        senha_hash=senha_criptografada.decode('utf-8'),
        tipo='comum'
    )

    try:
        db.session.add(novo_corredor)
        db.session.commit()
        return jsonify({'mensagem': 'Corredor cadastrado com sucesso!'}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao cadastrar corredor'}), 500

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    corredor = Corredor.query.filter_by(email=dados.get('email')).first()

    if corredor and bcrypt.checkpw(dados.get('senha', '').encode(), corredor.senha_hash.encode()):
        return jsonify({
            'mensagem': 'Login bem-sucedido',
            'usuario': {
                'id': corredor.id,
                'nome': corredor.nome,
                'email': corredor.email,
                'cep': corredor.cep,
                'cpf': corredor.cpf,
                'data_nascimento': corredor.data_nascimento.strftime('%Y-%m-%d'),
                'idade': corredor.idade,
                'tipo': corredor.tipo
            }
        }), 200

    return jsonify({'erro': 'E-mail ou senha inválidos'}), 401

@app.route('/usuarios/<int:id>', methods=['GET'])
def obter_corredor(id):
    corredor = Corredor.query.get_or_404(id)
    corredor_logado = get_corredor_logado()
    if not corredor_logado:
        return jsonify({'erro': 'Usuário não autenticado'}), 401

    if corredor_logado.id == corredor.id or corredor_logado.tipo == 'admin':
        return jsonify(corredor.to_dict_completo())
    else:
        return jsonify(corredor.to_dict_publico())

@app.route('/usuarios/me', methods=['GET'])
def obter_meu_perfil():
    corredor_logado = get_corredor_logado()
    if not corredor_logado:
        return jsonify({'erro': 'Usuário não autenticado'}), 401
    return jsonify(corredor_logado.to_dict_completo())

@app.route('/usuarios/<int:id>', methods=['PUT'])
def atualizar_corredor(id):
    corredor_logado = get_corredor_logado()
    if not corredor_logado:
        return jsonify({'erro': 'Usuário não autenticado'}), 401
    if corredor_logado.id != id and corredor_logado.tipo != 'admin':
        return jsonify({'erro': 'Acesso negado'}), 403

    dados = request.json
    corredor = Corredor.query.get_or_404(id)
    if 'nome' in dados:
        corredor.nome = dados['nome']
    if 'email' in dados:
        corredor.email = dados['email']

    try:
        db.session.commit()
        return jsonify({'mensagem': 'Dados atualizados com sucesso'})
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao atualizar usuário'}), 500

# --- Rotas Estilo ---

@app.route('/categorias', methods=['GET'])
def listar_estilos():
    estilos = Estilo.query.all()
    return jsonify([{'id': e.id, 'nome': e.nome} for e in estilos])

@app.route('/categorias', methods=['POST'])
def criar_estilo():
    dados = request.json
    nome = dados.get('nome')
    if not nome:
        return jsonify({'erro': 'Nome do estilo é obrigatório'}), 400

    existente = Estilo.query.filter_by(nome=nome).first()
    if existente:
        return jsonify({'erro': 'Estilo já existe'}), 400

    novo_estilo = Estilo(nome=nome)
    try:
        db.session.add(novo_estilo)
        db.session.commit()
        return jsonify({'mensagem': 'Estilo criado', 'id': novo_estilo.id}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao criar estilo'}), 500

# --- Rotas Tenis ---

@app.route('/produtos', methods=['GET'])
def listar_tenis():
    tenis = Tenis.query.all()
    lista = []
    for t in tenis:
        lista.append({
            'id': t.id,
            'nome': t.nome,
            'preco': t.preco,
            'imagem_url': t.imagem_url,
            'estoque': t.estoque,
            'categoria': {
                'id': t.estilo.id if t.estilo else None,
                'nome': t.estilo.nome if t.estilo else None
            }
        })
    return jsonify(lista)

@app.route('/produtos/<int:id>', methods=['GET'])
def obter_tenis(id):
    t = Tenis.query.get(id)
    if not t:
        return jsonify({'erro': 'Tênis não encontrado'}), 404
    return jsonify({
        'id': t.id,
        'nome': t.nome,
        'preco': t.preco,
        'imagem_url': t.imagem_url,
        'estoque': t.estoque,
        'categoria': {
            'id': t.estilo.id if t.estilo else None,
            'nome': t.estilo.nome if t.estilo else None
        },
        'usuario': {
            'id': t.corredor.id,
            'nome': t.corredor.nome
        }
    })

@app.route('/produtos', methods=['POST'])
def criar_tenis():
    corredor_logado = get_corredor_logado()
    if not corredor_logado:
        return jsonify({'erro': 'Usuário não autenticado'}), 401

    dados = request.json
    nome = dados.get('nome')
    preco = dados.get('preco')
    imagem_url = dados.get('imagem_url')
    estoque = dados.get('estoque')
    estilo_id = dados.get('categoria_id')

    if not nome or preco is None or not imagem_url or estoque is None or not estilo_id:
        return jsonify({'erro': 'Dados incompletos'}), 400

    try:
        preco = float(preco)
        estoque = int(estoque)
        estilo_id = int(estilo_id)
        if estoque <= 0:
            return jsonify({'erro': 'Estoque deve ser maior que zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'erro': 'Preço, estoque ou estilo inválidos'}), 400

    estilo = Estilo.query.get(estilo_id)
    if not estilo:
        return jsonify({'erro': 'Estilo não encontrado'}), 404

    novo_tenis = Tenis(
        nome=nome,
        preco=preco,
        imagem_url=imagem_url,
        estoque=estoque,
        estilo_id=estilo_id,
        corredor_id=corredor_logado.id
    )

    try:
        db.session.add(novo_tenis)
        db.session.commit()
        return jsonify({'mensagem': 'Tênis criado com sucesso!'}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao salvar tênis'}), 500

@app.route('/produtos/<int:id>', methods=['DELETE'])
def deletar_tenis(id):
    corredor_logado = get_corredor_logado()
    if not corredor_logado:
        return jsonify({'erro': 'Usuário não autenticado'}), 401

    tenis = Tenis.query.get(id)
    if not tenis:
        return jsonify({'erro': 'Tênis não encontrado'}), 404

    if corredor_logado.id != tenis.corredor_id and corredor_logado.tipo != 'admin':
        return jsonify({'erro': 'Acesso negado'}), 403

    try:
        Armario.query.filter_by(tenis_id=id).delete()
        db.session.delete(tenis)
        db.session.commit()
        return jsonify({'mensagem': 'Tênis deletado com sucesso'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao deletar tênis'}), 500

# --- Armário (sem usuário_id) ---

@app.route('/carrinho', methods=['POST'])
def adicionar_ao_armario():
    dados = request.json
    tenis_id = dados.get('produto_id')
    tenis = Tenis.query.get(tenis_id)
    if not tenis:
        return jsonify({'erro': 'Tênis não encontrado'}), 404
    if tenis.estoque <= 0:
        return jsonify({'erro': 'Tênis sem estoque'}), 400

    try:
        novo_item = Armario(tenis_id=tenis.id)
        tenis.estoque -= 1
        db.session.add(novo_item)
        db.session.commit()
        return jsonify({'mensagem': 'Tênis adicionado ao armário!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao adicionar ao armário', 'detalhe': str(e)}), 500

@app.route('/carrinho', methods=['GET'])
def listar_armario():
    itens = Armario.query.all()
    tenis_lista = []
    valor_total = 0.0

    for item in itens:
        t = Tenis.query.get(item.tenis_id)
        if t:
            valor_total += t.preco
            tenis_lista.append({
                'id': t.id,
                'nome': t.nome,
                'preco': t.preco,
                'imagem_url': t.imagem_url,
                'estoque': t.estoque,
                'categoria': {
                    'id': t.estilo.id if t.estilo else None,
                    'nome': t.estilo.nome if t.estilo else None
                }
            })

    return jsonify({'produtos': tenis_lista, 'valor_total': f"{valor_total:.2f}"})

@app.route('/carrinho/<int:produto_id>', methods=['DELETE'])
def remover_do_armario(produto_id):
    item = Armario.query.filter_by(tenis_id=produto_id).first()
    if not item:
        return jsonify({'erro': 'Tênis não está no armário'}), 404

    try:
        tenis = Tenis.query.get(produto_id)
        if tenis:
            tenis.estoque += 1
        db.session.delete(item)
        db.session.commit()
        return jsonify({'mensagem': 'Tênis removido do armário!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao remover do armário', 'detalhe': str(e)}), 500

@app.route('/produtos/usuario/<int:usuario_id>', methods=['GET'])
def tenis_por_corredor(usuario_id):
    tenis_lista = Tenis.query.filter_by(corredor_id=usuario_id).all()
    lista = []
    for t in tenis_lista:
        lista.append({
            'id': t.id,
            'nome': t.nome,
            'preco': t.preco,
            'imagem_url': t.imagem_url,
            'estoque': t.estoque,
            'categoria': {
                'id': t.estilo.id if t.estilo else None,
                'nome': t.estilo.nome if t.estilo else None
            }
        })
    return jsonify(lista)

@app.route('/produtos/categoria/<int:categoria_id>', methods=['GET'])
def tenis_por_estilo(categoria_id):
    tenis_lista = Tenis.query.filter_by(estilo_id=categoria_id).all()
    lista = []
    for t in tenis_lista:
        lista.append({
            'id': t.id,
            'nome': t.nome,
            'preco': t.preco,
            'imagem_url': t.imagem_url,
            'estoque': t.estoque,
            'categoria': {
                'id': t.estilo.id if t.estilo else None,
                'nome': t.estilo.nome if t.estilo else None
            }
        })
    return jsonify(lista)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
