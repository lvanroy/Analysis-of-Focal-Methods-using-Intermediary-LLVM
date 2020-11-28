#include "gtest/gtest.h"
#include "operations.h"

TEST(OPERATIONTEST, add){
    Operations operations;
    ASSERT_EQ(operations.add(2, 3), 5);
    ASSERT_EQ(operations.add(-2, 5), 3);
}

TEST(OPERATIONTEST, sub){
    Operations operations;
    ASSERT_EQ(operations.sub(3, 2), 1);
    ASSERT_EQ(operations.sub(3, -2), 5);
}

TEST(OPERATIONTEST, mul){
    Operations operations;
    ASSERT_EQ(operations.mul(4, 2), 8);
    ASSERT_EQ(operations.mul(4, -2), -8);
}

TEST(OPERATIONTEST, div){
    Operations operations;
    ASSERT_EQ(operations.div(4, 2), 2);
    ASSERT_EQ(operations.div(4, -2), -2);
}

TEST(OPERATIONTEST, rem){
    Operations operations;
    ASSERT_EQ(operations.rem(3, 2), 1);
    ASSERT_EQ(operations.rem(3, -2), -1);
}

TEST(OPERATIONTEST, udiv){
    Operations operations;
    ASSERT_EQ(operations.div((unsigned)3, (unsigned)2), 1);
    ASSERT_EQ(operations.div((unsigned)10, (unsigned)2), 5);
}

TEST(OPERATIONTEST, urem){
    Operations operations;
    ASSERT_EQ(operations.rem((unsigned)3, (unsigned)2), 1);
    ASSERT_EQ(operations.rem((unsigned)3, (unsigned)4), 3);
}

TEST(OPERATIONTEST, fadd){
    Operations operations;
    ASSERT_EQ(operations.fadd(3.2, 2), 5.2);
    ASSERT_EQ(operations.fadd(3.2, -2.2), 1);
}

TEST(OPERATIONTEST, fsub){
    Operations operations;
    ASSERT_EQ(operations.fsub(3.2, 2.2), 1);
    ASSERT_EQ(operations.fsub(3.5, -2.5), 6);
}

TEST(OPERATIONTEST, fmul){
    Operations operations;
    ASSERT_EQ(operations.fmul(3.5, 2), 7);
    ASSERT_EQ(operations.fmul(6, 0.5), 3);
}

TEST(OPERATIONTEST, fdiv){
    Operations operations;
    ASSERT_EQ(operations.fdiv(3, 0.5), 6);
    ASSERT_EQ(operations.fdiv(4, 0.25), 16);
}

TEST(OPERATIONTEST, frem){
    Operations operations;
    ASSERT_EQ(operations.frem(4.5, 2), 0.5);
    ASSERT_EQ(operations.frem(6, -5), -1);
}