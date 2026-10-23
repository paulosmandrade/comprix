---
icon: lucide/shield-lock
title: "Segurança"
---

# :lucide-shield-lock: Segurança


> Uma API que guarda dados de usuários assume uma responsabilidade:
> **proteger quem confia nela.**

No **COMPRIX**, essa proteção começa em dois pontos:

| Camada | O que protege | Tecnologia |
|---|---|---|
| 🗄️ **Senhas no banco de dados** | O que está **guardado** | Hash com **Argon2** |
| 🎟️ **Token de autorização** | O que está **em trânsito** | **JWT** + **OAuth2** |
| ✉️ **Link para definir a senha** | O **primeiro acesso** | **JWT** de uso único, enviado por e-mail |

---

## 🗄️ 1. Senhas armazenadas com hash

A senha **nunca** é salva como foi digitada. Ela passa por um algoritmo de
**hash**, no caso o **Argon2**, que a transforma em uma sequência que **não
pode ser revertida**.

```text
Senha digitada:   minhasenha123
Salvo no banco:   $argon2id$v=19$m=65536,t=3,p=4$Zk9x...$8Jk2...
```

Mesmo que aconteça alguma falha, como:

- 💥 vazamento do banco de dados
- 💾 backup exposto
- 🚪 acesso indevido

quem obtiver esses dados **não terá as senhas**, apenas hashes inúteis para
fazer login.

### 🌐 Uma proteção que vai além do sistema

Muitas pessoas repetem a mesma senha em vários serviços. Um vazamento em texto
puro colocaria em risco o **e-mail**, o **banco** e as **redes sociais**
delas.

### 🧂 Por que o Argon2?

- 🐢 **É lento de propósito**, o que torna inviáveis os ataques de força bruta.
- 🎲 **Usa um *salt* aleatório para cada senha**, o que anula as tabelas
  pré-calculadas (*rainbow tables*).
- 👥 **Duas pessoas com a mesma senha têm hashes completamente diferentes.**

> 💡 **Hash ≠ criptografia.** A criptografia pode ser revertida com a chave
> certa. O hash é de **mão única**: não existe "descriptografar" uma senha,
> e é exatamente isso que queremos.

---

## 🎟️ 2. Token de acesso (JWT + OAuth2)

Depois do login, a API **não pede a senha a cada requisição**. O usuário
recebe um **token JWT**, uma credencial **assinada digitalmente** com uma
chave secreta que **só o servidor conhece**.

```text
1. Usuário  ──(e-mail + senha)──▶  POST /auth/token
2. API      ◀──────(token JWT)───  confere a senha e assina o token
3. Usuário  ──(Bearer <token>)──▶  rotas protegidas
```

### ✍️ A assinatura impede alterações

Se alguém tentar modificar o token para:

- se passar por **outro usuário**, ou
- se dar permissões de **administrador**,

a assinatura **deixa de conferir** e o acesso é **negado**.

### ⏳ Validade curta

O token tem **prazo de validade curto**. Se for interceptado, só serve por
**alguns minutos**, o que limita bastante o estrago.

### 👮 Quem pode fazer o quê

Saber **quem** é o usuário não basta: algumas ações, como cadastrar
usuários, são exclusivas de **administradores**. Essa permissão vem da coluna
`admin` da tabela `usuarios`, conferida a cada requisição pela função
`get_current_admin`. Um usuário comum recebe **403 Forbidden**.

---

## ✉️ 3. A senha é definida pelo próprio usuário

No COMPRIX, o administrador cadastra só o **nome** e o **e-mail**. Ninguém
escolhe a senha por outra pessoa, e nenhuma senha é enviada por e-mail:

1. O usuário é criado com uma **senha aleatória** que ninguém conhece.
2. Ele recebe por e-mail um **link** com um token válido por **24 horas**.
3. Pelo link, ele mesmo define a senha. Depois disso, o link deixa de valer.

Os detalhes estão na página [Usuários](../routers/usuarios.md).

---

## 🤝 4. Camadas que se complementam

> 🗄️ **O hash protege o que está guardado.**
> 🎟️ **O token protege o que está em trânsito.**

Juntas, elas reduzem a exposição da senha ao mínimo: ela **só circula no
momento do login** e **nunca fica armazenada de forma legível** em lugar
nenhum.

---

## ✅ 5. Cuidados básicos

Nada disso funciona sem alguns cuidados:

- [x] 🔑 A **chave secreta** fica no arquivo `.env`, **fora do repositório**
  e guardada em um **cofre de senhas**.
- [x] 🔒 A comunicação deve **sempre usar HTTPS**.
- [x] 🚫 O token **nunca** deve carregar dados sensíveis: seu conteúdo pode
  ser **lido** por qualquer um, mesmo sem poder ser **alterado**.
- [x] 🧪 Os **testes automatizados** garantem que tokens **expirados**,
  **forjados** ou **malformados** sejam sempre recusados.

---

## 💬 Conclusão

> **Segurança não é um recurso que se acrescenta no fim do projeto.**
>
> É uma decisão tomada desde a primeira linha de código, e é ela que permite
> ao usuário **confiar no sistema sem precisar pensar nisso.**