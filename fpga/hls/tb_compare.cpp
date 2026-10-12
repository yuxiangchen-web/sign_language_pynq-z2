#include "image_preprocess.h"
#include <fstream>
#include <iostream>

int main() {
    for (int mode = 0; mode < 2; ++mode) {
        std::ifstream input("input_rgb.txt");
        std::ifstream expected(mode ? "expected_1.txt" : "expected_0.txt");
        if (!input || !expected) return 2;
        hls::stream<axis_rgb_t> in;
        hls::stream<axis_mask_t> out;
        for (int i = 0; i < IMAGE_PIXELS; ++i) {
            int r, g, b;
            if (!(input >> r >> g >> b)) return 3;
            axis_rgb_t p;
            p.data = (r << 16) | (g << 8) | b;
            p.keep = 7; p.strb = 7; p.user = i == 0;
            p.last = i == IMAGE_PIXELS - 1; p.id = 0; p.dest = 0;
            in.write(p);
        }
        image_preprocess(in, out, 45, 225, 135, 190, 80, 145, mode);
        int differences = 0;
        std::ofstream result(mode ? "actual_1.txt" : "actual_0.txt");
        for (int i = 0; i < IMAGE_PIXELS; ++i) {
            if (out.empty()) return 4;
            axis_mask_t p = out.read(); int value;
            if (!(expected >> value)) return 5;
            differences += p.data != value;
            if (p.user != (i == 0) || p.last != (i == IMAGE_PIXELS - 1)
                || p.keep != 1 || p.strb != 1) return 6;
            result << p.data.to_uint() << '\n';
        }
        if (!out.empty() || !in.empty()) return 7;
        std::cout << "mode=" << mode << " pixels=" << IMAGE_PIXELS
                  << " differences=" << differences << std::endl;
        if (differences) return 8;
    }
    return 0;
}
