#include <Arduino_JSON.h>

// ================= MOTOR PINS =================
#define MOTOR_LATCH 12
#define MOTOR_CLK 4
#define MOTOR_DATA 8
#define MOTOR_ENABLE 7  // Active LOW

// ================= ULTRASONIC =================
#define trigPin 9
#define echoPin 10

// ================= LINE SENSORS =================
#define left 2
#define right A5

// ================= STATE =================
bool runLineFollower = false;
bool obstacleReported = false;
bool waitingForDropAck = false;
bool intersectionHandled = false;

int totalPatients = 4;   // default (existing behavior)
int servedPatients = 0;
bool returnToOrigin = false;
bool executedthis = false;

// ================= ADD THIS GLOBAL =================
bool ignoreNode = false;
static int rectCount = 0;

// ================= NODE DETECTION =================
enum NodeDetectState {
  WAIT_FOR_ENTRY,
  INSIDE_NODE,
  WAIT_FOR_EXIT
};

NodeDetectState nodeState = WAIT_FOR_ENTRY;

// ================= PATH =================
enum Action {
  STRAIGHT,
  LEFT_TURN,
  RIGHT_TURN,
  UTURN_ACTION,
  UTURN_ACTION2
};

Action path[] = {
  LEFT_TURN,      // #1
  UTURN_ACTION,   // #2
  STRAIGHT,       // #3
  UTURN_ACTION2,  // #4
  RIGHT_TURN,     // #5
  LEFT_TURN,      // #6
  UTURN_ACTION,   // #7
  STRAIGHT,       // #8
  UTURN_ACTION2,  // #9
  LEFT_TURN,      // #10
  STRAIGHT        // #11
};

Action pendingTurn;   // stores which U-turn to execute

int stepState = 0;
// ================= UART =================
#define RX_BUF_SIZE 100
char rxBuf[RX_BUF_SIZE];
uint8_t idx = 0;

String line = "";
int rect_cnt = 0;
int end_cnt = 0;
bool in_rect = false;
#define RECT_THRESHOLD 10  // tune
#define END_THRESHOLD 15   // tune

// ================= JSON =================
JSONVar myObject;

// ================= MOTOR STATE =================
uint8_t latch_state = 0;

// ================= DISTANCE =================
long duration;
float distance;
unsigned long lastDistSend = 0;
unsigned long lastturned = 0;

const unsigned long DIST_INTERVAL = 200;  // ms
const unsigned long TURN_INTERVAL = 40;   // ms

// ================================================= 
// MOTOR 
// =================================================

void shiftWrite(uint8_t data) {
  digitalWrite(MOTOR_LATCH, LOW);
  shiftOut(MOTOR_DATA, MOTOR_CLK, MSBFIRST, data);
  digitalWrite(MOTOR_LATCH, HIGH);
}

void setMotor(uint8_t motor, uint8_t dir) {
  uint8_t a, b;

  if (motor == 1) {
    a = 2;
    b = 3;
  }

  if (motor == 2) {
    a = 1;
    b = 4;
  }

  if (motor == 3) {
    a = 5;
    b = 7;
  }

  if (motor == 4) {
    a = 0;
    b = 6;
  }

  latch_state &= ~(1 << a);
  latch_state &= ~(1 << b);

  if (dir == 1)
    latch_state |= (1 << a);

  else if (dir == 2)
    latch_state |= (1 << b);

  shiftWrite(latch_state);
}

void stopAllMotors() {
  setMotor(1, 0);
  setMotor(2, 0);
  setMotor(3, 0);
  setMotor(4, 0);
}

// ================================================= 
// ULTRASONIC 
// =================================================

float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH, 25000);  // timeout safety

  if (duration == 0) return 999;  // no echo = far

  return duration * 0.034 / 2;
}

void sendDistanceTelemetry() {
  unsigned long now = millis();
  if (now - lastDistSend >= DIST_INTERVAL) {
    lastDistSend = now;
    distance = getDistance();
    Serial.print("{\"DIST\":");
    Serial.print(distance);
    Serial.println("}");
  }
}

// ================================================= 
// UART JSON 
// =================================================

