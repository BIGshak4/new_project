#include <cstdio>

struct Base {
    virtual const char *kind() const { return "base"; }
    virtual ~Base() = default;
};

struct Derived : Base {
    const char *kind() const override { return "derived"; }
};

int main() {
    Base base;
    Derived derived;
    const Base &reference = derived;
    std::puts(base.kind());
    std::puts(reference.kind());
    return 0;
}
