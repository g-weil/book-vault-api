// O JavaScript encontra os elementos HTML e preenche a página com dados da API.
const estante = document.querySelector("#estante");
const mensagem = document.querySelector("#mensagem");
const filtro = document.querySelector("#filtro-status");
const atualizar = document.querySelector("#atualizar");
const modal = document.querySelector("#modal-capa");
const formulario = document.querySelector("#form-capa");
let livros = [];
let livroSelecionado = null;
let autorFiltro = null;
let versaoBiblioteca = 0;
let livroFiltroId = null;

async function requisitar(caminho, opcoes = {}) {
  // Uma URL relativa usa o mesmo servidor que entregou o HTML.
  const resposta = await fetch(caminho, opcoes);
  // DELETE bem-sucedido retorna 204, sem JSON para converter.
  if (resposta.status === 204) return null;
  const dados = await resposta.json();
  if (!resposta.ok) {
    const detalhe = dados.detail;
    const texto = Array.isArray(detalhe)
      ? detalhe.map(erro => erro.msg).join(" ")
      : typeof detalhe === "string" ? detalhe : detalhe?.mensagem;
    const erro = new Error(texto || "Não foi possível concluir a operação.");
    erro.codigo = resposta.status;
    erro.detalhe = detalhe;
    throw erro;
  }
  return dados;
}

function criarCard(livro) {
  const card = document.querySelector("#modelo-card").content.cloneNode(true);
  // textContent trata os títulos como texto, nunca como código HTML.
  card.querySelector("h3").textContent = livro.titulo;
  card.querySelector(".placeholder-title").textContent = livro.titulo;
  card.querySelector(".book-authors").textContent = livro.autores.map(autor => autor.nome).join(", ");
  const status = card.querySelector(".status-badge");
  status.textContent = livro.status;
  status.dataset.status = livro.status;
  const generos = card.querySelector(".genres");
  for (const genero of livro.generos) {
    const etiqueta = document.createElement("span");
    etiqueta.className = "genre";
    etiqueta.textContent = genero.nome;
    generos.append(etiqueta);
  }
  const imagem = card.querySelector(".cover-image");
  const padrao = card.querySelector(".cover-placeholder");
  if (livro.capa_url && /^https?:\/\//i.test(livro.capa_url)) {
    imagem.alt = `Capa de ${livro.titulo}`;
    imagem.addEventListener("load", () => { imagem.hidden = false; padrao.hidden = true; });
    imagem.addEventListener("error", () => { imagem.hidden = true; padrao.hidden = false; });
    imagem.src = livro.capa_url;
  }
  const editar = card.querySelector(".cover-button");
  editar.setAttribute("aria-label", `Editar capa de ${livro.titulo}`);
  editar.addEventListener("click", () => abrirModal(livro));
  const editarLivro = card.querySelector(".edit-button");
  editarLivro.setAttribute("aria-label", `Editar ${livro.titulo}`);
  editarLivro.addEventListener("click", () => abrirFormularioLivro(livro));
  const atualizarStatus = card.querySelector(".status-button");
  atualizarStatus.setAttribute("aria-label", `Atualizar status de ${livro.titulo}`);
  atualizarStatus.addEventListener("click", () => abrirModalStatus(livro));
  const excluir = card.querySelector(".delete-button");
  excluir.setAttribute("aria-label", `Excluir ${livro.titulo}`);
  excluir.addEventListener("click", () => abrirModalExclusao(livro));
  return card;
}

function renderizar() {
  estante.replaceChildren();
  // A API filtra por autor. A verificação local mantém a seleção correta após uma edição.
  const porAutor = livros.filter(livro => !autorFiltro || livro.autores.some(autor => autor.id === autorFiltro.id));
  const porLivro = porAutor.filter(livro => !livroFiltroId || livro.id === livroFiltroId);
  const exibidos = porLivro.filter(livro => !filtro.value || livro.status === filtro.value);
  document.querySelector("#quantidade").textContent = String(exibidos.length);
  mensagem.classList.remove("error");
  const buscandoTitulo = Boolean(document.querySelector("#livros-titulo").value.trim());
  mensagem.textContent = !porLivro.length
    ? buscandoTitulo ? "Nenhum livro encontrado para esse título e os filtros atuais."
      : autorFiltro ? "Nenhum livro encontrado para esse autor." : "Sua biblioteca está vazia. Clique em Cadastrar livro para começar."
    : !exibidos.length ? buscandoTitulo ? "Nenhum volume encontrado com o status selecionado."
      : autorFiltro ? "Nenhum livro desse autor com o status selecionado." : "Nenhum livro com esse status na sua estante." : "";
  mensagem.hidden = Boolean(exibidos.length);
  for (const livro of exibidos) estante.append(criarCard(livro));
  atualizarSugestoesTitulos(exibidos);
}

