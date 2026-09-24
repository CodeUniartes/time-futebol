# Identidade visual (Uniartes Uniformes)

Fonte: *Manual de Identidade Visual* (DESIGNAR Propaganda & Design, 2024) e os arquivos em `U:\Logos Uniartes\LOGOS`.
Vale para o site do cliente (SP4 a SP7) e para o Montador. Os tokens finais saem do `/spartan:ux system`; este arquivo é a
base que ele deve respeitar.

## Marca

- **Isotipo:** o "U" que lembra uma camisa de manga curta e longa, com a bolinha laranja (o "i"). Conceito: união,
  rapidez e qualidade.
- **Logotipo:** `UNIARTES` em caixa alta itálica, com `uniformes` em itálico abaixo.
- **Fontes da marca:** Rouge Sans Ext Light It (`UNIARTES`) e Gill Sans SemiBold Italic (`uniformes`). Servem só para o
  logo, que é sempre uma imagem vetorial (nunca redigitar o nome).
- **Arquivo vetorial de origem:** `UNIARTES - LOGO.pdf` (uma página). O site usa uma versão SVG dele; o `.cdr` é o editável.

## Cores

| Papel | Nome | Hex (tela) | CMYK do manual |
|---|---|---|---|
| Destaque | Laranja Uniartes | `#F47726` | C0 M66 Y96 K0 |
| Base | Cinza grafite | `#454849` | C62 M53 Y51 K48 |
| Fundo | Branco | `#FFFFFF` | |

Os hex saíram de amostras das páginas do manual, porque o CMYK convertido à mão dá cores diferentes (o laranja vira
`#FF570A`). Se a gráfica tiver os valores RGB oficiais, eles substituem estes.

### Contraste (regra de acessibilidade)

| Combinação | Razão | Uso |
|---|---|---|
| Branco sobre grafite | 9,2 : 1 | Texto, botão principal |
| Grafite sobre branco | 9,2 : 1 | Texto |
| Branco sobre laranja | **2,8 : 1** | **Não usar em texto nem em botão** |
| Grafite sobre laranja | 3,3 : 1 | Só texto grande e em negrito (>= 18,7 px) |
| Laranja sobre branco | **2,8 : 1** | **Não usar em texto ou link**; só decoração, ícone grande e destaque |
| Branco sobre laranja escuro `#B95A1D` | 4,6 : 1 | Derivado da marca, para botão laranja com texto branco |

Consequência prática: **botão principal = grafite com texto branco e detalhe laranja**. Botão laranja só com o tom escuro
`#B95A1D` (derivado; precisa da sua aprovação, pois não é cor do manual). O laranja puro fica para formas, ícones, o
selo do time e a barra de progresso.

## Aplicação do logo (do manual)

- Versões: colorida (grafite + bolinha laranja), monocromática grafite, monocromática laranja, contorno, e negativa
  (branca) sobre grafite, laranja ou preto. Isotipo sozinho em quadrados preto, laranja e grafite.
- **Fundo grafite:** logo branco, ou branco com bolinha laranja, ou laranja.
- **Fundo laranja:** logo branco, ou grafite com bolinha branca.
- **Redução:** existe versão para tamanhos pequenos; abaixo de cerca de 24 px de altura usar só o isotipo.
- Não distorcer, não recolorir fora das combinações acima, não colocar sobre foto sem contraste.

## Como aplicar aos produtos

| Onde | Como |
|---|---|
| **Site (SP4 a SP7)** | Cabeçalho branco com logo colorido ou grafite com logo branco; ações em grafite; laranja como destaque. A cor de destaque por time (roadmap SP4) vira **secundária**: a marca Uniartes continua no cabeçalho e nos botões |
| **Montador** | Trocar o azul atual (`#0b3970` em `src/ui/theme.py`) por grafite e laranja, logo novo no cabeçalho (hoje `assets/logo_cabecalho.png`) |
| **Mensagens de WhatsApp** | Sem cor; assinar como "Uniartes Uniformes" |

## Pendências da marca

- Confirmar o RGB oficial das duas cores.
- Aprovar o laranja escuro `#B95A1D` para botões.
- Fonte do site: as da marca são pagas; sugestão de fonte web livre parecida com o Gill Sans para o texto (a definir no
  `/spartan:ux system`).
- Escolher qual arquivo do logo entra no repositório (o repositório é público).
