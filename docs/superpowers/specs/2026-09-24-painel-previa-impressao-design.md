# Painel de prévia de impressão (sub-projeto 5)

Data: 2026-09-24 · Status: rascunho para revisão · Tamanho estimado: M (~1 a 1,5 dia, depois de SP2 e SP4)

## Contexto

O cliente monta o pedido no site e quer ter noção de como ficará a impressão. A película tem **58 cm de largura útil**;
as artes já estão nas medidas reais. O site mostra um painel de 58 × 200 cm com as artes do pedido encaixadas
automaticamente, em páginas navegáveis. Visão geral e demais sub-projetos: [`docs/roadmap.md`](../../roadmap.md).

## Objetivo e critério de sucesso

Na tela de resumo do pedido, o cliente vê o painel: cada arte na posição encaixada, na escala real, com abas de página
(`Página 1 de 3`) e o **comprimento usado** ("2,45 m"). Um item com quantidade 3 aparece 3 vezes. Mudar o carrinho
recalcula o painel na hora. Roda em celular, sem baixar `.tif`.

## Decisões (confirmadas com o dono)

| Tema | Decisão |
|---|---|
| Quem vê | O **cliente**, no site (o algoritmo roda no navegador, em TypeScript) |
| Saída | Só prévia na tela. PDF pronto fica para depois |
| Imagens | Prévias leves `.webp`, sem `.tif` no site |
| Largura / página | 58 cm × 200 cm por página; passou de 200 cm, abre a próxima página |
| Giro | 0° ou 90° |
| Formato da peça | Sempre **retângulo** (caixa da arte); sem encaixe pela silhueta |
| Espaçamento mínimo | 1/10 pol = 0,254 cm entre artes, na largura **e** na altura |
| Objetivo do encaixe | Menor comprimento total (economia para o cliente) |
| Quantidade | N cópias da arte, todas no painel |
| Preço | Fora daqui: só mostra comprimento. Preço por metro é decisão futura |

## Dados de que o painel precisa (mudança no SP2)

Cada item do catálogo público ganha `width_cm` e `height_cm` (opcionais no contrato, mesma `schema_version`).

- **Origem:** o SP2 lê o `.tif` (tamanho em pixels ÷ resolução gravada no arquivo) e mede o **retângulo útil**, isto é,
  a área com tinta, ignorando margem transparente. Sem isso o encaixe desperdiça película.
- **Prévia recortada:** a `.webp` gerada pelo SP2 é recortada nesse retângulo, então a imagem desenhada tem exatamente
  o tamanho do retângulo encaixado.
- **Levantamento (505 `.tif` reais em `X:\TIMES DE FUTEBOL`):** 495 com 300 dpi e 10 com 400 dpi, todos com resolução
  gravada. Seis artes "em tiras" medem 58,1 cm de largura por arredondamento, então a largura útil tem tolerância de
  0,2 cm (arte de até 58,2 cm entra e é tratada como 58,0).
- **Item que não cabe** (largura > 58,2 cm nos dois sentidos, ou altura > 200 cm): o painel avisa o nome do item e não o
  posiciona; o pedido continua válido.

## Algoritmo de encaixe

Módulo puro em TypeScript (sem DOM), em `web/site/src/layout/`, reaproveitável no Worker (SP3):

1. **Expandir:** cada item vira `quantity` retângulos independentes, com id estável `<item>#<n>`.
2. **Espaçamento (margem de largura e de altura):** cada retângulo cresce `gap` (0,254 cm) em largura e em altura, e a página cresce o mesmo valor, para
   garantir 0,254 cm entre artes sem sobrar borda.
3. **Empacotar (MaxRects, melhor encaixe por lado curto):** peças ordenadas da maior para a menor; cada peça tenta as duas
   orientações (0° e 90°) e escolhe a posição que menos desperdiça.
4. **Páginas:** enche a página 1 até não caber mais; peças restantes vão para a página 2, e assim por diante. A última
   página é medida só até a última arte.
5. **Escolher o melhor:** roda 3 ordenações (área, maior lado, altura) e fica com a de **menor comprimento total**
   (`páginas cheias × 200 + altura da última`).
6. **Determinismo:** mesma entrada gera o mesmo resultado (desempate por id). Necessário para o Montador ou o Worker
   reproduzirem o painel.

Saída:

```json
{
  "pages": [
    { "index": 1, "used_length_cm": 200.0,
      "placements": [ { "ref": "numero_costas:10#1", "x_cm": 0.0, "y_cm": 0.0, "rotated": false } ] }
  ],
  "total_length_cm": 245.3,
  "unplaced": [ { "ref": "logos:ALL#1", "reason": "maior_que_a_pelicula" } ]
}
```

## Interface (site)

- Painel em SVG/canvas na escala real, com régua lateral em cm e a página como retângulo 58 × 200.
- Abas ou seletor `Página 1 de N`, com setas; zoom com pinça no celular.
- Resumo: "Comprimento usado: X,XX m" e "N artes em M páginas".
- Estados: carregando (esqueleto), vazio ("Adicione itens para ver o painel"), erro de imagem (retângulo com o nome),
  item que não coube (aviso listado).
- Acessibilidade: alvos de 44 px, foco visível, texto alternativo por arte, `prefers-reduced-motion`.

## Pedido enviado e Montador

- O pedido pode levar o painel como campo **opcional** `layout` (mesma `schema_version` do contrato do pedido); o parser do
  SP1 já ignora campos desconhecidos, então isso não quebra o Montador atual.
- O `layout` do cliente é **só informativo**: quem manda é o servidor/Montador, que recalcula com o mesmo módulo. Nunca
  usar o painel enviado pelo navegador para cobrar ou produzir.
- Ver o painel dentro do Montador fica fora deste sub-projeto.

## Testes (escritos antes do código)

- Nenhuma arte fora dos limites da página; nenhuma sobreposição.
- Espaçamento mínimo de 0,254 cm respeitado entre qualquer par.
- Somente rotações de 0° e 90°.
- Quantidade: `sum(quantity)` retângulos posicionados (mais os não posicionados).
- Item de 58,1 cm de largura entra (tolerância); 58,3 cm vai para `unplaced`.
- Passou de 200 cm abre a página 2; a última página mede só até a última arte.
- Determinismo: duas execuções idênticas; ordem dos itens de entrada não altera o comprimento total.
- Casos reais: as 6 artes "em tiras" de 58,1 × 4,6 cm empilham sem giro; letras pequenas ocupam o espaço restante.
- Desempenho: 300 peças em menos de 200 ms em celular médio.

## Riscos

- Medir o retângulo útil em `.tif` grande (até 74 MB) e CMYK com alfa: no SP2; já validado que `tifffile` lê os 505.
- Encaixe heurístico não é o ótimo; o critério é "bom o bastante e previsível", com o melhor de 3 ordenações.
- O painel mostra estimativa: a produção final é a do Montador. Deixar isso escrito na tela.

## Fora do escopo

Encaixe pela silhueta da arte (só retângulos), PDF de saída, preço, upload de arte do cliente (SP6), painel dentro do Montador, edição manual das posições, giro em
ângulos diferentes de 90°.
