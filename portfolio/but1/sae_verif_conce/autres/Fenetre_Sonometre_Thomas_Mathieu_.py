# Crée par Thomas Lominé et Mathieu Dugué, le 19/01/2024 en Python

#-------------------------------------------------------------------------------------------------------------#
#- programme pour fair une sonometre python qui va afficher un interface avec un niveau de son sous forme de -#
#- vumètre de "LED"                                                                                          -#
#-------------------------------------------------------------------------------------------------------------#


################################################################################################################################################################################


from random import randint  # Pour générer des valeurs aléatoires
import serial.tools.list_ports as prtlst  # Pour obtenir la liste des ports série disponibles
import tkinter as tk  # Pour créer l'interface graphique
import serial  # Pour la communication série
import math  # Pour les opérations mathématiques

#fonction pour fermer la fenetre du sonometre
def detruire_sonometre():
        sonometre.destroy()
        print("sonometre fermée")

# Création de la fenêtre principale
sonometre = tk.Tk()#creration de la fenetre du sonometre
sonometre.geometry("550x500")#taille de la fenetre du sonometre (je sais pas si c'est la bonne, faut surement la changer)
sonometre.resizable(width=False, height=False)#empeche le redimentionnement de la fenetre du sonometre
sonometre.configure(bg="gray") #change la couleur de fond de la fenetre du sonometre
sonometre.protocol("WM_DELETE_WINDOW", detruire_sonometre)#action effectue quand on clique sur fermer la fenetre du sonometre
sonometre.title("Sonomètre") #change le titre de la fenetre
print("sonometre ouverte")


################################################################################################################################################################################


bool_mode_fonctionnement = False  # Indique si le programme est en mode test (True) ou si la carte est en fonctionnement (False)
int_decibel_max = 0  # Stocke la valeur maximale des décibels enregistrée jusqu'à présent
int_moyenne_decibel = 0  # Stocke la moyenne des valeurs de décibels enregistrées
int_decibel = 0  # Stocke la dernière valeur de décibels mesurée
int_mode_fonctionnement = 0  # Indique le mode de fonctionnement actuel (0, 1, 2 ou 3)
bool_mode_fonctionnement_etat = True  # Indique si le mode de fonctionnement est actif (True) ou non (False)
int_compteur_nombre_test = 0  # Compte le nombre de tests effectués en mode test
int_somme_db = 0  # Stocke la somme des valeurs de décibels pour le calcul de la moyenne
int_somme_db2 = 0  # Stocke une deuxième somme des valeurs de décibels pour un autre calcul de la moyenne
bool_etat_changer_etat_on_off = True  # Indique si le programme est actif (True) ou désactivé (False)
dernier_decibel = 50  # Stocke la dernière valeur de décibels mesurée
compteur_erreur = 0  # Compte le nombre d'erreurs survenues lors de la communication série
int_var1 = 0  # Variable de contrôle utilisée dans certaines parties du code
int_var2 = 0  # Variable de contrôle utilisée dans certaines parties du code
int_var3 = 0  # Variable de contrôle utilisée dans certaines parties du code
int_var4 = 0  # Variable de contrôle utilisée dans certaines parties du code
int_fin = 0  # Variable de contrôle utilisée dans certaines parties du code

#dictionnaitre pour faire la conversion entre decimal et hexadecimal
dico = {0 : "0", 1 : "1", 2 : "2", 3 : "3", 4 : "4", 5 : "5", 6 : "6", 7 : "7", 8 : "8", 9 : "9", 10 : "a", 11 : "b", 12 : "c", 13 : "d", 14 : "e", 15 : "f"}


################################################################################################################################################################################


#fonction qui recherche sur l'ordinateur le port USB sur lequel est branche la carte
def recherche_port_STM32():
    # Obtient la liste des ports série disponibles
    listeDesPorts = prtlst.comports()

    # Mots-clés de recherche pour identifier le port STM32
    Recherche = ['STM32', 'STLink', 'USB']

    # Recherche du port STM32 dans la liste
    for motCle in Recherche:
        for port in listeDesPorts:
            if motCle in port[1]:
                return port[0]