async function carregarBiblioteca() {
  const versao = ++versaoBiblioteca;
  const parametros = new URLSearchParams();
  if (autorFiltro) parametros.set("autor_id", autorFiltro.id);
  const titulo = document.querySelector("#livros-titulo").value.trim();
  if (titulo) parametros.set("titulo", titulo);
  const caminho = parametros.toString() ? `/livros?${parametros}` : "/livros";
  atualizar.disabled = true;
  filtro.disabled = true;
  estante.setAttribute("aria-busy", "true");
  mensagem.hidden = false;
  mensagem.classList.remove("error");
  mensagem.textContent = "Abrindo sua biblioteca…";
  estante.replaceChildren();
  document.querySelector("#quantidade").textContent = "—";
  document.querySelector("#sugestoes-titulos").hidden = true;
  try {
    const dados = await requisitar(caminho);
    if (versao !== versaoBiblioteca) return;
    livros = dados.livros;
    renderizar();
  } catch (erro) {
    if (versao !== versaoBiblioteca) return;
    mensagem.classList.add("error");
    mensagem.textContent = "Não foi possível atualizar sua biblioteca. Confira a conexão e clique em Atualizar.";
    if (titulo) document.querySelector("#mensagem-busca-titulo").textContent = "Não foi possível buscar os títulos. Tente novamente.";
  } finally {
    if (versao === versaoBiblioteca) {
      atualizar.disabled = false;
      filtro.disabled = false;
      estante.setAttribute("aria-busy", "false");
    }
  }
}

function abrirModal(livro) {
  livroSelecionado = livro;
  document.querySelector("#livro-modal").textContent = livro.titulo;
  document.querySelector("#capa-url").value = livro.capa_url || "";
  document.querySelector("#erro-capa").textContent = "";
  modal.showModal();
}

