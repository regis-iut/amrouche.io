#include <io.h>

#define F_CPU 8000000UL // Fr?quence du microcontr?leur : 8 MHz

// Prototypes de fonctions
void SPISetUp(void);                                // Configure le SPI
int ReadMCP3201(void);                              // Lit la valeur du MCP3201 via SPI
float ConvertToVoltage(int adc_value);              // Convertit la valeur de l'ADC en tension
void SetBit(unsigned char p);                       // D?finit un bit donn? dans PORTB
void ClearBit(unsigned char m);                     // Efface un bit donn? dans PORTB
void SetLoad(void);                                 // Met la broche LOAD (CS) en ?tat haut
void ClearLoad(void);                               // Met la broche LOAD (CS) en ?tat bas
void spi_send_byte(unsigned char data);             // Envoie un octet via SPI
void max7219_send_command(unsigned char address, unsigned char data); // Envoie une commande au MAX7219
void max7219_init(void);                            // Initialise le MAX7219
void max7219_display_digit(unsigned char position, unsigned char digit, unsigned char dot); // Affiche un chiffre ? une position sp?cifique
void display_voltage(float value);                  // Affiche une tension sur l'afficheur 7 segments
void timer0_config();                               // Configure le Timer0
void delay_20us();                                  // Cr?e un d?lai de 20 ?s




// Pin definitions
#define LOAD_PIN PORTB4  // Broche pour LOAD (CS) du MAX7219
#define DD_LOAD_PIN DDB4 // Direction pour la broche CS

#define CS_PIN PORTB3    // Broche pour chip select (CS) du MCP3201
#define DD_CS_PIN DDB3   // Direction pour la broche CS

#define DO_PIN PORTB1    // Broche pour MISO (data in) du MCP3201
#define DD_DO_PIN DDB1   // Direction pour MISO

#define MOSI_PIN PORTB0   // Broche pour MOSI du MAX7219
#define DD_MOSI_PIN DDB0  // Direction pour MOSI

#define CLK_PIN PORTB2   // Broche pour l'horloge SPI
#define DD_CLK_PIN DDB2  // Direction pour l'horloge SPI



#define VREF 3.3             // Tension de r?f?rence pour l'ADC
#define MAX_ADC_VALUE 4095   // R?solution maximale de l'ADC 12 bits (2^12 - 1)



// Lookup table for displaying digits 0-9 on 7-segment displays
const unsigned char digitCode[] = {
    0b01111110, // 0
    0b00110000, // 1
    0b01101101, // 2
    0b01111001, // 3
    0b00110011, // 4
    0b01011011, // 5
    0b01011111, // 6
    0b01110000, // 7
    0b01111111, // 8
    0b01111011  // 9
};




////////////////////////////MAIN/////////////////////////////////////////////



void main(void)
{
    unsigned int adc_value;    // Variable pour stocker la valeur de l'ADC
    float voltage;             // Variable pour stocker la tension convertie
    //int voltage_int = 0;       // Variable pour stocker la tension en millivolts
    int timer=0;
    
    // Configuration SPI 
    SPISetUp();

    // Configure ports: PB0 (DATA), PB2 (CLOCK), PB3 (LOAD) as outputs      POUR MAX7219
    DDRB |= (1 << DD_MOSI_PIN) | (1 << DD_CLK_PIN) | (1 << DD_LOAD_PIN); 

    // Initialize the MAX7219
    max7219_init();              // Initialise le MAX7219
    timer0_config();             // Initialise le Timer0

while (1)
{
    // Lecture du MCP3201
    adc_value = ReadMCP3201();           // Lit la valeur de l'ADC depuis le MCP3201
    voltage = ConvertToVoltage(adc_value); // Convertit la valeur ADC en tension
    //voltage_int = (int)(voltage * 100);  // Convertit la tension en millivolts   
    
    delay_20us();
    delay_20us();            
    
    // Afficher la tension sur l'afficheur 7 segments
    display_voltage(voltage * 4.83);     // Affiche la tension ajust?e sur MAX7219, Adapter Voltage*k pour calibrer   3V / R2/R1+R2
    //delay_ms(10);                       // Attente pour la stabilit? (500 ms)
    for(timer = 0; timer<499; timer++){
    delay_20us();
    }
}

}


////////////////////////////CAN MCP3201/////////////////////////////////////////////


void SPISetUp() {
    // Configurer les broches SPI
    DDRB |= (1 << DD_CS_PIN) | (1 << DD_CLK_PIN);  // CS et CLK en sortie
    DDRB &= ~(1 << DD_DO_PIN);                    // MISO en entr?e

    // Activer la r?sistance de pull-up sur MISO
    PORTB |= (1 << DO_PIN);

    // CS initialement d?sactiv?
    PORTB |= (1 << CS_PIN);
}

