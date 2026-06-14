# PRD — Lais Close: Copiloto de Fechamento para Locação

## 1. Visão Geral

O **Lais Close** é uma extensão operacional da Lais que aparece dentro de um chat ativo quando um lead demonstra intenção de fechar a locação de um imóvel.

A proposta é transformar o momento “quero fechar” em uma esteira guiada de fechamento, permitindo que corretor, imobiliária e IA acompanhem documentos, proposta, minuta contratual e pendências sem sair da conversa.

O produto não substitui análise jurídica, assinatura digital, aprovação de crédito ou sistemas administrativos da imobiliária. No MVP, ele atua como um **copiloto de fechamento**, organizando o processo, reduzindo atrito e acelerando a passagem do lead interessado para uma proposta formal.

---

## 2. Problema

A Lais já ajuda a imobiliária a atender, qualificar, recomendar imóveis e conduzir conversas com leads. Porém, quando o lead demonstra intenção de fechar negócio, o processo ainda tende a voltar para uma operação manual e fragmentada.

Hoje, após o lead dizer que quer alugar um imóvel, o corretor precisa:

* pedir documentos manualmente;
* acompanhar quais documentos foram enviados;
* conferir anexos recebidos no WhatsApp;
* procurar templates de proposta;
* copiar dados do lead, imóvel e negociação;
* montar proposta comercial;
* acionar administrativo/jurídico;
* acompanhar pendências por memória, planilha ou mensagens soltas;
* atualizar CRM ou sistema interno manualmente.

Esse processo cria atrito em um momento crítico: o lead já demonstrou intenção, mas ainda pode esfriar, desistir ou migrar para outro imóvel/imobiliária caso o fechamento seja lento ou confuso.

---

## 3. Oportunidade

A principal oportunidade está em aproximar a Lais do resultado final da imobiliária: **o contrato fechado**.

A Lais já conversa com o lead. O próximo passo é transformar essa conversa em uma operação estruturada de fechamento.

Frase central do produto:

> A Lais já conversa com o lead. O Lais Close ajuda a fechar o negócio.

---

## 4. Objetivo do MVP

Criar uma seção lateral dentro do chat da Lais que seja aberta quando o lead demonstrar intenção de fechar e permita ao corretor:

1. criar um processo de fechamento vinculado ao lead e ao imóvel;
2. acompanhar checklist de documentos obrigatórios;
3. classificar anexos enviados pelo lead no chat;
4. gerar proposta comercial com base em template;
5. gerar uma minuta/preparação contratual a partir de template;
6. visualizar pendências e próximos passos;
7. gerar mensagens automáticas para o lead;
8. produzir um resumo final para CRM, gestor ou time administrativo.

---

## 5. Não Objetivos do MVP

O MVP não deve tentar resolver completamente:

* assinatura digital;
* contrato juridicamente final;
* análise de crédito real;
* integração bancária;
* cobrança ou pagamento;
* vistoria;
* entrega de chaves;
* OCR avançado;
* validação documental oficial;
* integração real com cartórios, bancos ou seguradoras;
* substituição de advogado, jurídico ou administrativo.

O contrato gerado deve ser tratado como **minuta preliminar baseada em template aprovado pela imobiliária**, sempre com indicação de revisão humana.

---

## 6. Usuários

### 6.1 Corretor

Usuário principal do MVP.
Precisa conduzir o fechamento rapidamente, sem perder contexto da conversa.

Dores:

* não sabe exatamente quais documentos faltam;
* perde arquivos enviados no chat;
* precisa montar proposta manualmente;
* depende de administrativo/jurídico;
* esquece follow-ups;
* perde leads quentes por demora.

### 6.2 Gestor da imobiliária

Usuário secundário.
Quer visibilidade sobre gargalos de fechamento.

Dores:

* não sabe onde leads quentes estão travando;
* não tem padronização nas propostas;
* depende da memória dos corretores;
* não sabe quantos fechamentos estão parados por documentação;
* não consegue medir SLA do fechamento.

### 6.3 Lead locatário

Usuário indireto.
Recebe mensagens, pedidos de documentos e propostas geradas pelo sistema.

Dores:

* não entende quais documentos precisa mandar;
* recebe instruções confusas;
* demora para saber próximo passo;
* perde confiança quando a imobiliária parece desorganizada.

---

## 7. Jornada Principal

### 7.1 Detecção de intenção

Durante o chat ativo, o lead envia uma mensagem como:

> Gostei desse apartamento, quero fechar.

A Lais identifica intenção de fechamento e exibe uma sugestão para o corretor:

> Este lead demonstrou intenção de fechar. Deseja abrir o Lais Close?

Botão:

> Abrir fechamento

---

### 7.2 Criação do fechamento

Ao clicar no botão, a seção lateral do Lais Close é aberta.

O sistema cria um processo de fechamento com:

* lead vinculado;
* imóvel vinculado;
* tipo de operação: locação;
* status inicial: em negociação;
* checklist de documentos;
* proposta em branco;
* minuta não iniciada;
* próximas ações sugeridas.

