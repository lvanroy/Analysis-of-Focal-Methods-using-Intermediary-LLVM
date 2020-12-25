#include <cstdlib>

using namespace std;

class Stack{
private:
    int *arr;
    int top;
    int capacity;
public:
    Stack(int size);
    ~Stack();

    void push(int);
    int peek();

    bool full();
    bool empty();
};