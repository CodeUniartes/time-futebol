# Publicar catálogo (sub-projeto 2)

Data: 2026-09-24 · Status: rascunho para revisão · Tamanho estimado: M (~1,5 a 2 dias) · Depende de: SP1 (pronto)

## Contexto

O site precisa mostrar ao cliente o catálogo (times, camisas, letras, números, logos) sem ter acesso aos `.tif` de
produção, que **nunca saem do PC**. O Montador gera o **catálogo público** (`catalog.public.json`) e **prévias leves**
(`.webp`) a partir das pastas cadastradas em Configurações. A visão geral está em [`docs/roadmap.md`](../../roadmap.md); os
formatos, em [`contracts/`](../../../contracts/); a marca, em [`docs/brand.md`](../../brand.md).

## Divisão em duas etapas

O envio depende dos endpoints do Worker (SP3), que ainda não existem. Para não travar, o sub-projeto tem duas etapas:

| Etapa | Entrega | Depende de |
|---|---|---|
| **2A: gerar** | Botão **Publicar Catálogo** que gera, numa pasta local, o `catalog.public.json` e as prévias `.webp`, com relatório | SP1 |
| **2B: enviar** | Envia a pasta gerada ao R2 pelos endpoints do Worker e mostra o resultado | 2A e SP3 |

Este documento detalha a **2A** (a parte grande e arriscada) e descreve a 2B em alto nível.

## Objetivo e critério de sucesso (2A)

O dono clica em **Publicar Catálogo**; o Montador percorre as camisas ativas, lê os `.tif`, e produz em
`publish/` um `catalog.public.json` válido no contrato e uma prévia `.webp` por item, cada uma recortada na área com
tinta e com marca d'água. Rodar de novo só reprocessa o que mudou. Arquivos ilegíveis aparecem num relatório, sem
interromper o resto. Com o catálogo real (505 `.tif`), a primeira geração termina em poucos minutos.

## Decisões

| Tema | Decisão |
|---|---|
| Leitura do `.tif` | `tifffile` + `imagecodecs` (leem CMYK com alfa de 5 e 6 canais e RGB com alfa). O Pillow só redimensiona e grava `.webp` |
| Cor | CMYK convertido para RGB por fórmula simples; se o arquivo tiver perfil ICC, usa o perfil (via `ImageCms`) |
| Transparência | Mantida: a prévia é `.webp` com alfa, e a marca d'água entra por cima |
| Área útil | Retângulo que contém tudo com alfa acima de um limiar (8 de 255); margem transparente é descartada |
| Tamanho físico | `largura_px ÷ dpi × 2,54` e `altura_px ÷ dpi × 2,54` sobre a área útil, arredondado a 0,1 cm. Sem dpi gravado: assume 300 e registra aviso |
| Prévia | Lado maior de 400 px, `.webp`, qualidade 80, sem ampliar arte menor que isso |
| Marca d'água | Texto repetido na diagonal, cinza, baixa opacidade, só na prévia. Texto, opacidade e ângulo em `config/site.json` (padrão: `UNIARTES`) |
| Filtros | Só camisas `active`, categorias `enabled` com pasta existente, itens vindos de `list_available_items` |
| `catalog_version` | O `updated_at` do catálogo (SP1). Se ainda não existir, grava o catálogo uma vez antes |
| Falha em um arquivo | O item é omitido, entra no relatório com o motivo e o resto continua |
| Segredos | Nada de token na 2A; `config/site.json` continua ignorado pelo git |

## Item "Todos os arquivos"

Categorias como camisa completa (e fila/logos com `quick_action_all_files`) copiam **a pasta inteira**. O painel do SP5
precisa das medidas de **cada** arquivo, não de um só. Por isso o contrato ganha um campo **opcional** no item:

```json
{ "label": "Todos os arquivos", "preview": "previews/.../todos.webp",
  "pieces": [ { "width_cm": 48.0, "height_cm": 58.0 }, { "width_cm": 12.0, "height_cm": 6.0 } ] }
```

- `width_cm`/`height_cm` do item ficam ausentes nesse caso; quem lê usa `pieces`. Mesma `schema_version` (campo opcional).
- A prévia desse item é uma **colagem em grade** das peças, com no máximo 400 px de lado maior.

## Formato de saída

```
publish/
  catalog.public.json
  previews/<time>/<camisa>/<categoria>/<item>.webp
  .cache.json            (não publicado: hashes e medidas já calculados)
  relatorio.txt          (avisos e falhas da última geração)
```

- Nomes de pasta e arquivo com `slugify`; rótulo com caracteres inválidos vira nome seguro (`A/B` → `a_b`), único por
  categoria (colisão recebe sufixo `_2`). O `label` no JSON continua o original, porque é o `item_label` do pedido.
- `publish/` fica fora do git (adicionar ao `.gitignore`).

## Cache

Chave por arquivo de origem: caminho, tamanho, data de modificação, dpi e a configuração da marca d'água (mais a versão do
gerador). Se a chave não mudou, reaproveita a prévia e as medidas do `.cache.json`. Prévias de arquivos que saíram do
catálogo são apagadas da pasta de saída.

## Componentes