# Obtention du port USB de la carte STM32
portUSB= recherche_port_STM32()

# Configuration du port série
portSerie = serial.Serial(port=portUSB,
                            baudrate=921600,
                            bytesize=serial.EIGHTBITS)


################################################################################################################################################################################


#fonction qui cree des trames de test de 1600 caracteres
def creation_trame_hexadecimal():
    str_trame_total = ""
    for loop in range(200):
        str_trame = 'ab'
        for loop in range(2):
            str_trame += dico[randint(0,15)]
        str_trame += 'cd'
        int_nombre_aleatoire = randint(0,3)
        strvaleurint_fin = '00'
        if int_nombre_aleatoire == 1:
            strvaleurint_fin = '01'
        elif int_nombre_aleatoire == 2:
            strvaleurint_fin = '03'
        elif int_nombre_aleatoire == 3:
            strvaleurint_fin = '07'
        str_trame += strvaleurint_fin
        str_trame_total += str_trame
    return str_trame_total

#fonction qui rend la trame utilisable dans les autres fonctions
def rendre_trame_utilisable(str_trame):
    while str_trame[0] != 'a' and str_trame[4] != 'c':
        str_trame = str_trame[1:]
    while str_trame[-2] != '0' or str_trame[-3] != 'd' or str_trame[-4] != 'c':
        str_trame = str_trame[:-1]
    return str_trame

#fonction qui fait la moyenne des valeurs d'une trame
def moyenne_etat_led_trame(str_trame):
    int_rouge = 0
    int_orange = 0
    int_vert = 0
    int_rien = 0
    for i in range (0, int(len(str_trame)/8), 8):
        if str_trame[i + 7] == '0':
            int_rien += 1
        elif str_trame[i + 7] == '1':
            int_vert += 1
        elif str_trame[i + 7] == '3':
            int_orange += 1
        elif str_trame[i + 7] == '7':
            int_rouge += 1
    if int_rien > int_vert > int_orange > int_rouge:
        return 0
    elif int_rien < int_vert > int_orange > int_rouge:
        return 1
    elif int_rien < int_vert < int_orange > int_rouge:
        return 2
    else:
        return 3

#renvoie la valeur la plus grande d'une trame
def max_etat_led_trame(str_trame):
    int_rouge = 0
    int_orange = 0
    int_vert = 0
    int_rien = 0
    for i in range (0, int(len(str_trame)/8), 8):
        if str_trame[i + 7] == '0':
            int_rien += 1
        elif str_trame[i + 7] == '1':
            int_vert += 1
        elif str_trame[i + 7] == '3':
            int_orange += 1
        elif str_trame[i + 7] == '7':
            int_rouge += 1
    if int_rouge > 0:
        return 3
    elif int_orange > 0:
        return 2
    elif int_vert > 0:
        return 1
    else:
        return 0
    
# Trouve la valeur maximale de ce qui se trouve entre ab et cd d'une trame
def trouver_decibel_max_trame(str_trame):
    nombredecibelmax = []
    for i in range(0, len(str_trame), 8):
        nombretemp_hex = str_trame[i+2:i+4]
        nombredecibelmax.append(int(nombretemp_hex, 16))
    return max(nombredecibelmax)


################################################################################################################################################################################


def changer_taille_label_decibelmetre(int_decibel):
    # Inverser la normalisation des décibels dans la plage 0-26
    nouvelle_hauteur = int(((120 - int_decibel) / 120) * 26)
    # Mettre à jour la hauteur du rectangle gris
    label_decibelmetrefond.config(height=nouvelle_hauteur)
    # Mettre à jour la couleur en fonction du niveau de décibels
    if int_decibel > 94:
        label_decibelmetre.config(bg="red")
    elif int_decibel > 74:
        label_decibelmetre.config(bg="yellow")
    else:
        label_decibelmetre.config(bg="lime")

#fonction pour retirer le messaque disant que le sonometre n'est pas branché
def masquer_info_non_branche():
    global info_branche
    info_branche.place_forget()

