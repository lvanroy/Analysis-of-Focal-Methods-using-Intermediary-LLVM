//
// Created by larsv on 12/09/2020.
//

#include "gtest/gtest.h"

int add_int(int a, int b){
    return a + b;
}

TEST(ADDTEST, eq){
    ASSERT_EQ(add_int(2, 3), 5);
    ASSERT_EQ(add_int(-2, 5), 3);
}

TEST(ADDTEST, neq){
    ASSERT_NE(add_int(2,3), 6);
    ASSERT_NE(add_int(500,-4), 504);
}