---

### 7.3 Gestão de documentos

O corretor escolhe ou confirma o modelo documental.

Exemplo:

* locação PF com caução;
* locação PF com fiador;
* locação PF com seguro-fiança;
* locação PJ;
* compra e venda.

O sistema carrega um checklist padrão de documentos.

Quando o lead envia anexos no chat, o copiloto sugere a classificação:

> Este arquivo parece ser um comprovante de renda. Deseja vincular ao checklist?

O corretor pode:

* aceitar;
* rejeitar;
* corrigir o tipo do documento;
* marcar como pendente;
* pedir reenvio.

---

### 7.4 Geração de proposta

O corretor usa o mini chat do Lais Close para gerar uma proposta.

Exemplo de comando:

> Gere uma proposta com aluguel de R$ 2.700, condomínio de R$ 520, IPTU de R$ 110, caução de 3 meses, entrada em 10/07 e contrato de 30 meses.

O sistema gera um preview da proposta com base no template padrão da imobiliária.

O corretor pode:

* editar;
* pedir ajuste;
* aprovar;
* copiar;
* salvar;
* gerar mensagem para o lead.

---

### 7.5 Geração de minuta

Com base nos dados disponíveis, o sistema gera um preview de minuta contratual.

A minuta deve destacar campos ausentes.

Exemplo:

* nome completo do locatário: preenchido;
* CPF: pendente;
* endereço do imóvel: preenchido;
* valor do aluguel: preenchido;
* garantia: preenchida;
* prazo: preenchido;
* data de início: pendente.

O sistema não deve inventar informações ausentes.

---

### 7.6 Resumo e handoff

A qualquer momento, o corretor pode clicar em:

> Gerar resumo do fechamento

O sistema gera:

* dados do lead;
* imóvel;
* status atual;
* documentos recebidos;
* documentos pendentes;
* condições comerciais;
* proposta;
* pendências;
* próxima ação recomendada.

Esse resumo pode ser usado para atualizar CRM, encaminhar ao administrativo ou registrar histórico.

---

## 8. Funcionalidades do MVP

### 8.1 P0 — Essenciais para demonstração

#### F1. Botão “Abrir Fechamento”

O sistema deve exibir um botão para abrir o Lais Close quando o lead demonstrar intenção de fechar.

No MVP, a detecção pode ser mockada por mensagem específica, como:

> quero fechar

ou acionada manualmente pelo usuário.

---

#### F2. Seção lateral do Lais Close

A interface deve abrir uma seção lateral dentro do chat com:

* dados do lead;
* dados do imóvel;
* status do fechamento;
* abas de documentos, proposta, contrato e resumo;
* mini chat do copiloto;
* área de preview;
* botões de ação.

---

#### F3. Checklist de documentos

O sistema deve permitir selecionar um modelo de documentos.

Exemplo de modelo MVP:

**Locação PF com caução**

Documentos:

* RG ou CNH;
* CPF;
* comprovante de renda;
* comprovante de residência;
* estado civil;
* comprovante de pagamento da caução.

Cada documento deve ter status:

* pendente;
* recebido;
* aprovado manualmente;
* precisa reenvio.

---

#### F4. Associação de anexos ao checklist

O sistema deve simular anexos vindos do chat e permitir associá-los a itens do checklist.

No MVP, não é obrigatório implementar OCR real. A classificação pode ser feita com base em nome de arquivo, tipo mockado ou escolha manual assistida por IA.

---

#### F5. Construtor de proposta

O sistema deve gerar uma proposta comercial a partir de:

* dados do lead;
* dados do imóvel;
* condições informadas pelo corretor;
* template padrão.

A proposta deve aparecer em preview editável ou regenerável.

---

#### F6. Gerador de minuta

O sistema deve preencher um template de minuta preliminar com os dados disponíveis.

O sistema deve destacar campos faltantes e incluir aviso de revisão humana.

---

#### F7. Geração de mensagens para o lead

O sistema deve gerar mensagens curtas para:

* pedir documentos faltantes;
* confirmar recebimento;
* enviar resumo da proposta;
* avisar próxima etapa;
* cobrar pendências.

---

#### F8. Resumo do fechamento

O sistema deve gerar um resumo estruturado do processo com:

* status;
* documentos recebidos;
* documentos pendentes;
* proposta;
* minuta;
* próximas ações.

---

## 9. Funcionalidades P1 — Desejáveis, se houver tempo

* salvar templates customizados;
* editar checklist documental;
* alterar status do fechamento;
* timeline de eventos;
* cálculo de progresso percentual;
* alertas de SLA;
* mock de exportação para CRM;
* histórico de versões da proposta;
* múltiplos tipos de garantia.

---

## 10. Funcionalidades P2 — Futuro

* integração real com CRM;
* integração com assinatura digital;
* análise de crédito;
* OCR/document AI;
* validação automática de documentos;
* workflow de aprovação interna;
* integração com jurídico;
* integração com vistoria;
* integração com cobrança;
* envio automático de proposta ao lead;
* métricas de conversão por etapa;
* recuperação automática de fechamentos parados.

