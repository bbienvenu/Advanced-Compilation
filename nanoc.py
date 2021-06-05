import tatsu 

nanoc_gr = """
@@grammar::Nanoc

prg = 'main' '(' var_list ')' '{' commande 'return' '(' expression ')' ';' '}' $ ;

commande = 
        commande commande
        | var '=' expression ';'
        | 'print' '(' expression ')' ';'
        | 'if' '(' expression ')' '{' commande '}'
        | 'while' '(' expression ')' '{' commande '}'
        ;

expression = 
            expression op2 expression
            | nombre
            | var ;
            
var = /[a-zA-Z][a-zA-Z0-9]*/ ;

var_list = ",".{ var } ;

nombre = /[0-9]+/ ;

op2 = '+' | '-' | '*' | '<' ;
"""

class Semantics:
    def nombre(self, ast):
        return {'type' : 'nb', 'val' : int(ast)}
    def var(self, ast):
        return {'type' : 'var', 'val' : ast}
    def expression(self, ast):
        if isinstance(ast, tuple):
            return {'type' : 'op2', 'val' : (ast[0], ast[2]), 'op' : ast[1]}
        return ast
    def commande(self, ast):
        if ast[0] == "print":
            return {'type' : 'print', 'val' : ast[2]}
        elif ast[0] == "if":
            return {'type' : 'if', 'val' : (ast[2], ast[5])}
        elif ast[0] == "while":
            return {'type' : 'while', 'val' : (ast[2], ast[5])}
        elif len(ast) == 2:
            return {'type' : 'seq', 'val' : ast}
        else:
            return {'type' : '=', 'val' : (ast[0], ast[2])}
    def var_list(self, ast):
        return {'type' : 'var_list', 'val' : ast}
    def prg(self, ast):
        return {'type' : 'prg', 'val' : (ast[2], ast[5], ast[8])}

    def _default(self, ast):
        return ast


def pp_e(e):#sort une chaine correspondant a l'expression e
    if e['type'] == 'var':
        return e["val"]
    if e['type'] == 'nb':
        return str(e["val"])
    return "(%s) %s (%s)" % (pp_e(e['val'][0]), e["op"], pp_e(e['val'][1]))

def pp_c(c):#sort une chaine correspondant a la commande c
    if c["type"] == "print":
        return "print(%s);\n" % (pp_e(c['val']))
    elif c["type"] == "if":
        return "if(%s){\n %s }\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    elif c["type"] == "while":
        return "while(%s){\n %s }\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    elif c["type"] == "=":
        return "%s = %s;\n" % (pp_e(c['val'][0]), pp_e(c['val'][1]))
    return "%s\n%s" % (pp_c(c['val'][0]), pp_c(c['val'][1]))

def pp(P):#sort une representation du programme
    return """main(%s){
        %s
        return(%s);
    }""" % (", ".join([pp_e(v) for v in P["val"][0]["val"]]) , pp_c(P["val"][1]), pp_e(P["val"][2]))


def var_e(e): #sort la liste des variables pour l'expression e
    if e['type'] == 'var':
        return {e["val"]}
    if e['type'] == 'nb':
        return set()
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
    return var_c(c['val'][0])| var_c(c['val'][1])

def var_p(P):
    D = set([X["val"] for X in P["val"][0]["val"]])
    return D | var_c(P["val"][1]) | var_e(P["val"][2])


asm_op = {"+" : "add", "-" : "sub", "*" : "mul", "/" : "div"}
def asm_e(e):
    if e['type'] == 'var':
        return "mov rax, [%s]\n" % e["val"]
    if e['type'] == 'nb':
        return "mov rax, %s\n" % e["val"]
    else:
        res = asm_e(e["val"][1])
        res += "push rax\n"
        res += asm_e(e["val"][0])
        res += "pop rbx\n"
        res += "%s rax, rbx\n" % asm_op[e["op"]]
        return res

cpt = 0
def asm_c(c):
    global cpt
    if c["type"] == "print":
        return """%s 
mov rsi, rax
xor rax, rax
mov rdi, fmt
call printf
""" % asm_e(c["val"])
    elif c["type"] == "if":
        res = asm_e(c["val"][0])
        res += "cmp rax, 0\njz end%s\n" % cpt
        x = cpt
        cpt+= 1
        res += asm_c(c["val"][1])
        res += "end%s:\n" % x
        return res
    elif c["type"] == "while":
        res = "start%s: %s" % (cpt, asm_e(c["val"][0]))
        y = cpt
        cpt += 1
        res += "cmp rax, 0\njz end%s\n" % cpt
        x = cpt
        cpt+= 1
        res += asm_c(c["val"][1])
        res += "jmp start%s\nend%s:\n" % (y,x)
        return res
    elif c["type"] == "=":
        res = asm_e(c["val"][1])
        res += "mov [%s], rax\n" % (c["val"][0]["val"])
        return res
    else:
        return asm_c(c["val"][0]) + asm_c(c["val"][1])

def asm_p(P):
    with open("moule.asm") as f:
        moule = f.read()
        moule = moule.replace("RETURN", asm_e(P["val"][2]))
        moule = moule.replace("BODY", asm_c(P["val"][1]))
        D = ["%s: dq 0" % X for X in var_p(P)]
        moule = moule.replace("VAR_DECL", "\n".join(D))
        init = ""
        for i in range(len(P["val"][0]["val"])):
            init += "mov rbx, [rbp-16]\n"
            init += "mov rdi, [rbx+%s]\n" % (8*(i+1))
            init += "call atoi\n"
            init += "mov [%s], rax\n" % P["val"][0]['val'][i]["val"]
        moule = moule.replace("VAR_INIT", init)
        return moule


a = tatsu.parse(nanoc_gr, "main(x, y, z){x = y ; return(z+1);}", semantics=Semantics())
#print(a)
print(asm_p(a))