formulario.addEventListener("submit", async evento => {
  evento.preventDefault(); // Salva sem navegar para outra página.
  const botao = document.querySelector("#salvar-capa");
  const campo = document.querySelector("#capa-url");
  const url = campo.value.trim();
  const erro = document.querySelector("#erro-capa");
  if (url && !/^https?:\/\//i.test(url)) {
    erro.textContent = "Use um endereço começando com http:// ou https://.";
    return;
  }
  botao.disabled = true;
  erro.textContent = "";
  try {
    const atualizado = await requisitar(`/livros/${livroSelecionado.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capa_url: url || null }),
    });
    livros = livros.map(livro => livro.id === atualizado.id ? atualizado : livro);
    modal.close();
    renderizar();
  } catch (falha) {
    erro.textContent = falha instanceof TypeError ? "Sem conexão com a API. Tente novamente." : falha.message;
  } finally {
    botao.disabled = false;
  }
});

for (const id of ["fechar-modal", "cancelar-modal"]) {
  document.querySelector(`#${id}`).addEventListener("click", () => modal.close());
}
atualizar.addEventListener("click", carregarBiblioteca);
filtro.addEventListener("change", renderizar);

// O modal transforma entradas HTML em dados para o POST /livros.
const modalCadastro = document.querySelector("#modal-cadastro");
const formCadastro = document.querySelector("#form-cadastro");
const salvarCadastro = document.querySelector("#salvar-cadastro");
const erroCadastro = document.querySelector("#erro-cadastro");
const painelDuplicado = document.querySelector("#cadastro-duplicado");
let cadastroEnviando = false;
let generosDisponiveis = false;
let livroDuplicado = null;
let livroEmEdicao = null;
let versaoCargaGeneros = 0;

function fecharCadastro() {
  if (!cadastroEnviando) modalCadastro.close();
}

function bloquearCadastro(bloquear) {
  cadastroEnviando = bloquear;
  document.querySelector("#campos-cadastro").disabled = bloquear;
  salvarCadastro.disabled = bloquear || !generosDisponiveis || Boolean(livroDuplicado);
  for (const id of ["fechar-cadastro", "cancelar-cadastro", "alterar-duplicado", "nao-alterar-duplicado"]) {
    document.querySelector(`#${id}`).disabled = bloquear;
  }
}

async function carregarGenerosCadastro() {
  const versao = ++versaoCargaGeneros;
  const area = document.querySelector("#cadastro-generos");
  const estado = document.querySelector("#cadastro-carregamento");
  const tentar = document.querySelector("#recarregar-generos");
  generosDisponiveis = false;
  salvarCadastro.disabled = true;
  tentar.hidden = true;
  area.replaceChildren();
  estado.textContent = "Carregando gêneros…";
  try {
    const generos = await requisitar("/generos");
    if (versao !== versaoCargaGeneros) return;
    if (!generos.length) throw new Error("O catálogo de gêneros está vazio.");
    for (const genero of generos) {
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.name = "generos";
      checkbox.value = String(genero.id);
      checkbox.checked = Boolean(livroEmEdicao?.generos.some(item => item.id === genero.id));
      const texto = document.createElement("span");
      texto.textContent = genero.nome;
      label.append(checkbox, texto);
      area.append(label);
    }
    generosDisponiveis = true;
    estado.textContent = "";
    salvarCadastro.disabled = cadastroEnviando || Boolean(livroDuplicado);
  } catch (erro) {
    if (versao !== versaoCargaGeneros) return;
    estado.textContent = "Não foi possível carregar os gêneros. Tente novamente antes de cadastrar.";
    tentar.hidden = false;
  }
}

function abrirFormularioLivro(livro = null) {
  livroEmEdicao = livro;
  formCadastro.reset();
  erroCadastro.textContent = "";
  painelDuplicado.hidden = true;
  livroDuplicado = null;
  document.querySelector("#titulo-cadastro").textContent = livro ? "Editar sua história." : "Um novo livro na estante.";
  document.querySelector("#ajuda-form-livro").textContent = livro
    ? "Corrija os dados e salve. Autores em branco mantêm os atuais; capa em branco remove a imagem."
    : "Preencha os dados da sua próxima história. Campos com * são obrigatórios.";
  document.querySelector("#ajuda-autores").textContent = livro
    ? "Separe por ponto e vírgula. A lista preenchida substitui os autores atuais; em branco, eles são preservados."
    : "Separe os nomes por ponto e vírgula. Se nenhum autor for informado, usaremos Autor desconhecido.";
  document.querySelector("#aviso-edicao").hidden = !livro;
  document.querySelector("#grupo-cadastro-status").hidden = Boolean(livro);
  document.querySelector("#cadastro-status").disabled = Boolean(livro);
  salvarCadastro.textContent = livro ? "Salvar alterações" : "Cadastrar livro";
  if (livro) {
    document.querySelector("#cadastro-titulo").value = livro.titulo;
    document.querySelector("#cadastro-autores").value = livro.autores.map(autor => autor.nome).join("; ");
    document.querySelector("#cadastro-capa").value = livro.capa_url || "";
  }
  modalCadastro.showModal();
  document.querySelector("#cadastro-titulo").focus();
  carregarGenerosCadastro();
}
document.querySelector("#novo-livro").addEventListener("click", () => abrirFormularioLivro());
for (const id of ["fechar-cadastro", "cancelar-cadastro", "nao-alterar-duplicado"]) {
  document.querySelector(`#${id}`).addEventListener("click", fecharCadastro);
}
modalCadastro.addEventListener("cancel", evento => {
  if (cadastroEnviando) evento.preventDefault();
});
document.querySelector("#recarregar-generos").addEventListener("click", carregarGenerosCadastro);

formCadastro.addEventListener("input", () => {
  // Se os dados mudaram, uma nova tentativa precisa verificar a duplicidade novamente.
  livroDuplicado = null;
  painelDuplicado.hidden = true;
  erroCadastro.textContent = "";
  salvarCadastro.disabled = cadastroEnviando || !generosDisponiveis;
});

async function mostrarResultadoCadastro(livro, texto, manterFiltro = false) {
  const tinhaTitulo = Boolean(document.querySelector("#livros-titulo").value.trim());
  const recarregarTodos = !manterFiltro && (Boolean(autorFiltro) || tinhaTitulo);
  const indice = livros.findIndex(item => item.id === livro.id);
  if (indice < 0) livros.push(livro);
  else livros[indice] = livro;
  livros.sort((a, b) => a.id - b.id);
  if (!manterFiltro) {
    filtro.value = "";
    resetarFiltroAutor(); // Novos cadastros devem aparecer, mesmo fora da busca anterior.
    resetarFiltroTitulo();
  } else if (livroFiltroId === livro.id) {
    document.querySelector("#livros-titulo").value = livro.titulo;
    atualizarRotuloTitulo(livro);
  }
  renderizar();
  modalCadastro.close();
  const notificacao = document.querySelector("#notificacao");
  notificacao.textContent = texto;
  notificacao.hidden = false;
  if (recarregarTodos || (manterFiltro && tinhaTitulo)) await carregarBiblioteca();
}

formCadastro.addEventListener("submit", async evento => {
  evento.preventDefault();
  if (cadastroEnviando || !generosDisponiveis || livroDuplicado) return;
  if (!formCadastro.reportValidity()) return;
  const titulo = document.querySelector("#cadastro-titulo").value.trim();
  const autores = document.querySelector("#cadastro-autores").value.split(";")
    .map(nome => nome.trim()).filter(Boolean);
  const generoIds = Array.from(formCadastro.querySelectorAll('input[name="generos"]:checked'))
    .map(campo => Number(campo.value));
  const status = document.querySelector("#cadastro-status").value;
  const capa = document.querySelector("#cadastro-capa").value.trim();
  const emEdicao = Boolean(livroEmEdicao);
  if (!titulo || !generoIds.length || (!emEdicao && !status)) {
    erroCadastro.textContent = emEdicao
      ? "Preencha o título e escolha pelo menos um gênero."
      : "Preencha o título, escolha um status e pelo menos um gênero.";
    return;
  }
  let dados = { titulo, autores, genero_ids: generoIds, status, capa_url: capa || null };
  if (emEdicao) {
    // No PATCH, omitimos valores inalterados para preservar o cadastro atual.
    dados = {};
    if (titulo !== livroEmEdicao.titulo) dados.titulo = titulo;
    const nomesAtuais = livroEmEdicao.autores.map(autor => autor.nome);
    if (autores.length && JSON.stringify(autores) !== JSON.stringify(nomesAtuais)) dados.autores = autores;
    const idsAtuais = livroEmEdicao.generos.map(genero => genero.id);
    if (generoIds.length !== idsAtuais.length || generoIds.some(id => !idsAtuais.includes(id))) dados.genero_ids = generoIds;
    if ((capa || null) !== (livroEmEdicao.capa_url || null)) dados.capa_url = capa || null;
    if (!Object.keys(dados).length) {
      erroCadastro.textContent = "Nenhuma alteração informada.";
      return;
    }
  }
  if (capa && !/^https?:\/\//i.test(capa)) {
    erroCadastro.textContent = "Use um endereço HTTP/HTTPS para a capa ou deixe o campo vazio.";
    return;
  }
  erroCadastro.textContent = "";
  bloquearCadastro(true);
  salvarCadastro.textContent = emEdicao ? "Salvando…" : "Cadastrando…";
  try {
    const resposta = await requisitar(emEdicao ? `/livros/${livroEmEdicao.id}` : "/livros", {
      method: emEdicao ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    if (emEdicao) {
      await mostrarResultadoCadastro(resposta, "Livro atualizado com sucesso.", true);
      return;
    }
    const reutilizados = resposta.autores_reutilizados.map(autor => autor.nome);
    const texto = reutilizados.length
      ? `${resposta.mensagem}. Autores reutilizados: ${reutilizados.join(", ")}.`
      : resposta.mensagem;
    await mostrarResultadoCadastro(resposta.livro, texto);
  } catch (erro) {
    if (!emEdicao && erro.codigo === 409 && erro.detalhe?.livro) {
      livroDuplicado = erro.detalhe.livro;
      document.querySelector("#dados-duplicado").textContent =
        `${livroDuplicado.titulo} · ${livroDuplicado.autores.map(autor => autor.nome).join(", ")} · Status atual: ${livroDuplicado.status}`;
      const mesmoStatus = livroDuplicado.status === status;
      document.querySelector("#pergunta-duplicado").textContent = mesmoStatus
        ? "Este livro já está cadastrado e já possui esse mesmo status."
        : `Deseja alterar o status para “${status}”?`;
      document.querySelector("#alterar-duplicado").hidden = mesmoStatus;
      document.querySelector("#ajuda-duplicado").hidden = mesmoStatus;
      document.querySelector("#nao-alterar-duplicado").textContent = mesmoStatus ? "Fechar" : "Não alterar";
      painelDuplicado.hidden = false;
    } else {
      erroCadastro.textContent = erro instanceof TypeError ? "Sem conexão com a API. Seus dados foram mantidos; tente novamente." : erro.message;
    }
  } finally {
    bloquearCadastro(false);
    salvarCadastro.textContent = emEdicao ? "Salvar alterações" : "Cadastrar livro";
    if (livroDuplicado) {
      const acao = livroDuplicado.status === status ? "nao-alterar-duplicado" : "alterar-duplicado";
      document.querySelector(`#${acao}`).focus();
    }
  }
});

document.querySelector("#alterar-duplicado").addEventListener("click", async () => {
  if (cadastroEnviando || !livroDuplicado) return;
  if (livroDuplicado.status === document.querySelector("#cadastro-status").value) return;
  bloquearCadastro(true);
  erroCadastro.textContent = "";
  try {
    const livro = await requisitar(`/livros/${livroDuplicado.id}/status`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: document.querySelector("#cadastro-status").value }),
    });
    await mostrarResultadoCadastro(livro, "Status do livro existente atualizado.");
  } catch (erro) {
    erroCadastro.textContent = erro instanceof TypeError ? "Sem conexão com a API. Tente novamente." : erro.message;
  } finally {
    bloquearCadastro(false);
  }
});

const modalStatus = document.querySelector("#modal-status");
const formStatus = document.querySelector("#form-status");
const novoStatus = document.querySelector("#novo-status");
const erroStatus = document.querySelector("#erro-status");
const salvarStatus = document.querySelector("#salvar-status");
let livroStatus = null;
let statusEnviando = false;

function abrirModalStatus(livro) {
  livroStatus = livro;
  document.querySelector("#livro-status").textContent = `${livro.titulo} · Status atual: ${livro.status}`;
  novoStatus.value = livro.status;
  erroStatus.textContent = "";
  modalStatus.showModal();
  novoStatus.focus();
}

function bloquearStatus(bloquear) {
  statusEnviando = bloquear;
  novoStatus.disabled = bloquear;
  salvarStatus.disabled = bloquear;
  document.querySelector("#fechar-status").disabled = bloquear;
  document.querySelector("#cancelar-status").disabled = bloquear;
  salvarStatus.textContent = bloquear ? "Salvando…" : "Salvar status";
}

for (const id of ["fechar-status", "cancelar-status"]) {
  document.querySelector(`#${id}`).addEventListener("click", () => {
    if (!statusEnviando) modalStatus.close();
  });
}
modalStatus.addEventListener("cancel", evento => {
  if (statusEnviando) evento.preventDefault();
});
novoStatus.addEventListener("change", () => { erroStatus.textContent = ""; });

formStatus.addEventListener("submit", async evento => {
  evento.preventDefault();
  if (statusEnviando || !livroStatus || !formStatus.reportValidity()) return;
  if (!novoStatus.value) {
    erroStatus.textContent = "Escolha um dos cinco status.";
    return;
  }
  if (novoStatus.value === livroStatus.status) {
    erroStatus.textContent = "Este livro já possui esse status. Nenhuma alteração foi feita.";
    return;
  }
  bloquearStatus(true);
  erroStatus.textContent = "";
  try {
    const livro = await requisitar(`/livros/${livroStatus.id}/status`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: novoStatus.value }),
    });
    livros = livros.map(item => item.id === livro.id ? livro : item);
    renderizar(); // Mantém o filtro: o livro pode deixar de corresponder a ele.
    modalStatus.close();
    const notificacao = document.querySelector("#notificacao");
    notificacao.textContent = `Status de “${livro.titulo}” atualizado para “${livro.status}”.`;
    notificacao.hidden = false;
  } catch (erro) {
    erroStatus.textContent = erro instanceof TypeError
      ? "Sem conexão com a API. A seleção foi mantida; tente novamente."
      : erro.message;
  } finally {
    bloquearStatus(false);
  }
});

