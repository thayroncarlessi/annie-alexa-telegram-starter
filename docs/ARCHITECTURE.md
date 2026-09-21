# Architecture

## Fluxo principal

```text
Alexa / Echo
    │  evento de skill
    ▼
AWS Lambda
    │  valida ALEXA_SKILL_ID
    │  HMAC(timestamp + body)
    ▼
Gateway HTTPS
    │  allowlist de intents
    │  autorização somente leitura
    ├──────────────► Adaptador de IA (opcional)
    └──────────────► Telegram Bot API (notificação opcional)
```

O gateway é uma fronteira de segurança e adaptação. Ele não deve virar um proxy genérico para qualquer URL ou comando. Cada fonte de dados deve ter um adaptador com permissões mínimas e um contrato de saída validado.

## Componentes

### Alexa Custom Skill

Define o invocation name, intents, slots e as frases de exemplo. A skill não deve conter tokens de Telegram ou de IA. O endpoint configurado na console aponta para a Lambda.

### Lambda

```examples/lambda_handler.py``` valida o identificador da skill e encaminha o evento para o gateway com HMAC. Em produção, configure timeout curto, logs redigidos, alarmes e uma política IAM mínima.

### Gateway

```examples/gateway.py``` mostra uma implementação pequena com a biblioteca padrão do Python. Ela oferece ```GET /health``` e ```POST /alexa```, valida corpo, assinatura e timestamp, e aceita somente intents declarados.

### Adaptadores downstream

Um adaptador pode consultar uma API própria, um serviço de IA ou enviar uma notificação. Ele deve receber apenas o necessário e devolver uma resposta estruturada, por exemplo:

```json
{"answer": "resposta curta e validada", "source": "demo"}
```

O código do exemplo não lê banco local, não busca histórico de Telegram e não executa comandos do sistema. Esses comportamentos exigem uma política independente, autenticação adicional e revisão de privacidade.

## Perfis de implantação

### Desenvolvimento local

- gateway ligado em ```127.0.0.1```;
- túnel HTTPS temporário somente para testes;
- segredos em arquivo local ignorado ou gerenciador de segredos;
- dados de demonstração, não dados de produção.

### Produção simples

- Lambda e gateway em serviços gerenciados;
- HTTPS terminado por um API Gateway ou proxy confiável;
- Secret Manager para tokens e HMAC;
- allowlists e rate limiting no perímetro;
- logs sem prompts, mensagens ou dados pessoais.

### Separação organizacional

Quando o projeto for usado por uma empresa, mantenha o starter público como referência e crie adaptadores privados para sistemas internos. Não faça fork da configuração de produção para este repositório público. O fato de o código ser aberto não autoriza acesso aos dados da organização.

## Contrato de dados mínimo

Entrada do gateway:

- evento JSON da Alexa;
- timestamp e assinatura nos headers;
- nenhum segredo no corpo.

Saída para a Alexa:

- resposta JSON compatível com a skill;
- SSML escapado e limitado;
- mensagem genérica em caso de falha.

Saída para serviços externos:

- payload mínimo;
- timeout curto;
- validação de status e formato;
- nenhum retry infinito;
- falha isolada, sem derrubar o caminho de voz.

## Evolução recomendada

1. Adicionar testes unitários para assinatura, replay e allowlist.
2. Trocar o servidor HTTP de demonstração por uma camada gerenciada.
3. Adicionar correlação de requisição sem registrar conteúdo sensível.
4. Implementar armazenamento de replay com TTL.
5. Definir retenção e exclusão para mensagens encaminhadas.
6. Fazer revisão de ameaça e privacidade antes de conectar dados reais.
