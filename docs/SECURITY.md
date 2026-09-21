# Security model

Este starter separa voz, transporte, autorização, dados e geração de linguagem. O objetivo é tornar explícitos os limites que precisam ser preservados quando alguém adapta o exemplo.

## Limites de confiança

1. A Alexa fornece um evento de skill; o evento não deve ser tratado como autorização para acessar qualquer fonte de dados.
2. A Lambda valida o identificador da skill e assina o corpo enviado ao gateway.
3. O gateway valida a assinatura, a janela de tempo e o conjunto de intents permitido.
4. Adaptadores downstream recebem somente a informação mínima necessária para a consulta autorizada.
5. Telegram e provedores de IA são serviços externos: trate respostas, nomes, mensagens e documentos como dados não confiáveis.

## Assinatura do exemplo

A Lambda calcula:

```text
data = timestamp + "\n" + request_body
signature = HMAC-SHA256(GATEWAY_SHARED_SECRET, data)
```

Ela envia a assinatura no cabeçalho ```X-Bridge-Signature: sha256=<hex>``` e o timestamp em ```X-Bridge-Timestamp```. O gateway rejeita mensagens fora da janela configurada em ```GATEWAY_MAX_SKEW_SECONDS```.

Em produção:

- gere o segredo com um gerador criptograficamente seguro;
- armazene-o em Secret Manager ou equivalente;
- faça rotação coordenada entre Lambda e gateway;
- use HTTPS com certificado válido;
- adicione um identificador de requisição e uma store de replay com TTL;
- limite tamanho, frequência e tempo de execução;
- use comparação em tempo constante para segredos e assinaturas.

## Alexa

Valide o application ID da skill em todos os caminhos de entrada. Se a skill usar um endpoint direto da Alexa, implemente também a validação oficial de assinatura/certificado exigida pela plataforma. O exemplo público mantém essa parte curta para facilitar o estudo; não remova a validação ao adaptá-lo.

Não aceite nome de intent vindo do usuário como uma rota arbitrária. Mantenha uma allowlist explícita de intents e parâmetros. Operações de escrita, pagamentos, comandos de dispositivo e execução de código devem ficar fora deste starter.

## Telegram

- Restrinja o bot a chats e usuários autorizados.
- Não confie somente no nome exibido ou no username; use IDs confirmados na configuração privada.
- Nunca publique token do BotFather.
- Não replique histórico integral por padrão.
- Se enviar uma notificação, minimize o conteúdo e não inclua o texto falado automaticamente.
- Redija mensagens, nomes, anexos e IDs em logs públicos.

O exemplo usa a Bot API apenas para uma notificação opcional e genérica. Um fluxo conversacional real precisa de um adaptador separado, com política de retenção, deduplicação, controle de acesso e tratamento de respostas atrasadas.

## IA e prompt injection

Todo conteúdo externo deve ser tratado como dado, não como instrução operacional. Não permita que uma mensagem do Telegram ou uma resposta do modelo altere allowlists, segredos, permissões, destinatários ou rotas.

Use um contrato de saída estruturado, limite o tamanho da resposta e valide o campo ```answer```. Mantenha a geração de linguagem fora de decisões financeiras, jurídicas, regulatórias, de crédito ou de segurança sem revisão humana.

## O que não deve entrar neste repositório

- tokens, chaves privadas, cookies ou códigos de recuperação;
- IDs reais de usuários, clientes, skills ou chats;
- URLs de túnel temporárias em uso;
- arquivos ```.env```, bancos SQLite ou históricos do Telegram;
- documentos internos, dados financeiros ou dados pessoais;
- logs integrais de prompts e respostas;
- caminhos locais do computador do mantenedor.

Se um segredo for publicado por engano, revogue-o imediatamente, investigue o histórico e publique uma correção. Remover o arquivo em um commit posterior não invalida o segredo já exposto.

## Checklist de revisão

- [ ] O endpoint público aceita somente HTTPS.
- [ ] A skill ID é validada antes de qualquer consulta.
- [ ] HMAC, timestamp e replay são verificados.
- [ ] A allowlist de intents está fechada.
- [ ] O bot tem allowlist de chat/usuário.
- [ ] Logs são redigidos e têm retenção definida.
- [ ] Segredos são externos ao Git.
- [ ] A fonte de dados é somente leitura neste fluxo.
- [ ] Existe revisão humana para respostas de alto impacto.
