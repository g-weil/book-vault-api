// Testa os eventos do JavaScript com DOM simplificado e HTTP real para a API de teste.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class Elemento {
  constructor() {
    this.value = "";
    this.children = [];
    this.eventos = {};
    this.elementos = new Map();
    this.dataset = {};
    this.hidden = false;
    this.disabled = false;
    this.checked = false;
    this.classList = { add() {}, remove() {} };
    this.content = { cloneNode: () => new Elemento() };
  }
  querySelector(seletor) {
    if (!this.elementos.has(seletor)) this.elementos.set(seletor, new Elemento());
    return this.elementos.get(seletor);
  }
  addEventListener(evento, funcao) { this.eventos[evento] = funcao; }
  async emitir(evento) {
    if (evento === "click" && this.disabled) return;
    await this.eventos[evento]?.({ preventDefault() {} });
  }
  append(...itens) { this.children.push(...itens); }
  replaceChildren(...itens) { this.children = itens; }
  setAttribute() {}
  focus() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  reportValidity() { return true; }
}

const documento = new Elemento();
documento.createElement = () => new Elemento();
const elemento = seletor => documento.querySelector(seletor);
elemento("#form-cadastro").reset = () => {
  for (const id of ["titulo", "autores", "status", "capa"]) elemento(`#cadastro-${id}`).value = "";
};
elemento("#form-cadastro").querySelectorAll = () => elemento("#cadastro-generos").children
  .map(label => label.children[0]).filter(campo => campo.checked);

