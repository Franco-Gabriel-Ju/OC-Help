import ply.lex as lex
import re

# Lista de tokens
tokens = (
    'ACC',
    'GPR',
    'RAM',
    'MAR',
    'M',
    'ROL',
    'ROR',
    'F',
    'NOT',
    'COMMA',
    'LPAREN',
    'RPAREN',
    'ONE',
    'PLUS',
    'ARROW',
    'ZERO'
)

# Palabras clave
t_ACC = r'ACC'
t_GPR = r'GPR'
t_RAM = r'RAM'
t_MAR = r'MAR'
t_M = r'M'
t_ROL = r'ROL'
t_ROR = r'ROR'
t_F = r'F'

# Símbolos
t_NOT = r'!'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ONE = r'1'
t_ZERO= r'0'
t_PLUS = r'\+'
t_ARROW = r'->|:=|:'

# Ignorar espacios y tabs
t_ignore = ' \t'

# Manejar saltos de línea (para vacío)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error léxico
def t_error(t):
    print("Caracter ilegal:", t.value[0])
    t.lexer.skip(1)


lexer = lex.lex(reflags=re.IGNORECASE)


