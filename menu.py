from cliente_api import ClienteAPI, ErroAPI


STATUS = ("Quero ler", "Lendo", "Lido", "Relendo", "Abandonado")


def texto_obrigatorio(pergunta: str) -> str:
    while True:
        texto = input(pergunta).strip()
        if texto:
            return texto
        print("Preencha este campo.")


def confirmar(pergunta: str) -> bool:
    return input(f"{pergunta} [s/N]: ").strip().casefold() in {"s", "sim"}


def escolher_id(itens: list[dict], pergunta: str) -> int | None:
    ids = {item["id"] for item in itens}
    while True:
        resposta = input(f"{pergunta} (0 para voltar): ").strip()
        if resposta == "0":
            return None
        if resposta.isdecimal() and int(resposta) in ids:
            return int(resposta)
        print("Escolha um dos IDs exibidos.")


def escolher_status() -> str | None:
    print("\nStatus de leitura:")
    opcoes = [{"id": indice, "nome": nome} for indice, nome in enumerate(STATUS, 1)]
    for opcao in opcoes:
        print(f"{opcao['id']}. {opcao['nome']}")
    escolhido = escolher_id(opcoes, "Escolha o status")
    return STATUS[escolhido - 1] if escolhido is not None else None


def escolher_generos(api: ClienteAPI, edicao: bool = False) -> list[int] | None:
    generos = api.requisitar("GET", "/generos")
    if not generos:
        print("O catálogo de gêneros está vazio. Não é possível concluir o cadastro ou edição.")
        raise ValueError("Catálogo de gêneros indisponível.")
    print("\nGêneros disponíveis:")
    for genero in generos:
        print(f"{genero['id']}. {genero['nome']}")
    ids_validos = {genero["id"] for genero in generos}
    while True:
        complemento = "; Enter mantém os atuais" if edicao else ""
        resposta = input(f"IDs separados por vírgula (0 para cancelar{complemento}): ").strip()
        if resposta == "0":
            return None
        if not resposta and edicao:
            return []
        partes = [parte.strip() for parte in resposta.split(",")]
        if all(parte.isdecimal() for parte in partes):
            ids = list(dict.fromkeys(int(parte) for parte in partes))
            if ids and set(ids) <= ids_validos:
                return ids
        print("Escolha pelo menos um dos IDs exibidos, separado por vírgula.")


def mostrar_livro(livro: dict) -> None:
    autores = ", ".join(autor["nome"] for autor in livro["autores"])
    generos = ", ".join(genero["nome"] for genero in livro["generos"])
    print(f"\n[{livro['id']}] {livro['titulo']} — {livro['status']}")
    print(f"Autores: {autores}\nGêneros: {generos}")


def consultar_biblioteca(api: ClienteAPI, parametros=None) -> list[dict]:
    resposta = api.requisitar("GET", "/livros", parametros=parametros)
    print(resposta["mensagem"])
    for livro in resposta["livros"]:
        mostrar_livro(livro)
    return resposta["livros"]


def selecionar_livro(api: ClienteAPI) -> dict | None:
    livros = consultar_biblioteca(api)
    if not livros:
        return None
    escolhido = escolher_id(livros, "Escolha o livro")
    return next((livro for livro in livros if livro["id"] == escolhido), None)


def alterar_status(api: ClienteAPI, livro: dict | None = None) -> None:
    if livro is None:
        livro = selecionar_livro(api)
    if livro is None:
        return
    status = escolher_status()
    if status is None:
        return
    atualizado = api.requisitar("PATCH", f"/livros/{livro['id']}/status", {"status": status})
    print("Status atualizado.")
    mostrar_livro(atualizado)


def cadastrar_livro(api: ClienteAPI) -> None:
    titulo = texto_obrigatorio("Título: ")
    print("Separe vários autores por ponto e vírgula. Em branco: Autor desconhecido.")
    autores = [nome.strip() for nome in input("Autores: ").split(";") if nome.strip()]
    generos = escolher_generos(api)
    if generos is None:
        return
    status = escolher_status()
    if status is None:
        return
    try:
        resposta = api.requisitar("POST", "/livros", {
            "titulo": titulo, "autores": autores, "genero_ids": generos, "status": status,
        })
    except ErroAPI as erro:
        if erro.codigo != 409 or not isinstance(erro.detalhe, dict) or "livro" not in erro.detalhe:
            raise
        existente = erro.detalhe["livro"]
        mostrar_livro(existente)
        if confirmar("Este livro já está cadastrado. Deseja alterar o status?"):
            alterar_status(api, existente)
        return
    print(resposta["mensagem"])
    mostrar_livro(resposta["livro"])
    if resposta["autores_reutilizados"]:
        print("Autores já cadastrados reutilizados: " + ", ".join(
            autor["nome"] for autor in resposta["autores_reutilizados"]
        ))


