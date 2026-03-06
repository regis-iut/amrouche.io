const int pinEntree = 3;     // PB3 = broche 2 (entrée impulsions)
const int txPin = 4;         // PB4 = broche 3 (TX UART)
const int idPin0 = 0;        // PB0 = broche 5 (bit 0 de l'ID)
const int idPin1 = 1;        // PB1 = broche 6 (bit 1 de l'ID)
const int idPin2 = 2;        // PB2 = broche 7 (bit 2 de l'ID)

unsigned long compteur = 0;
bool etatOld = LOW;
uint8_t deviceID = 0;        // ID de l'appareil (3 bits)

void setup() {
  // Configuration des broches d'ID en entrée
  pinMode(idPin0, INPUT);
  pinMode(idPin1, INPUT);
  pinMode(idPin2, INPUT);
  
  // Lecture de l'ID au démarrage. On lit le premier pin, on décale la valeur lu de 2 vers la gauche, 
  // puis on lit le second pin d'id, on décale la valeur lu de 1 sur la gauche.
  // Enfin on lit le dernier pin d'ID. On obtient un résultat de la forme : 0b101 par exemple
  deviceID = (digitalRead(idPin2) << 2 ) | 
             (digitalRead(idPin1) << 1 ) | 
             digitalRead(idPin0);
  //deviceID = 0b101;  // ID fixe pour test (valeur décimale : 5)

  
  // Configuration des autres broches
  pinMode(pinEntree, INPUT);
  pinMode(txPin, OUTPUT);
  digitalWrite(txPin, HIGH);  // ligne TX au repos = HIGH
}

void loop() {
  bool valeurLu = digitalRead(pinEntree); // On lit un pin en sortie de l'AOP

  // Permet de vérifier si l'état actuel du pin est le meme que précédemment 
  if (valeurLu != etatOld) {
    etatOld = valeurLu;

    // Si on lit un état logique haut
    if (valeurLu == HIGH) {
      // Condition qui permet de calculer le temps entre deux front montant
      if (compteur > 0) {
        // Calcul du BPM et conversion en entier
        unsigned int bpm = 60000 / compteur;
        
        // Limitation à 255 (1 octet) et séparation en deux paquet de 4 bits (nible)
        if (bpm > 255) {
          bpm = 255;
        }

        uint8_t highNibble = (bpm >> 4) & 0x0F;  
        // Permet de garder les 4 bits de poids fort. Exemple : 0b11110000 devient dans un premier temps 0b00001111.
        // Le masque  & 0x0F permet d'être sûr que l'on garde uniquement que les 4 bits qui nous interresse
        
        uint8_t lowNibble = bpm & 0x0F;           
        // Permet de garder les 4 bits de poids faible. Par exemple, 0b10011011 devient ob00001011
        
        // Envoi des deux trames
        sendFrame(0,highNibble );  // Envoie la Trame 0 (B=0) //highNibble
        delay(10);
        sendFrame(1,lowNibble );   // Envoie la Trame 1 (B=1) , lowNibble
        delay(10);
      }
      compteur = 0;
    }
  } else {
    delay(1);
    compteur++;
  }
}


// Envoie une trame complète 
void sendFrame(bool frameNumber, uint8_t data4bits) {
  // Construction de la trame (8 bits)
  uint8_t frameData = (deviceID << 5) |       // AAA (3 bits) - ID configuré
                      (frameNumber << 4) |    // B (1 bit) - numéro de trame
                      (data4bits & 0x0F);     // CCCC (4 bits) - données

  // Calcul de la parité paire
  bool parity = 0;
  for (uint8_t i = 0; i < 8; i++) {
    parity ^= (frameData >> i) & 0x01;  
    // frameData >> i décale le bit i à droite, le mettant en position 0
    // & 0x01 isole le bit
    // parity ^= (frameData >> i) & 0x01; devient parity ^= bit
    // On fait donc pour tous les bits un XOR. D'après la table de vérité du XOR, 1 - 1 devient 0 et 1 - 0 devient 1
    // Si tous les bits valent 1 alors 1 Xor 1 Xor 1 Xor 1 alors on a 0
    // Si tous les bits valent 1 alors 1 Xor 1 Xor 0 Xor 1 alors on a 1 car on a une situation 1 - 0
    // 1 ^ 1 ^ 1 = (1 ^ 1) ^ 1 = 0 ^ 1 = 1 (impair)
    // 1 ^ 1 ^ 1 ^ 1 = (1 ^ 1) ^ (1 ^ 1) = 0 ^ 0 = 0 (pair)

  }

  // Arrete toutes les interrupts pour avoir une transmission stable, fonction en C++
  noInterrupts();
  
  // Start bit (D)
  digitalWrite(txPin, LOW);
  delayMicroseconds(208); // Corresponds au délais à attendre : 1/baudrate
  
  // Envoi des 8 bits de données (LSB-first)
  for (uint8_t i = 0; i < 8; i++) {
    // on commence à lire la position 7 de frameData jusqu'à la position 0
    digitalWrite(txPin, (frameData >> i) & 0x01);
    // frameData >> i permet d'être toujours à la position 0
    // & 0x01 masque tous les autres bits hormis le bit à la position 0 (sécurité)
    delayMicroseconds(208);
  }
  
  // Mettre: for (int8_t i = 7; i >= 0; i--) {
  //            digitalWrite(txPin, (frameData >> i) & 0x01);}
  // Si on veut MSB first





  // Bit de parité (E)
  digitalWrite(txPin, parity);
  delayMicroseconds(208);
  
  // Stop bit (F)
  digitalWrite(txPin, HIGH);
  delayMicroseconds(208);
  
  // Relance les interrupts
  interrupts();
}