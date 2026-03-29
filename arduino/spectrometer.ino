#include <Wire.h>
#include <MCP342x.h>

uint8_t address = 0x68;
MCP342x adc = MCP342x(address);

#define STEP_PIN 2  // Пин для шагов (CLK+)
#define DIR_PIN 3   // Пин для направления (CW+)
#define EN_PIN 4    // Пин для включения (EN+)

bool isRunning = false;
bool isReturning = false;
long currentStep = 0; 

void setup() {
  Serial.begin(9600);
  Wire.begin();
  pinMode(13, OUTPUT);
  
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);

  // Включаем мотор.
  digitalWrite(EN_PIN, LOW);
  
  MCP342x::generalCallReset(); 
  delay(10); // Дадим больше времени на перезагрузку АЦП
  
  Wire.requestFrom(address, (uint8_t)1);
  if (!Wire.available()) {
    Serial.println("ErrorADC_Init");
  }
}

void loop() {
  // 1. ПРОВЕРКА КОМАНД ОТ ПК
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      isRunning = true;
      isReturning = false;
      digitalWrite(13, HIGH);
      
      digitalWrite(DIR_PIN, HIGH);
      delay(5); // Обязательная пауза, чтобы оптопара драйвера успела переключить направление
    } 
    else if (command == '0') {
      isRunning = false;
      digitalWrite(13, LOW);
      
      isReturning = true;
      digitalWrite(DIR_PIN, LOW); 
      delay(5);
    }
  }

  // 2. ВЫПОЛНЕНИЕ ЗАДАЧИ (Сканирование)
  if (isRunning) {
    // --- ШАГ ---
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(100); 
    digitalWrite(STEP_PIN, LOW);
    
    delay(20); // Механическая пауза. Даем ротору время физически повернуться
    currentStep++;
    
    // --- АЦП (2 измерения) ---
    long int val1 = 0;
    long int val2 = 0;
    MCP342x::Config status;
    
    // Первое измерение
    uint8_t err1 = adc.convertAndRead(MCP342x::channel1, MCP342x::oneShot,
                                     MCP342x::resolution18, MCP342x::gain1,
                                     1000000, val1, status);
                                     
    // Второе измерение
    uint8_t err2 = adc.convertAndRead(MCP342x::channel1, MCP342x::oneShot,
                                     MCP342x::resolution18, MCP342x::gain1,
                                     1000000, val2, status);

    // --- ОТПРАВКА СРЕДНЕГО ЗНАЧЕНИЯ ---
    if (!err1 && !err2) {
      // Считаем среднее
      long int average = (val1 + val2) / 2;
      Serial.println(average);
    } else {
      // Если АЦП "отвалился" от помех мотора, отправляем маркер ошибки
      Serial.println(-9999);
    }
  } 
  
  // 3. ВОЗВРАТ В НОЛЬ
  else if (isReturning) {
    if (currentStep > 0) {
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(100);
      digitalWrite(STEP_PIN, LOW);
      
      delay(2); // Скорость возврата
      
      currentStep--;
    } else {
      isReturning = false; 
    }
  }
}