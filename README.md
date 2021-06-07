Auteur : Bienvenu Bambi - Étudiant FICM2A - Département GIMA-ISDP/Info

# Advanced Compilation


## Compilateur nanoc : gestion statique de types
  
L’objectif du projet est d’écrire un programme implémentant la gestion statique de types pour notre compilateur nanoc. En particulier, notre implémentation doit prendre en compte la déclatation des variables (et de la fonction ```main```) ainsi que les conversions implicites et explicites des expressions avec les types ```int``` et ```float``` (en réalité ```long``` et ```double```).

On rappelle que l'implémentation est faite en python et on utilise le module ```tatsu```.


## Fichiers et utilisation

### Fichiers fournis

1. ```exp_nanoc.py``` : le fichier python dans lequel figurent toutes les fonctions utiles à la compilation (en plus de la définition de la grammaire utilisée).

Le code nanoc à compiler doit être inscrit dans ce fichier à la ligne ```566```.

Exemple :

```python
a = tatsu.parse(nanoc_gr, """
int main(float x, int y){
float a = 2.5;
int z = 0;
float b = a + 1.0;
if (a) {
    z = x + y;
}
print(b);
return(z);
}
""", semantics=Semantics())

print(asm_p(a))
```

2. ```exp_moule.asm``` : le fichier asm qui va servir de "moule" (modèle) pour construire notre code assembleur. 

Les sections ```CONST_DECL```, ```VAR_DECL```, ```VAR_INIT```, ```BODY```, ```RETURN``` et ```AFFICHAGE_RETOUR``` vont être modifiées dans ```exp_nanoc.py``` selon le code nanoc à compiler.

3. ```compilateur.sh``` : il s'agit du fichier qui regroupe la suite de commandes à exécuter pour compiler un programme :

```sh
#!/bin/sh
# chmod +x compilateur.sh

python_file=exp_nanoc.py
out_file=exp_test.asm
object_file=exp_test.o  # This must be the out_file with a .O extanesion
python3 $python_file > $out_file
nasm -felf64 $out_file
gcc -no-pie $object_file
```

Ainsi, il suffira de l'exécuter via la commande ```./compilateur.sh``` dans un terminal pour avoir le fichier ```a.out```, résultat de la compilation de notre programme.


### Dépendances et utilisation :

- Utilisation :

Pour compiler un programme il faut avant tout l'écrire dans le fichier ```exp_nanoc.py``` (ligne 566). Ensuite, il suffit d'exécuter ```./compilateur.sh``` pour avoir le fichier de sortie ```a.out```.

- Dépendances :

  - Le module ```tatsu``` de python, qu'on peut installer avec la commande : ```pip install tatsu```
  - Le package ```nasm```, qu'on peut installer sur Ubuntu 20.04 avec les commandes :

```bash
sudo apt-get update -y
```
```bash
sudo apt-get install -y nasm
```


### Problèmes et particularités notés

- Problème de priorité si on applique des opérateurs différents dans un même calcul. 

Exemple : 
```C
int main(){
    int z = 3 - 2 + 1;
    return(z);
}
``` 
Le code ci-dessus retourne 0 au lieu de 2.

Une solution serait de parenthéser nos expressions pour intégrer les priorités dans les opérations et les effectuer dans le bon sens. Mais faute de temps, nous n'avons pas pu l'implémenter.

- La division et la comparaison ne sont pas encore implémentées mais les instructions restent (a priori) similaires à celles des autres opérations (```*, +, -```).

- Les variables déclarées mais non initialisées sont par défaut mises à 0 dans le programme.

Exemple :
```C
float main(){
    float a;
    float b = (int) a + 1.0;
    return(b);
}
```
Le code ci-dessus va retourner ```1.000000```.
