from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import StatusLeitura


IdPositivo = Annotated[int, Field(strict=True, gt=0)]


class AutorCadastro(BaseModel):
    nome: str = Field(min_length=1)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        if not nome.strip():
            raise ValueError("O nome do autor não pode estar vazio.")
        return nome


class AutorConsulta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class GeneroConsulta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class EntradaStatus(BaseModel):
    status: StatusLeitura = Field(
        description="Escolha: Quero ler, Lendo, Lido, Relendo ou Abandonado."
    )

    @field_validator("status", mode="before")
    @classmethod
    def validar_status(cls, status: object) -> object:
        if status not in [opcao.value for opcao in StatusLeitura]:
            raise ValueError(
                "Status inválido: essa opção não existe. Escolha uma das opções: "
                "Quero ler, Lendo, Lido, Relendo ou Abandonado."
            )
        return status


class LivroStatusAlteracao(EntradaStatus):
    model_config = ConfigDict(extra="forbid")


class LivroCadastro(EntradaStatus):
    titulo: str = Field(min_length=1)
    autores: list[str] = Field(
        default_factory=list,
        description=(
            "Informe os nomes dos autores. Se nenhum autor for informado, "
            "o livro será cadastrado como Autor desconhecido."
        ),
    )
    genero_ids: list[IdPositivo] = Field(
        min_length=1,
        description="Escolha pelo menos um ID do catálogo retornado por GET /generos.",
    )

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, titulo: str) -> str:
        titulo = " ".join(titulo.split())
        if not titulo:
            raise ValueError("O título não pode estar vazio.")
        return titulo

    @field_validator("autores")
    @classmethod
    def preparar_autores(cls, autores: list[str]) -> list[str]:
        # Nomes vazios não representam autores. Preservamos os demais para exibição.
        return [nome for nome in autores if nome.strip()]

class LivroEdicao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1)
    autores: list[str] | None = Field(
        default=None,
        description="Substitui os autores. Omitir ou enviar lista vazia/nomes em branco preserva os atuais.",
    )
    genero_ids: list[IdPositivo] | None = Field(default=None, min_length=1)

    @field_validator("titulo", "autores", "genero_ids", mode="before")
    @classmethod
    def rejeitar_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Omita o campo para preservar o valor atual; null não é permitido.")
        return valor

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, titulo: str) -> str:
        return LivroCadastro.validar_titulo(titulo)

    @field_validator("autores")
    @classmethod
    def preparar_autores(cls, autores: list[str]) -> list[str]:
        return LivroCadastro.preparar_autores(autores)


class LivroConsulta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    autores: list[AutorConsulta]
    generos: list[GeneroConsulta]
    status: StatusLeitura


class BibliotecaConsulta(BaseModel):
    mensagem: str
    livros: list[LivroConsulta]


class LivroCadastrado(BaseModel):
    mensagem: str
    livro: LivroConsulta
    autores_reutilizados: list[AutorConsulta]
