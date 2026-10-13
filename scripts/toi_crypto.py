"""Decodificador de ModExcel do Tale of Immortal.

Arquivos .json exportados com a opção excelEncrypt têm um marcador de 21 bytes
e o conteúdo é cifrado com soma modular usando a senha de mods do jogo.
É uma codificação reversível, NÃO criptografia moderna.

Algoritmo descrito em:
https://github.com/nozwock/tale-of-immortal-tool/blob/main/src/EncryptTool.cs
O decodificador opera somente em memória; não altera arquivos originais.
"""

VALIDATION_KEY = b"2a;ad.,&fSf^SX.,:12@D"
MOD_KEY = b",.?<aH.5:.L;_=-A%K/DF4s"
MAGIC = bytes(b ^ 3 for b in VALIDATION_KEY)


def is_mod_encrypted(data: bytes) -> bool:
    return data.startswith(MAGIC)


def decode_mod_file(data: bytes) -> bytes:
    """Devolve plaintext intacto ou decifra somente o formato identificado."""
    if not is_mod_encrypted(data):
        return data
    content = data[len(MAGIC):]
    return bytes((byte - MOD_KEY[index % len(MOD_KEY)]) & 0xff
                 for index, byte in enumerate(content))


def encode_mod_file_for_test(data: bytes) -> bytes:
    """Usada exclusivamente em testes de regressão. Nunca sobrescreve mods."""
    return MAGIC + bytes((byte + MOD_KEY[index % len(MOD_KEY)]) & 0xff
                         for index, byte in enumerate(data))
