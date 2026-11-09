import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ErroAPI(Exception):
    def __init__(self, codigo: int, detalhe):
        self.codigo = codigo
        self.detalhe = detalhe
        if isinstance(detalhe, dict):
            mensagem = detalhe.get("mensagem", str(detalhe))
        elif isinstance(detalhe, list):
            mensagem = "; ".join(
                f"{'.'.join(str(p) for p in erro.get('loc', []))}: {erro.get('msg', '')}"
                for erro in detalhe
            )
        else:
            mensagem = str(detalhe)
        super().__init__(mensagem)


class ClienteAPI:
    def __init__(self, endereco: str = "http://127.0.0.1:8000"):
        self.endereco = endereco.rstrip("/")

    def requisitar(self, metodo: str, caminho: str, dados=None, parametros=None):
        url = self.endereco + caminho
        if parametros:
            url += "?" + urlencode(parametros)
        corpo = json.dumps(dados).encode("utf-8") if dados is not None else None
        pedido = Request(url, data=corpo, method=metodo, headers={"Content-Type": "application/json"})
        try:
            with urlopen(pedido, timeout=10) as resposta:
                conteudo = resposta.read()
                return json.loads(conteudo) if conteudo else None
        except HTTPError as erro:
            with erro:
                conteudo = erro.read()
            try:
                detalhe = json.loads(conteudo).get("detail", "Não foi possível concluir a operação.")
            except (ValueError, AttributeError):
                detalhe = "Não foi possível concluir a operação."
            raise ErroAPI(erro.code, detalhe) from erro
        except (URLError, TimeoutError, OSError) as erro:
            raise ConnectionError(
                "Não foi possível acessar a API. Confira se o servidor está rodando e tente novamente."
            ) from erro