void processUART() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      line.toCharArray(rxBuf, RX_BUF_SIZE);

      // -------- Parse JSON --------
      myObject = JSON.parse(rxBuf);
      if (JSON.typeof(myObject) != "undefined") {

        if (myObject.hasOwnProperty("CMD")) {
          const char* cmd = myObject["CMD"];  
          // -------- START --------
          // if (strcmp(cmd, "START") == 0) {
          //   runLineFollower = true;
          //   Serial.println("{\"ACK\":\"READY\"}");
          // }  +

          if (strcmp(cmd, "START") == 0) {
            if (waitingForDropAck) {
              // execute stored turn
              if (pendingTurn == UTURN_ACTION) {
                uTurn();
              } else if (pendingTurn == UTURN_ACTION2) {
                uTurn2();
              }

              waitingForDropAck = false;
              stepState++;
              servedPatients++;

              // ================= CORRECT RETURN LOGIC =================

              // if (
              //   (totalPatients == 1 && stepState == 2) ||
              //   (totalPatients == 2 && stepState == 5) ||
              //   (totalPatients == 3 && stepState == 8)
              // ) {
              //   Serial.print("{\"ACK\":\"");
              //   Serial.print(totalPatients);
              //   Serial.print(" ");
              //   Serial.print(stepState);
              //   Serial.println("\"}");
              //   returnToOrigin = true;
              // }

              // if (returnToOrigin) {
              //   goToOrigin();
              //   return;
              // }

              Serial.println("{\"ACK\":\"CONTINUE\"}");
            }
            else {
              runLineFollower = true;
              Serial.println("{\"ACK\":\"READY\"}");
            }
          }
          
          // -------- STOP --------
          else if (strcmp(cmd, "STOP") == 0) {
            runLineFollower = false;
            stopAllMotors();
            obstacleReported = false;  // ✅ reset

            Serial.println("{\"ACK\":\"STOPPED\"}");
            delay(5);
            Serial.println("{\"ACK\":\"STOPPED\"}");
          }
        }

        if (myObject.hasOwnProperty("PAT")) {
          totalPatients = (int) myObject["PAT"];

          // safety clamp
          if (totalPatients < 1) totalPatients = 1;
          if (totalPatients > 4) totalPatients = 4;

          Serial.print("{\"ACK\":\"PAT_SET:");
          Serial.print(totalPatients);
          Serial.println("\"}");
        }
      }

      else {
        Serial.println("{\"ACK\":\"BAD_JSON\"}");
      }
      line = "";
    } 
    else if (c != '\r') {
      line += c;
    }
  }
}

// ================================================= 
// HANDLE CHECKPOINT ACTION 
// =================================================

void handleIntersection() {
  stopAllMotors();
  delay(100);

  Action current = path[stepState];

  // ---------- DROP CHECKPOINT ----------
  if (current == UTURN_ACTION || current == UTURN_ACTION2)
  {
    waitingForDropAck = true;
    pendingTurn = current;

    stopAllMotors();

    // 🔥 Send multiple times + flush
    for (int i = 0; i < 3; i++) {
      Serial.println("{\"CHK\":\"DROP\"}");
      Serial.flush();
      delay(10);
    }

    return;
  }

  if (servedPatients==1 && totalPatients==1) {
    current = RIGHT_TURN;
  }
  else if (servedPatients==2 && totalPatients==2) {
    current = LEFT_TURN;
    // current[5]
  }
  else if (servedPatients==3 && totalPatients==3 && executedThis==false) {
    current = RIGHT_TURN;
    executedThis=true;
  }
  else if(servedPatients==3 && totalPatients==3 && executedThis==true) {
    current = STRAIGHT;
  }

  if (current == LEFT_TURN) {
    Serial.println("{\"CHK\":\"LEFT\"}");
    turnLeft90();
  } else if (current == RIGHT_TURN) {
    Serial.println("{\"CHK\":\"RIGHT\"}");
    turnRight90();
  // } else if (current == UTURN_ACTION) {
  //   uTurn();
  // } else if (
  //   current == UTURN_ACTION2) {
  //   uTurn2();
  } else if (current == STRAIGHT) {
    Serial.println("{\"CHK\":\"STRAIGHT\"}");
    proceedStraight();
  }


  stepState++;
  Serial.print("{\"STEP\":");
  Serial.print(stepState);
  Serial.println("}");
}

// ================================================= 
// LINE FOLLOW LOGIC 
// =================================================