def boucle_principale():
    """
    Fonction pour afficher le vu-mètre en fonction de la trame du sonomètre.

    La fonction réalise les opérations suivantes :
    - Masque l'info de branchement.
    - Vérifie si le mode de fonctionnement est en carte et que le programme est activé.
    - Ouvre et lit les données du port série.
    - Cache les rectangles colorés du vu-mètre selon certaines conditions.
    - Affiche les rectangles du vu-mètre en fonction des valeurs de la trame.
    - Calcule la valeur de décibel en fonction de la trame.
    - Met à jour les labels d'informations.
    - Gère les erreurs de communication série.
    """
    global info_branche
    global int_compteur_nombre_test
    global int_somme_db
    global int_decibel_max
    global bool_etat_changer_etat_on_off
    global dernier_decibel
    global compteur_erreur
    global int_somme_db2
    global int_var1
    masquer_info_non_branche()
    try:
        if bool_mode_fonctionnement == False and bool_etat_changer_etat_on_off == True:
            # Communication série : lecture des données
            portSerie.open()
            str_donnees = portSerie.read(size=2000)
            portSerie.close()

            # Masquer les rectangles colorés du vu-mètre selon certaines conditions
            label_vertfonce.place_forget()
            if label_vertclair.winfo_ismapped() and int_var1 < 3:
                int_var1 += 1
            elif label_vertclair.winfo_ismapped() and int_var1 >= 3:
                int_var1 = 0
                label_vertclair.place_forget()
            label_jaunefonce.place_forget()
            if label_jauneclair.winfo_ismapped() and int_var1 < 3:
                int_var1 += 1
            elif label_jauneclair.winfo_ismapped() and int_var1 >= 3:
                int_var1 = 0
                label_jauneclair.place_forget()
            label_rougefonce.place_forget()
            label_rougeclair.place_forget()
            info_branche.place_forget()
            # Afficher le vu-mètre en fonction des valeurs de la trame
            grid_vumetre(max_etat_led_trame(rendre_trame_utilisable(str_donnees.hex())), 45, 250)
            # Calcul de la valeur de décibel en fonction de la trame
            if trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex())) < 48:
                int_decibel = (1.53) * trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex()))
            elif trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex())) > 107:
                int_decibel = (39.04/296) * trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex())) + 66.41
            elif trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex())) > 106:
                int_decibel = 0.75 * trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex()))
            else:
                int_decibel = 13.34 * math.log10(32.75 * (trouver_decibel_max_trame(rendre_trame_utilisable(str_donnees.hex())) - 38.54)) + 35.78
            dernier_decibel = int_decibel
            # Mettre à jour le label de décibel
            if int_decibel > dernier_decibel + 15:
                decibel["text"] = str(int(dernier_decibel)) + " dB"
            else:
                decibel["text"] = str(int(int_decibel)) + " dB"
            # Mettre à jour la taille du rectangle du vu-mètre
            changer_taille_label_decibelmetre(int(int_decibel))
            # Mettre à jour la somme des décibels pour le calcul de la moyenne
            int_somme_db2 += int_decibel
            int_moyenne_decibel = int_somme_db2 / (int_compteur_nombre_test + 1)
            int_compteur_nombre_test += 1
            # Mettre à jour le label de la moyenne
            moy_label["text"] = "Moyenne: " + str(int(int_moyenne_decibel)) + " dB"
            # Mettre à jour la valeur maximale des décibels
            if int_decibel > int_decibel_max:
                int_decibel_max = int_decibel
            # Mettre à jour le label de la valeur maximale
            max_label["text"] = "Maximum : " + str(int(int_decibel_max)) + " dB"
            # Réinitialiser le compteur d'erreurs
            compteur_erreur = 0
            # Planifier la prochaine exécution de la fonction
            if bool_mode_fonctionnement == True and bool_etat_changer_etat_on_off == True:
                sonometre.after(6, boucle_principale)
            else:
                grid_vumetre(0, 45, 250)
                sonometre.after(6, boucle_principale)
        else:
            # Si le mode de fonctionnement est différent de la carte ou si le programme est désactivé
            grid_vumetre(0, 45, 250)
            sonometre.after(6, boucle_principale)
    except Exception:
        # Gestion des erreurs de communication série
        compteur_erreur += 1
        if compteur_erreur >= 10:
            info_branche.place(y=200, x=10)
        # Planifier la prochaine exécution de la fonction
        if bool_mode_fonctionnement == False and bool_etat_changer_etat_on_off == True:
            grid_vumetre(0, 45, 250)
            sonometre.after(100, boucle_principale)
        else:
            grid_vumetre(0, 45, 250)
            decibel["text"] = "0 dB"
            reset_moyenne()
            reset_maximum()
            sonometre.after(100, boucle_principale)

