import tatsu 
import struct

nanoc_gr = """
@@grammar::Nanoc

prg = typage 'main' '(' var_list_type ')' '{' commande 'return' '(' expression ')' ';' '}' $ ;

commande = 
        commande commande
        | var '=' expression ';'
        | 'print' '(' expression ')' ';'
        | 'if' '(' expression ')' '{' commande '}'
        | 'while' '(' expression ')' '{' commande '}'
        | typage var '=' expression ';'
        | typage var ';'
        ;

expression = 
            expression op2 expression
            | nombre
            | var 
            | '(' typage ')' expression
            ;

typage =       
            |'int'
            |'float';
            
var = /[a-zA-Z][a-zA-Z0-9]*/ ;

var_list = ",".{ var } ;

var_list_type = ",".{ typage var } ;

int = /[0-9]+/ ;

float = /[0-9]+/ '.' /[0-9]*/;

nombre = 
        | float
        | int
        
        ;

op2 = '+' | '-' | '*' | '<' ;
"""

class Semantics:
    def nombre(self, ast):
        if len(ast)>1 and isinstance(ast, tuple):
            return {'type' : 'nb', 'val' : float("%s.%s" % (ast[0], ast[2]))}
        return {'type' : 'nb', 'val' : int(ast)}

    def var(self, ast):
        return {'type' : 'var', 'val' : ast, 'typage' : None}  # le type de la variable peut etre non-initialise au depart ?

    def expression(self, ast):
        if isinstance(ast, tuple):  # expression op2 expression ; nombre (si c'est un float) ; '(' typage ')' expression
            # premier cas, l'ast represente une operation
            if len(ast) == 3:
                # on verifie que ast[1]!='.' ; pour etre sur qu'on traite une operation et pas un simple float
                if ast[1] != '.':
                    return {'type' : 'op2', 'val' : (ast[0], ast[2]), 'op' : ast[1]}
                # sinon, ast est un float
                return ast
            # deuxieme cas, l'ast represente un cast
            else:
                return {'type' : 'cast', 'val' : ast[3], 'typage' : ast[1]}
        # sinon, on a affaire à un nombre (int) ou une variable
        return ast

    def commande(self, ast):
        # cas : 'print' '(' expression ')' ';'
        if ast[0] == "print":  
            return {'type' : 'print', 'val' : ast[2]}
        # cas : 'if' '(' expression ')' '{' commande '}'    
        elif ast[0] == "if":  
            return {'type' : 'if', 'val' : (ast[2], ast[5])}
        # cas : 'while' '(' expression ')' '{' commande '}'
        elif ast[0] == "while":  
            return {'type' : 'while', 'val' : (ast[2], ast[5])}
        # cas : commande commande
        elif len(ast) == 2: 
            return {'type' : 'seq', 'val' : ast}
        # cas : var '=' expression ';'
        elif ast[1] == '=':  
            return {'type' : '=', 'val' : (ast[0], ast[2])}
        # cas : typage var ';' // declaration sans initialisation
        elif len(ast) == 3:
            ast[1]['typage'] = ast[0]
            return {'type' : 'declaration', 'val' : ast[1]}
        # cas : typage var '=' expression ';' // declaration avec initialisation
        else:
            ast[1]['typage'] = ast[0]
            return {'type' : 'declaInit', 'val' : (ast[1], ast[3])}

    """
    # a priori inutile dans l'implementation de la gestion de types
    def var_list(self, ast):
        return {'type' : 'var_list', 'val' : ast}
    """

    def var_list_type(self, ast):
        for var_type in ast:  # on initialise le type des variables
            var_type[1]['typage'] = var_type[0]
        return {'type' : 'var_list_type', 'val' : ast}

    def prg(self, ast):
        return {'type' : 'prg', 'val' : (ast[0], ast[3], ast[6], ast[9])}

    def _default(self, ast):
        return ast


def pp_e(e):  # sort une chaine correspondant a l'expression e
    if e["type"] == 'var':
        return e["val"]
    elif e["type"] == 'nb':
        return str(e["val"])
    elif e["type"] == "cast":
        return "( %s ) %s" % (e["typage"], pp_e(e["val"]))
    return "(%s) %s (%s)" % (pp_e(e['val'][0]), e["op"], pp_e(e['val'][1]))

