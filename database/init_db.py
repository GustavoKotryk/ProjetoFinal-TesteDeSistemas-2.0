from app import app, db
from database.models import Usuario, ONG
from werkzeug.security import generate_password_hash


def init_database():
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")

        # Verificar se já existem dados
        if not Usuario.query.first():
            # Criar usuário de exemplo
            usuario_exemplo = Usuario(
                nome="João Silva",
                email="joao@exemplo.com",
                senha=generate_password_hash("123456"),
                telefone="(11) 99999-9999",
                cidade="São Paulo"
            )
            usuario_exemplo.set_habilidades(["Ensino", "TI"])
            db.session.add(usuario_exemplo)

            # Criar ONG de exemplo
            ong_exemplo = ONG(
                nome="ONG Amigos dos Animais",
                email="contato@amigosdosanimais.org",
                senha=generate_password_hash("123456"),
                cnpj="12.345.678/0001-90",
                telefone="(11) 3333-3333",
                endereco="Rua dos Bichos, 123",
                cidade="São Paulo",
                estado="SP",
                descricao="Ajudamos animais em situação de rua e promovemos adoção responsável.",
                latitude=-23.5505,
                longitude=-46.6333
            )
            ong_exemplo.set_causas(["Animais"])
            db.session.add(ong_exemplo)

            db.session.commit()
            print("✅ Dados de exemplo criados!")

        print("Banco de dados inicializado com sucesso!")


if __name__ == '__main__':
    init_database()