int ReadMCP3201() {

    int result = 0;         // Initialise la variable de r?sultat
    int i = 0; 
    int j = 0;
    
    // Activer le CS (LOW)
    PORTB &= ~(1 << CS_PIN);

    // Synchronisation initiale (2 bits HI-Z + 1 NULL BIT)
    for (i = 0; i < 3; i++) {
        PORTB |= (1 << CLK_PIN);   // Monter l'horloge
        delay_20us();              // D?lai ?tat haut
        PORTB &= ~(1 << CLK_PIN);  // Descendre l'horloge
        delay_20us();              // D?lai ?tat bas
    }

    // Lecture des 12 bits de donn?es
    for (j = 0; j < 12; j++) {
        PORTB |= (1 << CLK_PIN);   // Monter l'horloge
        delay_20us();
        
        // D?calage du r?sultat et lecture du bit
        result <<= 1;              // D?cale le r?sultat pour ins?rer un bit
        if (PINB & (1 << DO_PIN)) {             // V?rifie l'?tat de MISO
            result |= 1;           // Ajoute le bit lu ? result si DO_PIN est ? 1
        }

        PORTB &= ~(1 << CLK_PIN);  // Descend l'horloge
        delay_20us();
    }

    // D?sactiver le CS (HIGH)
    PORTB |= (1 << CS_PIN);

    // Retourner les 12 bits valides
    return result & 0x0FFF;    //Permet de supprimer les bits useless : 0x0FFF = 0000111111111111 les 4 "0" ne sont pas pris
}

float ConvertToVoltage(int adc_value) {
    return (adc_value * VREF) / MAX_ADC_VALUE;          // Formule de conversion de l'ADC en tension
}



////////////////////////////7 Segments/////////////////////////////////////////////




// Set a bit on PortB
void SetBit(unsigned char p)
{
    PORTB |= (1 << p);
}

// Clear a bit on PortB
void ClearBit(unsigned char m)
{
    PORTB &= ~(1 << m);
}

// Set LOAD (CS) high
void SetLoad(void)
{
    PORTB |= (1 << LOAD_PIN);
}

// Set LOAD (CS) low
void ClearLoad(void)
{
    PORTB &= ~(1 << LOAD_PIN);
}

// Function to send a byte via SPI to the MAX7219
void spi_send_byte(unsigned char data) {
    int j = 0;
    for (j = 0; j < 8; j++) {
        if (data & 0x80) {          //0x80 correspond ? 10000000 en binaire. L'op?ration & (AND bit ? bit) conserve uniquement le MSB actif.
            SetBit(MOSI_PIN); // Set DATA high
        } else {
            ClearBit(MOSI_PIN); // Set DATA low
        }
        data <<= 1;     // D?cale les bits vers la gauche

        // Pulse the CLOCK
        SetBit(PORTB2); // Set CLOCK high
        
        ClearBit(PORTB2); // Set CLOCK low
    }
}


// Send a command to the MAX7219

void max7219_send_command(unsigned char address, unsigned char data) {
    ClearLoad(); // Set LOAD low
    spi_send_byte(address); // Send the address
    spi_send_byte(data); // Send the data
    SetLoad(); // Set LOAD high
}

// Initialize the MAX7219
void max7219_init(void) {
    max7219_send_command(0x09, 0x00);            // Mode d?codage : pas de d?codage  / Les codes binaires envoyaient sont directement interpr?t?s comme des codes de segments ex : 0b01111110 pour afficher le chiffre 0
    max7219_send_command(0x0A, 0x05);            // R?glage de l'intensit? (luminosit?)
    max7219_send_command(0x0B, 0x03);            // Affiche 4 digits (0-3)
    max7219_send_command(0x0C, 0x01);            // Mode fonctionnement normal /  0x00 --> Mode arr?t (shutdown)
    max7219_send_command(0x0F, 0x00);            // D?sactive le test d'affichage 
}

// Affiche un chiffre ? une position sp?cifique sur un afficheur 7 segments
void max7219_display_digit(unsigned char position, unsigned char digit, unsigned char dot) {
    // V?rifie si le point d?cimal doit ?tre activ?
    if (dot) {
        digit |= 0x80; // Active le bit de poids fort (MSB) pour afficher le point d?cimal
    }

    // Envoie la commande au MAX7219 pour afficher le chiffre ? la position donn?e
    max7219_send_command(position, digit);
}



void display_voltage(float value) {
    // Extraire les parties de la tension
    int tens = (int)value / 10;                    // Dizaine
    int units = (int)value % 10;                   // Unit?
    int tenths = (int)(value * 10) % 10;           // Dixi?me, Multiplier la valeur par 10 pour "d?placer" la virgule d'un cran, Prendre la partie enti?re (int) pour ?liminer le reste, Prendre le reste de la division par 10 pour isoler le dernier chiffre
    int hundredths = (int)(value * 100) % 10;      // Centi?me

    // Afficher les chiffres sur les 7 segments
    max7219_display_digit(1, digitCode[tens], 0);      // Dizaine   : adresse,data,point ou pas
    max7219_display_digit(2, digitCode[units], 1);     // Unit? (avec un point pour d?cimales)  : adresse,data,point ou pas
    max7219_display_digit(3, digitCode[tenths], 0);    // Dixi?me : adresse,data,point ou pas
    max7219_display_digit(4, digitCode[hundredths], 0);// Centi?me : adresse,data,point ou pas
}







////////////////////////////TIMER/////////////////////////////////////////////




//1 tick =  1/8MHz = 0.125?s
void timer0_config() {
    // Configure Timer0 en mode Normal
    TCCR0A = 0x00;              // Mode Normal
    TCCR0B = (1 << CS00);       // Pas de prescaler
    TCNT0 = 0;                  // Initialise le compteur ? 0
}

void delay_20us() {
    TCNT0 = 0;                  // R?initialise le compteur ? 0
    while (TCNT0 < 4);          // Attends que le timer atteigne 4 ticks
}

