| Atributo BD       | Atributo CSV              | Título UI (atual)    |
|-------------------|---------------------------|----------------------|
| id                | -                         | ID                   |
| layout_name       | TAG DO LAYOUT / LAYOUT    | Layout               |
| dwg_name          | (interno - igual dwg_source) | -                 |
| proj_num          | PROJ_NUM                  | Proj Nº              |
| proj_nome         | PROJ_NOME                 | Projeto              |
| dwg_source        | NOME DWG / DWG_SOURCE     | DWG_SOURCE           |
| fase              | FASE                      | -                    |
| fase_pfix         | FASE_PFIX                 | -                    |
| emissao           | EMISSAO / EMISSÃO         | -                    |
| data              | DATA / DATA 1ª EMISSÃO    | -                    |
| escalas           | -                         | -                    |
| pfix              | PFIX                      | Prefixo              |
| tipo_display      | TIPO                      | Tipo                 |
| tipo_key          | (derivado de TIPO)        | -                    |
| elemento          | ELEMENTO                  | Elemento             |
| titulo            | TITULO / TÍTULO           | Título               |
| elemento_titulo   | (derivado)                | -                    |
| elemento_key      | (derivado de ELEMENTO)    | -                    |
| des_num           | NUMERO DE DESENHO / DES_NUM | Nº Desenho         |
| r                 | (última revisão)          | Rev                  |
| r_data            | (data última revisão)     | Data Rev             |
| r_desc            | (desc última revisão)     | -                    |
| id_cad            | ID_CAD                    | -                    |
| raw_attributes    | (JSON completo)           | -                    |
| estado_interno    | -                         | Estado               |
| comentario        | -                         | Comentário           |
| data_limite       | -                         | Data Limite          |
| responsavel       | -                         | Responsável          |
| created_at        | -                         | -                    |
| updated_at        | -                         | -                    |
| cliente           | CLIENTE (via projetos)    | -                    |
| obra              | OBRA (via projetos)       | -                    |
| localizacao       | LOCALIZAÇÃO (via projetos)| -                    |
| especialidade     | ESPECIALIDADE (via projetos) | -                 |
| projetou          | PROJETOU (via projetos)   | -                    |


| Atributo BD       | Atributo CSV              | Título UI            |
|-------------------|---------------------------|----------------------|
| rev_code          | REVISÃO A/B/C/D/E         | -                    |
| rev_date          | DATA REVISAO A/B/C/D/E    | -                    |
| rev_desc          | DESCRIÇÃO REVISÃO A/B/C/D/E | -                  |