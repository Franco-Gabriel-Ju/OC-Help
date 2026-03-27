import ply.yacc as yacc
from compilador.AnalizadorLexico import tokens

def p_acciones(p):
    '''acciones : acciones accion
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
              | ACC NOT ARROW ACC
              | ZERO ARROW ACC
              | ZERO ARROW F
              | ACC PLUS ONE ARROW ACC
              | GPR PLUS ONE ARROW GPR
              | ACC PLUS GPR ARROW ACC
              | GPR PLUS ACC ARROW ACC
              | ACC ARROW GPR
              | GPR ARROW ACC
              | GPR ARROW M
              | M ARROW GPR
              | GPR LPAREN AD RPAREN ARROW MAR
              | GPR LPAREN AD RPAREN ARROW OPR
              | PC PLUS ONE ARROW PC
              | PC ARROW MAR
    '''

    t1 = p.slice[1].type

    # ROL / ROR
    if t1 == 'ROL':
        p[0] = ("ROL_F_ACC",)

    elif t1 == 'ROR':
        p[0] = ("ROR_F_ACC",)

    # NOT prefijo: ! ACC  |  ! F
    elif t1 == 'NOT':
        if p.slice[2].type == 'ACC':
            p[0] = ("NOT_ACC",)
        else:
            p[0] = ("NOT_F",)

    # NOT sufijo: ACC! -> ACC
    elif t1 == 'ACC' and len(p) == 5 and p.slice[2].type == 'NOT':
        p[0] = ("NOT_ACC",)

    # ZERO → ACC / F  (antes que transferencias simples)
    elif t1 == 'ZERO':
        if p.slice[3].type == 'ACC':
            p[0] = ("ZERO_ACC",)
        else:
            p[0] = ("ZERO_F",)

    # INCREMENTOS: ACC+1 -> ACC  |  GPR+1 -> GPR
    elif len(p) == 6 and p.slice[3].type == 'ONE':
        if t1 == 'ACC':
            p[0] = ("INC_ACC",)
        else:
            p[0] = ("INC_GPR",)

    # SUMA: ACC+GPR -> ACC  |  GPR+ACC -> ACC
    elif len(p) == 6 and p.slice[3].type in ('GPR', 'ACC'):
        p[0] = ("SUM_ACC_GPR",)

    # TRANSFERENCIAS simples: X -> Y
    elif len(p) == 4 and p.slice[2].type == 'ARROW':
        if t1 == 'ACC':
            p[0] = ("ACC_TO_GPR",)
        elif t1 == 'GPR' and p.slice[3].type == 'ACC':
            p[0] = ("GPR_TO_ACC",)
        elif t1 == 'GPR' and p.slice[3].type == 'M':
            p[0] = ("GPR_TO_M",)
        elif t1 == 'M':
            p[0] = ("M_TO_GPR",)

    # PC → MAR
    elif t1 == 'PC' and len(p) == 4 and p.slice[3].type == 'MAR':
        p[0] = ("PC_TO_MAR",)

    # PC+1 → PC
    elif t1 == 'PC' and len(p) == 6:
        p[0] = ("INC_PC",)

    # GPR(AD) → MAR / OPR
    elif t1 == 'GPR' and len(p) > 3 and p.slice[3].type == 'AD':
        if p.slice[6].type == 'OPR':
            p[0] = ("GPR_OP_TO_OPR",)
        else:
            p[0] = ("GPR_AD_TO_MAR",)


def p_error(p):
    if p:
        print(f"  [Sintaxis] Línea {p.lineno}: token inesperado '{p.value}' (tipo: {p.type})")
        print(f"  Instrucciones válidas:")
        print(f"    ROL F,ACC  |  ROR F,ACC")
        print(f"    ! ACC  |  ! F  |  ACC! -> ACC")
        print(f"    0 -> ACC  |  0 -> F")
        print(f"    ACC+1 -> ACC  |  GPR+1 -> GPR")
        print(f"    ACC+GPR -> ACC  |  GPR+ACC -> ACC")
        print(f"    ACC -> GPR  |  GPR -> ACC")
        print(f"    GPR -> M  |  M -> GPR")
        print(f"    GPR(AD) -> MAR")
    else:
        print("  [Sintaxis] Error al final del programa (instrucción incompleta)")


parser = yacc.yacc()
