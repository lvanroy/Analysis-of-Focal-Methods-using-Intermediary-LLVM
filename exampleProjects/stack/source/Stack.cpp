#include "Stack.h"

Stack::Stack(int size) {
    arr = new int[size];
    capacity = size;
    top = -1;
}

Stack::~Stack() {
    delete[] arr;
}

void Stack::push(int x) {
    if (full()){
        exit(EXIT_FAILURE);
    }
    arr[++top] = x;
}


int Stack::peek()
{
    if (!empty())
        return arr[top];
    else
        exit(EXIT_FAILURE);
}

bool Stack::full(){
    return top == capacity - 1;
}

bool Stack::empty()
{
    return top == -1;
}