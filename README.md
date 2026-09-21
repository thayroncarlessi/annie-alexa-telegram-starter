# annie-alexa-telegram-starter
A generic, privacy-first starter for connecting Alexa, Telegram and an AI provider.
# Annie Alexa–Telegram Starter

Um projeto de referência, seguro e copiável para conectar uma skill personalizada da Amazon Alexa a um bot do Telegram e, opcionalmente, a um provedor de IA.

> Este repositório é educacional. Ele não acessa contas privadas, históricos pessoais, bancos de dados, ambientes corporativos ou serviços da Vantti/Lend Capital. Para uso real, substitua todos os placeholders e faça uma revisão de segurança.

## O que este starter demonstra

- recebimento de uma requisição de uma skill Alexa;
- validação de identidade da skill e do chamador;
- autenticação entre Alexa/Lambda e um gateway HTTPS;
- roteamento de comandos permitidos em modo somente leitura;
- consulta a um bot do Telegram usando allowlist de chat/usuário;
- adaptação opcional para um provedor de IA;
- respostas SSML simples e limites para evitar vazamento de dados.

## Arquitetura

```text
Echo/Alexa
   │
   ▼
Alexa Custom Skill ──► Lambda (webhook)
                           │ HTTPS + assinatura + timestamp
                           ▼
                    Gateway de integração
                       │              │
                       │              └──► Provedor de IA (opcional)
                       ▼
                 Telegram Bot API
```

Em desenvolvimento, o gateway pode rodar localmente atrás de um túnel HTTPS temporário. Em produção, prefira hospedar o gateway em uma função ou serviço gerenciado. Nunca publique uma porta local sem autenticação, allowlist e TLS.

## Estrutura do repositório

```text
annie-alexa-telegram-starter/
├── examples/              # exemplos mínimos, sem credenciais
├── docs/                  # arquitetura, configuração e segurança
├── .env.example           # nomes de variáveis, sem valores reais
├── .gitignore
├── LICENSE
└── README.md
```

## Começo rápido

1. Crie um bot de teste no Telegram e anote o token apenas em um gerenciador de segredos.
2. Escolha um provedor de IA, se quiser respostas geradas, e crie a chave na conta desse provedor.
3. Copie ```.env.example``` para ```.env```; nunca faça commit do arquivo preenchido.
4. Execute o exemplo localmente e exponha somente o endpoint necessário por HTTPS.
5. Na Alexa Developer Console, crie uma custom skill, defina um invocation name e aponte o endpoint da skill para sua Lambda.
6. Configure a Lambda para validar a requisição da Alexa e chamar o gateway usando a assinatura definida em ```docs/SECURITY.md```.
7. Teste primeiro com uma única consulta não sensível e confirme os logs redigidos.

Os exemplos são deliberadamente pequenos. Eles não são uma implantação pronta para produção: faltam, entre outras coisas, armazenamento de segredos, rate limiting distribuído, observabilidade, rotação de chaves e revisão de privacidade.

## Contrato de leitura

O starter assume que a Alexa só pode solicitar operações explicitamente permitidas, por exemplo:

- consultar o status de um serviço de demonstração;
- solicitar um resumo de dados já autorizados;
- encaminhar uma pergunta curta para um provedor de IA sem anexar histórico automaticamente.

Não inclua por padrão mensagens completas do Telegram, e-mails, calendário, documentos financeiros ou dados de clientes. Se uma integração de histórico for necessária, delimite os dados, aplique minimização, redija segredos e mantenha a operação fora do caminho de decisões automáticas.

## Checklist antes de publicar ou usar

- [ ] Nenhum token, chave, ID pessoal, URL de túnel ou dado de cliente aparece no código, no histórico ou nos logs.
- [ ] O bot aceita somente chats/usuários autorizados.
- [ ] A Lambda valida skill ID, application ID, timestamp e replay.
- [ ] O gateway usa HTTPS, autenticação forte e comparação em tempo constante.
- [ ] O conjunto de comandos é uma allowlist de leitura; não existe execução arbitrária.
- [ ] Logs não contêm texto integral de mensagens nem prompts sensíveis.
- [ ] Segredos ficam em Secret Manager, variáveis protegidas ou equivalente.
- [ ] A resposta da Alexa tem limite de tamanho e trata falhas sem revelar detalhes internos.
- [ ] Dados privados ficam em outro repositório e em outra configuração.

## Adaptando para uma organização

Substitua os nomes genéricos por seus próprios adaptadores, mantendo a separação entre:

1. interface de voz;
2. autenticação e transporte;
3. regras de autorização;
4. fonte de dados;
5. geração de linguagem.

O código público deve permanecer genérico. Regras internas, documentos, identificadores de clientes, histórico de conversas, bancos SQLite e configurações de produção devem ficar em um repositório privado e em um ambiente separado.

## Licença

MIT. O código é fornecido como exemplo; valide requisitos da Amazon, do Telegram, do provedor de IA e das leis de privacidade aplicáveis antes de colocá-lo em produção.
