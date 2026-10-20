---
icon: material/source-branch
---

# :material-source-branch: Migrações (Alembic)

Até agora, as tabelas do Comprix são criadas pelo `create_all`, que roda toda vez que a API liga. Isso funciona bem no começo, mas tem uma limitação importante: ele só **cria** tabelas que ainda não existem. Ele **nunca altera** uma tabela que já está no banco.

## O problema

Imagine esta situação:

1. Criamos o model `Usuarios` e rodamos a API. O `create_all` cria a tabela `usuarios` no banco.
2. Cadastramos alguns usuários reais.
3. Depois, decidimos adicionar uma coluna nova, como `primeiro_acesso`, no model.

Ao rodar a API de novo, o `create_all` vê que a tabela `usuarios` já existe e **não faz nada**. A coluna nova não é criada no banco, e a aplicação passa a dar erro sempre que tenta usá-la.

Durante o desenvolvimento, dá para contornar isso apagando o arquivo `comprix.db` e deixando a API criar tudo de novo. Mas, com dados reais, apagar o banco significa **perder todos os dados**. Precisamos de uma forma de alterar a estrutura do banco sem perder o que já está guardado.

## O que são migrações?

Uma **migração** é um arquivo que descreve uma mudança na estrutura do banco de dados, como:

- criar uma tabela nova;
- adicionar, renomear ou remover uma coluna;
- criar um índice ou uma restrição, como o `unique` do e-mail.

Cada migração é aplicada **uma única vez**, e em ordem. Juntas, elas formam um **histórico de versões do banco**, parecido com o histórico de commits do Git: olhando a lista de migrações, sabemos exatamente como o banco chegou ao formato atual.

``` title="Histórico de migrações"
001 - cria a tabela usuarios
002 - adiciona a coluna primeiro_acesso
003 - cria a tabela produtos
```

Assim, qualquer pessoa que baixar o projeto pode reconstruir o banco do zero, aplicando as migrações em sequência. E um banco que já existe, com dados, recebe só as migrações que ainda faltam.

## O que é o Alembic?

O **Alembic** é a ferramenta de migrações feita pelos mesmos criadores do SQLAlchemy. Ele trabalha diretamente com os nossos models e faz três coisas principais:

- :material-check-circle:{ style="color: #2fb985" } **Gera as migrações automaticamente:** ele compara os models com o banco e escreve o arquivo de migração com as diferenças que encontrou.

- :material-check-circle:{ style="color: #2fb985" } **Aplica as migrações:** com um comando, ele leva o banco para a versão mais recente, executando só o que ainda não foi aplicado.

- :material-check-circle:{ style="color: #2fb985" } **Desfaz as migrações:** se uma mudança deu errado, ele consegue voltar o banco para a versão anterior.

Na prática, o dia a dia com o Alembic se resume a dois comandos:

```console title="Terminal"
$ alembic revision --autogenerate -m "adiciona primeiro_acesso"
$ alembic upgrade head
```

- O primeiro **gera** uma nova migração a partir das mudanças nos models. O texto depois do `-m` é uma descrição, como a mensagem de um commit.
- O segundo **aplica** no banco todas as migrações que ainda faltam. O `head` significa "a versão mais recente".

!!! warning "Sempre revise a migração gerada"
    O `--autogenerate` é muito útil, mas não é perfeito. Ele não consegue perceber, por exemplo, que uma coluna foi **renomeada**: para ele, parece que uma coluna foi apagada e outra foi criada, o que faria os dados