const modalExclusao = document.querySelector("#modal-exclusao");
const formExclusao = document.querySelector("#form-exclusao");
const erroExclusao = document.querySelector("#erro-exclusao");
const confirmarExclusao = document.querySelector("#confirmar-exclusao");
let livroExclusao = null;
let exclusaoEnviando = false;

function abrirModalExclusao(livro) {
  livroExclusao = livro;
  document.querySelector("#livro-exclusao").textContent =
    `${livro.titulo} · ${livro.autores.map(autor => autor.nome).join(", ")}`;
  erroExclusao.textContent = "";
  modalExclusao.showModal();
  document.querySelector("#cancelar-exclusao").focus();
}

function bloquearExclusao(bloquear) {
  exclusaoEnviando = bloquear;
  for (const id of ["fechar-exclusao", "cancelar-exclusao", "confirmar-exclusao"]) {
    document.querySelector(`#${id}`).disabled = bloquear;
  }
  confirmarExclusao.textContent = bloquear ? "Excluindo…" : "Excluir definitivamente";
}

for (const id of ["fechar-exclusao", "cancelar-exclusao"]) {
  document.querySelector(`#${id}`).addEventListener("click", () => {
    if (!exclusaoEnviando) modalExclusao.close();
  });
}
modalExclusao.addEventListener("cancel", evento => {
  if (exclusaoEnviando) evento.preventDefault();
});