const pedidos = [];
const contexto = vm.createContext({
  document: documento,
  console,
  URLSearchParams,
  setTimeout,
  clearTimeout,
  fetch: async (caminho, opcoes = {}) => {
    pedidos.push({ caminho, metodo: opcoes.method || "GET" });
    return fetch(new URL(caminho, process.argv[2]), opcoes);
  },
});
const javascript = fs.readFileSync("frontend/app.js", "utf8");
const html = fs.readFileSync("frontend/index.html", "utf8");
for (const [, id] of javascript.matchAll(/querySelector\("#([^"$]+)"\)/g)) {
  assert.ok(html.includes(`id="${id}"`), `Elemento ausente no HTML: ${id}`);
}
assert.ok(html.includes('class="edit-button"'));
vm.runInContext(javascript, contexto);
const esperar = () => new Promise(resolve => setTimeout(resolve, 20));
async function aguardar(condicao) {
  for (let i = 0; i < 200; i++) {
    if (condicao()) return;
    await esperar();
  }
  throw new Error("Ação do frontend não terminou.");
}
async function abrir() {
  await elemento("#novo-livro").emitir("click");
  await aguardar(() => elemento("#cadastro-generos").children.length === 18);
}
function preencher(status = "Quero ler") {
  elemento("#cadastro-titulo").value = "Livro do formulário";
  elemento("#cadastro-status").value = status;
  elemento("#cadastro-generos").children[0].children[0].checked = true;
}
async function executar() {
  await aguardar(() => !elemento("#atualizar").disabled);
  await abrir();
  assert.equal(elemento("#modal-cadastro").open, true);
  await elemento("#cancelar-cadastro").emitir("click");
  assert.equal(pedidos.filter(p => p.metodo === "POST").length, 0);

  await abrir();
  preencher();
  elemento("#cadastro-generos").children[0].children[0].checked = false;
  await elemento("#form-cadastro").emitir("submit");
  assert.match(elemento("#erro-cadastro").textContent, /pelo menos um gênero/);
  assert.equal(pedidos.filter(p => p.metodo === "POST").length, 0);
  preencher();
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#modal-cadastro").open, false);
  let livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros.length, 1);
  assert.equal(livros.livros[0].autores[0].nome, "Autor desconhecido");
  assert.equal(elemento("#estante").children.length, 1);

  await abrir();
  preencher("Quero ler");
  await elemento("#form-cadastro").emitir("submit");
  assert.match(elemento("#pergunta-duplicado").textContent, /já possui esse mesmo status/);
  assert.equal(elemento("#alterar-duplicado").hidden, true);
  assert.equal(elemento("#ajuda-duplicado").hidden, true);
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, 0);
  await elemento("#nao-alterar-duplicado").emitir("click");

  await abrir();
  preencher("Lido");
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#cadastro-duplicado").hidden, false);
  assert.equal(elemento("#alterar-duplicado").hidden, false);
  assert.equal(elemento("#ajuda-duplicado").hidden, false);
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, 0);
  await elemento("#alterar-duplicado").emitir("click");
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros.length, 1);
  assert.equal(livros.livros[0].status, "Lido");
  assert.equal(elemento("#estante").children.length, 1);

  await abrir();
  preencher();
  elemento("#cadastro-titulo").value = "Gênero inválido";
  elemento("#cadastro-generos").children[0].children[0].value = "999";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#modal-cadastro").open, true);
  assert.equal(elemento("#cadastro-titulo").value, "Gênero inválido");
  assert.match(elemento("#erro-cadastro").textContent, /gêneros existentes/);
  assert.equal(elemento("#salvar-cadastro").disabled, false);
  await elemento("#cancelar-cadastro").emitir("click");

  // Edita a partir do botão do card, mantendo o status e os autores em branco.
  const abrirEdicao = async () => {
    await elemento("#estante").children[0].querySelector(".edit-button").emitir("click");
    await aguardar(() => elemento("#cadastro-generos").children.length === 18);
  };
  await abrirEdicao();
  assert.equal(elemento("#cadastro-titulo").value, "Livro do formulário");
  assert.equal(elemento("#cadastro-autores").value, "Autor desconhecido");
  assert.equal(elemento("#cadastro-generos").children[0].children[0].checked, true);
  assert.equal(elemento("#cadastro-status").disabled, true);
  const patchesAntes = pedidos.filter(p => p.metodo === "PATCH").length;
  await elemento("#form-cadastro").emitir("submit");
  assert.match(elemento("#erro-cadastro").textContent, /Nenhuma alteração/);
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, patchesAntes);
  elemento("#cadastro-titulo").value = "Título corrigido";
  elemento("#cadastro-autores").value = "   ";
  elemento("#cadastro-generos").children[0].children[0].checked = false;
  await elemento("#form-cadastro").emitir("submit");
  assert.match(elemento("#erro-cadastro").textContent, /pelo menos um gênero/);
  elemento("#cadastro-generos").children[1].children[0].checked = true;
  elemento("#cadastro-capa").value = "https://example.com/capa.jpg";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#modal-cadastro").open, false);
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros[0].titulo, "Título corrigido");
  assert.equal(livros.livros[0].status, "Lido");
  assert.equal(livros.livros[0].autores[0].nome, "Autor desconhecido");
  assert.equal(livros.livros[0].generos[0].id, 2);
  assert.equal(livros.livros[0].capa_url, "https://example.com/capa.jpg");
  assert.equal(elemento("#estante").children.length, 1);

  await abrirEdicao();
  elemento("#cadastro-capa").value = "";
  elemento("#cadastro-autores").value = "Autor novo; Outro autor";
  await elemento("#form-cadastro").emitir("submit");
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros[0].capa_url, null);
  assert.equal(livros.livros[0].autores.length, 2);

  await fetch(new URL("/livros", process.argv[2]), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titulo: "Outro cadastro", autores: ["Autor novo", "Outro autor"], genero_ids: [1], status: "Lendo" }),
  });
  await abrirEdicao();
  elemento("#cadastro-titulo").value = "Outro cadastro";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#modal-cadastro").open, true);
  assert.match(elemento("#erro-cadastro").textContent, /já cadastrado/);
  assert.equal(elemento("#cadastro-duplicado").hidden, true);
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros[0].titulo, "Título corrigido");
  await elemento("#cancelar-cadastro").emitir("click");
  await abrir();
  assert.equal(elemento("#cadastro-status").disabled, false);
  assert.equal(elemento("#grupo-cadastro-status").hidden, false);
  await elemento("#cancelar-cadastro").emitir("click");

  // A ação de status usa sua rota específica e respeita o filtro ativo.
  elemento("#filtro-status").value = "Lido";
  await elemento("#filtro-status").emitir("change");
  const abrirStatus = () => elemento("#estante").children[0].querySelector(".status-button").emitir("click");
  await abrirStatus();
  assert.equal(elemento("#novo-status").value, "Lido");
  assert.equal(elemento("#modal-status").open, true);
  const totalPatches = pedidos.filter(p => p.metodo === "PATCH").length;
  await elemento("#form-status").emitir("submit");
  assert.match(elemento("#erro-status").textContent, /já possui esse status/);
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, totalPatches);
  elemento("#novo-status").value = "Relendo";
  await elemento("#cancelar-status").emitir("click");
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, totalPatches);
  await abrirStatus();
  assert.equal(elemento("#novo-status").value, "Lido");
  elemento("#novo-status").value = "Relendo";
  await elemento("#form-status").emitir("submit");
  assert.equal(elemento("#modal-status").open, false);
  assert.equal(elemento("#filtro-status").value, "Lido");
  assert.equal(elemento("#estante").children.length, 0);
  assert.match(elemento("#notificacao").textContent, /Relendo/);
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros[0].status, "Relendo");
  assert.equal(livros.livros[0].titulo, "Título corrigido");
  assert.equal(livros.livros[0].autores.length, 2);
  assert.equal(livros.livros[0].generos[0].id, 2);
  assert.equal(livros.livros[0].capa_url, null);
  elemento("#filtro-status").value = "";
  await elemento("#filtro-status").emitir("change");
  await abrirStatus();
  elemento("#novo-status").value = "Inválido";
  await elemento("#form-status").emitir("submit");
  assert.equal(elemento("#modal-status").open, true);
  assert.equal(elemento("#novo-status").value, "Inválido");
  assert.equal(elemento("#salvar-status").disabled, false);
  assert.match(elemento("#erro-status").textContent, /opção não existe/);
  await elemento("#cancelar-status").emitir("click");

  const abrirExclusao = () => elemento("#estante").children[0].querySelector(".delete-button").emitir("click");
  await abrirExclusao();
  assert.match(elemento("#livro-exclusao").textContent, /Título corrigido/);
  const deletesAntes = pedidos.filter(p => p.metodo === "DELETE").length;
  await elemento("#cancelar-exclusao").emitir("click");
  assert.equal(pedidos.filter(p => p.metodo === "DELETE").length, deletesAntes);
  assert.equal(elemento("#estante").children.length, 1);
  await abrirExclusao();
  await Promise.all([
    elemento("#form-exclusao").emitir("submit"),
    elemento("#form-exclusao").emitir("submit"),
  ]);
  assert.equal(pedidos.filter(p => p.metodo === "DELETE").length, deletesAntes + 1);
  assert.equal(elemento("#modal-exclusao").open, false);
  assert.equal(elemento("#estante").children.length, 0);
  assert.equal(elemento("#quantidade").textContent, "0");
  assert.match(elemento("#notificacao").textContent, /foi excluído/);
  assert.match(elemento("#mensagem").textContent, /biblioteca está vazia/);
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros.length, 1);
  assert.equal(livros.livros[0].titulo, "Outro cadastro");
  const autores = await (await fetch(new URL("/autores", process.argv[2]))).json();
  assert.equal(autores.length, 3);
  const generos = await (await fetch(new URL("/generos", process.argv[2]))).json();
  assert.equal(generos.length, 18);

  // Simula um livro removido por outro cliente após a última consulta.
  await elemento("#atualizar").emitir("click");
  assert.equal(elemento("#estante").children.length, 1);
  await abrirExclusao();
  await fetch(new URL(`/livros/${livros.livros[0].id}`, process.argv[2]), { method: "DELETE" });
  await elemento("#form-exclusao").emitir("submit");
  assert.equal(elemento("#modal-exclusao").open, true);
  assert.match(elemento("#erro-exclusao").textContent, /não encontrado/);
  assert.equal(elemento("#confirmar-exclusao").disabled, false);
  await elemento("#cancelar-exclusao").emitir("click");
  await elemento("#atualizar").emitir("click");
  assert.equal(elemento("#estante").children.length, 0);
  const escritasAntesAutores = pedidos.filter(p => p.metodo !== "GET").length;
  await elemento("#nav-autores").emitir("click");
  assert.equal(elemento("#area-biblioteca").hidden, true);
  assert.equal(elemento("#area-autores").hidden, false);
  assert.equal(elemento("#secao-atual").textContent, "Autores");
  assert.equal(elemento("#lista-autores").children.length, 3);
  assert.equal(elemento("#quantidade-autores").textContent, "3");
  assert.equal(elemento("#tabela-autores").hidden, false);
  assert.equal(elemento("#lista-autores").children[0].children[1].textContent, "Autor desconhecido");

  elemento("#nome-autor").value = "  NOVO  ";
  await elemento("#busca-autores").emitir("submit");
  assert.equal(elemento("#lista-autores").children.length, 1);
  assert.equal(elemento("#lista-autores").children[0].children[1].textContent, "Autor novo");
  assert.ok(pedidos.at(-1).caminho.includes("nome=NOVO"));
  elemento("#nome-autor").value = "naoexiste";
  await elemento("#busca-autores").emitir("submit");
  assert.equal(elemento("#lista-autores").children.length, 0);
  assert.equal(elemento("#tabela-autores").hidden, true);
  assert.match(elemento("#mensagem-autores").textContent, /Nenhum autor encontrado/);
  await elemento("#limpar-busca-autores").emitir("click");
  assert.equal(elemento("#nome-autor").value, "");
  assert.equal(elemento("#lista-autores").children.length, 3);
  assert.equal(pedidos.filter(p => p.metodo !== "GET").length, escritasAntesAutores);

  await fetch(new URL("/autores", process.argv[2]), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome: "José & Silva" }),
  });
  await elemento("#atualizar-autores").emitir("click");
  assert.equal(elemento("#lista-autores").children.length, 4);
  elemento("#nome-autor").value = "JOSÉ &";
  await elemento("#busca-autores").emitir("submit");
  assert.equal(elemento("#lista-autores").children.length, 1);
  assert.equal(elemento("#lista-autores").children[0].children[1].textContent, "José & Silva");
  await elemento("#nav-biblioteca").emitir("click");
  assert.equal(elemento("#area-biblioteca").hidden, false);
  assert.equal(elemento("#area-autores").hidden, true);
  assert.equal(elemento("#secao-atual").textContent, "Biblioteca");
  await elemento("#nav-autores").emitir("click");
  const totalPostsAutor = pedidos.filter(p => p.metodo === "POST" && p.caminho === "/autores").length;
  await elemento("#novo-autor").emitir("click");
  await elemento("#cancelar-autor").emitir("click");
  assert.equal(pedidos.filter(p => p.metodo === "POST" && p.caminho === "/autores").length, totalPostsAutor);
  await elemento("#novo-autor").emitir("click");
  elemento("#autor-nome").value = "   ";
  await elemento("#form-autor").emitir("submit");
  assert.match(elemento("#erro-autor").textContent, /não pode estar vazio/);
  elemento("#autor-nome").value = "Autor da tela";
  await Promise.all([elemento("#form-autor").emitir("submit"), elemento("#form-autor").emitir("submit")]);
  assert.equal(pedidos.filter(p => p.metodo === "POST" && p.caminho === "/autores").length, totalPostsAutor + 1);
  assert.equal(elemento("#modal-autor").open, false);
  assert.equal(elemento("#nome-autor").value, "");
  assert.equal(elemento("#lista-autores").children.length, 5);
  assert.match(elemento("#notificacao-autores").textContent, /cadastrado com ID/);

  await elemento("#novo-autor").emitir("click");
  elemento("#autor-nome").value = " AUTOR DA TELA ";
  await elemento("#form-autor").emitir("submit");
  assert.equal(elemento("#modal-autor").open, true);
  assert.match(elemento("#erro-autor").textContent, /Autor existente/);
  assert.equal(elemento("#autor-nome").value, " AUTOR DA TELA ");
  await elemento("#cancelar-autor").emitir("click");
  let linhaAutor = elemento("#lista-autores").children.find(linha => linha.children[1].textContent === "Autor da tela");
  const idAutorTela = linhaAutor.children[0].textContent;
  await linhaAutor.children[2].children[0].emitir("click");
  assert.equal(elemento("#autor-nome").value, "Autor da tela");
  assert.equal(elemento("#aviso-editar-autor").hidden, false);
  const patchesAntesAutor = pedidos.filter(p => p.metodo === "PATCH").length;
  await elemento("#form-autor").emitir("submit");
  assert.match(elemento("#erro-autor").textContent, /Nenhuma alteração/);
  assert.equal(pedidos.filter(p => p.metodo === "PATCH").length, patchesAntesAutor);
  elemento("#autor-nome").value = "José & Silva";
  await elemento("#form-autor").emitir("submit");
  assert.match(elemento("#erro-autor").textContent, /outro autor/);
  await elemento("#cancelar-autor").emitir("click");

  for (const titulo of ["Livro vinculado 1", "Livro vinculado 2"]) {
    await fetch(new URL("/livros", process.argv[2]), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ titulo, autores: ["Autor da tela"], genero_ids: [1], status: "Lendo" }),
    });
  }
  await elemento("#nav-biblioteca").emitir("click");
  await elemento("#nav-autores").emitir("click");
  linhaAutor = elemento("#lista-autores").children.find(linha => linha.children[0].textContent === idAutorTela);
  await linhaAutor.children[2].children[0].emitir("click");
  elemento("#autor-nome").value = "Autor corrigido";
  await elemento("#form-autor").emitir("submit");
  assert.equal(elemento("#modal-autor").open, false);
  const linhaCorrigida = elemento("#lista-autores").children.find(linha => linha.children[0].textContent === idAutorTela);
  assert.equal(linhaCorrigida.children[1].textContent, "Autor corrigido");
  assert.equal(vm.runInContext("livros[0].autores[0].nome", contexto), "Autor corrigido");
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros.length, 2);
  assert.ok(livros.livros.every(livro => livro.autores[0].nome === "Autor corrigido"));
  assert.equal(elemento("#lista-autores").children.length, 5);
  // Autor vinculado: a API recusa, e o frontend mantém a confirmação e os registros.
  await linhaCorrigida.children[2].children[1].emitir("click");
  assert.match(elemento("#autor-exclusao").textContent, /Autor corrigido/);
  await elemento("#form-excluir-autor").emitir("submit");
  assert.equal(elemento("#modal-excluir-autor").open, true);
  assert.match(elemento("#erro-excluir-autor").textContent, /livros vinculados/);
  assert.equal(elemento("#confirmar-excluir-autor").disabled, false);
  assert.equal(elemento("#lista-autores").children.length, 5);
  await elemento("#cancelar-excluir-autor").emitir("click");

  elemento("#nome-autor").value = "JOSÉ &";
  await elemento("#busca-autores").emitir("submit");
  const linhaSemLivros = elemento("#lista-autores").children[0];
  await linhaSemLivros.children[2].children[1].emitir("click");
  const deletesAntesAutor = pedidos.filter(p => p.metodo === "DELETE").length;
  await elemento("#cancelar-excluir-autor").emitir("click");
  assert.equal(pedidos.filter(p => p.metodo === "DELETE").length, deletesAntesAutor);
  await linhaSemLivros.children[2].children[1].emitir("click");
  await Promise.all([elemento("#form-excluir-autor").emitir("submit"), elemento("#form-excluir-autor").emitir("submit")]);
  assert.equal(pedidos.filter(p => p.metodo === "DELETE").length, deletesAntesAutor + 1);
  assert.equal(elemento("#modal-excluir-autor").open, false);
  assert.equal(elemento("#nome-autor").value, "JOSÉ &");
  assert.equal(elemento("#lista-autores").children.length, 0);
  assert.equal(elemento("#quantidade-autores").textContent, "0");
  assert.match(elemento("#notificacao-autores").textContent, /excluído/);
  livros = await (await fetch(new URL("/livros", process.argv[2]))).json();
  assert.equal(livros.livros.length, 2);
  assert.ok(livros.livros.every(livro => livro.autores[0].nome === "Autor corrigido"));
  await elemento("#limpar-busca-autores").emitir("click");
  assert.equal(elemento("#lista-autores").children.length, 4);

  const linhaObsoleta = elemento("#lista-autores").children[0];
  const idObsoleto = linhaObsoleta.children[0].textContent;
  await linhaObsoleta.children[2].children[1].emitir("click");
  await fetch(new URL(`/autores/${idObsoleto}`, process.argv[2]), { method: "DELETE" });
  await elemento("#form-excluir-autor").emitir("submit");
  assert.equal(elemento("#modal-excluir-autor").open, true);
  assert.match(elemento("#erro-excluir-autor").textContent, /não encontrado/);
  await elemento("#cancelar-excluir-autor").emitir("click");
  await elemento("#atualizar-autores").emitir("click");
  assert.equal(elemento("#lista-autores").children.length, 3);
  await fetch(new URL("/autores", process.argv[2]), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome: "Autor sem livros na busca" }),
  });
  const terceiro = await (await fetch(new URL("/livros", process.argv[2]), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titulo: "Outra autoria", autores: ["Autora da busca"], genero_ids: [1], status: "Lido" }),
  })).json();
  await fetch(new URL(`/livros/${livros.livros[0].id}`, process.argv[2]), {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ autores: ["Autor corrigido", "Autora da busca"] }),
  });
  await elemento("#nav-biblioteca").emitir("click");
  assert.equal(elemento("#estante").children.length, 3);
  elemento("#livros-autor-nome").value = "corrig";
  await elemento("#livros-autor-nome").emitir("input");
  await aguardar(() => elemento("#sugestoes-autores").children.length === 1);
  assert.equal(elemento("#sugestoes-autores").hidden, false);
  await elemento("#sugestoes-autores").children[0].children[0].emitir("click");
  assert.equal(elemento("#estante").children.length, 2);
  assert.ok(pedidos.at(-1).caminho.includes(`autor_id=${idAutorTela}`));
  assert.match(elemento("#autor-filtro-atual").textContent, /Autor corrigido/);
  assert.match(elemento("#estante").children[0].querySelector(".book-authors").textContent, /Autora da busca/);
  elemento("#filtro-status").value = "Lido";
  await elemento("#filtro-status").emitir("change");
  assert.equal(elemento("#estante").children.length, 0);
  assert.match(elemento("#mensagem").textContent, /desse autor com o status/);
  elemento("#filtro-status").value = "Lendo";
  await elemento("#filtro-status").emitir("change");
  assert.equal(elemento("#estante").children.length, 2);
  await elemento("#estante").children[0].querySelector(".status-button").emitir("click");
  elemento("#novo-status").value = "Lido";
  await elemento("#form-status").emitir("submit");
  assert.equal(elemento("#estante").children.length, 1);
  await elemento("#atualizar").emitir("click");
  assert.ok(pedidos.at(-1).caminho.includes(`autor_id=${idAutorTela}`));
  assert.equal(elemento("#estante").children.length, 1);
  await elemento("#limpar-autor-livros").emitir("click");
  assert.equal(elemento("#filtro-status").value, "Lendo");
  assert.equal(elemento("#estante").children.length, 1);
  assert.equal(elemento("#autor-filtro-atual").hidden, true);
  elemento("#filtro-status").value = "";
  await elemento("#filtro-status").emitir("change");
  assert.equal(elemento("#estante").children.length, 3);

  elemento("#livros-autor-nome").value = "Autora da busca";
  await elemento("#busca-livros-autor").emitir("submit");
  await elemento("#sugestoes-autores").children[0].children[0].emitir("click");
  assert.equal(elemento("#estante").children.length, 2);
  await elemento("#estante").children[0].querySelector(".edit-button").emitir("click");
  await aguardar(() => elemento("#cadastro-generos").children.length === 18);
  elemento("#cadastro-autores").value = "Autor corrigido";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#estante").children.length, 1);
  assert.equal(vm.runInContext("autorFiltro.id", contexto), terceiro.livro.autores[0].id);
  await abrir();
  preencher();
  elemento("#cadastro-titulo").value = "Novo fora do filtro";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#autor-filtro-atual").hidden, true);
  assert.equal(elemento("#estante").children.length, 4);

  elemento("#livros-autor-nome").value = "Autor sem livros na busca";
  await elemento("#busca-livros-autor").emitir("submit");
  await elemento("#sugestoes-autores").children[0].children[0].emitir("click");
  assert.equal(elemento("#estante").children.length, 0);
  assert.match(elemento("#mensagem").textContent, /Nenhum livro encontrado para esse autor/);
  elemento("#livros-autor-nome").value = "naoexisteautor";
  await elemento("#busca-livros-autor").emitir("submit");
  assert.equal(elemento("#sugestoes-autores").hidden, true);
  assert.match(elemento("#mensagem-busca-livros").textContent, /Nenhum autor encontrado/);
  await elemento("#limpar-autor-livros").emitir("click");
  assert.equal(elemento("#estante").children.length, 4);
  for (const [titulo, autor, status] of [
    ["Saga - Volume 1", "Autor corrigido", "Lido"],
    ["Saga - Volume 2", "Autor corrigido", "Lendo"],
    ["Saga - Volume 1", "Autora da busca", "Lido"],
  ]) {
    await fetch(new URL("/livros", process.argv[2]), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ titulo, autores: [autor], genero_ids: [1], status }),
    });
  }
  await elemento("#atualizar").emitir("click");
  assert.equal(elemento("#estante").children.length, 7);
  elemento("#livros-titulo").value = "  SAGA  ";
  await elemento("#livros-titulo").emitir("input");
  await aguardar(() => elemento("#sugestoes-titulos").children.length === 3 && !elemento("#sugestoes-titulos").hidden);
  assert.equal(elemento("#estante").children.length, 3);
  assert.ok(pedidos.at(-1).caminho.includes("titulo=SAGA"));
  assert.match(elemento("#sugestoes-titulos").children[0].children[0].textContent, /Autor corrigido.*ID/);
  await elemento("#sugestoes-titulos").children[0].children[0].emitir("click");
  assert.equal(elemento("#estante").children.length, 1);
  const idTitulo = vm.runInContext("livroFiltroId", contexto);
  assert.match(elemento("#titulo-filtro-atual").textContent, new RegExp(`ID ${idTitulo}`));
  await elemento("#atualizar").emitir("click");
  assert.equal(elemento("#estante").children.length, 1);
  await elemento("#estante").children[0].querySelector(".edit-button").emitir("click");
  await aguardar(() => elemento("#cadastro-generos").children.length === 18);
  elemento("#cadastro-titulo").value = "Saga - Volume 1 revisado";
  await elemento("#form-cadastro").emitir("submit");
  assert.equal(elemento("#livros-titulo").value, "Saga - Volume 1 revisado");
  assert.equal(elemento("#estante").children.length, 1);
  assert.equal(vm.runInContext("livroFiltroId", contexto), idTitulo);
  await elemento("#limpar-titulo-livros").emitir("click");
  assert.equal(elemento("#estante").children.length, 7);

  elemento("#livros-autor-nome").value = "Autor corrigido";
  await elemento("#busca-livros-autor").emitir("submit");
  await elemento("#sugestoes-autores").children[0].children[0].emitir("click");
  elemento("#livros-titulo").value = "saga";
  await elemento("#busca-livros-titulo").emitir("submit");
  assert.equal(elemento("#estante").children.length, 2);
  assert.ok(pedidos.at(-1).caminho.includes("autor_id=") && pedidos.at(-1).caminho.includes("titulo=saga"));
  elemento("#filtro-status").value = "Lido";
  await elemento("#filtro-status").emitir("change");
  assert.equal(elemento("#estante").children.length, 1);
  await elemento("#limpar-titulo-livros").emitir("click");
  assert.equal(elemento("#filtro-status").value, "Lido");
  assert.equal(vm.runInContext("autorFiltro.nome", contexto), "Autor corrigido");
  assert.equal(elemento("#estante").children.length, 2);
  elemento("#livros-titulo").value = "naoexistetitulo";
  await elemento("#busca-livros-titulo").emitir("submit");
  assert.equal(elemento("#estante").children.length, 0);
  assert.match(elemento("#mensagem").textContent, /Nenhum livro encontrado para esse título/);
  await elemento("#limpar-titulo-livros").emitir("click");
  console.log("OK: fluxos de livros/autores; título parcial ao digitar; volumes com mesmo título distinguidos por ID/autoria; seleção e edição preservadas; título+autor+status combinados; limpar um filtro preserva os outros; sem resultados tratado.");
}
executar().catch(erro => { console.error(erro); process.exitCode = 1; });
