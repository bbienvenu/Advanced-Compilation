# Advanced Compilation - DepInfo - FICM 2A

  
<p align="justify">
  
  ## Compilateur nanoc : gestion statique de types
  
</p>

L’objectif du projet est d’écrire un programme implémentant la gestion statique de types pour notre compilateur nanoc. En particulier, notre implémentation doit prendre en compte la déclatation des variables (et du ```main```) ainsi que les conversions implicites et explicites des expressions avec les types ```int``` et ```float``` (en réalité ```long``` et ```double```).

On rappelle que l'implémentation est faite en python et on utilise le module ```tatsu```.

### Utilisation

- Fichier "d'entrée" :

1. ```exp_nanoc.py``` : le code python dans lequel figurent toutes les fonctions de compilation.

Le code nanoc à compiler doit être inscrit dans ce fichier à la ligne 494.

Exemple :

```
a = tatsu.parse(nanoc_gr, """
int main(float x, int y){
float a;
int z = 0;
float b = (int) a + 1.0;
if (a) {
    z = x + y;
}
print(b);
return(z);
}
""", semantics=Semantics())
```

2. ```exp_moule.asm```


### Problèmes et particularités

- Problème de priorité si on applique des opérateurs différents dans un même calcul. 

Exemple : ```int z = 3 - 2 + 1``` renvoie 0 au lieu de 2.
Une solution serait de parenthéser nos expressions pour intégrer les priorités dans les opérations et les effectuer dans le bon sens. Mais faute de temps, nous n'avons pas pu l'implémenter.

- La division et la comparaison ne sont pas implémentées mais les instructions restent similaires à celles des autres opérations (```*, +, -```).
  
- Les variables déclarées mais non initialisées sont par défaut mises à 0 dans le programme.
