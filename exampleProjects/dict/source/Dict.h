#include <vector>
#include <tuple>

using namespace std;

class Dict{
private:
    vector<tuple<int, int>> data;
public:
    Dict() =default;
    ~Dict() = default;

    void add_el(int, int);
    int get_el(int);
};