def selecionar_autor(api: ClienteAPI) -> dict | None:
    termo = input("Parte do nome do autor (Enter lista todos): ").strip()
    autores = api.requisitar("GET", "/autores", parametros={"nome": termo} if termo else None)
    if not autores:
        print("Nenhum autor encontrado.")
        return None
    for autor in autores:
        print(f"[{autor['id']}] {autor['nome']}")
    escolhido = escolher_id(autores, "Escolha o autor")
    return next((autor for autor in autores if autor["id"] == escolhido), None)


def buscar_por_autor(api: ClienteAPI) -> None:
    autor = selecionar_autor(api)
    if autor is not None:
        consultar_biblioteca(api, {"autor_id": autor["id"]})


def editar_livro(api: ClienteAPI) -> None:
    livro = selecionar_livro(api)
    if livro is None:
        return
    print("Deixe em branco para manter o valor atual.")
    titulo = input("Novo título: ").strip()
    nomes = input("Autores finais, separados por ponto e vírgula: ")
    autores = [nome.strip() for nome in nomes.split(";") if nome.strip()]
    print("Se escolher gêneros, envie a seleção completa que o livro deverá ter.")
    generos = escolher_generos(api, edicao=True)
    if generos is None:
        return
    dados = {}
    if titulo:
        dados["titulo"] = titulo
    if autores:
        print("A lista de autores informada substituirá os vínculos atuais.")
        dados["autores"] = autores
    if generos:
        dados["genero_ids"] = generos
    if not dados:
        print("Nenhuma alteração informada.")
        return
    if confirmar("Salvar as alterações desse livro?"):
        mostrar_livro(api.requisitar("PATCH", f"/livros/{livro['id']}", dados))
        print("Livro atualizado.")


def excluir_livro(api: ClienteAPI) -> None:
    livro = selecionar_livro(api)
    if livro is not None and confirmar(f"Excluir definitivamente '{livro['titulo']}'?"):
        api.requisitar("DELETE", f"/livros/{livro['id']}")
        print("Livro excluído. Autores e gêneros foram preservados.")


def gerenciar_autores(api: ClienteAPI) -> None:
    while True:
        print("\nAutores\n1. Consultar\n2. Cadastrar\n3. Editar nome\n4. Excluir\n0. Voltar")
        opcao = input("Opção: ").strip()
        if opcao == "0":
            return
        try:
            if opcao == "1":
                selecionar_autor(api)
            elif opcao == "2":
                nome = texto_obrigatorio("Nome do autor: ")
                autor = api.requisitar("POST", "/autores", {"nome": nome})
                print(f"Autor cadastrado: [{autor['id']}] {autor['nome']}")
            elif opcao in {"3", "4"}:
                autor = selecionar_autor(api)
                if autor is None:
                    continue
                caminho = f"/autores/{autor['id']}"
                if opcao == "3":
                    print("A mudança de nome aparecerá em todos os livros desse autor.")
                    nome = texto_obrigatorio("Novo nome: ")
                    if confirmar("Confirmar alteração do autor?"):
                        api.requisitar("PATCH", caminho, {"nome": nome})
                        print("Autor atualizado.")
                elif confirmar(f"Excluir o autor '{autor['nome']}'? Só é permitido sem livros vinculados."):
                    api.requisitar("DELETE", caminho)
                    print("Autor excluído.")
            else:
                print("Opção inválida.")
        except (ErroAPI, ConnectionError) as erro:
            print(erro)


def executar(api: ClienteAPI | None = None) -> None:
    api = api or ClienteAPI()
    acoes = {
        "1": cadastrar_livro,
        "2": consultar_biblioteca,
        "3": buscar_por_autor,
        "4": alterar_status,
        "5": gerenciar_autores,
        "6": excluir_livro,
        "7": editar_livro,
    }
    while True:
        print("\nBook Vault\n1. Cadastrar livro\n2. Consultar biblioteca\n3. Buscar livros por autor"
              "\n4. Alterar status de leitura\n5. Gerenciar autores\n6. Excluir livro\n7. Editar livro\n0. Sair")
        opcao = input("Opção: ").strip()
        if opcao == "0":
            print("Até a próxima leitura!")
            return
        acao = acoes.get(opcao)
        if acao is None:
            print("Opção inválida.")
            continue
        try:
            acao(api)
        except (ErroAPI, ConnectionError, ValueError) as erro:
            print(erro)


if __name__ == "__main__":
    try:
        executar()
    except (KeyboardInterrupt, EOFError):
        print("\nMenu encerrado.")
