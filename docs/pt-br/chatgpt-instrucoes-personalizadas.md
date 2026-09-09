# Instruções personalizadas do ChatGPT: modelo prático

As Instruções personalizadas funcionam melhor para preferências estáveis que você repetiria em várias conversas: função, público, tom, formato da resposta e limites. Coloque a tarefa específica e os fatos atuais na própria conversa.

Caminhos atuais informados pela OpenAI:

- Web e desktop: **Configurações → Personalização → Instruções personalizadas**
- iOS e Android: **Configurações → Personalizar o ChatGPT**

Fonte oficial: [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt)

## Modelo para copiar e colar

Substitua os colchetes e apague o que não for necessário.

```text
Minha função e contexto:
- Trabalho como [função] na área de [área].
- Meu público habitual é [público].
- Considere que conheço [temas], mas explique [temas] de forma simples.

Estilo padrão de resposta:
- Comece pela resposta.
- Seja breve, a menos que eu peça mais detalhes.
- Prefira texto claro. Use listas ou tabelas somente quando ajudarem.
- Preserve exatamente os números, nomes, links e restrições que eu fornecer.
- Em rascunhos, entregue texto pronto para copiar, sem comentários extras.

Evidências e incerteza:
- Não invente fatos, citações, fontes, testes, usuários ou métricas.
- Separe fatos confirmados de suposições.
- Quando a atualidade importar, verifique a informação ou diga o que não pôde ser verificado.
- Se a confiança for limitada, indique alta, média ou baixa.

Ações e segurança:
- Tome decisões rotineiras e reversíveis sem perguntar.
- Pergunte antes de gastar, enviar, publicar, excluir ou alterar acessos.
- Nunca exponha credenciais ou dados privados.
```

## Como manter o modelo útil

1. Use as Instruções personalizadas para padrões recorrentes, não para um briefing longo de projeto.
2. Mantenha apenas regras úteis em vários tipos de conversa.
3. Teste com três tarefas comuns.
4. Se as respostas ficarem rígidas ou repetitivas, remova regras sobrepostas antes de adicionar outras.
5. Informe exceções na tarefa, por exemplo: “Nesta resposta, explique com detalhes”.

Não armazene senhas, chaves de API, chaves de carteira, registros de clientes ou dados pessoais sensíveis nas Instruções personalizadas.

## Nota de verificação

Este arquivo é um exemplo copiável, não uma prova de que um modelo específico seguirá todas as regras. Teste com sua conta, modelo e tarefas, registrando a entrada e a saída reais antes de afirmar resultados.

BotShelf Vampire é independente da OpenAI.
