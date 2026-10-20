---
icon: lucide/database
---

# :material-database: Banco de dados


Até agora, a nossa API só devolve uma mensagem fixa. Mas o Comprix precisa **guardar informações**: produtos, compras, valores, datas. E essas informações precisam continuar existindo mesmo depois que o servidor é desligado. É para isso que serve um **banco de dados**.

## O que é um banco de dados?

Um banco de dados é um sistema feito para **armazenar, organizar e consultar dados** de forma segura e eficiente. Em vez de guardar tudo em arquivos de texto soltos, o banco organiza as informações em **tabelas**, parecidas com planilhas:

| id | nome | preco | quantidade |
|---|---|---|---|
| 1 | Arroz | 12.90 | 2 |
| 2 | Feijão | 8.50 | 1 |
| 3 | Café | 18.00 | 1 |

- Cada **linha** é um registro (um produto).
- Cada **coluna** é uma informação daquele registro (nome, preço, quantidade).
- O **id** identifica cada registro de forma única.


Para conversar com o banco, usamos a linguagem **SQL**. Por exemplo, para buscar todos os produtos que custam mais de 10 reais:

```sql
SELECT nome, preco FROM produtos WHERE preco > 10;
```

!!! info "Não vamos escrever SQL o tempo todo"
    Mais adiante, vamos usar uma biblioteca chamada **SQLAlchemy**, que permite trabalhar com o banco usando classes e objetos Python. Ela traduz o nosso código para SQL automaticamente.


## Por que escolhemos o SQLite?

Existem vários bancos de dados, como **PostgreSQL**, **MySQL** e **SQL Server**. Para o Comprix, começamos com o **SQLite**, pelos seguintes motivos:

- :material-check-circle:{ style="color: #2fb985" } **Já vem com o Python:** não precisamos instalar nem configurar nenhum servidor de banco de dados.

- :material-check-circle:{ style="color: #2fb985" } **O banco inteiro é um único arquivo:** todos os dados ficam em um arquivo, como `comprix.db`. Para fazer um backup, basta copiar esse arquivo.

- :material-check-circle:{ style="color: #2fb985" } **Ideal para começar e para os testes:** como é leve e rápido de criar, podemos gerar um banco novo a cada teste, sem interferir nos dados reais.

- :material-check-circle:{ style="color: #2fb985" } **Usa SQL de verdade:** tudo o que aprendermos com ele vale para os outros bancos.

- :material-check-circle:{ style="color: #2fb985" } **Fácil de trocar no futuro:** com o SQLAlchemy, mudar para o PostgreSQL, por exemplo, exige pouca alteração no código, principalmente o endereço de conexão.

- :material-check-circle:{ style="color: #2fb985" } **Escala:** Como esse sistema e para uma família onde teremos poucos usuários, o sqlite atende perfeitamente.

## Quando o SQLite não é a melhor escolha?

É importante conhecer as limitações:

- Ele não foi feito para **muitos usuários escrevendo dados ao mesmo tempo**, como acontece em sistemas grandes na internet.
- Por ser um arquivo local, ele não é a melhor opção quando a aplicação roda em **vários servidores** que precisam compartilhar os mesmos dados.

!!! tip "Nossa estratégia"
    Vamos desenvolver e testar o Comprix com o **SQLite**. Se no futuro o sistema crescer e tiver muitos usuários, poderemos migrar para o **PostgreSQL** aproveitando quase todo o código que já escrevemos. Graças a fantástica biblioteca do **SQLAlchemy** que veremos em breve.