def pp_c(c):  # sort une chaine correspondant a la commande c
    if c["type"] == "print":
        return "print(%s);\n" % (pp_e(c['val']))
    elif c["type"] == "if":
        return "if(%s){\n %s }\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    elif c["type"] == "while":
        return "while(%s){\n %s }\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    elif c["type"] == "=":
        return "%s = %s;\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    elif c["type"] == "seq":
        return "%s\n%s" % (pp_c(c['val'][0]), pp_c(c['val'][1]))
    elif c["type"] == "declaration":
        return "%s %s;" % (c["val"]["typage"], pp_e(c["val"]))
    return "%s %s = %s" % (c["val"][0]["typage"], pp_e(c["val"][0]), pp_e(c["val"][1]))

def pp(P):  # sort une representation du programme
    return """%s main(%s){
        %s
        return(%s);
    }""" % (P["val"][0], ", ".join([v[0] + " " + pp_e(v[1]) for v in P["val"][1]["val"]]) , pp_c(P["val"][2]), pp_e(P["val"][3]))


def var_e(e): # sort la liste des variables pour l'expression e (avec leur type)
    if e['type'] == 'var':
        return {(e["typage"], e["val"])}
    elif e['type'] == 'nb':
        return set()
    elif e["type"] == "cast":
        return var_e(e["val"])
    return var_e(e["val"][0]) | var_e(e["val"][1])

def var_c(c): #sort la liste des variables pour la commande c
    if c["type"] == "print":
        return var_e(c['val'])
    elif c["type"] == "if":
        return var_e(c['val'][0]) | var_e(c['val'][1])
    elif c["type"] == "while":
        return var_e(c['val'][0]) | var_e(c['val'][1])
    elif c["type"] == "=":
        return var_e(c['val'][0])| var_e(c['val'][1])
    elif c["type"] == "declaration":
        return var_e(c["val"])
    elif c["type"] == "declaInit":
        return var_e(c['val'][0])| var_e(c['val'][1])
    return var_c(c['val'][0])| var_c(c['val'][1])

def var_p(P): #sort la liste des variables pour le programme P (avec leur type)
    D = set([(X[1]["typage"], X[1]["val"]) for X in P["val"][1]["val"]])
    liste_var = D | var_c(P["val"][2]) | var_e(P["val"][3])
    # on enleve les variables dont le typage est None si elles apparaissent deja dans la liste de variables
    # ATTENTION : s'occuper des variables jamais initialisees en leur attribuant un type par defaut
    liste_var_finale = set()
    for variable in liste_var:
        if variable[0] is not None:
            liste_var_finale.add(variable)
    return liste_var_finale


# ici 

def const_e(e): # sort la liste des constantes de type float pour l'expression e
    if e['type'] == 'var':
        return set()
    elif e['type'] == 'nb':
        if isinstance(e["val"], float):
            return {e["val"]}
        return set()
    elif e["type"] == "cast":
        return const_e(e["val"])
    return const_e(e["val"][0]) | const_e(e["val"][1])

def const_c(c): #sort la liste des constantes de type float pour la commande c
    if c["type"] == "print":
        return const_e(c['val'])
    elif c["type"] == "if":
        return const_e(c['val'][0]) | const_e(c['val'][1])
    elif c["type"] == "while":
        return const_e(c['val'][0]) | const_e(c['val'][1])
    elif c["type"] == "=":
        return const_e(c['val'][0])| const_e(c['val'][1])
    elif c["type"] == "declaration":
        return const_e(c["val"])
    elif c["type"] == "declaInit":
        return const_e(c['val'][0])| const_e(c['val'][1])
    return const_c(c['val'][0])| const_c(c['val'][1])

def const_p(P): #sort la liste des constantes de type float pour le programme P
    return const_c(P["val"][2]) | const_e(P["val"][3])


# Determine le type d'une expression
def type_expr(e, liste_variables):
    if e["type"] == 'nb':
        if isinstance(e["val"], int):
            return "int"
        return "float"
    elif e["type"] == 'var':
        for variable in liste_variables:
            if variable[1] == e["val"]:  # si notre variable est dans la liste des variables, on retourne son type
                return variable[0]
        return "float"  # sinon on lui attribue un type par defaut (ici on choisit float arbitrairement)
    elif e["type"] == "cast":
        return e["typage"]
    else:   # si on a affaire a une expression de type "expression op2 expression"
        type_expr_gauche = type_expr(e["val"][0], liste_variables)
        type_expr_droite = type_expr(e["val"][1], liste_variables)
        if type_expr_gauche == type_expr_droite:
            return type_expr_droite
        return "float"

# Determine le type d'une variable
def type_variable(liste_variables, variable):
    for var in liste_variables:
        if var[1] == variable:  # attention aux variables dont on redefinit le type
            return var[0]
    return "float"  # on  attribue un type par defaut a notre variable si elle n'apparait pas dans la liste des variables (ici on choisit float arbitrairement)


