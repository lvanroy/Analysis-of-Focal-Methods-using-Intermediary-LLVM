#include "gtest/gtest.h"
#include "Stack.h"

TEST(StackTest, push){
    Stack s(10);

    s.push(5);
    ASSERT_FALSE(s.empty());
    ASSERT_EQ(5, s.peek());
}