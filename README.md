# LLM Compact

LLM Compact é um projeto para preparar código-fonte antes de enviá-lo a modelos de linguagem. A proposta é remover formatação dispensável, comparar a quantidade de tokens antes e depois e facilitar a cópia do resultado para um prompt.

O projeto começa como uma aplicação independente. A próxima etapa é levar o mesmo fluxo para uma extensão do VS Code.

## Motivação

Código bem formatado é importante para quem desenvolve, mas parte dos espaços, recuos e quebras de linha pode aumentar o número de tokens enviados a uma LLM. Compactar o código pode reduzir esse consumo, desde que a transformação preserve as informações necessárias e continue útil para a tarefa solicitada ao modelo.

A ideia foi motivada pelo artigo [*The Hidden Cost of Readability: How Code Formatting Silently Consumes Your LLM Budget*](https://arxiv.org/abs/2508.13666).

## Objetivos

- Compactar código respeitando as regras de cada linguagem.
- Comparar a contagem de tokens do código original e do compactado.
- Mostrar a economia obtida antes de copiar o resultado.
- Reaproveitar a lógica de processamento em uma futura extensão do VS Code.

## Avaliação

Uma redução no número de tokens, por si só, não demonstra que a transformação é útil. Este projeto pretende avaliar também:

- Se o código mantém sua estrutura e seu comportamento.
- Como a economia varia entre linguagens e tokenizadores.
- Se a compactação afeta a qualidade das respostas da LLM em tarefas de programação.

## Próximas etapas

- Documentar as linguagens e os tokenizadores efetivamente suportados.
- Adicionar exemplos reproduzíveis de entrada, saída e economia de tokens.
- Validar casos delicados, como strings, comentários e código incompleto.
- Criar a extensão do VS Code usando a mesma lógica da aplicação.

## Referência

Pan, D. et al. *The Hidden Cost of Readability: How Code Formatting Silently Consumes Your LLM Budget*. arXiv:2508.13666, 2025. https://arxiv.org/abs/2508.13666
