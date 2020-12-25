#include "gtest/gtest.h"
#include "Profile.h"

TEST(ProfileTester, setFirstName){
    Profile profile;

    profile.setFirstName("Lars");
    ASSERT_EQ(profile.getFirstName(), "Lars ");
}