# ATTENTION : les constantes flottantes sont a "initialiser" en debut du fichier asm
asm_op = {"+" : ["add", "addsd"], "-" : ["sub", "subsd"], "*" : ["mul", "mulsd"], "/" : ["div", "divsd"]}
def asm_e(e, liste_variables):
    if e['type'] == 'var':
        if type_variable(liste_variables, e["val"]) == "int":
            return "mov rax, [%s]\n" % e["val"]
        return "movsd xmm0, [%s]\n" % e["val"]
    if e['type'] == 'nb':
        if isinstance(e["val"], int):
            return "mov rax, %s\n" % e["val"]
        return "movsd xmm0, [float_%s_%s]\n" % (str(e["val"]).split(".")[0],str(e["val"]).split(".")[1])
    if e['type'] == 'op2':
        if type_expr(e, liste_variables) == "int":
            res = asm_e(e["val"][1], liste_variables)
            res += "push rax\n"
            res += asm_e(e["val"][0], liste_variables)
            res += "pop rbx\n"
            res += "%s rax, rbx\n" % asm_op[e["op"]][0]
            return res
        else:  # on ne peut operer que sur 2 termes a la fois
            type_expr_gauche = type_expr(e["val"][0], liste_variables)
            type_expr_droite = type_expr(e["val"][1], liste_variables)
            if type_expr_gauche == type_expr_droite:
                res = asm_e(e["val"][1], liste_variables)
                # a modifier ici
                res += "movsd xmm1, xmm0\n"
                res += asm_e(e["val"][0], liste_variables)
                res += "%s xmm0, xmm1\n" % asm_op[e["op"]][1]
                return res
            elif type_expr_gauche == "float":
                res = asm_e(e["val"][1], liste_variables) 
                res += "pxor xmm0, xmm0\n"
                res += "cvtsi2sd xmm0, rax\n"
                # a modifier ici
                res += "movsd xmm1, xmm0\n"
                res += asm_e(e["val"][0], liste_variables)
                res += "%s xmm0, xmm1\n" % asm_op[e["op"]][1]
                return res
            else:
                res = asm_e(e["val"][1], liste_variables)
                # a modifier ici
                res += "movsd xmm1, xmm0\n"
                res += asm_e(e["val"][0], liste_variables)
                res += "pxor xmm0, xmm0\n"
                res += "cvtsi2sd xmm0, rax\n"
                res += "%s xmm0, xmm1\n" % asm_op[e["op"]][1]
                return res
    if e["type"] == "cast":
        if e["typage"] == type_expr(e["val"], liste_variables):
            return asm_e(e["val"], liste_variables)
        else:
            if e["typage"] == "float":
                res = asm_e(e['val'], liste_variables)
                res += "pxor xmm0, xmm0\n"
                res += "cvtsi2sd xmm0, rax\n"
                return res
            else:
                res = asm_e(e['val'], liste_variables)
                res += "xor rax, rax\n"
                res += "cvttsd2si rax, xmm0\n"
                return res

