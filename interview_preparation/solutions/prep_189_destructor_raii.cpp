// C++17 illustrative code; see verification for the uncompiled-code limitation.
#include <memory>
#include <string>
#include <vector>

struct ValueRecord {
    std::string label;
    std::vector<int> samples;
    // Implicit destructor destroys both members: no manual delete is needed.
};
struct Interface {
    virtual ~Interface() = default; // Supports destruction through Interface*.
    virtual void run() = 0;
};
struct Implementation final : Interface {
    std::unique_ptr<int[]> buffer = std::make_unique<int[]>(16);
    void run() override { buffer[0] = 42; }
    // Implicit derived destructor releases buffer before the base destructor.
};
int main() {
    std::unique_ptr<Interface> object = std::make_unique<Implementation>();
    object->run();
} // Implementation, buffer, then Interface destruction through a virtual base.