def bouton_test():
    """
    Fonction qui commande l'effet du bouton test.

    Cette fonction réalise les opérations suivantes :
    - Vérifie l'état on/off.
    - Génère une valeur aléatoire pour simuler le sonomètre en mode test.
    - Met à jour les éléments graphiques en fonction de la valeur générée.
    - Calcule et affiche la moyenne et la valeur maximale des décibels.
    """
    global int_mode_fonctionnement
    global bool_mode_fonctionnement_etat
    global int_compteur_nombre_test
    global int_somme_db
    global int_decibel_max
    global bool_etat_changer_etat_on_off

    # Vérifiez l'état on/off
    if bool_mode_fonctionnement:
        if bool_etat_changer_etat_on_off:
            # Génération d'une valeur aléatoire pour simuler le sonomètre en mode test
            if bool_mode_fonctionnement == True:
                int_decibel = randint(0, 100)
            else:
                int_decibel
            # Masquer les rectangles colorés du vu-mètre
            label_vertfonce.place_forget()
            label_vertclair.place_forget()
            label_jaunefonce.place_forget()
            label_jauneclair.place_forget()
            label_rougefonce.place_forget()
            label_rougeclair.place_forget()
            # Déterminer le mode de fonctionnement en fonction de la valeur générée
            if bool_mode_fonctionnement_etat:
                if int_decibel == 0:
                    int_mode_fonctionnement = 0
                elif int_decibel < 90:
                    int_mode_fonctionnement = 1
                elif int_decibel < 130:
                    int_mode_fonctionnement = 2
                elif int_decibel >= 130:
                    int_mode_fonctionnement = 3
            # Mettre à jour le label de décibel
            decibel["text"] = str(int_decibel) + " dB"
            # Mettre à jour la somme des décibels pour le calcul de la moyenne
            int_somme_db += int_decibel
            int_moyenne_decibel = int_somme_db / (int_compteur_nombre_test + 1)
            int_compteur_nombre_test += 1
            # Mettre à jour le label de la moyenne
            moy_label["text"] = "Moyenne: " + str(int(int_moyenne_decibel)) + " dB"
            # Mettre à jour la valeur maximale des décibels
            if int_decibel > int_decibel_max:
                int_decibel_max = int_decibel
            # Mettre à jour le label de la valeur maximale
            max_label["text"] = "Maximum : " + str(int_decibel_max) + " dB"
            # Mettre à jour la taille du rectangle du vu-mètre
            changer_taille_label_decibelmetre(int_decibel)
            # Afficher le vu-mètre en fonction du mode de fonctionnement
            grid_vumetre(int_mode_fonctionnement, 45, 250)

def reset_moyenne():
    """
    Fonction qui réinitialise les valeurs liées à la moyenne des décibels.
    """
    global int_moyenne_decibel
    global int_somme_db2
    global int_compteur_nombre_test

    int_compteur_nombre_test = 0
    int_somme_db2 = 0
    int_moyenne_decibel = 0
    moy_label["text"] = "Moyenne : " + str(int_moyenne_decibel) + " dB"

def reset_maximum():
    """
    Fonction qui réinitialise les valeurs liées à la valeur maximale des décibels.
    """
    global int_decibel_max
    global int_somme_db
    int_somme_db = 0
    int_decibel_max = 0
    max_label["text"] = "Maximum : " + str(int_decibel_max) + " dB"

