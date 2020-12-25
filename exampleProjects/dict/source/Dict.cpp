#include "Dict.h"

void Dict::add_el(int ind, int val) {
    for(tuple<int, int>& element : data){
        if(get<0>(element) == ind){
            get<1>(element) = val;
            return;
        }
    }
    data.emplace_back(tuple<int, int>(ind, val));
}

int Dict::get_el(int ind) {
    for(const tuple<int, int>& element : data){
        if(get<0>(element) == ind){
            return get<1>(element);
        }
    }
    exit(-1);
}
