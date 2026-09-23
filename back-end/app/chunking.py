def dividir_em_chunks(texto: str, tamanho: int = 800, sobreposicao: int = 100) -> list[str]:
    texto = texto.strip()
    if len(texto) <= tamanho:
        return [texto]

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        chunks.append(texto[inicio:fim].strip())
        inicio += tamanho - sobreposicao

    return [c for c in chunks if c]
