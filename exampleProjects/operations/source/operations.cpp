#include "operations.h"
#include <math.h>

int Operations::add(int a, int b){
    return a + b;
}

int Operations::sub(int a, int b){
    return a - b;
}

int Operations::mul(int a, int b){
    return a * b;
}

int Operations::div(int a, int b){
    return a / b;
}

int Operations::rem(int a, int b){
    return a % b;
}

unsigned Operations::div(unsigned a, unsigned b){
    return a / b;
}

unsigned Operations::rem(unsigned a, unsigned b){
    return a % b;
}

float Operations::fadd(float a, float b){
    return a + b;
}

float Operations::fsub(float a, float b){
    return a - b;
}

float Operations::fmul(float a, float b){
    return a * b;
}

float Operations::fdiv(float a, float b){
    return a / b;
}

float Operations::frem(float a, float b){
    return fmod(a, b);
}