formExclusao.addEventListener("submit", async evento => {
  evento.preventDefault();
  if (exclusaoEnviando || !livroExclusao) return;
  bloquearExclusao(true);
  erroExclusao.textContent = "";
  try {
    await requisitar(`/livros/${livroExclusao.id}`, { method: "DELETE" });
    livros = livros.filter(livro => livro.id !== livroExclusao.id);
    renderizar();
    modalExclusao.close();
    const notificacao = document.querySelector("#notificacao");
    notificacao.textContent = `“${livroExclusao.titulo}” foi excluído. Autores e gêneros foram preservados.`;
    notificacao.hidden = false;
  } catch (erro) {
    erroExclusao.textContent = erro instanceof TypeError
      ? "Não foi possível confirmar a exclusão por falha de conexão. Atualize a biblioteca antes de tentar novamente."
      : erro.message;
  } finally {
    bloquearExclusao(false);
  }
});

// Biblioteca e autores compartilham a mesma área central, sem trocar de página.
const areaBiblioteca = document.querySelector("#area-biblioteca");
const areaAutores = document.querySelector("#area-autores");
const navBiblioteca = document.querySelector("#nav-biblioteca");
const navAutores = document.querySelector("#nav-autores");
const nomeAutor = document.querySelector("#nome-autor");
const listaAutores = document.querySelector("#lista-autores");
const mensagemAutores = document.querySelector("#mensagem-autores");
let versaoBuscaAutores = 0;