| Arquivo | Papel |
|---|---|
| `src/utils/tiff_reader.py` (novo) | Lê o `.tif`: canais, cor, alfa, dpi; devolve RGBA + dpi. Sem Tk |
| `src/utils/preview_image.py` (novo) | Área útil, redimensionar, marca d'água, colagem, gravar `.webp` |
| `src/services/site_config_service.py` (novo) | Lê `config/site.json` com padrões (marca d'água) |
| `src/services/publish_service.py` (novo) | Percorre o catálogo, aplica filtros e cache, monta o `catalog.public.json`, gera o relatório |
| `src/ui/publish_window.py` (novo) | Janela: iniciar, barra de progresso, cancelar, ver relatório, abrir a pasta |
| `src/ui/main_window.py` | Botão **Publicar Catálogo** (ou item em Configurações) |
| `contracts/catalog.public.schema.json`, `.example.json`, `README.md` | Campo opcional `pieces` |
| `requirements.txt`, `.gitignore`, `build_exe.bat` | Novas dependências, `publish/`, empacotamento |

A janela roda a geração numa **thread**, com fila de mensagens para a interface (o Tk não pode ser tocado de outra
thread) e botão de cancelar. Toda a lógica fica em `services/` e `utils/`, testável sem Tk.

## Etapa 2B: enviar (resumo)

- `POST /api/admin/publish` com o manifesto e o `catalog_version`, e `POST /api/admin/preview?key=` por arquivo novo ou
  alterado, com o token de administrador de `config/site.json`. Só envia o que mudou (compara com o manifesto do servidor).
- O Worker grava o JSON e as prévias no R2 (SP3). Se o envio falhar no meio, o `catalog.public.json` só é trocado no fim,
  para o site nunca ver um catálogo apontando para prévia inexistente.

## Testes (escritos antes do código)

- **Leitura:** TIFFs sintéticos criados com `tifffile` para RGB, RGB+alfa, CMYK+alfa (5 e 6 canais), 16 bits, sem dpi, dpi em
  cm e em polegadas, 300 e 400 dpi. Todos devem ler; arquivo corrompido levanta erro tratado.
- **Área útil e medidas:** margem transparente é cortada; largura/altura em cm corretas (ex.: 300 dpi → 1 cm = 118,1 px);
  imagem 100% transparente não quebra.
- **Prévia:** lado maior <= 400 px, proporção igual à do retângulo em cm, marca d'água altera pixels, arte pequena não é
  ampliada, formato `.webp` com alfa.
- **Filtros:** camisa inativa e categoria desabilitada ou sem pasta não aparecem; item ilegível vai para o relatório.
- **JSON:** o `catalog.public.json` gerado passa no `catalog.public.schema.json`; `catalog_version` = `updated_at`;
  categorias de todos os arquivos usam `ALL_FILES_LABEL` e `pieces`.
- **Cache:** segunda execução não reprocessa; mudar o arquivo ou a marca d'água reprocessa só o afetado; item removido
  apaga a prévia.
- **Nomes:** rótulos com caracteres inválidos ou repetidos geram caminhos únicos e seguros.
- **Interface:** verificação manual (barra de progresso, cancelar, relatório).

## Riscos e pontos em aberto

1. **Cores de letras e números em subpastas.** No catálogo real, letras do Cruzeiro estão em `AZUL`, `BRANCO`, `MARROM`, e
   o Montador hoje lê **uma pasta por categoria**, sem subpastas. O site precisa oferecer a **cor** da letra. Decisão
   necessária: cada cor vira uma categoria própria ("Letras — Azul") ou o modelo ganha o conceito de *variante de cor*.
   Recomendo a segunda, mas é uma mudança de modelo que merece spec própria antes da 2A publicar esses casos.
2. **Nomes de arquivo** como `JOSÉ SOARES.tif` na pasta de números (arte de nome) não casam com a regra de dígitos e ficam
   de fora da categoria; hoje já é assim no Montador.
3. **Fidelidade de cor** da prévia (CMYK convertido) é aproximada: o texto do site deve dizer "prévia ilustrativa".
4. **Tamanho do executável:** `numpy` e `imagecodecs` aumentam o `.exe`; medir e ajustar `build_exe.bat`.
5. **Tempo:** 505 arquivos leram em ~113 s no teste; com prévia, marca d'água e escrita, esperar de 3 a 6 minutos na
   primeira geração e segundos nas seguintes (cache).
6. **Marca d'água legível e discreta** em artes muito pequenas (letras de 5 cm); ajustar tamanho da fonte à prévia.
7. **Repositório público:** `publish/` e `config/site.json` ficam fora do git; as prévias nunca são commitadas.

## Fora do escopo

Envio ao R2 e endpoints (2B/SP3), o site, o painel de encaixe (SP5), marca d'água por time, ICC completo com gestão de cor,
edição das prévias e geração de PDF.

## Ordem de entrega

1. Contrato: campo `pieces` + testes.
2. `tiff_reader` + testes com TIFFs sintéticos.
3. `preview_image` (área útil, tamanho em cm, redução, marca d'água, colagem) + testes.
4. `site_config_service`.
5. `publish_service` (filtros, cache, JSON, relatório) + testes.
6. Janela e botão; dependências e `.gitignore`.
7. Teste com 5 arquivos reais e depois o catálogo completo; medir o `.exe`.
