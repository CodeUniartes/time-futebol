# Revisão do protótipo do Figma Make (2026-09-24)

Origem: export `Incorporate attachment.zip` (React 19 + Vite 8 + Tailwind 4 + react-router 8, ~2.500 linhas, dados
de exemplo). Base para o SP4; nada dele está no repositório ainda. Marca de referência: [`brand.md`](brand.md).

## O que está bom e pode ser reaproveitado

- **Stack igual à do plano do SP4** (React + Vite + Tailwind), então as telas viram o ponto de partida do `web/site`.
- **Tokens corretos** em `src/index.css`: `#F47726`, `#454849`, `#B95A1D`, `#F4F5F5`, `#D9DCDD`, `#6B7071`, Cabin, raios
  12 e 10, sombra suave, `focus-visible` com anel grafite, esqueleto com `prefers-reduced-motion`.
- **Telas e rotas prontas:** `/` (Time, Ano, Versão), `/catalog`, `/order` (painel), `/add-art`, `/signup`, `/login`,
  `/order-sent`, `/my-orders`. Botão "Ver catálogo" fica desativado até escolher o time.
- **Aviso de arte maior que a película (58 cm)** já existe na tela do painel.

## O que precisa mudar antes de virar produto

| # | Problema | Onde | Correção |
|---|---|---|---|
| 1 | Texto branco sobre laranja puro (contraste 2,8:1): contadores e passo atual do cadastro | `MainLayout.tsx:91`, `CatalogPage.tsx:149,207`, `SignupPage.tsx:119` | Fundo `dark-orange` (`#B95A1D`, 4,6:1) ou grafite com detalhe laranja |
| 2 | Texto em laranja sobre branco (2,8:1): "Clique para trocar", asteriscos de obrigatório, ações pequenas | `AddArtPage.tsx:128,187`, `CatalogPage.tsx:68`, `SignupPage.tsx:154,248`, `OrderPage.tsx:314` | `dark-orange` ou grafite; laranja só em ícone e forma |
| 3 | Texto de 7 a 10 px | `OrderPage.tsx:277`, badges | Mínimo de 12 px para texto que carrega informação |
| 4 | **Algoritmo do painel é provisório:** empacota em linhas, folga de 0,5 cm, gira só se não couber | `OrderPage.tsx` (`packItems`) | Trocar pelo módulo do SP5 (MaxRects, folga de 0,254 cm, giro de 90° para economizar, melhor de 3 ordenações, determinístico, testado) |
| 5 | Dados de exemplo com ids e categorias próprios | `src/data/mockData.ts` | Ler o `catalog.public.json` (ids do Montador; `width_cm`/`height_cm` do contrato) |
| 6 | Fonte carregada do Google Fonts em tempo de execução | `index.css` | Hospedar a Cabin junto do site (privacidade e desempenho) |
| 7 | Cadastro e login simulados | `SignupPage.tsx`, `LoginPage.tsx` | Ligar ao SP7 (código por WhatsApp só na criação, senha, redefinição pela gráfica) |
| 8 | Logo é um retângulo "Logo Uniartes" | `MainLayout.tsx`, `StartPage.tsx` | SVG oficial (ver pendência do repositório público em `brand.md`) |
| 9 | Status do pedido inventados (`pendente`, `em_producao`, `concluido`, `enviado`) | `mockData.ts` | Definir no SP3 quais estados existem, alinhados ao ClickUp |

## Mapeamento das categorias do protótipo para o Montador

| Protótipo | Montador (`CATEGORY_DEFINITIONS`) |
|---|---|
| `letras` | `letras` |
| `fila` | `fila_completa_letras` |
| `costas` | `numero_costas` |
| `frente` | `numero_frente` |
| `logos` | `logos` |
| `camisa` | `camisa_completa` |

## Decisão pendente

O protótipo não distingue "Letras avulsas" de "Adicionar nome" (várias letras de uma vez). O Montador já faz isso pela
ação de grupo (`allow_group_add`); o site deve usar o mesmo comportamento.