def changer_etat_on_off():
    """
    Fonction qui active ou désactive la fenêtre.

    Cette fonction réalise les opérations suivantes :
    - Change l'état on/off.
    - Met à jour les éléments graphiques en fonction de l'état.
    """
    global bool_etat_changer_etat_on_off

    if bool_etat_changer_etat_on_off:
        # Si la fenêtre est activée, la désactiver
        bool_etat_changer_etat_on_off = False
        bouton_changer_etat_on_off["text"] = "Off"
        bouton_changer_etat_on_off.config(bg="red")
        decibel["text"] = "0 dB"
        label_vertfonce.place_forget()
        label_vertclair.place_forget()
        label_jaunefonce.place_forget()
        label_jauneclair.place_forget()
        label_rougefonce.place_forget()
        label_rougeclair.place_forget()
        grid_vumetre(0, 45, 250)
    else:
        # Si la fenêtre est désactivée, l'activer
        bool_etat_changer_etat_on_off = True
        bouton_changer_etat_on_off["text"] = "On"
        bouton_changer_etat_on_off.config(bg="green")

def switch_mode_de_fonctionnement():
    """
    Fonction qui bascule entre le mode carte et le mode test.

    Cette fonction réalise les opérations suivantes :
    - Change le mode de fonctionnement entre le mode carte et le mode test.
    - Met à jour les éléments graphiques en fonction du mode.
    """
    global bool_mode_fonctionnement
    # Réinitialiser les valeurs liées aux décibels
    decibel["text"] = "0 dB"
    reset_moyenne()
    reset_maximum()
    # Bascule entre le mode carte et le mode test
    if bool_mode_fonctionnement:
        bool_mode_fonctionnement = False
        button_test.place_forget()
        label_vertfonce.place_forget()
        label_vertclair.place_forget()
        label_jaunefonce.place_forget()
        label_jauneclair.place_forget()
        label_rougefonce.place_forget()
        label_rougeclair.place_forget()
        info_branche.place_forget()
        bouton_switch_mode_de_fonctionnement["text"] = "Mode : Carte"
        boucle_principale()
    else:
        bool_mode_fonctionnement = True
        info_branche.place_forget()
        bouton_switch_mode_de_fonctionnement["text"] = "Mode : Test"
        grid_boutons(370, 10)
    return bool_mode_fonctionnement

#fonction pour empêcher le changement entre le mode carte et test après deux clics
def limite_changement_mode():
    global int_fin
    if int_fin < 2:
        switch_mode_de_fonctionnement()
        int_fin += 1
    elif int_fin >= 2:
        pass


################################################################################################################################################################################


#creation de tout ce qui sera affiché dans la fenetre
label_vertfonce=tk.Label(sonometre, width=10, height=20, bg = "darkgreen", relief="solid")
label_vertclair=tk.Label(sonometre, width=10, height=20, bg = "lime", relief="solid")
label_jaunefonce=tk.Label(sonometre, width=10, height=8, bg = "goldenrod", relief="solid")
label_jauneclair=tk.Label(sonometre, width=10, height=8, bg = "yellow", relief="solid")
label_rougefonce=tk.Label(sonometre, width=10, height=3, bg = "#8B2323", relief="solid")
label_rougeclair=tk.Label(sonometre, width=10, height=3, bg = "red", relief="solid")
label_decibelmetre=tk.Label(sonometre, width=10, height=3, bg = "darkgreen", relief="solid")
label_decibelmetre.place(y=45, x=450)
label_decibelmetre.config(width=10, height=26)
label_decibelmetrefond=tk.Label(sonometre, width=10, height=3, bg = "gray", relief="solid")
label_decibelmetrefond.place(y=45, x=450)
label_decibelmetrefond.config(width=10, height=16)
bouton_reset_moy = tk.Button(sonometre, text="Reset Moyenne", fg="black", bg="white", width=15, height=1, command=reset_moyenne)
bouton_reset_max = tk.Button(sonometre, text="Reset Maximum", fg="black", bg="white", width=15, height=1, command=reset_maximum)
bouton_changer_etat_on_off = tk.Button(sonometre, text="On",fg="black", bg="green", width=35, height=1, command = changer_etat_on_off)
button_test = tk.Button(sonometre, text="Test", fg="black", bg="white", width=15, height=1, command = bouton_test)
bouton_switch_mode_de_fonctionnement = tk.Button(sonometre, text="Mode : Test/Carte", fg="black", bg="white", width=15, height=1, command=limite_changement_mode)
info_branche = tk.Label(sonometre, text="Sonomètre non branché", fg="black", bg="white", width=30, height=3, font=("Helvetica", 14))
moy_label = tk.Label(sonometre, text = "Moyenne : " + str(int_moyenne_decibel) + " dB", font=("Helvetica", 20), bg="gray")
max_label = tk.Label(sonometre, text = "Maximum : " + str(int_decibel_max) + " dB", font=("Helvetica", 20), bg="gray")
decibel = tk.Label(sonometre, text = str(int_decibel) + " dB", font=("Helvetica", 30), bg="gray")


