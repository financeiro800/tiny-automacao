# Integração Tiny/Olist — Tributação, Notas, Pedidos e Produtos

Projeto inicial para automatizar correções e checagens no seu catálogo do
Tiny ERP (Olist), começando pela **tributação** (NCM/CST), que foi a
prioridade que você indicou. Os outros 3 módulos (notas fiscais, pedidos,
produtos) já estão com a estrutura pronta para entrarmos em detalhe nas
próximas conversas.

> **Rodando só pelo celular, sem computador?** Siga o guia
> **[GITHUB_SETUP.md](GITHUB_SETUP.md)** — ele monta tudo isso rodando
> sozinho no GitHub Actions, agendado pra rodar todo dia. As instruções
> abaixo (passos 1 a 7) são para quem prefere rodar local, num computador.

## O que já funciona

- Autenticação OAuth2 completa com a API v3 do Tiny (com renovação automática de token)
- Cliente HTTP com paginação automática e tratamento de rate limit
- Módulo de **tributação**: compara o cadastro fiscal de cada produto com
  regras que você define, e reporta (ou corrige) divergências de NCM,
  CEST, origem e CST de ICMS/PIS/COFINS

## O que ainda precisa da sua entrada

- **Regras de tributação reais** — o arquivo `config/regras_tributacao.json`
  está com valores de exemplo. Preciso que você me passe (ou preencha
  direto no arquivo) o NCM/CST correto por categoria ou SKU do seu catálogo.
- **Nomes exatos dos campos** — a API do Tiny pode nomear alguns campos
  fiscais de forma um pouco diferente do que usei aqui. O comando
  `--diagnostico` abaixo resolve isso mostrando um produto real.
- **Regras dos outros 3 módulos** — quando formos para notas fiscais,
  pedidos e produtos, preciso que você descreva o que "corrigir/automatizar"
  significa em cada caso (ex: "gerar NF-e automaticamente quando o pedido
  for pago", "meus produtos sem NCM aplicar o NCM da categoria", etc.)

## Configuração (passo a passo)

1. **Crie uma aplicação no Tiny**: dentro do ERP, vá em
   Conta > Aplicativos/Integrações > Nova aplicação, e copie o `client_id`
   e `client_secret` gerados.

   **Sobre a URL de redirecionamento:** diferente de outras APIs (como a
   do Bling), o Tiny exige que essa URL aponte para um endereço que
   realmente responda — não aceita só um `localhost` copiado do
   navegador. Jeito mais simples, sem precisar subir servidor nenhum:
   1. Acesse https://webhook.site e copie a URL única gerada pra você
      (algo como `https://webhook.site/xxxxxxxx-xxxx-...`)
   2. Cole essa URL como redirect URI na criação da aplicação no Tiny
   3. Cole essa mesma URL em `TINY_REDIRECT_URI` no seu `.env`
   4. No passo 4 (`python auth.py`), depois de autorizar, a página do
      webhook.site vai mostrar a requisição recebida com o `?code=...`
      na aba "Request" — copie a URL completa de lá pro terminal.
2. **Instale as dependências**:
   ```
   pip install -r requirements.txt
   ```
3. **Configure as credenciais**: copie `.env.example` para `.env` e
   preencha `TINY_CLIENT_ID` e `TINY_CLIENT_SECRET`.
4. **Autorize a aplicação (só uma vez)**:
   ```
   python auth.py
   ```
   Isso abre o navegador para você logar no Tiny e autorizar; depois cola
   a URL de retorno no terminal. O `refresh_token` gerado é salvo
   automaticamente no `.env` — não precisa repetir esse passo.
5. **Confira os nomes de campo antes de rodar em massa**:
   ```
   python main.py --diagnostico
   ```
   Isso imprime um produto completo (JSON) do seu catálogo. Me envie esse
   retorno para eu ajustar `modules/tributacao.py` com os nomes de campo
   certos, se forem diferentes dos que usei.
6. **Rode em modo simulação** (não altera nada, só mostra o que encontrou):
   ```
   python main.py
   ```
7. **Quando estiver satisfeito com o relatório, rode aplicando de verdade**:
   ```
   python main.py --aplicar
   ```

## Automação diária

Depois de validado, agende no cron (Linux/Mac) ou Agendador de Tarefas
(Windows) para rodar sozinho todo dia. Exemplo de cron às 7h da manhã:

```
0 7 * * * cd /caminho/do/projeto && /usr/bin/python3 main.py --aplicar >> logs/cron.log 2>&1
```

Cada execução também salva um relatório em JSON em `logs/`.

## Estrutura do projeto

```
tiny_integration/
├── auth.py                    # login OAuth2 e renovação de token
├── client.py                  # cliente HTTP genérico p/ API do Tiny
├── config.py                  # variáveis de ambiente e endpoints
├── main.py                    # orquestrador (rodar isso todo dia)
├── config/
│   └── regras_tributacao.json # AJUSTAR com as regras reais do seu catálogo
└── modules/
    ├── tributacao.py          # ✅ pronto (prioridade 1)
    ├── notas_fiscais.py       # 🔲 esqueleto (prioridade 2)
    ├── pedidos.py              # 🔲 esqueleto (prioridade 3)
    └── produtos.py             # 🔲 esqueleto (prioridade 4)
```

## Próximos passos sugeridos

1. Rodar `--diagnostico` e me mandar o retorno pra eu confirmar os campos
2. Preencher `regras_tributacao.json` com dados reais e validar o relatório em modo simulação
3. Definir juntos as regras de automação de notas fiscais (prioridade 2)
