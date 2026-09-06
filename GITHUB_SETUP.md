# Rodando essa integração sem computador (GitHub Actions)

Este guia monta a automação inteira na nuvem, agendada pra rodar sozinha
todo dia. Você só precisa do celular. Uma vez configurado, você nunca
mais precisa abrir esse zip de novo — os arquivos vão morar no GitHub.

## O que você vai ter no final

- Um repositório privado no GitHub com o código deste projeto
- Um "robô" (GitHub Actions) que roda `main.py --aplicar` todo dia sozinho
- Um jeito de ver o relatório de cada execução, direto do navegador do celular

---

## Passo 1 — Criar conta no GitHub (se ainda não tiver)

Acesse **github.com** pelo navegador do celular e crie uma conta grátis.

## Passo 2 — Criar o token de acesso pessoal (PAT)

Esse token é o que permite que o próprio robô atualize suas credenciais
sozinho quando o Tiny trocar o refresh_token (ele faz isso periodicamente).

1. No GitHub, toque no seu avatar (canto superior) → **Settings**
2. Role até **Developer settings** (fica no fim do menu esquerdo/lista)
3. **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
4. Dê um nome (ex: `tiny-actions`), escolha uma validade (ex: 1 ano)
5. Marque a permissão **repo** (marca a caixa principal, isso já inclui as outras daquele grupo)
6. Gere e **copie o token na hora** — ele só aparece uma vez. Cole em algum
   lugar temporário (ex: rascunho de notas) até usarmos no Passo 5.

## Passo 3 — Criar o repositório

1. Toque no **+** no canto superior → **New repository**
2. Nome: algo como `tiny-automacao`
3. Marque **Private**
4. Crie (pode adicionar um README padrão, vamos substituir os arquivos)

## Passo 4 — Colocar os arquivos do projeto no repositório

Escolha **uma** das opções abaixo, conforme seu aparelho.

### Opção A — Android, com Termux (recomendado se for Android)

1. Instale o **Termux** (Play Store ou F-Droid)
2. Coloque o `tiny_integration.zip` na pasta de Downloads do celular
3. No Termux:
   ```
   pkg install python git unzip -y
   termux-setup-storage
   cd storage/downloads
   unzip tiny_integration.zip
   cd tiny_integration
   git init
   git branch -M main
   git remote add origin https://SEU_USUARIO:SEU_TOKEN@github.com/SEU_USUARIO/tiny-automacao.git
   git add -A
   git commit -m "projeto inicial"
   git push -u origin main
   ```
   Troque `SEU_USUARIO` pelo seu usuário do GitHub e `SEU_TOKEN` pelo PAT do Passo 2.

### Opção B — iPhone, com Working Copy

1. Instale o app **Working Copy** (grátis, com opção paga p/ desbloquear tudo)
2. No app Arquivos do iPhone, descompacte o zip (tocar no arquivo já
   descompacta automaticamente)
3. No Working Copy: crie um repositório novo apontando pra
   `https://github.com/SEU_USUARIO/tiny-automacao.git` (ele vai pedir login,
   use seu usuário e o PAT do Passo 2 como senha)
4. Copie a pasta `tiny_integration` (os arquivos de dentro dela) pra dentro
   do repositório clonado no Working Copy, usando o menu de compartilhar
   do app Arquivos
5. Dentro do Working Copy: **Commit** → escreva uma mensagem → **Push**

### Opção C — Qualquer aparelho, sem instalar nada extra (GitHub Codespaces)

1. No repositório recém-criado, toque em **Code** → aba **Codespaces** →
   **Create codespace on main**
2. Isso abre um VS Code completo no navegador (funciona no celular, a tela
   fica pequena mas dá pra usar)
3. Na aba do terminal (ícone de terminal, ou menu ≡ → Terminal → New Terminal), envie o zip pro Codespace: use o próprio explorador de arquivos do
   Codespace (ícone de pasta na lateral) → botão direito/toque longo →
   **Upload...** → escolha o `tiny_integration.zip`
4. No terminal do Codespace:
   ```
   unzip tiny_integration.zip
   cp -r tiny_integration/. .
   rm -rf tiny_integration tiny_integration.zip
   git add -A
   git commit -m "projeto inicial"
   git push
   ```

---

## Passo 5 — Configurar os Secrets do repositório

No repositório: **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Crie um de cada vez:

| Nome | Valor |
|---|---|
| `TINY_CLIENT_ID` | o client_id da sua aplicação no Tiny |
| `TINY_CLIENT_SECRET` | o client_secret da sua aplicação no Tiny |
| `TINY_REDIRECT_URI` | a URL do webhook.site que você cadastrou no Tiny |
| `GH_PAT` | o mesmo token pessoal que você criou no Passo 2 |

(o `TINY_REFRESH_TOKEN` você **não** cria agora — ele é criado sozinho no
próximo passo)

## Passo 6 — Autorizar a aplicação no Tiny

1. No repositório: aba **Actions** → workflow **"Autorizar Tiny (passo único)"**
   → **Run workflow** → deixe o campo "code" em branco → **Run workflow**
2. Espere terminar (ícone fica verde) e abra o log dessa execução — ele vai
   mostrar uma URL de autorização do Tiny
3. Copie essa URL, abra no navegador do celular, faça login no Tiny e
   autorize a aplicação
4. Você será redirecionado pra sua página do webhook.site — copie o valor
   do parâmetro `code` que aparece na URL recebida lá
5. Volte em **Actions** → **"Autorizar Tiny (passo único)"** → **Run workflow**
   de novo, agora colando esse `code` no campo → **Run workflow**
6. Confira o log: deve aparecer "Autorização concluída! O TINY_REFRESH_TOKEN
   foi salvo como Secret."

## Passo 7 — Testar manualmente antes de deixar rodando sozinho

1. **Actions** → workflow **"Rotina diária Tiny"** → **Run workflow**
2. Acompanhe o log. Na primeira vez, vale rodar `--diagnostico` manualmente
   uma vez (edite temporariamente o `run:` do workflow pra
   `python main.py --diagnostico`, rode, confira o produto de exemplo no
   log, e desfaça a edição depois)
3. Quando o relatório fizer sentido, é só deixar — ele já roda sozinho
   todo dia no horário configurado (07h de Brasília, ajustável no arquivo
   `.github/workflows/tiny-diario.yml`)

## Passo 8 — Acompanhar os resultados

Cada execução aparece em **Actions** → **"Rotina diária Tiny"**. Toque numa
execução pra ver o log, ou baixe o arquivo **relatorio-...** nos "Artifacts"
daquela execução pra ver o JSON completo do que foi encontrado/corrigido.

---

## Resumindo o que cada Secret faz

- `TINY_CLIENT_ID` / `TINY_CLIENT_SECRET` — identificam sua aplicação pro Tiny
- `TINY_REDIRECT_URI` — pra onde o Tiny manda o usuário depois do login
- `GH_PAT` — permite que o robô atualize o `TINY_REFRESH_TOKEN` sozinho
- `TINY_REFRESH_TOKEN` — criado automaticamente no Passo 6, renovado sozinho depois