---

## 11. Requisitos de Produto

### R1. O usuário deve conseguir abrir o Lais Close a partir de um chat ativo

Critério de aceite:

* Dado um chat com lead e imóvel selecionado,
* quando o usuário clicar em “Abrir Fechamento”,
* então a seção lateral deve abrir com dados do lead e imóvel.

---

### R2. O usuário deve conseguir acompanhar documentos pendentes

Critério de aceite:

* Dado um modelo documental selecionado,
* quando a seção de documentos for aberta,
* então o sistema deve listar todos os documentos obrigatórios e seus status.

---

### R3. O usuário deve conseguir associar um anexo recebido a um documento

Critério de aceite:

* Dado um anexo enviado no chat,
* quando o usuário selecionar “vincular ao checklist”,
* então o documento correspondente deve mudar para “recebido”.

---

### R4. O usuário deve conseguir gerar uma proposta

Critério de aceite:

* Dado um lead, imóvel e condições comerciais,
* quando o usuário solicitar uma proposta,
* então o sistema deve gerar um texto estruturado com base no template.

---

### R5. O usuário deve conseguir gerar uma minuta preliminar

Critério de aceite:

* Dado um template de contrato e dados disponíveis,
* quando o usuário solicitar uma minuta,
* então o sistema deve preencher os campos conhecidos e destacar campos pendentes.

---

### R6. O usuário deve conseguir gerar mensagens para o lead

Critério de aceite:

* Dado um conjunto de pendências,
* quando o usuário clicar em “Gerar mensagem”,
* então o sistema deve gerar uma mensagem clara, curta e orientada ao próximo passo.

---

### R7. O usuário deve conseguir gerar resumo do fechamento

Critério de aceite:

* Dado um processo de fechamento em andamento,
* quando o usuário clicar em “Gerar resumo”,
* então o sistema deve retornar um resumo estruturado com status, pendências e próxima ação.

---

## 12. Métricas de Sucesso

### Métricas de negócio futuras

* aumento da taxa de leads interessados que chegam à proposta;
* redução do tempo entre “quero fechar” e proposta enviada;
* redução de abandono por documentação;
* aumento da taxa de contratos fechados;
* redução de tarefas manuais do corretor;
* aumento da padronização das propostas.

### Métricas do MVP/hackathon

* tempo para abrir um fechamento;
* número de etapas demonstráveis;
* clareza visual do fluxo;
* capacidade de gerar proposta com dados mockados;
* capacidade de listar pendências;
* capacidade de gerar mensagem útil para o lead;
* qualidade do resumo final.

---

## 13. Dados Mockados Necessários

O MVP deve operar com bases mockadas de:

### Leads

* nome;
* telefone;
* renda declarada;
* interesse;
* data desejada de mudança;
* mensagens recentes;
* anexos enviados.

### Imóveis

* endereço;
* bairro;
* aluguel;
* condomínio;
* IPTU;
* quartos;
* vagas;
* aceita pet;
* status;
* proprietário.

### Templates

* checklist documental;
* proposta;
* minuta contratual;
* mensagens.

### Fechamentos

* lead;
* imóvel;
* status;
* documentos;
* proposta;
* contrato;
* pendências;
* histórico.

---

## 14. Riscos

### Risco jurídico

Gerar contratos automaticamente pode criar risco se o produto parecer substituir jurídico.

Mitigação:

* chamar de minuta preliminar;
* usar templates aprovados;
* destacar revisão humana;
* não criar cláusulas novas;
* não dar parecer jurídico.

---

### Risco de escopo

O produto pode crescer demais e tentar resolver crédito, assinatura, contrato, vistoria e pagamento.

Mitigação:

* focar em documentos, proposta, minuta e resumo;
* tratar integrações como futuro;
* manter dados mockados no MVP.

---

### Risco de parecer redundante com a Lais

A Lais já atende, qualifica e recomenda imóveis.

Mitigação:

* posicionar como módulo pós-intenção;
* focar em fechamento operacional;
* não vender como chatbot;
* enfatizar “do quero fechar até proposta/minuta”.

---

## 15. Pitch do Produto

Quando o lead diz “quero fechar”, o corretor ainda precisa sair do chat, procurar documentos, montar proposta, acionar administrativo e acompanhar pendências manualmente.

O **Lais Close** transforma esse momento em uma esteira guiada dentro da própria conversa.

Ele cria um processo de fechamento, acompanha documentos, gera proposta, prepara minuta e resume próximos passos.

Com isso, a Lais deixa de ser apenas uma IA de atendimento e passa a atuar também como copiloto operacional de fechamento.

---

## 16. Escopo Final Recomendado para Hackathon

O MVP deve demonstrar:

1. chat ativo com lead;
2. botão “Abrir Fechamento”;
3. seção lateral Lais Close;
4. checklist documental;
5. anexos mockados vindos do chat;
6. classificação/vinculação de documentos;
7. geração de proposta;
8. geração de minuta preliminar;
9. geração de mensagem para o lead;
10. resumo final do fechamento.
