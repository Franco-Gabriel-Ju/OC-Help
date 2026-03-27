import ply.yacc as yacc
from compilador.AnalizadorLexico import tokens  # o donde tengas tus tokens

def p_acciones(p): 
    '''
    acciones : acciones accion
             | accion
    '''
    
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]


def p_accion(p):
    '''accion : ROL F COMMA ACC
              | ROR F COMMA ACC
              | NOT ACC
              | NOT F
              | ACC PLUS ONE ARROW ACC
              | GPR PLUS ONE ARROW GPR
              | ACC ARROW GPR
              | GPR ARROW ACC
              | ACC PLUS GPR ARROW ACC
              | ZERO ARROW ACC
              | ZERO ARROW F
              | GPR LPAREN AD RPAREN ARROW MAR
              | GPR ARROW M
              | M ARROW GPR
              | GPR LPAREN AD RPAREN ARROW OPR
              | PC PLUS ONE ARROW PC
              | PC ARROW MAR
              | GPR LPAREN 
    '''

    # ROL / ROR
    if p.slice[1].type == 'ROL':
        p[0] = ("ROL_F_ACC",)

    elif p.slice[1].type == 'ROR':
        p[0] = ("ROR_F_ACC",)

    # NOT
    elif p.slice[1].type == 'NOT':
        if p.slice[2].type == 'ACC':
            p[0] = ("NOT_ACC",)
        else:
            p[0] = ("NOT_F",)

    # INCREMENTOS
    elif len(p) == 6 and p.slice[2].type == 'PLUS':
        if p.slice[1].type == 'ACC':
            p[0] = ("INC_ACC",)
        else:
            p[0] = ("INC_GPR",)

    # SUMA ACC + GPR → ACC
    elif len(p) == 6 and p.slice[2].type != 'PLUS':
        p[0] = ("SUM_ACC_GPR",)

    # TRANSFERENCIAS simples (ACC ↔ GPR)
    elif len(p) == 4 and p.slice[2].type == 'ARROW':
        if p.slice[1].type == 'ACC':
            p[0] = ("ACC_TO_GPR",)
        else:
            p[0] = ("GPR_TO_ACC",)

    # ZERO → ACC / F
    elif p.slice[1].type == 'ZERO':
        if p.slice[3].type == 'ACC':
            p[0] = ("ZERO_ACC",)
        else:
            p[0] = ("ZERO_F",)

    # GPR (AD) → MAR
    elif p.slice[1].type == 'GPR' and p.slice[3].type == 'AD':
        p[0] = ("GPR_AD_TO_MAR",)

    # GPR → M
    elif p.slice[1].type == 'GPR' and p.slice[3].type == 'M':
        p[0] = ("GPR_TO_M",)

    # M → GPR
    elif p.slice[1].type == 'M':
        p[0] = ("M_TO_GPR",)


def p_error(p):
    if p:
        print(f"Error de sintaxis en '{p.value}'")
    else:
        print("Error de sintaxis al final del input") 

parser = yacc.yacc()