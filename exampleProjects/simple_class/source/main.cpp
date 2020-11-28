//
// Created by larsv on 21/11/2020.
//
#include "Profile.h"
#include <iostream>

int main(){
    Profile profile;

    profile.setFirstName("Lars");
    std::cout << profile.getFirstName() << std::endl;
    return 0;
}