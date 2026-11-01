// C++17 illustrative source; Python checks do not compile this listing.
struct Shape {
    virtual double area() const = 0;
    virtual ~Shape() = default;
    int sides() const { return 0; }
};
struct Rectangle : Shape {
    double width, height;
    Rectangle(double w, double h) : width(w), height(h) {}
    double area() const override { return width * height; }
};
