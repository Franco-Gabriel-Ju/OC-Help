import ply.lex as lex
import re

# Lista de tokens
tokens = (
    'ACC',
    'AD',
    'PC',
    'OP',
    'OPR',
    'GPR',
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
t_MAR = r'MAR'
t_M = r'M'
t_ROL = r'ROL'
t_ROR = r'ROR'
t_F = r'F'
t_AD = r'AD'
t_OP = r'OP'
t_PC = r'PC'
t_OPR = r'OPR'

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