cpt = 0
def asm_c(c, liste_variables):
    global cpt
    if c["type"] == "print":
        if type_expr(c["val"], liste_variables) == "int":
            return """%s 
mov rsi, rax
xor rax, rax
mov rdi, fmt
call printf
""" % asm_e(c["val"], liste_variables)
        else:
            return """%s 
mov rax, 1
mov rdi, fmt_f
call printf
""" % asm_e(c["val"], liste_variables)
    elif c["type"] == "if":
        if type_expr(c["val"][0], liste_variables) == "int":
            res = asm_e(c["val"][0], liste_variables)
            res += "cmp rax, 0\njz end%s\n" % cpt
            x = cpt
            cpt+= 1
            res += asm_c(c["val"][1], liste_variables)
            res += "end%s:\n" % x
            return res
        else:
            res = asm_e(c["val"][0], liste_variables)
            res += "pxor xmm1, xmm1\n"
            res += "ucomisd xmm0, xmm1\njz end%s\n" % cpt
            x = cpt
            cpt+= 1
            res += asm_c(c["val"][1], liste_variables)
            res += "end%s:\n" % x
            return res
    elif c["type"] == "while":
        if type_expr(c["val"][0], liste_variables) == "int":
            res = "start%s: %s" % (cpt, asm_e(c["val"][0], liste_variables))
            y = cpt
            cpt += 1
            res += "cmp rax, 0\njz end%s\n" % cpt
            x = cpt
            cpt+= 1
            res += asm_c(c["val"][1], liste_variables)
            res += "jmp start%s\nend%s:\n" % (y,x)
            return res
        else:
            res = "start%s: %s" % (cpt, asm_e(c["val"][0], liste_variables))
            y = cpt
            cpt += 1
            res += "pxor xmm1, xmm1\n"
            res += "ucomisd xmm0, xmm1\njz end%s\n" % cpt
            x = cpt
            cpt+= 1
            res += asm_c(c["val"][1], liste_variables)
            res += "jmp start%s\nend%s:\n" % (y,x)
            return res
    elif c["type"] == "=":
        if type_expr(c["val"][1], liste_variables) == "int":
            if type_variable(liste_variables, c["val"][0]["val"]) == "int":
                res = asm_e(c["val"][1], liste_variables)
                res += "mov [%s], rax\n" % (c["val"][0]["val"])
                return res
            else:
                res = asm_e(c["val"][1], liste_variables)
                res += "pxor xmm0, xmm0\n"
                res += "cvtsi2sd xmm0, rax\n"
                res += "movsd [%s], xmm0\n" % (c["val"][0]["val"])
                return res
        else:
            if type_variable(liste_variables, c["val"][0]["val"]) == "float":
                res = asm_e(c["val"][1], liste_variables)
                res += "movsd [%s], xmm0\n" % (c["val"][0]["val"])
                return res
            else:
                res = asm_e(c["val"][1], liste_variables)
                res += "xor rax, rax\n"
                res += "cvttsd2si rax, xmm0\n"
                res += "mov [%s], rax\n" % (c["val"][0]["val"])
                return res
    elif c["type"] == "seq":
        return asm_c(c["val"][0], liste_variables) + asm_c(c["val"][1], liste_variables)
    elif c["type"] == "declaration":
        return asm_e(c["val"], liste_variables)
    else:
        if type_variable(liste_variables, c["val"][0]["val"]) == type_expr(c["val"][1], liste_variables):
            if type_variable(liste_variables, c["val"][0]["val"]) == "int":
                res = asm_e(c["val"][1], liste_variables)
                res += "mov [%s], rax\n" % (c["val"][0]["val"])
                return res
            else:
                res = asm_e(c["val"][1], liste_variables)
                res += "movsd [%s], xmm0\n" % (c["val"][0]["val"])
                return res
        else:
            if type_variable(liste_variables, c["val"][0]["val"]) == "int":
                res = asm_e(c["val"][1], liste_variables)
                res += "xor rax, rax\n"
                res += "cvttsd2si rax, xmm0\n"
                res += "mov [%s], rax\n" % (c["val"][0]["val"])
                return res
            else:
                res = asm_e(c["val"][1], liste_variables)
                res += "pxor xmm0, xmm0\n"
                res += "cvtsi2sd xmm0, rax\n"
                res += "movsd [%s], xmm0\n" % (c["val"][0]["val"])
                return res
                


def asm_p(P):
    liste_constantes = const_p(P)
    liste_variables = var_p(P)
    with open("exp_moule.asm") as f:
        moule = f.read()
        moule = moule.replace("RETURN", asm_e(P["val"][3], liste_variables))
        moule = moule.replace("BODY", asm_c(P["val"][2], liste_variables))
        C = ["float_%s_%s : dq %s" % (str(X).split(".")[0],str(X).split(".")[1], float.hex(X)) for X in liste_constantes]
        moule = moule.replace("CONST_DECL", "\n".join(C))
        D = ["%s: dq 0" % X[1] for X in liste_variables]  # X est un tuple (type, variable)
        moule = moule.replace("VAR_DECL", "\n".join(D))
        if type_expr(P["val"][3], liste_variables) == "int":
            retour = """
mov rdi, fmt
mov rsi, rax
xor rax, rax
call printf
add rsp, 16
pop rbp
ret
"""
            moule = moule.replace("AFFICHAGE_RETOUR", retour)
        else:
            retour = """
mov rdi, fmt_f
mov rax, 1
call printf
add rsp, 16
pop rbp
ret
"""
            moule = moule.replace("AFFICHAGE_RETOUR", retour)
        init = ""
        for i in range(len(P["val"][1]["val"])):
            init += "mov rbx, [rbp-16]\n"
            init += "mov rdi, [rbx+%s]\n" % (8*(i+1))
            init += "call atoi\n"
            init += "mov [%s], rax\n" % P["val"][1]['val'][i][1]["val"]
        moule = moule.replace("VAR_INIT", init)
        return moule


a = tatsu.parse(nanoc_gr, """
float main(){
float x = 3.14;
float y = 1.0;
float z = (int) x + y;
return(z);
}
""", semantics=Semantics())

#print(a)
#print(var_p(a))
#print(pp(a))
print(asm_p(a))