async function carregarAutores() {
  const versao = ++versaoBuscaAutores;
  const termo = nomeAutor.value.trim();
  const caminho = termo ? `/autores?${new URLSearchParams({ nome: termo })}` : "/autores";
  listaAutores.replaceChildren();
  listaAutores.setAttribute("aria-busy", "true");
  document.querySelector("#tabela-autores").hidden = true;
  document.querySelector("#quantidade-autores").textContent = "—";
  mensagemAutores.hidden = false;
  mensagemAutores.classList.remove("error");
  mensagemAutores.textContent = "Consultando autores…";
  for (const id of ["buscar-autores", "atualizar-autores", "limpar-busca-autores"]) {
    document.querySelector(`#${id}`).disabled = true;
  }
  try {
    const autores = await requisitar(caminho);
    if (versao !== versaoBuscaAutores) return;
    for (const autor of autores) {
      const linha = document.createElement("tr");
      const id = document.createElement("td");
      id.textContent = String(autor.id);
      const nome = document.createElement("td");
      nome.textContent = autor.nome;
      const acoes = document.createElement("td");
      const editar = document.createElement("button");
      editar.type = "button";
      editar.className = "edit-button";
      editar.textContent = "Editar ↗";
      editar.setAttribute("aria-label", `Editar autor ${autor.nome}`);
      editar.addEventListener("click", () => abrirModalAutor(autor));
      const excluir = document.createElement("button");
      excluir.type = "button";
      excluir.className = "delete-button";
      excluir.textContent = "Excluir";
      excluir.setAttribute("aria-label", `Excluir autor ${autor.nome}`);
      excluir.addEventListener("click", () => abrirExclusaoAutor(autor));
      acoes.append(editar, excluir);
      linha.append(id, nome, acoes);
      listaAutores.append(linha);
    }
    document.querySelector("#quantidade-autores").textContent = String(autores.length);
    document.querySelector("#tabela-autores").hidden = !autores.length;
    mensagemAutores.textContent = autores.length
      ? `${autores.length} ${autores.length === 1 ? "autor encontrado" : "autores encontrados"}.`
      : termo ? "Nenhum autor encontrado para essa busca." : "Nenhum autor cadastrado.";
  } catch (erro) {
    if (versao !== versaoBuscaAutores) return;
    mensagemAutores.classList.add("error");
    mensagemAutores.textContent = erro instanceof TypeError
      ? "Não foi possível acessar a API. Confira a conexão e clique em Atualizar."
      : erro.message;
  } finally {
    if (versao === versaoBuscaAutores) {
      listaAutores.setAttribute("aria-busy", "false");
      for (const id of ["buscar-autores", "atualizar-autores", "limpar-busca-autores"]) {
        document.querySelector(`#${id}`).disabled = false;
      }
    }
  }
}

async function selecionarArea(autores) {
  areaBiblioteca.hidden = autores;
  areaAutores.hidden = !autores;
  const ativa = autores ? navAutores : navBiblioteca;
  const inativa = autores ? navBiblioteca : navAutores;
  ativa.classList.add("nav-active");
  inativa.classList.remove("nav-active");
  ativa.setAttribute("aria-current", "page");
  inativa.setAttribute("aria-current", "false");
  document.querySelector("#secao-atual").textContent = autores ? "Autores" : "Biblioteca";
  document.title = `${autores ? "Autores" : "Minha biblioteca"} · Book Vault`;
  if (autores) {
    document.querySelector("#titulo-autores").focus();
    await carregarAutores();
  } else {
    await carregarBiblioteca();
  }
}

navAutores.addEventListener("click", () => selecionarArea(true));
navBiblioteca.addEventListener("click", () => selecionarArea(false));
document.querySelector("#busca-autores").addEventListener("submit", async evento => {
  evento.preventDefault();
  await carregarAutores();
});
document.querySelector("#atualizar-autores").addEventListener("click", carregarAutores);
document.querySelector("#limpar-busca-autores").addEventListener("click", async () => {
  nomeAutor.value = "";
  await carregarAutores();
});

const modalAutor = document.querySelector("#modal-autor");
const formAutor = document.querySelector("#form-autor");
const campoNomeAutor = document.querySelector("#autor-nome");
const erroAutor = document.querySelector("#erro-autor");
const salvarAutor = document.querySelector("#salvar-autor");
let autorEmEdicao = null;
let autorEnviando = false;

function abrirModalAutor(autor = null) {
  autorEmEdicao = autor;
  campoNomeAutor.value = autor ? autor.nome : "";
  erroAutor.textContent = "";
  document.querySelector("#titulo-modal-autor").textContent = autor ? "Editar autor." : "Cadastrar autor.";
  document.querySelector("#aviso-editar-autor").hidden = !autor;
  salvarAutor.textContent = autor ? "Salvar alterações" : "Cadastrar autor";
  modalAutor.showModal();
  campoNomeAutor.focus();
}

function bloquearAutor(bloquear) {
  autorEnviando = bloquear;
  campoNomeAutor.disabled = bloquear;
  for (const id of ["fechar-autor", "cancelar-autor", "salvar-autor"]) {
    document.querySelector(`#${id}`).disabled = bloquear;
  }
  salvarAutor.textContent = bloquear ? "Salvando…" : autorEmEdicao ? "Salvar alterações" : "Cadastrar autor";
}

document.querySelector("#novo-autor").addEventListener("click", () => abrirModalAutor());
for (const id of ["fechar-autor", "cancelar-autor"]) {
  document.querySelector(`#${id}`).addEventListener("click", () => {
    if (!autorEnviando) modalAutor.close();
  });
}
modalAutor.addEventListener("cancel", evento => {
  if (autorEnviando) evento.preventDefault();
});
campoNomeAutor.addEventListener("input", () => { erroAutor.textContent = ""; });