################################################################################################################################################################################


#fonction pour placer les differents boutons de la sonometre

def grid_boutons(h, l):
    bouton_changer_etat_on_off.place(y=80 + h, x=10 + l)
    button_test.place(y=0 + h, x=10 + l)
    bouton_reset_moy.place(y=40 + h, x=10 + l)
    bouton_reset_max.place(y=40 + h, x=150 + l)
    bouton_switch_mode_de_fonctionnement.place(y=0 + h, x=150 + l)

def grid_boutons_pour_demarrage(h, l):
    bouton_changer_etat_on_off.place(y=80 + h, x=10 + l)
    bouton_reset_moy.place(y=40 + h, x=10 + l)
    bouton_reset_max.place(y=40 + h, x=150 + l)
    bouton_switch_mode_de_fonctionnement.place(y=0 + h, x=150 + l)

#fonction pour placer les differents labels d'information sur les décibels
def grid_label_info(h, l):
    decibel.place (y=0 + h, x=10 + l)
    moy_label.place(y=60 + h, x=10 + l)
    max_label.place(y=110 + h, x=10 + l)

#fonction pour placer les differents reclangles du vu-metre en fonction du nombre de leds allumees
def grid_vumetre(nombre_de_led_allumes, hauteur, largeur):
        if nombre_de_led_allumes == 0:
            label_vertfonce.place(y=90 + hauteur, x=100 + largeur)
            label_jaunefonce.place(y=10 + hauteur, x=100 + largeur)
            label_rougefonce.place(y=0 + hauteur, x=100 + largeur)
        elif nombre_de_led_allumes == 1:
            label_vertclair.place(y=90 + hauteur, x=100 + largeur)
            label_jaunefonce.place(y=10 + hauteur, x=100 + largeur)
            label_rougefonce.place(y=0 + hauteur, x=100 + largeur)
        elif nombre_de_led_allumes == 2:
            label_vertclair.place(y=90 + hauteur, x=100 + largeur)
            label_jauneclair.place(y=10 + hauteur, x=100 + largeur)
            label_rougefonce.place(y=0 + hauteur, x=100 + largeur)
        elif nombre_de_led_allumes == 3:
            label_vertclair.place(y=90 + hauteur, x=100 + largeur)
            label_jauneclair.place(y=10 + hauteur, x=100 + largeur)
            label_rougeclair.place(y=0 + hauteur, x=100 + largeur)


################################################################################################################################################################################


#le premier caractere correspond a son emplacement en hauteur puis en largeur
grid_boutons_pour_demarrage(370, 10)
#le premier caractere correspond a son emplacement en hauteur puis en largeur
grid_label_info(40, 10)
#le premier caractere correspond au nombre de led a allumer, puis son emplacement en hauteur puis en largeur
grid_vumetre(0, 45, 250)
#on ferme le port au cas ou
portSerie.close()
#boucle principale de la sonometre
sonometre.mainloop()