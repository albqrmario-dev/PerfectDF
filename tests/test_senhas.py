import pymupdf
import pytest

from perfectdf.core import abrir_pdf, proteger_pdf, remover_senha


def test_proteger_pdf_com_senha_usuario(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "protegido.pdf"

    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Documento Ultrassecreto")
    doc.save(str(origem))
    doc.close()

    res = proteger_pdf(str(origem), str(saida), senha_usuario="segredo123")
    assert res == str(saida)

    # Documento de origem continua desprotegido
    doc_orig = abrir_pdf(str(origem))
    assert doc_orig.needs_pass == 0
    assert not doc_orig.is_encrypted
    doc_orig.close()

    # Documento de saída exige senha
    doc_prot = pymupdf.open(str(saida))
    assert doc_prot.needs_pass == 1
    assert doc_prot.is_encrypted

    # Senha errada falha
    assert doc_prot.authenticate("senha_errada") == 0

    # Senha correta tem sucesso e libera conteúdo
    auth_res = doc_prot.authenticate("segredo123")
    assert auth_res > 0
    assert "Documento Ultrassecreto" in doc_prot[0].get_text()
    doc_prot.close()


def test_proteger_pdf_com_senha_usuario_e_dono(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "protegido_duplo.pdf"

    doc = pymupdf.open()
    doc.new_page().insert_text((50, 50), "Dados Confidenciais")
    doc.save(str(origem))
    doc.close()

    proteger_pdf(
        str(origem),
        str(saida),
        senha_usuario="usuario123",
        senha_dono="admin456",
    )

    doc_user = pymupdf.open(str(saida))
    assert doc_user.authenticate("usuario123") == 2
    doc_user.close()

    doc_owner = pymupdf.open(str(saida))
    assert doc_owner.authenticate("admin456") >= 4
    doc_owner.close()


def test_remover_senha_sucesso(tmp_path):
    origem = tmp_path / "origem.pdf"
    protegido = tmp_path / "protegido.pdf"
    desprotegido = tmp_path / "desprotegido.pdf"

    doc = pymupdf.open()
    doc.new_page().insert_text((50, 50), "Conteúdo Desbloqueado")
    doc.save(str(origem))
    doc.close()

    proteger_pdf(str(origem), str(protegido), senha_usuario="abracadabra")

    res = remover_senha(str(protegido), "abracadabra", str(desprotegido))
    assert res == str(desprotegido)

    # Documento desprotegido abre sem necessidade de autenticação
    doc_livre = abrir_pdf(str(desprotegido))
    assert doc_livre.needs_pass == 0
    assert not doc_livre.is_encrypted
    assert "Conteúdo Desbloqueado" in doc_livre[0].get_text()
    doc_livre.close()

    # O arquivo protegido original mantém sua senha
    doc_ainda_prot = pymupdf.open(str(protegido))
    assert doc_ainda_prot.needs_pass == 1
    doc_ainda_prot.close()


def test_remover_senha_erros_especificos(tmp_path):
    sem_senha = tmp_path / "sem_senha.pdf"
    protegido = tmp_path / "protegido.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(sem_senha))
    doc.close()

    proteger_pdf(str(sem_senha), str(protegido), senha_usuario="chave123")

    # Tentar remover senha de PDF que não tem senha
    with pytest.raises(ValueError, match="não possui proteção por senha"):
        remover_senha(str(sem_senha), "qualquer", str(saida))

    # Tentar remover com senha incorreta
    with pytest.raises(ValueError, match="senha informada está incorreta"):
        remover_senha(str(protegido), "chave_errada", str(saida))


def test_senhas_nao_vazam_em_erros_e_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    senha_secreta = "MinhaSenhaSuperSecreta999"

    # Validações de senhas vazias ou não strings
    with pytest.raises(ValueError, match="string não vazia") as exc_info:
        proteger_pdf(str(origem), str(saida), "")
    assert senha_secreta not in str(exc_info.value)

    with pytest.raises(ValueError, match="string não vazia") as exc_info:
        proteger_pdf(str(origem), str(saida), senha_secreta, senha_dono="")
    assert senha_secreta not in str(exc_info.value)

    with pytest.raises(ValueError, match="string não vazia") as exc_info:
        remover_senha(str(origem), "", str(saida))
    assert senha_secreta not in str(exc_info.value)

    # Verifica que em senha incorreta a senha fornecida não vaza na mensagem
    prot = tmp_path / "prot.pdf"
    proteger_pdf(str(origem), str(prot), senha_usuario="certa")
    with pytest.raises(ValueError) as exc_info:
        remover_senha(str(prot), senha_secreta, str(saida))
    assert senha_secreta not in str(exc_info.value)

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        proteger_pdf(str(origem), str(origem), "senha")
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        remover_senha(str(prot), "certa", str(prot))

    # Arquivo inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        proteger_pdf(str(tmp_path / "inexistente.pdf"), str(saida), "senha")
    with pytest.raises(ValueError, match="não foi encontrado"):
        remover_senha(str(tmp_path / "inexistente.pdf"), "senha", str(saida))