formAutor.addEventListener("submit", async evento => {
  evento.preventDefault();
  if (autorEnviando || !formAutor.reportValidity()) return;
  const nome = campoNomeAutor.value.trim();
  if (!nome) {
    erroAutor.textContent = "O nome do autor não pode estar vazio.";
    return;
  }
  if (autorEmEdicao && nome === autorEmEdicao.nome) {
    erroAutor.textContent = "Nenhuma alteração informada.";
    return;
  }
  bloquearAutor(true);
  erroAutor.textContent = "";
  try {
    const autor = await requisitar(autorEmEdicao ? `/autores/${autorEmEdicao.id}` : "/autores", {
      method: autorEmEdicao ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome }),
    });
    // Mantém também o nome atualizado nos livros já carregados pelo frontend.
    if (autorEmEdicao) {
      if (autorFiltro?.id === autor.id) {
        autorFiltro = autor;
        document.querySelector("#livros-autor-nome").value = autor.nome;
        atualizarRotuloFiltroAutor();
      }
      livros = livros.map(livro => ({
        ...livro,
        autores: livro.autores.map(item => item.id === autor.id ? autor : item),
      }));
      renderizar();
    }
    const notificacao = document.querySelector("#notificacao-autores");
    notificacao.textContent = autorEmEdicao
      ? `Autor “${autor.nome}” atualizado. A correção vale para todos os livros vinculados.`
      : `Autor “${autor.nome}” cadastrado com ID ${autor.id}.`;
    notificacao.hidden = false;
    modalAutor.close();
    nomeAutor.value = ""; // Exibe todos para que o registro salvo não fique oculto pela busca anterior.
    await carregarAutores();
  } catch (erro) {
    const existente = erro.detalhe?.autor;
    erroAutor.textContent = erro instanceof TypeError
      ? "Sem conexão com a API. O nome foi mantido; tente novamente."
      : existente ? `${erro.message} Autor existente: [${existente.id}] ${existente.nome}.` : erro.message;
  } finally {
    bloquearAutor(false);
  }
});

const modalExcluirAutor = document.querySelector("#modal-excluir-autor");
const formExcluirAutor = document.querySelector("#form-excluir-autor");
const erroExcluirAutor = document.querySelector("#erro-excluir-autor");
let autorParaExcluir = null;
let exclusaoAutorEnviando = false;

function abrirExclusaoAutor(autor) {
  autorParaExcluir = autor;
  document.querySelector("#autor-exclusao").textContent = `[${autor.id}] ${autor.nome}`;
  erroExcluirAutor.textContent = "";
  modalExcluirAutor.showModal();
  document.querySelector("#cancelar-excluir-autor").focus();
}

function bloquearExclusaoAutor(bloquear) {
  exclusaoAutorEnviando = bloquear;
  for (const id of ["fechar-excluir-autor", "cancelar-excluir-autor", "confirmar-excluir-autor"]) {
    document.querySelector(`#${id}`).disabled = bloquear;
  }
  document.querySelector("#confirmar-excluir-autor").textContent = bloquear ? "Excluindo…" : "Excluir autor";
}

for (const id of ["fechar-excluir-autor", "cancelar-excluir-autor"]) {
  document.querySelector(`#${id}`).addEventListener("click", () => {
    if (!exclusaoAutorEnviando) modalExcluirAutor.close();
  });
}
modalExcluirAutor.addEventListener("cancel", evento => {
  if (exclusaoAutorEnviando) evento.preventDefault();
});

formExcluirAutor.addEventListener("submit", async evento => {
  evento.preventDefault();
  if (exclusaoAutorEnviando || !autorParaExcluir) return;
  bloquearExclusaoAutor(true);
  erroExcluirAutor.textContent = "";
  try {
    await requisitar(`/autores/${autorParaExcluir.id}`, { method: "DELETE" });
    modalExcluirAutor.close();
    const notificacao = document.querySelector("#notificacao-autores");
    notificacao.textContent = `Autor “${autorParaExcluir.nome}” excluído. Nenhum livro foi alterado.`;
    notificacao.hidden = false;
    await carregarAutores(); // Reconsulta mantendo a busca atual e atualiza a quantidade.
  } catch (erro) {
    erroExcluirAutor.textContent = erro instanceof TypeError
      ? "Não foi possível confirmar a exclusão. Confira a conexão e atualize a lista antes de tentar novamente."
      : erro.message;
  } finally {
    bloquearExclusaoAutor(false);
  }
});

const campoAutorLivros = document.querySelector("#livros-autor-nome");
const sugestoesAutores = document.querySelector("#sugestoes-autores");
const mensagemBuscaLivros = document.querySelector("#mensagem-busca-livros");
let versaoSugestoes = 0;
let temporizadorSugestoes = null;

function invalidarSugestoes() {
  clearTimeout(temporizadorSugestoes);
  versaoSugestoes++;
  sugestoesAutores.replaceChildren();
  sugestoesAutores.hidden = true;
}

function atualizarRotuloFiltroAutor() {
  const rotulo = document.querySelector("#autor-filtro-atual");
  rotulo.hidden = !autorFiltro;
  rotulo.textContent = autorFiltro ? `Livros de: ${autorFiltro.nome} · ID ${autorFiltro.id}` : "";
}

function resetarFiltroAutor() {
  autorFiltro = null;
  campoAutorLivros.value = "";
  invalidarSugestoes();
  mensagemBuscaLivros.textContent = "";
  atualizarRotuloFiltroAutor();
}

async function limparBuscaLivros() {
  resetarFiltroAutor();
  await carregarBiblioteca();
}

