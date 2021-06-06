extern printf, atoi, atof
global main
section .data
fmt: db "%d", 10, 0
fmt_f: db "%f", 10, 0
CONST_DECL
VAR_DECL

section .text
main:
    push rbp
    mov rbp, rsp
    push rdi
    push rsi

VAR_INIT

BODY

RETURN

    AFFICHAGE_RETOUR