void lineFollowerTask() {
  uint8_t L = digitalRead(left);
  uint8_t R = digitalRead(right);

  // ---------- RECTANGLE DETECTION (EARLY + CONFIRM) ----------
  bool nodeDetected = false;
  static bool rectStarted = false;
  static int confirmCount = 0;

  // if (!ignoreNode)   // {
  // if (L == 0 && R == 0)   // {
  // if (!rectStarted) {
  //
  // 🔥 FIRST TOUCH OF RECTANGLE → STOP IMMEDIATELY
  // stopAllMotors();
  // rectStarted = true;
  // confirmCount = 0;
  // delay(50);   // small settle
  // }
  // confirmCount++;
  // if (confirmCount > 3) {
  // 🔥 small value (2–4)
  // nodeDetected = true;
  // rectStarted = false;
  // }
  // }
  // else
  // {
  // rectStarted = false;
  // confirmCount = 0;
  // }
  // }
  // if (nodeDetected) {
  // ignoreNode = true;
  // handleIntersection();
  // return;
  // } distance = getDistance();

  // ---------- OBSTACLE DETECT ----------
  Serial.print("{\"DIST\":\"");
  Serial.print(distance);
  Serial.println("\"}");

  if (distance < 30.0) {
    stopAllMotors();
    if (!obstacleReported) {
      Serial.println("{\"ACK\":\"OBSTACLE\"}");
      obstacleReported = true;
    }
    return;  // do NOT do line following
  } else {
    // Clear obstacle flag when obstacle is gone
    // ---------- NORMAL LINE FOLLOW ----------
    // uint8_t L = digitalRead(left);
    // uint8_t R = digitalRead(right);

    if (waitingForDropAck) {
      stopAllMotors();
      return;
    }

    static int lastDir = 0;
    if (L == 0 && R == 0) {
      intersectionHandled = false;
      lastDir = 0;
      setMotor(1, 1);
      setMotor(2, 1);
      setMotor(3, 1);
      setMotor(4, 1);
    } else if (L == 0 && R == 1) {
      lastDir = 1;
      // soft right
      setMotor(1, 1);
      setMotor(2, 1);
      setMotor(3, 0);
      setMotor(4, 0);
    } else if (L == 1 && R == 0) {
      lastDir = -1;
      // soft left
      setMotor(1, 0);
      setMotor(2, 0);
      setMotor(3, 1);
      setMotor(4, 1);
    } else {
      if (!intersectionHandled) {
        intersectionHandled = true;
        handleIntersection();
      }
    }

    obstacleReported = false;
  }
}

// ================================================= 
// SETUP 
// =================================================

void setup() {
  pinMode(MOTOR_LATCH, OUTPUT);
  pinMode(MOTOR_CLK, OUTPUT);
  pinMode(MOTOR_DATA, OUTPUT);
  pinMode(MOTOR_ENABLE, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(left, INPUT);
  pinMode(right, INPUT);

  digitalWrite(MOTOR_ENABLE, LOW);
  shiftWrite(0);
  Serial.begin(115200);
  Serial.println("{\"ACK\":\"READY\"}");
  line.reserve(128);
}

// ================================================= 
// LOOP 
// =================================================

void goStraight() {
  setMotor(1, 1);
  setMotor(2, 1);
  setMotor(3, 1);
  setMotor(4, 1);
}

void rotateLeft() {
  // Left wheels backward, right wheels forward
  setMotor(1, 2);
  setMotor(2, 2);
  setMotor(3, 1);
  setMotor(4, 1);
}

void rotateRight() {
  setMotor(1, 1);
  setMotor(2, 1);
  setMotor(3, 2);
  setMotor(4, 2);
}

void proceedStraight() {
  goStraight();
  delay(300);
}

void turnLeft90() {
  goStraight();
  delay(300);
  rotateLeft();
  delay(1200);  // tune

  // wait until line found
  goStraight();
  delay(40);
  stopAllMotors();
  // delay(100);
  // while (digitalRead(left) == 1 && digitalRead(right) == 1);
  // stopAllMotors();
}

void turnRight90() {
  goStraight();
  delay(300);
  rotateRight();
  delay(1200);  // tune
  goStraight();
  delay(40);
  stopAllMotors();
  // delay(100);
  // while (digitalRead(left) == 1 && digitalRead(right) == 1);
  // stopAllMotors();
}

void uTurn() {
  rotateRight();
  delay(2700);  // tune for 180 deg
  // while (digitalRead(left) == 1 && digitalRead(right) == 1);
  stopAllMotors();
}

void uTurn2() {
  rotateLeft();
  delay(2700);  // tune for 180 deg
  // while (digitalRead(left) == 1 && digitalRead(right) == 1);
  stopAllMotors();
}

void goToOrigin() {
  Serial.println("{\"MODE\":\"RETURN_ORIGIN\"}");

  stopAllMotors();
  delay(200);

  if (totalPatients == 1) {
    // RIGHT → origin
    turnRight90();
    proceedStraight();
  }

  else if (totalPatients == 2) {
    // LEFT → origin
    turnLeft90();
    proceedStraight();
  }

  else if (totalPatients == 3) {
    // RIGHT → STRAIGHT → origin
    turnRight90();
    proceedStraight();
  }

  // PAT=4 → do nothing (already ends correctly)

  stopAllMotors();
  runLineFollower = false;

  Serial.println("{\"ACK\":\"AT_ORIGIN\"}");
}

void loop() {
  processUART();  // ALWAYS listen for commands

  if (runLineFollower) {
    lineFollowerTask();
  } else {
    stopAllMotors();
  }

  sendDistanceTelemetry();  // ✅ independent telemetry
  // turnLeft90();
  // delay(5000);
  // turnRight90();
  // delay(5000);;
  // uTurn();
  // delay(5000);
}void setup() {
  // put your setup code here, to run once:

}

void loop() {
  // put your main code here, to run repeatedly:

}