async function buscarSugestoesAutores() {
  clearTimeout(temporizadorSugestoes);
  const termo = campoAutorLivros.value.trim();
  if (!termo) {
    await limparBuscaLivros();
    return;
  }
  invalidarSugestoes();
  const versao = versaoSugestoes;
  mensagemBuscaLivros.textContent = "Buscando autores…";
  try {
    const autores = await requisitar(`/autores?${new URLSearchParams({ nome: termo })}`);
    if (versao !== versaoSugestoes) return;
    for (const autor of autores) {
      const item = document.createElement("li");
      const botao = document.createElement("button");
      botao.type = "button";
      botao.textContent = `${autor.nome} · ID ${autor.id}`;
      botao.addEventListener("click", async () => {
        autorFiltro = autor;
        campoAutorLivros.value = autor.nome;
        invalidarSugestoes();
        mensagemBuscaLivros.textContent = "";
        atualizarRotuloFiltroAutor();
        await carregarBiblioteca();
      });
      item.append(botao);
      sugestoesAutores.append(item);
    }
    sugestoesAutores.hidden = !autores.length;
    mensagemBuscaLivros.textContent = autores.length
      ? "Selecione um autor abaixo para consultar seus livros."
      : "Nenhum autor encontrado para essa busca.";
  } catch (erro) {
    if (versao !== versaoSugestoes) return;
    mensagemBuscaLivros.textContent = erro instanceof TypeError
      ? "Não foi possível buscar autores. Confira a conexão e tente novamente."
      : erro.message;
  }
}

document.querySelector("#busca-livros-autor").addEventListener("submit", async evento => {
  evento.preventDefault();
  await buscarSugestoesAutores();
});
campoAutorLivros.addEventListener("input", () => {
  invalidarSugestoes(); // Uma resposta anterior não deve substituir o que está sendo digitado.
  mensagemBuscaLivros.textContent = "";
  temporizadorSugestoes = setTimeout(buscarSugestoesAutores, 300);
});
document.querySelector("#limpar-autor-livros").addEventListener("click", limparBuscaLivros);

const campoTituloLivros = document.querySelector("#livros-titulo");
const sugestoesTitulos = document.querySelector("#sugestoes-titulos");
const mensagemBuscaTitulo = document.querySelector("#mensagem-busca-titulo");
let temporizadorTitulo = null;

function atualizarRotuloTitulo(livro = null) {
  const rotulo = document.querySelector("#titulo-filtro-atual");
  rotulo.hidden = !livro;
  rotulo.textContent = livro ? `Livro selecionado: ${livro.titulo} · ID ${livro.id}` : "";
}

function resetarFiltroTitulo() {
  clearTimeout(temporizadorTitulo);
  livroFiltroId = null;
  campoTituloLivros.value = "";
  sugestoesTitulos.replaceChildren();
  sugestoesTitulos.hidden = true;
  mensagemBuscaTitulo.textContent = "";
  atualizarRotuloTitulo();
}

function atualizarSugestoesTitulos(exibidos) {
  sugestoesTitulos.replaceChildren();
  sugestoesTitulos.hidden = true;
  if (!campoTituloLivros.value.trim() || livroFiltroId) {
    mensagemBuscaTitulo.textContent = "";
    return;
  }
  for (const livro of exibidos) {
    const item = document.createElement("li");
    const botao = document.createElement("button");
    botao.type = "button";
    botao.textContent = `${livro.titulo} · ${livro.autores.map(autor => autor.nome).join(", ")} · ID ${livro.id}`;
    botao.addEventListener("click", () => {
      clearTimeout(temporizadorTitulo);
      livroFiltroId = livro.id;
      campoTituloLivros.value = livro.titulo;
      atualizarRotuloTitulo(livro);
      renderizar();
    });
    item.append(botao);
    sugestoesTitulos.append(item);
  }
  sugestoesTitulos.hidden = !exibidos.length;
  mensagemBuscaTitulo.textContent = exibidos.length
    ? "Os volumes encontrados já aparecem abaixo. Selecione uma sugestão para ver só aquele livro."
    : "Nenhum volume encontrado com os filtros atuais.";
}

async function buscarTitulos() {
  clearTimeout(temporizadorTitulo);
  await carregarBiblioteca();
}

document.querySelector("#busca-livros-titulo").addEventListener("submit", async evento => {
  evento.preventDefault();
  livroFiltroId = null;
  atualizarRotuloTitulo();
  await buscarTitulos();
});
campoTituloLivros.addEventListener("input", () => {
  clearTimeout(temporizadorTitulo);
  versaoBiblioteca++; // Invalida requisições feitas para um texto anterior.
  livroFiltroId = null;
  atualizarRotuloTitulo();
  sugestoesTitulos.hidden = true;
  mensagemBuscaTitulo.textContent = "Buscando títulos…";
  temporizadorTitulo = setTimeout(buscarTitulos, 300);
});
document.querySelector("#limpar-titulo-livros").addEventListener("click", async () => {
  resetarFiltroTitulo();
  await carregarBiblioteca();
});

carregarBiblioteca();
