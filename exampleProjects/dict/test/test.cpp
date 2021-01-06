#include "gtest/gtest.h"
#include "Dict.h"

TEST(DictTest, add_el){
    Dict d;

    d.add_el(1, 5);
    ASSERT_EQ(5, d.get_el(1));
}