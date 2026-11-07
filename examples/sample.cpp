#include <cstdio>
#include <vector>
#include <string>

#define SQUARE(x) \
    ((x) * (x))

using namespace std;

template <typename T>
struct Box {
    T value;
    Box(T v) : value(v) {}
    T get() const { return value; }
};

static const char* RAW = R"txt(
   raw   text with "quotes" and \ backslashes
)txt";

int compute(int a, int b) {
    int r = a - -b;
    r = r + +a;
    r -= b;
    vector<vector<int> > grid(3, vector<int>(3, 0));
    vector<vector<int>> grid2(2, vector<int>(2, 1));
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j)
            grid[i][j] = i * j;
    int big = 1'000'000;
    double d = 1.5e+3;
    unsigned x = 0xE + 1;
    return r + grid[1][2] + big + (int)d + (int)x + SQUARE(3);
}

int main() {
    Box<int> b(compute(3, 4));
    printf("value = %d  (%s)\n", b.get(), "text   with   spaces");
    int k = 10;
    while (k --> 0) { if (k % 3) continue; }
    return 0;
}
